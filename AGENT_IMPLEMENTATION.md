# Agent Implementation Guide: Autonomous Agents
## Build Consumer & Provider Agents

This guide walks you through building autonomous AI agents that make independent payment and execution decisions.

---

## 🎯 What You'll Build

By the end of this guide:
- ✅ Consumer agent that autonomously requests compute
- ✅ Provider agent that autonomously provides services
- ✅ Wallet management for both agents
- ✅ Independent decision-making logic
- ✅ Real-time payment verification

---

## 📋 Prerequisites

Completed:
- ✅ GETTING_STARTED.md
- ✅ SMART_CONTRACT_GUIDE.md (contract deployed)
- ✅ BACKEND_SETUP.md (server running)
- ✅ Backend running on http://localhost:8000

---

## 🤖 Step 1: Create Consumer Agent

Create `backend/agents/consumer.py`:

```python
"""
Consumer Agent
Autonomous agent that requests compute from providers
Makes independent payment and purchasing decisions
"""
import asyncio
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
import httpx

from backend.config import settings


class ConsumerAgent:
    """
    Autonomous consumer agent
    - Manages wallet and USDC balance
    - Decides what compute to request
    - Negotiates pricing
    - Makes payment decisions
    """
    
    def __init__(
        self,
        agent_id: str,
        wallet_address: str,
        initial_balance_usdc: float,
        api_endpoint: str = "http://localhost:8000"
    ):
        """
        Initialize consumer agent
        
        Args:
            agent_id: Unique identifier for agent
            wallet_address: Arc wallet address
            initial_balance_usdc: Starting USDC balance
            api_endpoint: Backend API endpoint
        """
        self.agent_id = agent_id
        self.wallet_address = wallet_address
        self.balance_usdc = initial_balance_usdc
        self.api_endpoint = api_endpoint
        
        # Track completed purchases
        self.purchases: List[Dict[str, Any]] = []
        self.total_spent = 0.0
        self.successful_requests = 0
        self.failed_requests = 0
        
        self.client = httpx.AsyncClient(timeout=10.0)
        
        print(f"✓ Consumer agent initialized: {self.agent_id}")
        print(f"  Wallet: {wallet_address[:16]}...")
        print(f"  Balance: ${initial_balance_usdc:.2f} USDC")
    
    async def decide_purchase(
        self,
        provider_agent_id: str,
        compute_type: str,
        units: int
    ) -> bool:
        """
        Autonomous decision: Should we request compute from this provider?
        
        Decision logic:
        1. Do we have sufficient balance?
        2. Is the provider trusted?
        3. Is the price acceptable?
        
        Args:
            provider_agent_id: ID of provider agent
            compute_type: Type of compute requested
            units: Number of units to request
            
        Returns:
            True if we decide to purchase, False otherwise
        """
        # Estimate cost (base: $0.0001 per unit)
        estimated_cost = units * 0.0001
        
        # Decision 1: Balance check
        if self.balance_usdc < estimated_cost:
            print(f"  ❌ {self.agent_id}: Insufficient balance")
            return False
        
        # Decision 2: Trust (in real system, check provider reputation)
        # For demo: accept all providers
        
        # Decision 3: Price check
        max_acceptable_price = 0.01 * units  # Max $0.01 per unit
        if estimated_cost > max_acceptable_price:
            print(f"  ❌ {self.agent_id}: Price too high")
            return False
        
        return True
    
    async def request_compute(
        self,
        provider_address: str,
        compute_type: str,
        units: int,
        max_price_usdc: float
    ) -> Optional[Dict[str, Any]]:
        """
        Request compute from provider
        Autonomous agent makes request if conditions are met
        
        Args:
            provider_address: Arc address of provider
            compute_type: Type of compute
            units: Number of units
            max_price_usdc: Maximum price willing to pay
            
        Returns:
            Result from provider, or None if request failed
        """
        # Generate unique task ID
        task_id = f"task-{uuid.uuid4().hex[:8]}"
        
        print(f"\n📤 {self.agent_id} requesting compute")
        print(f"   Task: {task_id}")
        print(f"   Provider: {provider_address[:16]}...")
        print(f"   Units: {units}")
        print(f"   Max price: ${max_price_usdc:.6f}")
        
        try:
            # Check balance before requesting
            if self.balance_usdc < max_price_usdc:
                print(f"   ❌ Insufficient balance: ${self.balance_usdc:.2f} < ${max_price_usdc:.6f}")
                self.failed_requests += 1
                return None
            
            # Prepare request
            request_data = {
                "task_id": task_id,
                "task_type": compute_type,
                "consumer_address": self.wallet_address,
                "provider_address": provider_address,
                "estimated_units": units,
                "max_price_usdc": max_price_usdc,
                "params": {
                    "model": "resnet50",
                    "batch_size": units
                }
            }
            
            # Simulate x402 payment header (in real: signed payment proof)
            x402_header = f"Bearer {uuid.uuid4().hex}"
            
            # Send request to backend
            response = await self.client.post(
                f"{self.api_endpoint}/api/compute",
                json=request_data,
                headers={"X-402-Payment": x402_header}
            )
            
            if response.status_code != 200:
                print(f"   ❌ Request failed: {response.status_code}")
                self.failed_requests += 1
                return None
            
            result = response.json()
            
            # Extract cost
            actual_cost = result["actual_cost_usdc"]
            tx_hash = result["arc_tx_hash"]
            
            # Update balance (deduct payment)
            self.balance_usdc -= actual_cost
            self.total_spent += actual_cost
            self.successful_requests += 1
            
            # Record purchase
            purchase = {
                "task_id": task_id,
                "provider": provider_address,
                "units": units,
                "cost": actual_cost,
                "tx_hash": tx_hash,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success"
            }
            self.purchases.append(purchase)
            
            print(f"   ✅ Success!")
            print(f"      Cost: ${actual_cost:.6f} USDC")
            print(f"      Remaining: ${self.balance_usdc:.6f} USDC")
            print(f"      TX: {tx_hash[:16]}...")
            
            return result
        
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            self.failed_requests += 1
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "agent_id": self.agent_id,
            "wallet": self.wallet_address,
            "balance": self.balance_usdc,
            "total_spent": self.total_spent,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "purchase_count": len(self.purchases),
        }
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Example usage
async def example_consumer():
    """Example consumer agent usage"""
    agent = ConsumerAgent(
        agent_id="consumer-1",
        wallet_address="0x1234567890123456789012345678901234567890",
        initial_balance_usdc=5.0
    )
    
    # Make some requests
    for i in range(3):
        provider = f"0x{i:040x}"
        result = await agent.request_compute(
            provider_address=provider,
            compute_type="image_classification",
            units=100,
            max_price_usdc=0.01
        )
        await asyncio.sleep(0.1)
    
    print(f"\nFinal status: {agent.get_status()}")
    await agent.close()


if __name__ == "__main__":
    asyncio.run(example_consumer())
```

---

## 👨‍💼 Step 2: Create Provider Agent

Create `backend/agents/provider.py`:

```python
"""
Provider Agent
Autonomous agent that provides compute services
Decides what work to accept and pricing
"""
import asyncio
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class ProviderWorkloadType(str, Enum):
    """Types of work provider can handle"""
    IMAGE_CLASSIFICATION = "image_classification"
    DATA_PROCESSING = "data_processing"
    MODEL_INFERENCE = "model_inference"


class ProviderAgent:
    """
    Autonomous provider agent
    - Manages wallet and USDC balance (earned as revenue)
    - Decides what compute to provide
    - Sets pricing
    - Executes work
    """
    
    def __init__(
        self,
        agent_id: str,
        wallet_address: str,
        supported_tasks: List[str],
        base_unit_price: float = 0.0001
    ):
        """
        Initialize provider agent
        
        Args:
            agent_id: Unique identifier
            wallet_address: Arc wallet address
            supported_tasks: List of compute tasks this provider supports
            base_unit_price: Base price per unit
        """
        self.agent_id = agent_id
        self.wallet_address = wallet_address
        self.supported_tasks = supported_tasks
        self.base_unit_price = base_unit_price
        
        # Track work completed
        self.balance_usdc = 0.0  # Revenue earned
        self.completed_work: List[Dict[str, Any]] = []
        self.total_units_processed = 0
        self.total_revenue = 0.0
        
        print(f"✓ Provider agent initialized: {self.agent_id}")
        print(f"  Wallet: {wallet_address[:16]}...")
        print(f"  Supported tasks: {', '.join(supported_tasks)}")
        print(f"  Base price: ${base_unit_price:.6f} per unit")
    
    def can_handle_task(self, task_type: str) -> bool:
        """
        Check if provider can handle this task type
        
        Args:
            task_type: Type of compute task
            
        Returns:
            True if provider supports this task
        """
        return task_type in self.supported_tasks
    
    async def decide_accept_work(
        self,
        consumer_address: str,
        task_type: str,
        units: int,
        offered_price_usdc: float
    ) -> bool:
        """
        Autonomous decision: Should we accept this work?
        
        Decision logic:
        1. Do we support this task type?
        2. Is the price acceptable?
        3. Do we have capacity?
        
        Args:
            consumer_address: Consumer's address
            task_type: Type of work
            units: Number of units
            offered_price_usdc: Price offered
            
        Returns:
            True if we accept, False otherwise
        """
        # Decision 1: Task support
        if not self.can_handle_task(task_type):
            print(f"  ❌ {self.agent_id}: Task type not supported")
            return False
        
        # Decision 2: Price check
        # Minimum: our base price (no loss-making)
        min_acceptable = units * self.base_unit_price
        if offered_price_usdc < min_acceptable:
            print(f"  ❌ {self.agent_id}: Price too low (${offered_price_usdc:.6f} < ${min_acceptable:.6f})")
            return False
        
        # Decision 3: Capacity (always accept in demo)
        
        return True
    
    async def execute_work(
        self,
        task_id: str,
        task_type: str,
        units: int,
        params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute compute work for consumer
        
        Args:
            task_id: Unique task identifier
            task_type: Type of compute
            units: Number of units to process
            params: Task parameters
            
        Returns:
            Dictionary with work results
        """
        print(f"\n⚙️  {self.agent_id} executing work")
        print(f"   Task: {task_id}")
        print(f"   Type: {task_type}")
        print(f"   Units: {units}")
        
        # Simulate compute work
        start_time = datetime.utcnow()
        compute_time_ms = int((units / 100) * 50 + 10)  # Estimate 50ms per 100 units
        
        # Simulate async processing
        await asyncio.sleep(compute_time_ms / 1000)
        
        end_time = datetime.utcnow()
        actual_compute_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Generate results
        results = {
            "task_id": task_id,
            "status": "success",
            "units_processed": units,
            "compute_time_ms": actual_compute_ms,
            "data": [{"unit": i, "result": "processed"} for i in range(min(5, units))]
        }
        
        # Record work
        work = {
            "task_id": task_id,
            "type": task_type,
            "units": units,
            "compute_time_ms": actual_compute_ms,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "completed"
        }
        self.completed_work.append(work)
        self.total_units_processed += units
        
        print(f"   ✅ Work completed")
        print(f"      Time: {actual_compute_ms}ms")
        print(f"      Units: {units}")
        
        return results
    
    def receive_payment(
        self,
        amount_usdc: float,
        task_id: str,
        consumer_address: str
    ):
        """
        Record payment received for work
        
        Args:
            amount_usdc: Amount paid
            task_id: Task identifier
            consumer_address: Who paid us
        """
        self.balance_usdc += amount_usdc
        self.total_revenue += amount_usdc
        
        print(f"💰 {self.agent_id} received payment")
        print(f"   Amount: ${amount_usdc:.6f} USDC")
        print(f"   From: {consumer_address[:16]}...")
        print(f"   New balance: ${self.balance_usdc:.6f} USDC")
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "agent_id": self.agent_id,
            "wallet": self.wallet_address,
            "balance": self.balance_usdc,
            "total_revenue": self.total_revenue,
            "total_units_processed": self.total_units_processed,
            "work_completed": len(self.completed_work),
            "avg_revenue_per_unit": self.total_revenue / self.total_units_processed if self.total_units_processed > 0 else 0,
        }


# Example usage
async def example_provider():
    """Example provider agent usage"""
    agent = ProviderAgent(
        agent_id="provider-1",
        wallet_address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
        supported_tasks=["image_classification", "data_processing"]
    )
    
    # Accept and execute some work
    for i in range(3):
        task_id = f"task-{i}"
        result = await agent.execute_work(
            task_id=task_id,
            task_type="image_classification",
            units=100
        )
        
        # Simulate payment received
        payment = 0.01  # $0.01 for this task
        agent.receive_payment(
            amount_usdc=payment,
            task_id=task_id,
            consumer_address=f"0x{i:040x}"
        )
        
        await asyncio.sleep(0.1)
    
    print(f"\nFinal status: {agent.get_status()}")


if __name__ == "__main__":
    asyncio.run(example_provider())
```

---

## 🔗 Step 3: Create Agent Manager

Create `backend/agents/manager.py`:

```python
"""
Agent Manager
Manages multiple consumer and provider agents
Orchestrates agent interactions
"""
import asyncio
from typing import Dict, List, Tuple
from datetime import datetime
import random

from backend.agents.consumer import ConsumerAgent
from backend.agents.provider import ProviderAgent


class AgentManager:
    """
    Manages fleet of consumer and provider agents
    Coordinates marketplace interactions
    """
    
    def __init__(self, api_endpoint: str = "http://localhost:8000"):
        """Initialize manager"""
        self.api_endpoint = api_endpoint
        self.consumers: Dict[str, ConsumerAgent] = {}
        self.providers: Dict[str, ProviderAgent] = {}
        self.interaction_count = 0
    
    def add_consumer(
        self,
        agent_id: str,
        wallet_address: str,
        initial_balance: float
    ) -> ConsumerAgent:
        """Add consumer agent"""
        agent = ConsumerAgent(
            agent_id=agent_id,
            wallet_address=wallet_address,
            initial_balance_usdc=initial_balance,
            api_endpoint=self.api_endpoint
        )
        self.consumers[agent_id] = agent
        return agent
    
    def add_provider(
        self,
        agent_id: str,
        wallet_address: str,
        supported_tasks: List[str]
    ) -> ProviderAgent:
        """Add provider agent"""
        agent = ProviderAgent(
            agent_id=agent_id,
            wallet_address=wallet_address,
            supported_tasks=supported_tasks
        )
        self.providers[agent_id] = agent
        return agent
    
    async def marketplace_simulation(
        self,
        num_transactions: int = 10,
        units_per_transaction: int = 100
    ):
        """
        Simulate marketplace: consumers request, providers execute
        
        Args:
            num_transactions: Number of transactions to execute
            units_per_transaction: Units per request
        """
        print(f"\n{'='*60}")
        print(f"MARKETPLACE SIMULATION")
        print(f"{'='*60}")
        print(f"Consumers: {len(self.consumers)}")
        print(f"Providers: {len(self.providers)}")
        print(f"Transactions: {num_transactions}")
        print(f"{'='*60}\n")
        
        for i in range(num_transactions):
            # Pick random consumer and provider
            consumer_id = random.choice(list(self.consumers.keys()))
            provider_id = random.choice(list(self.providers.keys()))
            
            consumer = self.consumers[consumer_id]
            provider = self.providers[provider_id]
            
            # Consumer decides to purchase
            should_purchase = await consumer.decide_purchase(
                provider_id,
                "image_classification",
                units_per_transaction
            )
            
            if should_purchase:
                # Consumer requests compute
                max_price = units_per_transaction * 0.0001
                result = await consumer.request_compute(
                    provider_address=provider.wallet_address,
                    compute_type="image_classification",
                    units=units_per_transaction,
                    max_price_usdc=max_price
                )
                
                if result:
                    self.interaction_count += 1
                    
                    # Provider executes work
                    task_id = result["task_id"]
                    work = await provider.execute_work(
                        task_id=task_id,
                        task_type="image_classification",
                        units=units_per_transaction
                    )
                    
                    # Provider receives payment
                    actual_cost = result["actual_cost_usdc"]
                    provider.receive_payment(
                        amount_usdc=actual_cost,
                        task_id=task_id,
                        consumer_address=consumer.wallet_address
                    )
            
            # Small delay between transactions
            await asyncio.sleep(0.05)
        
        self._print_summary()
    
    def _print_summary(self):
        """Print marketplace summary"""
        print(f"\n{'='*60}")
        print(f"MARKETPLACE SUMMARY")
        print(f"{'='*60}\n")
        
        print("CONSUMERS:")
        for agent_id, agent in self.consumers.items():
            status = agent.get_status()
            print(f"  {agent_id}:")
            print(f"    Balance: ${status['balance']:.2f}")
            print(f"    Spent: ${status['total_spent']:.2f}")
            print(f"    Requests: {status['successful_requests']} success, {status['failed_requests']} failed")
        
        print("\nPROVIDERS:")
        total_provider_revenue = 0.0
        for agent_id, agent in self.providers.items():
            status = agent.get_status()
            total_provider_revenue += status['balance']
            print(f"  {agent_id}:")
            print(f"    Revenue: ${status['balance']:.2f}")
            print(f"    Units processed: {status['total_units_processed']}")
            print(f"    Avg revenue per unit: ${status['avg_revenue_per_unit']:.6f}")
        
        print(f"\nTOTAL INTERACTIONS: {self.interaction_count}")
        print(f"TOTAL PROVIDER REVENUE: ${total_provider_revenue:.2f}")
        print(f"{'='*60}\n")
    
    async def close(self):
        """Close all agent connections"""
        for agent in self.consumers.values():
            await agent.close()


# Example usage
async def main():
    """Run example marketplace simulation"""
    manager = AgentManager()
    
    # Create agents
    # Consumers
    manager.add_consumer("consumer-1", "0x1111111111111111111111111111111111111111", 5.0)
    manager.add_consumer("consumer-2", "0x2222222222222222222222222222222222222222", 5.0)
    
    # Providers
    manager.add_provider("provider-1", "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", ["image_classification"])
    manager.add_provider("provider-2", "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", ["image_classification", "data_processing"])
    
    # Run simulation
    await manager.marketplace_simulation(num_transactions=10, units_per_transaction=100)
    
    # Cleanup
    await manager.close()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📝 Step 4: Update Agents __init__.py

Create `backend/agents/__init__.py`:

```python
"""
Agent module exports
"""
from backend.agents.consumer import ConsumerAgent
from backend.agents.provider import ProviderAgent
from backend.agents.manager import AgentManager

__all__ = ["ConsumerAgent", "ProviderAgent", "AgentManager"]
```

---

## 🧪 Step 5: Create Agent Tests

Create `tests/test_agents.py`:

```python
"""
Tests for agent implementations
"""
import pytest
import asyncio
from backend.agents.consumer import ConsumerAgent
from backend.agents.provider import ProviderAgent


@pytest.mark.asyncio
async def test_consumer_agent_creation():
    """Test consumer agent creation"""
    agent = ConsumerAgent(
        agent_id="test-consumer",
        wallet_address="0x123...",
        initial_balance_usdc=5.0
    )
    
    status = agent.get_status()
    assert status["agent_id"] == "test-consumer"
    assert status["balance"] == 5.0
    assert status["successful_requests"] == 0
    
    await agent.close()


@pytest.mark.asyncio
async def test_consumer_decides_purchase():
    """Test consumer purchase decision"""
    agent = ConsumerAgent(
        agent_id="test-consumer",
        wallet_address="0x123...",
        initial_balance_usdc=5.0
    )
    
    # Should accept (sufficient balance)
    result = await agent.decide_purchase(
        provider_agent_id="provider-1",
        compute_type="image_classification",
        units=100
    )
    assert result == True
    
    # Should reject (insufficient balance)
    agent.balance_usdc = 0.001
    result = await agent.decide_purchase(
        provider_agent_id="provider-1",
        compute_type="image_classification",
        units=100
    )
    assert result == False
    
    await agent.close()


@pytest.mark.asyncio
async def test_provider_agent_creation():
    """Test provider agent creation"""
    agent = ProviderAgent(
        agent_id="test-provider",
        wallet_address="0xabc...",
        supported_tasks=["image_classification"]
    )
    
    status = agent.get_status()
    assert status["agent_id"] == "test-provider"
    assert status["balance"] == 0.0
    assert status["work_completed"] == 0


@pytest.mark.asyncio
async def test_provider_executes_work():
    """Test provider work execution"""
    agent = ProviderAgent(
        agent_id="test-provider",
        wallet_address="0xabc...",
        supported_tasks=["image_classification"]
    )
    
    result = await agent.execute_work(
        task_id="task-1",
        task_type="image_classification",
        units=100
    )
    
    assert result["status"] == "success"
    assert result["units_processed"] == 100
    assert agent.total_units_processed == 100


@pytest.mark.asyncio
async def test_provider_receives_payment():
    """Test provider payment receipt"""
    agent = ProviderAgent(
        agent_id="test-provider",
        wallet_address="0xabc...",
        supported_tasks=["image_classification"]
    )
    
    agent.receive_payment(
        amount_usdc=0.01,
        task_id="task-1",
        consumer_address="0x123..."
    )
    
    assert agent.balance_usdc == 0.01
    assert agent.total_revenue == 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## ✅ Step 6: Test Agents

```bash
# Run agent tests
pytest tests/test_agents.py -v

# Run example consumer
python -m backend.agents.consumer

# Run example provider
python -m backend.agents.provider

# Run agent manager simulation
python -m backend.agents.manager
```

---

## 🎯 Key Features

### Consumer Agent Autonomy
- ✅ Checks balance before purchasing
- ✅ Validates pricing
- ✅ Makes independent requests
- ✅ Tracks spending

### Provider Agent Autonomy
- ✅ Decides what tasks to support
- ✅ Validates offered price
- ✅ Executes work autonomously
- ✅ Tracks revenue

### Wallet Management
- ✅ Consumer tracks spending
- ✅ Provider tracks earnings
- ✅ Real-time balance updates
- ✅ Transaction history

---

## 📋 Verification Checklist

- [ ] Consumer agent created and imports correctly
- [ ] Provider agent created and imports correctly
- [ ] Agent manager created
- [ ] Consumer decision logic works
- [ ] Provider work execution works
- [ ] Payment receipt updates balances
- [ ] Agent tests pass
- [ ] Example runs without errors

---

## 🚨 Troubleshooting

### "httpx.ConnectError" when testing
```bash
# Make sure backend is running:
python -m backend.main
```

### "asyncio.TimeoutError"
- Increase timeout in consumer agent
- Check backend is responding

### Agents not connecting
- Verify API endpoint in agent
- Check CORS settings if needed

---

## 📚 Next Steps

1. **Integration Guide** — Wire agents to backend
2. **Testing Guide** — Full integration tests
3. **Demo Execution** — Generate 50+ transactions

---

## ✅ Completion

**Agents successfully implemented! 🎉**

Your agents are now:
- ✅ Autonomous and decision-making
- ✅ Making independent requests
- ✅ Executing work
- ✅ Managing balances
- ✅ Ready for marketplace integration

**Next: Open INTEGRATION_GUIDE.md to connect agents to backend!**
