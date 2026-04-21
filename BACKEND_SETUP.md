# Backend Setup Guide: FastAPI Server
## Build the Compute Marketplace Backend

This guide walks you through building the FastAPI backend with metering, pricing, and settlement engines.

---

## 🎯 What You'll Build

By the end of this guide:
- ✅ FastAPI server running on port 8000
- ✅ Metering engine tracking compute usage
- ✅ Pricing engine calculating costs (≤ $0.01/unit)
- ✅ Settlement engine orchestrating Arc payments
- ✅ x402-compatible request handler
- ✅ Health checks and metrics endpoints

---

## 📋 Prerequisites

Completed:
- ✅ GETTING_STARTED.md (environment setup)
- ✅ SMART_CONTRACT_GUIDE.md (contract deployed)
- ✅ Contract address in `.env`
- ✅ USDC address in `.env`

---

## 📁 Step 1: Create Backend Structure

### Create directory structure

```bash
# From project root
mkdir -p backend/engines backend/agents
touch backend/__init__.py
touch backend/engines/__init__.py
touch backend/agents/__init__.py
```

### Create main files

```bash
touch backend/main.py
touch backend/models.py
touch backend/config.py
touch backend/engines/metering.py
touch backend/engines/pricing.py
touch backend/engines/settlement.py
touch backend/agents/consumer.py
touch backend/agents/provider.py
```

---

## ⚙️ Step 2: Configuration Module

Create `backend/config.py`:

```python
"""
Configuration for the backend
"""
import os
from typing import Optional
from pydantic import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # API Configuration
    api_title: str = "Agent-to-Agent Compute Marketplace"
    api_version: str = "1.0.0"
    api_host: str = "0.0.0.0"
    api_port: int = int(os.getenv("API_PORT", "8000"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Arc Network
    arc_rpc_url: str = os.getenv("ARC_RPC_URL", "https://arc-testnet-rpc.io")
    arc_chain_id: int = int(os.getenv("ARC_CHAIN_ID", "11155111"))
    arc_contract_address: str = os.getenv("ARC_CONTRACT_ADDRESS", "")
    
    # Circle API
    circle_api_key: str = os.getenv("CIRCLE_API_KEY", "")
    circle_entity_id: str = os.getenv("CIRCLE_ENTITY_ID", "")
    x402_facilitator_url: str = os.getenv("X402_FACILITATOR_URL", "")
    
    # USDC Token
    usdc_address: str = os.getenv("USDC_ADDRESS", "")
    
    # Agent Configuration
    consumer_wallet_address: Optional[str] = os.getenv("CONSUMER_WALLET_ADDRESS")
    provider_wallet_address: Optional[str] = os.getenv("PROVIDER_WALLET_ADDRESS")
    
    # Pricing Configuration
    base_unit_price: float = 0.0001  # $0.0001 per unit
    max_unit_price: float = 0.01     # $0.01 per unit
    compute_time_multiplier: float = 0.00001  # $0.00001 per ms
    token_multiplier: float = 0.000001  # $0.000001 per token
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Validate critical settings
def validate_settings():
    """Validate that all required settings are configured"""
    required = [
        ("arc_rpc_url", settings.arc_rpc_url),
        ("arc_contract_address", settings.arc_contract_address),
        ("usdc_address", settings.usdc_address),
    ]
    
    missing = [name for name, value in required if not value]
    if missing:
        raise ValueError(f"Missing required settings: {', '.join(missing)}")
    
    print(f"✓ Configuration validated")
    print(f"  Arc RPC: {settings.arc_rpc_url}")
    print(f"  Contract: {settings.arc_contract_address}")
    print(f"  USDC: {settings.usdc_address}")
```

---

## 📊 Step 3: Data Models

Create `backend/models.py`:

```python
"""
Pydantic models for request/response validation
"""
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class ComputeTaskType(str, Enum):
    """Types of compute tasks"""
    IMAGE_CLASSIFICATION = "image_classification"
    DATA_PROCESSING = "data_processing"
    MODEL_INFERENCE = "model_inference"
    EMBEDDING_GENERATION = "embedding_generation"


class ComputeRequestModel(BaseModel):
    """Consumer agent request for compute"""
    task_id: str
    task_type: ComputeTaskType
    consumer_address: str
    provider_address: str
    estimated_units: int = Field(gt=0)
    max_price_usdc: float = Field(gt=0)
    params: Dict[str, Any] = {}
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task-abc123",
                "task_type": "image_classification",
                "consumer_address": "0x123...",
                "provider_address": "0x456...",
                "estimated_units": 100,
                "max_price_usdc": 0.01,
                "params": {"model": "resnet50"}
            }
        }


class UsageMetricsModel(BaseModel):
    """Track compute usage"""
    quantity: int
    unit_type: str
    compute_time_ms: int
    tokens_used: int = 0
    memory_used_mb: int = 0


class ComputeResultModel(BaseModel):
    """Result from provider agent"""
    task_id: str
    status: str  # "success", "failed"
    actual_cost_usdc: float
    arc_tx_hash: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime


class HealthCheckModel(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str
    arc_connected: bool
    usdc_available: bool


class MetricsModel(BaseModel):
    """Aggregated metrics"""
    metering: Dict[str, Any]
    settlement: Dict[str, Any]
    uptime_seconds: float
    requests_total: int
    requests_success: int
```

---

## 🔍 Step 4: Metering Engine

Create `backend/engines/metering.py`:

```python
"""
Usage metering engine
Tracks compute usage and generates reports
"""
from typing import List, Dict, Any
from datetime import datetime
import time
from pydantic import BaseModel


class UsageMetrics(BaseModel):
    """Single usage record"""
    quantity: int
    unit_type: str
    compute_time_ms: int
    tokens_used: int = 0
    memory_used_mb: int = 0
    timestamp: datetime = None
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class MeteringEngine:
    """
    Track compute usage and generate metrics
    """
    
    def __init__(self):
        """Initialize metering engine"""
        self.records: List[UsageMetrics] = []
        self.start_time = datetime.utcnow()
    
    def record_usage(
        self,
        quantity: int,
        unit_type: str,
        compute_time_ms: int,
        tokens_used: int = 0,
        memory_used_mb: int = 0
    ) -> UsageMetrics:
        """
        Record a compute usage event
        
        Args:
            quantity: Number of units processed
            unit_type: Type of unit ("query", "image", "token", etc.)
            compute_time_ms: Time spent computing
            tokens_used: Tokens consumed (for LLM tasks)
            memory_used_mb: Memory footprint
            
        Returns:
            UsageMetrics object
        """
        metrics = UsageMetrics(
            quantity=quantity,
            unit_type=unit_type,
            compute_time_ms=compute_time_ms,
            tokens_used=tokens_used,
            memory_used_mb=memory_used_mb
        )
        self.records.append(metrics)
        return metrics
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get aggregated usage summary
        
        Returns:
            Dictionary with aggregated metrics
        """
        if not self.records:
            return {
                "total_units": 0,
                "total_compute_ms": 0,
                "total_tokens": 0,
                "avg_time_ms": 0,
                "record_count": 0,
                "unit_types": {}
            }
        
        # Group by unit type
        unit_types = {}
        for record in self.records:
            if record.unit_type not in unit_types:
                unit_types[record.unit_type] = 0
            unit_types[record.unit_type] += record.quantity
        
        return {
            "total_units": sum(r.quantity for r in self.records),
            "total_compute_ms": sum(r.compute_time_ms for r in self.records),
            "total_tokens": sum(r.tokens_used for r in self.records),
            "avg_time_ms": sum(r.compute_time_ms for r in self.records) / len(self.records),
            "record_count": len(self.records),
            "unit_types": unit_types,
            "oldest_record": self.records[0].timestamp.isoformat() if self.records else None,
            "latest_record": self.records[-1].timestamp.isoformat() if self.records else None,
        }
    
    def reset(self):
        """Clear all records"""
        self.records = []
        print("✓ Metering engine reset")


# Global instance
metering_engine = MeteringEngine()
```

---

## 💰 Step 5: Pricing Engine

Create `backend/engines/pricing.py`:

```python
"""
Pricing engine
Calculate costs based on usage
"""
from typing import Optional
from dataclasses import dataclass
from pydantic import BaseModel

from backend.config import settings
from backend.engines.metering import UsageMetrics


@dataclass
class PricingModel:
    """Pricing configuration"""
    base_unit_price: float
    compute_time_multiplier: float
    token_multiplier: float


class PricingEngine:
    """
    Calculate per-unit and total costs
    Ensures ≤ $0.01 per unit
    """
    
    # Default pricing from settings
    DEFAULT_PRICING = PricingModel(
        base_unit_price=settings.base_unit_price,
        compute_time_multiplier=settings.compute_time_multiplier,
        token_multiplier=settings.token_multiplier
    )
    
    @classmethod
    def calculate_cost(
        cls,
        usage: UsageMetrics,
        pricing: Optional[PricingModel] = None
    ) -> float:
        """
        Calculate total cost for compute usage
        
        Args:
            usage: UsageMetrics object
            pricing: Optional custom pricing model
            
        Returns:
            Total cost in USDC
        """
        if pricing is None:
            pricing = cls.DEFAULT_PRICING
        
        cost = 0.0
        
        # Base cost: units × base price
        cost += usage.quantity * pricing.base_unit_price
        
        # Compute time cost: if > 1000ms, add multiplier
        if usage.compute_time_ms > 1000:
            additional_ms = usage.compute_time_ms - 1000
            cost += (additional_ms / 1000) * pricing.compute_time_multiplier
        
        # Token-based cost: for LLM tasks
        if usage.tokens_used > 0:
            cost += usage.tokens_used * pricing.token_multiplier
        
        return cost
    
    @classmethod
    def validate_price(
        cls,
        usage: UsageMetrics,
        max_price_usdc: float,
        pricing: Optional[PricingModel] = None
    ) -> tuple[bool, float]:
        """
        Check if actual cost is within consumer's max price
        
        Args:
            usage: UsageMetrics object
            max_price_usdc: Consumer's max price limit
            pricing: Optional custom pricing model
            
        Returns:
            Tuple of (is_valid, actual_cost)
        """
        actual_cost = cls.calculate_cost(usage, pricing)
        is_valid = actual_cost <= max_price_usdc
        return is_valid, actual_cost
    
    @classmethod
    def get_unit_price(
        cls,
        usage: UsageMetrics,
        pricing: Optional[PricingModel] = None
    ) -> float:
        """
        Get cost per unit (for logging/display)
        
        Returns:
            Cost per unit in USDC
        """
        if usage.quantity == 0:
            return 0.0
        
        total_cost = cls.calculate_cost(usage, pricing)
        return total_cost / usage.quantity
    
    @classmethod
    def enforce_max_unit_price(
        cls,
        usage: UsageMetrics,
        pricing: Optional[PricingModel] = None
    ) -> bool:
        """
        Verify that per-unit price doesn't exceed $0.01 limit
        
        Args:
            usage: UsageMetrics object
            pricing: Optional custom pricing model
            
        Returns:
            True if valid, raises AssertionError if exceeds limit
        """
        unit_price = cls.get_unit_price(usage, pricing)
        max_allowed = settings.max_unit_price
        
        assert unit_price <= max_allowed, (
            f"Unit price ${unit_price:.6f} exceeds "
            f"${max_allowed:.2f} limit"
        )
        return True


# Global instance
pricing_engine = PricingEngine()
```

---

## 💳 Step 6: Settlement Engine

Create `backend/engines/settlement.py`:

```python
"""
Settlement engine
Orchestrate Arc payments
"""
import asyncio
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import random

from backend.config import settings


@dataclass
class SettlementRecord:
    """Record of a settled payment"""
    consumer_address: str
    provider_address: str
    amount_usdc: float
    task_id: str
    arc_tx_hash: str
    timestamp: datetime
    status: str  # "pending", "confirmed", "failed"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "consumer": self.consumer_address,
            "provider": self.provider_address,
            "amount": self.amount_usdc,
            "task_id": self.task_id,
            "tx_hash": self.arc_tx_hash,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status,
        }


class SettlementEngine:
    """
    Orchestrate payments on Arc via Circle Nanopayments
    """
    
    def __init__(self):
        """Initialize settlement engine"""
        self.records: List[SettlementRecord] = []
        self.arc_contract_address = settings.arc_contract_address
        self.arc_rpc_url = settings.arc_rpc_url
        self.circle_api_key = settings.circle_api_key
    
    async def settle_payment(
        self,
        consumer_address: str,
        provider_address: str,
        amount_usdc: float,
        task_id: str
    ) -> Optional[str]:
        """
        Execute atomic payment on Arc
        
        Args:
            consumer_address: Consumer agent address
            provider_address: Provider agent address
            amount_usdc: Amount to transfer (in USDC)
            task_id: Unique task identifier
            
        Returns:
            Arc transaction hash if successful, None if failed
        """
        try:
            # Validate inputs
            assert amount_usdc > 0, "Amount must be > 0"
            assert consumer_address != provider_address, "Addresses must differ"
            
            # Call Arc smart contract (simulated for demo)
            tx_hash = await self._call_arc_contract(
                consumer_address=consumer_address,
                provider_address=provider_address,
                amount_usdc=amount_usdc,
                task_id=task_id
            )
            
            # Record settlement
            record = SettlementRecord(
                consumer_address=consumer_address,
                provider_address=provider_address,
                amount_usdc=amount_usdc,
                task_id=task_id,
                arc_tx_hash=tx_hash,
                timestamp=datetime.utcnow(),
                status="pending"
            )
            self.records.append(record)
            
            print(
                f"✓ Payment settled: {amount_usdc:.6f} USDC "
                f"({consumer_address[:8]}... → {provider_address[:8]}...)"
            )
            return tx_hash
        
        except Exception as e:
            print(f"✗ Settlement failed: {e}")
            return None
    
    async def _call_arc_contract(
        self,
        consumer_address: str,
        provider_address: str,
        amount_usdc: float,
        task_id: str
    ) -> str:
        """
        Call Arc smart contract
        
        In production, this would use web3.py to call the actual contract.
        For demo, we simulate the transaction.
        """
        # Simulate network delay
        await asyncio.sleep(0.01)
        
        # Generate transaction hash
        tx_hash = f"0x{random.getrandbits(256):064x}"
        
        return tx_hash
    
    def get_settlement_summary(self) -> Dict[str, Any]:
        """
        Get aggregated settlement statistics
        
        Returns:
            Dictionary with settlement metrics
        """
        if not self.records:
            return {
                "total_settled": 0.0,
                "transaction_count": 0,
                "avg_amount": 0.0,
                "total_consumers": 0,
                "total_providers": 0,
            }
        
        total = sum(r.amount_usdc for r in self.records)
        consumers = set(r.consumer_address for r in self.records)
        providers = set(r.provider_address for r in self.records)
        
        return {
            "total_settled": total,
            "transaction_count": len(self.records),
            "avg_amount": total / len(self.records),
            "total_consumers": len(consumers),
            "total_providers": len(providers),
            "oldest": self.records[0].timestamp.isoformat() if self.records else None,
            "latest": self.records[-1].timestamp.isoformat() if self.records else None,
        }
    
    def get_records(self) -> List[Dict[str, Any]]:
        """Get all settlement records"""
        return [r.to_dict() for r in self.records]
    
    def reset(self):
        """Clear all records"""
        self.records = []
        print("✓ Settlement engine reset")


# Global instance
settlement_engine = SettlementEngine()
```

---

## 🌐 Step 7: Main FastAPI Server

Create `backend/main.py`:

```python
"""
FastAPI backend for Agent-to-Agent Compute Marketplace
"""
import os
import time
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import JSONResponse
import uvicorn

from backend.config import settings, validate_settings
from backend.models import (
    ComputeRequestModel, ComputeResultModel, HealthCheckModel, MetricsModel
)
from backend.engines.metering import metering_engine
from backend.engines.pricing import pricing_engine
from backend.engines.settlement import settlement_engine


# Validate settings on startup
try:
    validate_settings()
except ValueError as e:
    print(f"ERROR: {e}")
    exit(1)

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Trustless marketplace for agent-to-agent compute services"
)

# Startup timestamp
startup_time = datetime.utcnow()


@app.on_event("startup")
async def startup():
    """Initialize on startup"""
    print("\n" + "=" * 60)
    print(f"Starting {settings.api_title}")
    print("=" * 60)
    print(f"API Port: {settings.api_port}")
    print(f"Arc RPC: {settings.arc_rpc_url[:40]}...")
    print(f"Contract: {settings.arc_contract_address[:16]}...")
    print("=" * 60 + "\n")


@app.get("/health")
async def health_check() -> HealthCheckModel:
    """
    Health check endpoint
    """
    return HealthCheckModel(
        status="ok",
        timestamp=datetime.utcnow(),
        version=settings.api_version,
        arc_connected=True,  # Would check actual connection
        usdc_available=True  # Would check actual availability
    )


@app.post("/api/compute")
async def request_compute(
    request: ComputeRequestModel,
    x_402_payment: Optional[str] = Header(None)
) -> ComputeResultModel:
    """
    Consumer agent requests compute from provider agent
    
    Expects x402 payment header in request
    """
    # Verify x402 payment header
    if not x_402_payment:
        raise HTTPException(
            status_code=402,
            detail="Payment Required - x402 header missing"
        )
    
    # Simulate compute execution
    import asyncio
    await asyncio.sleep(0.05)
    
    # Create usage metrics
    usage = metering_engine.record_usage(
        quantity=request.estimated_units,
        unit_type="query",
        compute_time_ms=50,
        tokens_used=request.estimated_units * 10
    )
    
    # Calculate cost
    actual_cost = pricing_engine.calculate_cost(usage)
    
    # Validate price
    is_valid, _ = pricing_engine.validate_price(usage, request.max_price_usdc)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"Actual cost ${actual_cost:.6f} exceeds max ${request.max_price_usdc:.6f}"
        )
    
    # Settle payment
    tx_hash = await settlement_engine.settle_payment(
        consumer_address=request.consumer_address,
        provider_address=request.provider_address,
        amount_usdc=actual_cost,
        task_id=request.task_id
    )
    
    return ComputeResultModel(
        task_id=request.task_id,
        status="success",
        actual_cost_usdc=actual_cost,
        arc_tx_hash=tx_hash,
        result={"data": "computed", "units_processed": request.estimated_units},
        timestamp=datetime.utcnow()
    )


@app.get("/api/metrics")
async def get_metrics() -> Dict:
    """
    Get aggregated metering and settlement metrics
    """
    uptime = (datetime.utcnow() - startup_time).total_seconds()
    
    return {
        "metering": metering_engine.get_summary(),
        "settlement": settlement_engine.get_settlement_summary(),
        "uptime_seconds": uptime,
        "settlement_records": settlement_engine.get_records(),
    }


@app.get("/api/debug/reset")
async def debug_reset():
    """
    Reset all engines (debug only)
    """
    metering_engine.reset()
    settlement_engine.reset()
    return {"status": "reset", "timestamp": datetime.utcnow()}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "status": "running",
        "endpoints": {
            "health": "/health",
            "compute": "/api/compute",
            "metrics": "/api/metrics",
            "docs": "/docs",
            "openapi": "/openapi.json"
        }
    }


def run():
    """Run the server"""
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    run()
```

---

## ✅ Step 8: Test the Backend

### Start the server

```bash
# From project root
python -m backend.main

# Should output:
# ============================================================
# Starting Agent-to-Agent Compute Marketplace
# ============================================================
# API Port: 8000
# Arc RPC: https://arc-testnet-rpc.io...
# Contract: 0x...
# ============================================================
```

### Test endpoints

```bash
# In another terminal

# 1. Health check
curl http://localhost:8000/health
# Should return: {"status":"ok","version":"1.0.0",...}

# 2. Root endpoint
curl http://localhost:8000/
# Should return API info

# 3. Metrics (empty at first)
curl http://localhost:8000/api/metrics
# Should return: {"metering":{},"settlement":{},...}

# 4. Test compute request (should fail - needs x402 header)
curl -X POST http://localhost:8000/api/compute \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "test-1",
    "task_type": "image_classification",
    "consumer_address": "0x123",
    "provider_address": "0x456",
    "estimated_units": 100,
    "max_price_usdc": 0.01
  }'
# Should return: 402 Payment Required

# 5. Test with x402 header
curl -X POST http://localhost:8000/api/compute \
  -H "Content-Type: application/json" \
  -H "X-402-Payment: dummy_payment_proof" \
  -d '{
    "task_id": "test-1",
    "task_type": "image_classification",
    "consumer_address": "0x123",
    "provider_address": "0x456",
    "estimated_units": 100,
    "max_price_usdc": 0.01
  }'
# Should return: success with transaction hash
```

---

## 📝 Step 9: Add Logging

Create `backend/logging_config.py`:

```python
"""
Logging configuration
"""
import logging
import sys
from backend.config import settings

def setup_logging():
    """Configure logging"""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('backend.log')
        ]
    )
    
    return logging.getLogger(__name__)

logger = setup_logging()
```

Update `backend/main.py` to use logging:

```python
from backend.logging_config import logger

# In handlers:
logger.info(f"Received compute request: {request.task_id}")
logger.info(f"Payment settled: {actual_cost} USDC")
```

---

## 🧪 Step 10: Create Tests

Create `tests/test_backend.py`:

```python
"""
Tests for backend components
"""
import pytest
from backend.engines.metering import metering_engine, UsageMetrics
from backend.engines.pricing import pricing_engine, PricingModel
from backend.engines.settlement import settlement_engine


def test_metering():
    """Test metering engine"""
    metering_engine.reset()
    
    # Record usage
    metrics = metering_engine.record_usage(
        quantity=100,
        unit_type="image",
        compute_time_ms=50,
        tokens_used=1000
    )
    
    assert metrics.quantity == 100
    
    # Get summary
    summary = metering_engine.get_summary()
    assert summary["total_units"] == 100
    assert summary["record_count"] == 1


def test_pricing():
    """Test pricing engine"""
    usage = UsageMetrics(
        quantity=100,
        unit_type="image",
        compute_time_ms=50,
        tokens_used=1000
    )
    
    cost = pricing_engine.calculate_cost(usage)
    assert cost > 0
    
    # Unit price should be ≤ $0.01
    unit_price = pricing_engine.get_unit_price(usage)
    assert unit_price <= 0.01


@pytest.mark.asyncio
async def test_settlement():
    """Test settlement engine"""
    settlement_engine.reset()
    
    tx_hash = await settlement_engine.settle_payment(
        consumer_address="0x123",
        provider_address="0x456",
        amount_usdc=0.01,
        task_id="task-1"
    )
    
    assert tx_hash is not None
    assert settlement_engine.get_settlement_summary()["transaction_count"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

Run tests:
```bash
pytest tests/test_backend.py -v
```

---

## 📋 Verification Checklist

- [ ] Backend directory structure created
- [ ] `backend/config.py` with settings
- [ ] `backend/models.py` with Pydantic models
- [ ] `backend/engines/metering.py` tracking usage
- [ ] `backend/engines/pricing.py` calculating costs
- [ ] `backend/engines/settlement.py` executing payments
- [ ] `backend/main.py` FastAPI server
- [ ] Server starts without errors
- [ ] `/health` endpoint returns 200
- [ ] `/api/compute` accepts requests
- [ ] `/api/metrics` returns aggregated stats
- [ ] Tests pass

---

## 🚨 Troubleshooting

### "ModuleNotFoundError: No module named 'fastapi'"
```bash
pip install -r requirements.txt
```

### "Port 8000 already in use"
```bash
# Change port in .env:
API_PORT=8001

# Or find and kill process:
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

### "Settings validation failed"
- Check all required vars in `.env`
- Run: `python -c "from backend.config import settings; print(settings)"`

### Async errors in tests
```bash
# Install pytest-asyncio:
pip install pytest-asyncio

# Run with asyncio mode:
pytest tests/ -v --asyncio-mode=auto
```

---

## 📚 Next Steps

1. **Agent Implementation** — Open AGENT_IMPLEMENTATION.md
2. **Integration** — Wire agents to backend
3. **Testing** — Run full integration tests
4. **Demo** — Generate 50+ transactions

---

## ✅ Completion

**Backend successfully built! 🎉**

Your backend is now:
- ✅ Running on port 8000
- ✅ Accepting compute requests
- ✅ Metering usage
- ✅ Calculating prices
- ✅ Settling payments
- ✅ Ready for agent integration

**Next: Open AGENT_IMPLEMENTATION.md to build the agents!**
