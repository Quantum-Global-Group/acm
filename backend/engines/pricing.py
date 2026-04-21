"""Pricing engine — converts usage into USDC cost while enforcing the $0.01/unit ceiling."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from backend.config import settings
from backend.engines.metering import UsageMetrics


@dataclass(frozen=True)
class PricingModel:
    base_unit_price: float
    compute_time_multiplier: float
    token_multiplier: float


class PricingEngine:
    """Stateless calculator: usage → USDC cost, with hard per-unit ceiling."""

    DEFAULT = PricingModel(
        base_unit_price=settings.base_unit_price,
        compute_time_multiplier=settings.compute_time_multiplier,
        token_multiplier=settings.token_multiplier,
    )

    @classmethod
    def calculate_cost(
        cls,
        usage: UsageMetrics,
        pricing: Optional[PricingModel] = None,
    ) -> float:
        pricing = pricing or cls.DEFAULT
        cost = usage.quantity * pricing.base_unit_price

        if usage.compute_time_ms > 1000:
            additional_seconds = (usage.compute_time_ms - 1000) / 1000.0
            cost += additional_seconds * pricing.compute_time_multiplier

        if usage.tokens_used > 0:
            cost += usage.tokens_used * pricing.token_multiplier

        return cost

    @classmethod
    def get_unit_price(
        cls,
        usage: UsageMetrics,
        pricing: Optional[PricingModel] = None,
    ) -> float:
        if usage.quantity == 0:
            return 0.0
        return cls.calculate_cost(usage, pricing) / usage.quantity

    @classmethod
    def validate_price(
        cls,
        usage: UsageMetrics,
        max_price_usdc: float,
        pricing: Optional[PricingModel] = None,
    ) -> Tuple[bool, float]:
        actual = cls.calculate_cost(usage, pricing)
        return (actual <= max_price_usdc), actual

    @classmethod
    def enforce_max_unit_price(
        cls,
        usage: UsageMetrics,
        pricing: Optional[PricingModel] = None,
    ) -> bool:
        unit_price = cls.get_unit_price(usage, pricing)
        if unit_price > settings.max_unit_price:
            raise AssertionError(
                f"Unit price ${unit_price:.6f} exceeds ${settings.max_unit_price:.2f} ceiling"
            )
        return True


pricing_engine = PricingEngine()
