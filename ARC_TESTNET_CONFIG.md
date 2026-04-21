# Arc Testnet Configuration Guide
## Get All Required Values for Deployment

Before starting SMART_CONTRACT_GUIDE.md, you need these testnet configuration values. This guide walks you through obtaining each one.

---

## 📋 Required Values Checklist

You need these 3 critical values:

- [ ] `PRIVATE_KEY` — Testnet wallet private key
- [ ] `ARC_RPC_URL` — Arc testnet RPC endpoint  
- [ ] `USDC_ADDRESS` — USDC token address on Arc testnet

---

## 🔑 Step 1: Generate PRIVATE_KEY

### Option A: Generate a NEW testnet-only wallet (Recommended)

```bash
# Generate a new private key
python -c "from eth_account import Account; a=Account.create(); print(f'Address: {a.address}\nPrivate Key: {a.key.hex()}')"
```

Output will look like:
```
Address: 0x1234567890123456789012345678901234567890
Private Key: 0xabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcd
```

**Save both values!**

### Option B: Use existing Ethereum/EVM wallet

If you have a wallet you already use:

**MetaMask:**
1. Open MetaMask
2. Click account icon → "Account details"
3. Click "Export Private Key"
4. Enter password
5. Copy the private key (starts with 0x)

**Important:** This is a TESTNET key only. Never use mainnet keys for testing.

---

## 🌐 Step 2: Find ARC_RPC_URL

The RPC URL is the endpoint to connect to Arc testnet.

### Current Arc Testnet RPC Endpoints:

Check the official Arc documentation:

```bash
# Primary testnet RPC (as of April 2026)
https://arc-testnet-rpc.io

# Alternative (if primary is down)
https://rpc.arc-testnet.io
```

**To verify the RPC works:**

```bash
curl -X POST https://arc-testnet-rpc.io \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}'

# Should return: {"jsonrpc":"2.0","result":"0x2b6bee1","id":1}
```

If successful, you have the right RPC URL!

**Save it in .env:**
```bash
ARC_RPC_URL=https://arc-testnet-rpc.io
```

---

## 💰 Step 3: Find USDC_ADDRESS

USDC address on Arc testnet. This is the token contract we'll use.

### Check Arc Documentation:

Visit: https://docs.arc.io → Search "USDC testnet address"

Or check Circle's documentation:
https://developers.circle.com → Documentation → USDC on testnet networks

### Common USDC Addresses on Arc Testnet:

```bash
# Arc testnet USDC (verify in official docs)
0x... (check Arc/Circle docs for current address)
```

**To verify USDC address:**

```bash
# Once you have the address, verify it's ERC20
curl -X POST https://arc-testnet-rpc.io \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0",
    "method":"eth_call",
    "params":[{
      "to":"0xUSDADDRESS",
      "data":"0x313ce567"
    },"latest"],
    "id":1
  }'
```

**Save it in .env:**
```bash
USDC_ADDRESS=0x...
```

---

## 🔗 Step 4: Verify ARC_CHAIN_ID

Arc testnet chain ID identifies the network.

### Arc Testnet Chain ID:

```bash
# Arc testnet chain ID
11155111
```

Verify by calling:

```bash
curl -X POST https://arc-testnet-rpc.io \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}'

# Should return: 0x2b6bee1 (which is 11155111 in hex)
```

**Save it in .env:**
```bash
ARC_CHAIN_ID=11155111
```

---

## 💾 Step 5: Set Up .env File

Create `.env` in project root with all values:

```bash
# Arc Network Configuration
ARC_RPC_URL=https://arc-testnet-rpc.io
ARC_CHAIN_ID=11155111
USDC_ADDRESS=0x...   # Get from Arc/Circle docs
PRIVATE_KEY=0x...    # Your testnet wallet private key

# Circle API (optional, can add later)
CIRCLE_API_KEY=
CIRCLE_ENTITY_ID=

# Backend Configuration
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

---

## 💵 Step 6: Fund Your Testnet Wallet

You need testnet USDC to deploy and test.

### Get Testnet USDC:

1. **Visit Circle Testnet Faucet:**
   https://testnet.circle.com/faucet

2. **Enter your wallet address:**
   ```
   0x1234567890123456789012345678901234567890
   ```

3. **Request testnet USDC:**
   - Usually 100 USDC for testing
   - Click "Request"
   - Wait 1-2 minutes for confirmation

4. **Verify receipt:**
   ```bash
   # Check balance via RPC
   curl -X POST https://arc-testnet-rpc.io \
     -H "Content-Type: application/json" \
     -d '{
       "jsonrpc":"2.0",
       "method":"eth_call",
       "params":[{
         "to":"0xUSDCADDRESS",
         "data":"0x70a08231000000000000000000000000YOURADDRESS"
       },"latest"],
       "id":1
     }'
   ```

---

## 📊 Step 7: Complete Configuration Template

Here's your complete `.env.example` to use as template:

```bash
# ============================================
# Arc Testnet Configuration
# ============================================

# Arc RPC Endpoint (where you send transactions)
ARC_RPC_URL=https://arc-testnet-rpc.io

# Arc Chain ID (identifies the testnet)
ARC_CHAIN_ID=11155111

# USDC Token Address on Arc
# Get from Arc/Circle documentation
USDC_ADDRESS=0x...

# Your testnet wallet private key
# Generated with: python -c "from eth_account import Account; a=Account.create(); print(a.key.hex())"
# NEVER use mainnet keys here!
PRIVATE_KEY=0x...

# ============================================
# Circle API (Optional, add later)
# ============================================

CIRCLE_API_KEY=sk_test_...
CIRCLE_ENTITY_ID=...
X402_FACILITATOR_URL=https://...

# ============================================
# Backend Configuration
# ============================================

API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# ============================================
# Contract Configuration (after deployment)
# ============================================

ARC_CONTRACT_ADDRESS=0x...  # Will fill in after deployment
ARC_EXPLORER_URL=https://testnet.arc.io
```

---

## ✅ Verification Checklist

Before proceeding to SMART_CONTRACT_GUIDE.md:

- [ ] **PRIVATE_KEY** generated or obtained
- [ ] **ARC_RPC_URL** verified (curl test passed)
- [ ] **USDC_ADDRESS** obtained from official docs
- [ ] **ARC_CHAIN_ID** confirmed (11155111)
- [ ] Wallet funded with testnet USDC (from faucet)
- [ ] `.env` file created with all values
- [ ] `.env` file added to `.gitignore` (don't commit!)

---

## 🔍 Troubleshooting

### "Connection refused" when testing RPC

```bash
# The testnet might be down
# Try alternative endpoint:
ARC_RPC_URL=https://rpc.arc-testnet.io

# Or check Arc status page:
https://status.arc.io
```

### "Invalid USDC_ADDRESS"

- Verify in Arc/Circle official documentation
- Make sure it starts with `0x`
- Make sure it's 42 characters long (0x + 40 hex digits)

### "Private key is invalid"

```bash
# Make sure it's in hex format starting with 0x
# Regenerate if needed:
python -c "from eth_account import Account; a=Account.create(); print(a.key.hex())"
```

### "Testnet USDC not received"

- Check you sent to the right address
- Wait 2-3 minutes for confirmation
- Check balance using explorer: https://testnet.arc.io

---

## 📚 Resources

### Official Documentation:

- **Arc Docs:** https://docs.arc.io
- **Arc Testnet:** https://testnet.arc.io
- **Circle Docs:** https://developers.circle.com
- **Circle Testnet Faucet:** https://testnet.circle.com/faucet

### Tools:

- **Arc Explorer:** https://testnet.arc.io (view transactions)
- **Wallet Inspector:** View your balance and history
- **RPC Tester:** https://chainlist.org (verify network)

---

## 🚀 Next Step

Once you've completed this checklist and have all values in `.env`:

**Proceed to: GETTING_STARTED.md**

Then follow: SMART_CONTRACT_GUIDE.md

---

## 💡 Pro Tips

1. **Never share your PRIVATE_KEY** — Not even in code comments
2. **Always use testnet keys for testing** — Keep mainnet keys secure elsewhere
3. **Save your configuration values** — You'll need them throughout the build
4. **Back up your .env file** — But don't commit it to git
5. **Verify RPC before deploying** — Test with curl first

---

## ⚠️ Security Reminders

- ✅ Do use testnet wallet for testing
- ✅ Do keep PRIVATE_KEY in .env (not in code)
- ✅ Do add .env to .gitignore
- ❌ Don't commit .env to git
- ❌ Don't share PRIVATE_KEY with anyone
- ❌ Don't use mainnet keys for testnet
- ❌ Don't push .env to GitHub

---

**Ready?** Once .env is configured, go to GETTING_STARTED.md! 🚀
