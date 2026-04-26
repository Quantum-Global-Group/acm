"""
Settlement engine — orchestrates per-action USDC payments.

Two modes:
  - SIMULATE: deterministic-ish in-memory tx hashes. Used for offline tests
    and when ARC_CONTRACT_ADDRESS is not deployed yet.
  - LIVE:     calls the deployed Arc contract via web3.py and waits for
    the receipt. Requires ARC_RPC_URL, PRIVATE_KEY, and a non-zero contract.

The mode is selected per-call from settings.settlement_simulate AND whether
a contract address is configured, so the same code path works in dev and prod.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import secrets
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.config import settings

log = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class SettlementRecord:
    consumer_address: str
    provider_address: str
    amount_usdc: float
    task_id: str
    arc_tx_hash: str
    timestamp: datetime
    status: str  # "pending" | "confirmed" | "failed"
    mode: str    # "simulate" | "live"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        return d


class SettlementEngine:
    """Atomic per-action settlement, sim or live."""

    def __init__(self) -> None:
        self.records: List[SettlementRecord] = []
        self._w3 = None
        self._contract = None
        self._account = None
        self._abi: Optional[List[Dict[str, Any]]] = None

    # ------------------------------------------------------------------ helpers

    def _live_enabled(self) -> bool:
        addr = settings.arc_contract_address
        if not addr or addr.lower() == "0x" + "0" * 40:
            return False
        if settings.settlement_simulate:
            return False
        return bool(settings.arc_rpc_url and settings.private_key)

    def _ensure_web3(self):
        if self._contract is not None:
            return
        from web3 import Web3
        from eth_account import Account

        abi_path = Path(__file__).resolve().parents[2] / "smart_contracts" / "abi.json"
        if self._abi is None:
            self._abi = json.loads(abi_path.read_text())

        self._w3 = Web3(Web3.HTTPProvider(settings.arc_rpc_url))
        self._account = Account.from_key(settings.private_key)
        self._contract = self._w3.eth.contract(
            address=Web3.to_checksum_address(settings.arc_contract_address),
            abi=self._abi,
        )

    # ------------------------------------------------------------------- modes

    async def _simulate(
        self,
        consumer_address: str,
        provider_address: str,
        amount_usdc: float,
        task_id: str,
        quantity: int = 1,
    ) -> str:
        await asyncio.sleep(0.005)
        return "0x" + secrets.token_hex(32)

    async def _live(
        self,
        consumer_address: str,
        provider_address: str,
        amount_usdc: float,
        task_id: str,
        quantity: int = 1,
    ) -> str:
        from web3 import Web3
        self._ensure_web3()
        loop = asyncio.get_event_loop()

        # Distribute total cost across quantity units so each unit_price stays
        # within the contract's max_unit_price ceiling (10 000 micro = $0.01).
        q = max(1, quantity)
        total_micro = int(round(amount_usdc * 1_000_000))
        if total_micro <= 0:
            raise ValueError(f"amount_usdc {amount_usdc} rounds to 0 micro-USDC")

        unit_price_micro = total_micro // q
        remainder = total_micro - unit_price_micro * q
        # Absorb the remainder by rounding up on the last unit only; we always
        # send a single pay_for_compute call so quantity * unit_price must equal
        # total_micro exactly.  Add remainder to unit_price and reduce quantity
        # by 1 if needed, or just bump unit_price and accept ±1 micro drift.
        unit_price_micro = (total_micro + q - 1) // q  # ceiling division

        MAX_UNIT_PRICE_MICRO = 10_000  # mirrors contract max_unit_price
        if unit_price_micro > MAX_UNIT_PRICE_MICRO:
            raise ValueError(
                f"unit_price_micro {unit_price_micro} exceeds contract ceiling "
                f"{MAX_UNIT_PRICE_MICRO} ({MAX_UNIT_PRICE_MICRO / 1_000_000:.4f} USDC). "
                "Reduce estimated_units or lower pricing knobs."
            )

        def _send() -> str:
            assert self._w3 is not None and self._contract is not None and self._account is not None
            nonce = self._w3.eth.get_transaction_count(self._account.address)
            fn = self._contract.functions.pay_for_compute(
                Web3.to_checksum_address(consumer_address),
                Web3.to_checksum_address(provider_address),
                q,
                unit_price_micro,
                task_id,
            )
            tx = fn.build_transaction({
                "from": self._account.address,
                "nonce": nonce,
                "gas": 300_000,
                "gasPrice": self._w3.eth.gas_price,
                "chainId": settings.arc_chain_id or self._w3.eth.chain_id,
            })
            signed = self._account.sign_transaction(tx)
            raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
            tx_hash = self._w3.eth.send_raw_transaction(raw)
            self._w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            return tx_hash.hex()

        return await loop.run_in_executor(None, _send)

    # ------------------------------------------------------------------ public

    async def settle_payment(
        self,
        consumer_address: str,
        provider_address: str,
        amount_usdc: float,
        task_id: str,
        quantity: int = 1,
    ) -> Optional[str]:
        if amount_usdc <= 0:
            return None
        if consumer_address == provider_address:
            return None

        live = self._live_enabled()
        mode = "live" if live else "simulate"

        try:
            if live:
                tx_hash = await self._live(
                    consumer_address, provider_address, amount_usdc, task_id, quantity
                )
                status = "confirmed"
            else:
                tx_hash = await self._simulate(
                    consumer_address, provider_address, amount_usdc, task_id, quantity
                )
                status = "pending"
        except Exception as exc:
            log.error(
                "[settlement] %s settlement failed for task=%s consumer=%s provider=%s: %s",
                mode, task_id, consumer_address, provider_address, exc, exc_info=True,
            )
            self.records.append(SettlementRecord(
                consumer_address=consumer_address,
                provider_address=provider_address,
                amount_usdc=amount_usdc,
                task_id=task_id,
                arc_tx_hash="",
                timestamp=_utcnow(),
                status=f"failed: {exc}",
                mode=mode,
            ))
            return None

        self.records.append(SettlementRecord(
            consumer_address=consumer_address,
            provider_address=provider_address,
            amount_usdc=amount_usdc,
            task_id=task_id,
            arc_tx_hash=tx_hash,
            timestamp=_utcnow(),
            status=status,
            mode=mode,
        ))
        return tx_hash

    def get_settlement_summary(self) -> Dict[str, Any]:
        if not self.records:
            return {
                "total_settled": 0.0,
                "transaction_count": 0,
                "avg_amount": 0.0,
                "total_consumers": 0,
                "total_providers": 0,
                "mode": "simulate" if not self._live_enabled() else "live",
            }
        total = sum(r.amount_usdc for r in self.records)
        consumers = {r.consumer_address for r in self.records}
        providers = {r.provider_address for r in self.records}
        confirmed = sum(1 for r in self.records if r.status in ("pending", "confirmed"))
        return {
            "total_settled": total,
            "transaction_count": len(self.records),
            "successful_count": confirmed,
            "avg_amount": total / len(self.records),
            "total_consumers": len(consumers),
            "total_providers": len(providers),
            "oldest": self.records[0].timestamp.isoformat(),
            "latest": self.records[-1].timestamp.isoformat(),
            "mode": "live" if self._live_enabled() else "simulate",
        }

    def get_records(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self.records]

    def reset(self) -> None:
        self.records.clear()


settlement_engine = SettlementEngine()
