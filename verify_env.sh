#!/bin/bash

################################################################################
# Environment Verification Script
# Tests all Arc configuration values with curl commands
# Usage: bash verify_env.sh
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration file
ENV_FILE=".env"

################################################################################
# Helper functions
################################################################################

load_env() {
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${RED}✗ $ENV_FILE not found${NC}"
        echo "Run: bash setup_env.sh"
        exit 1
    fi
    
    # Load environment variables
    export $(cat "$ENV_FILE" | grep -v '^#' | grep -v '^$' | xargs)
}

check_value() {
    local key=$1
    local value=$(eval echo \$$key)
    
    if [ -z "$value" ]; then
        echo -e "${RED}✗ $key is empty${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✓ $key is set${NC}"
    return 0
}

test_rpc() {
    local rpc_url=$1
    
    echo ""
    echo -e "${BLUE}Testing RPC endpoint...${NC}"
    echo "URL: $rpc_url"
    echo ""
    
    response=$(curl -s -X POST "$rpc_url" \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}')
    
    echo "Testing eth_chainId..."
    
    if echo "$response" | grep -q '"result"'; then
        chain_id=$(echo "$response" | grep -o '"result":"[^"]*"' | cut -d'"' -f4)
        echo -e "${GREEN}✓ RPC responding correctly${NC}"
        echo "  Chain ID: $chain_id"
        return 0
    else
        echo -e "${RED}✗ RPC not responding correctly${NC}"
        echo "  Response: $response"
        return 1
    fi
}

test_block_number() {
    local rpc_url=$1
    
    echo ""
    echo -e "${BLUE}Testing block number...${NC}"
    
    response=$(curl -s -X POST "$rpc_url" \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}')
    
    if echo "$response" | grep -q '"result"'; then
        block=$(echo "$response" | grep -o '"result":"[^"]*"' | cut -d'"' -f4)
        echo -e "${GREEN}✓ Current block: $block${NC}"
        return 0
    else
        echo -e "${RED}✗ Could not fetch block number${NC}"
        return 1
    fi
}

test_wallet_format() {
    local private_key=$1
    
    echo ""
    echo -e "${BLUE}Validating private key format...${NC}"
    
    if [[ $private_key =~ ^0x[0-9a-fA-F]{64}$ ]]; then
        echo -e "${GREEN}✓ Private key format is valid${NC}"
        
        # Extract wallet address from private key
        wallet_address=$(python3 -c "from eth_account import Account; a=Account.from_key('$private_key'); print(a.address)" 2>/dev/null)
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Wallet address: $wallet_address${NC}"
            return 0
        fi
    else
        echo -e "${RED}✗ Private key format invalid${NC}"
        echo "  Must be 0x followed by 64 hex characters"
        return 1
    fi
}

test_usdc_address() {
    local rpc_url=$1
    local usdc_address=$2
    
    echo ""
    echo -e "${BLUE}Validating USDC address...${NC}"
    echo "Address: $usdc_address"
    
    # Validate format
    if [[ $usdc_address =~ ^0x[0-9a-fA-F]{40}$ ]]; then
        echo -e "${GREEN}✓ Address format is valid${NC}"
    else
        echo -e "${RED}✗ Address format invalid${NC}"
        return 1
    fi
    
    # Try to call decimals() function on USDC contract
    # Signature for decimals() = 0x313ce567
    echo "Testing USDC contract call..."
    
    response=$(curl -s -X POST "$rpc_url" \
        -H "Content-Type: application/json" \
        -d "{
            \"jsonrpc\":\"2.0\",
            \"method\":\"eth_call\",
            \"params\":[{
                \"to\":\"$usdc_address\",
                \"data\":\"0x313ce567\"
            },\"latest\"],
            \"id\":1
        }")
    
    if echo "$response" | grep -q '"result"'; then
        echo -e "${GREEN}✓ USDC contract is responding${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ USDC contract not responding${NC}"
        echo "  This is OK if address is correct but contract hasn't been deployed"
        return 0
    fi
}

test_wallet_balance() {
    local rpc_url=$1
    local wallet_address=$2
    
    echo ""
    echo -e "${BLUE}Checking wallet balance...${NC}"
    echo "Wallet: $wallet_address"
    
    response=$(curl -s -X POST "$rpc_url" \
        -H "Content-Type: application/json" \
        -d "{
            \"jsonrpc\":\"2.0\",
            \"method\":\"eth_getBalance\",
            \"params\":[\"$wallet_address\",\"latest\"],
            \"id\":1
        }")
    
    if echo "$response" | grep -q '"result"'; then
        balance=$(echo "$response" | grep -o '"result":"[^"]*"' | cut -d'"' -f4)
        balance_eth=$(echo "scale=6; $(echo $balance | sed 's/^0x//' | tr '[:lower:]' '[:upper:]' | xargs -I {} python3 -c 'print(int("0x{}", 16) / 1e18)' 2>/dev/null || echo 0)" | bc)
        
        if [ "$balance" = "0x0" ]; then
            echo -e "${YELLOW}⚠ Wallet balance is 0${NC}"
            echo "  Fund your wallet from testnet faucet"
            return 1
        else
            echo -e "${GREEN}✓ Wallet has balance: ~$balance_eth ETH${NC}"
            return 0
        fi
    else
        echo -e "${RED}✗ Could not fetch wallet balance${NC}"
        return 1
    fi
}

################################################################################
# Main execution
################################################################################

clear

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║     Environment Configuration Verification                   ║"
echo "║     Arc x Circle Hackathon                                    ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Load environment
echo "Loading environment from $ENV_FILE..."
load_env
echo -e "${GREEN}✓ Environment loaded${NC}"
echo ""

################################################################################
# Check all required values exist
################################################################################

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Checking Configuration Values${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

all_values_set=true

check_value "ARC_RPC_URL" || all_values_set=false
check_value "ARC_CHAIN_ID" || all_values_set=false
check_value "USDC_ADDRESS" || all_values_set=false
check_value "PRIVATE_KEY" || all_values_set=false

if [ "$all_values_set" = false ]; then
    echo ""
    echo -e "${YELLOW}⚠ Some values are missing${NC}"
    echo "Run: bash setup_env.sh"
    exit 1
fi

################################################################################
# Test RPC connection
################################################################################

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Testing RPC Connection${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if ! test_rpc "$ARC_RPC_URL"; then
    echo -e "${RED}✗ RPC connection failed${NC}"
    echo "Check your ARC_RPC_URL in .env"
    exit 1
fi

if ! test_block_number "$ARC_RPC_URL"; then
    echo -e "${YELLOW}⚠ Warning: Could not fetch block number${NC}"
fi

################################################################################
# Test wallet
################################################################################

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Testing Wallet${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

wallet_address=$(python3 -c "from eth_account import Account; a=Account.from_key('$PRIVATE_KEY'); print(a.address)" 2>/dev/null)

if ! test_wallet_format "$PRIVATE_KEY"; then
    echo -e "${RED}✗ Wallet validation failed${NC}"
    exit 1
fi

# Test balance
if ! test_wallet_balance "$ARC_RPC_URL" "$wallet_address"; then
    echo -e "${YELLOW}⚠ Wallet not funded${NC}"
    echo "Visit: https://testnet.circle.com/faucet to fund"
fi

################################################################################
# Test USDC address
################################################################################

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Testing USDC Contract${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

test_usdc_address "$ARC_RPC_URL" "$USDC_ADDRESS" || true

################################################################################
# Summary
################################################################################

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ Verification Complete${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "Configuration Summary:"
echo "  RPC URL: $ARC_RPC_URL"
echo "  Chain ID: $ARC_CHAIN_ID"
echo "  Wallet: $wallet_address"
echo "  USDC Address: $USDC_ADDRESS"
echo ""

echo "Next steps:"
echo "  1. Verify .env is correct: cat .env | grep -v '^#' | grep -v '^$'"
echo "  2. Keep .env secure (add to .gitignore)"
echo "  3. Start building: Follow GETTING_STARTED.md"
echo ""
echo -e "${GREEN}Ready to deploy smart contract! 🚀${NC}"
echo ""
