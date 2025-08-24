#!/usr/bin/env python3
"""Simple test for new file format support."""

import sys
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

print("Testing new file format support...")

try:
    from data.extractors.risk_extractor import RiskExtractor
    re = RiskExtractor()
    print(f"Risk extractor has DOCX handler: {hasattr(re, 'docx_handler')}")
    print(f"Risk extractor has MPP handler: {hasattr(re, 'mpp_handler')}")
    
    if hasattr(re, 'docx_handler'):
        print(f"DOCX handler can handle .docx files: {re.docx_handler.can_handle('test.docx')}")
    
    if hasattr(re, 'mpp_handler'):
        print(f"MPP handler can handle .mpp files: {re.mpp_handler.can_handle('test.mpp')}")
    
    print("✓ Risk extractor test passed")
except Exception as e:
    print(f"❌ Risk extractor test failed: {e}")

try:
    from file_handlers.docx_handler import DocxHandler
    dh = DocxHandler()
    print(f"✓ DOCX handler imported successfully")
    print(f"  Can handle .docx: {dh.can_handle('test.docx')}")
    print(f"  Supported extensions: {dh.supported_extensions}")
except Exception as e:
    print(f"❌ DOCX handler test failed: {e}")

print("Test complete!")