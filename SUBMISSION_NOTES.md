# Submission Notes — Agent-to-Agent Compute Marketplace

## What's in this repo

| Layer | Path | Status |
|------|------|--------|
| Smart contract | [`compute_marketplace.vy`](compute_marketplace.vy) | Compiles green (Vyper 0.3.10). Bytecode + ABI in `smart_contracts/`. |
| Deployment | [`scripts/deploy_contract.py`](scripts/deploy_contract.py) | Deploys to Arc when RPC + funded wallet are configured. |
| Backend | [`backend/`](backend/) | FastAPI app with metering / pricing / settlement engines. |
| Agents | [`backend/agents/`](backend/agents/) | `ConsumerAgent`, `ProviderAgent`, `AgentManager`. |
| Integration | [`backend/integration.py`](backend/integration.py), [`scripts/run_integration.py`](scripts/run_integration.py) | Drives the marketplace through the live backend. |
| Demo | [`demo.py`](demo.py) | Self-contained 60-tx demo. |
| Tests | [`tests/`](tests/) | 17 tests, all passing. |
| Feedback | [`FEEDBACK.md`](FEEDBACK.md) | 1,212-word draft for the $500 USDC bonus. |

## Verifiable results (offline mode)

Run sequence:
```bash
source venv/bin/activate
pytest tests/ --asyncio-mode=auto -q     # 17 passed
python demo.py --agents 5 --jobs-per-consumer 30   # 60 settled, all $0.01/tx
SETTLEMENT_SIMULATE=true python -m backend.main &
python scripts/run_integration.py --transactions 60 --consumers 2 --providers 3
```

Artifacts:
- `artifacts/demo_capture.txt` — full text capture of a 60-transaction run (proxy for the screen recording).
- `smart_contracts/abi.json` + `smart_contracts/bytecode.txt` — deployable artifacts.

## What requires manual action before live submission

1. **Real Arc RPC + USDC address** — the canonical values are not in the starter kit's `arc_auto_discover.py`; obtain from Arc docs / Discord and update `.env`.
2. **Fund the wallet** — `0xBBFd3B891f87d5429CBf92FA029E9ba2fAa0290a` (generated for this build) needs Arc testnet USDC from `https://testnet.circle.com/faucet`.
3. **Deploy contract** — `python scripts/deploy_contract.py` once 1+2 are satisfied. The script writes `ARC_CONTRACT_ADDRESS` back into `.env`.
4. **Switch to live mode** — set `SETTLEMENT_SIMULATE=false` in `.env`. Re-run `demo.py` (or the integration script) to generate 50+ real Arc transactions.
5. **Record demo video** — follow [`VIDEO_SUBMISSION.md`](VIDEO_SUBMISSION.md). Show: starting balances, run command, live tx hashes, Arc explorer.
6. **Push public repo & submit** — `git push` to GitHub, fill the hackathon portal, paste `FEEDBACK.md` for the bonus.

## Pricing math (sanity-check column for judges)

| Knob | Value |
|------|------|
| `base_unit_price` | $0.0001 / unit |
| `compute_time_multiplier` | $0.00001 / extra-second |
| `token_multiplier` | $0.000001 / token |
| Hard ceiling | $0.01 / unit (enforced both off-chain and on-chain) |
| Demo per-transaction cost | $0.01 (max ceiling) |
| Demo total volume (60 tx) | $0.60 |
| Equivalent traditional gas | $60 – $300 (167–833× overhead) |

## Test summary

```
tests/test_api.py ............. 5 passed
tests/test_engines.py ......... 9 passed
tests/test_full_flow.py ....... 2 passed
tests/test_performance.py ..... 1 passed (60 tx in <1s in-process)
17 passed in 0.21s
```

## Architecture

```
ConsumerAgent ──[POST /api/compute + X-402-Payment]──▶ FastAPI
                                                      │
                                          ┌───────────┼──────────────┐
                                          ▼           ▼              ▼
                                     metering     pricing       settlement
                                   (record_usage) (≤$0.01/u)   (sim or live Arc)
                                                                  │
                                                                  ▼
                                                          compute_marketplace.vy
                                                          pay_for_compute()
                                                                  │
                                                                  ▼
                                                          USDC: consumer→provider
```

## Known limitations

- `arc_auto_discover.py` placeholder URLs do not resolve — deferred to manual configuration.
- Settlement live-mode signs from a single relayer key (`PRIVATE_KEY` in `.env`); a production version would have each consumer sign its own pay_for_compute call directly.
- Only `pay_for_compute` is exercised by the agent flow; `batch_payments`, `deposit`, and `withdraw` are tested at the contract level only.
