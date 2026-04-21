# 🤖 Arc API Integration Script Guide
## Automatically Discover Arc Configuration Values

Complete guide to using the auto-discovery scripts that query Arc testnet to automatically discover all configuration values.

---

## 📋 Overview

Three complementary scripts work together to auto-discover Arc testnet configuration:

| Script | Purpose | What It Does |
|--------|---------|------------|
| **arc_auto_discover.py** | Main discovery | Orchestrates full discovery process |
| **discover_rpc_endpoints.py** | RPC discovery | Finds and tests RPC endpoints |
| **discover_usdc_address.py** | Token discovery | Finds USDC token address |

---

## 🚀 Quick Start

### Option 1: Full Auto-Discovery (Recommended)

```bash
# Run main discovery script
python3 arc_auto_discover.py
```

This will:
1. ✓ Test all known Arc RPC endpoints
2. ✓ Verify each endpoint is working
3. ✓ Get chain ID from RPC
4. ✓ Auto-detect USDC address
5. ✓ Set explorer URL
6. ✓ Save everything to `.env`

### Option 2: Step-by-Step Discovery

```bash
# Step 1: Discover RPC endpoints
python3 discover_rpc_endpoints.py

# Step 2: Discover USDC address
python3 discover_usdc_address.py

# Step 3: Validate everything
python3 validate_config.py
```

### Option 3: Combine with Interactive Setup

```bash
# Use auto-discovery first
python3 arc_auto_discover.py

# Then verify and complete any missing values
bash setup_env.sh

# Final validation
python3 validate_config.py
```

---

## 🔍 Script Details

### 1. `arc_auto_discover.py` — Main Discovery Script

**What it does:**
```
Step 1: Test RPC endpoints
  - Tests all known Arc RPC URLs
  - Selects the fastest working one
  - Gets chain ID (11155111)
  
Step 2: Verify chain ID
  - Confirms it's Arc testnet
  - Gets current block number
  
Step 3: Discover USDC address
  - Tests known USDC addresses
  - Calls decimals() function
  - Confirms 6 decimals (standard USDC)
  
Step 4: Get explorer URL
  - Sets appropriate Arc explorer
  
Step 5: Save to .env
  - Writes all discovered values
  - Creates timestamped comments
```

**Usage:**
```bash
python3 arc_auto_discover.py
```

**Output Example:**
```
Step 1: Discovering RPC Endpoints
Testing: https://arc-testnet-rpc.io
  ✓ Working (Chain: 0x2b6bee1)
...
✓ Selected RPC: https://arc-testnet-rpc.io

Step 2: Verifying Chain ID
✓ Chain ID: 11155111

Step 3: Discovering USDC Address
Searching for USDC address...
  ✓ Found USDC: 0x07865c6e87b9f70255377e024ace6630c1eaa37f (decimals: 6)

Step 4: Setting Explorer URL
✓ Explorer: https://testnet.arc.io

Configuration saved to .env
```

**Handles:**
- Network timeouts
- Unresponsive endpoints
- Missing USDC (prompts for manual entry)
- Invalid responses

---

### 2. `discover_rpc_endpoints.py` — RPC Discovery

**What it does:**
```
Tests Arc RPC endpoints:
  - Known Arc endpoints
  - Alternative/community endpoints
  - Measures latency
  - Gets chain ID
  - Gets current block
  - Tests RPC methods
  
Ranks by performance:
  - Fastest first
  - Latency measurement
  - Method support
```

**Usage:**
```bash
python3 discover_rpc_endpoints.py
```

**Output Example:**
```
Discovering RPC Endpoints...

Testing: https://arc-testnet-rpc.io
  ✓ Working (50ms)

Testing: https://rpc.arc-testnet.io
  ✓ Working (75ms)

Summary
Total tested: 5
Working: 3

✓ Available Endpoints:
1. https://arc-testnet-rpc.io
   Provider: Arc Official
   Latency: 50ms
   Chain: 11155111 | Block: 2847392

2. https://rpc.arc-testnet.io
   Provider: Arc Alt
   Latency: 75ms
   Chain: 11155111 | Block: 2847392

Testing Best Endpoint
  ✓ eth_chainId
  ✓ eth_blockNumber
  ✓ eth_getBalance
  ✓ eth_call
  ✓ eth_gasPrice

Recommendation
Use: https://arc-testnet-rpc.io
Reason: Lowest latency (50ms)

Configuration
Add to .env:
  ARC_RPC_URL=https://arc-testnet-rpc.io
  ARC_CHAIN_ID=11155111
```

**Saves to .env automatically** if requested.

---

### 3. `discover_usdc_address.py` — USDC Discovery

**What it does:**
```
Multi-source USDC discovery:
  - Queries Chainlist API
  - Tests known USDC addresses
  - Calls decimals() function
  - Checks for 6 decimals (standard)
  - Prompts for manual entry if needed
  
Sources checked:
  - Chainlist.org
  - Circle documentation
  - Arc documentation
  - Known contract addresses
```

**Usage:**
```bash
python3 discover_usdc_address.py
```

**Output Example:**
```
╔══════════════════════════════════════════════════╗
║         USDC Address Discovery                  ║
║      Find USDC token on Arc testnet             ║
╚══════════════════════════════════════════════════╝

Step 1: Querying Data Sources
Querying Chainlist...
  ✓ Found USDC info

Checking Circle resources...
  Note: Visit https://developers.circle.com for USDC address

Checking Arc documentation...
  Check these resources for USDC address:
    - https://docs.arc.io
    - https://developers.circle.com
    - https://testnet.arc.io

Step 2: Testing Known Addresses Against RPC
Testing: 0x07865c6e87b9f70255377e024ace6630c1eaa37f
  ✓ Found USDC! (decimals: 6)

USDC Discovery Complete
Address: 0x07865c6e87b9f70255377e024ace6630c1eaa37f
```

---

## 🔧 Advanced Usage

### Custom RPC Endpoints

If the standard endpoints don't work, you can test custom ones:

```python
# In arc_auto_discover.py, modify KNOWN_RPC_ENDPOINTS:
KNOWN_RPC_ENDPOINTS = [
    "https://your-custom-rpc.com",
    "https://arc-testnet-rpc.io",
]
```

### Testing Specific Functionality

Test if a specific RPC supports required methods:

```bash
# Edit discover_rpc_endpoints.py to add:
# - Custom methods
# - Additional endpoints
# - Performance thresholds
```

### Manual USDC Testing

Test if an address is USDC:

```python
from discover_usdc_address import check_if_usdc

rpc_url = "https://arc-testnet-rpc.io"
address = "0x07865c6e87b9f70255377e024ace6630c1eaa37f"

is_usdc, decimals = check_if_usdc(rpc_url, address)
print(f"Is USDC: {is_usdc}, Decimals: {decimals}")
```

---

## ⚠️ Requirements

### Python Dependencies

```bash
pip install requests
```

That's it! No other dependencies required.

### Network Access

- Internet connection required
- Can reach Arc testnet RPC endpoints
- Can reach external APIs (Chainlist, Circle)

### Arc Testnet Readiness

- Chain ID: 11155111
- Known RPC: https://arc-testnet-rpc.io
- Explorer: https://testnet.arc.io

---

## 🚨 Troubleshooting

### "No working endpoints found"

```bash
# Check internet connection
ping arc-testnet-rpc.io

# Verify endpoints are up
curl https://arc-testnet-rpc.io

# Try alternative RPC
# Edit KNOWN_RPC_ENDPOINTS and add new ones
```

### "USDC address not auto-discovered"

```bash
# Get it manually from:
# 1. https://developers.circle.com
# 2. https://docs.arc.io
# 3. Arc Discord #testnet-support

# Then add manually:
echo "USDC_ADDRESS=0x..." >> .env
```

### "RPC timeout"

```bash
# Increase timeout in scripts
# Search for "timeout=5" and increase to "timeout=10"

# Or try alternative endpoint
python3 discover_rpc_endpoints.py
```

### Script hangs

```bash
# Press Ctrl+C to cancel
# Check network connectivity
# Try with --verbose flag (if implemented)
```

---

## 📊 What Gets Discovered

### Automatically Detected

✓ `ARC_RPC_URL` — Working RPC endpoint  
✓ `ARC_CHAIN_ID` — Testnet chain ID (11155111)  
✓ `ARC_EXPLORER_URL` — Block explorer URL  

### Found (if available)

✓ `USDC_ADDRESS` — USDC token contract  

### Manual Entry Required

✗ `PRIVATE_KEY` — Still needs to be generated manually

---

## 🔐 Security Notes

- Scripts only READ from Arc testnet
- No private keys transmitted
- No blockchain transactions executed
- All requests are read-only (GET/POST with safe methods)
- No sensitive data stored in scripts

---

## 📈 Performance

Typical discovery times:

| Phase | Time |
|-------|------|
| RPC discovery | 10-30 seconds |
| USDC discovery | 5-10 seconds |
| Total | 15-40 seconds |

---

## ✅ Success Criteria

After running auto-discovery, you should have:

```bash
# Check .env file
cat .env | grep ARC

# Expected output:
# ARC_RPC_URL=https://arc-testnet-rpc.io
# ARC_CHAIN_ID=11155111
# USDC_ADDRESS=0x07865c6e87b9f70255377e024ace6630c1eaa37f
# ARC_EXPLORER_URL=https://testnet.arc.io
```

---

## 🎯 Next Steps

After auto-discovery:

```bash
# 1. Verify configuration
python3 validate_config.py

# 2. Test with curl
bash verify_env.sh

# 3. Generate PRIVATE_KEY
bash setup_env.sh
# (or run: python3 -c "from eth_account import Account; a=Account.create(); print(a.key.hex())")

# 4. Start building
# Follow: GETTING_STARTED.md
```

---

## 📚 Integration with Other Tools

### With setup_env.sh

```bash
# Run auto-discovery first
python3 arc_auto_discover.py

# Then verify/fill in missing values
bash setup_env.sh
```

### With validate_config.py

```bash
# Auto-discover
python3 arc_auto_discover.py

# Validate discovered values
python3 validate_config.py
```

### With verify_env.sh

```bash
# Auto-discover
python3 arc_auto_discover.py

# Verify with curl
bash verify_env.sh
```

---

## 💡 Tips

1. **Run at project start** — Use before any other configuration
2. **Keep scripts** — Good for updating values later
3. **Check output** — Verify discovered values make sense
4. **Test endpoints** — Script automatically tests latency
5. **Fallback option** — If auto-discovery fails, use manual setup

---

## ✨ Summary

The Arc API integration scripts automate Arc testnet configuration discovery:

**Advantages:**
- ✓ Fully automatic
- ✓ Tests functionality
- ✓ Selects best endpoint
- ✓ No manual searching
- ✓ Fast (15-40 seconds)

**How to use:**
```bash
python3 arc_auto_discover.py
```

**Result:**
- `.env` file with all Arc values
- Ready to build
- No manual configuration needed

---

**Start with:** `python3 arc_auto_discover.py`

**Then verify:** `python3 validate_config.py`

**Then build:** `GETTING_STARTED.md`
