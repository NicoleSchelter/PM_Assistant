"""
Unit tests for core data models.
"""

import pytest
from datetime import datetime, date
from pathlib import Path

from core.models import (
    FileInfo, ProcessingResult, ModeRecommendation, ProjectStatus,
    OperationMode, FileFormat, ProcessingStatus, DocumentType
)


class TestFileInfo:
    """Test cases for FileInfo dataclass."""
    
    def test_file_info_creation(self, sample_file_info):
        """Test basic FileInfo creation."""
        assert sample_file_info.path == Path("test_file.xlsx")
        assert sample_file_info.format == FileFormat.EXCEL
        assert sample_file_info.document_type == DocumentType.RISK_REGISTER
        assert sample_file_info.size_bytes == 1024
        assert sample_file_info.is_readable is True
        assert sample_file_info.processing_status == ProcessingStatus.NOT_STARTED
    
    def test_file_info_properties(self, sample_file_info):
        """Test FileInfo properties."""
        assert sample_file_info.filename == "test_file.xlsx"
        assert sample_file_info.extension == ".xlsx"
        assert sample_file_info.is_processed() is False
        assert sample_file_info.has_error() is False
    
    def test_file_info_path_conversion(self):
        """Test automatic path conversion to Path object."""
        file_info = FileInfo(
            path="test_file.md",
            format=FileFormat.MARKDOWN,
            document_type=DocumentType.REQUIREMENTS,
            size_bytes=512,
            last_modified=datetime.now()
        )
        assert isinstance(file_info.path, Path)
        assert file_info.path == Path("test_file.md")
    
    def test_file_info_negative_size_correction(self):
        """Test that negative file sizes are corrected to 0."""
        file_info = FileInfo(
            path=Path("test.txt"),
            format=FileFormat.MARKDOWN,
            document_type=DocumentType.UNKNOWN,
            size_bytes=-100,
            last_modified=datetime.now()
        )
        assert file_info.size_bytes == 0
    
    def test_mark_as_processed(self, sample_file_info):
        """Test marking file as processed."""
        sample_file_info.mark_as_processed()
        assert sample_file_info.processing_status == ProcessingStatus.COMPLETED
        assert sample_file_info.error_message is None
        assert sample_file_info.is_processed() is True
    
    def test_mark_as_failed(self, sample_file_info):
        """Test marking file as failed."""
        error_msg = "File is corrupted"
        sample_file_info.mark_as_failed(error_msg)
        assert sample_file_info.processing_status == ProcessingStatus.FAILED
        assert sample_file_info.error_message == error_msg
        assert sample_file_info.has_error() is True


class TestProcessingResult:
    """Test cases for ProcessingResult dataclass."""
    
    def test_processing_result_creation(self, sample_processing_result):
        """Test basic ProcessingResult creation."""
        assert sample_processing_result.success is True
        assert sample_processing_result.operation == "file_processing"
        assert sample_processing_result.file_path == Path("test_file.xlsx")
        assert sample_processing_result.data == {"records": 10, "errors": 0}
        assert sample_processing_result.processing_time_seconds == 2.5
        assert len(sample_processing_result.errors) == 0
        assert len(sample_processing_result.warnings) == 0
    
    def test_processing_result_negative_time_correction(self):
        """Test that negative processing times are corrected to 0."""
        result = ProcessingResult(
            success=True,
            operation="test",
            processing_time_seconds=-1.0
        )
        assert result.processing_time_seconds == 0.0
    
    def test_add_error(self, sample_processing_result):
        """Test adding errors to processing result."""
        sample_processing_result.add_error("Test error")
        assert len(sample_processing_result.errors) == 1
        assert sample_processing_result.errors[0] == "Test error"
        assert sample_processing_result.success is False
        assert sample_processing_result.has_errors() is True
    
    def test_add_warning(self, sample_processing_result):
        """Test adding warnings to processing result."""
        sample_processing_result.add_warning("Test warning")
        assert len(sample_processing_result.warnings) == 1
        assert sample_processing_result.warnings[0] == "Test warning"
        assert sample_processing_result.has_warnings() is True
    
    def test_get_summary_success(self, sample_processing_result):
        """Test summary generation for successful result."""
        summary = sample_processing_result.get_summary()
        assert summary == "file_processing: SUCCESS"
    
    def test_get_summary_with_errors_and_warnings(self):
        """Test summary generation with errors and warnings."""
        result = ProcessingResult(success=False, operation="test_op")
        result.add_error("Error 1")
        result.add_error("Error 2")
        result.add_warning("Warning 1")
        
        summary = result.get_summary()
        assert summary == "test_op: FAILED (2 errors) (1 warnings)"


class TestModeRecommendation:
    """Test cases for ModeRecommendation dataclass."""
    
    def test_mode_recommendation_creation(self, sample_mode_recommendation):
        """Test basic ModeRecommendation creation."""
        assert sample_mode_recommendation.recommended_mode == OperationMode.STATUS_ANALYSIS
        assert sample_mode_recommendation.confidence_score == 0.85
        assert "All required documents" in sample_mode_recommendation.reasoning
        assert DocumentType.RISK_REGISTER in sample_mode_recommendation.available_documents
        assert DocumentType.STAKEHOLDER_REGISTER in sample_mode_recommendation.missing_documents
    
    def test_confidence_score_bounds(self):
        """Test confidence score is bounded between 0 and 1."""
        # Test lower bound
        recommendation = ModeRecommendation(
            recommended_mode=OperationMode.DOCUMENT_CHECK,
            confidence_score=-0.5,
            reasoning="Test"
        )
        assert recommendation.confidence_score == 0.0
        
        # Test upper bound
        recommendation = ModeRecommendation(
            recommended_mode=OperationMode.DOCUMENT_CHECK,
            confidence_score=1.5,
            reasoning="Test"
        )
        assert recommendation.confidence_score == 1.0
    
    def test_file_quality_scores_bounds(self):
        """Test file quality scores are bounded between 0 and 1."""
        recommendation = ModeRecommendation(
            recommended_mode=OperationMode.STATUS_ANALYSIS,
            confidence_score=0.8,
            reasoning="Test",
            file_quality_scores={
                DocumentType.RISK_REGISTER: -0.1,
                DocumentType.WBS: 1.5
            }
        )
        assert recommendation.file_quality_scores[DocumentType.RISK_REGISTER] == 0.0
        assert recommendation.file_quality_scores[DocumentType.WBS] == 1.0
    
    def test_confidence_percentage(self, sample_mode_recommendation):
        """Test confidence percentage calculation."""
        assert sample_mode_recommendation.confidence_percentage == 85
    
    def test_is_high_confidence(self, sample_mode_recommendation):
        """Test high confidence detection."""
        assert sample_mode_recommendation.is_high_confidence() is True
        assert sample_mode_recommendation.is_high_confidence(threshold=0.9) is False
    
    def test_get_quality_summary(self, sample_mode_recommendation):
        """Test quality summary generation."""
        summary = sample_mode_recommendation.get_quality_summary()
        assert summary["risk_register"] == "Excellent"
        assert summary["wbs"] == "Good"


class TestProjectStatus:
    """Test cases for ProjectStatus dataclass."""
    
    def test_project_status_creation(self, sample_project_status):
        """Test basic ProjectStatus creation."""
        assert sample_project_status.project_name == "Test Project"
        assert sample_project_status.overall_health_score == 0.75
        assert sample_project_status.total_risks == 15
        assert sample_project_status.high_priority_risks == 3
        assert sample_project_status.total_deliverables == 25
        assert sample_project_status.completed_deliverables == 10
    
    def test_health_score_bounds(self):
        """Test health score is bounded between 0 and 1."""
        # Test lower bound
        status = ProjectStatus(
            project_name="Test",
            analysis_timestamp=datetime.now(),
            overall_health_score=-0.5
        )
        assert status.overall_health_score == 0.0
        
        # Test upper bound
        status = ProjectStatus(
            project_name="Test",
            analysis_timestamp=datetime.now(),
            overall_health_score=1.5
        )
        assert status.overall_health_score == 1.0
    
    def test_negative_counts_correction(self):
        """Test that negative counts are corrected to 0."""
        status = ProjectStatus(
            project_name="Test",
            analysis_timestamp=datetime.now(),
            overall_health_score=0.5,
            total_risks=-5,
            total_deliverables=-10
        )
        assert status.total_risks == 0
        assert status.total_deliverables == 0
    
    def test_health_percentage(self, sample_project_status):
        """Test health percentage calculation."""
        assert sample_project_status.health_percentage == 75
    
    def test_deliverable_completion_rate(self, sample_project_status):
        """Test deliverable completion rate calculation."""
        assert sample_project_status.deliverable_completion_rate == 0.4  # 10/25
    
    def test_milestone_completion_rate(self, sample_project_status):
        """Test milestone completion rate calculation."""
        assert sample_project_status.milestone_completion_rate == 0.375  # 3/8
    
    def test_risk_severity_ratio(self, sample_project_status):
        """Test risk severity ratio calculation."""
        assert sample_project_status.risk_severity_ratio == 0.2  # 3/15
    
    def test_is_healthy(self, sample_project_status):
        """Test health status determination."""
        assert sample_project_status.is_healthy() is True
        assert sample_project_status.is_healthy(threshold=0.8) is False
    
    def test_has_critical_issues(self, sample_project_status):
        """Test critical issues detection."""
        assert sample_project_status.has_critical_issues() is False
        
        sample_project_status.add_critical_issue("Budget overrun")
        assert sample_project_status.has_critical_issues() is True
    
    def test_get_status_summary(self, sample_project_status):
        """Test status summary generation."""
        summary = sample_project_status.get_status_summary()
        assert summary == "Test Project: Healthy (75%)"
    
    def test_add_critical_issue(self, sample_project_status):
        """Test adding critical issues."""
        issue = "Critical resource shortage"
        sample_project_status.add_critical_issue(issue)
        assert issue in sample_project_status.critical_issues
        
        # Test duplicate prevention
        sample_project_status.add_critical_issue(issue)
        assert sample_project_status.critical_issues.count(issue) == 1
    
    def test_add_recommendation(self, sample_project_status):
        """Test adding recommendations."""
        recommendation = "Increase team size"
        sample_project_status.add_recommendation(recommendation)
        assert recommendation in sample_project_status.recommendations
        
        # Test duplicate prevention
        sample_project_status.add_recommendation(recommendation)
        assert sample_project_status.recommendations.count(recommendation) == 1
    
    def test_zero_division_handling(self):
        """Test handling of zero division in rate calculations."""
        status = ProjectStatus(
            project_name="Test",
            analysis_timestamp=datetime.now(),
            overall_health_score=0.5,
            total_deliverables=0,
            total_milestones=0,
            total_risks=0
        )
        assert status.deliverable_completion_rate == 0.0
        assert status.milestone_completion_rate == 0.0
        assert status.risk_severity_ratio == 0.0