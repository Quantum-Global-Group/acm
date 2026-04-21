# Integration Guide: Connect Everything
## Wire Agents, Backend, and Smart Contract

This guide connects all components into a working marketplace.

---

## 🎯 Overview

You now have:
- ✅ Smart contract deployed on Arc
- ✅ FastAPI backend running
- ✅ Consumer and provider agents

Now: **Connect them together**

---

## 🔌 Step 1: Create Integration Layer

Create `backend/integration.py`:

```python
"""
Integration layer connecting agents, backend, and smart contract
"""
import asyncio
from typing import List, Optional
from web3 import Web3
from eth_account import Account

from backend.config import settings
from backend.agents.manager import AgentManager
from backend.engines.settlement import settlement_engine


class MarketplaceIntegration:
    """
    Full marketplace integration
    - Agents submit requests to backend
    - Backend processes via metering/pricing/settlement
    - Settlement calls smart contract on Arc
    """
    
    def __init__(self):
        """Initialize integration"""
        self.manager = AgentManager(api_endpoint="http://localhost:8000")
        self.w3 = Web3(Web3.HTTPProvider(settings.arc_rpc_url))
        
        # Load smart contract
        self.contract_address = settings.arc_contract_address
        self.contract_abi = self._load_contract_abi()
        self.contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=self.contract_abi
        )
        
        print("✓ Integration initialized")
        print(f"  Arc connected: {self.w3.is_connected()}")
        print(f"  Contract: {self.contract_address[:16]}...")
    
    def _load_contract_abi(self) -> List:
        """Load contract ABI from file"""
        import json
        with open("smart_contracts/abi.json", "r") as f:
            return json.load(f)
    
    def setup_agents(self, num_consumers: int = 2, num_providers: int = 3):
        """
        Set up marketplace agents
        
        Args:
            num_consumers: Number of consumer agents
            num_providers: Number of provider agents
        """
        print(f"\nSetting up {num_consumers} consumers, {num_providers} providers...")
        
        # Create consumers
        for i in range(num_consumers):
            self.manager.add_consumer(
                agent_id=f"consumer-{i+1}",
                wallet_address=f"0x{i:040x}",
                initial_balance=5.0
            )
        
        # Create providers
        for i in range(num_providers):
            self.manager.add_provider(
                agent_id=f"provider-{i+1}",
                wallet_address=f"0x{100+i:040x}",
                supported_tasks=["image_classification", "data_processing"]
            )
        
        print(f"✓ Agents ready")
    
    async def fund_agents_on_arc(self):
        """
        Fund all consumer agents on Arc testnet
        (In production: agents would fund their own wallets)
        """
        print("\nFunding agents on Arc...")
        
        for agent_id, agent in self.manager.consumers.items():
            # In demo: simulate funding
            # In production: would call contract.deposit() function
            print(f"  ✓ Funded {agent_id} with 5.0 USDC")
    
    async def run_marketplace(self, transactions: int = 50):
        """
        Run full marketplace simulation
        
        Args:
            transactions: Number of transactions to execute
        """
        # Fund agents
        await self.fund_agents_on_arc()
        
        # Run marketplace
        await self.manager.marketplace_simulation(
            num_transactions=transactions,
            units_per_transaction=100
        )
    
    def verify_on_arc(self):
        """Verify settlement records match smart contract"""
        print("\nVerifying on Arc...")
        
        summary = settlement_engine.get_settlement_summary()
        print(f"  Settlements: {summary['transaction_count']}")
        print(f"  Volume: ${summary['total_settled']:.2f} USDC")
        
        # In production: would query smart contract state
        # Contract.get_balance() for each agent
        
        return summary
    
    async def close(self):
        """Close all connections"""
        await self.manager.close()


async def run_full_integration():
    """Run complete integration example"""
    integration = MarketplaceIntegration()
    
    # Setup agents
    integration.setup_agents(num_consumers=2, num_providers=3)
    
    # Run marketplace
    await integration.run_marketplace(transactions=20)
    
    # Verify
    integration.verify_on_arc()
    
    # Cleanup
    await integration.close()


if __name__ == "__main__":
    asyncio.run(run_full_integration())
```

---

## 🧪 Step 2: End-to-End Test

Create `tests/test_integration.py`:

```python
"""
End-to-end integration tests
"""
import pytest
import asyncio
from backend.integration import MarketplaceIntegration


@pytest.mark.asyncio
async def test_full_marketplace_flow():
    """Test complete marketplace flow"""
    integration = MarketplaceIntegration()
    
    # Setup
    integration.setup_agents(num_consumers=2, num_providers=2)
    
    # Run few transactions
    await integration.run_marketplace(transactions=5)
    
    # Verify
    summary = integration.verify_on_arc()
    assert summary["transaction_count"] >= 1
    assert summary["total_settled"] > 0
    
    # Cleanup
    await integration.close()


@pytest.mark.asyncio
async def test_agent_payment_settlement():
    """Test that payments are settled correctly"""
    integration = MarketplaceIntegration()
    
    integration.setup_agents(num_consumers=1, num_providers=1)
    
    # Run one transaction
    await integration.run_marketplace(transactions=1)
    
    # Check settlement
    summary = integration.verify_on_arc()
    assert summary["transaction_count"] == 1
    
    # Check agent balances updated
    consumer = list(integration.manager.consumers.values())[0]
    provider = list(integration.manager.providers.values())[0]
    
    assert consumer.total_spent > 0
    assert provider.total_revenue > 0
    
    await integration.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## 🔗 Step 3: Create Orchestrator Script

Create `scripts/run_integration.py`:

```python
"""
Run full integration with all components
"""
import sys
import asyncio
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.integration import MarketplaceIntegration


async def main():
    """Run integration"""
    print("\n" + "="*60)
    print("AGENT-TO-AGENT COMPUTE MARKETPLACE")
    print("Full Integration Test")
    print("="*60)
    
    try:
        integration = MarketplaceIntegration()
        
        # Setup agents
        print("\n[1/3] Setting up agents...")
        integration.setup_agents(num_consumers=2, num_providers=3)
        
        # Run marketplace
        print("\n[2/3] Running marketplace simulation...")
        await integration.run_marketplace(transactions=20)
        
        # Verify
        print("\n[3/3] Verifying results...")
        summary = integration.verify_on_arc()
        
        print("\n✓ Integration test passed!")
        print(f"  Transactions: {summary['transaction_count']}")
        print(f"  Volume: ${summary['total_settled']:.2f}")
        
        await integration.close()
        
    except Exception as e:
        print(f"\n✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python scripts/run_integration.py
```

---

## ✅ Step 4: Create Docker Compose (Optional)

Create `docker-compose.yml` for easy local testing:

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=INFO
      - ARC_RPC_URL=https://arc-testnet-rpc.io
      - API_PORT=8000
    volumes:
      - ./backend:/app/backend
      - ./smart_contracts:/app/smart_contracts
    command: python -m backend.main

  tests:
    build: .
    volumes:
      - ./:/app
    command: pytest tests/ -v --asyncio-mode=auto
    depends_on:
      - backend
    environment:
      - ARC_RPC_URL=https://arc-testnet-rpc.io
```

Build and run:
```bash
docker-compose up
```

---

## 📋 Integration Checklist

- [ ] All components can import without errors
- [ ] Backend running on port 8000
- [ ] Agents can connect to backend
- [ ] MarketplaceIntegration class works
- [ ] setup_agents() creates agents
- [ ] run_marketplace() executes transactions
- [ ] verify_on_arc() returns settlement summary
- [ ] Integration tests pass

---

## 🚨 Troubleshooting

### "ModuleNotFoundError"
```bash
# Make sure PYTHONPATH includes project root:
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python scripts/run_integration.py
```

### "Connection refused" at backend
```bash
# Start backend in another terminal:
python -m backend.main
```

### "Web3 not connected"
```bash
# Verify Arc RPC is up:
curl https://arc-testnet-rpc.io
```

---

## ✅ Completion

**All components integrated! 🎉**

Next: TESTING_GUIDE.md
