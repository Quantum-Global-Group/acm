"""
Provider registry — directory of marketplace providers.

Consumers discover providers here. Each provider advertises the task types
it serves and a price per task type (with a default fallback). The registry
also holds the running reputation stats that the reputation engine updates
after each settlement.

In-memory only; production would persist to Postgres / Redis.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from backend.models import (
    ComputeTaskType,
    ProviderListing,
    ProviderRegistration,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ProviderRecord:
    agent_id: str
    wallet_address: str
    supported_tasks: List[ComputeTaskType]
    pricing: Dict[ComputeTaskType, float]
    default_unit_price: float
    name: Optional[str]
    description: Optional[str]
    registered_at: datetime
    provider_endpoint: Optional[str] = None
    active: bool = True
    # Reputation fields — written by reputation engine, read here.
    jobs_completed: int = 0
    jobs_failed: int = 0
    total_latency_ms: float = 0.0
    reputation_score: float = 0.0

    @property
    def success_rate(self) -> float:
        total = self.jobs_completed + self.jobs_failed
        if total == 0:
            return 1.0
        return self.jobs_completed / total

    @property
    def avg_latency_ms(self) -> float:
        if self.jobs_completed == 0:
            return 0.0
        return self.total_latency_ms / self.jobs_completed

    def price_for(self, task_type: ComputeTaskType) -> float:
        return self.pricing.get(task_type, self.default_unit_price)

    def to_listing(self) -> ProviderListing:
        return ProviderListing(
            agent_id=self.agent_id,
            wallet_address=self.wallet_address,
            supported_tasks=list(self.supported_tasks),
            pricing={t.value: p for t, p in self.pricing.items()},
            default_unit_price=self.default_unit_price,
            name=self.name,
            description=self.description,
            provider_endpoint=self.provider_endpoint,
            registered_at=self.registered_at,
            active=self.active,
            jobs_completed=self.jobs_completed,
            jobs_failed=self.jobs_failed,
            success_rate=self.success_rate,
            avg_latency_ms=self.avg_latency_ms,
            reputation_score=self.reputation_score,
        )


class ProviderRegistry:
    """In-memory directory of providers."""

    def __init__(self) -> None:
        self._providers: Dict[str, ProviderRecord] = {}

    def register(self, registration: ProviderRegistration) -> ProviderRecord:
        """Idempotent register/update. Re-registering with the same agent_id
        overwrites advertised details but preserves reputation history."""
        existing = self._providers.get(registration.agent_id)
        if existing is not None:
            existing.wallet_address = registration.wallet_address
            existing.supported_tasks = list(registration.supported_tasks)
            existing.pricing = dict(registration.pricing)
            existing.default_unit_price = registration.default_unit_price
            existing.name = registration.name
            existing.description = registration.description
            existing.provider_endpoint = registration.provider_endpoint
            existing.active = True
            return existing

        record = ProviderRecord(
            agent_id=registration.agent_id,
            wallet_address=registration.wallet_address,
            supported_tasks=list(registration.supported_tasks),
            pricing=dict(registration.pricing),
            default_unit_price=registration.default_unit_price,
            name=registration.name,
            description=registration.description,
            provider_endpoint=registration.provider_endpoint,
            registered_at=_utcnow(),
        )
        self._providers[registration.agent_id] = record
        return record

    def deregister(self, agent_id: str) -> bool:
        record = self._providers.get(agent_id)
        if record is None:
            return False
        record.active = False
        return True

    def get(self, agent_id: str) -> Optional[ProviderRecord]:
        return self._providers.get(agent_id)

    def get_by_wallet(self, wallet_address: str) -> Optional[ProviderRecord]:
        wallet = wallet_address.lower()
        for record in self._providers.values():
            if record.wallet_address.lower() == wallet:
                return record
        return None

    def list(
        self,
        task_type: Optional[ComputeTaskType] = None,
        max_price: Optional[float] = None,
        min_reputation: Optional[float] = None,
        active_only: bool = True,
    ) -> List[ProviderRecord]:
        result: List[ProviderRecord] = []
        for record in self._providers.values():
            if active_only and not record.active:
                continue
            if task_type is not None and task_type not in record.supported_tasks:
                continue
            if max_price is not None and record.price_for(
                task_type or record.supported_tasks[0]
            ) > max_price:
                continue
            if min_reputation is not None and record.reputation_score < min_reputation:
                continue
            result.append(record)
        return result

    def reset(self) -> None:
        self._providers.clear()

    def count(self) -> int:
        return len(self._providers)


provider_registry = ProviderRegistry()
