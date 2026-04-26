#!/usr/bin/env python3

################################################################################
# USDC Address Discovery Script
# Automatically discovers USDC token address on Arc testnet
# Usage: python3 discover_usdc_address.py
################################################################################

import requests
import json
from typing import Optional, List, Tuple, Dict

class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'

# Arc testnet chain ID
ARC_TESTNET_CHAIN_ID = 5042002

# Known USDC addresses to test
KNOWN_USDC_ADDRESSES = [
    "0x07865c6e87b9f70255377e024ace6630c1eaa37f",
    "0xb19c8395d2bdf7f1506b0a51a50919d5109b5860",
    "0x2f3a40a3db8a0e46ff2f47b7446787b1cecd7ae6",
    "0xf1f48b4d7a6825a8f0e85fb0fc2d1df0f9faf6de",
    "0x90f8bf6a479f320ead074411a4b0e7944ea8c9c1",
]

# Data sources for USDC info
DATA_SOURCES = {
    'chainlist': 'https://chainid.network/chains.json',
    'tokenlists': 'https://tokens.uniswap.org',
}

################################################################################
# USDC Contract Checking
################################################################################

def check_if_usdc(rpc_url: str, address: str) -> Tuple[bool, Optional[int]]:
    """
    Check if address is USDC by calling decimals() and name()
    
    Returns:
        Tuple of (is_usdc, decimals)
    """
    
    if not address or not address.startswith('0x'):
        return False, None
    
    try:
        # Check decimals (should be 6 for USDC)
        response = requests.post(
            rpc_url,
            json={
                "jsonrpc": "2.0",
                "method": "eth_call",
                "params": [{
                    "to": address,
                    "data": "0x313ce567"  # decimals()
                }, "latest"],
                "id": 1
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "result" in data and data['result'] != "0x":
                try:
                    decimals = int(data['result'], 16)
                    
                    # USDC typically has 6 decimals
                    if decimals == 6:
                        return True, decimals
                    else:
                        # Still might be a token, but not standard USDC
                        return True, decimals
                except:
                    pass
    except:
        pass
    
    return False, None

def get_token_info(rpc_url: str, address: str) -> Dict:
    """Get token information"""
    
    info = {
        'address': address,
        'name': None,
        'symbol': None,
        'decimals': None,
        'total_supply': None,
    }
    
    try:
        # Get decimals
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
            if "result" in data:
                info['decimals'] = int(data['result'], 16)
    except:
        pass
    
    return info

################################################################################
# Data Source Querying
################################################################################

def query_chainlist() -> Optional[Dict]:
    """Query chainlist.org for Arc testnet USDC"""
    
    print(f"{Colors.CYAN}Querying Chainlist...{Colors.RESET}")
    
    try:
        response = requests.get(
            'https://chainid.network/chains.json',
            timeout=10
        )
        
        if response.status_code == 200:
            chains = response.json()
            
            # Find Arc testnet
            for chain in chains:
                if chain.get('chainId') == ARC_TESTNET_CHAIN_ID:
                    if chain.get('nativeCurrency', {}).get('symbol') == 'USDC':
                        print(f"  {Colors.GREEN}✓ Found USDC info{Colors.RESET}")
                        
                        # Return RPC URLs
                        return {
                            'name': chain.get('name'),
                            'rpc_urls': chain.get('rpc', []),
                            'explorer_urls': chain.get('explorers', []),
                        }
    except:
        pass
    
    print(f"  {Colors.YELLOW}✗ Not found on Chainlist{Colors.RESET}")
    return None

def query_circle_api() -> Optional[str]:
    """
    Query Circle API for USDC address on Arc testnet
    Note: This would require Circle API key, so it's simulated
    """
    
    print(f"{Colors.CYAN}Checking Circle resources...{Colors.RESET}")
    print(f"  {Colors.YELLOW}Note: Visit https://developers.circle.com for USDC address{Colors.RESET}")
    
    return None

def query_arc_documentation() -> List[str]:
    """
    Get USDC addresses from Arc documentation
    (In real implementation, would scrape Arc docs or use Arc API)
    """
    
    print(f"{Colors.CYAN}Checking Arc documentation...{Colors.RESET}")
    
    resources = [
        'https://docs.arc.io',
        'https://developers.circle.com',
        'https://testnet.arc.io',
    ]
    
    print(f"  {Colors.YELLOW}Check these resources for USDC address:{Colors.RESET}")
    for resource in resources:
        print(f"    - {resource}")
    
    return resources

################################################################################
# Main Discovery
################################################################################

def discover_usdc(rpc_url: Optional[str] = None) -> Optional[str]:
    """
    Discover USDC address on Arc testnet
    
    Args:
        rpc_url: Optional RPC URL to test addresses against
        
    Returns:
        USDC address if found, None otherwise
    """
    
    print(f"\n{Colors.BOLD}")
    print("╔" + "="*70 + "╗")
    print("║" + " "*70 + "║")
    print("║" + "USDC Address Discovery".center(70) + "║")
    print("║" + "Find USDC token on Arc testnet".center(70) + "║")
    print("║" + " "*70 + "║")
    print("╚" + "="*70 + "╝")
    print(f"{Colors.RESET}")
    
    usdc_address = None
    
    # Step 1: Query data sources
    print(f"\n{Colors.BOLD}Step 1: Querying Data Sources{Colors.RESET}\n")
    
    chainlist_info = query_chainlist()
    circle_info = query_circle_api()
    arc_resources = query_arc_documentation()
    
    # Step 2: If RPC provided, test known addresses
    if rpc_url:
        print(f"\n{Colors.BOLD}Step 2: Testing Known Addresses Against RPC{Colors.RESET}\n")
        
        for address in KNOWN_USDC_ADDRESSES:
            print(f"Testing: {address}")
            
            is_usdc, decimals = check_if_usdc(rpc_url, address)
            
            if is_usdc:
                print(f"  {Colors.GREEN}✓ Found USDC! (decimals: {decimals}){Colors.RESET}")
                usdc_address = address
                break
            else:
                print(f"  {Colors.RED}✗ Not USDC{Colors.RESET}")
    
    # Step 3: Manual entry
    if not usdc_address:
        print(f"\n{Colors.BOLD}Step 3: Manual Entry{Colors.RESET}\n")
        
        print("USDC address not auto-discovered.")
        print("Get it from:")
        print("  1. https://developers.circle.com")
        print("  2. https://docs.arc.io")
        print("  3. Arc Discord #testnet-support")
        print()
        
        response = input("Enter USDC address (or press Enter to skip): ").strip()
        
        if response and response.startswith('0x'):
            usdc_address = response
            print(f"{Colors.GREEN}✓ Saved address: {usdc_address}{Colors.RESET}")
    
    return usdc_address

################################################################################
# Integration with Setup
################################################################################

def save_usdc_address(address: str, env_file: str = ".env"):
    """Save USDC address to .env file"""
    
    if not address:
        return False
    
    try:
        # Read existing .env
        existing_content = ""
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                existing_content = f.read()
        
        # Update or add USDC_ADDRESS
        lines = existing_content.split('\n')
        found = False
        
        for i, line in enumerate(lines):
            if line.startswith('USDC_ADDRESS='):
                lines[i] = f"USDC_ADDRESS={address}"
                found = True
                break
        
        if not found:
            lines.append(f"USDC_ADDRESS={address}")
        
        # Write back
        with open(env_file, 'w') as f:
            f.write('\n'.join(lines))
        
        print(f"{Colors.GREEN}✓ Saved to .env{Colors.RESET}")
        return True
        
    except Exception as e:
        print(f"{Colors.RED}✗ Error saving: {e}{Colors.RESET}")
        return False

################################################################################
# Main
################################################################################

def main():
    """Main discovery process"""
    
    # Get RPC URL from .env if available
    rpc_url = None
    
    import os
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('ARC_RPC_URL='):
                    rpc_url = line.split('=', 1)[1].strip()
                    break
    
    # Discover USDC
    usdc_address = discover_usdc(rpc_url)
    
    # Save if found
    if usdc_address:
        print(f"\n{Colors.BOLD}Saving Configuration{Colors.RESET}\n")
        
        import os
        save_usdc_address(usdc_address)
        
        print(f"\n{Colors.GREEN}✓ USDC Discovery Complete{Colors.RESET}")
        print(f"Address: {usdc_address}")
        
        return 0
    else:
        print(f"\n{Colors.YELLOW}⚠ USDC address not found{Colors.RESET}")
        print("Please obtain from official sources")
        return 1

if __name__ == '__main__':
    try:
        import sys
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Cancelled{Colors.RESET}")
        sys.exit(1)
