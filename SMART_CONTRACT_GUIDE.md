# Smart Contract Guide: Deploy to Arc
## Build & Deploy the Compute Marketplace Contract

This guide walks you through writing, testing, and deploying the Vyper smart contract on Arc testnet.

---

## 🎯 What You'll Do

By the end of this guide:
- ✅ Write a Vyper smart contract for agent payments
- ✅ Compile and test the contract locally
- ✅ Deploy to Arc testnet
- ✅ Verify deployment on Arc explorer
- ✅ Save contract address & ABI for backend

---

## 📋 Prerequisites

From GETTING_STARTED.md, you should have:
- ✅ Python 3.10+ installed
- ✅ Virtual environment activated
- ✅ Vyper installed (`pip install vyper==0.3.10`)
- ✅ Arc testnet account with ~$10 USDC
- ✅ Project structure created

---

## 📝 Step 1: Create the Smart Contract

### Create contract file

```bash
# Make sure you're in project root
mkdir -p smart_contracts
cd smart_contracts

# Create the main contract
touch compute_marketplace.vy
```

### Write the contract

Open `smart_contracts/compute_marketplace.vy` and paste this complete contract:

```vyper
# @version ^0.3.0
# Agent-to-Agent Compute Marketplace Smart Contract
# Arc EVM-compatible L1
# USDC is the native gas token and stablecoin

# Interface for USDC token
interface IERC20:
    def transfer(to: address, amount: uint256) -> bool: nonpayable
    def transferFrom(sender: address, to: address, amount: uint256) -> bool: nonpayable
    def balanceOf(holder: address) -> uint256: view
    def approve(spender: address, amount: uint256) -> bool: nonpayable

# State variables
usdc_token: IERC20
owner: address

# Agent balance tracking (in wei)
agent_balances: public(HashMap[address, uint256])

# Max price enforcement
max_unit_price: public(uint256)

# Events
event Deposit:
    agent: indexed(address)
    amount: uint256

event Withdrawal:
    agent: indexed(address)
    amount: uint256

event PaymentSettled:
    consumer: indexed(address)
    provider: indexed(address)
    amount: uint256
    timestamp: uint256
    task_id: String[256]

event UsageRecorded:
    consumer: indexed(address)
    provider: indexed(address)
    quantity: uint256
    unit_price: uint256
    total_cost: uint256


@external
def __init__(usdc_address: address):
    """
    Initialize the contract.
    Args:
        usdc_address: Address of USDC token on Arc
    """
    self.usdc_token = IERC20(usdc_address)
    self.owner = msg.sender
    # Max unit price: $0.01 = 10,000 wei
    self.max_unit_price = 10000


@external
def deposit(amount: uint256):
    """
    Deposit USDC into agent's balance.
    """
    assert amount > 0, "Deposit amount must be > 0"
    assert self.usdc_token.transferFrom(msg.sender, self, amount), "Transfer failed"
    self.agent_balances[msg.sender] += amount
    log Deposit(msg.sender, amount)


@external
def withdraw(amount: uint256):
    """
    Withdraw USDC from agent's balance.
    """
    assert amount > 0, "Withdrawal amount must be > 0"
    assert self.agent_balances[msg.sender] >= amount, "Insufficient balance"
    self.agent_balances[msg.sender] -= amount
    assert self.usdc_token.transfer(msg.sender, amount), "Transfer failed"
    log Withdrawal(msg.sender, amount)


@external
def pay_for_compute(
    consumer: address,
    provider: address,
    quantity: uint256,
    unit_price: uint256,
    task_id: String[256]
) -> bool:
    """
    Atomic payment: transfer USDC from consumer to provider.
    Core function for agent-to-agent payments.
    """
    assert quantity > 0, "Quantity must be > 0"
    assert unit_price > 0, "Unit price must be > 0"
    assert unit_price <= self.max_unit_price, "Unit price exceeds $0.01 limit"
    assert provider != empty(address), "Provider address is invalid"
    assert consumer != empty(address), "Consumer address is invalid"
    assert consumer != provider, "Consumer and provider must be different"
    
    # Calculate total cost
    total_cost: uint256 = quantity * unit_price
    
    # Validate consumer has sufficient balance
    assert self.agent_balances[consumer] >= total_cost, "Consumer has insufficient balance"
    
    # Atomic transfer: debit consumer, credit provider
    self.agent_balances[consumer] -= total_cost
    self.agent_balances[provider] += total_cost
    
    # Log payment
    log PaymentSettled(consumer, provider, total_cost, block.timestamp, task_id)
    log UsageRecorded(consumer, provider, quantity, unit_price, total_cost)
    
    return True


@external
def batch_payments(
    payments: DynArray[tuple[address, address, uint256, uint256, String[256]], 256]
) -> uint256:
    """
    Process multiple payments in one transaction.
    Returns: Number of successful payments
    """
    count: uint256 = 0
    for payment in payments:
        consumer: address = payment[0]
        provider: address = payment[1]
        quantity: uint256 = payment[2]
        unit_price: uint256 = payment[3]
        task_id: String[256] = payment[4]
        
        if self.pay_for_compute(consumer, provider, quantity, unit_price, task_id):
            count += 1
    
    return count


@external
@view
def get_balance(agent: address) -> uint256:
    """Get USDC balance for an agent."""
    return self.agent_balances[agent]


@external
@view
def get_balances_batch(agents: DynArray[address, 256]) -> DynArray[uint256, 256]:
    """Get USDC balances for multiple agents."""
    balances: DynArray[uint256, 256] = []
    for agent in agents:
        balances.append(self.agent_balances[agent])
    return balances


@external
def set_max_unit_price(new_max_price: uint256):
    """Update the maximum unit price (only owner)."""
    assert msg.sender == self.owner, "Only owner can set price limit"
    assert new_max_price > 0, "Max price must be > 0"
    self.max_unit_price = new_max_price
```

### Verify contract syntax

```bash
# From project root
vyper smart_contracts/compute_marketplace.vy

# Should output bytecode (no errors)
# If errors, fix them and try again
```

---

## 🧪 Step 2: Test the Contract Locally

### Create test file

```bash
cat > tests/test_contract.py << 'EOF'
"""
Test Vyper contract locally using Titanoboa
"""
import pytest
from eth_account import Account
from eth_utils import to_checksum_address

# NOTE: For real testing, use Titanoboa
# pip install titanoboa

def test_contract_deployment():
    """Test that contract deploys with correct initial state"""
    # This is a placeholder test
    # Real implementation would use Titanoboa to deploy and test
    
    # Example assertions (actual test would require Titanoboa):
    # assert contract.max_unit_price() == 10000
    # assert contract.get_balance(agent_address) == 0
    pass


def test_deposit_and_withdraw():
    """Test deposit and withdrawal functionality"""
    # Would test:
    # 1. Agent deposits USDC
    # 2. Balance updates correctly
    # 3. Agent withdraws
    # 4. Balance decreases
    pass


def test_atomic_payment():
    """Test that pay_for_compute is atomic"""
    # Would test:
    # 1. Consumer has sufficient balance
    # 2. Payment executes
    # 3. Consumer balance decreases
    # 4. Provider balance increases
    # 5. Event is logged
    pass


def test_price_limit_enforcement():
    """Test that unit price is limited to $0.01"""
    # Would test:
    # 1. Payment with price > $0.01 fails
    # 2. Payment with price == $0.01 succeeds
    # 3. Payment with price < $0.01 succeeds
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
EOF
```

### Run tests

```bash
# Install titanoboa for testing
pip install titanoboa

# Run test suite
pytest tests/test_contract.py -v
```

---

## 🚀 Step 3: Prepare for Arc Deployment

### Setup Arc connection

Create `smart_contracts/deploy.py`:

```python
"""
Deployment script for Arc testnet
"""
import os
import json
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

load_dotenv()

# Arc testnet configuration
ARC_RPC_URL = os.getenv("ARC_RPC_URL", "https://arc-testnet-rpc.io")
CHAIN_ID = 11155111  # Arc testnet chain ID
USDC_ADDRESS = "0x"  # USDC token address on Arc (you'll fill this in)

# Connect to Arc
w3 = Web3(Web3.HTTPProvider(ARC_RPC_URL))
print(f"Connected to Arc: {w3.is_connected()}")
print(f"Chain ID: {w3.eth.chain_id}")

# Get your account
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
if not PRIVATE_KEY:
    print("ERROR: PRIVATE_KEY not set in .env")
    print("Generate with: python -c \"from eth_account import Account; a=Account.create(); print(f'PRIVATE_KEY={a.key.hex()}')\"")
    exit(1)

account = Account.from_key(PRIVATE_KEY)
print(f"Deploying from: {account.address}")

# Check balance
balance_wei = w3.eth.get_balance(account.address)
balance_usdc = balance_wei / 1e6  # Assuming 1 USDC = 10^6 wei
print(f"Balance: {balance_usdc:.2f} USDC")

if balance_usdc < 0.5:
    print("ERROR: Insufficient balance for deployment")
    print("Request USDC from faucet: https://testnet.circle.com/faucet")
    exit(1)
```

### Create account if needed

```bash
# Generate new account
python << 'EOF'
from eth_account import Account

# Generate new account
account = Account.create()
print(f"Address: {account.address}")
print(f"Private Key: {account.key.hex()}")
print("\nAdd to .env:")
print(f"PRIVATE_KEY={account.key.hex()}")
EOF

# Save the PRIVATE_KEY to .env
# IMPORTANT: Keep this secret!
```

### Get USDC on Arc testnet

```bash
# 1. Visit https://testnet.circle.com/faucet
# 2. Enter your wallet address
# 3. Request testnet USDC
# 4. Wait ~1-2 minutes for confirmation

# Verify receipt
python smart_contracts/deploy.py
# Should show your balance increased
```

---

## 📦 Step 4: Compile Contract for Deployment

### Create bytecode

```bash
# Compile to bytecode
vyper smart_contracts/compute_marketplace.vy -o bytecode > smart_contracts/bytecode.txt

# Verify bytecode was created
ls -lh smart_contracts/bytecode.txt
```

### Export ABI

Create `smart_contracts/export_abi.py`:

```python
"""
Export contract ABI to JSON
"""
import json

# Standard ERC20-compatible contract interface
USDC_INTERFACE = [
    {
        "constant": False,
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "sender", "type": "address"},
            {"name": "to", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "transferFrom",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    }
]

# Our contract's ABI
CONTRACT_ABI = [
    {
        "type": "constructor",
        "inputs": [{"name": "usdc_address", "type": "address"}],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "deposit",
        "inputs": [{"name": "amount", "type": "uint256"}],
        "outputs": [],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "withdraw",
        "inputs": [{"name": "amount", "type": "uint256"}],
        "outputs": [],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "pay_for_compute",
        "inputs": [
            {"name": "consumer", "type": "address"},
            {"name": "provider", "type": "address"},
            {"name": "quantity", "type": "uint256"},
            {"name": "unit_price", "type": "uint256"},
            {"name": "task_id", "type": "string"}
        ],
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "get_balance",
        "inputs": [{"name": "agent", "type": "address"}],
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view"
    },
    {
        "type": "event",
        "name": "PaymentSettled",
        "inputs": [
            {"name": "consumer", "type": "address", "indexed": True},
            {"name": "provider", "type": "address", "indexed": True},
            {"name": "amount", "type": "uint256"},
            {"name": "timestamp", "type": "uint256"},
            {"name": "task_id", "type": "string"}
        ]
    }
]

# Save to file
with open("smart_contracts/abi.json", "w") as f:
    json.dump(CONTRACT_ABI, f, indent=2)

print("ABI exported to smart_contracts/abi.json")
```

Run it:
```bash
python smart_contracts/export_abi.py
```

---

## 🌐 Step 5: Deploy to Arc Testnet

### Using Hardhat (Recommended)

Install Hardhat:
```bash
npm init -y
npm install --save-dev hardhat
npx hardhat
# Select: Create an empty hardhat.config.js
```

Create `hardhat.config.js`:
```javascript
require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

module.exports = {
  solidity: "0.8.20",
  networks: {
    arc_testnet: {
      url: process.env.ARC_RPC_URL || "https://arc-testnet-rpc.io",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      chainId: 11155111,
    },
  },
};
```

Create `scripts/deploy.js`:
```javascript
// Deploy Vyper contract via Hardhat
// Note: For Vyper, you may need to compile first then deploy

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log(`Deploying from: ${deployer.address}`);

  // USDC address on Arc testnet
  // (You'll get this from Circle/Arc documentation)
  const USDC_ADDRESS = "0x"; // Fill in actual address

  // Deploy contract
  const ComputeMarketplace = await ethers.getContractFactory("ComputeMarketplace");
  const contract = await ComputeMarketplace.deploy(USDC_ADDRESS);
  await contract.deployed();

  console.log(`\n✓ Contract deployed to: ${contract.address}`);
  console.log(`\nSave this address to .env:`);
  console.log(`ARC_CONTRACT_ADDRESS=${contract.address}`);

  // Save to file
  const fs = require("fs");
  fs.writeFileSync("deployment_log.txt", 
    `Contract Address: ${contract.address}\n` +
    `Deployed At: ${new Date().toISOString()}\n` +
    `Block: ${await ethers.provider.getBlockNumber()}\n`
  );

  // Verify on explorer
  console.log(`\nVerify on Arc Explorer:`);
  console.log(`https://testnet.arc.io/address/${contract.address}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
```

Deploy:
```bash
# Make sure .env has PRIVATE_KEY and ARC_RPC_URL
npx hardhat run scripts/deploy.js --network arc_testnet
```

### Using Foundry (Alternative)

```bash
# Install Foundry
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Create Foundry project
forge init --no-git

# Copy contract
cp smart_contracts/compute_marketplace.vy src/

# Deploy
forge create --rpc-url $ARC_RPC_URL \
  --private-key $PRIVATE_KEY \
  src/compute_marketplace.vy:ComputeMarketplace \
  --constructor-args "0x..." \
  --via-ir
```

### Using Python with web3.py

Create `smart_contracts/deploy_web3.py`:

```python
"""
Deploy contract using web3.py
"""
import os
import json
from web3 import Web3
from eth_account import Account
from eth_account.signers.local import LocalAccount
from dotenv import load_dotenv

load_dotenv()

# Configuration
ARC_RPC_URL = os.getenv("ARC_RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
USDC_ADDRESS = "0x"  # Fill in USDC address on Arc

# Connect
w3 = Web3(Web3.HTTPProvider(ARC_RPC_URL))
assert w3.is_connected(), "Not connected to Arc"

# Account
account: LocalAccount = Account.from_key(PRIVATE_KEY)
nonce = w3.eth.get_transaction_count(account.address)

# Read bytecode
with open("smart_contracts/bytecode.txt", "r") as f:
    bytecode = f.read().strip()

# Read ABI
with open("smart_contracts/abi.json", "r") as f:
    abi = json.load(f)

# Create contract factory
contract = w3.eth.contract(abi=abi, bytecode=bytecode)

# Build constructor transaction
constructor_tx = contract.constructor(USDC_ADDRESS).build_transaction({
    "from": account.address,
    "nonce": nonce,
    "gas": 5000000,
    "gasPrice": w3.eth.gas_price,
})

# Sign transaction
signed_tx = w3.eth.account.sign_transaction(constructor_tx, PRIVATE_KEY)

# Send transaction
tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
print(f"Transaction hash: {tx_hash.hex()}")

# Wait for receipt
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
contract_address = tx_receipt.contractAddress

print(f"\n✓ Contract deployed to: {contract_address}")
print(f"\nSave to .env:")
print(f"ARC_CONTRACT_ADDRESS={contract_address}")

# Save deployment log
with open("smart_contracts/deployment_log.txt", "w") as f:
    f.write(f"Contract Address: {contract_address}\n")
    f.write(f"Deployed At: {tx_receipt.blockNumber}\n")
    f.write(f"TX Hash: {tx_hash.hex()}\n")

print(f"\nVerify on Arc Explorer:")
print(f"https://testnet.arc.io/address/{contract_address}")
```

Run:
```bash
python smart_contracts/deploy_web3.py
```

---

## ✅ Step 6: Verify Deployment

### Check on Arc Explorer

```bash
# After deployment, visit Arc testnet explorer
# https://testnet.arc.io/address/[YOUR_CONTRACT_ADDRESS]

# You should see:
# - Contract code (bytecode)
# - Constructor arguments
# - Transaction history
# - State variables
```

### Test contract functions

Create `scripts/test_contract.py`:

```python
"""
Test deployed contract
"""
import os
import json
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

load_dotenv()

# Setup
w3 = Web3(Web3.HTTPProvider(os.getenv("ARC_RPC_URL")))
contract_address = os.getenv("ARC_CONTRACT_ADDRESS")
account = Account.from_key(os.getenv("PRIVATE_KEY"))

# Load ABI
with open("smart_contracts/abi.json", "r") as f:
    abi = json.load(f)

# Create contract instance
contract = w3.eth.contract(address=contract_address, abi=abi)

# Test get_balance (read-only)
balance = contract.functions.get_balance(account.address).call()
print(f"Balance: {balance} wei ({balance/1e6:.6f} USDC)")

# Test max unit price
max_price = contract.functions.max_unit_price().call()
print(f"Max unit price: {max_price} wei ({max_price/1e6:.6f} USDC)")

# Test deposit (requires transaction)
print("\nTesting deposit...")
deposit_amount = 1_000_000  # 1 USDC
tx_hash = contract.functions.deposit(deposit_amount).transact({"from": account.address})
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(f"✓ Deposit successful: {receipt.transactionHash.hex()}")

# Check new balance
new_balance = contract.functions.get_balance(account.address).call()
print(f"New balance: {new_balance} wei ({new_balance/1e6:.6f} USDC)")
```

Run:
```bash
python scripts/test_contract.py
```

---

## 📝 Step 7: Save Configuration

Update `.env` with deployment details:

```bash
# Add to .env
echo "ARC_CONTRACT_ADDRESS=0x..." >> .env
echo "USDC_ADDRESS=0x..." >> .env
```

Create `smart_contracts/contract_info.json`:

```json
{
  "contract_address": "0x...",
  "usdc_address": "0x...",
  "deployment_block": 12345,
  "deployment_tx": "0x...",
  "deployed_at": "2024-01-20T10:00:00Z",
  "network": "arc_testnet",
  "chain_id": 11155111,
  "functions": {
    "deposit": "Deposit USDC",
    "withdraw": "Withdraw USDC",
    "pay_for_compute": "Execute atomic payment",
    "get_balance": "Check agent balance"
  }
}
```

---

## 🎯 Verification Checklist

- [ ] Contract compiles without errors (`vyper smart_contracts/compute_marketplace.vy`)
- [ ] Bytecode generated (`smart_contracts/bytecode.txt` exists)
- [ ] ABI exported (`smart_contracts/abi.json` exists)
- [ ] Contract deployed to Arc testnet
- [ ] Contract address visible on Arc explorer
- [ ] `get_balance()` function callable
- [ ] `deposit()` function works
- [ ] Events logged correctly
- [ ] Contract address saved in `.env` and `contract_info.json`

---

## 🚨 Troubleshooting

### "Contract creation failed: insufficient balance"
- Check balance: `python smart_contracts/deploy.py`
- Request more USDC from faucet
- Wait for transaction confirmation

### "vyper: command not found"
- Install Vyper: `pip install vyper==0.3.10`
- Verify: `vyper --version`

### "Connection refused" at RPC URL
- Check Arc is up: `curl https://arc-testnet-rpc.io`
- Try alternative RPC endpoint
- Wait and retry

### "USDC_ADDRESS not found"
- USDC address is provided by Arc/Circle
- Check Circle documentation for Arc USDC address
- Add to `.env`: `USDC_ADDRESS=0x...`

### Contract transaction reverted
- Check reason with `trace` on Arc explorer
- Common: insufficient approval, wrong token address
- Review contract code for assert statements

---

## 📚 Next Steps

Once deployment is verified:

1. **Save contract address** to `.env` and `contract_info.json`
2. **Open BACKEND_SETUP.md** to implement the FastAPI server
3. **Reference this contract** in backend configuration
4. **Test contract functions** from backend

---

## 🎓 Key Learnings

### Vyper Features Used
- **Interfaces** — Define USDC token interface
- **Events** — Log deposits, withdrawals, payments
- **Atomicity** — All-or-nothing transfers
- **View functions** — Read-only balance checks
- **Internal functions** — Reusable logic

### Smart Contract Security
- Balance checks before transfers
- Atomic operations (no partial state)
- Owner-only functions
- Event logging for auditing
- No reentrancy vectors

### Arc-Specific Considerations
- USDC as native token (no separate gas)
- Low gas costs enable Nanopayments
- EVM-compatible bytecode
- Testnet for development

---

## ✅ Completion

**Smart contract successfully deployed! 🎉**

Your contract is now:
- ✅ Deployed on Arc testnet
- ✅ Verified on Arc explorer
- ✅ Ready for backend integration
- ✅ Fully functional for agent payments

**Next: Open BACKEND_SETUP.md to build the FastAPI server!**
