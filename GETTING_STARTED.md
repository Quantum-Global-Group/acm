# Getting Started: Agent-to-Agent Compute Marketplace
## Complete Build Guide

This guide walks you through building the entire Agent-to-Agent Compute Marketplace from scratch.

---

## 📋 Prerequisites

Before starting, you'll need:

### System Requirements
- **Python:** 3.10 or higher
- **Node.js:** 16+ (optional, for Hardhat deployment)
- **Git:** For version control
- **OS:** macOS, Linux, or Windows (WSL2)

### Developer Accounts
- **Circle Developer Account** — https://developers.circle.com
  - Sign up at https://dashboard.circle.com
  - Use the same email as your hackathon registration
  - Keep your API key safe

- **GitHub Account** — For repo hosting
  - Create a new public repo for submission

- **Arc Testnet Account** — For smart contract deployment
  - Visit https://testnet.arc.io
  - Fund via faucet at https://testnet.circle.com/faucet
  - Request ~$10 USDC for testing

### Knowledge Requirements
- Familiar with Python async/await
- Basic understanding of smart contracts (Vyper or Solidity)
- HTTP APIs and REST concepts
- Blockchain fundamentals (addresses, transactions, gas)

---

## 🎯 Project Overview

### What You're Building

A trustless marketplace where autonomous AI agents:
1. **Consume** compute services (image classification, data processing, etc.)
2. **Provide** compute services (execute tasks)
3. **Settle payments** in USDC via Arc in real-time
4. **Track usage** per unit (query, token, image, etc.)
5. **Calculate pricing** dynamically (≤ $0.01 per action)

### Architecture at a Glance

```
Consumer Agent → Request/Response Handler → Provider Agent
      ↓              Metering Engine              ↓
      └─→ Pricing Engine → Settlement Engine → Arc Contract
                              ↓
                         Circle Wallets
                         (Balance update)
```

### End-to-End Flow

1. Consumer agent has $10 USDC in Circle Wallet
2. Consumer requests 1,000 image classifications from Provider
3. Metering engine tracks usage: 1,000 × $0.0001 = $0.10
4. Pricing engine validates: $0.0001 ≤ $0.01 per unit ✓
5. Settlement engine calls Arc smart contract
6. Arc transfers $0.10 from Consumer to Provider
7. Both agents' wallets update in real-time
8. Provider verifies payment and returns result
9. Process repeats for next 49+ transactions

---

## 📁 Project Structure

```
agent-compute-marketplace/
├── smart_contracts/
│   ├── compute_marketplace.vy      # Vyper contract
│   ├── contracts.json              # ABI export
│   └── deployment_log.txt          # Contract address log
│
├── backend/
│   ├── main.py                     # FastAPI app
│   ├── engines/
│   │   ├── metering.py             # Usage tracking
│   │   ├── pricing.py              # Cost calculation
│   │   └── settlement.py           # Arc payments
│   ├── agents/
│   │   ├── consumer.py             # Consumer agent logic
│   │   └── provider.py             # Provider agent logic
│   ├── models.py                   # Pydantic models
│   ├── config.py                   # Configuration
│   └── requirements.txt
│
├── scripts/
│   ├── demo.py                     # Generate 50+ transactions
│   ├── fund_agents.py              # Testnet funding
│   └── verify_transactions.py      # Check Arc explorer
│
├── tests/
│   ├── test_pricing.py
│   ├── test_metering.py
│   └── test_settlement.py
│
├── docs/
│   ├── GETTING_STARTED.md          # This file
│   ├── SMART_CONTRACT_GUIDE.md
│   ├── BACKEND_SETUP.md
│   ├── AGENT_IMPLEMENTATION.md
│   ├── INTEGRATION_GUIDE.md
│   ├── TESTING_GUIDE.md
│   ├── DEPLOYMENT_GUIDE.md
│   ├── DEMO_EXECUTION.md
│   └── VIDEO_SUBMISSION.md
│
├── .env.example                     # Environment template
├── .gitignore
├── README.md                        # Project overview
└── requirements.txt                 # Python dependencies
```

---

## 🚀 Quick Start (30 mins)

### Step 1: Clone & Setup Environment

```bash
# Create project directory
mkdir agent-compute-marketplace
cd agent-compute-marketplace

# Initialize git repo
git init
git config user.email "your-email@example.com"
git config user.name "Your Name"

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows

# Create directory structure
mkdir -p smart_contracts backend/engines backend/agents scripts tests docs

# Create .gitignore
cat > .gitignore << 'EOF'
# Virtual environments
venv/
env/
.env
.env.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/

# Smart contracts
bytecode/
*.json

# Logs
*.log
logs/
EOF
```

### Step 2: Install Dependencies

```bash
# Create requirements.txt
cat > requirements.txt << 'EOF'
# Web framework
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0

# HTTP client
httpx==0.25.1

# Blockchain
web3.py==6.11.1

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1

# Utilities
python-dotenv==1.0.0
EOF

# Install dependencies
pip install -r requirements.txt

# Install Vyper for smart contracts
pip install vyper==0.3.10
```

### Step 3: Create Configuration

```bash
# Create .env.example
cat > .env.example << 'EOF'
# Circle API
CIRCLE_API_KEY=sk_test_your_key_here
CIRCLE_ENTITY_ID=your_entity_id
X402_FACILITATOR_URL=https://your-facilitator-url

# Arc Network
ARC_RPC_URL=https://arc-testnet-rpc.io
ARC_CHAIN_ID=11155111
ARC_CONTRACT_ADDRESS=0x

# Agent Configuration
CONSUMER_WALLET_ADDRESS=0x
PROVIDER_WALLET_ADDRESS=0x

# Backend
LOG_LEVEL=INFO
API_PORT=8000
EOF

# Copy to actual .env and fill in values
cp .env.example .env
```

### Step 4: Initialize Core Files

```bash
# Create empty Python files to establish structure
touch smart_contracts/__init__.py
touch backend/__init__.py
touch backend/engines/__init__.py
touch backend/agents/__init__.py
touch scripts/__init__.py
touch tests/__init__.py
```

### Step 5: First Commit

```bash
git add .
git commit -m "Initial project structure"
```

---

## 📚 Next Steps

Now that you have the environment set up, follow these guides in order:

### Phase 1: Smart Contract (Days 1-2)
1. **SMART_CONTRACT_GUIDE.md** — Write & test Vyper contract
   - Implement payment logic
   - Add batch settlement
   - Deploy to Arc testnet

### Phase 2: Backend (Days 2-3)
2. **BACKEND_SETUP.md** — Create FastAPI server
   - Set up metering engine
   - Implement pricing engine
   - Build settlement orchestrator

3. **AGENT_IMPLEMENTATION.md** — Create autonomous agents
   - Consumer agent logic
   - Provider agent logic
   - Autonomous decision-making

### Phase 3: Integration & Testing (Day 3-4)
4. **INTEGRATION_GUIDE.md** — Wire everything together
   - Connect agents to smart contract
   - Implement x402 payment flow
   - Circle Wallet integration

5. **TESTING_GUIDE.md** — Validate all components
   - Unit tests for pricing/metering
   - Integration tests
   - End-to-end testing

### Phase 4: Deployment & Demo (Days 4-5)
6. **DEPLOYMENT_GUIDE.md** — Deploy to Arc testnet
   - Smart contract deployment
   - Backend configuration
   - Agent wallet setup

7. **DEMO_EXECUTION.md** — Run the full demo
   - Generate 50+ transactions
   - Verify on Arc explorer
   - Measure performance

8. **VIDEO_SUBMISSION.md** — Record & submit
   - Demo video recording
   - Screenshots & documentation
   - Feedback submission

---

## 🎯 Key Milestones

### Milestone 1: Smart Contract Live (Day 2)
- [ ] Vyper contract compiles
- [ ] Contract deployed to Arc testnet
- [ ] `pay_for_compute()` function tested
- [ ] Contract address saved in .env

### Milestone 2: Backend Server Running (Day 3)
- [ ] FastAPI server starts on port 8000
- [ ] `/health` endpoint returns 200
- [ ] `/api/compute` endpoint accepts requests
- [ ] Metering engine tracks usage

### Milestone 3: Agents Operational (Day 3)
- [ ] Consumer agent makes requests
- [ ] Provider agent executes tasks
- [ ] Settlement engine calls contract
- [ ] Wallets update in real-time

### Milestone 4: Demo Generates 50+ Transactions (Day 4)
- [ ] `python demo.py` runs without errors
- [ ] 50+ Arc transactions generated
- [ ] Each transaction ≤ $0.01
- [ ] All transactions verified on Arc explorer

### Milestone 5: Submission Ready (Day 5)
- [ ] Demo video recorded
- [ ] Feedback written
- [ ] GitHub repo public
- [ ] All files committed

---

## 🔧 Development Workflow

### Daily Workflow

**Morning:** Review yesterday's progress, plan today's tasks
```bash
# Pull latest changes
git pull

# Activate environment
source venv/bin/activate

# Start development
# Follow guide for today's phase
```

**Throughout the day:** Make progress, commit frequently
```bash
# After each logical unit of work
git add .
git commit -m "Descriptive commit message"

# Push to GitHub
git push origin main
```

**End of day:** Document progress, plan next day
```bash
# Run tests to verify nothing broke
pytest tests/

# Update progress in README or PROGRESS.md
echo "Today: Completed smart contract deployment" >> PROGRESS.md

# Final commit
git add .
git commit -m "End of day: [summary]"
git push origin main
```

### Testing During Development

```bash
# Test individual component
pytest tests/test_pricing.py -v

# Test with coverage
pytest tests/ --cov=backend

# Test specific function
pytest tests/test_settlement.py::test_atomic_payment -v

# Run async tests
pytest tests/test_backend.py -v --asyncio-mode=auto
```

### Debugging

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
python scripts/demo.py --verbose

# Inspect Arc transactions
# Visit: https://testnet.arc.io/address/[CONTRACT_ADDRESS]

# Check wallet balances
python scripts/check_balances.py
```

---

## 📖 Documentation Layout

Each guide follows this structure:

1. **Overview** — What you'll accomplish
2. **Prerequisites** — What you need before starting
3. **Step-by-step instructions** — Numbered, detailed steps
4. **Code examples** — Copy-paste ready code
5. **Verification** — How to confirm it worked
6. **Troubleshooting** — Common issues & solutions
7. **Next steps** — What to do next

---

## 💡 Tips for Success

### 1. Commit Often
Don't wait until the end of the day. Commit after each feature:
```bash
git add .
git commit -m "Feat: Implement metering engine"
```

### 2. Use Branches for Experimentation
```bash
git checkout -b feature/payment-batching
# ... experiment ...
git checkout main
git merge feature/payment-batching
```

### 3. Keep Environment Variables Secure
- Never commit `.env` file
- Always use `.env.example` as template
- Rotate API keys if compromised

### 4. Test on Testnet First
- Deploy contract to Arc testnet first
- Use testnet USDC for demo
- Only submit when fully working

### 5. Document as You Go
- Add docstrings to code
- Update README.md with progress
- Keep PROGRESS.md for daily notes

---

## 🚨 Common Issues & Solutions

### Python Version Mismatch
```bash
# Check Python version
python --version

# Should be 3.10+. If not:
# - macOS: brew install python@3.10
# - Ubuntu: sudo apt-get install python3.10
# - Windows: Download from python.org
```

### Virtual Environment Issues
```bash
# If venv is broken, recreate it
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Vyper Compilation Fails
```bash
# Make sure Vyper is installed
pip install vyper==0.3.10

# Verify installation
vyper --version

# Try compiling again
vyper smart_contracts/compute_marketplace.vy -o bytecode
```

### Arc RPC Timeouts
```bash
# Check if testnet is up
curl https://arc-testnet-rpc.io

# If timeout, wait a moment and retry
# If persistent, try alternative RPC endpoint
```

### Port 8000 Already in Use
```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process or use different port
python backend/main.py --port 8001
```

---

## 📞 Getting Help

### Within This Guide
- Each markdown file has a "Troubleshooting" section
- Search for your error message in the docs
- Check the FAQ at the end of each guide

### External Resources
- **Arc Docs:** https://docs.arc.io
- **Circle Docs:** https://developers.circle.com
- **Vyper Docs:** https://docs.vyperlang.org
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **Stack Overflow:** Tag with `[arc]` `[vyper]` `[fastapi]`

### Debugging Tools
```bash
# Arc explorer (verify transactions)
https://testnet.arc.io

# Circle Dashboard (check API keys)
https://dashboard.circle.com

# Testnet Faucet (request USDC)
https://testnet.circle.com/faucet

# VS Code Extensions
# - Vyper (VSCode Vyper extension)
# - Python (Microsoft Python extension)
# - REST Client (for testing APIs)
```

---

## ✅ Checklist Before Moving to Next Guide

- [ ] Python 3.10+ installed
- [ ] Virtual environment activated
- [ ] All dependencies installed
- [ ] Project structure created
- [ ] `.env` file configured
- [ ] Git repo initialized
- [ ] First commit made
- [ ] Circle account created
- [ ] Arc testnet account funded

**Once all items are checked, you're ready for SMART_CONTRACT_GUIDE.md! 🚀**

---

## 📊 Timeline

| Phase | Days | Deliverable | Status |
|-------|------|-------------|--------|
| Smart Contract | 1-2 | Deployed contract on Arc testnet | → Next: SMART_CONTRACT_GUIDE.md |
| Backend | 2-3 | FastAPI server with engines | Follow: BACKEND_SETUP.md |
| Agents | 3 | Consumer & Provider agents | Follow: AGENT_IMPLEMENTATION.md |
| Integration | 3-4 | All components connected | Follow: INTEGRATION_GUIDE.md |
| Testing | 4 | Unit & integration tests | Follow: TESTING_GUIDE.md |
| Demo | 4 | 50+ transactions on Arc | Follow: DEMO_EXECUTION.md |
| Submission | 5 | Video + feedback + repo | Follow: VIDEO_SUBMISSION.md |

---

**Next step: Open SMART_CONTRACT_GUIDE.md and follow the Vyper contract walkthrough! 🔥**
