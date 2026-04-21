"""FastAPI entrypoint for the Agent-to-Agent Compute Marketplace backend."""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, Header, HTTPException

from backend.config import settings, validate_settings
from backend.engines.metering import metering_engine
from backend.engines.pricing import pricing_engine
from backend.engines.settlement import settlement_engine
from backend.models import (
    ComputeRequestModel,
    ComputeResultModel,
    HealthCheckModel,
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
    yield


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
            "docs": "/docs",
        },
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
      2. Provider executes task (simulated here).
      3. Metering records actual usage.
      4. Pricing verifies cost ≤ consumer's max_price_usdc and ≤ $0.01/unit.
      5. Settlement issues an Arc transaction (sim or live).
    """
    if not x_402_payment:
        raise HTTPException(status_code=402, detail="Payment Required - x402 header missing")

    # Simulated provider work — production would dispatch to real compute backends.
    await asyncio.sleep(0.01)

    usage = metering_engine.record_usage(
        quantity=request.estimated_units,
        unit_type="query",
        compute_time_ms=50,
        tokens_used=request.estimated_units * 10,
    )

    actual_cost = pricing_engine.calculate_cost(usage)

    try:
        pricing_engine.enforce_max_unit_price(usage)
    except AssertionError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    is_valid, _ = pricing_engine.validate_price(usage, request.max_price_usdc)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"Actual cost ${actual_cost:.6f} exceeds caller max ${request.max_price_usdc:.6f}",
        )

    tx_hash = await settlement_engine.settle_payment(
        consumer_address=request.consumer_address,
        provider_address=request.provider_address,
        amount_usdc=actual_cost,
        task_id=request.task_id,
    )

    if tx_hash is None:
        raise HTTPException(status_code=502, detail="Settlement failed")

    return ComputeResultModel(
        task_id=request.task_id,
        status="success",
        actual_cost_usdc=actual_cost,
        arc_tx_hash=tx_hash,
        result={
            "data": "computed",
            "units_processed": request.estimated_units,
            "task_type": request.task_type.value,
        },
        timestamp=datetime.now(timezone.utc),
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


@app.post("/api/debug/reset", tags=["debug"])
async def debug_reset() -> Dict[str, Any]:
    metering_engine.reset()
    settlement_engine.reset()
    return {"status": "reset", "timestamp": datetime.now(timezone.utc).isoformat()}


def run() -> None:
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run()
