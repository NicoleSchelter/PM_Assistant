#!/usr/bin/env python3
"""
Minimal Streamlit test to debug processor issues.
"""

import sys
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

import streamlit as st

st.title("PM Assistant Debug Test")

try:
    st.write("Testing processor imports...")
    
    # Test processor imports
    from service.processors.status_analysis import StatusAnalysisProcessor
    st.success("✓ StatusAnalysisProcessor imported")
    
    # Test engine import
    from logic.orchestration.engine import PMAnalysisEngine
    st.success("✓ PMAnalysisEngine imported")
    
    # Test engine creation
    if st.button("Test Engine Creation"):
        with st.spinner("Creating engine..."):
            try:
                engine = PMAnalysisEngine()
                st.success(f"✓ Engine created with {len(engine.processors)} processors")
                
                # Test specific processor access
                from logic.models.models import OperationMode
                processor = engine.processors.get(OperationMode.STATUS_ANALYSIS)
                if processor:
                    st.success("✓ StatusAnalysisProcessor found in engine")
                else:
                    st.error("❌ StatusAnalysisProcessor NOT found in engine")
                    st.write(f"Available: {list(engine.processors.keys())}")
                    
            except Exception as e:
                st.error(f"❌ Engine creation failed: {e}")
                st.exception(e)
    
except Exception as e:
    st.error(f"❌ Import failed: {e}")
    st.exception(e)