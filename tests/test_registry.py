"""Tests for the provider registry, reputation engine, and smart consumer selection."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from backend.agents.consumer import ConsumerAgent, SelectionStrategy
from backend.engines.metering import metering_engine
from backend.engines.registry import provider_registry
from backend.engines.reputation import reputation_engine
from backend.engines.settlement import settlement_engine
from backend.main import app
from backend.models import ComputeTaskType, ProviderRegistration


@pytest.fixture
async def client():
    metering_engine.reset()
    settlement_engine.reset()
    provider_registry.reset()
    reputation_engine.reset()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# --------------------------------------------------------------------- registry


@pytest.mark.asyncio
async def test_register_and_list_provider(client):
    r = await client.post("/api/providers/register", json={
        "agent_id": "prov-1",
        "wallet_address": "0x" + "a" * 40,
        "supported_tasks": ["image_classification"],
        "pricing": {"image_classification": 0.0002},
        "default_unit_price": 0.0001,
        "name": "GPU A",
    })
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["agent_id"] == "prov-1"
    assert body["pricing"] == {"image_classification": 0.0002}
    assert body["active"] is True
    assert body["reputation_score"] == 0.0

    r = await client.get("/api/providers")
    assert r.status_code == 200
    listing = r.json()
    assert listing["count"] == 1
    assert listing["providers"][0]["agent_id"] == "prov-1"


@pytest.mark.asyncio
async def test_list_filters_by_task_type(client):
    await client.post("/api/providers/register", json={
        "agent_id": "p-img",
        "wallet_address": "0x" + "b" * 40,
        "supported_tasks": ["image_classification"],
    })
    await client.post("/api/providers/register", json={
        "agent_id": "p-txt",
        "wallet_address": "0x" + "c" * 40,
        "supported_tasks": ["text_classification"],
    })

    r = await client.get("/api/providers", params={"task_type": "text_classification"})
    assert r.status_code == 200
    ids = [p["agent_id"] for p in r.json()["providers"]]
    assert ids == ["p-txt"]


@pytest.mark.asyncio
async def test_list_filters_by_max_price(client):
    await client.post("/api/providers/register", json={
        "agent_id": "p-cheap",
        "wallet_address": "0x" + "1" * 40,
        "supported_tasks": ["image_classification"],
        "pricing": {"image_classification": 0.0001},
    })
    await client.post("/api/providers/register", json={
        "agent_id": "p-pricey",
        "wallet_address": "0x" + "2" * 40,
        "supported_tasks": ["image_classification"],
        "pricing": {"image_classification": 0.005},
    })

    r = await client.get("/api/providers", params={
        "task_type": "image_classification",
        "max_price": 0.0002,
    })
    ids = [p["agent_id"] for p in r.json()["providers"]]
    assert ids == ["p-cheap"]


@pytest.mark.asyncio
async def test_deregister_removes_from_active_list(client):
    await client.post("/api/providers/register", json={
        "agent_id": "gone",
        "wallet_address": "0x" + "d" * 40,
        "supported_tasks": ["image_classification"],
    })
    r = await client.delete("/api/providers/gone")
    assert r.status_code == 200

    r = await client.get("/api/providers")
    assert r.json()["count"] == 0

    r = await client.get("/api/providers", params={"include_inactive": True})
    assert r.json()["count"] == 1


@pytest.mark.asyncio
async def test_re_register_preserves_reputation(client):
    registration = ProviderRegistration(
        agent_id="persist",
        wallet_address="0x" + "e" * 40,
        supported_tasks=[ComputeTaskType.IMAGE_CLASSIFICATION],
    )
    provider_registry.register(registration)
    reputation_engine.record_success("persist", latency_ms=50.0)

    # Re-register with different pricing — reputation must not reset.
    r = await client.post("/api/providers/register", json={
        "agent_id": "persist",
        "wallet_address": "0x" + "e" * 40,
        "supported_tasks": ["image_classification"],
        "pricing": {"image_classification": 0.0005},
    })
    assert r.status_code == 201
    assert r.json()["jobs_completed"] == 1


# ----------------------------------------------------- reputation / quality


@pytest.mark.asyncio
async def test_reputation_updates_after_compute(client):
    # Use a valid checksum-friendly address and register it.
    provider_addr = "0x" + "A" * 40
    await client.post("/api/providers/register", json={
        "agent_id": "live-1",
        "wallet_address": provider_addr,
        "supported_tasks": ["image_classification"],
        "pricing": {"image_classification": 0.0001},
    })

    for i in range(3):
        r = await client.post(
            "/api/compute",
            json={
                "task_id": f"rep-{i}",
                "task_type": "image_classification",
                "consumer_address": "0x" + "1" * 40,
                "provider_address": provider_addr,
                "estimated_units": 10,
                "max_price_usdc": 0.01,
            },
            headers={"X-402-Payment": "proof"},
        )
        assert r.status_code == 200, r.text

    r = await client.get("/api/providers/live-1")
    body = r.json()
    assert body["jobs_completed"] == 3
    assert body["jobs_failed"] == 0
    assert body["success_rate"] == 1.0
    assert body["reputation_score"] > 0.0
    assert body["avg_latency_ms"] > 0.0


@pytest.mark.asyncio
async def test_leaderboard_orders_by_score(client):
    # Two providers, one gets more successful jobs → higher reputation.
    await client.post("/api/providers/register", json={
        "agent_id": "fast",
        "wallet_address": "0x" + "A" * 40,
        "supported_tasks": ["image_classification"],
    })
    await client.post("/api/providers/register", json={
        "agent_id": "slow",
        "wallet_address": "0x" + "B" * 40,
        "supported_tasks": ["image_classification"],
    })

    for i in range(5):
        await client.post(
            "/api/compute",
            json={
                "task_id": f"f-{i}",
                "task_type": "image_classification",
                "consumer_address": "0x" + "1" * 40,
                "provider_address": "0x" + "A" * 40,
                "estimated_units": 10,
                "max_price_usdc": 0.01,
            },
            headers={"X-402-Payment": "proof"},
        )
    await client.post(
        "/api/compute",
        json={
            "task_id": "s-1",
            "task_type": "image_classification",
            "consumer_address": "0x" + "1" * 40,
            "provider_address": "0x" + "B" * 40,
            "estimated_units": 10,
            "max_price_usdc": 0.01,
        },
        headers={"X-402-Payment": "proof"},
    )

    r = await client.get("/api/leaderboard")
    lb = r.json()["leaderboard"]
    assert len(lb) == 2
    assert lb[0]["agent_id"] == "fast"
    assert lb[0]["reputation_score"] > lb[1]["reputation_score"]


# ---------------------------------------------------------- provider pricing


@pytest.mark.asyncio
async def test_provider_advertised_price_overrides_default(client):
    # Provider advertises a HIGHER-than-default price; /api/compute should charge that.
    provider_addr = "0x" + "C" * 40
    await client.post("/api/providers/register", json={
        "agent_id": "premium",
        "wallet_address": provider_addr,
        "supported_tasks": ["model_inference"],
        "pricing": {"model_inference": 0.0005},  # 5× global default of 0.0001
    })

    r = await client.post(
        "/api/compute",
        json={
            "task_id": "premium-1",
            "task_type": "model_inference",
            "consumer_address": "0x" + "1" * 40,
            "provider_address": provider_addr,
            "estimated_units": 10,
            "max_price_usdc": 0.01,
        },
        headers={"X-402-Payment": "proof"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    # Base = 10 * 0.0005 = 0.005, plus token_multiplier * 100 tokens = 0.0001 → 0.0051
    assert body["actual_cost_usdc"] == pytest.approx(0.0051, abs=1e-5)


# ------------------------------------------------------- consumer selection


def test_consumer_cheapest_strategy():
    agent = ConsumerAgent(
        agent_id="c1",
        wallet_address="0x" + "1" * 40,
        api_endpoint="http://unused",
    )
    candidates = [
        {"wallet_address": "a", "pricing": {"image_classification": 0.0003}, "reputation_score": 0.9},
        {"wallet_address": "b", "pricing": {"image_classification": 0.0001}, "reputation_score": 0.1},
        {"wallet_address": "c", "pricing": {"image_classification": 0.0002}, "reputation_score": 0.5},
    ]
    chosen = agent.select_provider(
        candidates, ComputeTaskType.IMAGE_CLASSIFICATION, strategy=SelectionStrategy.CHEAPEST
    )
    assert chosen["wallet_address"] == "b"


def test_consumer_most_reputable_strategy():
    agent = ConsumerAgent(
        agent_id="c2",
        wallet_address="0x" + "1" * 40,
        api_endpoint="http://unused",
    )
    candidates = [
        {"wallet_address": "a", "pricing": {"image_classification": 0.0003}, "reputation_score": 0.9},
        {"wallet_address": "b", "pricing": {"image_classification": 0.0001}, "reputation_score": 0.1},
    ]
    chosen = agent.select_provider(
        candidates, ComputeTaskType.IMAGE_CLASSIFICATION, strategy=SelectionStrategy.MOST_REPUTABLE
    )
    assert chosen["wallet_address"] == "a"


def test_consumer_balanced_strategy_prefers_value():
    agent = ConsumerAgent(
        agent_id="c3",
        wallet_address="0x" + "1" * 40,
        api_endpoint="http://unused",
    )
    # 'b' has the best (reputation / price) ratio: 0.8 / 0.0001 = 8000 vs. 0.9 / 0.0003 = 3000.
    candidates = [
        {"wallet_address": "a", "pricing": {"image_classification": 0.0003}, "reputation_score": 0.9},
        {"wallet_address": "b", "pricing": {"image_classification": 0.0001}, "reputation_score": 0.8},
    ]
    chosen = agent.select_provider(
        candidates, ComputeTaskType.IMAGE_CLASSIFICATION, strategy=SelectionStrategy.BALANCED
    )
    assert chosen["wallet_address"] == "b"


def test_consumer_returns_none_on_empty_candidates():
    agent = ConsumerAgent(
        agent_id="c4",
        wallet_address="0x" + "1" * 40,
        api_endpoint="http://unused",
    )
    assert agent.select_provider([], ComputeTaskType.IMAGE_CLASSIFICATION) is None


@pytest.mark.asyncio
async def test_consumer_discover_providers_via_registry(client):
    """Full loop: register → discover from ConsumerAgent → pick."""
    await client.post("/api/providers/register", json={
        "agent_id": "disc-1",
        "wallet_address": "0x" + "A" * 40,
        "supported_tasks": ["embedding_generation"],
        "pricing": {"embedding_generation": 0.0002},
    })

    # Build a ConsumerAgent pointing at the in-process ASGI app.
    agent = ConsumerAgent(
        agent_id="disc-consumer",
        wallet_address="0x" + "1" * 40,
        api_endpoint="http://test",
    )
    # Share the ASGI client so the agent doesn't open a real socket.
    agent._client = client  # type: ignore[attr-defined]

    providers = await agent.discover_providers(task_type=ComputeTaskType.EMBEDDING_GENERATION)
    assert len(providers) == 1
    assert providers[0]["agent_id"] == "disc-1"

    chosen = agent.select_provider(providers, ComputeTaskType.EMBEDDING_GENERATION)
    assert chosen is not None
    assert chosen["wallet_address"] == "0x" + "A" * 40
    # Prevent pytest from closing the shared ASGI client.
    agent._client = None  # type: ignore[attr-defined]
