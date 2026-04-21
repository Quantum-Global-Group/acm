"""Unit tests for metering, pricing, settlement engines."""
from __future__ import annotations

import pytest

from backend.engines.metering import MeteringEngine, UsageMetrics
from backend.engines.pricing import PricingEngine
from backend.engines.settlement import SettlementEngine


def test_metering_records_and_summary():
    engine = MeteringEngine()
    engine.record_usage(quantity=100, unit_type="image", compute_time_ms=50, tokens_used=1000)
    engine.record_usage(quantity=50, unit_type="image", compute_time_ms=10, tokens_used=200)
    summary = engine.get_summary()
    assert summary["record_count"] == 2
    assert summary["total_units"] == 150
    assert summary["unit_types"]["image"] == 150
    assert summary["total_tokens"] == 1200


def test_metering_reset_clears():
    engine = MeteringEngine()
    engine.record_usage(quantity=1, unit_type="x", compute_time_ms=1)
    engine.reset()
    assert engine.get_summary()["record_count"] == 0


def test_pricing_basic_cost():
    usage = UsageMetrics(quantity=100, unit_type="image", compute_time_ms=50, tokens_used=0)
    cost = PricingEngine.calculate_cost(usage)
    # 100 * 0.0001 = 0.01 baseline, no token / overflow add
    assert cost == pytest.approx(0.01, rel=1e-6)


def test_pricing_unit_price_under_ceiling():
    usage = UsageMetrics(quantity=100, unit_type="image", compute_time_ms=50, tokens_used=1000)
    unit_price = PricingEngine.get_unit_price(usage)
    assert unit_price <= 0.01


def test_pricing_enforce_ceiling_raises():
    # Construct usage that would over-price by inflating tokens.
    usage = UsageMetrics(quantity=1, unit_type="x", compute_time_ms=0, tokens_used=20_000)
    # 1 * 0.0001 + 20000 * 0.000001 = 0.0001 + 0.02 = 0.0201/unit > 0.01
    with pytest.raises(AssertionError):
        PricingEngine.enforce_max_unit_price(usage)


def test_pricing_validate_price_against_max():
    usage = UsageMetrics(quantity=100, unit_type="image", compute_time_ms=0, tokens_used=0)
    max_price = 0.05
    ok, cost = PricingEngine.validate_price(usage, max_price_usdc=max_price)
    assert ok and cost <= max_price


@pytest.mark.asyncio
async def test_settlement_simulated_payment_records():
    engine = SettlementEngine()
    tx = await engine.settle_payment("0x" + "a" * 40, "0x" + "b" * 40, 0.01, "task-1")
    assert tx is not None and tx.startswith("0x")


@pytest.mark.asyncio
async def test_settlement_records_match_request():
    engine = SettlementEngine()
    consumer = "0x" + "1" * 40
    provider = "0x" + "2" * 40
    tx = await engine.settle_payment(consumer, provider, 0.005, "task-A")
    assert tx is not None and tx.startswith("0x")
    summary = engine.get_settlement_summary()
    assert summary["transaction_count"] == 1
    assert summary["total_settled"] == pytest.approx(0.005)
    assert summary["mode"] == "simulate"


@pytest.mark.asyncio
async def test_settlement_rejects_self_payment():
    engine = SettlementEngine()
    addr = "0x" + "3" * 40
    tx = await engine.settle_payment(addr, addr, 0.01, "task-self")
    assert tx is None
    assert engine.get_settlement_summary()["transaction_count"] == 0
