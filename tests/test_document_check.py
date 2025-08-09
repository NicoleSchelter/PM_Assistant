"""
Unit tests for DocumentCheckProcessor.

This module contains comprehensive tests for the document check processor
functionality including document presence verification and format validation.
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

from processors.document_check import DocumentCheckProcessor
from core.models import FileInfo, FileFormat, DocumentType, ProcessingStatus
from utils.exceptions import ValidationError


class TestDocumentCheckProcessor:
    """Test cases for DocumentCheckProcessor class."""
    
    @pytest.fixture
    def processor(self):
        """Create a DocumentCheckProcessor instance for testing."""
        return DocumentCheckProcessor()
    
    @pytest.fixture
    def sample_config(self):
        """Create sample configuration for testing."""
        return {
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
                },
                {
                    "name": "Stakeholder Register",
                    "patterns": ["*stakeholder*"],
                    "formats": ["xlsx"],
                    "required": True
                }
            ]
        }
    
    @pytest.fixture
    def complete_file_set(self):
        """Create a complete set of project files for testing."""
        return [
            FileInfo(
                path=Path("project_charter.md"),
                format=FileFormat.MARKDOWN,
                document_type=DocumentType.CHARTER,
                size_bytes=2048,
                last_modified=datetime(2024, 1, 15, 10, 0, 0),
                is_readable=True
            ),
            FileInfo(
                path=Path("risk_register.xlsx"),
                format=FileFormat.EXCEL,
                document_type=DocumentType.RISK_REGISTER,
                size_bytes=4096,
                last_modified=datetime(2024, 1, 15, 11, 0, 0),
                is_readable=True
            ),
            FileInfo(
                path=Path("stakeholder_register.xlsx"),
                format=FileFormat.EXCEL,
                document_type=DocumentType.STAKEHOLDER_REGISTER,
                size_bytes=3072,
                last_modified=datetime(2024, 1, 15, 12, 0, 0),
                is_readable=True
            )
        ]
    
    @pytest.fixture
    def incomplete_file_set(self):
        """Create an incomplete set of project files for testing."""
        return [
            FileInfo(
                path=Path("project_charter.md"),
                format=FileFormat.MARKDOWN,
                document_type=DocumentType.CHARTER,
                size_bytes=2048,
                last_modified=datetime(2024, 1, 15, 10, 0, 0),
                is_readable=True
            ),
            # Missing risk register and stakeholder register
        ]
    
    @pytest.fixture
    def format_mismatch_files(self):
        """Create files with format mismatches for testing."""
        return [
            FileInfo(
                path=Path("project_charter.md"),
                format=FileFormat.MARKDOWN,
                document_type=DocumentType.CHARTER,
                size_bytes=2048,
                last_modified=datetime(2024, 1, 15, 10, 0, 0),
                is_readable=True
            ),
            FileInfo(
                path=Path("risk_register.md"),  # Should be xlsx/csv
                format=FileFormat.MARKDOWN,
                document_type=DocumentType.RISK_REGISTER,
                size_bytes=1024,
                last_modified=datetime(2024, 1, 15, 11, 0, 0),
                is_readable=True
            ),
            FileInfo(
                path=Path("stakeholder_register.csv"),  # Should be xlsx
                format=FileFormat.CSV,
                document_type=DocumentType.STAKEHOLDER_REGISTER,
                size_bytes=512,
                last_modified=datetime(2024, 1, 15, 12, 0, 0),
                is_readable=True
            )
        ]
    
    def test_processor_initialization(self, processor):
        """Test that processor initializes correctly."""
        assert processor.processor_name == "Document Check Processor"
        assert len(processor.required_files) > 0
        assert len(processor.optional_files) > 0
        assert "*charter*" in processor.required_files
        assert "*risk*" in processor.required_files
        assert "*stakeholder*" in processor.required_files
    
    def test_validate_inputs_with_valid_files(self, processor, complete_file_set):
        """Test input validation with valid files."""
        assert processor.validate_inputs(complete_file_set) is True
    
    def test_validate_inputs_with_empty_list(self, processor):
        """Test input validation with empty file list."""
        assert processor.validate_inputs([]) is False
    
    def test_validate_inputs_with_unreadable_files(self, processor):
        """Test input validation with unreadable files."""
        unreadable_files = [
            FileInfo(
                path=Path("corrupted_file.xlsx"),
                format=FileFormat.EXCEL,
                document_type=DocumentType.RISK_REGISTER,
                size_bytes=0,
                last_modified=datetime.now(),
                is_readable=False
            )
        ]
        assert processor.validate_inputs(unreadable_files) is False
    
    def test_process_complete_document_set(self, processor, complete_file_set, sample_config):
        """Test processing with complete document set."""
        result = processor.process(complete_file_set, sample_config)
        
        assert result.success is True
        assert result.operation == "document_check"
        assert "summary" in result.data
        assert "available_documents" in result.data
        assert "missing_documents" in result.data
        
        # Should have all required documents
        summary = result.data["summary"]
        assert summary["available_documents_count"] == 3
        assert summary["missing_documents_count"] == 0
        assert summary["compliance_score"] == 1.0
        assert summary["compliance_percentage"] == 100
    
    def test_process_incomplete_document_set(self, processor, incomplete_file_set, sample_config):
        """Test processing with incomplete document set."""
        result = processor.process(incomplete_file_set, sample_config)
        
        assert result.success is True
        assert result.operation == "document_check"
        
        summary = result.data["summary"]
        assert summary["available_documents_count"] == 1
        assert summary["missing_documents_count"] == 2
        assert summary["compliance_score"] < 1.0
        
        # Check missing documents
        missing_docs = result.data["missing_documents"]
        assert len(missing_docs) == 2
        missing_names = [doc["name"] for doc in missing_docs]
        assert "Risk Register" in missing_names
        assert "Stakeholder Register" in missing_names
    
    def test_process_format_mismatches(self, processor, format_mismatch_files, sample_config):
        """Test processing with format mismatches."""
        result = processor.process(format_mismatch_files, sample_config)
        
        assert result.success is True
        assert len(result.warnings) > 0
        
        # Should detect format mismatches
        format_mismatches = result.data["format_mismatches"]
        assert len(format_mismatches) > 0
        
        # Check that warnings mention format mismatches
        warning_text = " ".join(result.warnings)
        assert "format" in warning_text.lower()
    
    def test_process_with_no_config(self, processor, complete_file_set):
        """Test processing with no configuration (should use defaults)."""
        result = processor.process(complete_file_set, {})
        
        assert result.success is True
        # Should use default configuration
        assert "summary" in result.data
    
    def test_process_with_invalid_files(self, processor, sample_config):
        """Test processing with invalid file list."""
        result = processor.process([], sample_config)
        
        assert result.success is False
        assert len(result.errors) > 0
        assert "No valid files" in result.errors[0]
    
    def test_find_matching_files(self, processor, complete_file_set):
        """Test file pattern matching functionality."""
        # Test charter pattern
        charter_files = processor._find_matching_files(complete_file_set, ["*charter*"])
        assert len(charter_files) == 1
        assert "charter" in charter_files[0].filename.lower()
        
        # Test risk pattern
        risk_files = processor._find_matching_files(complete_file_set, ["*risk*"])
        assert len(risk_files) == 1
        assert "risk" in risk_files[0].filename.lower()
        
        # Test non-matching pattern
        budget_files = processor._find_matching_files(complete_file_set, ["*budget*"])
        assert len(budget_files) == 0
    
    def test_analyze_documents_complete_set(self, processor, complete_file_set, sample_config):
        """Test document analysis with complete file set."""
        analysis = processor._analyze_documents(complete_file_set, sample_config["required_documents"])
        
        assert len(analysis["available_documents"]) == 3
        assert len(analysis["missing_documents"]) == 0
        assert len(analysis["format_mismatches"]) == 0
        
        # Check document coverage
        coverage = analysis["document_coverage"]
        assert all(score == 1.0 for score in coverage.values())
    
    def test_analyze_documents_missing_files(self, processor, incomplete_file_set, sample_config):
        """Test document analysis with missing files."""
        analysis = processor._analyze_documents(incomplete_file_set, sample_config["required_documents"])
        
        assert len(analysis["available_documents"]) == 1
        assert len(analysis["missing_documents"]) == 2
        
        # Check that missing documents are correctly identified
        missing_names = [doc["name"] for doc in analysis["missing_documents"]]
        assert "Risk Register" in missing_names
        assert "Stakeholder Register" in missing_names
    
    def test_generate_recommendations_complete_set(self, processor):
        """Test recommendation generation for complete document set."""
        analysis = {
            "missing_documents": [],
            "format_mismatches": [],
            "optional_documents": []
        }
        summary = {"compliance_score": 1.0}
        
        recommendations = processor._generate_recommendations(analysis, summary)
        
        # Should suggest optional documents since everything else is complete
        assert any("optional" in rec.lower() for rec in recommendations)
    
    def test_generate_recommendations_missing_docs(self, processor):
        """Test recommendation generation for missing documents."""
        analysis = {
            "missing_documents": [
                {"name": "Project Charter", "patterns": ["*charter*"]},
                {"name": "Risk Register", "patterns": ["*risk*"]}
            ],
            "format_mismatches": [],
            "optional_documents": []
        }
        summary = {"compliance_score": 0.5}
        
        recommendations = processor._generate_recommendations(analysis, summary)
        
        # Should recommend creating missing documents
        assert any("missing" in rec.lower() for rec in recommendations)
        assert any("charter" in rec.lower() for rec in recommendations)
    
    def test_generate_recommendations_critical_compliance(self, processor):
        """Test recommendation generation for critical compliance issues."""
        analysis = {
            "missing_documents": [
                {"name": "Project Charter", "patterns": ["*charter*"]},
                {"name": "Scope Statement", "patterns": ["*scope*"]},
                {"name": "Risk Register", "patterns": ["*risk*"]}
            ],
            "format_mismatches": [],
            "optional_documents": []
        }
        summary = {"compliance_score": 0.2}
        
        recommendations = processor._generate_recommendations(analysis, summary)
        
        # Should have urgent recommendations
        urgent_recs = [rec for rec in recommendations if "URGENT" in rec]
        assert len(urgent_recs) > 0
    
    def test_get_compliance_status(self, processor):
        """Test compliance status calculation."""
        assert processor._get_compliance_status(0.95) == "Excellent"
        assert processor._get_compliance_status(0.85) == "Good"
        assert processor._get_compliance_status(0.65) == "Fair"
        assert processor._get_compliance_status(0.45) == "Poor"
        assert processor._get_compliance_status(0.25) == "Critical"
    
    def test_is_file_accounted_for(self, processor, sample_config):
        """Test file accounting functionality."""
        charter_file = FileInfo(
            path=Path("project_charter.md"),
            format=FileFormat.MARKDOWN,
            document_type=DocumentType.CHARTER,
            size_bytes=1024,
            last_modified=datetime.now(),
            is_readable=True
        )
        
        unknown_file = FileInfo(
            path=Path("random_document.pdf"),
            format=FileFormat.MARKDOWN,  # Using markdown as placeholder
            document_type=DocumentType.UNKNOWN,
            size_bytes=1024,
            last_modified=datetime.now(),
            is_readable=True
        )
        
        required_docs = sample_config["required_documents"]
        
        assert processor._is_file_accounted_for(charter_file, required_docs) is True
        assert processor._is_file_accounted_for(unknown_file, required_docs) is False
    
    def test_processing_time_tracking(self, processor, complete_file_set, sample_config):
        """Test that processing time is tracked correctly."""
        result = processor.process(complete_file_set, sample_config)
        
        assert result.success is True
        assert result.processing_time_seconds > 0
        assert result.processing_time_seconds < 10  # Should be fast
    
    @patch('processors.document_check.logger')
    def test_logging_behavior(self, mock_logger, processor, complete_file_set, sample_config):
        """Test that appropriate logging occurs during processing."""
        processor.process(complete_file_set, sample_config)
        
        # Verify that info logging occurred
        mock_logger.info.assert_called()
        
        # Check that debug logging occurred for found documents
        mock_logger.debug.assert_called()
    
    def test_error_handling_during_processing(self, processor, sample_config):
        """Test error handling when processing fails."""
        # Create a file that will cause issues
        problematic_files = [
            FileInfo(
                path=Path("test.xlsx"),
                format=FileFormat.EXCEL,
                document_type=DocumentType.RISK_REGISTER,
                size_bytes=1024,
                last_modified=datetime.now(),
                is_readable=True
            )
        ]
        
        # Mock an exception during analysis
        with patch.object(processor, '_analyze_documents', side_effect=Exception("Test error")):
            result = processor.process(problematic_files, sample_config)
            
            assert result.success is False
            assert len(result.errors) > 0
            assert "Test error" in result.errors[0]
    
    def test_default_required_documents(self, processor):
        """Test that default required documents are properly defined."""
        defaults = processor._get_default_required_documents()
        
        assert len(defaults) >= 6  # Should have at least 6 core documents
        
        # Check that core documents are included
        doc_names = [doc["name"] for doc in defaults]
        assert any("Charter" in name for name in doc_names)
        assert any("Risk" in name for name in doc_names)
        assert any("Stakeholder" in name for name in doc_names)
        assert any("WBS" in name or "Breakdown" in name for name in doc_names)
        
        # Verify structure of default documents
        for doc in defaults:
            assert "name" in doc
            assert "patterns" in doc
            assert "formats" in doc
            assert "required" in doc
            assert isinstance(doc["patterns"], list)
            assert isinstance(doc["formats"], list)
            assert isinstance(doc["required"], bool)