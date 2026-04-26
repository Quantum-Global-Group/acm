"""
AgentManager — orchestrates a population of consumer + provider agents
against a running backend (or in-process pipeline).
"""
from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from backend.agents.consumer import ConsumerAgent
from backend.agents.provider import ProviderAgent
from backend.engines.registry import provider_registry
from backend.models import ComputeTaskType, ProviderRegistration


@dataclass
class ManagerStats:
    interaction_count: int = 0


class AgentManager:
    def __init__(self, api_endpoint: str = "http://localhost:8000") -> None:
        self.api_endpoint = api_endpoint
        self.consumers: Dict[str, ConsumerAgent] = {}
        self.providers: Dict[str, ProviderAgent] = {}
        self.stats = ManagerStats()

    # -------------------------------------------------------------- lifecycle

    def add_consumer(
        self,
        agent_id: str,
        wallet_address: str,
        initial_balance: float = 5.0,
        max_price_per_unit: float = 0.001,
    ) -> ConsumerAgent:
        agent = ConsumerAgent(
            agent_id=agent_id,
            wallet_address=wallet_address,
            api_endpoint=self.api_endpoint,
            initial_balance_usdc=initial_balance,
            max_price_per_unit=max_price_per_unit,
        )
        self.consumers[agent_id] = agent
        return agent

    def add_provider(
        self,
        agent_id: str,
        wallet_address: str,
        supported_tasks: Optional[List[str]] = None,
        unit_price: float = 0.0001,
        pricing: Optional[Dict[str, float]] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        register: bool = True,
    ) -> ProviderAgent:
        if supported_tasks is None:
            tasks = list(ComputeTaskType)
        else:
            tasks = [ComputeTaskType(t) for t in supported_tasks]

        pricing_map: Dict[ComputeTaskType, float] = {}
        if pricing:
            pricing_map = {ComputeTaskType(k): float(v) for k, v in pricing.items()}

        agent = ProviderAgent(
            agent_id=agent_id,
            wallet_address=wallet_address,
            supported_tasks=tasks,
            unit_price=unit_price,
            pricing=pricing_map,
            name=name,
            description=description,
        )
        self.providers[agent_id] = agent

        if register:
            provider_registry.register(ProviderRegistration(
                agent_id=agent_id,
                wallet_address=wallet_address,
                supported_tasks=tasks,
                pricing=pricing_map,
                default_unit_price=unit_price,
                name=name,
                description=description,
            ))

        return agent

    async def close(self) -> None:
        await asyncio.gather(*(c.close() for c in self.consumers.values()))

    # ---------------------------------------------------------------- driving

    async def marketplace_simulation(
        self,
        num_transactions: int,
        units_per_transaction: int = 100,
    ) -> None:
        """Spread `num_transactions` requests across all consumer/provider pairs."""
        if not self.consumers or not self.providers:
            raise RuntimeError("Need at least one consumer and one provider")

        consumer_list = list(self.consumers.values())
        provider_list = list(self.providers.values())

        async def _run_one(idx: int) -> None:
            consumer = consumer_list[idx % len(consumer_list)]
            provider = provider_list[idx % len(provider_list)]
            # Pick a random supported task from the chosen provider.
            task = random.choice(provider.supported_tasks)
            result = await consumer.request_compute(
                provider_address=provider.wallet_address,
                units=units_per_transaction,
                task_type=task,
            )
            if result and result.get("status") == "success":
                provider.credit(float(result.get("actual_cost_usdc") or 0.0), units_per_transaction)
                self.stats.interaction_count += 1

        # Serialize when driving live settlement: all txs are signed with the same
        # backend PRIVATE_KEY, so parallel sends race on nonce / gas price.
        sem = asyncio.Semaphore(1)

        async def _bounded(i: int) -> None:
            async with sem:
                await _run_one(i)

        await asyncio.gather(*(_bounded(i) for i in range(num_transactions)))

    # ------------------------------------------------------------------ views

    def status(self) -> Dict[str, Any]:
        return {
            "interaction_count": self.stats.interaction_count,
            "consumers": [c.status() for c in self.consumers.values()],
            "providers": [p.status() for p in self.providers.values()],
        }

    @property
    def interaction_count(self) -> int:
        return self.stats.interaction_count
