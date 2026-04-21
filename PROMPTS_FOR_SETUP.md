# 🤖 Prompts for Arc Testnet Setup

## Ready-to-use prompts for automating Arc configuration

Use these prompts with Claude, Cowork, or any automation system to set up Arc testnet using the markdown task files.

---

## 📋 PROMPT 1: Cowork Quick Setup (Fastest)

**Use this to quickly configure Arc with Cowork**

```
I need to configure Arc testnet for the hackathon project immediately.

Reference task file: COWORK_TASK_ARC_SETUP.md
Quick reference: COWORK_QUICK_REFERENCE.md

Please execute:
python3 arc_auto_discover.py && python3 validate_config.py

Success indicators:
- .env file created
- All ARC_ variables populated
- Configuration validates without errors
- Ready to build

Expected output:
✓ RPC discovered and tested
✓ USDC address found
✓ Chain ID verified (11155111)
✓ Explorer URL set
✓ Configuration complete

After completion:
Show me the .env configuration (without sensitive keys)
Confirm all required values are set
```

---

## 📋 PROMPT 2: Complete Cowork Automation (With Private Key)

**Use this for full setup including wallet generation**

```
I need complete Arc testnet configuration with wallet setup.

Reference files:
- COWORK_TASK_ARC_SETUP.md (full specifications)
- COWORK_QUICK_REFERENCE.md (quick reference)

Please execute the complete setup:

1. Install dependencies
   pip install requests eth-account

2. Auto-discover Arc configuration
   python3 arc_auto_discover.py

3. Generate wallet private key
   python3 -c "from eth_account import Account; a=Account.create(); print(f'PRIVATE_KEY={a.key.hex()}')" >> .env

4. Validate configuration
   python3 validate_config.py

5. Test with curl verification
   bash verify_env.sh

Success criteria (all must pass):
- .env file created with all values
- ARC_RPC_URL is set and valid
- ARC_CHAIN_ID is 11155111
- USDC_ADDRESS is valid Ethereum address
- PRIVATE_KEY is generated
- validate_config.py shows ✓ for all
- RPC connection test passes
- Ready to build notification shown

After completion:
Display configuration summary
List next steps for building
Show wallet address for funding
```

---

## 📋 PROMPT 3: Option A Interactive Setup

**Use this to follow Option A (learning-focused)**

```
I want to learn and understand the Arc testnet configuration process step-by-step.

Reference file: SETUP_SCRIPTS_GUIDE.md
Setup script: setup_env.sh

Please execute interactive setup:

1. Read the setup instructions
   cat README_SETUP_FIRST.txt

2. Run interactive guided setup
   bash setup_env.sh

3. Follow all prompts for:
   - ARC_RPC_URL selection
   - ARC_CHAIN_ID confirmation  
   - USDC_ADDRESS entry
   - Private key generation/entry
   - Wallet funding instructions

4. After setup, verify:
   python3 validate_config.py

5. Test configuration:
   bash verify_env.sh

Expected workflow:
- Interactive prompts for each value
- Explanations of what each value is
- Automatic wallet generation option
- RPC testing during setup
- Clear success/failure messages

After completion:
Show configuration summary
Explain what each value does
List next steps for building
```

---

## 📋 PROMPT 4: Full Project Setup (End-to-End)

**Use this to set up everything from start to build**

```
I need to set up the complete Arc x Circle hackathon project from configuration to building.

Reference file: 00_FINAL_DELIVERY_SUMMARY.md
Additional: ARC_API_INTEGRATION_GUIDE.md

Please execute complete workflow:

PHASE 1: Arc Configuration (Option C - Fastest)
1. python3 arc_auto_discover.py
2. python3 validate_config.py
3. bash verify_env.sh

PHASE 2: Generate Wallet
4. python3 -c "from eth_account import Account; a=Account.create(); print(f'PRIVATE_KEY={a.key.hex()}')" >> .env

PHASE 3: Verify Setup
5. cat .env | grep ARC
6. echo "Configuration complete!"

PHASE 4: Setup Checklist
Verify:
- [ ] .env exists
- [ ] ARC_RPC_URL set
- [ ] ARC_CHAIN_ID=11155111
- [ ] USDC_ADDRESS populated
- [ ] PRIVATE_KEY generated
- [ ] All values validated
- [ ] Ready to build

PHASE 5: Next Steps Display
Show:
- Wallet address (for funding)
- Testnet faucet URL
- Next guide to follow (GETTING_STARTED.md)
- Build timeline

Success: Configuration complete and ready to deploy smart contract
```

---

## 📋 PROMPT 5: Cowork Task Automation

**Use this to create a Cowork automated task**

```
Create a Cowork task for Arc testnet configuration.

Reference: COWORK_TASK_ARC_SETUP.md

Task specifications:
Name: Configure Arc Testnet
Type: Terminal Automation
Duration: 15-40 seconds

Command to execute:
python3 arc_auto_discover.py && python3 validate_config.py

Expected output:
Step 1: Discovering RPC Endpoints ✓
Step 2: Verifying Chain ID ✓
Step 3: Discovering USDC Address ✓
Step 4: Setting Explorer URL ✓
Configuration saved to .env ✓

Success indicators to check:
- stdout contains "✓ Successfully"
- .env file exists
- No error messages
- Return code 0

On success:
Mark task complete
Display summary
Ready for next task: Fund wallet

On failure:
Retry with increased timeout
Log error details
Suggest manual troubleshooting

Post-task actions:
Show configuration summary
Display wallet address
Provide next steps link
```

---

## 📋 PROMPT 6: Debug & Troubleshooting

**Use this when something goes wrong**

```
Arc testnet configuration failed. Please diagnose and fix.

Reference files:
- COWORK_TASK_ARC_SETUP.md (troubleshooting section)
- COWORK_QUICK_REFERENCE.md (if something goes wrong)
- ARC_API_INTEGRATION_GUIDE.md

Troubleshooting workflow:

1. Check what failed
   Run: python3 validate_config.py
   Show all errors

2. Diagnose RPC issues
   Run: python3 discover_rpc_endpoints.py
   List working endpoints

3. Diagnose USDC issues
   Run: python3 discover_usdc_address.py
   Show available addresses

4. Retry configuration
   Run: python3 arc_auto_discover.py

5. Verify fix
   Run: python3 validate_config.py
   Show results

Possible issues to check:
- Internet connectivity
- RPC endpoint responsiveness
- Python dependency installation
- File permissions
- .env file corruption

For each issue:
1. Identify the problem
2. Suggest solution
3. Execute fix
4. Verify resolution
5. Document what was wrong
```

---

## 📋 PROMPT 7: Minimal Setup (For Experts)

**Use this if you just need it done fast**

```
Execute Arc testnet configuration now.

File: arc_auto_discover.py

Command:
python3 arc_auto_discover.py && python3 validate_config.py && bash verify_env.sh

Success: Configuration complete
Failure: Show error and retry suggestions

Next: Ready to fund wallet and build
```

---

## 📋 PROMPT 8: For Claude (Direct Use)

**Use this when asking Claude directly to help with setup**

```
I have markdown task files for Arc testnet configuration:
- COWORK_TASK_ARC_SETUP.md (complete specifications)
- COWORK_QUICK_REFERENCE.md (quick reference)
- ARC_API_INTEGRATION_GUIDE.md (integration details)

I need you to:

1. Read COWORK_QUICK_REFERENCE.md and identify the best option for me
2. Provide the exact command I should run
3. Explain what it does step-by-step
4. Tell me what to expect as output
5. Show me how to verify success

Context: I'm setting up for Arc x Circle hackathon, building Agent-to-Agent Compute Marketplace

My situation: [Choose one]
- I want the fastest setup (use Option C)
- I want to learn how it works (use Option A)
- I want complete control (use Option B)

Please help me choose and provide clear instructions.
```

---

## 🎯 PROMPT 9: For GitHub Actions or CI/CD

**Use this to integrate with continuous integration**

```
Create a CI/CD workflow for Arc testnet configuration.

Reference: COWORK_TASK_ARC_SETUP.md

Workflow name: Configure Arc Testnet
Trigger: On project setup / On push to main

Steps:

1. Checkout code
2. Setup Python 3.8+
3. Install dependencies: pip install requests
4. Run discovery:
   python3 arc_auto_discover.py
5. Validate:
   python3 validate_config.py
6. Test:
   bash verify_env.sh
7. Upload artifact:
   Save .env as artifact (masked)
8. Report success/failure

Success criteria:
- All steps complete without error
- .env file created
- Configuration validated

On failure:
- Show error logs
- Suggest manual setup
- Provide troubleshooting guide

Output:
- Configuration summary
- Ready for deployment
- Next steps document
```

---

## 📋 PROMPT 10: For Project Documentation

**Use this to document the setup process**

```
Create setup documentation for Arc testnet configuration.

Reference files to include:
- COWORK_TASK_ARC_SETUP.md
- COWORK_QUICK_REFERENCE.md  
- ARC_API_INTEGRATION_GUIDE.md
- 00_FINAL_DELIVERY_SUMMARY.md

Documentation should cover:

1. Overview
   - What is Arc testnet
   - What gets configured
   - Why it's important

2. Quick Start (3 versions)
   - Fastest (15-40 sec)
   - With verification (2 min)
   - Complete with wallet (3 min)

3. Detailed Steps
   - Prerequisites
   - Each step explained
   - Expected output
   - Troubleshooting

4. Success Verification
   - How to know it worked
   - Testing commands
   - Common issues

5. Next Steps
   - Fund wallet
   - Deploy smart contract
   - Run backend
   - Execute demo

6. Reference
   - All available scripts
   - Environment variables
   - File locations

Format: Professional README.md for project documentation
```

---

## 🚀 How to Use These Prompts

### **For Cowork:**
1. Open Cowork
2. Create new task
3. Copy PROMPT 1, 2, or 5
4. Paste into task description
5. Run task

### **For Claude:**
1. Copy relevant prompt
2. Paste into Claude chat
3. Let Claude execute or guide you
4. Follow provided instructions

### **For Automation:**
1. Copy prompt
2. Integrate with your workflow
3. Execute with automation tool
4. Monitor for success

### **For Documentation:**
1. Use PROMPT 10
2. Have Claude generate docs
3. Save as project README
4. Share with team

---

## ✅ Prompt Selection Guide

| Scenario | Use This Prompt |
|----------|-----------------|
| **Need it done NOW** | PROMPT 1 or 7 |
| **Want complete setup** | PROMPT 2 |
| **Learning Arc** | PROMPT 3 |
| **Full project setup** | PROMPT 4 |
| **Setting up Cowork task** | PROMPT 5 |
| **Something went wrong** | PROMPT 6 |
| **Expert quick setup** | PROMPT 7 |
| **Ask Claude for help** | PROMPT 8 |
| **CI/CD integration** | PROMPT 9 |
| **Create documentation** | PROMPT 10 |

---

## 💡 Tips for Using Prompts

### **Customize for Your Needs**
- Replace [choose one] with your situation
- Add specific details about your setup
- Modify success criteria as needed

### **Chain Multiple Prompts**
- Start with PROMPT 1 for quick setup
- Then use PROMPT 8 if you have questions
- Follow with PROMPT 6 if there are issues

### **Save Successful Prompts**
- Copy successful prompts to a file
- Reuse for future projects
- Share with team members

### **Add Your Context**
- Include your project details
- Specify your constraints
- Mention any custom requirements

---

## 🎯 Quick Copy-Paste

### **Just want the command?**

```bash
python3 arc_auto_discover.py && python3 validate_config.py
```

### **Want verification too?**

```bash
python3 arc_auto_discover.py && python3 validate_config.py && bash verify_env.sh
```

### **Need wallet generation?**

```bash
pip install requests eth-account && \
python3 arc_auto_discover.py && \
python3 -c "from eth_account import Account; a=Account.create(); print(f'PRIVATE_KEY={a.key.hex()}')" >> .env && \
python3 validate_config.py && \
bash verify_env.sh
```

---

## 📝 Summary

**10 Prompts Provided:**
1. Cowork Quick Setup
2. Complete Cowork Automation
3. Option A Interactive
4. Full Project Setup
5. Cowork Task Creation
6. Debug & Troubleshooting
7. Minimal Expert Setup
8. Claude Direct Help
9. CI/CD Integration
10. Documentation

**All prompts reference markdown files:**
- COWORK_TASK_ARC_SETUP.md
- COWORK_QUICK_REFERENCE.md
- ARC_API_INTEGRATION_GUIDE.md
- And others

**Use these prompts with:**
- Cowork (desktop automation)
- Claude (AI assistance)
- CI/CD systems
- Documentation generation
- Team communication

---

## 🚀 Next Steps

1. **Choose a prompt** above based on your scenario
2. **Copy the prompt** (full text)
3. **Paste into your tool** (Cowork, Claude, or automation system)
4. **Execute** and follow the results
5. **Reference the markdown files** if you need more details

---

**Ready to use?**

Pick a prompt, copy it, and execute!

All markdown task files are in `/mnt/user-data/outputs/`
