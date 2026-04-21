"""Performance test — confirms a 50+ transaction run completes under tight budgets."""
from __future__ import annotations

import time

import pytest
from httpx import ASGITransport, AsyncClient

from backend.agents.consumer import ConsumerAgent
from backend.agents.manager import AgentManager
from backend.engines.metering import metering_engine
from backend.engines.settlement import settlement_engine
from backend.main import app


class _ASGIConsumer(ConsumerAgent):
    async def _http(self):
        if self._client is None:
            self._client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
        return self._client


@pytest.mark.asyncio
async def test_50_plus_transactions():
    metering_engine.reset()
    settlement_engine.reset()

    manager = AgentManager(api_endpoint="http://test")
    for i in range(2):
        c = _ASGIConsumer(
            agent_id=f"c{i}",
            wallet_address=f"0x{(0xaa + i):040x}",
            api_endpoint="http://test",
            initial_balance_usdc=20.0,
            max_price_per_unit=0.001,
        )
        manager.consumers[c.agent_id] = c
    for i in range(3):
        manager.add_provider(f"p{i}", f"0x{(0xbb + i):040x}", ["image_classification"])

    start = time.time()
    await manager.marketplace_simulation(num_transactions=60, units_per_transaction=100)
    elapsed = time.time() - start
    await manager.close()

    assert manager.interaction_count >= 50, f"only {manager.interaction_count}"
    summary = settlement_engine.get_settlement_summary()
    assert summary["transaction_count"] >= 50
    # Real Arc would be slower; in-process simulate must be quick.
    assert elapsed < 30.0, f"took {elapsed:.2f}s"
    print(f"[perf] {manager.interaction_count} txs in {elapsed:.2f}s "
          f"({manager.interaction_count / elapsed:.1f} tx/s)")
