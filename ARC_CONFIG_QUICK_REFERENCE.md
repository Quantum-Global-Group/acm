# 🔑 Arc Testnet Configuration Quick Reference
## Get All Required Values - Fast Checklist

**⚠️ CRITICAL:** Do this BEFORE you start building!

---

## 🎯 What You Need (3 Required + 2 Optional)

### Required (Cannot proceed without these)

```bash
PRIVATE_KEY=0x...          # Testnet wallet private key
ARC_RPC_URL=...            # Arc testnet RPC endpoint
USDC_ADDRESS=0x...         # USDC token on Arc testnet
```

### Optional (Highly Recommended)

```bash
ARC_CHAIN_ID=5042002       # Official Arc testnet chain ID (eth_chainId: 0x4cef52)
ARC_EXPLORER_URL=...       # Arc block explorer
```

---

## 🔧 Step-by-Step Getting Each Value

### 1️⃣ Generate PRIVATE_KEY (1 minute)

**Run this command:**
```bash
python -c "from eth_account import Account; a=Account.create(); print(f'Address: {a.address}\nPrivate Key: {a.key.hex()}')"
```

**Output will be:**
```
Address: 0x1234567890123456789012345678901234567890
Private Key: 0xabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcd
```

**Copy both values and save in secure location!**

### 2️⃣ Get ARC_RPC_URL (2 minutes)

**Primary Arc testnet RPC (official docs — “Connect to network”):**
```
https://rpc.testnet.arc.network
```

**WebSocket (official):** `wss://rpc.testnet.arc.network`

**Provider-backed alternatives** (same chain):  
`https://rpc.blockdaemon.testnet.arc.network` · `https://rpc.drpc.testnet.arc.network` · `https://rpc.quicknode.testnet.arc.network` · `https://arc-testnet.drpc.org` · `https://5042002.rpc.thirdweb.com`

**Verify it works:**
```bash
curl -X POST https://rpc.testnet.arc.network \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}'
```

**Should return:**
```json
{"jsonrpc":"2.0","result":"0x4cef52","id":1}
```

(`0x4cef52` = **5042002** — official Arc testnet chain ID.)

If you see that response → **RPC is working!** ✅

### 3️⃣ Get USDC_ADDRESS (5 minutes)

**Check Arc Documentation:**
- https://docs.arc.io → Search "USDC testnet"
- https://developers.circle.com → USDC addresses

**Or ask in Arc Discord:** #testnet-support

**Example format:**
```
0x... (40 hex characters after 0x)
```

**Verify it's valid:**
```bash
# Copy this and replace USDC_ADDRESS and YOUR_RPC_URL
curl -X POST YOUR_RPC_URL \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0",
    "method":"eth_call",
    "params":[{
      "to":"0xUSDCADDRESS",
      "data":"0x313ce567"
    },"latest"],
    "id":1
  }'
```

If you get a result → **Address is valid!** ✅

### 4️⃣ Get ARC_CHAIN_ID (1 minute)

**Official Arc testnet chain ID:**
```
5042002
```

**Verify with curl:**
```bash
curl -X POST https://rpc.testnet.arc.network \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}'
```

**Look for response:**
```
0x4cef52  (this is 5042002 in hex)
```

### 5️⃣ Get ARC_EXPLORER_URL (1 minute)

**Standard Arc testnet explorer:**
```
https://testnet.arc.io
```

**Verify it's up:**
- Visit https://testnet.arc.io in your browser
- You should see a blockchain explorer interface

---

## 📝 Create Your .env File

Once you have all values, create `.env` in your project root:

```bash
# Arc Network Configuration
ARC_RPC_URL=https://rpc.testnet.arc.network
ARC_CHAIN_ID=5042002
USDC_ADDRESS=0x...   # From Arc docs
PRIVATE_KEY=0x...    # From generation above
ARC_EXPLORER_URL=https://testnet.arc.io

# Optional (can fill later)
CIRCLE_API_KEY=
CIRCLE_ENTITY_ID=
X402_FACILITATOR_URL=

# Backend Configuration  
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

**IMPORTANT: Add to .gitignore!**
```bash
echo ".env" >> .gitignore
```

---

## 💰 Fund Your Testnet Wallet

Before building, fund your wallet with testnet USDC:

1. **Get your wallet address** (from PRIVATE_KEY generation)
2. **Use Circle’s faucets** — see [How-to: Fund a Testnet Wallet](https://developers.circle.com/wallets/fund-a-testnet-wallet) (Public Faucet at [faucet.circle.com](https://faucet.circle.com) or Developer Console Faucet)
3. **Enter your wallet address** (or wallet ID for console faucet)
4. **Request testnet USDC** for the Arc testnet network your wallet uses
5. **Wait for confirmation** per faucet instructions
6. **Verify in explorer:** https://testnet.arc.io/address/YOUR_ADDRESS

---

## ✅ Verification Checklist

Complete this before starting GETTING_STARTED.md:

### Values Obtained
- [ ] PRIVATE_KEY generated (starts with 0x)
- [ ] ARC_RPC_URL verified (curl test passed)
- [ ] USDC_ADDRESS confirmed from docs
- [ ] ARC_CHAIN_ID confirmed (5042002)
- [ ] ARC_EXPLORER_URL noted (https://testnet.arc.io)

### Wallet Ready
- [ ] Wallet address from PRIVATE_KEY
- [ ] Testnet USDC requested from faucet
- [ ] Wait 1-2 minutes for confirmation
- [ ] Balance visible in explorer

### Configuration File
- [ ] .env file created with all values
- [ ] .env added to .gitignore
- [ ] No .env file committed to git

---

## 🚨 Critical Security Rules

✅ **DO:**
- Use testnet-only wallet for testing
- Keep PRIVATE_KEY in .env file (not in code)
- Add .env to .gitignore
- Use unique testnet wallet for each project
- Save backup of configuration

❌ **DON'T:**
- Share PRIVATE_KEY with anyone
- Commit .env to git
- Use mainnet keys for testnet
- Hardcode values in Python files
- Use same wallet across projects

---

## 🔍 Troubleshooting

### RPC Not Responding
```bash
# Try alternative Arc RPC endpoint
ARC_RPC_URL=https://rpc.arc-testnet.io

# Or check Arc status page
https://status.arc.io
```

### Can't Find USDC Address
- Check Arc official documentation (not random sources)
- Try Circle documentation: https://developers.circle.com
- Ask in Arc Discord #testnet-support

### Testnet USDC Not Received
- Verify you sent to correct address
- Wait additional 2-3 minutes
- Check address in Arc explorer: https://testnet.arc.io
- Try faucet again if first failed

### Invalid Private Key
```bash
# Regenerate if corrupted
python -c "from eth_account import Account; a=Account.create(); print(a.key.hex())"
```

---

## 📋 Copy-Paste Your Values

Once obtained, fill this in and save:

```
PRIVATE_KEY=_________________________________

ARC_RPC_URL=_________________________________

USDC_ADDRESS=_________________________________

ARC_CHAIN_ID=_________________________________

ARC_EXPLORER_URL=_________________________________

WALLET_ADDRESS=_________________________________

TESTNET_USDC_BALANCE=_________________________________
```

---

## 🎯 Next Steps After Completing This

1. ✅ All 5 values in .env
2. ✅ Wallet funded with testnet USDC
3. ✅ Verified values work (curl tests passed)
4. ✅ .env file ignored by git

Then proceed to: **GETTING_STARTED.md**

---

## ⏱️ Time Estimate

- Getting values: **10 minutes**
- Funding wallet: **5 minutes** (waiting)
- Verifying: **5 minutes**
- **Total: ~20 minutes**

**This is the most critical 20 minutes of the entire build!**

---

## 📞 Quick Help

**Values not found?**
- Check ARC_TESTNET_CONFIG.md (full guide)
- Visit Arc Discord for community help

**RPC not responding?**
- Try alternative endpoint
- Check Arc status page
- Wait and retry

**Wallet not funded?**
- Wait additional time from faucet
- Try faucet again
- Check correct wallet address

---

**✅ Once complete, you're ready to build! Start with GETTING_STARTED.md**

---

Generated: April 19, 2026  
Status: **CRITICAL SETUP GUIDE**  
Use before: All other guides
