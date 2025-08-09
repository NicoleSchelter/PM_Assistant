"""
Tests for the PMAnalysisEngine core orchestration system.

This module contains comprehensive tests for the PMAnalysisEngine class,
including integration tests for complete workflow execution.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from core.engine import PMAnalysisEngine
from core.models import (
    FileInfo, 
    OperationMode, 
    ProcessingResult, 
    ModeRecommendation,
    DocumentType,
    FileFormat,
    ProcessingStatus
)
from utils.exceptions import (
    ConfigurationError,
    FileProcessingError,
    ValidationError,
    PMAnalysisError
)


class TestPMAnalysisEngine:
    """Test cases for PMAnalysisEngine class."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory with sample files."""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir) / "test_project"
        project_path.mkdir()
        
        # Create sample project files
        (project_path / "project_charter.md").write_text("# Project Charter\nThis is a test charter.")
        (project_path / "risk_register.xlsx").write_text("Risk data")  # Mock Excel content
        (project_path / "stakeholder_register.xlsx").write_text("Stakeholder data")
        
        yield str(project_path)
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration data."""
        return {
            "project": {
                "name": "Test Project",
                "default_path": "./test_project"
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
                    "formats": ["xlsx", "csv"],
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
                    "output_formats": ["markdown", "excel"]
                },
                "learning_module": {
                    "enabled": True,
                    "content_path": "./learning/modules"
                }
            },
            "output": {
                "directory": "./reports",
                "timestamp_files": True
            },
            "logging": {
                "level": "INFO"
            }
        }
    
    @pytest.fixture
    def sample_files(self):
        """Sample FileInfo objects for testing."""
        return [
            FileInfo(
                path=Path("project_charter.md"),
                format=FileFormat.MARKDOWN,
                document_type=DocumentType.CHARTER,
                size_bytes=1024,
                last_modified=datetime.now(),
                is_readable=True
            ),
            FileInfo(
                path=Path("risk_register.xlsx"),
                format=FileFormat.EXCEL,
                document_type=DocumentType.RISK_REGISTER,
                size_bytes=2048,
                last_modified=datetime.now(),
                is_readable=True
            )
        ]
    
    @pytest.fixture
    def mock_mode_recommendation(self):
        """Mock mode recommendation."""
        return ModeRecommendation(
            recommended_mode=OperationMode.STATUS_ANALYSIS,
            confidence_score=0.85,
            reasoning="Project has sufficient documents for comprehensive analysis",
            available_documents=[DocumentType.CHARTER, DocumentType.RISK_REGISTER],
            missing_documents=[DocumentType.STAKEHOLDER_REGISTER],
            file_quality_scores={
                DocumentType.CHARTER: 0.9,
                DocumentType.RISK_REGISTER: 0.8
            },
            alternative_modes=[OperationMode.DOCUMENT_CHECK]
        )
    
    @patch('core.engine.ConfigManager')
    def test_engine_initialization_success(self, mock_config_manager, mock_config):
        """Test successful engine initialization."""
        # Setup mocks
        mock_config_instance = Mock()
        mock_config_instance.load_config.return_value = mock_config
        mock_config_instance.get_required_documents.return_value = mock_config["required_documents"]
        mock_config_instance.get_project_path.return_value = "./test_project"
        mock_config_manager.return_value = mock_config_instance
        
        # Initialize engine
        engine = PMAnalysisEngine()
        
        # Verify initialization
        assert engine.config == mock_config
        assert engine.config_manager == mock_config_instance
        assert engine.file_scanner is not None
        assert engine.mode_detector is not None
        assert len(engine.processors) == 3
        assert len(engine.reporters) == 2
        assert engine.last_scan_results == []
        assert engine.last_mode_recommendation is None
        assert engine.execution_history == []
    
    @patch('core.engine.ConfigManager')
    def test_engine_initialization_config_error(self, mock_config_manager):
        """Test engine initialization with configuration error."""
        # Setup mock to raise exception
        mock_config_manager.side_effect = Exception("Config load failed")
        
        # Test initialization failure
        with pytest.raises(ConfigurationError, match="Failed to initialize PM Analysis Engine"):
            PMAnalysisEngine()
    
    @patch('core.engine.ConfigManager')
    def test_run_with_explicit_mode(self, mock_config_manager, mock_config, temp_project_dir, sample_files):
        """Test running engine with explicit mode override."""
        # Setup mocks
        mock_config_instance = Mock()
        mock_config_instance.load_config.return_value = mock_config
        mock_config_instance.get_required_documents.return_value = mock_config["required_documents"]
        mock_config_instance.get_project_path.return_value = temp_project_dir
        mock_config_manager.return_value = mock_config_instance
        
        engine = PMAnalysisEngine()
        
        # Mock file scanner
        engine.file_scanner.scan_directory = Mock(return_value=sample_files)
        engine.file_scanner.validate_file_formats = Mock(return_value=ProcessingResult(
            success=True, operation="validation"
        ))
        
        # Mock processor
        mock_processing_result = ProcessingResult(
            success=True,
            operation="document_check",
            data={"summary": "test results"}
        )
        engine.processors[OperationMode.DOCUMENT_CHECK].process = Mock(return_value=mock_processing_result)
        engine.processors[OperationMode.DOCUMENT_CHECK].validate_inputs = Mock(return_value=True)
        
        # Mock reporters
        mock_report_result = ProcessingResult(
            success=True,
            operation="report_generation",
            data={"output_path": "/test/report.md"}
        )
        engine.reporters['markdown'].generate_report = Mock(return_value=mock_report_result)
        
        # Execute with explicit mode
        result = engine.run(mode="document_check", project_path=temp_project_dir)
        
        # Verify execution
        assert result.success
        assert result.operation == "pm_analysis_execution"
        assert "execution_summary" in result.data
        assert result.data["execution_summary"]["selected_mode"] == "document_check"
        assert result.data["execution_summary"]["files_discovered"] == 2
        
        # Verify mocks were called
        engine.file_scanner.scan_directory.assert_called_once()
        engine.processors[OperationMode.DOCUMENT_CHECK].process.assert_called_once()
        engine.reporters['markdown'].generate_report.assert_called_once()
    
    @patch('core.engine.ConfigManager')
    def test_run_with_mode_detection(self, mock_config_manager, mock_config, temp_project_dir, 
                                   sample_files, mock_mode_recommendation):
        """Test running engine with automatic mode detection."""
        # Setup mocks
        mock_config_instance = Mock()
        mock_config_instance.load_config.return_value = mock_config
        mock_config_instance.get_required_documents.return_value = mock_config["required_documents"]
        mock_config_instance.get_project_path.return_value = temp_project_dir
        mock_config_manager.return_value = mock_config_instance
        
        engine = PMAnalysisEngine()
        
        # Mock file scanner
        engine.file_scanner.scan_directory = Mock(return_value=sample_files)
        engine.file_scanner.validate_file_formats = Mock(return_value=ProcessingResult(
            success=True, operation="validation"
        ))
        
        # Mock mode detector
        engine.mode_detector.analyze_files = Mock(return_value=mock_mode_recommendation)
        
        # Mock processor
        mock_processing_result = ProcessingResult(
            success=True,
            operation="status_analysis",
            data={"project_status": "healthy"}
        )
        engine.processors[OperationMode.STATUS_ANALYSIS].process = Mock(return_value=mock_processing_result)
        engine.processors[OperationMode.STATUS_ANALYSIS].validate_inputs = Mock(return_value=True)
        
        # Mock reporters
        mock_report_result = ProcessingResult(
            success=True,
            operation="report_generation",
            data={"output_path": "/test/report.md"}
        )
        engine.reporters['markdown'].generate_report = Mock(return_value=mock_report_result)
        
        # Execute without explicit mode
        result = engine.run(project_path=temp_project_dir)
        
        # Verify execution
        assert result.success
        assert result.data["execution_summary"]["selected_mode"] == "status_analysis"
        assert "mode_analysis" in result.data
        assert result.data["mode_analysis"]["recommended_mode"] == "status_analysis"
        assert result.data["mode_analysis"]["confidence_percentage"] == 85
        assert result.data["mode_analysis"]["was_recommendation_followed"] is True
        
        # Verify mode detection was called
        engine.mode_detector.analyze_files.assert_called_once_with(sample_files, temp_project_dir)
    
    @patch('core.engine.ConfigManager')
    def test_run_with_processing_failure(self, mock_config_manager, mock_config, temp_project_dir, sample_files):
        """Test engine behavior when processing fails."""
        # Setup mocks
        mock_config_instance = Mock()
        mock_config_instance.load_config.return_value = mock_config
        mock_config_instance.get_required_documents.return_value = mock_config["required_documents"]
        mock_config_instance.get_project_path.return_value = temp_project_dir
        mock_config_manager.return_value = mock_config_instance
        
        engine = PMAnalysisEngine()
        
        # Mock file scanner
        engine.file_scanner.scan_directory = Mock(return_value=sample_files)
        engine.file_scanner.validate_file_formats = Mock(return_value=ProcessingResult(
            success=True, operation="validation"
        ))
        
        # Mock processor to fail
        mock_processing_result = ProcessingResult(
            success=False,
            operation="document_check",
            errors=["Processing failed due to test error"]
        )
        engine.processors[OperationMode.DOCUMENT_CHECK].process = Mock(return_value=mock_processing_result)
        engine.processors[OperationMode.DOCUMENT_CHECK].validate_inputs = Mock(return_value=True)
        
        # Execute with explicit mode
        result = engine.run(mode="document_check", project_path=temp_project_dir)
        
        # Verify execution handled failure gracefully
        assert not result.success  # Overall execution should fail
        assert result.operation == "pm_analysis_execution"
        assert "Processing failed due to test error" in result.errors
    
    @patch('core.engine.ConfigManager')
    def test_run_with_invalid_mode(self, mock_config_manager, mock_config):
        """Test engine behavior with invalid mode."""
        # Setup mocks
        mock_config_instance = Mock()
        mock_config_instance.load_config.return_value = mock_config
        mock_config_instance.get_required_documents.return_value = mock_config["required_documents"]
        mock_config_manager.return_value = mock_config_instance
        
        engine = PMAnalysisEngine()
        
        # Execute with invalid mode
        result = engine.run(mode="invalid_mode")
        
        # Verify validation error
        assert not result.success
        assert any("Invalid mode" in error for error in result.errors)
    
    @patch('core.engine.ConfigManager')
    def test_run_with_invalid_project_path(self, mock_config_manager, mock_config):
        """Test engine behavior with invalid project path."""
        # Setup mocks
        mock_config_instance = Mock()
        mock_config_instance.load_config.return_value = mock_config
        mock_config_instance.get_required_documents.return_value = mock_config["required_documents"]
        mock_config_manager.return_value = mock_config_instance
        
        engine = PMAnalysisEngine()
        
        # Execute with non-existent path
        result = engine.run(project_path="/non/existent/path")
        
        # Verify validation error
        assert not result.success
        assert any("does not exist" in error for error in result.errors)
    
    @patch('core.engine.ConfigManager')
    def test_detect_optimal_mode(self, mock_config_manager, mock_config, temp_project_dir, 
                                sample_files, mock_mode_recommendation):
        """Test standalone mode detection."""
        # Setup mocks
        mock_config_instance = Mock()
        mock_config_instance.load_config.return_value = mock_config
        mock_config_instance.get_required_documents.return_value = mock_config["required_documents"]
        mock_config_instance.get_project_path.return_value = temp_project_dir
        mock_config_manager.return_value = mock_config_instance
        
        engine = PMAnalysisEngine()
        
        # Mock file scanner and mode detector
        engine.file_scanner.scan_directory = Mock(return_value=sample_files)
        engine.file_scanner.validate_file_formats = Mock(return_value=ProcessingResult(
            success=True, operation="validation"
        ))
        engine.mode_detector.analyze_files = Mock(return_value=mock_mode_recommendation)
        
        # Test mode detection
        recommendation = engine.detect_optimal_mode(temp_project_dir)
        
        # Verify results
        assert recommendation.recommended_mode == OperationMode.STATUS_ANALYSIS
        assert recommendation.confidence_score == 0.85
        assert "sufficient documents" in recommendation.reasoning
        
        # Verify mocks were called
        engine.file_scanner.scan_directory.assert_called_once()
        engine.mode_detector.analyze_files.assert_called_once()
    
    @patch('core.engine.ConfigManager')
    def test_get_available_files(self, mock_config_manager, mock_config, temp_project_dir, sample_files):
        """Test getting available files without processing."""
        # Setup mocks
        mock_config_instance = Mock()
        mock_config_instance.load_config.return_value = mock_config
        mock_config_instance.get_required_documents.return_value = mock_config["required_documents"]
        mock_config_instance.get_project_path.return_value = temp_project_dir
        mock_config_manager.return_value = mock_config_instance
        
        engine = PMAnalysisEngine()
        
        # Mock file scanner
        engine.file_scanner.scan_directory = Mock(return_value=sample_files)
        engine.file_scanner.validate_file_formats = Mock(return_value=ProcessingResult(
            success=True, operation="validation"
        ))
        
        # Test getting available files
        files = engine.get_available_files(temp_project_dir)
        
        # Verify results
        assert len(files) == 2
        assert files[0].filename == "project_charter.md"
        assert files[1].filename == "risk_register.xlsx"
        
        # Verify file scanner was called
        engine.file_scanner.scan_directory.assert_called_once()
    
    @patch('core.engine.ConfigManager')
    def test_get_processor_info(self, mock_config_manager, mock_config):
        """Test getting processor information."""
        # Setup mocks
        mock_config_instance = Mock()
        mock_config_instance.load_config.return_value = mock_config
        mock_config_instance.get_required_documents.return_value = mock_config["required_documents"]
        mock_config_manager.return_value = mock_config_instance
        
        engine = PMAnalysisEngine()
        
        # Test getting processor info
        processor_info = engine.get_processor_info()
        
        # Verify results
        assert len(processor_info) == 3
        assert "document_check" in processor_info
        assert "status_analysis" in processor_info
        assert "learning_module" in processor_info
        
        # Verify each processor info has expected fields
        for mode_name, info in processor_info.items():
            assert "name" in info
            assert "required_files" in info
            assert "optional_files" in info
            assert "class" in info
    
    @patch('core.engine.ConfigManager')
    def test_get_engine_status(self, mock_config_manager, mock_config):
        """Test getting engine status."""
        # Setup mocks
        mock_config_instance = Mock()
        mock_config_instance.load_config.return_value = mock_config
        mock_config_instance.get_required_documents.return_value = mock_config["required_documents"]
        mock_config_manager.return_value = mock_config_instance
        
        engine = PMAnalysisEngine()
        
        # Test getting engine status
        status = engine.get_engine_status()
        
        # Verify results
        assert status["initialized"] is True
        assert status["config_loaded"] is True
        assert len(status["processors_available"]) == 3
        assert len(status["reporters_available"]) == 2
        assert status["last_scan_file_count"] == 0
        assert status["execution_count"] == 0
        assert status["last_recommended_mode"] is None
    
    @patch('core.engine.ConfigManager')
    def test_report_generation_with_multiple_formats(self, mock_config_manager, mock_config, 
                                                   temp_project_dir, sample_files):
        """Test report generation with multiple output formats."""
        # Setup mocks
        mock_config_instance = Mock()
        mock_config_instance.load_config.return_value = mock_config
        mock_config_instance.get_required_documents.return_value = mock_config["required_documents"]
        mock_config_instance.get_project_path.return_value = temp_project_dir
        mock_config_manager.return_value = mock_config_instance
        
        engine = PMAnalysisEngine()
        
        # Mock file scanner
        engine.file_scanner.scan_directory = Mock(return_value=sample_files)
        engine.file_scanner.validate_file_formats = Mock(return_value=ProcessingResult(
            success=True, operation="validation"
        ))
        
        # Mock processor
        mock_processing_result = ProcessingResult(
            success=True,
            operation="status_analysis",
            data={"project_status": "healthy"}
        )
        engine.processors[OperationMode.STATUS_ANALYSIS].process = Mock(return_value=mock_processing_result)
        engine.processors[OperationMode.STATUS_ANALYSIS].validate_inputs = Mock(return_value=True)
        
        # Mock reporters
        mock_markdown_result = ProcessingResult(
            success=True,
            operation="markdown_report",
            data={"output_path": "/test/report.md"}
        )
        mock_excel_result = ProcessingResult(
            success=True,
            operation="excel_report",
            data={"output_path": "/test/report.xlsx"}
        )
        engine.reporters['markdown'].generate_report = Mock(return_value=mock_markdown_result)
        engine.reporters['excel'].generate_report = Mock(return_value=mock_excel_result)
        
        # Execute with multiple output formats
        result = engine.run(
            mode="status_analysis",
            project_path=temp_project_dir,
            output_formats=["markdown", "excel"]
        )
        
        # Verify execution
        assert result.success
        assert "report_summary" in result.data
        assert "markdown" in result.data["report_summary"]
        assert "excel" in result.data["report_summary"]
        assert result.data["report_summary"]["markdown"]["success"] is True
        assert result.data["report_summary"]["excel"]["success"] is True
        
        # Verify both reporters were called
        engine.reporters['markdown'].generate_report.assert_called_once()
        engine.reporters['excel'].generate_report.assert_called_once()
    
    @patch('core.engine.ConfigManager')
    def test_engine_state_updates(self, mock_config_manager, mock_config, temp_project_dir, 
                                 sample_files, mock_mode_recommendation):
        """Test that engine state is properly updated after execution."""
        # Setup mocks
        mock_config_instance = Mock()
        mock_config_instance.load_config.return_value = mock_config
        mock_config_instance.get_required_documents.return_value = mock_config["required_documents"]
        mock_config_instance.get_project_path.return_value = temp_project_dir
        mock_config_manager.return_value = mock_config_instance
        
        engine = PMAnalysisEngine()
        
        # Mock components
        engine.file_scanner.scan_directory = Mock(return_value=sample_files)
        engine.file_scanner.validate_file_formats = Mock(return_value=ProcessingResult(
            success=True, operation="validation"
        ))
        engine.mode_detector.analyze_files = Mock(return_value=mock_mode_recommendation)
        
        mock_processing_result = ProcessingResult(
            success=True,
            operation="status_analysis",
            data={"project_status": "healthy"}
        )
        engine.processors[OperationMode.STATUS_ANALYSIS].process = Mock(return_value=mock_processing_result)
        engine.processors[OperationMode.STATUS_ANALYSIS].validate_inputs = Mock(return_value=True)
        
        mock_report_result = ProcessingResult(
            success=True,
            operation="report_generation",
            data={"output_path": "/test/report.md"}
        )
        engine.reporters['markdown'].generate_report = Mock(return_value=mock_report_result)
        
        # Execute
        result = engine.run(project_path=temp_project_dir)
        
        # Verify state updates
        assert len(engine.last_scan_results) == 2
        assert engine.last_mode_recommendation == mock_mode_recommendation
        assert len(engine.execution_history) == 1
        
        execution_record = engine.execution_history[0]
        assert execution_record["success"] is True
        assert execution_record["mode"] == "status_analysis"
        assert execution_record["files_processed"] == 2
        assert "execution_time" in execution_record
    
    @patch('core.engine.ConfigManager')
    def test_file_scanning_failure_handling(self, mock_config_manager, mock_config, temp_project_dir):
        """Test handling of file scanning failures."""
        # Setup mocks
        mock_config_instance = Mock()
        mock_config_instance.load_config.return_value = mock_config
        mock_config_instance.get_required_documents.return_value = mock_config["required_documents"]
        mock_config_instance.get_project_path.return_value = temp_project_dir
        mock_config_manager.return_value = mock_config_instance
        
        engine = PMAnalysisEngine()
        
        # Mock file scanner to fail
        engine.file_scanner.scan_directory = Mock(side_effect=Exception("File scanning failed"))
        
        # Execute
        result = engine.run(project_path=temp_project_dir)
        
        # Verify failure handling
        assert not result.success
        assert any("File scanning failed" in error for error in result.errors)
        assert result.metadata["failure_stage"] == "file_scanning"
    
    @patch('core.engine.ConfigManager')
    def test_mode_detection_failure_fallback(self, mock_config_manager, mock_config, 
                                           temp_project_dir, sample_files):
        """Test fallback behavior when mode detection fails."""
        # Setup mocks
        mock_config_instance = Mock()
        mock_config_instance.load_config.return_value = mock_config
        mock_config_instance.get_required_documents.return_value = mock_config["required_documents"]
        mock_config_instance.get_project_path.return_value = temp_project_dir
        mock_config_manager.return_value = mock_config_instance
        
        engine = PMAnalysisEngine()
        
        # Mock file scanner
        engine.file_scanner.scan_directory = Mock(return_value=sample_files)
        engine.file_scanner.validate_file_formats = Mock(return_value=ProcessingResult(
            success=True, operation="validation"
        ))
        
        # Mock mode detector to fail
        engine.mode_detector.analyze_files = Mock(side_effect=Exception("Mode detection failed"))
        
        # Mock learning module processor (fallback mode)
        mock_processing_result = ProcessingResult(
            success=True,
            operation="learning_module",
            data={"learning_content": "test content"}
        )
        engine.processors[OperationMode.LEARNING_MODULE].process = Mock(return_value=mock_processing_result)
        engine.processors[OperationMode.LEARNING_MODULE].validate_inputs = Mock(return_value=True)
        
        # Mock reporter
        mock_report_result = ProcessingResult(
            success=True,
            operation="report_generation",
            data={"output_path": "/test/report.md"}
        )
        engine.reporters['markdown'].generate_report = Mock(return_value=mock_report_result)
        
        # Execute without explicit mode (should trigger mode detection)
        result = engine.run(project_path=temp_project_dir)
        
        # Verify fallback to learning module
        assert result.success
        assert result.data["execution_summary"]["selected_mode"] == "learning_module"
        assert "mode_analysis" in result.data
        assert "Mode detection failed" in result.data["mode_analysis"]["reasoning"]