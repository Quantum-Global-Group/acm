"""FastAPI entrypoint for the Agent-to-Agent Compute Marketplace backend."""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, Header, HTTPException

from backend.config import settings, validate_settings
from backend.engines.execution import (
    STATUS_SUCCESS,
    close_dispatch_client,
    execute_job,
    volume_discount_rate,
)
from backend.engines.metering import metering_engine
from backend.engines.pricing import pricing_engine
from backend.engines.registry import provider_registry
from backend.engines.reputation import reputation_engine
from backend.engines.settlement import settlement_engine
from backend.models import (
    BatchComputeRequestModel,
    BatchComputeResultModel,
    ComputeRequestModel,
    ComputeResultModel,
    ComputeTaskType,
    HealthCheckModel,
    ProviderListing,
    ProviderListResponse,
    ProviderRegistration,
)


startup_time = datetime.now(timezone.utc)


@asynccontextmanager
async def lifespan(_: FastAPI):
    print("=" * 60)
    print(f"Starting {settings.api_title} v{settings.api_version}")
    print("=" * 60)
    try:
        validate_settings()
    except ValueError as exc:
        print(f"[startup] WARNING: {exc}")
    print(f"Listening on {settings.api_host}:{settings.api_port}")
    print("=" * 60)
    try:
        yield
    finally:
        await close_dispatch_client()


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Trustless marketplace for autonomous agent-to-agent compute settlement",
    lifespan=lifespan,
)


@app.get("/", tags=["meta"])
async def root() -> Dict[str, Any]:
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "status": "running",
        "endpoints": {
            "health": "/health",
            "compute": "/api/compute",
            "metrics": "/api/metrics",
            "records": "/api/records",
            "providers": "/api/providers",
            "docs": "/docs",
        },
    }


@app.get("/api/public-meta", tags=["meta"])
async def public_meta() -> Dict[str, Any]:
    """
    Non-sensitive chain + API metadata for stakeholder UIs.

    Excludes any keys, secrets, or relayer addresses. Safe to expose to a
    browser via the BFF proxy.
    """
    return {
        "api_version": settings.api_version,
        "arc_chain_id": settings.arc_chain_id,
        "arc_contract_address": settings.arc_contract_address,
        "arc_explorer_url": settings.arc_explorer_url,
        "usdc_address": settings.usdc_address,
    }


@app.get("/health", response_model=HealthCheckModel, tags=["meta"])
async def health() -> HealthCheckModel:
    contract_deployed = bool(
        settings.arc_contract_address
        and settings.arc_contract_address.lower() != "0x" + "0" * 40
    )
    return HealthCheckModel(
        status="ok",
        timestamp=datetime.now(timezone.utc),
        version=settings.api_version,
        arc_connected=bool(settings.arc_rpc_url),
        contract_deployed=contract_deployed,
        settlement_simulate=settings.settlement_simulate or not contract_deployed,
    )


@app.post("/api/compute", response_model=ComputeResultModel, tags=["marketplace"])
async def request_compute(
    request: ComputeRequestModel,
    x_402_payment: Optional[str] = Header(default=None, alias="X-402-Payment"),
) -> ComputeResultModel:
    """
    Consumer-agent compute request entry point.

    Flow:
      1. x402 payment proof must be present (402 otherwise).
      2. Execution engine dispatches (to provider endpoint if set, else simulates),
         meters, prices, enforces SLA + quote, settles, records reputation.
      3. Non-success outcomes are mapped to their HTTP status (400/408/502).
    """
    if not x_402_payment:
        raise HTTPException(status_code=402, detail="Payment Required - x402 header missing")

    outcome = await execute_job(request)

    if outcome.status != STATUS_SUCCESS:
        raise HTTPException(status_code=outcome.http_status, detail=outcome.error or outcome.status)

    return ComputeResultModel(
        task_id=outcome.task_id,
        status="success",
        actual_cost_usdc=outcome.actual_cost_usdc,
        arc_tx_hash=outcome.tx_hash,
        result=outcome.result,
        timestamp=datetime.now(timezone.utc),
    )


@app.post(
    "/api/compute/batch",
    response_model=BatchComputeResultModel,
    tags=["marketplace"],
)
async def request_compute_batch(
    batch: BatchComputeRequestModel,
    x_402_payment: Optional[str] = Header(default=None, alias="X-402-Payment"),
) -> BatchComputeResultModel:
    """
    Batch compute — submit many jobs in one call and receive a volume discount.

    Discount tiers (applied to every job's cost):
      -   1–9 jobs: 0%
      -  10–49 jobs: 5%
      -  50–99 jobs: 10%
      - 100+ jobs:   15%

    If `allow_partial` is true, per-job failures are returned in-line and the
    batch still returns 200. Otherwise a single failure aborts the batch with 207.
    """
    if not x_402_payment:
        raise HTTPException(status_code=402, detail="Payment Required - x402 header missing")

    jobs = batch.jobs
    discount = volume_discount_rate(len(jobs))

    results: List[ComputeResultModel] = []
    gross_total = 0.0
    net_total = 0.0
    success_count = 0
    failed_count = 0
    first_fatal: Optional[str] = None

    for job in jobs:
        outcome = await execute_job(job, discount_rate=discount)
        gross_total += outcome.gross_cost_usdc
        net_total += outcome.actual_cost_usdc
        if outcome.ok:
            success_count += 1
        else:
            failed_count += 1
            if first_fatal is None:
                first_fatal = outcome.error or outcome.status
            if not batch.allow_partial:
                break

        results.append(ComputeResultModel(
            task_id=outcome.task_id,
            status="success" if outcome.ok else "failed",
            actual_cost_usdc=outcome.actual_cost_usdc,
            arc_tx_hash=outcome.tx_hash,
            result=outcome.result if outcome.ok else None,
            error=None if outcome.ok else outcome.error,
            timestamp=datetime.now(timezone.utc),
        ))

    if not batch.allow_partial and failed_count > 0:
        raise HTTPException(status_code=400, detail=f"Batch aborted: {first_fatal}")

    return BatchComputeResultModel(
        results=results,
        job_count=len(jobs),
        successful_count=success_count,
        failed_count=failed_count,
        discount_rate=discount,
        total_cost_usdc=net_total,
        gross_cost_usdc=gross_total,
        savings_usdc=max(0.0, gross_total - net_total),
    )


@app.get("/api/metrics", tags=["marketplace"])
async def metrics() -> Dict[str, Any]:
    uptime = (datetime.now(timezone.utc) - startup_time).total_seconds()
    return {
        "metering": metering_engine.get_summary(),
        "settlement": settlement_engine.get_settlement_summary(),
        "uptime_seconds": uptime,
    }


@app.get("/api/records", tags=["marketplace"])
async def records() -> Dict[str, Any]:
    return {"records": settlement_engine.get_records()}


@app.post(
    "/api/providers/register",
    response_model=ProviderListing,
    tags=["registry"],
    status_code=201,
)
async def register_provider(registration: ProviderRegistration) -> ProviderListing:
    """
    Register (or update) a provider in the marketplace directory.

    Providers advertise the task types they serve and a price per task type.
    Re-registering with the same agent_id overwrites advertised details but
    preserves accumulated reputation.
    """
    record = provider_registry.register(registration)
    return record.to_listing()


@app.get(
    "/api/providers",
    response_model=ProviderListResponse,
    tags=["registry"],
)
async def list_providers(
    task_type: Optional[ComputeTaskType] = None,
    max_price: Optional[float] = None,
    min_reputation: Optional[float] = None,
    include_inactive: bool = False,
) -> ProviderListResponse:
    """
    Discover providers. Filters:
      - task_type: only providers supporting this task
      - max_price: only providers whose price for task_type (or default) is ≤ this
      - min_reputation: only providers with reputation score ≥ this
      - include_inactive: include deregistered providers
    """
    records = provider_registry.list(
        task_type=task_type,
        max_price=max_price,
        min_reputation=min_reputation,
        active_only=not include_inactive,
    )
    listings = [r.to_listing() for r in records]
    return ProviderListResponse(providers=listings, count=len(listings))


@app.get(
    "/api/providers/{agent_id}",
    response_model=ProviderListing,
    tags=["registry"],
)
async def get_provider(agent_id: str) -> ProviderListing:
    record = provider_registry.get(agent_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Provider {agent_id} not found")
    return record.to_listing()


@app.delete("/api/providers/{agent_id}", tags=["registry"])
async def deregister_provider(agent_id: str) -> Dict[str, Any]:
    if not provider_registry.deregister(agent_id):
        raise HTTPException(status_code=404, detail=f"Provider {agent_id} not found")
    return {"status": "deregistered", "agent_id": agent_id}


@app.get("/api/providers/{agent_id}/events", tags=["registry"])
async def get_provider_events(agent_id: str, limit: int = 100) -> Dict[str, Any]:
    """Recent quality events for a provider (successes + failures with latency)."""
    if provider_registry.get(agent_id) is None:
        raise HTTPException(status_code=404, detail=f"Provider {agent_id} not found")
    return {
        "agent_id": agent_id,
        "events": reputation_engine.recent_events(agent_id=agent_id, limit=limit),
    }


@app.get("/api/leaderboard", tags=["registry"])
async def leaderboard(top_n: int = 10) -> Dict[str, Any]:
    """Top providers by reputation score."""
    return {"leaderboard": reputation_engine.leaderboard(top_n=top_n)}


@app.post("/api/debug/reset", tags=["debug"])
async def debug_reset() -> Dict[str, Any]:
    metering_engine.reset()
    settlement_engine.reset()
    provider_registry.reset()
    reputation_engine.reset()
    return {"status": "reset", "timestamp": datetime.now(timezone.utc).isoformat()}


def run() -> None:
    import os
    # Allow preview system's PORT env var to override configured port
    port = int(os.getenv("PORT", settings.api_port))
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run()
