#!/usr/bin/env python3
"""
Test script to verify configuration fixes.
"""

import sys
import os
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_config():
    """Test that configuration no longer contains 'console' output format."""
    try:
        # Import config manager
        from logic.orchestration.config_manager import ConfigManager
        
        # Create config manager
        cm = ConfigManager()
        
        # Load config
        config = cm.load_config()
        
        # Check document check output formats
        doc_check_formats = config['modes']['document_check']['output_formats']
        print(f"Document check output formats: {doc_check_formats}")
        
        # Check if 'console' is in the formats
        if 'console' in doc_check_formats:
            print("ERROR: 'console' format still found in document_check output_formats")
            return False
        else:
            print("SUCCESS: 'console' format correctly removed from document_check output_formats")
            
        # Check status analysis output formats
        status_formats = config['modes']['status_analysis']['output_formats']
        print(f"Status analysis output formats: {status_formats}")
        
        # Check if 'console' is in the formats
        if 'console' in status_formats:
            print("ERROR: 'console' format still found in status_analysis output_formats")
            return False
        else:
            print("SUCCESS: 'console' format correctly removed from status_analysis output_formats")
            
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    print("Testing configuration fixes...")
    success = test_config()
    if success:
        print("\nAll tests passed!")
        sys.exit(0)
    else:
        print("\nSome tests failed!")
        sys.exit(1)