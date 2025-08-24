#!/usr/bin/env python3
"""
Debug script to test PM analysis execution and identify where failures occur.
"""

import sys
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from logic.orchestration.engine import PMAnalysisEngine
from logic.models.models import ProcessingResult


def debug_analysis():
    """Test analysis execution with debug output."""
    
    print("=== PM Analysis Debug ===")
    
    try:
        # Create engine
        print("1. Creating engine...")
        engine = PMAnalysisEngine()
        print(f"✓ Engine created with {len(engine.processors)} processors")
        
        # Check project path
        project_path = "uploaded_project"
        print(f"2. Analyzing project path: {project_path}")
        
        if not Path(project_path).exists():
            print(f"⚠️ Project path does not exist: {project_path}")
            return
            
        # Run analysis
        print("3. Running analysis...")
        result: ProcessingResult = engine.run(
            mode="status-analysis",
            project_path=project_path,
            output_formats=["markdown"]
        )
        
        print(f"4. Analysis completed:")
        print(f"   Success: {result.success}")
        print(f"   Operation: {result.operation}")
        print(f"   Processing time: {result.processing_time_seconds:.2f}s")
        
        if result.errors:
            print(f"   Errors ({len(result.errors)}):")
            for i, error in enumerate(result.errors):
                print(f"     {i+1}. {error}")
        
        if result.warnings:
            print(f"   Warnings ({len(result.warnings)}):")
            for i, warning in enumerate(result.warnings):
                print(f"     {i+1}. {warning}")
        
        if result.data:
            print(f"   Data keys: {list(result.data.keys())}")
        
        # Check for report files
        reports_dir = Path("reports")
        if reports_dir.exists():
            report_files = list(reports_dir.glob("*"))
            print(f"5. Report files in reports/ directory: {len(report_files)}")
            for report_file in sorted(report_files)[-3:]:  # Show last 3
                print(f"   - {report_file.name}")
        else:
            print("5. No reports/ directory found")
            
        # Check for output files
        outputs_dir = Path("outputs")
        if outputs_dir.exists():
            output_files = list(outputs_dir.glob("*"))
            print(f"6. Output files in outputs/ directory: {len(output_files)}")
            for output_file in output_files:
                print(f"   - {output_file.name}")
        else:
            print("6. No outputs/ directory found")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_analysis()