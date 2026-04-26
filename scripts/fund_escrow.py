"""
Fund the marketplace escrow for a consumer wallet.

Flow:
  1. approve(marketplace, amount) on the USDC contract.
  2. deposit(amount) on the marketplace contract.

After running this, the consumer wallet has an internal marketplace balance
that the settlement engine can debit via pay_for_compute.

Usage:
  python scripts/fund_escrow.py --amount 1.0
  python scripts/fund_escrow.py --amount 0.50 --dry-run

Reads from .env / environment:
  ARC_RPC_URL, ARC_CONTRACT_ADDRESS, USDC_ADDRESS, PRIVATE_KEY,
  ARC_CHAIN_ID (optional, auto-detected if absent)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Allow running from any cwd.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


# Minimal ERC-20 ABI: only the functions we call.
_ERC20_ABI = [
    {
        "name": "approve",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "outputs": [{"name": "", "type": "bool"}],
    },
    {
        "name": "balanceOf",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "account", "type": "address"}],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "name": "decimals",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint8"}],
    },
    {
        "name": "allowance",
        "type": "function",
        "stateMutability": "view",
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"},
        ],
        "outputs": [{"name": "", "type": "uint256"}],
    },
]


def _load_env() -> dict:
    keys = ["ARC_RPC_URL", "ARC_CONTRACT_ADDRESS", "USDC_ADDRESS", "PRIVATE_KEY"]
    cfg = {k: os.environ.get(k, "").strip() for k in keys}
    cfg["ARC_CHAIN_ID"] = os.environ.get("ARC_CHAIN_ID", "0").strip()
    missing = [k for k in keys if not cfg[k]]
    if missing:
        print(f"[fund_escrow] ERROR: missing env vars: {', '.join(missing)}")
        sys.exit(1)
    return cfg


def _load_marketplace_abi() -> list:
    abi_path = Path(__file__).resolve().parent.parent / "smart_contracts" / "abi.json"
    if not abi_path.exists():
        print(f"[fund_escrow] ERROR: ABI not found at {abi_path}")
        sys.exit(1)
    return json.loads(abi_path.read_text())


def _send_tx(w3, fn, account, chain_id: int, label: str, dry_run: bool) -> str | None:
    tx = fn.build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 150_000,
        "gasPrice": w3.eth.gas_price,
        "chainId": chain_id,
    })
    if dry_run:
        print(f"[fund_escrow] DRY-RUN — would send tx for: {label}")
        print(f"  to={tx['to']}  gas={tx['gas']}  gasPrice={tx['gasPrice']}")
        return None
    signed = account.sign_transaction(tx)
    raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
    tx_hash = w3.eth.send_raw_transaction(raw)
    print(f"[fund_escrow] {label} → tx {tx_hash.hex()} (waiting for receipt…)")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    if receipt["status"] != 1:
        print(f"[fund_escrow] ERROR: tx reverted — {tx_hash.hex()}")
        sys.exit(1)
    print(f"[fund_escrow] {label} confirmed in block {receipt['blockNumber']}")
    return tx_hash.hex()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Approve and deposit USDC into the compute marketplace escrow.",
    )
    parser.add_argument(
        "--amount",
        type=float,
        required=True,
        help="Amount of USDC to deposit (human-readable, e.g. 1.0 = 1 USDC).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build and print transactions without broadcasting them.",
    )
    args = parser.parse_args()

    try:
        from web3 import Web3
        from eth_account import Account
    except ImportError:
        print("[fund_escrow] ERROR: web3 not installed. Run: pip install web3")
        sys.exit(1)

    cfg = _load_env()
    marketplace_abi = _load_marketplace_abi()

    w3 = Web3(Web3.HTTPProvider(cfg["ARC_RPC_URL"]))
    if not w3.is_connected():
        print(f"[fund_escrow] ERROR: cannot connect to RPC {cfg['ARC_RPC_URL']}")
        sys.exit(1)

    account = Account.from_key(cfg["PRIVATE_KEY"])
    chain_id = int(cfg["ARC_CHAIN_ID"]) or w3.eth.chain_id

    marketplace_addr = Web3.to_checksum_address(cfg["ARC_CONTRACT_ADDRESS"])
    usdc_addr = Web3.to_checksum_address(cfg["USDC_ADDRESS"])

    usdc = w3.eth.contract(address=usdc_addr, abi=_ERC20_ABI)
    marketplace = w3.eth.contract(address=marketplace_addr, abi=marketplace_abi)

    try:
        decimals = usdc.functions.decimals().call()
    except Exception:
        decimals = 6  # USDC is always 6 decimals
    amount_micro = int(round(args.amount * 10 ** decimals))

    print(f"[fund_escrow] Wallet:      {account.address}")
    print(f"[fund_escrow] USDC:        {usdc_addr}")
    print(f"[fund_escrow] Marketplace: {marketplace_addr}")
    print(f"[fund_escrow] Amount:      {args.amount} USDC ({amount_micro} units, decimals={decimals})")
    print(f"[fund_escrow] Chain ID:    {chain_id}")
    if args.dry_run:
        print("[fund_escrow] *** DRY-RUN MODE — no transactions will be broadcast ***")

    # Show current balances for context.
    try:
        wallet_balance = usdc.functions.balanceOf(account.address).call()
        marketplace_balance = marketplace.functions.get_balance(account.address).call()
        current_allowance = usdc.functions.allowance(account.address, marketplace_addr).call()
        print(f"\n[fund_escrow] Current wallet USDC balance:      {wallet_balance / 10**decimals:.6f}")
        print(f"[fund_escrow] Current marketplace balance:      {marketplace_balance / 10**decimals:.6f}")
        print(f"[fund_escrow] Current allowance to marketplace: {current_allowance / 10**decimals:.6f}\n")
    except Exception as exc:
        print(f"[fund_escrow] Could not fetch balances ({exc}); continuing…\n")

    # Step 1: approve
    approve_fn = usdc.functions.approve(marketplace_addr, amount_micro)
    _send_tx(w3, approve_fn, account, chain_id, "approve(marketplace, amount)", args.dry_run)

    # Step 2: deposit
    deposit_fn = marketplace.functions.deposit(amount_micro)
    _send_tx(w3, deposit_fn, account, chain_id, "deposit(amount)", args.dry_run)

    if not args.dry_run:
        try:
            new_balance = marketplace.functions.get_balance(account.address).call()
            print(f"\n[fund_escrow] New marketplace balance: {new_balance / 10**decimals:.6f} USDC")
        except Exception:
            pass
        print("\n[fund_escrow] Done. Consumer wallet is funded and ready for live settlement.")
    else:
        print("\n[fund_escrow] Dry-run complete. Re-run without --dry-run to broadcast.")


if __name__ == "__main__":
    main()
