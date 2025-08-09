"""
Integration tests for PMAnalysisEngine with real file system operations.

This module contains end-to-end integration tests that verify the engine
works correctly with actual files and the complete workflow.
"""

import pytest
import tempfile
import shutil
import yaml
from pathlib import Path
from datetime import datetime

from core.engine import PMAnalysisEngine
from core.models import OperationMode


class TestPMAnalysisEngineIntegration:
    """Integration tests for PMAnalysisEngine."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace with config and project files."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        
        # Create project directory
        project_path = workspace_path / "test_project"
        project_path.mkdir()
        
        # Create sample project files
        (project_path / "project_charter.md").write_text("""
# Project Charter

## Project Overview
This is a test project for the PM Analysis Tool.

## Objectives
- Test the analysis capabilities
- Validate the engine functionality

## Stakeholders
- Project Manager: John Doe
- Team Lead: Jane Smith
""")
        
        (project_path / "risk_register.md").write_text("""
# Risk Register

## High Priority Risks

### Risk 1: Technical Complexity
- **Probability**: High
- **Impact**: High
- **Mitigation**: Conduct technical spike
- **Owner**: Tech Lead

### Risk 2: Resource Availability
- **Probability**: Medium
- **Impact**: High
- **Mitigation**: Secure backup resources
- **Owner**: Project Manager
""")
        
        (project_path / "stakeholder_register.md").write_text("""
# Stakeholder Register

## Key Stakeholders

### John Doe - Project Manager
- **Role**: Project Manager
- **Influence**: High
- **Interest**: High
- **Contact**: john.doe@company.com

### Jane Smith - Team Lead
- **Role**: Technical Lead
- **Influence**: High
- **Interest**: High
- **Contact**: jane.smith@company.com
""")
        
        # Create configuration file
        config_data = {
            "project": {
                "name": "Test Integration Project",
                "default_path": str(project_path)
            },
            "required_documents": [
                {
                    "name": "Project Charter",
                    "patterns": ["*charter*"],
                    "formats": ["md", "docx"],
                    "required": True
                },
                {
                    "name": "Risk Register",
                    "patterns": ["*risk*"],
                    "formats": ["md", "xlsx"],
                    "required": True
                },
                {
                    "name": "Stakeholder Register",
                    "patterns": ["*stakeholder*"],
                    "formats": ["md", "xlsx"],
                    "required": True
                }
            ],
            "modes": {
                "document_check": {
                    "enabled": True,
                    "output_formats": ["markdown"]
                },
                "status_analysis": {
                    "enabled": True,
                    "output_formats": ["markdown"]
                },
                "learning_module": {
                    "enabled": True,
                    "content_path": "./learning/modules"
                }
            },
            "output": {
                "directory": str(workspace_path / "reports"),
                "timestamp_files": True,
                "overwrite_existing": False
            },
            "logging": {
                "level": "INFO",
                "file": "pm_analysis.log",
                "console": True
            }
        }
        
        config_path = workspace_path / "config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False)
        
        # Create reports directory
        (workspace_path / "reports").mkdir()
        
        yield {
            'workspace_path': workspace_path,
            'project_path': project_path,
            'config_path': config_path
        }
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_engine_full_workflow_with_mode_detection(self, temp_workspace):
        """Test complete engine workflow with automatic mode detection."""
        config_path = temp_workspace['config_path']
        project_path = temp_workspace['project_path']
        
        # Initialize engine with real config
        engine = PMAnalysisEngine(str(config_path))
        
        # Execute analysis without specifying mode
        result = engine.run()
        
        # Verify successful execution
        assert result.success, f"Execution failed with errors: {result.errors}"
        assert result.operation == "pm_analysis_execution"
        
        # Verify execution summary
        execution_summary = result.data["execution_summary"]
        assert execution_summary["files_discovered"] >= 3  # At least our 3 test files
        assert execution_summary["files_processed"] >= 0
        assert execution_summary["total_execution_time"] > 0
        
        # Verify mode was detected (should be status analysis with good files)
        assert "mode_analysis" in result.data
        mode_analysis = result.data["mode_analysis"]
        assert mode_analysis["recommended_mode"] in ["status_analysis", "document_check"]
        assert mode_analysis["confidence_percentage"] > 0
        
        # Verify file processing
        file_summary = result.data["file_summary"]
        assert file_summary["total_files"] >= 3
        assert file_summary["readable_files"] >= 3
        
        # Verify report generation
        assert "report_summary" in result.data
        report_summary = result.data["report_summary"]
        assert "markdown" in report_summary
        assert report_summary["markdown"]["success"] is True
    
    def test_engine_explicit_document_check_mode(self, temp_workspace):
        """Test engine with explicit document check mode."""
        config_path = temp_workspace['config_path']
        
        # Initialize engine
        engine = PMAnalysisEngine(str(config_path))
        
        # Execute with explicit document check mode
        result = engine.run(mode="document_check")
        
        # Verify successful execution
        assert result.success, f"Execution failed with errors: {result.errors}"
        
        # Verify correct mode was used
        execution_summary = result.data["execution_summary"]
        assert execution_summary["selected_mode"] == "document_check"
        
        # Verify document check specific data
        processing_data = result.data["processing_data"]
        assert "summary" in processing_data
        assert "available_documents" in processing_data
        assert "missing_documents" in processing_data
        
        # Should find our test documents
        available_docs = processing_data["available_documents"]
        assert len(available_docs) >= 3  # Our test files
    
    def test_engine_explicit_status_analysis_mode(self, temp_workspace):
        """Test engine with explicit status analysis mode."""
        config_path = temp_workspace['config_path']
        
        # Initialize engine
        engine = PMAnalysisEngine(str(config_path))
        
        # Execute with explicit status analysis mode
        result = engine.run(mode="status_analysis")
        
        # Verify successful execution
        assert result.success, f"Execution failed with errors: {result.errors}"
        
        # Verify correct mode was used
        execution_summary = result.data["execution_summary"]
        assert execution_summary["selected_mode"] == "status_analysis"
        
        # Verify status analysis specific data
        processing_data = result.data["processing_data"]
        assert "project_overview" in processing_data
        assert "risk_analysis" in processing_data
        assert "stakeholder_analysis" in processing_data
    
    def test_engine_explicit_learning_module_mode(self, temp_workspace):
        """Test engine with explicit learning module mode."""
        config_path = temp_workspace['config_path']
        
        # Initialize engine
        engine = PMAnalysisEngine(str(config_path))
        
        # Execute with explicit learning module mode
        result = engine.run(mode="learning_module")
        
        # Verify successful execution
        assert result.success, f"Execution failed with errors: {result.errors}"
        
        # Verify correct mode was used
        execution_summary = result.data["execution_summary"]
        assert execution_summary["selected_mode"] == "learning_module"
        
        # Verify learning module specific data
        processing_data = result.data["processing_data"]
        assert "learning_content" in processing_data
        assert "recommendations" in processing_data
    
    def test_engine_mode_detection_standalone(self, temp_workspace):
        """Test standalone mode detection functionality."""
        config_path = temp_workspace['config_path']
        project_path = temp_workspace['project_path']
        
        # Initialize engine
        engine = PMAnalysisEngine(str(config_path))
        
        # Test mode detection without execution
        recommendation = engine.detect_optimal_mode(str(project_path))
        
        # Verify recommendation structure
        assert recommendation.recommended_mode in [
            OperationMode.DOCUMENT_CHECK,
            OperationMode.STATUS_ANALYSIS,
            OperationMode.LEARNING_MODULE
        ]
        assert 0 <= recommendation.confidence_score <= 1
        assert len(recommendation.reasoning) > 0
        assert isinstance(recommendation.available_documents, list)
        assert isinstance(recommendation.missing_documents, list)
        assert isinstance(recommendation.alternative_modes, list)
    
    def test_engine_get_available_files(self, temp_workspace):
        """Test getting available files without processing."""
        config_path = temp_workspace['config_path']
        project_path = temp_workspace['project_path']
        
        # Initialize engine
        engine = PMAnalysisEngine(str(config_path))
        
        # Get available files
        files = engine.get_available_files(str(project_path))
        
        # Verify files were found
        assert len(files) >= 3  # Our test files
        
        # Verify file information
        filenames = [f.filename for f in files]
        assert "project_charter.md" in filenames
        assert "risk_register.md" in filenames
        assert "stakeholder_register.md" in filenames
        
        # Verify file properties
        for file_info in files:
            assert file_info.path.exists()
            assert file_info.size_bytes > 0
            assert file_info.is_readable
            assert file_info.last_modified <= datetime.now()
    
    def test_engine_status_and_info_methods(self, temp_workspace):
        """Test engine status and information methods."""
        config_path = temp_workspace['config_path']
        
        # Initialize engine
        engine = PMAnalysisEngine(str(config_path))
        
        # Test processor info
        processor_info = engine.get_processor_info()
        assert len(processor_info) == 3
        assert "document_check" in processor_info
        assert "status_analysis" in processor_info
        assert "learning_module" in processor_info
        
        # Test engine status
        status = engine.get_engine_status()
        assert status["initialized"] is True
        assert status["config_loaded"] is True
        assert len(status["processors_available"]) == 3
        assert len(status["reporters_available"]) == 2
        assert status["execution_count"] == 0  # No executions yet
        
        # Execute once and check status update
        result = engine.run(mode="document_check")
        assert result.success
        
        # Check updated status
        updated_status = engine.get_engine_status()
        assert updated_status["execution_count"] == 1
        assert updated_status["last_scan_file_count"] >= 3
    
    def test_engine_error_handling_invalid_project_path(self, temp_workspace):
        """Test engine error handling with invalid project path."""
        config_path = temp_workspace['config_path']
        
        # Initialize engine
        engine = PMAnalysisEngine(str(config_path))
        
        # Execute with non-existent project path
        result = engine.run(project_path="/non/existent/path")
        
        # Verify error handling
        assert not result.success
        assert len(result.errors) > 0
        assert any("does not exist" in error for error in result.errors)
    
    def test_engine_error_handling_invalid_mode(self, temp_workspace):
        """Test engine error handling with invalid mode."""
        config_path = temp_workspace['config_path']
        
        # Initialize engine
        engine = PMAnalysisEngine(str(config_path))
        
        # Execute with invalid mode
        result = engine.run(mode="invalid_mode")
        
        # Verify error handling
        assert not result.success
        assert len(result.errors) > 0
        assert any("Invalid mode" in error for error in result.errors)
    
    def test_engine_state_persistence_across_executions(self, temp_workspace):
        """Test that engine state is properly maintained across multiple executions."""
        config_path = temp_workspace['config_path']
        
        # Initialize engine
        engine = PMAnalysisEngine(str(config_path))
        
        # Execute multiple times
        result1 = engine.run(mode="document_check")
        result2 = engine.run(mode="status_analysis")
        result3 = engine.run(mode="learning_module")
        
        # Verify all executions succeeded
        assert result1.success
        assert result2.success
        assert result3.success
        
        # Verify execution history
        status = engine.get_engine_status()
        assert status["execution_count"] == 3
        
        # Verify last scan results are maintained
        assert status["last_scan_file_count"] >= 3
        
        # Verify execution history contains all executions
        assert len(engine.execution_history) == 3
        
        # Verify execution history details
        modes_executed = [exec_record["mode"] for exec_record in engine.execution_history]
        assert "document_check" in modes_executed
        assert "status_analysis" in modes_executed
        assert "learning_module" in modes_executed