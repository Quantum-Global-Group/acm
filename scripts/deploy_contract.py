"""
Deploy compute_marketplace.vy to Arc testnet.

Reads:
  - smart_contracts/bytecode.txt
  - smart_contracts/abi.json
  - .env (ARC_RPC_URL, PRIVATE_KEY, USDC_ADDRESS)

Writes:
  - smart_contracts/contract_address.txt
  - Updates ARC_CONTRACT_ADDRESS in .env

Usage:
  python scripts/deploy_contract.py
"""
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv, set_key
from eth_account import Account
from web3 import Web3

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"
BYTECODE_FILE = ROOT / "smart_contracts" / "bytecode.txt"
ABI_FILE = ROOT / "smart_contracts" / "abi.json"
ADDRESS_FILE = ROOT / "smart_contracts" / "contract_address.txt"


def main() -> int:
    load_dotenv(ENV_FILE)

    rpc_url = os.getenv("ARC_RPC_URL")
    private_key = os.getenv("PRIVATE_KEY")
    usdc_address = os.getenv("USDC_ADDRESS")
    chain_id = int(os.getenv("ARC_CHAIN_ID", "0") or 0)

    if not all([rpc_url, private_key, usdc_address]):
        print("ERROR: Missing ARC_RPC_URL, PRIVATE_KEY, or USDC_ADDRESS in .env")
        return 1

    if usdc_address.lower() == "0x" + "0" * 40:
        print("ERROR: USDC_ADDRESS in .env is the zero address. Set the real Arc USDC address.")
        return 1

    bytecode = BYTECODE_FILE.read_text().strip()
    if not bytecode.startswith("0x"):
        bytecode = "0x" + bytecode

    abi = json.loads(ABI_FILE.read_text())

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print(f"ERROR: Could not connect to RPC {rpc_url}")
        return 1

    account = Account.from_key(private_key)
    print(f"Deploying from: {account.address}")
    print(f"USDC token:     {usdc_address}")
    print(f"RPC:            {rpc_url}")

    balance_wei = w3.eth.get_balance(account.address)
    print(f"Native balance: {w3.from_wei(balance_wei, 'ether')}")

    contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    constructor = contract.constructor(Web3.to_checksum_address(usdc_address))

    nonce = w3.eth.get_transaction_count(account.address)
    gas_estimate = constructor.estimate_gas({"from": account.address})
    print(f"Gas estimate:   {gas_estimate}")

    tx = constructor.build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": int(gas_estimate * 1.2),
        "gasPrice": w3.eth.gas_price,
        "chainId": chain_id or w3.eth.chain_id,
    })

    signed = account.sign_transaction(tx)
    raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
    tx_hash = w3.eth.send_raw_transaction(raw)
    print(f"Submitted:      {tx_hash.hex()}")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    if receipt.status != 1:
        print(f"ERROR: deployment reverted (status={receipt.status})")
        return 1

    address = receipt.contractAddress
    print(f"\nDeployed at:    {address}")
    print(f"Explorer:       {os.getenv('ARC_EXPLORER_URL', '')}/address/{address}")

    ADDRESS_FILE.write_text(address + "\n")
    set_key(str(ENV_FILE), "ARC_CONTRACT_ADDRESS", address)
    print(f"Saved to {ADDRESS_FILE} and {ENV_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
