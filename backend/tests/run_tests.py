#!/usr/bin/env python3
"""
Test runner script for RehabConnect backend tests.
"""

import sys
import subprocess
from pathlib import Path

def run_tests(test_type="all", coverage=False, verbose=True):
    """Run the specified type of tests."""

    base_cmd = [sys.executable, "-m", "pytest"]

    if coverage:
        base_cmd.extend(["--cov=app", "--cov-report=html", "--cov-report=term"])

    if verbose:
        base_cmd.append("-v")

    if test_type == "unit":
        base_cmd.append("tests/test_models.py")
        base_cmd.append("tests/test_services.py")
        base_cmd.append("tests/test_compliance_engines.py")
        base_cmd.append("tests/test_risk_engine.py")
    elif test_type == "models":
        base_cmd.append("tests/test_models.py")
    elif test_type == "services":
        base_cmd.append("tests/test_services.py")
    elif test_type == "engines":
        base_cmd.append("tests/test_compliance_engines.py")
        base_cmd.append("tests/test_risk_engine.py")
    else:
        base_cmd.append("tests/")

    print(f"Running command: {' '.join(base_cmd)}")
    result = subprocess.run(base_cmd, cwd=Path(__file__).parent)

    return result.returncode

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Run RehabConnect backend tests")
    parser.add_argument(
        "test_type",
        choices=["all", "unit", "models", "services", "engines"],
        default="all",
        nargs="?",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce output verbosity"
    )

    args = parser.parse_args()

    return run_tests(
        test_type=args.test_type,
        coverage=args.coverage,
        verbose=not args.quiet
    )

if __name__ == "__main__":
    sys.exit(main())