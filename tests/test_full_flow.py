"""End-to-end agent → backend → settlement flow using ASGI in-process transport."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from backend.agents.consumer import ConsumerAgent
from backend.agents.manager import AgentManager
from backend.engines.metering import metering_engine
from backend.engines.settlement import settlement_engine
from backend.main import app


class _ASGIPatchedConsumer(ConsumerAgent):
    """ConsumerAgent that talks to the FastAPI app in-process (no real network)."""

    async def _http(self):
        if self._client is None:
            self._client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
            self.api_endpoint = "http://test"
        return self._client


@pytest.fixture
def reset_engines():
    metering_engine.reset()
    settlement_engine.reset()
    yield
    metering_engine.reset()
    settlement_engine.reset()


@pytest.mark.asyncio
async def test_single_consumer_provider(reset_engines):
    manager = AgentManager(api_endpoint="http://test")
    # Replace add_consumer to use our in-process subclass.
    consumer = _ASGIPatchedConsumer(
        agent_id="c1",
        wallet_address="0x" + "1" * 40,
        api_endpoint="http://test",
        initial_balance_usdc=10.0,
        max_price_per_unit=0.001,
    )
    manager.consumers["c1"] = consumer
    provider = manager.add_provider("p1", "0x" + "2" * 40, ["image_classification"])

    await manager.marketplace_simulation(num_transactions=5, units_per_transaction=50)
    await manager.close()

    assert manager.interaction_count == 5
    assert provider.stats.jobs_completed == 5
    assert provider.stats.total_revenue > 0
    assert consumer.stats.successful_requests == 5
    assert consumer.balance_usdc < 10.0


@pytest.mark.asyncio
async def test_unit_price_under_ceiling_in_e2e(reset_engines):
    manager = AgentManager(api_endpoint="http://test")
    consumer = _ASGIPatchedConsumer(
        agent_id="c1",
        wallet_address="0x" + "1" * 40,
        api_endpoint="http://test",
        initial_balance_usdc=10.0,
        max_price_per_unit=0.001,
    )
    manager.consumers["c1"] = consumer
    provider = manager.add_provider("p1", "0x" + "2" * 40, ["image_classification"])

    await manager.marketplace_simulation(num_transactions=10, units_per_transaction=100)
    await manager.close()

    for record in settlement_engine.get_records():
        # Each settlement is for 100 units; per-unit must stay ≤ $0.01.
        unit_price = record["amount_usdc"] / 100
        assert unit_price <= 0.01, f"unit price {unit_price} exceeds ceiling"
