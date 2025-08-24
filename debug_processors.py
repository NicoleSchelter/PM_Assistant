#!/usr/bin/env python3
"""
Debug script to test processor imports and initialization.
"""

import sys
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    print("Testing processor imports...")
    
    # Test individual processor imports
    from service.processors.document_check import DocumentCheckProcessor
    print("✓ DocumentCheckProcessor imported successfully")
    
    from service.processors.status_analysis import StatusAnalysisProcessor  
    print("✓ StatusAnalysisProcessor imported successfully")
    
    from service.processors.learning_module import LearningModuleProcessor
    print("✓ LearningModuleProcessor imported successfully")
    
    # Test processor initialization
    print("\nTesting processor initialization...")
    
    doc_processor = DocumentCheckProcessor()
    print("✓ DocumentCheckProcessor initialized successfully")
    
    status_processor = StatusAnalysisProcessor()
    print("✓ StatusAnalysisProcessor initialized successfully") 
    
    learning_processor = LearningModuleProcessor()
    print("✓ LearningModuleProcessor initialized successfully")
    
    # Test engine creation
    print("\nTesting engine creation...")
    from logic.orchestration.engine import PMAnalysisEngine
    
    engine = PMAnalysisEngine()
    print(f"✓ Engine created successfully with {len(engine.processors)} processors")
    
    # Test engine processor access
    from logic.models.models import OperationMode
    status_processor = engine.processors.get(OperationMode.STATUS_ANALYSIS)
    if status_processor:
        print("✓ StatusAnalysisProcessor found in engine")
    else:
        print("❌ StatusAnalysisProcessor NOT found in engine")
        print(f"Available processors: {list(engine.processors.keys())}")
    
    print("\n🎉 All processors working correctly!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()