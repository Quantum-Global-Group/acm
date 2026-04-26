"""
Execution engine — per-job pipeline shared by /api/compute and /api/compute/batch.

Responsibilities:
  1. Dispatch the task (either simulate, or forward to the provider's registered
     provider_endpoint URL if one is set).
  2. Apply metering for actual usage.
  3. Price the work using the provider's advertised per-task rate (if registered),
     optionally discounted (used by the batch endpoint for volume discounts).
  4. Enforce the hard per-unit ceiling and the caller's max_price_usdc quote.
  5. Enforce SLA (max_latency_ms) — if the task exceeds its deadline, skip
     settlement, record a reputation failure, and return an sla_breach outcome.
  6. Settle the USDC payment on-chain (live) or simulate (offline).
  7. Record reputation (success with latency, or failure with reason).
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx

from backend.engines.metering import metering_engine
from backend.engines.pricing import PricingModel, pricing_engine
from backend.engines.registry import ProviderRecord, provider_registry
from backend.engines.reputation import reputation_engine
from backend.engines.settlement import settlement_engine
from backend.models import ComputeRequestModel


# Outcome statuses — consumed by HTTP layer to choose status codes.
STATUS_SUCCESS = "success"
STATUS_PRICE_CEILING = "price_ceiling"
STATUS_QUOTE_EXCEEDED = "quote_exceeded"
STATUS_SLA_BREACH = "sla_breach"
STATUS_DISPATCH_FAILED = "dispatch_failed"
STATUS_SETTLEMENT_FAILED = "settlement_failed"


@dataclass
class JobOutcome:
    status: str
    task_id: str
    actual_cost_usdc: float
    gross_cost_usdc: float
    tx_hash: Optional[str]
    latency_ms: float
    result: Dict[str, Any]
    task_type: str
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.status == STATUS_SUCCESS

    @property
    def http_status(self) -> int:
        return {
            STATUS_SUCCESS: 200,
            STATUS_PRICE_CEILING: 400,
            STATUS_QUOTE_EXCEEDED: 400,
            STATUS_SLA_BREACH: 408,
            STATUS_DISPATCH_FAILED: 502,
            STATUS_SETTLEMENT_FAILED: 502,
        }.get(self.status, 500)


_dispatch_client: Optional[httpx.AsyncClient] = None


async def _get_dispatch_client() -> httpx.AsyncClient:
    global _dispatch_client
    if _dispatch_client is None:
        _dispatch_client = httpx.AsyncClient(timeout=30.0)
    return _dispatch_client


async def close_dispatch_client() -> None:
    global _dispatch_client
    if _dispatch_client is not None:
        await _dispatch_client.aclose()
        _dispatch_client = None


async def _dispatch_to_provider(
    record: ProviderRecord,
    request: ComputeRequestModel,
    timeout_s: float,
) -> Dict[str, Any]:
    """Forward the task to the provider's HTTP endpoint; return its response dict."""
    client = await _get_dispatch_client()
    payload = request.model_dump(mode="json")
    r = await client.post(record.provider_endpoint, json=payload, timeout=timeout_s)
    r.raise_for_status()
    return r.json()


def _elapsed_ms(started: datetime) -> float:
    return (datetime.now(timezone.utc) - started).total_seconds() * 1000.0


async def execute_job(
    request: ComputeRequestModel,
    *,
    discount_rate: float = 0.0,
) -> JobOutcome:
    """
    Run one compute job end-to-end. Returns a JobOutcome either way — the HTTP
    layer maps the status onto a response code.
    """
    started = datetime.now(timezone.utc)
    provider_record = provider_registry.get_by_wallet(request.provider_address)
    task_type_value = request.task_type.value

    # Per-request SLA deadline. Default 30s if unset.
    deadline_ms = float(request.max_latency_ms or 30_000)
    # Leave a buffer for settlement (which happens after dispatch).
    dispatch_timeout_s = max(deadline_ms / 1000.0 - 0.5, 0.1)

    # ---------------------- dispatch (simulate or forward) ----------------------
    compute_time_ms = 50
    tokens_used = request.estimated_units * 10
    dispatch_result: Optional[Dict[str, Any]] = None

    try:
        if provider_record is not None and provider_record.provider_endpoint:
            dispatch_result = await asyncio.wait_for(
                _dispatch_to_provider(provider_record, request, dispatch_timeout_s),
                timeout=dispatch_timeout_s,
            )
            # Provider may report actual usage; fall back to defaults.
            compute_time_ms = int(dispatch_result.get("compute_time_ms", compute_time_ms))
            tokens_used = int(dispatch_result.get("tokens_used", tokens_used))
        else:
            # Simulated provider work.
            await asyncio.sleep(0.01)
    except asyncio.TimeoutError:
        latency_ms = _elapsed_ms(started)
        if provider_record is not None:
            reputation_engine.record_failure(
                provider_record.agent_id,
                reason="dispatch_timeout",
                task_type=request.task_type,
                latency_ms=latency_ms,
            )
        return JobOutcome(
            status=STATUS_SLA_BREACH,
            task_id=request.task_id,
            actual_cost_usdc=0.0,
            gross_cost_usdc=0.0,
            tx_hash=None,
            latency_ms=latency_ms,
            result={},
            task_type=task_type_value,
            error=f"Provider exceeded SLA deadline ({deadline_ms:.0f}ms) during dispatch",
        )
    except Exception as exc:  # network error, 5xx, etc.
        latency_ms = _elapsed_ms(started)
        if provider_record is not None:
            reputation_engine.record_failure(
                provider_record.agent_id,
                reason=f"dispatch_error: {exc}",
                task_type=request.task_type,
                latency_ms=latency_ms,
            )
        return JobOutcome(
            status=STATUS_DISPATCH_FAILED,
            task_id=request.task_id,
            actual_cost_usdc=0.0,
            gross_cost_usdc=0.0,
            tx_hash=None,
            latency_ms=latency_ms,
            result={},
            task_type=task_type_value,
            error=f"dispatch_error: {exc}",
        )

    # ---------------------- SLA gate (post-dispatch) ----------------------
    post_dispatch_ms = _elapsed_ms(started)
    if request.max_latency_ms is not None and post_dispatch_ms > request.max_latency_ms:
        if provider_record is not None:
            reputation_engine.record_failure(
                provider_record.agent_id,
                reason=f"sla_breach: {post_dispatch_ms:.0f}ms > {request.max_latency_ms}ms",
                task_type=request.task_type,
                latency_ms=post_dispatch_ms,
            )
        return JobOutcome(
            status=STATUS_SLA_BREACH,
            task_id=request.task_id,
            actual_cost_usdc=0.0,
            gross_cost_usdc=0.0,
            tx_hash=None,
            latency_ms=post_dispatch_ms,
            result={},
            task_type=task_type_value,
            error=f"Provider exceeded SLA: {post_dispatch_ms:.0f}ms > {request.max_latency_ms}ms",
        )

    # ---------------------- metering + pricing ----------------------
    usage = metering_engine.record_usage(
        quantity=request.estimated_units,
        unit_type="query",
        compute_time_ms=compute_time_ms,
        tokens_used=tokens_used,
    )

    pricing_model: Optional[PricingModel] = None
    if provider_record is not None:
        pricing_model = PricingModel(
            base_unit_price=provider_record.price_for(request.task_type),
            compute_time_multiplier=pricing_engine.DEFAULT.compute_time_multiplier,
            token_multiplier=pricing_engine.DEFAULT.token_multiplier,
        )

    gross_cost = pricing_engine.calculate_cost(usage, pricing_model)
    # Clamp discount to [0, 1) so we always send a positive amount.
    discount = max(0.0, min(float(discount_rate), 0.99))
    actual_cost = gross_cost * (1.0 - discount)

    def _record_failure(status: str, reason: str) -> JobOutcome:
        latency = _elapsed_ms(started)
        if provider_record is not None:
            reputation_engine.record_failure(
                provider_record.agent_id,
                reason=reason,
                task_type=request.task_type,
                latency_ms=latency,
            )
        return JobOutcome(
            status=status,
            task_id=request.task_id,
            actual_cost_usdc=0.0,
            gross_cost_usdc=gross_cost,
            tx_hash=None,
            latency_ms=latency,
            result={},
            task_type=task_type_value,
            error=reason,
        )

    try:
        pricing_engine.enforce_max_unit_price(usage, pricing_model)
    except AssertionError as exc:
        return _record_failure(STATUS_PRICE_CEILING, f"price_ceiling: {exc}")

    is_valid, _ = pricing_engine.validate_price(usage, request.max_price_usdc, pricing_model)
    if not is_valid:
        return _record_failure(
            STATUS_QUOTE_EXCEEDED,
            f"quote_exceeded: {actual_cost:.6f} > {request.max_price_usdc:.6f}",
        )

    # ---------------------- settlement ----------------------
    tx_hash = await settlement_engine.settle_payment(
        consumer_address=request.consumer_address,
        provider_address=request.provider_address,
        amount_usdc=actual_cost,
        task_id=request.task_id,
        quantity=request.estimated_units,
    )
    if tx_hash is None:
        return _record_failure(STATUS_SETTLEMENT_FAILED, "settlement_failed")

    latency_ms = _elapsed_ms(started)
    if provider_record is not None:
        reputation_engine.record_success(
            provider_record.agent_id,
            latency_ms=latency_ms,
            task_type=request.task_type,
        )

    result_payload: Dict[str, Any] = {
        "data": "computed",
        "units_processed": request.estimated_units,
        "task_type": task_type_value,
        "latency_ms": latency_ms,
        "compute_time_ms": compute_time_ms,
        "tokens_used": tokens_used,
    }
    if dispatch_result is not None:
        # Let the provider surface whatever payload it wants under `provider_result`.
        result_payload["provider_result"] = dispatch_result.get("result", dispatch_result)

    return JobOutcome(
        status=STATUS_SUCCESS,
        task_id=request.task_id,
        actual_cost_usdc=actual_cost,
        gross_cost_usdc=gross_cost,
        tx_hash=tx_hash,
        latency_ms=latency_ms,
        result=result_payload,
        task_type=task_type_value,
    )


# --------------------------------------------------------------------- batching


def volume_discount_rate(job_count: int) -> float:
    """Step curve: more jobs → bigger discount. Caps at 15%."""
    if job_count >= 100:
        return 0.15
    if job_count >= 50:
        return 0.10
    if job_count >= 10:
        return 0.05
    return 0.0
