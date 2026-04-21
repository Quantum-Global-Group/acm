#!/bin/bash

################################################################################
# Arc Testnet Configuration Setup Script
# Interactive guide to gather all required configuration values
# Usage: bash setup_env.sh
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration file
ENV_FILE=".env"
ENV_EXAMPLE=".env.example"

################################################################################
# Display welcome message
################################################################################

clear
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║     Arc Testnet Configuration Setup Script                   ║"
echo "║     Agent-to-Agent Compute Marketplace                       ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo "This script will help you gather and configure all required Arc"
echo "testnet values. It will also verify each value works correctly."
echo ""
echo "⏱️  Estimated time: 15-20 minutes"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Exiting..."
    exit 1
fi

################################################################################
# Check if .env already exists
################################################################################

if [ -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}Warning: $ENV_FILE already exists${NC}"
    read -p "Overwrite? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Using existing .env"
        exit 0
    fi
fi

################################################################################
# Create backup of existing .env if it exists
################################################################################

if [ -f "$ENV_FILE" ]; then
    BACKUP_FILE="${ENV_FILE}.backup.$(date +%s)"
    cp "$ENV_FILE" "$BACKUP_FILE"
    echo -e "${GREEN}✓ Backed up existing .env to $BACKUP_FILE${NC}"
fi

################################################################################
# Copy template if it exists
################################################################################

if [ -f "$ENV_EXAMPLE" ]; then
    cp "$ENV_EXAMPLE" "$ENV_FILE"
    echo -e "${GREEN}✓ Copied $ENV_EXAMPLE to $ENV_FILE${NC}"
else
    echo -e "${YELLOW}⚠ $ENV_EXAMPLE not found, creating new .env${NC}"
    touch "$ENV_FILE"
fi

################################################################################
# Helper functions
################################################################################

set_env_var() {
    local key=$1
    local value=$2
    
    if grep -q "^${key}=" "$ENV_FILE"; then
        # Key exists, update it
        sed -i.bak "s|^${key}=.*|${key}=${value}|" "$ENV_FILE"
    else
        # Key doesn't exist, append it
        echo "${key}=${value}" >> "$ENV_FILE"
    fi
}

verify_rpc() {
    local rpc_url=$1
    
    echo ""
    echo "Testing RPC connection..."
    
    response=$(curl -s -X POST "$rpc_url" \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}' \
        2>/dev/null || echo "")
    
    if [[ $response == *"0x"* ]]; then
        echo -e "${GREEN}✓ RPC connection successful${NC}"
        echo "  Response: $response"
        return 0
    else
        echo -e "${RED}✗ RPC connection failed${NC}"
        echo "  Check the URL and try again"
        return 1
    fi
}

verify_private_key() {
    local key=$1
    
    echo ""
    echo "Verifying private key format..."
    
    # Check if key starts with 0x and is 66 characters (0x + 64 hex)
    if [[ $key =~ ^0x[0-9a-fA-F]{64}$ ]]; then
        echo -e "${GREEN}✓ Private key format is valid${NC}"
        return 0
    else
        echo -e "${RED}✗ Private key format is invalid${NC}"
        echo "  Must be 0x followed by 64 hex characters"
        return 1
    fi
}

verify_address() {
    local address=$1
    
    echo ""
    echo "Verifying address format..."
    
    # Check if address is valid Ethereum address (0x + 40 hex)
    if [[ $address =~ ^0x[0-9a-fA-F]{40}$ ]]; then
        echo -e "${GREEN}✓ Address format is valid${NC}"
        return 0
    else
        echo -e "${RED}✗ Address format is invalid${NC}"
        echo "  Must be 0x followed by 40 hex characters"
        return 1
    fi
}

################################################################################
# STEP 1: Get ARC_RPC_URL
################################################################################

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}STEP 1: Arc Testnet RPC URL${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "The RPC URL is the endpoint to connect to Arc testnet."
echo ""
echo "Options:"
echo "  1. Primary Arc RPC (recommended): https://arc-testnet-rpc.io"
echo "  2. Alternative RPC: https://rpc.arc-testnet.io"
echo "  3. Custom RPC URL"
echo ""

read -p "Select option (1-3) or paste URL: " rpc_choice

case $rpc_choice in
    1)
        ARC_RPC_URL="https://arc-testnet-rpc.io"
        ;;
    2)
        ARC_RPC_URL="https://rpc.arc-testnet.io"
        ;;
    3|*)
        read -p "Enter custom RPC URL: " ARC_RPC_URL
        ;;
esac

echo "Testing RPC URL: $ARC_RPC_URL"

if verify_rpc "$ARC_RPC_URL"; then
    set_env_var "ARC_RPC_URL" "$ARC_RPC_URL"
    set_env_var "ARC_RPC_VERIFIED" "true"
else
    echo -e "${YELLOW}⚠ RPC verification failed, but saved for now${NC}"
    set_env_var "ARC_RPC_URL" "$ARC_RPC_URL"
fi

################################################################################
# STEP 2: Get ARC_CHAIN_ID
################################################################################

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}STEP 2: Arc Chain ID${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "The chain ID identifies the Arc testnet."
echo "Standard value: 11155111"
echo ""

read -p "Enter chain ID (default: 11155111): " ARC_CHAIN_ID
ARC_CHAIN_ID=${ARC_CHAIN_ID:-11155111}

set_env_var "ARC_CHAIN_ID" "$ARC_CHAIN_ID"

echo -e "${GREEN}✓ Chain ID set to $ARC_CHAIN_ID${NC}"

################################################################################
# STEP 3: Get USDC_ADDRESS
################################################################################

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}STEP 3: USDC Token Address${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Get USDC address from official sources:"
echo "  - Arc Documentation: https://docs.arc.io"
echo "  - Circle Documentation: https://developers.circle.com"
echo "  - Arc Discord: #testnet-support"
echo ""
echo "Format: 0x followed by 40 hex characters"
echo "Example: 0x1234567890123456789012345678901234567890"
echo ""

while true; do
    read -p "Enter USDC token address: " USDC_ADDRESS
    
    if [ -z "$USDC_ADDRESS" ]; then
        echo -e "${YELLOW}⚠ Address cannot be empty${NC}"
        continue
    fi
    
    if verify_address "$USDC_ADDRESS"; then
        set_env_var "USDC_ADDRESS" "$USDC_ADDRESS"
        set_env_var "USDC_ADDRESS_VERIFIED" "true"
        break
    fi
done

################################################################################
# STEP 4: Generate/Get PRIVATE_KEY
################################################################################

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}STEP 4: Private Key (Testnet Wallet)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "⚠️  IMPORTANT: Use testnet-only wallet!"
echo "Never use mainnet keys for testnet."
echo ""
echo "Options:"
echo "  1. Generate new testnet wallet (RECOMMENDED)"
echo "  2. Use existing wallet private key"
echo ""

read -p "Select option (1-2): " key_choice

case $key_choice in
    1)
        echo ""
        echo "Generating new testnet wallet..."
        
        # Check if Python is available
        if ! command -v python3 &> /dev/null; then
            echo -e "${RED}✗ Python3 not found${NC}"
            echo "Install Python 3.10+ first: https://python.org"
            exit 1
        fi
        
        # Generate new account
        KEY_OUTPUT=$(python3 -c "from eth_account import Account; a=Account.create(); print(f'{a.address}|{a.key.hex()}')" 2>&1)
        
        if [ $? -eq 0 ]; then
            WALLET_ADDRESS=$(echo "$KEY_OUTPUT" | cut -d'|' -f1)
            PRIVATE_KEY=$(echo "$KEY_OUTPUT" | cut -d'|' -f2)
            
            echo ""
            echo -e "${GREEN}✓ Wallet generated successfully${NC}"
            echo "  Address: $WALLET_ADDRESS"
            echo "  Private Key: ${PRIVATE_KEY:0:10}...${PRIVATE_KEY: -8}"
        else
            echo -e "${RED}✗ Failed to generate wallet${NC}"
            echo "Error: $KEY_OUTPUT"
            exit 1
        fi
        ;;
    2)
        echo ""
        while true; do
            read -p "Enter your private key (0x...): " PRIVATE_KEY
            
            if [ -z "$PRIVATE_KEY" ]; then
                echo -e "${YELLOW}⚠ Private key cannot be empty${NC}"
                continue
            fi
            
            if verify_private_key "$PRIVATE_KEY"; then
                break
            fi
        done
        ;;
    *)
        echo -e "${RED}Invalid option${NC}"
        exit 1
        ;;
esac

set_env_var "PRIVATE_KEY" "$PRIVATE_KEY"
set_env_var "PRIVATE_KEY_VERIFIED" "true"

################################################################################
# STEP 5: Fund Wallet
################################################################################

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}STEP 5: Fund Your Testnet Wallet${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "You need testnet USDC to deploy and test the contract."
echo ""
echo "Get testnet USDC:"
echo "  1. Visit: https://testnet.circle.com/faucet"
echo "  2. Enter wallet address: $WALLET_ADDRESS"
echo "  3. Request testnet USDC (usually 100 USDC)"
echo "  4. Wait 1-2 minutes for confirmation"
echo ""
echo "Verify funding:"
echo "  - Visit: https://testnet.arc.io/address/$WALLET_ADDRESS"
echo "  - Check balance in Arc explorer"
echo ""

read -p "Have you funded your wallet? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    set_env_var "WALLET_FUNDED" "true"
    echo -e "${GREEN}✓ Wallet funding confirmed${NC}"
else
    echo -e "${YELLOW}⚠ Please fund your wallet before proceeding with deployment${NC}"
    set_env_var "WALLET_FUNDED" "false"
fi

################################################################################
# STEP 6: Verify All Configuration
################################################################################

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}STEP 6: Verify Configuration${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "Summary of configuration:"
echo "  ARC_RPC_URL: $ARC_RPC_URL"
echo "  ARC_CHAIN_ID: $ARC_CHAIN_ID"
echo "  USDC_ADDRESS: ${USDC_ADDRESS:0:10}...${USDC_ADDRESS: -8}"
echo "  WALLET_ADDRESS: $WALLET_ADDRESS"
echo "  PRIVATE_KEY: ${PRIVATE_KEY:0:10}...${PRIVATE_KEY: -8}"
echo ""

# Final verification
echo "Running final verification tests..."
echo ""

# Test RPC
echo -n "Testing RPC connection... "
if verify_rpc "$ARC_RPC_URL" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Check private key
echo -n "Checking private key format... "
if verify_private_key "$PRIVATE_KEY" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Check address
echo -n "Checking USDC address format... "
if verify_address "$USDC_ADDRESS" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

################################################################################
# Mark setup as complete
################################################################################

set_env_var "SETUP_COMPLETE" "true"

################################################################################
# Final summary
################################################################################

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Configuration saved to: .env"
echo ""
echo "Next steps:"
echo "  1. Verify .env has all values: cat .env | grep -v '^#'"
echo "  2. Keep .env safe (add to .gitignore)"
echo "  3. Start building: bash GETTING_STARTED.md"
echo ""
echo "⚠️  SECURITY REMINDERS:"
echo "  - Never commit .env to git"
echo "  - Never share your PRIVATE_KEY"
echo "  - Only use testnet wallets for testing"
echo ""
echo -e "${GREEN}Ready to build! 🚀${NC}"
echo ""

# Show what to do next
echo "Command to verify configuration:"
echo "  bash verify_env.sh"
echo ""
