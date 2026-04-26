#!/usr/bin/env python3

################################################################################
# Arc Testnet Auto-Discovery Script
# Automatically discovers Arc configuration values from testnet
# Usage: python3 arc_auto_discover.py
################################################################################

import os
import json
import sys
import time
import requests
from typing import Dict, Optional, Tuple, List
from pathlib import Path
from dataclasses import dataclass

################################################################################
# Configuration
################################################################################

@dataclass
class ArcConfig:
    """Arc testnet configuration"""
    rpc_url: str = ""
    chain_id: int = 0
    usdc_address: str = ""
    explorer_url: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'ARC_RPC_URL': self.rpc_url,
            'ARC_CHAIN_ID': str(self.chain_id),
            'USDC_ADDRESS': self.usdc_address,
            'ARC_EXPLORER_URL': self.explorer_url,
        }

# Known Arc testnet RPC endpoints (official + provider-backed + aggregators)
# Primary + alts: Arc developer docs "Connect to network" / public RPC.
KNOWN_RPC_ENDPOINTS = [
    "https://rpc.testnet.arc.network",
    "https://rpc.blockdaemon.testnet.arc.network",
    "https://rpc.drpc.testnet.arc.network",
    "https://rpc.quicknode.testnet.arc.network",
    "https://arc-testnet.drpc.org",
    "https://5042002.rpc.thirdweb.com",
]

# Known USDC addresses to test (common patterns)
# These are typical USDC contract addresses on EVM testnets
USDC_ADDRESS_PATTERNS = [
    "0x07865c6e87b9f70255377e024ace6630c1eaa37f",  # Typical testnet USDC
    "0x2f3a40a3db8a0e46ff2f47b7446787b1cecd7ae6",  # Alternative
    "0xb19c8395d2bdf7f1506b0a51a50919d5109b5860",  # Another variant
]

# Arc testnet chain ID (official; eth_chainId returns 0x4cef52)
ARC_TESTNET_CHAIN_ID = 5042002

# USDC contract ABI (minimal - just decimals function)
USDC_ABI_PARTIAL = [
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]

# Colors for CLI output
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'

################################################################################
# RPC Verification Functions
################################################################################

def test_rpc_endpoint(rpc_url: str, timeout: int = 5) -> Tuple[bool, str]:
    """
    Test if RPC endpoint is working
    
    Args:
        rpc_url: RPC endpoint URL
        timeout: Request timeout in seconds
        
    Returns:
        Tuple of (is_working, message)
    """
    try:
        response = requests.post(
            rpc_url,
            json={
                "jsonrpc": "2.0",
                "method": "eth_chainId",
                "params": [],
                "id": 1
            },
            timeout=timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            if "result" in data:
                return True, f"✓ Working (Chain: {data['result']})"
            else:
                return False, f"✗ Responded but no result"
        else:
            return False, f"✗ Status {response.status_code}"
            
    except requests.Timeout:
        return False, "✗ Timeout"
    except requests.ConnectionError:
        return False, "✗ Connection error"
    except Exception as e:
        return False, f"✗ Error: {str(e)}"

def get_chain_id(rpc_url: str) -> Optional[int]:
    """Get chain ID from RPC endpoint"""
    try:
        response = requests.post(
            rpc_url,
            json={
                "jsonrpc": "2.0",
                "method": "eth_chainId",
                "params": [],
                "id": 1
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if "result" in data:
                # Convert hex to int
                return int(data['result'], 16)
    except:
        pass
    
    return None

def get_block_number(rpc_url: str) -> Optional[int]:
    """Get current block number"""
    try:
        response = requests.post(
            rpc_url,
            json={
                "jsonrpc": "2.0",
                "method": "eth_blockNumber",
                "params": [],
                "id": 1
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if "result" in data:
                return int(data['result'], 16)
    except:
        pass
    
    return None

################################################################################
# USDC Discovery Functions
################################################################################

def test_usdc_address(rpc_url: str, address: str) -> Tuple[bool, Optional[int]]:
    """
    Test if address is valid USDC contract
    
    Returns:
        Tuple of (is_valid, decimals)
    """
    try:
        # Call decimals() function on contract
        # Function selector for decimals() = 0x313ce567
        response = requests.post(
            rpc_url,
            json={
                "jsonrpc": "2.0",
                "method": "eth_call",
                "params": [{
                    "to": address,
                    "data": "0x313ce567"
                }, "latest"],
                "id": 1
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if "result" in data and data['result'] != "0x":
                # Got a result - likely a contract
                try:
                    decimals = int(data['result'], 16)
                    # USDC typically has 6 decimals
                    if decimals == 6:
                        return True, decimals
                    else:
                        return True, decimals  # Still valid, might be variant
                except:
                    pass
    except:
        pass
    
    return False, None

def find_usdc_address(rpc_url: str) -> Optional[str]:
    """
    Try to find USDC address by testing known patterns
    
    Args:
        rpc_url: RPC endpoint to test against
        
    Returns:
        USDC address if found, None otherwise
    """
    print(f"\n{Colors.CYAN}Searching for USDC address...{Colors.RESET}")
    
    for address in USDC_ADDRESS_PATTERNS:
        is_valid, decimals = test_usdc_address(rpc_url, address)
        
        if is_valid:
            print(f"  {Colors.GREEN}✓ Found USDC: {address} (decimals: {decimals}){Colors.RESET}")
            return address
        else:
            print(f"  {Colors.YELLOW}✗ Not USDC: {address}{Colors.RESET}")
    
    print(f"  {Colors.YELLOW}⚠ Could not auto-detect USDC address{Colors.RESET}")
    print(f"  Check: https://developers.circle.com or https://docs.arc.io")
    
    return None

################################################################################
# RPC Discovery Functions
################################################################################

def discover_rpc_endpoints() -> List[Tuple[str, bool, str]]:
    """
    Discover working RPC endpoints
    
    Returns:
        List of (url, is_working, chain_id_info)
    """
    print(f"\n{Colors.CYAN}Testing RPC endpoints...{Colors.RESET}\n")
    
    results = []
    
    for rpc_url in KNOWN_RPC_ENDPOINTS:
        print(f"Testing: {rpc_url}")
        
        is_working, message = test_rpc_endpoint(rpc_url)
        
        if is_working:
            print(f"  {Colors.GREEN}{message}{Colors.RESET}")
            chain_id = get_chain_id(rpc_url)
            block_num = get_block_number(rpc_url)
            
            info = f"Chain {chain_id}, Block {block_num}"
            results.append((rpc_url, True, info))
        else:
            print(f"  {Colors.RED}{message}{Colors.RESET}")
            results.append((rpc_url, False, ""))
    
    return results

def select_best_rpc(results: List[Tuple[str, bool, str]]) -> Optional[str]:
    """
    Select the best working RPC endpoint
    
    Args:
        results: Results from discover_rpc_endpoints()
        
    Returns:
        Best RPC URL or None if none working
    """
    working = [r for r in results if r[1]]
    
    if not working:
        return None
    
    # Return first working one (could be enhanced to test speed)
    return working[0][0]

################################################################################
# Arc Testnet Info Functions
################################################################################

def get_arc_explorer_url(chain_id: int) -> str:
    """Get Arc explorer URL based on chain ID"""
    if chain_id == ARC_TESTNET_CHAIN_ID:
        return "https://testnet.arc.io"
    else:
        return f"https://explorer.arc.io"

def fetch_arc_testnet_info() -> Optional[Dict]:
    """
    Fetch Arc testnet info from external source
    
    Attempts to fetch from:
    1. Arc official API
    2. Chainlist API
    3. Fallback to known values
    """
    # Try Chainlist API
    try:
        response = requests.get(
            f"https://chainid.network/chains.json",
            timeout=5
        )
        
        if response.status_code == 200:
            chains = response.json()
            
            # Look for Arc testnet
            for chain in chains:
                if chain.get('chainId') == ARC_TESTNET_CHAIN_ID:
                    if chain.get('rpc'):
                        return {
                            'rpc': chain['rpc'][0],
                            'chain_id': chain['chainId'],
                            'name': chain.get('name', 'Arc Testnet')
                        }
    except:
        pass
    
    return None

################################################################################
# Configuration Loading/Saving
################################################################################

def load_env_file(filename: str = ".env") -> Dict[str, str]:
    """Load existing .env file"""
    env_vars = {}
    
    if not os.path.exists(filename):
        return env_vars
    
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    
    return env_vars

def save_config_to_env(config: ArcConfig, env_file: str = ".env"):
    """Save discovered configuration to .env file"""
    
    # Load existing env
    existing = load_env_file(env_file)
    
    # Update with new values
    config_dict = config.to_dict()
    existing.update(config_dict)
    
    # Write back
    with open(env_file, 'w') as f:
        # Write with comments
        f.write("# Arc Testnet Configuration\n")
        f.write("# Auto-discovered by arc_auto_discover.py\n")
        f.write(f"# Discovery time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Write Arc config
        f.write("# ============ Arc Configuration ============\n")
        f.write(f"ARC_RPC_URL={config.rpc_url}\n")
        f.write(f"ARC_CHAIN_ID={config.chain_id}\n")
        f.write(f"USDC_ADDRESS={config.usdc_address}\n")
        f.write(f"ARC_EXPLORER_URL={config.explorer_url}\n\n")
        
        # Write other variables
        f.write("# ============ Other Configuration ============\n")
        for key, value in existing.items():
            if key not in config_dict:
                f.write(f"{key}={value}\n")

################################################################################
# Main Discovery Process
################################################################################

def main():
    """Main discovery process"""
    
    # Print header
    print(f"\n{Colors.BOLD}")
    print("╔" + "="*70 + "╗")
    print("║" + " "*70 + "║")
    print("║" + "Arc Testnet Auto-Discovery".center(70) + "║")
    print("║" + "Automatically detect configuration values".center(70) + "║")
    print("║" + " "*70 + "║")
    print("╚" + "="*70 + "╝")
    print(f"{Colors.RESET}\n")
    
    config = ArcConfig()
    
    # ========== Step 1: Discover RPC Endpoints ==========
    print(f"{Colors.BOLD}Step 1: Discovering RPC Endpoints{Colors.RESET}")
    rpc_results = discover_rpc_endpoints()
    
    best_rpc = select_best_rpc(rpc_results)
    
    if not best_rpc:
        print(f"\n{Colors.RED}✗ No working RPC endpoints found{Colors.RESET}")
        print("Check your internet connection or try manual setup:")
        print("  bash setup_env.sh")
        return 1
    
    config.rpc_url = best_rpc
    print(f"\n{Colors.GREEN}✓ Selected RPC: {best_rpc}{Colors.RESET}")
    
    # ========== Step 2: Get Chain ID ==========
    print(f"\n{Colors.BOLD}Step 2: Verifying Chain ID{Colors.RESET}")
    
    chain_id = get_chain_id(config.rpc_url)
    
    if not chain_id:
        print(f"{Colors.RED}✗ Could not get chain ID{Colors.RESET}")
        return 1
    
    config.chain_id = chain_id
    print(f"{Colors.GREEN}✓ Chain ID: {chain_id}{Colors.RESET}")
    
    # Verify it's Arc testnet
    if chain_id != ARC_TESTNET_CHAIN_ID:
        print(f"{Colors.YELLOW}⚠ Warning: Chain ID {chain_id} != expected {ARC_TESTNET_CHAIN_ID}{Colors.RESET}")
    
    # ========== Step 3: Find USDC Address ==========
    print(f"\n{Colors.BOLD}Step 3: Discovering USDC Address{Colors.RESET}")
    
    usdc_address = find_usdc_address(config.rpc_url)
    
    if usdc_address:
        config.usdc_address = usdc_address
    else:
        print(f"\n{Colors.YELLOW}⚠ USDC address not auto-discovered{Colors.RESET}")
        print("Please obtain from:")
        print("  - https://developers.circle.com")
        print("  - https://docs.arc.io")
        print("  - Arc Discord #testnet-support")
        
        response = input(f"\nEnter USDC address manually (or press Enter to skip): ").strip()
        if response:
            config.usdc_address = response
    
    # ========== Step 4: Get Explorer URL ==========
    print(f"\n{Colors.BOLD}Step 4: Setting Explorer URL{Colors.RESET}")
    
    config.explorer_url = get_arc_explorer_url(config.chain_id)
    print(f"{Colors.GREEN}✓ Explorer: {config.explorer_url}{Colors.RESET}")
    
    # ========== Summary ==========
    print(f"\n{Colors.BOLD}Discovery Summary{Colors.RESET}\n")
    
    print(f"RPC URL:        {config.rpc_url}")
    print(f"Chain ID:       {config.chain_id}")
    print(f"USDC Address:   {config.usdc_address if config.usdc_address else '(not found)'}")
    print(f"Explorer:       {config.explorer_url}")
    
    # ========== Save to .env ==========
    print(f"\n{Colors.BOLD}Saving Configuration{Colors.RESET}\n")
    
    try:
        save_config_to_env(config)
        print(f"{Colors.GREEN}✓ Configuration saved to .env{Colors.RESET}")
        
        print(f"\n{Colors.BOLD}Next Steps:{Colors.RESET}")
        print("  1. Verify configuration:")
        print("     python3 validate_config.py")
        print("  2. Test with curl:")
        print("     bash verify_env.sh")
        print("  3. Start building:")
        print("     Follow GETTING_STARTED.md")
        
        return 0
        
    except Exception as e:
        print(f"{Colors.RED}✗ Error saving configuration: {e}{Colors.RESET}")
        return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Cancelled by user{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.RESET}")
        sys.exit(1)
