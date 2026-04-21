"""Integration tests that exercise the FastAPI app via httpx.AsyncClient (no real socket)."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from backend.engines.metering import metering_engine
from backend.engines.settlement import settlement_engine
from backend.main import app


@pytest.fixture
async def client():
    metering_engine.reset()
    settlement_engine.reset()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"


@pytest.mark.asyncio
async def test_compute_requires_x402(client):
    r = await client.post("/api/compute", json={
        "task_id": "no-pay",
        "task_type": "image_classification",
        "consumer_address": "0x" + "1" * 40,
        "provider_address": "0x" + "2" * 40,
        "estimated_units": 10,
        "max_price_usdc": 0.01,
    })
    assert r.status_code == 402


@pytest.mark.asyncio
async def test_compute_succeeds_with_x402(client):
    r = await client.post(
        "/api/compute",
        json={
            "task_id": "ok-1",
            "task_type": "image_classification",
            "consumer_address": "0x" + "1" * 40,
            "provider_address": "0x" + "2" * 40,
            "estimated_units": 100,
            "max_price_usdc": 0.05,
        },
        headers={"X-402-Payment": "proof"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "success"
    assert body["arc_tx_hash"].startswith("0x")
    assert body["actual_cost_usdc"] > 0


@pytest.mark.asyncio
async def test_compute_rejects_overpriced(client):
    # max_price_usdc deliberately well below baseline cost (100 * 0.0001 + 1000 tokens cost)
    r = await client.post(
        "/api/compute",
        json={
            "task_id": "expensive-1",
            "task_type": "image_classification",
            "consumer_address": "0x" + "1" * 40,
            "provider_address": "0x" + "2" * 40,
            "estimated_units": 100,
            "max_price_usdc": 0.0001,
        },
        headers={"X-402-Payment": "proof"},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_metrics_grow_with_requests(client):
    for i in range(5):
        await client.post(
            "/api/compute",
            json={
                "task_id": f"m-{i}",
                "task_type": "image_classification",
                "consumer_address": "0x" + "1" * 40,
                "provider_address": "0x" + "2" * 40,
                "estimated_units": 10,
                "max_price_usdc": 0.01,
            },
            headers={"X-402-Payment": "proof"},
        )
    r = await client.get("/api/metrics")
    body = r.json()
    assert body["metering"]["record_count"] == 5
    assert body["settlement"]["transaction_count"] == 5
