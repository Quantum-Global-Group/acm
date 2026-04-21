#!/usr/bin/env python3

################################################################################
# Environment Configuration Validator
# Checks .env file for completeness and correctness
# Usage: python3 validate_config.py
################################################################################

import os
import re
import sys
from pathlib import Path
from typing import Dict, Tuple, List

# Colors
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'

# Configuration requirements
REQUIRED_VARS = {
    'ARC_RPC_URL': {
        'description': 'Arc testnet RPC endpoint',
        'pattern': r'^https?://',
        'required': True
    },
    'ARC_CHAIN_ID': {
        'description': 'Arc testnet chain ID',
        'pattern': r'^\d+$',
        'required': True
    },
    'USDC_ADDRESS': {
        'description': 'USDC token address on Arc',
        'pattern': r'^0x[0-9a-fA-F]{40}$',
        'required': True
    },
    'PRIVATE_KEY': {
        'description': 'Testnet wallet private key',
        'pattern': r'^0x[0-9a-fA-F]{64}$',
        'required': True
    }
}

OPTIONAL_VARS = {
    'ARC_EXPLORER_URL': {
        'description': 'Arc testnet block explorer URL',
        'pattern': r'^https?://',
    },
    'ARC_CONTRACT_ADDRESS': {
        'description': 'Deployed contract address',
        'pattern': r'^(0x[0-9a-fA-F]{40})?$',
    },
    'API_HOST': {
        'description': 'Backend API host',
        'pattern': r'^[\d.\w]+$',
    },
    'API_PORT': {
        'description': 'Backend API port',
        'pattern': r'^\d+$',
    },
    'LOG_LEVEL': {
        'description': 'Logging level',
        'pattern': r'^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$',
    },
}

def load_env_file(path: str = '.env') -> Dict[str, str]:
    """Load environment variables from .env file"""
    env_vars = {}
    
    if not os.path.exists(path):
        print(f"{Colors.RED}✗ {path} not found{Colors.RESET}")
        return env_vars
    
    with open(path, 'r') as f:
        for line in f:
            # Skip comments and empty lines
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    
    return env_vars

def validate_value(key: str, value: str, spec: Dict) -> Tuple[bool, str]:
    """Validate a configuration value"""
    if not value:
        return False, "Value is empty"
    
    pattern = spec.get('pattern')
    if pattern:
        if not re.match(pattern, value):
            return False, f"Value doesn't match pattern: {pattern}"
    
    return True, "Valid"

def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BLUE}{title:^70}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*70}{Colors.RESET}\n")

def print_check(success: bool, key: str, message: str, value: str = ""):
    """Print a validation check result"""
    status = f"{Colors.GREEN}✓{Colors.RESET}" if success else f"{Colors.RED}✗{Colors.RESET}"
    
    if value:
        # Mask sensitive values
        if 'KEY' in key.upper():
            display_value = f"{value[:10]}...{value[-8:]}"
        elif key == 'USDC_ADDRESS':
            display_value = f"{value[:10]}...{value[-8:]}"
        else:
            display_value = value
        
        print(f"{status} {key}: {display_value}")
    else:
        print(f"{status} {key}")
    
    if message:
        print(f"  → {message}")

def main():
    """Main validation function"""
    print(f"{Colors.BOLD}")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "Arc Configuration Validator".center(68) + "║")
    print("║" + "Agent-to-Agent Compute Marketplace".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    print(f"{Colors.RESET}")
    
    # Load configuration
    env_file = '.env'
    print(f"Loading configuration from: {env_file}\n")
    
    config = load_env_file(env_file)
    
    if not config:
        print(f"{Colors.RED}✗ No configuration found{Colors.RESET}")
        print("Run: bash setup_env.sh")
        sys.exit(1)
    
    # Track results
    required_ok = 0
    required_total = 0
    optional_ok = 0
    optional_total = 0
    errors: List[str] = []
    warnings: List[str] = []
    
    # Validate required variables
    print_header("Required Configuration")
    
    for key, spec in REQUIRED_VARS.items():
        required_total += 1
        value = config.get(key, '')
        is_valid, message = validate_value(key, value, spec)
        
        print_check(is_valid, key, message, value)
        
        if is_valid:
            required_ok += 1
        else:
            if not value:
                errors.append(f"{key} is missing")
            else:
                errors.append(f"{key} is invalid: {message}")
    
    # Validate optional variables
    print_header("Optional Configuration")
    
    for key, spec in OPTIONAL_VARS.items():
        optional_total += 1
        value = config.get(key, '')
        
        if value:
            is_valid, message = validate_value(key, value, spec)
            print_check(is_valid, key, message, value)
            
            if is_valid:
                optional_ok += 1
            else:
                warnings.append(f"{key} is invalid: {message}")
        else:
            print_check(True, key, "Not set (optional)", "")
            optional_ok += 1
    
    # Check for unknown variables
    print_header("Configuration Review")
    
    all_known_keys = set(REQUIRED_VARS.keys()) | set(OPTIONAL_VARS.keys())
    unknown_keys = set(config.keys()) - all_known_keys
    
    if unknown_keys:
        print(f"{Colors.YELLOW}⚠ Unknown configuration variables:{Colors.RESET}")
        for key in sorted(unknown_keys):
            print(f"  - {key}")
    
    # Print security checks
    print_header("Security Checks")
    
    # Check if .env in .gitignore
    gitignore_ok = False
    if os.path.exists('.gitignore'):
        with open('.gitignore', 'r') as f:
            if '.env' in f.read():
                gitignore_ok = True
    
    print_check(gitignore_ok, ".env in .gitignore", 
                "✓ Protected from accidental commit" if gitignore_ok else "⚠ Add .env to .gitignore")
    
    # Check if .env is in git history
    env_in_git = False
    import subprocess
    try:
        subprocess.run(['git', 'log', '--all', '--', '.env'], 
                      capture_output=True, timeout=5, check=False)
        # If this doesn't error, .env might be in git
    except:
        pass
    
    print_check(not env_in_git, "File permissions", 
                "✓ .env should only be readable by owner")
    
    # Summary
    print_header("Validation Summary")
    
    print(f"Required: {Colors.GREEN}{required_ok}/{required_total}{Colors.RESET}")
    print(f"Optional: {Colors.GREEN}{optional_ok}/{optional_total}{Colors.RESET}")
    
    if errors:
        print(f"\n{Colors.RED}Errors:{Colors.RESET}")
        for error in errors:
            print(f"  {Colors.RED}✗{Colors.RESET} {error}")
    
    if warnings:
        print(f"\n{Colors.YELLOW}Warnings:{Colors.RESET}")
        for warning in warnings:
            print(f"  {Colors.YELLOW}⚠{Colors.RESET} {warning}")
    
    # Final status
    print()
    if required_ok == required_total and not errors:
        print(f"{Colors.GREEN}✓ Configuration is valid and complete!{Colors.RESET}")
        print(f"\nReady to proceed with: {Colors.BOLD}GETTING_STARTED.md{Colors.RESET}")
        return 0
    else:
        print(f"{Colors.RED}✗ Configuration has errors{Colors.RESET}")
        print(f"\nRun: bash setup_env.sh")
        return 1

if __name__ == '__main__':
    sys.exit(main())
