"""Run the full integration loop. Backend must be running at http://localhost:8000."""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.integration import MarketplaceIntegration  # noqa: E402


async def amain(transactions: int, consumers: int, providers: int) -> int:
    integration = MarketplaceIntegration()
    integration.setup_agents(num_consumers=consumers, num_providers=providers)
    await integration.run_marketplace(transactions=transactions)
    summary = await integration.verify()
    await integration.close()
    if summary["transaction_count"] < transactions:
        print(f"[integration] WARN: settled {summary['transaction_count']} of {transactions}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--transactions", type=int, default=60)
    parser.add_argument("--consumers", type=int, default=2)
    parser.add_argument("--providers", type=int, default=3)
    args = parser.parse_args()
    return asyncio.run(amain(args.transactions, args.consumers, args.providers))


if __name__ == "__main__":
    sys.exit(main())
