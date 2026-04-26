"""
Consumer agent — autonomous compute purchaser.

Responsibilities:
  - Track its own USDC balance (off-chain mirror of marketplace balance).
  - Decide when and what to buy (autonomous policy).
  - Discover providers via the marketplace registry.
  - Sign x402 payment proofs and submit /api/compute requests.
  - Reconcile observed cost vs internal budget.
"""
from __future__ import annotations

import asyncio
import random
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx

from backend.models import ComputeTaskType


class SelectionStrategy(str, Enum):
    """How the consumer picks a provider from the registry."""
    CHEAPEST = "cheapest"                # min price for task_type
    MOST_REPUTABLE = "most_reputable"    # max reputation_score
    BALANCED = "balanced"                # max (reputation / price)
    RANDOM = "random"                    # uniform sample from candidates


@dataclass
class ConsumerStats:
    requests_made: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_spent: float = 0.0
    tx_hashes: List[str] = field(default_factory=list)


class ConsumerAgent:
    """Autonomous consumer with simple policy: pick a provider, request, settle."""

    def __init__(
        self,
        agent_id: str,
        wallet_address: str,
        api_endpoint: str,
        initial_balance_usdc: float = 5.0,
        max_price_per_unit: float = 0.001,
        selection_strategy: SelectionStrategy = SelectionStrategy.BALANCED,
    ) -> None:
        self.agent_id = agent_id
        self.wallet_address = wallet_address
        self.api_endpoint = api_endpoint.rstrip("/")
        self.balance_usdc = initial_balance_usdc
        self.max_price_per_unit = max_price_per_unit
        self.selection_strategy = selection_strategy
        self.stats = ConsumerStats()
        self._client: Optional[httpx.AsyncClient] = None

    async def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # -------------------------------------------------------------------- policy

    def _choose_task(self) -> ComputeTaskType:
        return random.choice(list(ComputeTaskType))

    def _x402_header(self, task_id: str, max_amount: float) -> str:
        # Production: signed payload via Circle x402 facilitator.
        # Demo: deterministic proof string derived from agent + task.
        return f"x402:{self.agent_id}:{task_id}:{max_amount:.6f}"

    # ------------------------------------------------------------------- actions

    async def request_compute(
        self,
        provider_address: str,
        units: int = 100,
        task_type: Optional[ComputeTaskType] = None,
    ) -> Optional[Dict[str, Any]]:
        """Submit one request to the marketplace; return the parsed result or None."""
        if self.balance_usdc < self.max_price_per_unit * units:
            return None

        task_id = f"task-{uuid.uuid4().hex[:12]}"
        task = task_type or self._choose_task()
        max_total = self.max_price_per_unit * units

        payload = {
            "task_id": task_id,
            "task_type": task.value,
            "consumer_address": self.wallet_address,
            "provider_address": provider_address,
            "estimated_units": units,
            "max_price_usdc": max_total,
            "params": {"requested_by": self.agent_id},
        }
        headers = {"X-402-Payment": self._x402_header(task_id, max_total)}

        client = await self._http()
        self.stats.requests_made += 1
        try:
            r = await client.post(f"{self.api_endpoint}/api/compute", json=payload, headers=headers)
            if r.status_code != 200:
                self.stats.failed_requests += 1
                return None
            data = r.json()
            cost = float(data.get("actual_cost_usdc") or 0.0)
            self.balance_usdc -= cost
            self.stats.total_spent += cost
            self.stats.successful_requests += 1
            tx = data.get("arc_tx_hash")
            if tx:
                self.stats.tx_hashes.append(tx)
            return data
        except Exception:
            self.stats.failed_requests += 1
            return None

    async def run_jobs(self, providers: List[str], num_jobs: int, units_per_job: int = 100) -> None:
        """Round-robin through a fixed provider list. Legacy path; prefer run_jobs_discovered."""
        if not providers:
            return
        for i in range(num_jobs):
            provider = providers[i % len(providers)]
            await self.request_compute(provider, units=units_per_job)

    # ---------------------------------------------------------------- discovery

    async def discover_providers(
        self,
        task_type: Optional[ComputeTaskType] = None,
        max_price: Optional[float] = None,
        min_reputation: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Query /api/providers with optional filters. Returns listing dicts."""
        params: Dict[str, Any] = {}
        if task_type is not None:
            params["task_type"] = task_type.value
        if max_price is not None:
            params["max_price"] = max_price
        if min_reputation is not None:
            params["min_reputation"] = min_reputation

        client = await self._http()
        try:
            r = await client.get(f"{self.api_endpoint}/api/providers", params=params)
            if r.status_code != 200:
                return []
            return r.json().get("providers", [])
        except Exception:
            return []

    def select_provider(
        self,
        candidates: List[Dict[str, Any]],
        task_type: ComputeTaskType,
        strategy: Optional[SelectionStrategy] = None,
    ) -> Optional[Dict[str, Any]]:
        """Pick one provider from candidates according to strategy."""
        if not candidates:
            return None
        strat = strategy or self.selection_strategy

        def price(p: Dict[str, Any]) -> float:
            return float(
                p.get("pricing", {}).get(task_type.value, p.get("default_unit_price", 0.0))
            )

        def reputation(p: Dict[str, Any]) -> float:
            return float(p.get("reputation_score", 0.0))

        if strat is SelectionStrategy.RANDOM:
            return random.choice(candidates)
        if strat is SelectionStrategy.CHEAPEST:
            return min(candidates, key=price)
        if strat is SelectionStrategy.MOST_REPUTABLE:
            return max(candidates, key=reputation)
        # BALANCED: reputation / price; protect against zero-reputation cold-start
        # by adding a small constant so cheapest still wins when no history exists.
        def score(p: Dict[str, Any]) -> float:
            pr = max(price(p), 1e-9)
            return (reputation(p) + 0.01) / pr
        return max(candidates, key=score)

    async def run_jobs_discovered(
        self,
        num_jobs: int,
        task_type: Optional[ComputeTaskType] = None,
        units_per_job: int = 100,
        strategy: Optional[SelectionStrategy] = None,
        refresh_every: int = 10,
    ) -> None:
        """
        Discover providers via the registry, then fire `num_jobs` requests.
        Refreshes the candidate list every `refresh_every` jobs so newly-good
        providers get traffic as their reputation grows.
        """
        candidates: List[Dict[str, Any]] = []
        for i in range(num_jobs):
            task = task_type or self._choose_task()
            if i % refresh_every == 0 or not candidates:
                candidates = await self.discover_providers(task_type=task)
            if not candidates:
                self.stats.failed_requests += 1
                continue
            chosen = self.select_provider(candidates, task, strategy=strategy)
            if chosen is None:
                self.stats.failed_requests += 1
                continue
            await self.request_compute(
                provider_address=chosen["wallet_address"],
                units=units_per_job,
                task_type=task,
            )

    def status(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "wallet": self.wallet_address,
            "balance_usdc": self.balance_usdc,
            "requests_made": self.stats.requests_made,
            "successful": self.stats.successful_requests,
            "failed": self.stats.failed_requests,
            "total_spent": self.stats.total_spent,
            "tx_count": len(self.stats.tx_hashes),
        }
