"""
Agent-to-Agent Compute Marketplace Backend
Combines autonomous agents with usage-based billing and real-time USDC settlement on Arc
"""

import json
import asyncio
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum

from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import JSONResponse
import uvicorn
from pydantic import BaseModel
import httpx

# ============================================================================
# 1. DATA MODELS
# ============================================================================

class ComputeTaskType(str, Enum):
    """Types of compute tasks agents can request"""
    IMAGE_CLASSIFICATION = "image_classification"
    DATA_PROCESSING = "data_processing"
    MODEL_INFERENCE = "model_inference"
    EMBEDDING_GENERATION = "embedding_generation"


@dataclass
class UsageMetrics:
    """Track actual compute usage"""
    quantity: int  # Number of units (images, queries, tokens)
    unit_type: str  # "image", "query", "token", "second"
    compute_time_ms: int  # Actual compute time
    tokens_used: int  # For LLM-based tasks
    memory_used_mb: int  # Memory footprint


@dataclass
class PricingModel:
    """Calculate cost based on usage"""
    base_unit_price: float  # $0.0001 per unit
    compute_time_multiplier: float  # Price per ms of compute
    token_multiplier: float  # Price per token used
    
    def calculate_cost(self, usage: UsageMetrics) -> float:
        """Calculate total cost in USDC"""
        cost = 0.0
        
        # Base: units × base price
        cost += usage.quantity * self.base_unit_price
        
        # Compute time: if > 1000ms, add multiplier
        if usage.compute_time_ms > 1000:
            cost += (usage.compute_time_ms / 1000) * self.compute_time_multiplier
        
        # Token-based: for LLM tasks
        if usage.tokens_used > 0:
            cost += usage.tokens_used * self.token_multiplier
        
        return cost


@dataclass
class ComputeRequest:
    """Request from consumer agent to provider agent"""
    task_id: str
    task_type: ComputeTaskType
    consumer_address: str
    provider_address: str
    params: Dict
    estimated_units: int
    max_price_usdc: float
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class ComputeResult:
    """Result from provider agent"""
    task_id: str
    provider_address: str
    consumer_address: str
    status: str  # "success", "failed", "timeout"
    result: Optional[Dict] = None
    error: Optional[str] = None
    usage: Optional[UsageMetrics] = None
    actual_cost_usdc: float = 0.0
    arc_tx_hash: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class SettlementRecord:
    """Record of a settled payment on Arc"""
    consumer_address: str
    provider_address: str
    amount_usdc: float
    task_id: str
    arc_tx_hash: str
    timestamp: datetime
    status: str  # "pending", "confirmed", "failed"


# ============================================================================
# 2. USAGE METERING ENGINE
# ============================================================================

class MeteringEngine:
    """Track compute usage and generate usage reports"""
    
    def __init__(self):
        self.records: List[UsageMetrics] = []
    
    def record_usage(
        self,
        quantity: int,
        unit_type: str,
        compute_time_ms: int,
        tokens_used: int = 0,
        memory_used_mb: int = 0
    ) -> UsageMetrics:
        """Record a compute usage event"""
        metrics = UsageMetrics(
            quantity=quantity,
            unit_type=unit_type,
            compute_time_ms=compute_time_ms,
            tokens_used=tokens_used,
            memory_used_mb=memory_used_mb
        )
        self.records.append(metrics)
        return metrics
    
    def get_summary(self) -> Dict:
        """Get aggregated usage metrics"""
        if not self.records:
            return {
                "total_units": 0,
                "total_compute_ms": 0,
                "total_tokens": 0,
                "avg_time_ms": 0
            }
        
        return {
            "total_units": sum(r.quantity for r in self.records),
            "total_compute_ms": sum(r.compute_time_ms for r in self.records),
            "total_tokens": sum(r.tokens_used for r in self.records),
            "avg_time_ms": sum(r.compute_time_ms for r in self.records) / len(self.records),
            "count": len(self.records)
        }


# ============================================================================
# 3. PRICING ENGINE
# ============================================================================

class PricingEngine:
    """Calculate per-unit and total cost"""
    
    # Default pricing model: $0.0001 per unit, ensuring ≤ $0.01 per action
    DEFAULT_PRICING = PricingModel(
        base_unit_price=0.0001,  # $0.0001 per query/image/token
        compute_time_multiplier=0.00001,  # $0.00001 per ms of compute time
        token_multiplier=0.000001  # $0.000001 per token
    )
    
    @classmethod
    def calculate_cost(cls, usage: UsageMetrics, pricing: PricingModel = None) -> float:
        """Calculate total cost for compute usage"""
        if pricing is None:
            pricing = cls.DEFAULT_PRICING
        
        cost = pricing.calculate_cost(usage)
        
        # Enforce ≤ $0.01 per unit
        if usage.quantity > 0:
            unit_cost = cost / usage.quantity
            assert unit_cost <= 0.01, f"Unit cost ${unit_cost:.6f} exceeds $0.01 limit"
        
        return cost
    
    @classmethod
    def validate_price(cls, usage: UsageMetrics, max_price_usdc: float) -> bool:
        """Check if actual cost is within consumer's max price"""
        actual_cost = cls.calculate_cost(usage)
        return actual_cost <= max_price_usdc


# ============================================================================
# 4. SETTLEMENT ENGINE
# ============================================================================

class SettlementEngine:
    """Orchestrate Arc payments via Circle Nanopayments"""
    
    def __init__(
        self,
        arc_contract_address: str,
        arc_rpc_url: str,
        circle_api_key: str,
        x402_facilitator_url: str
    ):
        self.contract_address = arc_contract_address
        self.arc_rpc_url = arc_rpc_url
        self.circle_api_key = circle_api_key
        self.x402_facilitator = x402_facilitator_url
        self.settlement_records: List[SettlementRecord] = []
    
    async def settle_payment(
        self,
        consumer_address: str,
        provider_address: str,
        amount_usdc: float,
        task_id: str
    ) -> Optional[str]:
        """
        Execute atomic payment on Arc via Circle Nanopayments.
        
        Returns:
            Arc transaction hash if successful, None if failed
        """
        try:
            # Step 1: Call Arc smart contract to transfer USDC
            tx_hash = await self._call_arc_contract(
                consumer_address=consumer_address,
                provider_address=provider_address,
                amount_usdc=amount_usdc,
                task_id=task_id
            )
            
            # Step 2: Record settlement
            record = SettlementRecord(
                consumer_address=consumer_address,
                provider_address=provider_address,
                amount_usdc=amount_usdc,
                task_id=task_id,
                arc_tx_hash=tx_hash,
                timestamp=datetime.utcnow(),
                status="pending"
            )
            self.settlement_records.append(record)
            
            print(f"[SETTLEMENT] Paid {amount_usdc} USDC: {consumer_address} → {provider_address} | Tx: {tx_hash}")
            return tx_hash
        
        except Exception as e:
            print(f"[SETTLEMENT ERROR] {e}")
            return None
    
    async def _call_arc_contract(
        self,
        consumer_address: str,
        provider_address: str,
        amount_usdc: float,
        task_id: str
    ) -> str:
        """Call Arc smart contract (pay_for_compute)"""
        
        # Convert USDC to smallest unit (1 USDC = 10^6 wei)
        amount_wei = int(amount_usdc * 1_000_000)
        
        # This is a placeholder; real implementation would use web3.py
        # to interact with Arc contract via RPC
        print(f"[ARC CONTRACT] Calling pay_for_compute(...)")
        print(f"  Consumer: {consumer_address}")
        print(f"  Provider: {provider_address}")
        print(f"  Amount: {amount_usdc} USDC ({amount_wei} wei)")
        print(f"  Task ID: {task_id}")
        
        # For demo: simulate successful tx hash
        tx_hash = f"0x{'a' * 64}"  # Placeholder
        
        return tx_hash
    
    def get_settlement_summary(self) -> Dict:
        """Get aggregated settlement stats"""
        if not self.settlement_records:
            return {
                "total_settled": 0.0,
                "transaction_count": 0,
                "avg_amount": 0.0
            }
        
        total = sum(r.amount_usdc for r in self.settlement_records)
        
        return {
            "total_settled": total,
            "transaction_count": len(self.settlement_records),
            "avg_amount": total / len(self.settlement_records) if self.settlement_records else 0
        }


# ============================================================================
# 5. REQUEST/RESPONSE HANDLER (x402-compatible)
# ============================================================================

class RequestResponseHandler:
    """Handle x402 payment verification and request routing"""
    
    def __init__(self, settlement_engine: SettlementEngine):
        self.settlement_engine = settlement_engine
    
    async def verify_x402_payment(
        self,
        x402_header: str,
        expected_amount_usdc: float
    ) -> bool:
        """
        Verify x402 payment header.
        
        Args:
            x402_header: x402 facilitator payment proof
            expected_amount_usdc: Expected payment amount
            
        Returns:
            True if payment is valid
        """
        # In real implementation: call x402 facilitator to validate
        # For demo: assume valid if header is present
        return len(x402_header) > 0
    
    async def handle_compute_request(
        self,
        request: ComputeRequest,
        x402_header: str
    ) -> ComputeResult:
        """
        Handle incoming compute request with payment verification.
        """
        print(f"[REQUEST] Task {request.task_id} from {request.consumer_address}")
        
        # Verify payment proof
        is_valid = await self.verify_x402_payment(
            x402_header,
            request.max_price_usdc
        )
        
        if not is_valid:
            return ComputeResult(
                task_id=request.task_id,
                provider_address=request.provider_address,
                consumer_address=request.consumer_address,
                status="failed",
                error="Payment verification failed"
            )
        
        # Simulate compute work (in real implementation: actual computation)
        result = await self._execute_compute(request)
        
        return result
    
    async def _execute_compute(self, request: ComputeRequest) -> ComputeResult:
        """Execute the actual compute task"""
        
        # Simulate computation based on task type
        await asyncio.sleep(0.1)  # Simulate processing
        
        usage = UsageMetrics(
            quantity=request.estimated_units,
            unit_type="query",
            compute_time_ms=100,
            tokens_used=request.estimated_units * 10
        )
        
        actual_cost = PricingEngine.calculate_cost(usage)
        
        return ComputeResult(
            task_id=request.task_id,
            provider_address=request.provider_address,
            consumer_address=request.consumer_address,
            status="success",
            result={"data": "computed", "units_processed": request.estimated_units},
            usage=usage,
            actual_cost_usdc=actual_cost
        )


# ============================================================================
# 6. FASTAPI APPLICATION
# ============================================================================

app = FastAPI(title="Agent-to-Agent Compute Marketplace")

# Initialize engines
metering = MeteringEngine()
settlement = SettlementEngine(
    arc_contract_address="0x",  # Will be set at deployment
    arc_rpc_url="https://arc-testnet-rpc.example.com",
    circle_api_key="sk_test_...",
    x402_facilitator_url="https://x402-facilitator.example.com"
)
handler = RequestResponseHandler(settlement)


class ComputeRequestPayload(BaseModel):
    """Request payload from consumer agent"""
    task_id: str
    task_type: str
    consumer_address: str
    provider_address: str
    estimated_units: int
    max_price_usdc: float
    params: Dict = {}


@app.post("/api/compute")
async def request_compute(
    payload: ComputeRequestPayload,
    x_402_payment: Optional[str] = Header(None)
):
    """
    Consumer agent requests compute from provider agent.
    Expects x402 payment header in request.
    """
    if not x_402_payment:
        raise HTTPException(status_code=402, detail="Payment Required (x402)")
    
    request = ComputeRequest(
        task_id=payload.task_id,
        task_type=ComputeTaskType(payload.task_type),
        consumer_address=payload.consumer_address,
        provider_address=payload.provider_address,
        params=payload.params,
        estimated_units=payload.estimated_units,
        max_price_usdc=payload.max_price_usdc
    )
    
    result = await handler.handle_compute_request(request, x_402_payment)
    
    if result.status == "success":
        # Settle payment on Arc
        tx_hash = await settlement.settle_payment(
            consumer_address=request.consumer_address,
            provider_address=request.provider_address,
            amount_usdc=result.actual_cost_usdc,
            task_id=request.task_id
        )
        result.arc_tx_hash = tx_hash
    
    return JSONResponse(status_code=200, content={
        "task_id": result.task_id,
        "status": result.status,
        "actual_cost_usdc": result.actual_cost_usdc,
        "arc_tx_hash": result.arc_tx_hash,
        "result": result.result,
        "error": result.error,
        "timestamp": result.timestamp.isoformat() if result.timestamp else None
    })


@app.get("/api/metrics")
async def get_metrics():
    """Get aggregated metering and settlement metrics"""
    return {
        "metering": metering.get_summary(),
        "settlement": settlement.get_settlement_summary(),
        "settlement_records": len(settlement.settlement_records)
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
