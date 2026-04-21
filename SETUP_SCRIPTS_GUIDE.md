# 🔧 Complete Setup Package - Script Guide
## Quick Reference for Setup, Verification, and Validation

All scripts work together to help you configure Arc testnet correctly.

---

## 📦 What You Have

### 4 Scripts for Configuration Management:

1. **`.env.example`** — Configuration template
2. **`setup_env.sh`** — Interactive setup script (gathers values)
3. **`verify_env.sh`** — Verification script (tests with curl)
4. **`validate_config.py`** — Validation script (checks syntax)

---

## 🚀 Quick Start (3 Steps)

### Step 1: Interactive Setup (10 min)
```bash
bash setup_env.sh
```

This script will:
- Walk you through getting each Arc value
- Generate or input PRIVATE_KEY
- Create `.env` file with all values
- Fund your testnet wallet

### Step 2: Verify Configuration (5 min)
```bash
bash verify_env.sh
```

This script will:
- Test RPC connection with curl
- Validate private key format
- Check wallet balance
- Test USDC contract address

### Step 3: Final Validation (2 min)
```bash
python3 validate_config.py
```

This script will:
- Check all required values are present
- Validate value formats
- Security checks (.gitignore, etc.)
- Show final status

---

## 📋 Detailed Usage Guide

### 1. `.env.example` - Template File

**What it is:** Template with all configuration options explained

**How to use:**
```bash
# Copy template to working file
cp .env.example .env

# Manually fill in values
nano .env
```

**Contains:**
- All required variables (marked REQUIRED)
- All optional variables (marked OPTIONAL)
- Comments explaining each value
- Verification status flags
- Security reminders

**When to use:** If you prefer manual setup instead of interactive script

---

### 2. `setup_env.sh` - Interactive Setup

**What it is:** Guided script that walks you through configuration

**How to use:**
```bash
bash setup_env.sh
```

**What it does:**
- Step 1: Get ARC_RPC_URL (with verification)
- Step 2: Get ARC_CHAIN_ID
- Step 3: Get USDC_ADDRESS
- Step 4: Generate or input PRIVATE_KEY
- Step 5: Fund wallet instructions
- Step 6: Verification summary

**Example output:**
```
╔═══════════════════════════════════════════════════════════════╗
║     Arc Testnet Configuration Setup Script                   ║
║     Agent-to-Agent Compute Marketplace                       ║
╚═══════════════════════════════════════════════════════════════╝

STEP 1: Arc Testnet RPC URL
...
```

**Features:**
- Interactive prompts for each value
- Automatic wallet generation (Python)
- RPC testing during setup
- Creates `.env` file automatically

---

### 3. `verify_env.sh` - Verification Script

**What it is:** Tests all configuration with real Arc testnet calls

**How to use:**
```bash
bash verify_env.sh
```

**What it does:**
- Loads `.env` file
- Tests RPC connection (eth_chainId)
- Tests block number (eth_blockNumber)
- Validates private key format
- Checks wallet balance
- Tests USDC contract

**Example output:**
```
Testing RPC connection... ✓
Current block: 0x1a2b3c
Validating private key... ✓
Wallet address: 0x1234...
Checking wallet balance... ✓
Wallet has balance: ~0.5 ETH
```

**Uses curl commands:**
- `eth_chainId` — Verify chain
- `eth_blockNumber` — Check block sync
- `eth_getBalance` — Get wallet balance
- `eth_call` — Test USDC contract

---

### 4. `validate_config.py` - Python Validator

**What it is:** Comprehensive configuration checker

**How to use:**
```bash
python3 validate_config.py
```

**What it does:**
- Loads `.env` file
- Validates all required variables
- Validates optional variables
- Checks value formats with regex
- Validates patterns:
  - URLs: `^https?://`
  - Chain ID: `^\d+$`
  - Address: `^0x[0-9a-fA-F]{40}$`
  - Private Key: `^0x[0-9a-fA-F]{64}$`
- Security checks (.gitignore, file permissions)
- Shows summary with status

**Example output:**
```
Required Configuration
✓ ARC_RPC_URL: https://arc-testnet-rpc.io
✓ ARC_CHAIN_ID: 11155111
✓ USDC_ADDRESS: 0x1234...
✓ PRIVATE_KEY: 0xabcd...

Required: 4/4
Optional: 3/5

✓ Configuration is valid and complete!
```

**Masks sensitive data:**
- Shows only first/last 8 chars of keys and addresses
- Safe to run publicly

---

## 🔄 Complete Workflow

Here's the recommended order:

```bash
# 1. Copy template (optional - setup script does this)
cp .env.example .env

# 2. Run interactive setup (RECOMMENDED)
bash setup_env.sh

# 3. Verify configuration with curl tests
bash verify_env.sh

# 4. Validate configuration format
python3 validate_config.py

# 5. Check what was created
cat .env | grep -v '^#' | grep -v '^$'

# 6. Ready to build!
# Follow: GETTING_STARTED.md
```

---

## ✅ Verification Checklist

Use this to track progress:

```bash
# Step 1: Run setup
☐ bash setup_env.sh
  ☐ ARC_RPC_URL entered
  ☐ ARC_CHAIN_ID confirmed
  ☐ USDC_ADDRESS obtained
  ☐ PRIVATE_KEY generated
  ☐ Wallet address noted
  ☐ Wallet funded from faucet

# Step 2: Verify configuration
☐ bash verify_env.sh
  ☐ RPC connection successful
  ☐ Block number retrieved
  ☐ Private key validated
  ☐ Wallet has balance

# Step 3: Validate format
☐ python3 validate_config.py
  ☐ All required vars present
  ☐ All formats correct
  ☐ Security checks pass

# Step 4: Ready to build
☐ .env created with all values
☐ .env added to .gitignore
☐ .env not committed to git
☐ Wallet funded with testnet USDC
```

---

## 🛠️ Troubleshooting

### "setup_env.sh: command not found"
```bash
# Make script executable
chmod +x setup_env.sh
bash setup_env.sh
```

### "RPC connection failed"
```bash
# Check RPC URL in .env
grep ARC_RPC_URL .env

# Test manually
curl -X POST https://arc-testnet-rpc.io \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}'

# Should return: {"jsonrpc":"2.0","result":"0x...","id":1}
```

### "Python: No module named 'eth_account'"
```bash
# Install missing dependencies
pip install eth-account web3

# Try validation again
python3 validate_config.py
```

### ".env file not found"
```bash
# Create from template
cp .env.example .env

# Or run setup
bash setup_env.sh
```

### "Private key format invalid"
```bash
# Generate new key
python3 -c "from eth_account import Account; a=Account.create(); print(f'0x{a.key.hex()}')"

# Or regenerate in setup
bash setup_env.sh
```

### "USDC_ADDRESS not found in Arc docs"
```bash
# Check these sources:
# 1. https://docs.arc.io
# 2. https://developers.circle.com
# 3. Arc Discord #testnet-support

# Update .env manually
nano .env
# Change USDC_ADDRESS=0x...
```

---

## 🔐 Security Best Practices

### ✅ DO:
```bash
# Add .env to .gitignore
echo ".env" >> .gitignore

# Use testnet-only wallet
# Never use mainnet keys

# Keep .env secure
chmod 600 .env

# Verify .env is ignored
git status
```

### ❌ DON'T:
```bash
# Don't commit .env to git
git add .env  # Wrong!

# Don't share .env file
# Don't hardcode values in code
# Don't use mainnet keys for testnet
# Don't log PRIVATE_KEY output

# Check if .env is in git history
git log --all -- .env
```

---

## 📊 Configuration Validation Flow

```
┌─────────────────┐
│  setup_env.sh   │  Interactive setup
│  (10 minutes)   │  ↓ Creates .env
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ verify_env.sh   │  Tests with curl
│  (5 minutes)    │  ↓ Tests RPC, wallet, contract
└────────┬────────┘
         │
         ↓
┌──────────────────────┐
│ validate_config.py   │  Validates format
│  (2 minutes)         │  ↓ Checks all values
└────────┬─────────────┘
         │
         ↓
    ✓ READY
    Configuration complete!
```

---

## 🎯 Next Steps After Setup

Once all scripts pass:

1. **Verify .env contents:**
   ```bash
   cat .env | grep -v '^#' | grep -v '^$'
   ```

2. **Keep .env safe:**
   ```bash
   # Make sure it's in .gitignore
   cat .gitignore | grep .env
   
   # Verify it's not in git
   git status
   ```

3. **Start building:**
   ```bash
   # Follow the main build guide
   # Next: GETTING_STARTED.md
   ```

---

## 📋 File Reference

| File | Purpose | When to Use | Time |
|------|---------|------------|------|
| `.env.example` | Template | Manual setup | 5 min |
| `setup_env.sh` | Interactive setup | Recommended | 10 min |
| `verify_env.sh` | Verify with curl | After setup | 5 min |
| `validate_config.py` | Validate format | Final check | 2 min |

---

## ✨ Summary

**Complete Setup Process:**
1. Run `bash setup_env.sh` — Interactive guided setup
2. Run `bash verify_env.sh` — Test with Arc testnet
3. Run `python3 validate_config.py` — Final validation
4. Check `cat .env` — Verify all values
5. Start building! — Follow GETTING_STARTED.md

**Total Time:** ~20 minutes

**Result:** Complete, verified Arc testnet configuration ready for deployment

---

**Ready? Start with:**
```bash
bash setup_env.sh
```
