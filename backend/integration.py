"""
Integration layer — assembles AgentManager + (optional) live Arc contract
and runs the marketplace end-to-end against the FastAPI backend.
"""
from __future__ import annotations

import asyncio
import json
import secrets
from pathlib import Path
from typing import Any, Dict, Optional

from backend.agents.manager import AgentManager
from backend.config import settings
from backend.engines.settlement import settlement_engine


def _rand_addr() -> str:
    return "0x" + secrets.token_hex(20)


class MarketplaceIntegration:
    def __init__(self, api_endpoint: str = "http://localhost:8000") -> None:
        self.manager = AgentManager(api_endpoint=api_endpoint)
        self._w3 = None
        self._contract = None
        self._maybe_load_contract()

    def _maybe_load_contract(self) -> None:
        addr = settings.arc_contract_address
        if not addr or addr.lower() == "0x" + "0" * 40:
            return
        try:
            from web3 import Web3
            abi_path = Path(__file__).resolve().parent.parent / "smart_contracts" / "abi.json"
            abi = json.loads(abi_path.read_text())
            self._w3 = Web3(Web3.HTTPProvider(settings.arc_rpc_url))
            self._contract = self._w3.eth.contract(
                address=Web3.to_checksum_address(addr),
                abi=abi,
            )
            print(f"[integration] Connected to contract {addr}")
        except Exception as exc:
            print(f"[integration] Contract attach skipped: {exc}")

    def setup_agents(self, num_consumers: int = 2, num_providers: int = 3,
                     initial_balance: float = 5.0) -> None:
        print(f"[integration] Setting up {num_consumers} consumers, {num_providers} providers")
        for i in range(num_consumers):
            self.manager.add_consumer(
                agent_id=f"consumer-{i + 1}",
                wallet_address=_rand_addr(),
                initial_balance=initial_balance,
            )
        for i in range(num_providers):
            self.manager.add_provider(
                agent_id=f"provider-{i + 1}",
                wallet_address=_rand_addr(),
                supported_tasks=["image_classification", "data_processing"],
            )

    async def run_marketplace(self, transactions: int = 50, units: int = 100) -> None:
        await self.manager.marketplace_simulation(
            num_transactions=transactions,
            units_per_transaction=units,
        )

    async def verify(self) -> Dict[str, Any]:
        """Pull settlement summary from the running backend, not the local process."""
        import httpx
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(f"{self.manager.api_endpoint}/api/metrics")
                r.raise_for_status()
                summary = r.json().get("settlement", {})
        except Exception as exc:
            print(f"[integration] Could not fetch backend metrics ({exc}); using local view")
            summary = settlement_engine.get_settlement_summary()
        print("[integration] Settlement summary:")
        for k, v in summary.items():
            print(f"  {k}: {v}")
        return summary

    async def close(self) -> None:
        await self.manager.close()


async def main(transactions: int = 60) -> None:
    integration = MarketplaceIntegration()
    integration.setup_agents(num_consumers=2, num_providers=3)
    await integration.run_marketplace(transactions=transactions)
    await integration.verify()
    await integration.close()


if __name__ == "__main__":
    asyncio.run(main())
