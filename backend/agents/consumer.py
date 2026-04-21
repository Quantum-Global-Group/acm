"""
Consumer agent — autonomous compute purchaser.

Responsibilities:
  - Track its own USDC balance (off-chain mirror of marketplace balance).
  - Decide when and what to buy (autonomous policy).
  - Sign x402 payment proofs and submit /api/compute requests.
  - Reconcile observed cost vs internal budget.
"""
from __future__ import annotations

import asyncio
import random
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx

from backend.models import ComputeTaskType


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
    ) -> None:
        self.agent_id = agent_id
        self.wallet_address = wallet_address
        self.api_endpoint = api_endpoint.rstrip("/")
        self.balance_usdc = initial_balance_usdc
        self.max_price_per_unit = max_price_per_unit
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
        """Round-robin through providers, fire `num_jobs` requests."""
        if not providers:
            return
        for i in range(num_jobs):
            provider = providers[i % len(providers)]
            await self.request_compute(provider, units=units_per_job)

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
