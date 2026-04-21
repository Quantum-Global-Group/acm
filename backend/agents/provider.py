"""
Provider agent — autonomous compute supplier.

In the modular flow the actual /api/compute endpoint embeds provider
behavior (the backend handles execution and metering).  This class
represents the off-chain mirror used for accounting, balance reconciliation,
and capability advertisement that consumers select against.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from backend.models import ComputeTaskType


@dataclass
class ProviderStats:
    jobs_completed: int = 0
    total_revenue: float = 0.0
    units_served: int = 0


class ProviderAgent:
    def __init__(
        self,
        agent_id: str,
        wallet_address: str,
        supported_tasks: List[ComputeTaskType],
        unit_price: float = 0.0001,
    ) -> None:
        self.agent_id = agent_id
        self.wallet_address = wallet_address
        self.supported_tasks = supported_tasks
        self.unit_price = unit_price
        self.balance_usdc: float = 0.0
        self.stats = ProviderStats()

    def can_serve(self, task_type: ComputeTaskType) -> bool:
        return task_type in self.supported_tasks

    def credit(self, amount_usdc: float, units: int) -> None:
        """Called when a payment is recorded against this provider."""
        self.balance_usdc += amount_usdc
        self.stats.total_revenue += amount_usdc
        self.stats.units_served += units
        self.stats.jobs_completed += 1

    def status(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "wallet": self.wallet_address,
            "balance_usdc": self.balance_usdc,
            "jobs_completed": self.stats.jobs_completed,
            "total_revenue": self.stats.total_revenue,
            "units_served": self.stats.units_served,
            "supported_tasks": [t.value for t in self.supported_tasks],
        }
