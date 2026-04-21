"""Usage metering engine — records and aggregates per-action compute usage."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UsageMetrics(BaseModel):
    quantity: int
    unit_type: str
    compute_time_ms: int
    tokens_used: int = 0
    memory_used_mb: int = 0
    timestamp: datetime = Field(default_factory=_utcnow)


class MeteringEngine:
    """In-memory metering. Production would persist to DB / time-series store."""

    def __init__(self) -> None:
        self.records: List[UsageMetrics] = []

    def record_usage(
        self,
        quantity: int,
        unit_type: str,
        compute_time_ms: int,
        tokens_used: int = 0,
        memory_used_mb: int = 0,
    ) -> UsageMetrics:
        metrics = UsageMetrics(
            quantity=quantity,
            unit_type=unit_type,
            compute_time_ms=compute_time_ms,
            tokens_used=tokens_used,
            memory_used_mb=memory_used_mb,
        )
        self.records.append(metrics)
        return metrics

    def get_summary(self) -> Dict[str, Any]:
        if not self.records:
            return {
                "total_units": 0,
                "total_compute_ms": 0,
                "total_tokens": 0,
                "avg_time_ms": 0,
                "record_count": 0,
                "unit_types": {},
            }

        unit_types: Dict[str, int] = {}
        for record in self.records:
            unit_types[record.unit_type] = unit_types.get(record.unit_type, 0) + record.quantity

        total_ms = sum(r.compute_time_ms for r in self.records)
        return {
            "total_units": sum(r.quantity for r in self.records),
            "total_compute_ms": total_ms,
            "total_tokens": sum(r.tokens_used for r in self.records),
            "avg_time_ms": total_ms / len(self.records),
            "record_count": len(self.records),
            "unit_types": unit_types,
            "oldest_record": self.records[0].timestamp.isoformat(),
            "latest_record": self.records[-1].timestamp.isoformat(),
        }

    def reset(self) -> None:
        self.records.clear()


metering_engine = MeteringEngine()
