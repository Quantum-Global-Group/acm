"""Pydantic models for request/response validation."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ComputeTaskType(str, Enum):
    IMAGE_CLASSIFICATION = "image_classification"
    DATA_PROCESSING = "data_processing"
    MODEL_INFERENCE = "model_inference"
    EMBEDDING_GENERATION = "embedding_generation"
    TEXT_CLASSIFICATION = "text_classification"


class ComputeRequestModel(BaseModel):
    """Consumer agent request for compute."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "task_id": "task-abc123",
            "task_type": "image_classification",
            "consumer_address": "0x" + "1" * 40,
            "provider_address": "0x" + "2" * 40,
            "estimated_units": 100,
            "max_price_usdc": 0.01,
            "max_latency_ms": 2000,
            "params": {"model": "resnet50"},
        }
    })

    task_id: str
    task_type: ComputeTaskType
    consumer_address: str
    provider_address: str
    estimated_units: int = Field(gt=0)
    max_price_usdc: float = Field(gt=0)
    max_latency_ms: Optional[int] = Field(default=None, gt=0)
    params: Dict[str, Any] = Field(default_factory=dict)


class UsageMetricsModel(BaseModel):
    quantity: int
    unit_type: str
    compute_time_ms: int
    tokens_used: int = 0
    memory_used_mb: int = 0


class ComputeResultModel(BaseModel):
    task_id: str
    status: str  # "success" | "failed"
    actual_cost_usdc: float
    arc_tx_hash: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime


class HealthCheckModel(BaseModel):
    status: str
    timestamp: datetime
    version: str
    arc_connected: bool
    contract_deployed: bool
    settlement_simulate: bool


class MetricsModel(BaseModel):
    metering: Dict[str, Any]
    settlement: Dict[str, Any]
    uptime_seconds: float


class BatchComputeRequestModel(BaseModel):
    """Submit many compute jobs in one call; volume discount applies to all."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "jobs": [
                {
                    "task_id": "batch-1",
                    "task_type": "image_classification",
                    "consumer_address": "0x" + "1" * 40,
                    "provider_address": "0x" + "2" * 40,
                    "estimated_units": 10,
                    "max_price_usdc": 0.01,
                }
            ],
            "allow_partial": True,
        }
    })

    jobs: List[ComputeRequestModel] = Field(min_length=1, max_length=500)
    allow_partial: bool = True


class BatchComputeResultModel(BaseModel):
    results: List["ComputeResultModel"]
    job_count: int
    successful_count: int
    failed_count: int
    discount_rate: float            # e.g. 0.10 for 10% off
    total_cost_usdc: float          # after discount
    gross_cost_usdc: float          # before discount
    savings_usdc: float             # gross - net


class ProviderRegistration(BaseModel):
    """Payload a provider POSTs to /api/providers/register."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "agent_id": "provider-gpu-1",
            "wallet_address": "0x" + "2" * 40,
            "supported_tasks": ["image_classification", "text_classification"],
            "pricing": {"image_classification": 0.0002, "text_classification": 0.00015},
            "default_unit_price": 0.0001,
            "name": "GPU Inference Pool A",
            "description": "RTX 4090 cluster, <100ms p50 on 224x224 images.",
        }
    })

    agent_id: str = Field(min_length=1)
    wallet_address: str = Field(min_length=1)
    supported_tasks: List[ComputeTaskType] = Field(min_length=1)
    pricing: Dict[ComputeTaskType, float] = Field(default_factory=dict)
    default_unit_price: float = Field(default=0.0001, gt=0)
    name: Optional[str] = None
    description: Optional[str] = None
    provider_endpoint: Optional[str] = None  # If set, backend POSTs tasks here instead of simulating


class ProviderListing(BaseModel):
    """Public view of a registered provider — returned by /api/providers."""

    agent_id: str
    wallet_address: str
    supported_tasks: List[ComputeTaskType]
    pricing: Dict[str, float]
    default_unit_price: float
    name: Optional[str]
    description: Optional[str]
    provider_endpoint: Optional[str] = None
    registered_at: datetime
    active: bool
    jobs_completed: int = 0
    jobs_failed: int = 0
    success_rate: float = 1.0
    avg_latency_ms: float = 0.0
    reputation_score: float = 0.0


class ProviderListResponse(BaseModel):
    providers: List[ProviderListing]
    count: int
