#!/usr/bin/env python3
"""
PM Analysis Tool - Main Entry Point

This is the main entry point that delegates to the CLI interface in the UI layer.
This maintains backward compatibility while following the new 4-layer architecture.
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import and run the CLI main function
from ui.cli.main import cli

if __name__ == "__main__":
    cli()