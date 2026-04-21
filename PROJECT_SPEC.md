# Agent-to-Agent Compute Marketplace
## Arc x Circle x Hackathon Submission

---

## 1. Project Vision

**What it is:** A trustless marketplace where autonomous AI agents both *consume* and *provide* computational services, paying each other in USDC per query/computation with real-time settlement on Arc.

**Why it matters:**
- **Agent autonomy:** Agents manage their own wallets (Circle Wallets) and make independent payment decisions
- **Efficient pricing:** Unlike traditional gas fees (which would be $0.50–$5 per transaction), Nanopayments enable sub-cent pricing ≤$0.01
- **Proof of economic viability:** Real-world use case that fails without Nanopayments but thrives with them

**Example user story:**
1. **Consumer Agent** needs to classify 1,000 images → requests from Provider Agent
2. **Provider Agent** processes them, metering usage: 1,000 classifications @ $0.0001 each = $0.10 total
3. **Pricing engine** calculates cost based on actual compute consumed
4. **Settlement engine** atomically transfers $0.10 USDC from Consumer → Provider on Arc
5. Both agents' wallets settle in real-time; no batching needed

---

## 2. Core Requirement Alignment

### ✓ Real per-action pricing (≤ $0.01)
- **Agent-to-Agent:** Consumer pays $0.0001–$0.001 per computation
- **Usage-Based:** Metering tied to actual resource consumption (tokens, queries, compute units)
- **Why this works:** Nanopayments eliminate gas cost friction; traditional EVM would cost $1–$5 per tx

### ✓ 50+ onchain transactions in demo
- **Script generates 50+ sequential payments** across different agents
- **Each computation = 1 Arc tx** (via x402 facilitator)
- **Real settlement:** Consumer wallets → Arc → Provider wallets

### ✓ Margin explanation
**Traditional model fails:**
- Gas: $1–$5 per transaction
- For $0.10 compute job: 10–50× overhead
- Economic incentive: Wait and batch, sacrificing real-time payment

**Nanopayments model succeeds:**
- Gas: embedded in Nanopayments (near-zero)
- For $0.10 compute job: Margin is real, payment happens immediately
- Economic incentive: Agents trust real-time settlement

---

## 3. Hackathon Track Alignment

### 🤖 Agent-to-Agent Payment Loop
- Consumer and Provider agents are **autonomous entities** with independent wallets
- **Real-time payment** for each computation (no batching)
- **Trustless:** Smart contract enforces payment atomicity (no platform custody)

### 🧮 Usage-Based Compute Billing
- **Metering:** Track tokens consumed, queries processed, compute units used
- **Pricing:** Calculate cost per unit ($0.0001–$0.001 per action)
- **Settlement:** Charge only for what was consumed, immediately

---

## 4. System Architecture

### 4.1 High-Level Flow

```
Consumer Agent (has $10 USDC)
  ↓ [1. sendRequest("classify images", params)]
  ↓
Request/Response Handler
  ↓ [2. Forward to Provider]
  ↓
Provider Agent (listening on Arc)
  ↓ [3. Execute computation]
  ↓
Usage Metering Engine
  ↓ [4. Calculate cost: 1,000 classifications × $0.0001 = $0.10]
  ↓
Pricing Engine
  ↓ [5. Confirm price ≤ $0.01 per unit (✓)]
  ↓
Settlement Engine
  ↓ [6. Call Arc smart contract]
  ↓
Arc Smart Contract
  ↓ [Transfer $0.10 USDC: Consumer → Provider]
  ↓
Circle Wallets (via Circle Gateway)
  ↓ [Consumer balance: $10 → $9.90, Provider balance: $0 → $0.10]
```

### 4.2 Component Breakdown

#### 1. **Consumer Agent** (LLM-powered, autonomous)
- **Wallet:** Circle Wallet (programmatic, KMS-backed)
- **Balance check:** Ensure sufficient USDC before requesting
- **Request logic:** Decide what compute to buy (based on internal goals)
- **Payment approval:** Sign x402 payment header (automated, per-request)

#### 2. **Provider Agent** (LLM-powered, autonomous)
- **Wallet:** Circle Wallet (same as Consumer)
- **Service:** Expose compute endpoint (e.g., image classification, data analysis)
- **Metering:** Track resources used (tokens, queries, walltime)
- **Payment receipt:** Verify Arc tx confirms payment before returning result

#### 3. **Request/Response Handler**
- **Protocol:** x402 (web-native payment standard)
- **Headers:** Consumer includes payment proof in request
- **Endpoint:** `/api/compute` (POST with x402 header)
- **Authentication:** x402 facilitator validates payment signature

#### 4. **Usage Metering Engine**
- **Input:** Compute task parameters (num queries, tokens, time)
- **Output:** Usage report (quantity, unit cost, total)
- **Example:**
  ```
  Task: Classify 1,000 images
  Unit cost: $0.0001 per image
  Total: 1,000 × $0.0001 = $0.10
  ```

#### 5. **Pricing Engine**
- **Input:** Usage report
- **Output:** Final price (must be ≤$0.01 per unit)
- **Logic:**
  ```python
  unit_cost = base_cost * (1 + compute_intensity_multiplier)
  total_cost = unit_cost * quantity
  assert unit_cost <= 0.01, "Price too high"
  ```

#### 6. **Settlement Engine**
- **Input:** Consumer address, Provider address, USDC amount
- **Output:** Arc tx hash
- **Actions:**
  1. Call Arc smart contract `payForCompute(consumer, provider, amount_usdc)`
  2. Contract deducts from consumer's balance (Circle Wallet)
  3. Contract credits provider's balance (Circle Wallet)
  4. Return tx hash as proof-of-settlement

#### 7. **Arc Smart Contract** (Vyper or Solidity)
- **State:** `agent_balances[address] → uint256` (USDC)
- **Functions:**
  - `deposit(amount)`: Agent deposits USDC via Circle Gateway
  - `payForCompute(consumer, provider, amount)`: Atomic transfer
  - `withdraw(amount)`: Agent withdraws USDC back to Circle Wallet
  - `getBalance(agent)`: Check agent's USDC balance

#### 8. **Circle Integration**
- **Circle Wallets:** Programmable wallets for agents (controlled by Circle API)
- **Circle Gateway:** Unified USDC balance (cross-chain visibility)
- **x402 Facilitator:** Validates x402 payment headers, submits to Arc
- **Circle Bridge:** Cross-chain USDC movement (if needed)

---

## 5. Tech Stack

### Backend
- **Language:** Python 3.10+ (LangChain agents) or Node.js (agentic SDK)
- **Framework:** FastAPI (Python) or Express (Node.js)
- **Agents:** LangChain ReAct agents (autonomous decision-making)
- **Metering:** Custom usage tracking module

### Smart Contracts
- **Language:** Vyper (recommended) or Solidity
- **Network:** Arc (EVM-compatible, USDC is native)
- **Libraries:** Circle-titanoboa-sdk (Vyper + x402) or OpenZeppelin (Solidity)

### Payments & Settlement
- **Circle Nanopayments:** Sub-cent transaction support
- **x402 Facilitator:** Web-native payment standard validator
- **Circle Wallets API:** Programmatic wallet control
- **Circle Gateway:** Cross-chain USDC management

### Demo Infrastructure
- **Transaction Generator:** Script that spins up 10 agents, runs 50+ compute tasks
- **Dashboard:** Real-time settlement visualization (Arc tx explorer)
- **Testnet:** Arc testnet with faucet for USDC

---

## 6. Demo & Transaction Strategy

### Goal: 50+ onchain transactions

**Approach:**
```
1. Spin up 2 Consumer Agents + 3 Provider Agents (5 total)
2. Each Consumer Agent requests 10 compute jobs
3. Each job = 1 payment transaction on Arc
4. Total: 2 Consumers × 10 jobs × 3 Providers = 60 transactions
5. Run in parallel to keep demo time under 5 minutes
```

### Example Demo Script
```bash
# 1. Fund all agents with USDC on Arc testnet
$ python fund_agents.py --count 5 --amount 5.0

# 2. Start provider agents (listening)
$ python agents/provider.py --agent-id provider-1 &
$ python agents/provider.py --agent-id provider-2 &
$ python agents/provider.py --agent-id provider-3 &

# 3. Run consumer agents (request compute, pay)
$ python agents/consumer.py --agent-id consumer-1 --jobs 10 &
$ python agents/consumer.py --agent-id consumer-2 --jobs 10 &

# 4. Monitor settlements in real-time
$ python dashboard.py --show-transactions

# 5. Verify 50+ txs on Arc explorer
```

### Expected Output
```
✓ 60 onchain transactions (50+ required)
✓ Average settlement time: 2–5 seconds per transaction
✓ Total cost: ~$0.006 per transaction (Nanopayments + Arc gas)
✓ Margin analysis: Traditional gas would cost $1–$5 (167–833× overhead)
```

---

## 7. Margin Analysis: Why Traditional Gas Fails

| Factor | Traditional EVM | Arc + Nanopayments |
|--------|-----------------|-------------------|
| Gas cost per tx | $1–$5 | $0.00001–$0.0001 |
| Tx for $0.10 job | ❌ 10–50× loss | ✓ Profitable |
| Provider incentive | Batch 100s of jobs (latency) | Settle per-action (real-time) |
| Agent autonomy | Impractical (can't afford individual txs) | Practical (sub-cent settlement) |
| Use case viability | Dead on arrival | Economically viable |

**Conclusion:** Without Nanopayments, agent-to-agent compute markets cannot exist at per-action granularity. Arc + Nanopayments makes them real.

---

## 8. Submission Checklist

### Code Deliverables
- [ ] Agent framework (Consumer + Provider)
- [ ] Smart contract (Arc, Vyper)
- [ ] Request/response handler (x402-compatible)
- [ ] Usage metering + pricing engine
- [ ] Settlement orchestrator
- [ ] Integration with Circle Wallets + Nanopayments
- [ ] Demo script (generates 50+ txs)

### Documentation
- [ ] README with setup instructions
- [ ] Architecture diagram (included above)
- [ ] API documentation (request/response format)
- [ ] Usage metering specification
- [ ] Pricing model explanation
- [ ] Arc contract ABI + deployment guide

### Demo Materials
- [ ] Video (2–3 min): Run demo, show 50+ Arc txs, explain economics
- [ ] Screenshots: Agent balances before/after, Arc explorer (50+ txs)
- [ ] Transaction logs: Proof of settlement
- [ ] Dashboard: Real-time settlement visualization

### Feedback Submission (for $500 USDC bonus)
- [ ] Detailed feedback on Circle Nanopayments (UX, limitations, ideas)
- [ ] Feedback on Arc (developer experience, gas model, tooling)
- [ ] Feedback on x402 standard (adoption, clarity, improvements)
- [ ] Feedback on Vyper/titanoboa-sdk (ease of use, docs)
- [ ] Suggestions for future hackathons / developer programs

---

## 9. Success Criteria

1. **Economic proof:** ≤$0.01 per-action pricing, real settlement
2. **Autonomous agents:** Both Consumer and Provider make independent decisions
3. **Real transactions:** 50+ verified onchain transactions (Arc explorer)
4. **Trustless:** No platform custody; settlement is atomic via smart contract
5. **Scalable:** Demo runs 60 txs in <5 minutes with low latency
6. **Documented:** Clear explanation of why this fails without Nanopayments

---

## 10. Next Steps

1. **Set up Circle Developer Account** (same email as hackathon registration)
2. **Deploy Arc testnet contract** (Vyper smart contract)
3. **Implement agents** (LangChain ReAct, autonomous decision-making)
4. **Build metering + pricing** (usage tracking, per-unit costs)
5. **Integrate Circle Wallets + x402** (payment flows)
6. **Run demo script** (generate 50+ transactions)
7. **Record submission video** (2–3 min walkthrough)
8. **Write feedback** (detailed, actionable; $500 bonus)
9. **Submit** (code repo + demo video + feedback form)

---

## 11. Resources

- **Arc:** https://docs.arc.io
- **Circle Nanopayments:** https://developers.circle.com/nanopayments
- **Circle Wallets:** https://developers.circle.com/wallets
- **x402 Standard:** https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/402
- **Circle-titanoboa-sdk:** https://github.com/circle/circle-titanoboa-sdk
- **Vyper Docs:** https://docs.vyperlang.org
- **LangChain Agents:** https://docs.langchain.com/agents
- **Circle Testnet Faucet:** https://testnet.circle.com/faucet

---

**Estimated Timeline:** 3–4 days of development + 1 day for documentation and feedback

**Team Size:** 1–2 developers (full-stack with smart contracts)

**Difficulty:** Medium–High (agents + smart contracts + payments integration)

**Winning Potential:** High (novel combination of tracks, clear economic justification, ambitious scope)
