# Demo Script — Agent-to-Agent Compute Marketplace

Use this as a 3-5 minute demo script for the lablab.ai submission video.

## Demo Goal

Show that the project makes **agent-to-agent compute payments economically viable** with programmable USDC and nanopayments:

- Agents register as compute providers.
- A consumer agent submits a paid compute job.
- The marketplace meters usage, prices the job under a `$0.01` per-unit ceiling, and settles USDC.
- Batch compute shows high-frequency payment behavior.
- Reputation and status pages prove the marketplace state updates after actions.

Algorithmic pattern: **event-driven marketplace workflow** with usage metering, price validation, settlement orchestration, and reputation ranking.

## Before Recording

Run the app in simulated settlement mode:

```bash
# Terminal 1: backend
cd /home/roc/quantumGlobalGroup/acm
source venv/bin/activate
SETTLEMENT_SIMULATE=true uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2: frontend
cd /home/roc/quantumGlobalGroup/acm/web
npm run dev
```

Open:

```text
http://127.0.0.1:3000
```

Use these demo addresses:

```text
Consumer: 0x1111111111111111111111111111111111111111
Provider: 0x3333333333333333333333333333333333333333
```

## Page Flow

Recommended order:

1. `/` — explain the problem and architecture.
2. `/status` — prove the backend and Arc config are connected.
3. `/providers` — register a provider.
4. `/compute` — run one paid compute request.
5. `/batch` — run multiple paid jobs and show volume economics.
6. `/leaderboard` — show reputation updated from successful work.
7. `/funding` — explain real Arc escrow and production settlement.

## Full Narration Script

### 1. Overview Page

Page: `/`

Say:

> This project is an Agent-to-Agent Compute Marketplace. The idea is simple: autonomous agents should be able to buy and sell compute without invoices, subscriptions, or human approval for every payment.
>
> A consumer agent requests work from a provider agent. The marketplace meters the usage, calculates a price, enforces a hard per-unit ceiling of one cent, and settles USDC through Arc.
>
> This matters because normal blockchain gas costs make tiny per-action payments uneconomical. Arc and Circle nanopayments make this kind of machine-to-machine commerce practical.

Point to:

- “Consumer agent requests compute”
- “Marketplace meters and prices the work”
- “Settlement on Arc”
- “Why agents need this”
- “Why Arc”

Transition:

> First, I’ll show that the live backend is connected and tracking marketplace state.

Click: `Status`

### 2. Status Page

Page: `/status`

Say:

> This page is reading directly from the FastAPI backend. For the public demo I’m running in simulated settlement mode, which means we can exercise the full product flow without exposing private keys or spending real testnet funds.
>
> The same settlement engine can switch to live Arc mode once a deployed contract, funded wallet, and escrow balance are configured.

Point to:

- Settlement mode
- Arc RPC
- Contract
- Total settlements
- Total settled
- Chain ID
- USDC address

Optional click: `Refresh`

Transition:

> Next, I’ll register a compute provider. This represents an autonomous agent advertising capacity into the marketplace.

Click: `Providers`

### 3. Provider Directory

Page: `/providers`

Say:

> This is the provider directory. Agents can advertise which tasks they support, their wallet address, pricing, and optional endpoint. The directory also shows reputation, success rate, latency, and completed jobs.

Click: `+ Register a provider`

Fill:

```text
Agent ID: provider-ui-demo
Wallet address: 0x3333333333333333333333333333333333333333
Default unit price: 0.0003
Display name: Demo Compute Provider
Description: Demo provider for image classification and model inference tasks.
Supported tasks: keep image classification selected
```

Click: `Register provider`led

Say:

> Now the provider is listed with a default unit price well below one cent. At this point, consumer agents can discover it and route work to it.

Transition:

> Now I’ll submit a paid compute request from a consumer agent to this provider.

Click: `Run compute`

### 4. Single Compute Request

Page: `/compute`

Fill:

```text
Task type: Image classification
Consumer address: 0x1111111111111111111111111111111111111111
Provider address: 0x3333333333333333333333333333333333333333
Estimated units: 100
Max price: 0.05
```

Click: `Submit and settle`

Say while it runs:

> When I submit this, the Next.js UI calls the backend through a server-side API route. The backend verifies the payment header, meters the work, calculates cost, checks the user’s max price, and then records settlement.

After result appears, say:

> The request settled successfully. We can see the task ID, status, USDC cost, and transaction hash placeholder. In live mode, this hash would point to the Arc transaction.
>
> This is the core economic proof: the system can charge per compute action, not per subscription or monthly invoice.

Optional: open `Raw response`.

Transition:

> One compute job is useful, but the hackathon requires high-frequency transaction behavior. I’ll show the batch workflow next.

Click: `Batch`

### 5. Batch Compute

Page: `/batch`

Say:

> This page demonstrates high-frequency usage. A consumer can submit many jobs together, and each job is still metered and represented in settlement state. The volume tiers show how the product can support repeated machine-to-machine actions.

For a quick recording, use:

```text
Number of jobs: 10
Consumer address: 0x1111111111111111111111111111111111111111
Provider address: 0x3333333333333333333333333333333333333333
Units per job: 10
Max price per job: 0.01
Allow partial: checked
```

Click: `Submit batch of 10`

Say:

> The batch applies a volume discount while preserving per-job accounting. This is important because agent systems may make many small calls, and the economics only work if each action is cheap enough to settle independently or near-independently.

After result appears, point to:

- Jobs settled
- Discount
- Gross cost
- Net cost
- Savings

Transition:

> Now that the provider has completed work, its reputation should update.

Click: `Leaderboard`

### 6. Leaderboard

Page: `/leaderboard`

Say:

> The leaderboard ranks providers by reputation. The score combines success rate, completed jobs, and latency. This gives consumer agents a signal for provider selection instead of relying on a centralized operator.

Click the provider row.

Say:

> Expanding the provider shows recent events. This connects the compute workflow to the reputation system: successful work increases provider credibility over time.

Point to:

- Score
- Success rate
- Average latency
- Jobs
- Recent events

Transition:

> Finally, I’ll explain how real USDC escrow works when moving from demo mode to live Arc settlement.

Click: `Funding`

### 7. Funding Page

Page: `/funding`

Say:

> In live mode, the consumer wallet needs an internal marketplace balance. Funding only the wallet is not enough. The consumer first approves USDC, then deposits into the marketplace contract.
>
> After that, each `pay_for_compute` call debits the consumer’s escrow balance and credits the provider in one settlement path. This avoids repeated approval overhead and keeps per-task payments economically viable.

Point to:

- Approve
- Deposit
- `pay_for_compute`
- Operator command
- Why escrow

Transition to close:

> So the full product loop is: providers register capacity, consumers buy compute, the backend meters and prices usage under a one-cent ceiling, settlement records update, and reputation makes the market discoverable.

## Closing Pitch

Say:

> Agent-to-Agent Compute Marketplace shows how programmable USDC and Arc nanopayments can unlock a new economic model for AI agents. Instead of subscriptions or manual billing, agents can pay for exactly the compute they use, at sub-cent prices, with transparent settlement and reputation.
>
> The demo runs safely in simulated mode for public review, and the same architecture supports live Arc settlement once the contract, funded wallet, and marketplace escrow are configured.

## Short 60-Second Version

Use this if you need a short video:

1. Start on `/`.
   > This is an Agent-to-Agent Compute Marketplace where autonomous agents buy and sell compute with USDC.

2. Jump to `/providers`.
   > Providers register their wallet, supported task types, and pricing.

3. Jump to `/compute`.
   > A consumer submits a task. The backend meters usage, checks the price ceiling, and settles the payment.

4. Jump to `/batch`.
   > Batch mode shows high-frequency compute jobs and volume discounts.

5. Jump to `/leaderboard`.
   > Successful work updates provider reputation, giving agents a way to choose reliable providers.

6. Jump to `/status`.
   > The backend tracks settlement counts, total volume, Arc metadata, and simulation/live mode.

Close:

> The key point is economic viability: this model fails with traditional gas costs but works with Arc, USDC, and nanopayments.

## If Something Goes Wrong During Recording

If the backend is unreachable:

```bash
cd /home/roc/quantumGlobalGroup/acm
source venv/bin/activate
SETTLEMENT_SIMULATE=true uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

If the UI is unreachable:

```bash
cd /home/roc/quantumGlobalGroup/acm/web
npm run dev
```

If the leaderboard is empty:

1. Register a provider on `/providers`.
2. Run one compute request on `/compute` using that provider wallet.
3. Refresh `/leaderboard`.

If a compute request is rejected:

- Confirm consumer and provider addresses are different.
- Confirm both are valid `0x` addresses with 40 hex characters.
- Keep `max_price_usdc` high enough for the demo, such as `0.05`.

## Submission Talking Points

- Project aligns with **Agent-to-Agent Payment Loop**.
- Project aligns with **Usage-Based Compute Billing**.
- Per-unit price ceiling is `$0.01`.
- Backend includes metering, pricing, settlement, provider registry, and reputation.
- Frontend includes compute submission, batch jobs, provider discovery, leaderboard, status, and funding explanation.
- Simulated mode is used for safe public demo hosting.
- Live mode requires funded Arc testnet credentials, deployed contract, and marketplace escrow.
