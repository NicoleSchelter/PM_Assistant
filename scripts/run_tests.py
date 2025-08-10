#!/usr/bin/env python3
"""
Comprehensive test runner for PM Analysis Tool.

This script provides different test execution modes:
- Unit tests only
- Integration tests only
- Performance tests only
- All tests
- Coverage reporting
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


def run_pytest(
    test_path: Optional[str] = None,
    markers: Optional[str] = None,
    coverage: bool = False,
    verbose: bool = False,
    parallel: bool = False,
) -> bool:
    """
    Run pytest with specified options.

    Args:
        test_path: Specific test path to run
        markers: Pytest markers to filter tests
        coverage: Whether to run with coverage
        verbose: Whether to run in verbose mode
        parallel: Whether to run tests in parallel

    Returns:
        True if tests passed, False otherwise
    """
    command = ["python", "-m", "pytest"]

    if test_path:
        command.append(test_path)

    if markers:
        command.extend(["-m", markers])

    if coverage:
        command.extend(
            [
                "--cov=core",
                "--cov=utils",
                "--cov=processors",
                "--cov=extractors",
                "--cov=file_handlers",
                "--cov=reporters",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov",
                "--cov-fail-under=80",
            ]
        )

    if verbose:
        command.append("-v")
    else:
        command.append("-q")

    if parallel:
        command.extend(["-n", "auto"])

    # Add other useful options
    command.extend(["--tb=short", "--strict-markers", "--disable-warnings"])

    print(f"Running: {' '.join(command)}")

    try:
        result = subprocess.run(command, cwd=Path(__file__).parent.parent)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running tests: {e}")
        return False


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="PM Analysis Tool Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_tests.py --unit                    # Run unit tests only
  python scripts/run_tests.py --integration             # Run integration tests only
  python scripts/run_tests.py --performance             # Run performance tests only
  python scripts/run_tests.py --all --coverage          # Run all tests with coverage
  python scripts/run_tests.py --fast                    # Run fast tests only
  python scripts/run_tests.py --file tests/test_engine.py  # Run specific test file
        """,
    )

    # Test selection options
    test_group = parser.add_mutually_exclusive_group()
    test_group.add_argument(
        "--unit",
        action="store_true",
        help="Run unit tests only (excludes integration and performance tests)",
    )
    test_group.add_argument("--integration", action="store_true", help="Run integration tests only")
    test_group.add_argument(
        "--performance", action="store_true", help="Run performance tests only (marked as slow)"
    )
    test_group.add_argument(
        "--fast", action="store_true", help="Run fast tests only (excludes slow/performance tests)"
    )
    test_group.add_argument(
        "--all", action="store_true", help="Run all tests including performance tests"
    )
    test_group.add_argument("--file", type=str, help="Run specific test file")

    # Test execution options
    parser.add_argument("--coverage", action="store_true", help="Run with coverage reporting")
    parser.add_argument("--verbose", "-v", action="store_true", help="Run in verbose mode")
    parser.add_argument(
        "--parallel",
        "-p",
        action="store_true",
        help="Run tests in parallel (requires pytest-xdist)",
    )

    args = parser.parse_args()

    # Default to fast tests if no option specified
    if not any([args.unit, args.integration, args.performance, args.fast, args.all, args.file]):
        args.fast = True

    print("🧪 PM Analysis Tool - Test Runner")
    print("=" * 60)

    # Determine test parameters
    test_path = None
    markers = None

    if args.file:
        test_path = args.file
        print(f"Running specific test file: {test_path}")
    elif args.unit:
        markers = "not integration and not slow"
        print("Running unit tests only...")
    elif args.integration:
        markers = "integration"
        print("Running integration tests only...")
    elif args.performance:
        markers = "slow"
        print("Running performance tests only...")
    elif args.fast:
        markers = "not slow"
        print("Running fast tests only...")
    elif args.all:
        print("Running all tests...")

    # Run tests
    success = run_pytest(
        test_path=test_path,
        markers=markers,
        coverage=args.coverage,
        verbose=args.verbose,
        parallel=args.parallel,
    )

    # Print summary
    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
