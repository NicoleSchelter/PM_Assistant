#!/usr/bin/env python3
"""
Code quality check script for PM Analysis Tool.

This script runs various code quality tools including:
- Black (code formatting)
- Flake8 (linting)
- isort (import sorting)
- mypy (type checking)
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


def run_command(command: List[str], description: str) -> Tuple[bool, str]:
    """
    Run a command and return success status and output.

    Args:
        command: Command to run as list of strings
        description: Description of what the command does

    Returns:
        Tuple of (success, output)
    """
    print(f"\n{'='*60}")
    print(f"Running {description}...")
    print(f"Command: {' '.join(command)}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            command, capture_output=True, text=True, cwd=Path(__file__).parent.parent
        )

        if result.stdout:
            print("STDOUT:")
            print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        success = result.returncode == 0
        print(f"\n{description}: {'✅ PASSED' if success else '❌ FAILED'}")

        return success, result.stdout + result.stderr

    except FileNotFoundError:
        error_msg = f"Command not found: {command[0]}"
        print(f"❌ ERROR: {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Error running {description}: {str(e)}"
        print(f"❌ ERROR: {error_msg}")
        return False, error_msg


def main():
    """Run all code quality checks."""
    print("🔍 PM Analysis Tool - Code Quality Check")
    print("=" * 60)

    # Define quality checks
    checks = [
        {
            "command": ["python", "-m", "black", "--check", "--diff", "."],
            "description": "Black code formatting check",
            "required": True,
        },
        {
            "command": ["python", "-m", "flake8", "."],
            "description": "Flake8 linting",
            "required": True,
        },
        {
            "command": ["python", "-m", "isort", "--check-only", "--diff", "."],
            "description": "isort import sorting check",
            "required": False,
        },
        {
            "command": [
                "python",
                "-m",
                "mypy",
                "core",
                "utils",
                "processors",
                "extractors",
                "file_handlers",
                "reporters",
            ],
            "description": "MyPy type checking",
            "required": False,
        },
    ]

    results = []

    # Run each check
    for check in checks:
        success, output = run_command(check["command"], check["description"])
        results.append(
            {
                "name": check["description"],
                "success": success,
                "required": check["required"],
                "output": output,
            }
        )

    # Summary
    print(f"\n{'='*60}")
    print("📊 SUMMARY")
    print(f"{'='*60}")

    passed = 0
    failed = 0
    warnings = 0

    for result in results:
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        requirement = "REQUIRED" if result["required"] else "OPTIONAL"
        print(f"{result['name']}: {status} ({requirement})")

        if result["success"]:
            passed += 1
        elif result["required"]:
            failed += 1
        else:
            warnings += 1

    print(f"\nResults: {passed} passed, {failed} failed, {warnings} warnings")

    # Exit with appropriate code
    if failed > 0:
        print("\n❌ Some required quality checks failed!")
        sys.exit(1)
    elif warnings > 0:
        print("\n⚠️  All required checks passed, but some optional checks failed.")
        sys.exit(0)
    else:
        print("\n✅ All quality checks passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
