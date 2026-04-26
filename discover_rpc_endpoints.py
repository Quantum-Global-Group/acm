#!/usr/bin/env python3

################################################################################
# RPC Endpoint Discovery & Performance Testing
# Discovers Arc testnet RPC endpoints and ranks by performance
# Usage: python3 discover_rpc_endpoints.py
################################################################################

import requests
import time
import statistics
from typing import List, Tuple, Dict
from dataclasses import dataclass
import concurrent.futures

class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'

@dataclass
class RPCEndpoint:
    """RPC endpoint information"""
    url: str
    is_working: bool = False
    latency_ms: float = 0.0
    chain_id: int = 0
    block_number: int = 0
    provider: str = ""
    
    def __str__(self) -> str:
        status = f"{Colors.GREEN}✓{Colors.RESET}" if self.is_working else f"{Colors.RED}✗{Colors.RESET}"
        return f"{status} {self.url} ({self.latency_ms:.0f}ms) Chain {self.chain_id} Block {self.block_number}"

# Known RPC endpoints to test (official Arc testnet + provider-backed + aggregators)
ENDPOINTS_TO_TEST = [
    ("https://rpc.testnet.arc.network", "Arc primary (official)"),
    ("https://rpc.blockdaemon.testnet.arc.network", "Blockdaemon"),
    ("https://rpc.drpc.testnet.arc.network", "dRPC (Arc)"),
    ("https://rpc.quicknode.testnet.arc.network", "QuickNode"),
    ("https://arc-testnet.drpc.org", "dRPC public"),
    ("https://5042002.rpc.thirdweb.com", "thirdweb"),
]

# Legacy / deprecated placeholders (kept for diagnostics only)
ADDITIONAL_ENDPOINTS = [
    "https://arc-testnet-rpc.io",
    "https://rpc.arc-testnet.io",
    "https://testnet-rpc.arc.io",
]

################################################################################
# RPC Testing Functions
################################################################################

def test_rpc_latency(rpc_url: str, num_tests: int = 3) -> Tuple[bool, float, int, int]:
    """
    Test RPC endpoint latency and functionality
    
    Returns:
        Tuple of (is_working, avg_latency_ms, chain_id, block_number)
    """
    latencies = []
    chain_id = 0
    block_number = 0
    
    for i in range(num_tests):
        try:
            start = time.time()
            
            response = requests.post(
                rpc_url,
                json={
                    "jsonrpc": "2.0",
                    "method": "eth_chainId",
                    "params": [],
                    "id": 1
                },
                timeout=10
            )
            
            latency_ms = (time.time() - start) * 1000
            latencies.append(latency_ms)
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    chain_id = int(data['result'], 16)
                    break  # Success on first try
        except:
            if i == num_tests - 1:
                return False, 0, 0, 0
    
    if not latencies:
        return False, 0, 0, 0
    
    # Get block number
    try:
        response = requests.post(
            rpc_url,
            json={
                "jsonrpc": "2.0",
                "method": "eth_blockNumber",
                "params": [],
                "id": 1
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "result" in data:
                block_number = int(data['result'], 16)
    except:
        pass
    
    avg_latency = statistics.mean(latencies)
    return True, avg_latency, chain_id, block_number

def test_rpc_methods(rpc_url: str) -> Dict[str, bool]:
    """
    Test various RPC methods to ensure full compatibility
    
    Returns:
        Dictionary of method: is_supported
    """
    methods = {
        'eth_chainId': False,
        'eth_blockNumber': False,
        'eth_getBalance': False,
        'eth_call': False,
        'eth_gasPrice': False,
    }
    
    for method in methods.keys():
        try:
            response = requests.post(
                rpc_url,
                json={
                    "jsonrpc": "2.0",
                    "method": method,
                    "params": [],
                    "id": 1
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                # Method is supported if we got a result or error (not "method not found")
                if "result" in data or ("error" in data and "not found" not in str(data['error']).lower()):
                    methods[method] = True
        except:
            pass
    
    return methods

################################################################################
# Endpoint Discovery
################################################################################

def discover_endpoints() -> List[RPCEndpoint]:
    """
    Discover and test all known Arc testnet RPC endpoints
    
    Returns:
        List of tested endpoints, sorted by performance
    """
    print(f"\n{Colors.BOLD}Discovering RPC Endpoints...{Colors.RESET}\n")
    
    endpoints_to_test = list(ENDPOINTS_TO_TEST)
    
    results: List[RPCEndpoint] = []
    
    # Test known endpoints
    for url, provider in endpoints_to_test:
        print(f"Testing: {url}")
        
        is_working, latency, chain_id, block_number = test_rpc_latency(url)
        
        endpoint = RPCEndpoint(
            url=url,
            is_working=is_working,
            latency_ms=latency,
            chain_id=chain_id,
            block_number=block_number,
            provider=provider
        )
        
        if is_working:
            print(f"  {Colors.GREEN}✓ Working ({latency:.0f}ms){Colors.RESET}")
        else:
            print(f"  {Colors.RED}✗ Not responding{Colors.RESET}")
        
        results.append(endpoint)
    
    # Test additional endpoints
    print(f"\n{Colors.CYAN}Testing additional endpoints...{Colors.RESET}\n")
    
    for url in ADDITIONAL_ENDPOINTS:
        print(f"Testing: {url}")
        
        is_working, latency, chain_id, block_number = test_rpc_latency(url)
        
        if is_working:
            print(f"  {Colors.GREEN}✓ Working ({latency:.0f}ms){Colors.RESET}")
            
            endpoint = RPCEndpoint(
                url=url,
                is_working=is_working,
                latency_ms=latency,
                chain_id=chain_id,
                block_number=block_number,
                provider="Community"
            )
            results.append(endpoint)
        else:
            print(f"  {Colors.RED}✗ Not responding{Colors.RESET}")
    
    # Sort by latency (working endpoints first)
    working = sorted([e for e in results if e.is_working], key=lambda e: e.latency_ms)
    not_working = [e for e in results if not e.is_working]
    
    return working + not_working

################################################################################
# Endpoint Analysis
################################################################################

def analyze_endpoints(endpoints: List[RPCEndpoint]) -> Dict:
    """Analyze endpoint performance"""
    
    working = [e for e in endpoints if e.is_working]
    
    if not working:
        return {
            'total_tested': len(endpoints),
            'working_count': 0,
            'best_endpoint': None,
            'avg_latency': 0,
            'min_latency': 0,
            'max_latency': 0,
        }
    
    latencies = [e.latency_ms for e in working]
    
    return {
        'total_tested': len(endpoints),
        'working_count': len(working),
        'best_endpoint': working[0],
        'avg_latency': statistics.mean(latencies),
        'min_latency': min(latencies),
        'max_latency': max(latencies),
        'all_working': working,
    }

def test_endpoint_features(endpoint: RPCEndpoint) -> Dict[str, bool]:
    """Test specific features of an endpoint"""
    
    if not endpoint.is_working:
        return {}
    
    print(f"\nTesting features of: {endpoint.url}")
    
    features = test_rpc_methods(endpoint.url)
    
    for method, supported in features.items():
        status = f"{Colors.GREEN}✓{Colors.RESET}" if supported else f"{Colors.RED}✗{Colors.RESET}"
        print(f"  {status} {method}")
    
    return features

################################################################################
# Main
################################################################################

def main():
    """Main discovery process"""
    
    print(f"\n{Colors.BOLD}")
    print("╔" + "="*70 + "╗")
    print("║" + " "*70 + "║")
    print("║" + "Arc RPC Endpoint Discovery".center(70) + "║")
    print("║" + "Find and test available RPC endpoints".center(70) + "║")
    print("║" + " "*70 + "║")
    print("╚" + "="*70 + "╝")
    print(f"{Colors.RESET}")
    
    # Discover endpoints
    endpoints = discover_endpoints()
    
    # Analyze results
    analysis = analyze_endpoints(endpoints)
    
    # Print summary
    print(f"\n{Colors.BOLD}Summary{Colors.RESET}\n")
    print(f"Total tested: {analysis['total_tested']}")
    print(f"Working: {analysis['working_count']}")
    
    if analysis['working_count'] > 0:
        print(f"\n{Colors.GREEN}✓ Available Endpoints:{Colors.RESET}\n")
        
        for i, endpoint in enumerate(analysis['all_working'], 1):
            print(f"{i}. {endpoint.url}")
            print(f"   Provider: {endpoint.provider}")
            print(f"   Latency: {endpoint.latency_ms:.0f}ms")
            print(f"   Chain: {endpoint.chain_id} | Block: {endpoint.block_number}")
        
        # Test best endpoint
        print(f"\n{Colors.BOLD}Testing Best Endpoint{Colors.RESET}")
        best = analysis['best_endpoint']
        features = test_endpoint_features(best)
        
        # Recommendation
        print(f"\n{Colors.BOLD}Recommendation{Colors.RESET}\n")
        print(f"Use: {best.url}")
        print(f"Reason: Lowest latency ({best.latency_ms:.0f}ms)")
        
        print(f"\n{Colors.BOLD}Configuration{Colors.RESET}\n")
        print(f"Add to .env:")
        print(f"  ARC_RPC_URL={best.url}")
        print(f"  ARC_CHAIN_ID={best.chain_id}")
        
        # Save to .env if requested
        response = input(f"\nSave to .env? (y/n): ").strip().lower()
        if response == 'y':
            # Append to .env
            with open('.env', 'a') as f:
                f.write(f"\nARC_RPC_URL={best.url}\n")
                f.write(f"ARC_CHAIN_ID={best.chain_id}\n")
            print(f"{Colors.GREEN}✓ Saved to .env{Colors.RESET}")
    else:
        print(f"\n{Colors.RED}✗ No working endpoints found{Colors.RESET}")
        print("Try:")
        print("  1. Check your internet connection")
        print("  2. Wait a few minutes and try again")
        print("  3. Use manual setup: bash setup_env.sh")
        return 1
    
    return 0

if __name__ == '__main__':
    try:
        import sys
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Cancelled{Colors.RESET}")
        sys.exit(1)
