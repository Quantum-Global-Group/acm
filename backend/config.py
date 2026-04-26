"""Backend configuration loaded from environment variables."""
from __future__ import annotations

import os
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings sourced from .env / environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API
    api_title: str = "Agent-to-Agent Compute Marketplace"
    api_version: str = "1.0.0"
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Arc network
    arc_rpc_url: str = Field(default="", alias="ARC_RPC_URL")
    arc_chain_id: int = Field(default=0, alias="ARC_CHAIN_ID")
    arc_explorer_url: str = Field(default="", alias="ARC_EXPLORER_URL")
    arc_contract_address: str = Field(default="", alias="ARC_CONTRACT_ADDRESS")

    # Circle / x402
    circle_api_key: str = Field(default="", alias="CIRCLE_API_KEY")
    circle_entity_id: str = Field(default="", alias="CIRCLE_ENTITY_ID")
    x402_facilitator_url: str = Field(default="", alias="X402_FACILITATOR_URL")

    # USDC
    usdc_address: str = Field(default="", alias="USDC_ADDRESS")

    # Wallet
    private_key: str = Field(default="", alias="PRIVATE_KEY")
    consumer_wallet_address: Optional[str] = Field(default=None, alias="CONSUMER_WALLET_ADDRESS")
    provider_wallet_address: Optional[str] = Field(default=None, alias="PROVIDER_WALLET_ADDRESS")

    # Pricing knobs
    base_unit_price: float = 0.0001        # $0.0001 per unit baseline
    max_unit_price: float = 0.01           # Hard ceiling enforced everywhere
    compute_time_multiplier: float = 0.00001
    token_multiplier: float = 0.000001

    # Operational
    settlement_simulate: bool = Field(default=False, alias="SETTLEMENT_SIMULATE")


settings = Settings()


def validate_settings() -> None:
    """Hard fail early if a critical knob is unset."""
    required = [
        ("ARC_RPC_URL", settings.arc_rpc_url),
        ("USDC_ADDRESS", settings.usdc_address),
    ]
    missing = [name for name, value in required if not value]
    if missing:
        raise ValueError(f"Missing required settings: {', '.join(missing)}")

    # ARC_CONTRACT_ADDRESS is allowed to be the zero address pre-deploy,
    # but warn if it looks unset after Day 2.
    if settings.arc_contract_address.lower() in ("", "0x" + "0" * 40):
        print("[config] WARNING: ARC_CONTRACT_ADDRESS is unset/zero — settlement will simulate.")

    print("[config] Validated:")
    print(f"  Arc RPC:   {settings.arc_rpc_url}")
    print(f"  USDC:      {settings.usdc_address}")
    print(f"  Contract:  {settings.arc_contract_address or '(not deployed)'}")
    print(f"  Simulate:  {settings.settlement_simulate}")
