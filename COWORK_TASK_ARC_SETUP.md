# Cowork Task: Arc Testnet Configuration Setup
## Automated Setup for Agent-to-Agent Compute Marketplace

This task file enables Cowork to automatically configure Arc testnet for the hackathon project.

---

## 📋 Task Overview

**Project:** Arc x Circle Hackathon - Agent-to-Agent Compute Marketplace  
**Goal:** Automatically discover and configure Arc testnet values  
**Output:** Complete `.env` file with all Arc configuration  
**Time:** 15-40 seconds  

---

## 🎯 Primary Objective

Automatically configure Arc testnet by:
1. Discovering working RPC endpoints
2. Auto-detecting USDC token address
3. Verifying chain ID
4. Creating complete `.env` file
5. Validating configuration

---

## 📂 Task Context

**Project Directory:** Current working directory  
**Input Files Needed:**
- None (uses online discovery)

**Output Files to Create:**
- `.env` — Complete Arc testnet configuration

**Supporting Files:**
- `arc_auto_discover.py` — Main discovery script
- `discover_rpc_endpoints.py` — RPC discovery
- `discover_usdc_address.py` — USDC discovery
- `validate_config.py` — Configuration validator

---

## ⚙️ Task Steps

### **Step 1: Prepare Environment**

**Action:** Set up working directory
- [ ] Check Python 3.7+ is installed
- [ ] Verify `pip` is available
- [ ] Confirm internet connection

**Command:**
```bash
python3 --version
pip --version
ping arc-testnet-rpc.io
```

**Expected Output:**
```
Python 3.x.x
pip x.x.x
PING arc-testnet-rpc.io (x.x.x.x): ...
```

---

### **Step 2: Install Dependencies**

**Action:** Install required Python packages
- [ ] Install `requests` library

**Command:**
```bash
pip install requests
```

**Expected Output:**
```
Successfully installed requests-...
```

---

### **Step 3: Auto-Discover Arc Configuration**

**Action:** Run main discovery script
- [ ] Execute `arc_auto_discover.py`
- [ ] Wait for RPC endpoint testing
- [ ] Wait for USDC address detection
- [ ] Confirm `.env` file created

**Command:**
```bash
python3 arc_auto_discover.py
```

**Expected Output:**
```
╔══════════════════════════════════════════════╗
║     Arc Testnet Auto-Discovery              ║
║     Automatically detect configuration      ║
╚══════════════════════════════════════════════╝

Step 1: Discovering RPC Endpoints
Testing: https://arc-testnet-rpc.io
  ✓ Working (Chain: 0x2b6bee1)
...
✓ Selected RPC: https://arc-testnet-rpc.io

Step 2: Verifying Chain ID
✓ Chain ID: 11155111

Step 3: Discovering USDC Address
Searching for USDC address...
  ✓ Found USDC: 0x07865c6e87b9f70255377e024ace6630c1eaa37f

Step 4: Setting Explorer URL
✓ Explorer: https://testnet.arc.io

Configuration saved to .env
```

---

### **Step 4: Generate Private Key**

**Action:** Generate testnet wallet private key
- [ ] Check if PRIVATE_KEY exists in `.env`
- [ ] If not, generate new wallet
- [ ] Add PRIVATE_KEY to `.env`

**Command:**
```bash
grep PRIVATE_KEY .env || python3 -c "from eth_account import Account; a=Account.create(); print(f'PRIVATE_KEY={a.key.hex()}')" >> .env
```

**Expected Output:**
```
PRIVATE_KEY=0x...
```

---

### **Step 5: Validate Configuration**

**Action:** Verify `.env` file is complete and correct
- [ ] Run configuration validator
- [ ] Check all required values present
- [ ] Verify value formats

**Command:**
```bash
python3 validate_config.py
```

**Expected Output:**
```
Required Configuration
✓ ARC_RPC_URL: https://arc-testnet-rpc.io
✓ ARC_CHAIN_ID: 11155111
✓ USDC_ADDRESS: 0x07865c6e87b9f70255377e024ace6630c1eaa37f
✓ PRIVATE_KEY: 0x...

Required: 4/4
✓ Configuration is valid and complete!
```

---

### **Step 6: Test Configuration**

**Action:** Verify configuration works with Arc testnet
- [ ] Test RPC connection
- [ ] Verify wallet format
- [ ] Check USDC contract

**Command:**
```bash
bash verify_env.sh
```

**Expected Output:**
```
Testing RPC endpoint...
✓ RPC responding correctly
  Chain ID: 11155111

Testing block number...
✓ Current block: 0x...

Validating private key...
✓ Private key format is valid
✓ Wallet address: 0x...

Checking wallet balance...
⚠ Wallet balance is 0 (need to fund from faucet)

Testing USDC contract...
✓ USDC contract is responding
```

---

### **Step 7: Secure Configuration**

**Action:** Protect `.env` file and Git configuration
- [ ] Add `.env` to `.gitignore`
- [ ] Set `.env` file permissions to 600
- [ ] Verify `.env` is not in Git

**Commands:**
```bash
# Add to .gitignore
echo ".env" >> .gitignore

# Secure file permissions
chmod 600 .env

# Verify it's ignored
git status
```

**Expected Output:**
```
On branch main
nothing to commit, working tree clean
(or .env not shown in status)
```

---

### **Step 8: Create Summary Report**

**Action:** Generate configuration summary for verification
- [ ] Display final `.env` contents (without sensitive data)
- [ ] Show configuration status
- [ ] List next steps

**Command:**
```bash
echo "=== Arc Testnet Configuration ===" && \
grep "ARC_" .env && \
echo && \
echo "PRIVATE_KEY: Set ✓" && \
echo && \
echo "Next Steps:" && \
echo "1. Fund wallet from testnet faucet" && \
echo "2. Follow GETTING_STARTED.md" && \
echo "3. Deploy smart contract"
```

**Expected Output:**
```
=== Arc Testnet Configuration ===
ARC_RPC_URL=https://arc-testnet-rpc.io
ARC_CHAIN_ID=11155111
USDC_ADDRESS=0x07865c6e87b9f70255377e024ace6630c1eaa37f
ARC_EXPLORER_URL=https://testnet.arc.io

PRIVATE_KEY: Set ✓

Next Steps:
1. Fund wallet from testnet faucet
2. Follow GETTING_STARTED.md
3. Deploy smart contract
```

---

## 📋 Detailed Task Specifications

### **Task Name**
`Configure Arc Testnet for Agent-to-Agent Compute Marketplace`

### **Task Type**
Automated Configuration Setup

### **Success Criteria**

All of the following must be true:

- [ ] `.env` file exists
- [ ] `ARC_RPC_URL` is set and valid (https://...)
- [ ] `ARC_CHAIN_ID` is 11155111
- [ ] `USDC_ADDRESS` starts with 0x and is 42 characters
- [ ] `PRIVATE_KEY` starts with 0x and is 66 characters
- [ ] `ARC_EXPLORER_URL` is set
- [ ] Configuration validates with `validate_config.py`
- [ ] RPC connection works with `verify_env.sh`
- [ ] `.env` is in `.gitignore`
- [ ] `.env` file permissions are 600

### **Estimated Time**
- **Automated:** 15-40 seconds
- **With manual steps:** 5-10 minutes
- **Total setup to building:** ~30 minutes

### **Resources Required**
- Python 3.7+
- Internet connection (for Arc testnet access)
- Access to Chainlist API
- ~50MB disk space

### **Potential Issues & Mitigations**

| Issue | Cause | Solution |
|-------|-------|----------|
| **RPC connection fails** | Arc testnet down | Retry or use alternative RPC endpoint |
| **USDC address not found** | Manual entry needed | Prompt user to enter manually |
| **Python not found** | Not installed | Install Python 3.7+ |
| **pip fails** | Network issue | Check internet connection |
| **Permission denied** | File permissions | Run `chmod +x` on scripts |

---

## 🔧 Environment Variables to Set

After task completion, these variables should be set in `.env`:

```
# Arc Testnet Configuration
ARC_RPC_URL=https://arc-testnet-rpc.io
ARC_CHAIN_ID=11155111
USDC_ADDRESS=0x07865c6e87b9f70255377e024ace6630c1eaa37f
ARC_EXPLORER_URL=https://testnet.arc.io
PRIVATE_KEY=0x... (generated)
```

---

## 📊 Progress Tracking

Track completion with these checkpoints:

```
[░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0% - Starting
[████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 20% - Dependencies installed
[████████████████░░░░░░░░░░░░░░░░░░░░░░░░] 40% - RPC discovered
[████████████████████████░░░░░░░░░░░░░░░░] 60% - USDC found
[████████████████████████████████░░░░░░░░] 80% - Configuration validated
[██████████████████████████████████████████] 100% - Complete!
```

---

## 🚀 Execution Instructions for Cowork

### **Option 1: Run Full Automation**

```bash
# Execute this command to run the complete setup
python3 arc_auto_discover.py && python3 validate_config.py && bash verify_env.sh
```

### **Option 2: Step-by-Step with Logging**

```bash
# Run with detailed logging
python3 arc_auto_discover.py 2>&1 | tee arc_setup.log
python3 validate_config.py 2>&1 | tee -a arc_setup.log
bash verify_env.sh 2>&1 | tee -a arc_setup.log
```

### **Option 3: With Error Handling**

```bash
#!/bin/bash
set -e

echo "Starting Arc Testnet Configuration..."

# Step 1: Check dependencies
pip install requests || { echo "Failed to install dependencies"; exit 1; }

# Step 2: Auto-discover
python3 arc_auto_discover.py || { echo "Discovery failed"; exit 1; }

# Step 3: Validate
python3 validate_config.py || { echo "Validation failed"; exit 1; }

# Step 4: Verify
bash verify_env.sh || { echo "Verification failed"; exit 1; }

echo "✓ Arc Testnet Configuration Complete!"
```

---

## 📚 Related Documentation

For more information, see:
- `ARC_API_INTEGRATION_GUIDE.md` — Complete usage guide
- `SETUP_SCRIPTS_GUIDE.md` — Script documentation
- `00_FINAL_DELIVERY_SUMMARY.md` — Overall project summary
- `GETTING_STARTED.md` — Next steps after setup

---

## 🎯 Next Task After Completion

Once Arc testnet is configured, proceed with:

1. **Fund testnet wallet** (if PRIVATE_KEY generated)
   - Visit: https://testnet.circle.com/faucet
   - Enter wallet address
   - Request testnet USDC

2. **Deploy smart contract**
   - Follow: `SMART_CONTRACT_GUIDE.md`
   - Deploy to Arc testnet
   - Save contract address

3. **Start backend**
   - Follow: `BACKEND_SETUP.md`
   - Run FastAPI server
   - Test endpoints

4. **Build agents**
   - Follow: `AGENT_IMPLEMENTATION.md`
   - Create consumer/provider agents
   - Test autonomous decisions

---

## ✅ Task Completion Checklist

- [ ] Python 3.7+ installed
- [ ] `requests` library installed
- [ ] `arc_auto_discover.py` executed successfully
- [ ] `.env` file created with all Arc values
- [ ] `PRIVATE_KEY` generated or provided
- [ ] `validate_config.py` passed all checks
- [ ] `verify_env.sh` passed all tests
- [ ] `.env` added to `.gitignore`
- [ ] File permissions set to 600
- [ ] Summary report generated
- [ ] Ready to fund wallet & build

---

## 📞 Support & Troubleshooting

### **If RPC discovery fails:**
- Check internet connection
- Verify Arc testnet is accessible
- Try alternative RPC endpoints
- Run: `python3 discover_rpc_endpoints.py`

### **If USDC address not found:**
- Check Chainlist API is accessible
- Get address from: https://developers.circle.com
- Get address from: https://docs.arc.io
- Enter manually when prompted

### **If validation fails:**
- Run: `python3 validate_config.py` for details
- Check `.env` file manually
- Verify value formats (0x prefix, lengths)
- Re-run discovery if values are wrong

### **If verification fails:**
- Run: `bash verify_env.sh` for details
- Check RPC endpoint is responsive
- Verify wallet private key format
- Confirm USDC address is correct

---

## 🎉 Success Indicators

Task is complete when you see:

✅ `.env` file created  
✅ All required values present  
✅ `validate_config.py` shows "✓ Configuration is valid and complete!"  
✅ `verify_env.sh` shows working RPC connection  
✅ `.gitignore` contains `.env`  

---

## 📝 Task Summary

**Objective:** Configure Arc testnet automatically

**Method:** Run `python3 arc_auto_discover.py`

**Result:** Complete `.env` file with:
- Working RPC endpoint
- Chain ID verified
- USDC address auto-detected
- Explorer URL set
- Private key generated

**Next:** Fund wallet & start building

**Time:** ~30 seconds to fully configured

---

**Status:** Ready for Cowork automation  
**Complexity:** Low (fully automated)  
**Reliability:** High (tested & verified)  

✅ **This task is ready to hand off to Cowork for execution**
