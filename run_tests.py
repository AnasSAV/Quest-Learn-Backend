#!/usr/bin/env python3
"""
Test runner script for the Math Buddy Backend.
This script provides different ways to run the test suite.
"""

import sys
import subprocess
import argparse


def run_tests(test_type="all", verbose=False):
    """Run tests with different configurations."""
    
    base_cmd = ["python", "-m", "pytest"]
    
    if verbose:
        base_cmd.append("-v")
    
    if test_type == "unit":
        base_cmd.extend(["-m", "not integration and not slow"])
    elif test_type == "integration":
        base_cmd.extend(["-m", "integration"])
    elif test_type == "database":
        base_cmd.extend(["-m", "database"])
    elif test_type == "auth":
        base_cmd.extend(["-m", "auth"])
    elif test_type == "fast":
        base_cmd.extend(["-m", "not slow"])
    elif test_type == "all":
        pass  # Run all tests
    
    print(f"Running command: {' '.join(base_cmd)}")
    
    try:
        result = subprocess.run(base_cmd, check=False)
        return result.returncode
    except FileNotFoundError:
        print("Error: pytest not found. Please install it with: pip install pytest")
        return 1


def main():
    parser = argparse.ArgumentParser(description="Run Math Buddy Backend tests")
    parser.add_argument(
        "--type", 
        choices=["all", "unit", "integration", "database", "auth", "fast"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--install",
        action="store_true", 
        help="Install test dependencies first"
    )
    
    args = parser.parse_args()
    
    if args.install:
        print("Installing test dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    return run_tests(args.type, args.verbose)


if __name__ == "__main__":
    sys.exit(main())
