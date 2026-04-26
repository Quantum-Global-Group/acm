## Learned User Preferences

- When following an attached implementation plan, do not edit the plan file itself; use the existing todo list and mark items `in_progress` / `completed` as work proceeds.
- For exercising the stack without real on-chain transactions, keep simulated settlement on (`SETTLEMENT_SIMULATE=true`) and use pytest, `demo.py`, and/or integration scripts against the local API instead of live settlement.
- Prefer onboarding in the order the repo documents: start from `README_SETUP_FIRST.txt`, then the day-by-day guides (`00_START_HERE.md`, `GETTING_STARTED.md`, etc.) when configuring Arc and the rest of the stack.

## Learned Workspace Facts

- Official Arc testnet uses chain ID **5042002** (`eth_chainId` `0x4cef52`). Primary RPC: `https://rpc.testnet.arc.network` (WebSocket: `wss://rpc.testnet.arc.network`). Provider-backed and aggregator alternates are listed in `arc_auto_discover.py`, `discover_rpc_endpoints.py`, and `ARC_CONFIG_QUICK_REFERENCE.md`.
- Arc testnet native USDC contract address (public, from Arc contract references): `0x3600000000000000000000000000000000000000` — set `USDC_ADDRESS` to this for deploy and backend when using that token; it must be non-empty for `scripts/deploy_contract.py`.
- `demo.py` splits `--agents` into `num_agents // 2` consumers and the remainder as providers; total jobs = `num_consumers * jobs_per_consumer`, and the script asserts at least 50 completed tasks (e.g. `--agents 10 --jobs-per-consumer 10` → 50 jobs, or `--agents 5 --jobs-per-consumer 30` → 60).
- `scripts/deploy_contract.py` requires non-empty `ARC_RPC_URL`, `PRIVATE_KEY`, and `USDC_ADDRESS` in `.env` (blank `USDC_ADDRESS=` triggers the missing-variable error).
- Success paths (`demo.py`, `validate_config.py`, integration scripts, backend) report to stdout, HTTP responses, or in-memory engine state; nothing writes a default “run succeeded” audit file—capture output with shell redirection (e.g. `tee` to a log) or CI if you need a durable record.
- For live (non-simulated) `pay_for_compute`, the consumer address must have **on-marketplace** USDC in the contract ledger (`approve` the USDC, then `deposit` to the marketplace); funding only the EOA wallet is not enough for the contract’s internal balance checks.
- `demo.py` is an offline/in-memory simulation: it does not read `.env` or `SETTLEMENT_SIMULATE`, does not call Arc, and generates fake transaction hashes; use the live backend plus `scripts/run_integration.py` for real on-chain settlements.
- Live settlement sends transactions through the backend signer `PRIVATE_KEY`; parallel integration traffic can race nonces, so use serialized requests/single funded consumer or explicitly fund and wire additional consumers before running multi-consumer live tests.
- Deployment/live-run logs are captured under `artifacts/` with timestamped `tee` outputs such as `deploy_*.txt`, `fund_escrow_*.txt`, `backend_live_*.txt`, and `integration_live_*.txt`.
