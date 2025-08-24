#!/usr/bin/env python3
"""
Test script to verify new file format support (.docx, .mpp, .xlsx).
"""

import sys
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_file_handlers():
    """Test all file handlers for new format support."""
    
    print("=== Testing File Handler Support ===")
    
    # Test DOCX handler
    try:
        from file_handlers.docx_handler import DocxHandler
        docx_handler = DocxHandler()
        print(f"✓ DOCX Handler: {docx_handler.handler_name}")
        print(f"  - Supported extensions: {docx_handler.supported_extensions}")
        print(f"  - Can handle test.docx: {docx_handler.can_handle('test.docx')}")
    except Exception as e:
        print(f"❌ DOCX Handler failed: {e}")
    
    # Test MPP handler
    try:
        from file_handlers.mpp_handler import MPPHandler
        mpp_handler = MPPHandler()
        print(f"✓ MPP Handler: {mpp_handler.handler_name}")
        print(f"  - Supported extensions: {mpp_handler.supported_extensions}")
        print(f"  - Can handle test.mpp: {mpp_handler.can_handle('test.mpp')}")
    except Exception as e:
        print(f"❌ MPP Handler failed: {e}")
    
    # Test Excel handler (should already work)
    try:
        from file_handlers.excel_handler import ExcelHandler
        excel_handler = ExcelHandler()
        print(f"✓ Excel Handler: {excel_handler.handler_name}")
        print(f"  - Supported extensions: {excel_handler.supported_extensions}")
        print(f"  - Can handle test.xlsx: {excel_handler.can_handle('test.xlsx')}")
    except Exception as e:
        print(f"❌ Excel Handler failed: {e}")

def test_extractors():
    """Test all extractors for new format support."""
    
    print("\n=== Testing Extractor Support ===")
    
    extractors = [
        ("Risk Extractor", "data.extractors.risk_extractor", "RiskExtractor"),
        ("Deliverable Extractor", "data.extractors.deliverable_extractor", "DeliverableExtractor"),
        ("Milestone Extractor", "data.extractors.milestone_extractor", "MilestoneExtractor"),
        ("Stakeholder Extractor", "data.extractors.stakeholder_extractor", "StakeholderExtractor"),
    ]
    
    for name, module_path, class_name in extractors:
        try:
            module = __import__(module_path, fromlist=[class_name])
            extractor_class = getattr(module, class_name)
            extractor = extractor_class()
            
            print(f"✓ {name}: Initialized successfully")
            
            # Test if it has the new handlers
            if hasattr(extractor, 'docx_handler'):
                print(f"  - DOCX support: {extractor.docx_handler.can_handle('test.docx')}")
            
            if hasattr(extractor, 'mpp_handler'):
                print(f"  - MPP support: {extractor.mpp_handler.can_handle('test.mpp')}")
            
            if hasattr(extractor, 'excel_handler'):
                print(f"  - Excel support: {extractor.excel_handler.can_handle('test.xlsx')}")
                
        except Exception as e:
            print(f"❌ {name} failed: {e}")

def test_engine():
    """Test the engine with new format support."""
    
    print("\n=== Testing Engine ===")
    
    try:
        from logic.orchestration.engine import PMAnalysisEngine
        engine = PMAnalysisEngine()
        
        print(f"✓ Engine initialized with {len(engine.processors)} processors")
        
        # Check if engine can handle different file formats
        test_files = ["test.docx", "test.mpp", "test.xlsx", "test.md", "test.pdf"]
        
        from logic.orchestration.file_scanner import FileScanner
        file_scanner = FileScanner()
        
        for file_name in test_files:
            can_handle = any(
                handler.can_handle(file_name) 
                for processor in engine.processors.values()
                for handler in getattr(processor, 'handlers', [])
                if hasattr(handler, 'can_handle')
            )
            print(f"  - {file_name}: {'✓' if can_handle else '❌'}")
            
    except Exception as e:
        print(f"❌ Engine test failed: {e}")

if __name__ == "__main__":
    test_file_handlers()
    test_extractors() 
    test_engine()
    print("\n=== Test Complete ===")