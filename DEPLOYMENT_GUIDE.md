# Deployment Guide
## Deploy to Arc Testnet

Final deployment and configuration steps.

---

## 🎯 Deployment Checklist

- [ ] Smart contract deployed and verified
- [ ] Backend environment configured
- [ ] Agents funded with testnet USDC
- [ ] All endpoints tested
- [ ] Integration verified
- [ ] Ready for demo

---

## 🚀 Step 1: Smart Contract Verification

```bash
# Verify contract on Arc
curl https://testnet.arc.io/api/eth/contracts/$(cat smart_contracts/contract_address.txt)

# Should show:
# - Contract bytecode
# - Creation transaction
# - Function signatures
```

---

## 🔧 Step 2: Production Configuration

Create `.env.production`:

```bash
# Arc Network
ARC_RPC_URL=https://arc-testnet-rpc.io
ARC_CHAIN_ID=11155111
ARC_CONTRACT_ADDRESS=0x...from_deploy

# Circle API (production keys from dashboard)
CIRCLE_API_KEY=sk_prod_...
CIRCLE_ENTITY_ID=...
X402_FACILITATOR_URL=https://...

# Backend
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# Agent Wallets (from Circle)
CONSUMER_WALLET_ADDRESS=0x...
PROVIDER_WALLET_ADDRESS=0x...

# USDC
USDC_ADDRESS=0x...arc_usdc
```

Deploy config:
```bash
cp .env.production .env
```

---

## 💰 Step 3: Fund Agents

```bash
# Request testnet USDC for each agent
# Visit: https://testnet.circle.com/faucet

# For each consumer agent wallet:
# 1. Enter wallet address
# 2. Request $100 testnet USDC
# 3. Wait for confirmation

# Verify funding:
python scripts/check_balances.py
```

---

## 🌐 Step 4: Deploy Backend

```bash
# Production deployment options:

# Option 1: Docker
docker build -t marketplace-backend .
docker run -p 8000:8000 \
  --env-file .env.production \
  marketplace-backend

# Option 2: Cloud (AWS Lambda, Google Cloud Run)
# Deploy FastAPI via serverless

# Option 3: VPS (AWS EC2, DigitalOcean)
ssh user@server.com
git clone <repo>
cd agent-compute-marketplace
python -m backend.main --host 0.0.0.0 --port 80

# Option 4: Local development
python -m backend.main
```

---

## ✅ Step 5: Verify Deployment

```bash
# Health check
curl https://your-domain/health

# Get metrics
curl https://your-domain/api/metrics

# Test compute request
curl -X POST https://your-domain/api/compute \
  -H "X-402-Payment: proof" \
  -d '{"task_id":"test",...}'
```

---

## 📊 Step 6: Monitor

Create `monitoring/health_check.py`:

```python
"""Monitor deployed service"""
import asyncio
import httpx
import time
from datetime import datetime

async def health_check(api_endpoint: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{api_endpoint}/health", timeout=5)
            if response.status_code == 200:
                print(f"✓ {datetime.now()} - Health OK")
                return True
            else:
                print(f"✗ Status {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

async def monitor(api_endpoint: str, interval: int = 60):
    """Continuous monitoring"""
    while True:
        await health_check(api_endpoint)
        await asyncio.sleep(interval)

if __name__ == "__main__":
    asyncio.run(monitor("http://localhost:8000"))
```

Run: `python monitoring/health_check.py`

---

## 📋 Deployment Checklist

- [ ] Contract address saved in `.env`
- [ ] USDC address configured
- [ ] Backend environment configured
- [ ] All agents funded
- [ ] Health endpoints responding
- [ ] Settlement engine working
- [ ] Agents can request compute
- [ ] Payments settling on Arc

---

## 🚨 Troubleshooting

### "Connection refused" at RPC
- Check Arc testnet status
- Verify RPC URL in .env
- Try alternative RPC endpoint

### "Insufficient balance"
- Request more testnet USDC
- Check wallet funding

### "Contract not found"
- Verify contract address
- Check contract deployed correctly
- Visit Arc explorer

---

## ✅ Completion

**Deployment ready! 🎉**

Next: DEMO_EXECUTION.md
