#!/usr/bin/env python3
"""
Code formatting script for PM Analysis Tool.

This script automatically formats code using:
- Black (code formatting)
- isort (import sorting)
"""

import subprocess
import sys
from pathlib import Path
from typing import List


def run_formatter(command: List[str], description: str) -> bool:
    """
    Run a formatting command.

    Args:
        command: Command to run as list of strings
        description: Description of what the command does

    Returns:
        True if successful, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"Running {description}...")
    print(f"Command: {' '.join(command)}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(command, cwd=Path(__file__).parent.parent, text=True)

        success = result.returncode == 0
        print(f"{description}: {'✅ COMPLETED' if success else '❌ FAILED'}")

        return success

    except FileNotFoundError:
        print(f"❌ ERROR: Command not found: {command[0]}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


def main():
    """Run all code formatters."""
    print("🎨 PM Analysis Tool - Code Formatting")
    print("=" * 60)

    # Define formatters
    formatters = [
        {"command": ["python", "-m", "black", "."], "description": "Black code formatting"},
        {"command": ["python", "-m", "isort", "."], "description": "isort import sorting"},
    ]

    success_count = 0

    # Run each formatter
    for formatter in formatters:
        if run_formatter(formatter["command"], formatter["description"]):
            success_count += 1

    # Summary
    print(f"\n{'='*60}")
    print("📊 FORMATTING SUMMARY")
    print(f"{'='*60}")

    total = len(formatters)
    print(f"Completed: {success_count}/{total} formatters")

    if success_count == total:
        print("\n✅ All code formatting completed successfully!")
        sys.exit(0)
    else:
        print(f"\n❌ {total - success_count} formatters failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
