"""Pydantic models for request/response validation."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class ComputeTaskType(str, Enum):
    IMAGE_CLASSIFICATION = "image_classification"
    DATA_PROCESSING = "data_processing"
    MODEL_INFERENCE = "model_inference"
    EMBEDDING_GENERATION = "embedding_generation"


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
            "params": {"model": "resnet50"},
        }
    })

    task_id: str
    task_type: ComputeTaskType
    consumer_address: str
    provider_address: str
    estimated_units: int = Field(gt=0)
    max_price_usdc: float = Field(gt=0)
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
