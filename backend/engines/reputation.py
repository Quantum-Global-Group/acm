"""
Reputation engine — tracks per-provider quality metrics and derives a
reputation score that consumers can use when picking providers.

What it records (per event):
  - success: (agent_id, latency_ms, task_type)
  - failure: (agent_id, reason, task_type)

What it writes back to the registry (per provider):
  - jobs_completed, jobs_failed, total_latency_ms (raw counters)
  - reputation_score: a single [0, 1]-ish scalar consumers can sort by

Scoring philosophy:
  score = success_rate * experience_factor * latency_factor

  success_rate     = completed / (completed + failed)            in [0, 1]
  experience_factor = min(1, log10(1 + jobs_completed) / 2)      saturates ~100 jobs
  latency_factor   = 1 / (1 + avg_latency_ms / 1000)             penalty above ~1s

Event log kept in-memory for analytics; trim-on-size to avoid unbounded growth.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Deque, Dict, List, Optional
from collections import deque

from backend.engines.registry import provider_registry
from backend.models import ComputeTaskType


MAX_EVENT_LOG = 10_000


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class QualityEvent:
    agent_id: str
    task_type: Optional[ComputeTaskType]
    outcome: str  # "success" | "failure"
    latency_ms: Optional[float]
    reason: Optional[str]
    timestamp: datetime = field(default_factory=_utcnow)


class ReputationEngine:
    """Updates provider reputation based on compute outcomes."""

    def __init__(self) -> None:
        self.events: Deque[QualityEvent] = deque(maxlen=MAX_EVENT_LOG)

    # --------------------------------------------------------------- recording

    def record_success(
        self,
        agent_id: str,
        latency_ms: float,
        task_type: Optional[ComputeTaskType] = None,
    ) -> None:
        record = provider_registry.get(agent_id)
        if record is None:
            return
        record.jobs_completed += 1
        record.total_latency_ms += max(0.0, float(latency_ms))
        record.reputation_score = self._score_for(record)
        self.events.append(QualityEvent(
            agent_id=agent_id,
            task_type=task_type,
            outcome="success",
            latency_ms=latency_ms,
            reason=None,
        ))

    def record_failure(
        self,
        agent_id: str,
        reason: str,
        task_type: Optional[ComputeTaskType] = None,
        latency_ms: Optional[float] = None,
    ) -> None:
        record = provider_registry.get(agent_id)
        if record is None:
            return
        record.jobs_failed += 1
        record.reputation_score = self._score_for(record)
        self.events.append(QualityEvent(
            agent_id=agent_id,
            task_type=task_type,
            outcome="failure",
            latency_ms=latency_ms,
            reason=reason,
        ))

    # ----------------------------------------------------------------- scoring

    @staticmethod
    def _score_for(record) -> float:
        total = record.jobs_completed + record.jobs_failed
        if total == 0:
            return 0.0
        success_rate = record.jobs_completed / total
        experience = min(1.0, math.log10(1 + record.jobs_completed) / 2.0)
        avg_latency = (
            record.total_latency_ms / record.jobs_completed
            if record.jobs_completed
            else 0.0
        )
        latency_factor = 1.0 / (1.0 + avg_latency / 1000.0)
        return success_rate * experience * latency_factor

    # ------------------------------------------------------------------- views

    def recent_events(self, agent_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
        events = list(self.events)
        if agent_id:
            events = [e for e in events if e.agent_id == agent_id]
        events = events[-limit:]
        out = []
        for e in events:
            out.append({
                "agent_id": e.agent_id,
                "task_type": e.task_type.value if e.task_type else None,
                "outcome": e.outcome,
                "latency_ms": e.latency_ms,
                "reason": e.reason,
                "timestamp": e.timestamp.isoformat(),
            })
        return out

    def leaderboard(self, top_n: int = 10) -> List[Dict]:
        """Providers sorted by reputation score (highest first)."""
        records = [
            r for r in provider_registry.list(active_only=True)
            if (r.jobs_completed + r.jobs_failed) > 0
        ]
        records.sort(key=lambda r: r.reputation_score, reverse=True)
        result = []
        for r in records[:top_n]:
            result.append({
                "agent_id": r.agent_id,
                "name": r.name,
                "reputation_score": r.reputation_score,
                "success_rate": r.success_rate,
                "avg_latency_ms": r.avg_latency_ms,
                "jobs_completed": r.jobs_completed,
                "jobs_failed": r.jobs_failed,
            })
        return result

    def reset(self) -> None:
        self.events.clear()


reputation_engine = ReputationEngine()
