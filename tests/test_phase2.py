"""Phase 2 tests — batch endpoint + SLA enforcement + provider dispatch."""
from __future__ import annotations

from typing import Any, Dict

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from backend.engines import execution as execution_engine
from backend.engines.execution import volume_discount_rate
from backend.engines.metering import metering_engine
from backend.engines.registry import provider_registry
from backend.engines.reputation import reputation_engine
from backend.engines.settlement import settlement_engine
from backend.main import app


@pytest.fixture
async def client():
    metering_engine.reset()
    settlement_engine.reset()
    provider_registry.reset()
    reputation_engine.reset()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ------------------------------------------------------- volume discount curve


def test_volume_discount_tiers():
    assert volume_discount_rate(1) == 0.0
    assert volume_discount_rate(9) == 0.0
    assert volume_discount_rate(10) == 0.05
    assert volume_discount_rate(49) == 0.05
    assert volume_discount_rate(50) == 0.10
    assert volume_discount_rate(99) == 0.10
    assert volume_discount_rate(100) == 0.15
    assert volume_discount_rate(500) == 0.15


# ----------------------------------------------------------------------- batch


def _job(i: int, units: int = 10, max_price: float = 0.01, task_type: str = "image_classification") -> Dict[str, Any]:
    return {
        "task_id": f"batch-job-{i}",
        "task_type": task_type,
        "consumer_address": "0x" + "1" * 40,
        "provider_address": "0x" + "2" * 40,
        "estimated_units": units,
        "max_price_usdc": max_price,
    }


@pytest.mark.asyncio
async def test_batch_small_applies_no_discount(client):
    r = await client.post(
        "/api/compute/batch",
        json={"jobs": [_job(i) for i in range(5)]},
        headers={"X-402-Payment": "proof"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["job_count"] == 5
    assert body["successful_count"] == 5
    assert body["discount_rate"] == 0.0
    assert body["savings_usdc"] == 0.0


@pytest.mark.asyncio
async def test_batch_large_applies_volume_discount(client):
    job_count = 50
    r = await client.post(
        "/api/compute/batch",
        json={"jobs": [_job(i) for i in range(job_count)]},
        headers={"X-402-Payment": "proof"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["job_count"] == job_count
    assert body["successful_count"] == job_count
    assert body["discount_rate"] == 0.10
    assert body["gross_cost_usdc"] > body["total_cost_usdc"]
    assert body["savings_usdc"] == pytest.approx(
        body["gross_cost_usdc"] - body["total_cost_usdc"], abs=1e-9
    )


@pytest.mark.asyncio
async def test_batch_requires_x402(client):
    r = await client.post(
        "/api/compute/batch",
        json={"jobs": [_job(0)]},
    )
    assert r.status_code == 402


@pytest.mark.asyncio
async def test_batch_partial_failures_returned_inline(client):
    # Mix a job that will succeed with one that breaks max_price_usdc.
    jobs = [
        _job(0),
        _job(1, max_price=0.00000001),  # below the baseline cost → will fail
        _job(2),
    ]
    r = await client.post(
        "/api/compute/batch",
        json={"jobs": jobs, "allow_partial": True},
        headers={"X-402-Payment": "proof"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["successful_count"] == 2
    assert body["failed_count"] == 1
    statuses = [r["status"] for r in body["results"]]
    assert statuses.count("failed") == 1


@pytest.mark.asyncio
async def test_batch_allow_partial_false_aborts_on_first_failure(client):
    jobs = [
        _job(0, max_price=0.00000001),  # will fail first
        _job(1),
        _job(2),
    ]
    r = await client.post(
        "/api/compute/batch",
        json={"jobs": jobs, "allow_partial": False},
        headers={"X-402-Payment": "proof"},
    )
    assert r.status_code == 400


# ------------------------------------------------------------------- SLA gate


@pytest.mark.asyncio
async def test_sla_breach_returns_408(client, monkeypatch):
    """Force execute_job to see a very tight deadline with a slow simulated path."""
    import asyncio
    original = execution_engine.asyncio.sleep

    async def slow_sleep(_):
        await original(0.25)  # 250ms — longer than the 50ms max_latency_ms below

    monkeypatch.setattr(execution_engine.asyncio, "sleep", slow_sleep)

    r = await client.post(
        "/api/compute",
        json={
            **_job(0),
            "max_latency_ms": 50,
        },
        headers={"X-402-Payment": "proof"},
    )
    assert r.status_code == 408, r.text


@pytest.mark.asyncio
async def test_sla_within_deadline_succeeds(client):
    r = await client.post(
        "/api/compute",
        json={
            **_job(0),
            "max_latency_ms": 10_000,
        },
        headers={"X-402-Payment": "proof"},
    )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_sla_breach_records_reputation_failure(client, monkeypatch):
    import asyncio
    original = execution_engine.asyncio.sleep

    async def slow_sleep(_):
        await original(0.25)

    monkeypatch.setattr(execution_engine.asyncio, "sleep", slow_sleep)

    provider_addr = "0x" + "D" * 40
    await client.post("/api/providers/register", json={
        "agent_id": "sla-prov",
        "wallet_address": provider_addr,
        "supported_tasks": ["image_classification"],
    })

    r = await client.post(
        "/api/compute",
        json={
            "task_id": "sla-1",
            "task_type": "image_classification",
            "consumer_address": "0x" + "1" * 40,
            "provider_address": provider_addr,
            "estimated_units": 10,
            "max_price_usdc": 0.01,
            "max_latency_ms": 50,
        },
        headers={"X-402-Payment": "proof"},
    )
    assert r.status_code == 408

    listing = (await client.get("/api/providers/sla-prov")).json()
    assert listing["jobs_completed"] == 0
    assert listing["jobs_failed"] == 1
    assert listing["success_rate"] == 0.0


# ---------------------------------------------------------- provider dispatch


@pytest.mark.asyncio
async def test_provider_dispatch_forwards_to_endpoint(monkeypatch, client):
    """When a provider advertises provider_endpoint, backend POSTs to it."""
    dispatched: Dict[str, Any] = {}

    # Build a tiny fake provider app.
    provider_app = FastAPI()

    @provider_app.post("/infer")
    async def infer(body: Dict[str, Any]) -> Dict[str, Any]:
        dispatched["body"] = body
        return {
            "task_id": body["task_id"],
            "result": {"label": "POSITIVE", "score": 0.97},
            "compute_time_ms": 123,
            "tokens_used": 7,
        }

    provider_transport = ASGITransport(app=provider_app)

    # Patch execution engine's HTTP client to hit the in-memory provider app.
    import httpx
    provider_client = httpx.AsyncClient(
        transport=provider_transport, base_url="http://provider-app"
    )

    async def _get_client_stub() -> httpx.AsyncClient:
        return provider_client

    monkeypatch.setattr(execution_engine, "_get_dispatch_client", _get_client_stub)

    # Register the provider pointing at the fake endpoint.
    provider_addr = "0x" + "E" * 40
    await client.post("/api/providers/register", json={
        "agent_id": "dispatch-prov",
        "wallet_address": provider_addr,
        "supported_tasks": ["text_classification"],
        "pricing": {"text_classification": 0.0002},
        "provider_endpoint": "http://provider-app/infer",
    })

    r = await client.post(
        "/api/compute",
        json={
            "task_id": "dispatch-1",
            "task_type": "text_classification",
            "consumer_address": "0x" + "1" * 40,
            "provider_address": provider_addr,
            "estimated_units": 5,
            "max_price_usdc": 0.01,
            "params": {"text": "I love this!"},
        },
        headers={"X-402-Payment": "proof"},
    )
    assert r.status_code == 200, r.text
    body = r.json()

    # Backend received the dispatch, forwarded payload intact.
    assert dispatched["body"]["task_id"] == "dispatch-1"
    assert dispatched["body"]["params"] == {"text": "I love this!"}

    # Result surfaced back through the compute endpoint.
    assert body["result"]["provider_result"] == {"label": "POSITIVE", "score": 0.97}
    # Provider's reported compute_time_ms was used in metering.
    assert body["result"]["compute_time_ms"] == 123
    assert body["result"]["tokens_used"] == 7

    await provider_client.aclose()


@pytest.mark.asyncio
async def test_provider_dispatch_failure_maps_to_502(monkeypatch, client):
    import httpx

    async def _get_client_stub() -> httpx.AsyncClient:
        # Return a client that will always fail connecting.
        return httpx.AsyncClient(base_url="http://127.0.0.1:1")  # closed port

    monkeypatch.setattr(execution_engine, "_get_dispatch_client", _get_client_stub)

    provider_addr = "0x" + "F" * 40
    await client.post("/api/providers/register", json={
        "agent_id": "broken-prov",
        "wallet_address": provider_addr,
        "supported_tasks": ["text_classification"],
        "provider_endpoint": "http://127.0.0.1:1/infer",
    })

    r = await client.post(
        "/api/compute",
        json={
            "task_id": "broken-1",
            "task_type": "text_classification",
            "consumer_address": "0x" + "1" * 40,
            "provider_address": provider_addr,
            "estimated_units": 5,
            "max_price_usdc": 0.01,
        },
        headers={"X-402-Payment": "proof"},
    )
    assert r.status_code == 502

    listing = (await client.get("/api/providers/broken-prov")).json()
    assert listing["jobs_failed"] == 1
