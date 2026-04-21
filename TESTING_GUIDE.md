# Testing Guide
## Unit, Integration, and E2E Tests

Comprehensive testing strategy for the marketplace.

---

## 🎯 Testing Strategy

Three levels of testing:
1. **Unit tests** — Individual components (metering, pricing, settlement)
2. **Integration tests** — Components together (agents, backend, contract)
3. **E2E tests** — Full marketplace flow (50+ transactions)

---

## 🧪 Step 1: Unit Tests

Create `tests/test_engines.py`:

```python
"""Unit tests for pricing, metering, settlement engines"""
import pytest
from backend.engines.metering import metering_engine, UsageMetrics
from backend.engines.pricing import pricing_engine
from backend.engines.settlement import settlement_engine


def test_metering_single_record():
    """Test recording single usage"""
    metering_engine.reset()
    metrics = metering_engine.record_usage(100, "image", 50, 1000)
    
    assert metrics.quantity == 100
    summary = metering_engine.get_summary()
    assert summary["total_units"] == 100


def test_pricing_calculation():
    """Test cost calculation"""
    usage = UsageMetrics(quantity=100, unit_type="image", compute_time_ms=50, tokens_used=1000)
    cost = pricing_engine.calculate_cost(usage)
    
    assert cost > 0
    unit_price = pricing_engine.get_unit_price(usage)
    assert unit_price <= 0.01  # Max price limit


def test_pricing_validation():
    """Test price validation"""
    usage = UsageMetrics(quantity=100, unit_type="image", compute_time_ms=50, tokens_used=0)
    cost = pricing_engine.calculate_cost(usage)
    
    is_valid, actual = pricing_engine.validate_price(usage, cost * 1.1)
    assert is_valid


@pytest.mark.asyncio
async def test_settlement_payment():
    """Test payment settlement"""
    settlement_engine.reset()
    tx_hash = await settlement_engine.settle_payment("0x123", "0x456", 0.01, "task-1")
    
    assert tx_hash is not None
    summary = settlement_engine.get_settlement_summary()
    assert summary["transaction_count"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

Run: `pytest tests/test_engines.py -v`

---

## 🔗 Step 2: Integration Tests

Create `tests/test_full_flow.py`:

```python
"""Integration tests for full marketplace flow"""
import pytest
import asyncio
from backend.agents.manager import AgentManager


@pytest.mark.asyncio
async def test_consumer_provider_flow():
    """Test complete consumer-provider interaction"""
    manager = AgentManager()
    
    # Setup agents
    manager.add_consumer("consumer-1", "0x123...", 1.0)
    manager.add_provider("provider-1", "0x456...", ["image_classification"])
    
    # Run interaction
    await manager.marketplace_simulation(num_transactions=3, units_per_transaction=100)
    
    # Verify
    consumer = manager.consumers["consumer-1"]
    provider = manager.providers["provider-1"]
    
    assert consumer.successful_requests > 0
    assert provider.total_revenue > 0
    assert manager.interaction_count > 0
    
    await manager.close()


@pytest.mark.asyncio
async def test_multiple_agents():
    """Test marketplace with multiple agents"""
    manager = AgentManager()
    
    # Create network
    for i in range(3):
        manager.add_consumer(f"consumer-{i}", f"0x{i:040x}", 5.0)
    for i in range(2):
        manager.add_provider(f"provider-{i}", f"0x{100+i:040x}", ["image_classification"])
    
    # Run
    await manager.marketplace_simulation(num_transactions=10, units_per_transaction=100)
    
    # Verify all agents traded
    assert len(manager.consumers) == 3
    assert len(manager.providers) == 2
    assert manager.interaction_count > 0
    
    await manager.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

Run: `pytest tests/test_full_flow.py -v`

---

## 📊 Step 3: Performance Tests

Create `tests/test_performance.py`:

```python
"""Performance and load tests"""
import pytest
import time
import asyncio
from backend.agents.manager import AgentManager


@pytest.mark.asyncio
async def test_50_transactions():
    """Verify 50+ transactions complete successfully"""
    manager = AgentManager()
    
    # Setup agents
    for i in range(2):
        manager.add_consumer(f"consumer-{i}", f"0x{i:040x}", 10.0)
    for i in range(3):
        manager.add_provider(f"provider-{i}", f"0x{100+i:040x}", ["image_classification"])
    
    # Run 50+ transactions
    start = time.time()
    await manager.marketplace_simulation(num_transactions=60, units_per_transaction=100)
    duration = time.time() - start
    
    # Verify
    assert manager.interaction_count >= 50, f"Only {manager.interaction_count} transactions"
    print(f"\n✓ 60 transactions in {duration:.1f}s")
    print(f"  Rate: {manager.interaction_count / duration:.1f} tx/sec")
    
    # Verify economics
    total_volume = sum(c.total_spent for c in manager.consumers.values())
    total_revenue = sum(p.total_revenue for p in manager.providers.values())
    
    assert total_volume > 0
    assert total_revenue == total_volume  # Should match
    
    await manager.close()


@pytest.mark.asyncio
async def test_pricing_accuracy():
    """Verify all transactions ≤ $0.01 per unit"""
    from backend.engines.settlement import settlement_engine
    
    settlement_engine.reset()
    manager = AgentManager()
    
    manager.add_consumer("consumer-1", "0x123...", 10.0)
    manager.add_provider("provider-1", "0xabc...", ["image_classification"])
    
    await manager.marketplace_simulation(num_transactions=10, units_per_transaction=100)
    
    # Check all settlements
    records = settlement_engine.get_records()
    for record in records:
        cost = record["amount"]
        units = 100  # from test params
        unit_price = cost / units
        
        assert unit_price <= 0.01, f"Unit price ${unit_price:.6f} exceeds limit"
    
    await manager.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
```

Run: `pytest tests/test_performance.py -v -s`

---

## 📋 Step 4: Create Test Runner

Create `scripts/run_all_tests.py`:

```bash
#!/bin/bash
# Run all tests with coverage

echo "======================================"
echo "Running All Tests"
echo "======================================"

echo "\n[1/4] Unit tests..."
pytest tests/test_engines.py tests/test_agents.py -v

echo "\n[2/4] Integration tests..."
pytest tests/test_integration.py tests/test_full_flow.py -v

echo "\n[3/4] Performance tests..."
pytest tests/test_performance.py -v -s

echo "\n[4/4] Coverage report..."
pytest tests/ --cov=backend --cov-report=html

echo "\n✓ All tests complete"
echo "Coverage report: htmlcov/index.html"
```

Make executable:
```bash
chmod +x scripts/run_all_tests.py
python scripts/run_all_tests.py
```

---

## ✅ Testing Checklist

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] 50+ transaction test passes
- [ ] Pricing validation test passes
- [ ] Coverage > 80%
- [ ] No async errors
- [ ] Backend handles concurrent requests

---

## 📚 Next Steps

1. **Deployment Guide** — Deploy to Arc
2. **Demo Execution** — Run full demo
3. **Video Submission** — Record results

---

**✅ Testing complete!**
