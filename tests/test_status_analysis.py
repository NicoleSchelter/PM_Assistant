"""
Unit tests for StatusAnalysisProcessor.

This module contains comprehensive tests for the status analysis processor
functionality including data integration and project health analysis.
"""

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from core.domain import (
    Deliverable,
    DeliverableStatus,
    Milestone,
    MilestoneStatus,
    Risk,
    RiskPriority,
    RiskStatus,
    Stakeholder,
    StakeholderInfluence,
    StakeholderInterest,
)
from core.models import DocumentType, FileFormat, FileInfo, ProjectStatus
from processors.status_analysis import StatusAnalysisProcessor
from utils.exceptions import DataExtractionError, FileProcessingError


class TestStatusAnalysisProcessor:
    """Test cases for StatusAnalysisProcessor class."""

    @pytest.fixture
    def processor(self):
        """Create a StatusAnalysisProcessor instance for testing."""
        return StatusAnalysisProcessor()

    @pytest.fixture
    def sample_config(self):
        """Create sample configuration for testing."""
        return {"project": {"name": "Test Project"}}

    @pytest.fixture
    def complete_file_set(self):
        """Create a complete set of project files for testing."""
        return [
            FileInfo(
                path=Path("risk_register.xlsx"),
                format=FileFormat.EXCEL,
                document_type=DocumentType.RISK_REGISTER,
                size_bytes=4096,
                last_modified=datetime(2024, 1, 15, 10, 0, 0),
                is_readable=True,
            ),
            FileInfo(
                path=Path("stakeholder_register.xlsx"),
                format=FileFormat.EXCEL,
                document_type=DocumentType.STAKEHOLDER_REGISTER,
                size_bytes=3072,
                last_modified=datetime(2024, 1, 15, 11, 0, 0),
                is_readable=True,
            ),
            FileInfo(
                path=Path("wbs_deliverables.md"),
                format=FileFormat.MARKDOWN,
                document_type=DocumentType.WBS,
                size_bytes=2048,
                last_modified=datetime(2024, 1, 15, 12, 0, 0),
                is_readable=True,
            ),
            FileInfo(
                path=Path("project_roadmap.md"),
                format=FileFormat.MARKDOWN,
                document_type=DocumentType.ROADMAP,
                size_bytes=1536,
                last_modified=datetime(2024, 1, 15, 13, 0, 0),
                is_readable=True,
            ),
        ]

    @pytest.fixture
    def minimal_file_set(self):
        """Create a minimal set of files for testing."""
        return [
            FileInfo(
                path=Path("risk_register.xlsx"),
                format=FileFormat.EXCEL,
                document_type=DocumentType.RISK_REGISTER,
                size_bytes=4096,
                last_modified=datetime(2024, 1, 15, 10, 0, 0),
                is_readable=True,
            )
        ]

    @pytest.fixture
    def sample_risks(self):
        """Create sample risk data for testing."""
        return [
            Risk(
                risk_id="RISK-001",
                title="Budget Overrun",
                description="Risk of budget overrun",
                category="Financial",
                probability=0.7,
                impact=0.8,
                priority=RiskPriority.HIGH,
                status=RiskStatus.OPEN,
                owner="John Doe",
                identified_date=date(2024, 1, 10),
            ),
            Risk(
                risk_id="RISK-002",
                title="Schedule Delay",
                description="Risk of schedule delay",
                category="Schedule",
                probability=0.5,
                impact=0.6,
                priority=RiskPriority.MEDIUM,
                status=RiskStatus.MITIGATED,
                owner="Jane Smith",
                identified_date=date(2024, 1, 12),
            ),
        ]

    @pytest.fixture
    def sample_deliverables(self):
        """Create sample deliverable data for testing."""
        return [
            Deliverable(
                deliverable_id="DEL-001",
                name="Requirements Document",
                description="Project requirements",
                wbs_code="1.1",
                status=DeliverableStatus.COMPLETED,
                assigned_to="Alice Johnson",
                completion_percentage=100.0,
                due_date=date(2024, 2, 1),
            ),
            Deliverable(
                deliverable_id="DEL-002",
                name="Design Document",
                description="System design",
                wbs_code="1.2",
                status=DeliverableStatus.IN_PROGRESS,
                assigned_to="Bob Wilson",
                completion_percentage=60.0,
                due_date=date(2024, 2, 15),
            ),
        ]

    @pytest.fixture
    def sample_milestones(self):
        """Create sample milestone data for testing."""
        return [
            Milestone(
                milestone_id="MS-001",
                name="Requirements Complete",
                description="All requirements approved",
                target_date=date(2024, 2, 1),
                status=MilestoneStatus.COMPLETED,
                actual_date=date(2024, 1, 30),
                owner="Project Manager",
            ),
            Milestone(
                milestone_id="MS-002",
                name="Design Review",
                description="Design review meeting",
                target_date=date(2024, 2, 20),
                status=MilestoneStatus.UPCOMING,
                owner="Lead Architect",
            ),
        ]

    @pytest.fixture
    def sample_stakeholders(self):
        """Create sample stakeholder data for testing."""
        return [
            Stakeholder(
                stakeholder_id="STK-001",
                name="Project Sponsor",
                role="Sponsor",
                organization="ABC Corp",
                influence=StakeholderInfluence.VERY_HIGH,
                interest=StakeholderInterest.HIGH,
                is_decision_maker=True,
                is_sponsor=True,
            ),
            Stakeholder(
                stakeholder_id="STK-002",
                name="End User Rep",
                role="User Representative",
                organization="XYZ Dept",
                influence=StakeholderInfluence.MEDIUM,
                interest=StakeholderInterest.VERY_HIGH,
                is_end_user=True,
            ),
        ]

    def test_processor_initialization(self, processor):
        """Test that processor initializes correctly."""
        assert processor.processor_name == "Status Analysis Processor"
        assert len(processor.required_files) > 0
        assert len(processor.optional_files) > 0
        assert "*risk*" in processor.required_files
        assert "*stakeholder*" in processor.required_files

        # Check that extractors are initialized
        assert processor.risk_extractor is not None
        assert processor.deliverable_extractor is not None
        assert processor.milestone_extractor is not None
        assert processor.stakeholder_extractor is not None

    def test_validate_inputs_with_valid_files(self, processor, complete_file_set):
        """Test input validation with valid files."""
        assert processor.validate_inputs(complete_file_set) is True

    def test_validate_inputs_with_minimal_files(self, processor, minimal_file_set):
        """Test input validation with minimal required files."""
        assert processor.validate_inputs(minimal_file_set) is True

    def test_validate_inputs_with_empty_list(self, processor):
        """Test input validation with empty file list."""
        assert processor.validate_inputs([]) is False

    def test_validate_inputs_with_no_risk_data(self, processor):
        """Test input validation with no risk data."""
        files_without_risk = [
            FileInfo(
                path=Path("stakeholder_register.xlsx"),
                format=FileFormat.EXCEL,
                document_type=DocumentType.STAKEHOLDER_REGISTER,
                size_bytes=3072,
                last_modified=datetime.now(),
                is_readable=True,
            )
        ]
        assert processor.validate_inputs(files_without_risk) is False

    def test_validate_inputs_with_unreadable_files(self, processor):
        """Test input validation with unreadable files."""
        unreadable_files = [
            FileInfo(
                path=Path("risk_register.xlsx"),
                format=FileFormat.EXCEL,
                document_type=DocumentType.RISK_REGISTER,
                size_bytes=0,
                last_modified=datetime.now(),
                is_readable=False,
            )
        ]
        assert processor.validate_inputs(unreadable_files) is False

    @patch("processors.status_analysis.RiskExtractor")
    @patch("processors.status_analysis.DeliverableExtractor")
    @patch("processors.status_analysis.MilestoneExtractor")
    @patch("processors.status_analysis.StakeholderExtractor")
    def test_extract_all_data(
        self,
        mock_stakeholder_ext,
        mock_milestone_ext,
        mock_deliverable_ext,
        mock_risk_ext,
        processor,
        complete_file_set,
        sample_risks,
        sample_deliverables,
        sample_milestones,
        sample_stakeholders,
    ):
        """Test data extraction from all files."""
        # Setup mocks
        mock_risk_ext.return_value.extract_risks.return_value = sample_risks
        mock_deliverable_ext.return_value.extract_deliverables.return_value = sample_deliverables
        mock_milestone_ext.return_value.extract_milestones.return_value = sample_milestones
        mock_stakeholder_ext.return_value.extract_stakeholders.return_value = sample_stakeholders

        # Reinitialize processor to use mocked extractors
        processor = StatusAnalysisProcessor()

        results = processor._extract_all_data(complete_file_set)

        assert len(results["risks"]) == len(sample_risks)
        assert len(results["deliverables"]) == len(sample_deliverables)
        assert len(results["milestones"]) == len(sample_milestones)
        assert len(results["stakeholders"]) == len(sample_stakeholders)
        assert "extraction_summary" in results
        assert results["extraction_summary"]["total_files_processed"] == len(complete_file_set)

    def test_compile_project_status(
        self, processor, sample_risks, sample_deliverables, sample_milestones, sample_stakeholders
    ):
        """Test project status compilation."""
        extraction_results = {
            "risks": sample_risks,
            "deliverables": sample_deliverables,
            "milestones": sample_milestones,
            "stakeholders": sample_stakeholders,
        }

        project_status = processor._compile_project_status(extraction_results, "Test Project")

        assert project_status.project_name == "Test Project"
        assert project_status.total_risks == len(sample_risks)
        assert project_status.total_deliverables == len(sample_deliverables)
        assert project_status.total_milestones == len(sample_milestones)
        assert project_status.total_stakeholders == len(sample_stakeholders)
        assert 0.0 <= project_status.overall_health_score <= 1.0
        assert isinstance(project_status.critical_issues, list)
        assert isinstance(project_status.recommendations, list)

    def test_calculate_stakeholder_engagement(self, processor, sample_stakeholders):
        """Test stakeholder engagement calculation."""
        engagement = processor._calculate_stakeholder_engagement(sample_stakeholders)

        assert 0.0 <= engagement <= 1.0
        assert isinstance(engagement, float)

    def test_calculate_stakeholder_engagement_empty_list(self, processor):
        """Test stakeholder engagement calculation with empty list."""
        engagement = processor._calculate_stakeholder_engagement([])
        assert engagement == 0.0

    def test_calculate_schedule_variance(self, processor, sample_milestones):
        """Test schedule variance calculation."""
        # Set some variance data
        sample_milestones[0].actual_date = date(2024, 1, 30)  # 2 days early

        variance = processor._calculate_schedule_variance(sample_milestones)
        assert isinstance(variance, int)

    def test_calculate_schedule_variance_empty_list(self, processor):
        """Test schedule variance calculation with empty list."""
        variance = processor._calculate_schedule_variance([])
        assert variance == 0

    def test_calculate_health_score(
        self, processor, sample_risks, sample_deliverables, sample_milestones, sample_stakeholders
    ):
        """Test health score calculation."""
        health_score = processor._calculate_health_score(
            sample_risks, sample_deliverables, sample_milestones, sample_stakeholders
        )

        assert 0.0 <= health_score <= 1.0
        assert isinstance(health_score, float)

    def test_calculate_health_score_empty_data(self, processor):
        """Test health score calculation with empty data."""
        health_score = processor._calculate_health_score([], [], [], [])
        assert health_score == 0.5  # Default score when no data

    def test_identify_critical_issues(
        self, processor, sample_risks, sample_deliverables, sample_milestones, sample_stakeholders
    ):
        """Test critical issues identification."""
        # Create some critical conditions
        sample_risks[0].priority = RiskPriority.CRITICAL
        sample_milestones[1].status = MilestoneStatus.OVERDUE

        issues = processor._identify_critical_issues(
            sample_risks, sample_deliverables, sample_milestones, sample_stakeholders
        )

        assert isinstance(issues, list)
        # Should identify critical risk
        assert any("critical" in issue.lower() for issue in issues)

    def test_generate_recommendations(
        self, processor, sample_risks, sample_deliverables, sample_milestones, sample_stakeholders
    ):
        """Test recommendations generation."""
        recommendations = processor._generate_recommendations(
            sample_risks, sample_deliverables, sample_milestones, sample_stakeholders
        )

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        # Should have at least one recommendation
        assert all(isinstance(rec, str) for rec in recommendations)

    def test_serialize_risk(self, processor, sample_risks):
        """Test risk serialization."""
        serialized = processor._serialize_risk(sample_risks[0])

        assert "risk_id" in serialized
        assert "title" in serialized
        assert "priority" in serialized
        assert "status" in serialized
        assert "probability" in serialized
        assert "impact" in serialized
        assert "risk_score" in serialized
        assert "owner" in serialized

    def test_serialize_deliverable(self, processor, sample_deliverables):
        """Test deliverable serialization."""
        serialized = processor._serialize_deliverable(sample_deliverables[0])

        assert "deliverable_id" in serialized
        assert "name" in serialized
        assert "wbs_code" in serialized
        assert "status" in serialized
        assert "completion_percentage" in serialized
        assert "assigned_to" in serialized
        assert "is_overdue" in serialized

    def test_serialize_milestone(self, processor, sample_milestones):
        """Test milestone serialization."""
        serialized = processor._serialize_milestone(sample_milestones[0])

        assert "milestone_id" in serialized
        assert "name" in serialized
        assert "target_date" in serialized
        assert "status" in serialized
        assert "is_overdue" in serialized
        assert "days_until_target" in serialized
        assert "owner" in serialized

    def test_serialize_stakeholder(self, processor, sample_stakeholders):
        """Test stakeholder serialization."""
        serialized = processor._serialize_stakeholder(sample_stakeholders[0])

        assert "stakeholder_id" in serialized
        assert "name" in serialized
        assert "role" in serialized
        assert "organization" in serialized
        assert "influence" in serialized
        assert "interest" in serialized
        assert "engagement_priority" in serialized
        assert "is_high_priority" in serialized

    @patch.object(StatusAnalysisProcessor, "_extract_all_data")
    def test_process_successful(
        self,
        mock_extract,
        processor,
        complete_file_set,
        sample_config,
        sample_risks,
        sample_deliverables,
        sample_milestones,
        sample_stakeholders,
    ):
        """Test successful processing."""
        # Setup mock extraction results
        mock_extract.return_value = {
            "risks": sample_risks,
            "deliverables": sample_deliverables,
            "milestones": sample_milestones,
            "stakeholders": sample_stakeholders,
            "warnings": [],
            "extraction_summary": {
                "total_files_processed": len(complete_file_set),
                "risks_extracted": len(sample_risks),
                "deliverables_extracted": len(sample_deliverables),
                "milestones_extracted": len(sample_milestones),
                "stakeholders_extracted": len(sample_stakeholders),
                "warnings_count": 0,
            },
        }

        result = processor.process(complete_file_set, sample_config)

        assert result.success is True
        assert result.operation == "status_analysis"
        assert "project_overview" in result.data
        assert "risk_analysis" in result.data
        assert "deliverable_analysis" in result.data
        assert "milestone_analysis" in result.data
        assert "stakeholder_analysis" in result.data
        assert result.processing_time_seconds >= 0

    def test_process_with_invalid_files(self, processor, sample_config):
        """Test processing with invalid file list."""
        result = processor.process([], sample_config)

        assert result.success is False
        assert len(result.errors) > 0
        assert "Insufficient files" in result.errors[0]

    @patch.object(StatusAnalysisProcessor, "_extract_all_data")
    def test_process_with_extraction_error(
        self, mock_extract, processor, complete_file_set, sample_config
    ):
        """Test processing when extraction fails."""
        mock_extract.side_effect = Exception("Extraction failed")

        result = processor.process(complete_file_set, sample_config)

        assert result.success is False
        assert len(result.errors) > 0
        assert "Extraction failed" in result.errors[0]

    def test_generate_status_report(
        self,
        processor,
        sample_risks,
        sample_deliverables,
        sample_milestones,
        sample_stakeholders,
        complete_file_set,
    ):
        """Test status report generation."""
        # Create a sample project status
        project_status = ProjectStatus(
            project_name="Test Project",
            analysis_timestamp=datetime.now(),
            overall_health_score=0.75,
            total_risks=len(sample_risks),
            total_deliverables=len(sample_deliverables),
            total_milestones=len(sample_milestones),
            total_stakeholders=len(sample_stakeholders),
        )

        extraction_results = {
            "risks": sample_risks,
            "deliverables": sample_deliverables,
            "milestones": sample_milestones,
            "stakeholders": sample_stakeholders,
            "warnings": [],
            "extraction_summary": {"total_files_processed": len(complete_file_set)},
        }

        report = processor._generate_status_report(
            project_status, extraction_results, complete_file_set
        )

        assert "project_overview" in report
        assert "risk_analysis" in report
        assert "deliverable_analysis" in report
        assert "milestone_analysis" in report
        assert "stakeholder_analysis" in report
        assert "critical_issues" in report
        assert "recommendations" in report
        assert "extraction_summary" in report

        # Check project overview structure
        overview = report["project_overview"]
        assert "project_name" in overview
        assert "analysis_date" in overview
        assert "overall_health_score" in overview
        assert "health_percentage" in overview

    @patch("processors.status_analysis.logger")
    def test_logging_behavior(self, mock_logger, processor, complete_file_set, sample_config):
        """Test that appropriate logging occurs during processing."""
        # Mock the extraction to avoid actual file processing
        with patch.object(processor, "_extract_all_data") as mock_extract:
            mock_extract.return_value = {
                "risks": [],
                "deliverables": [],
                "milestones": [],
                "stakeholders": [],
                "warnings": [],
                "extraction_summary": {"total_files_processed": 0},
            }

            processor.process(complete_file_set, sample_config)

            # Verify that info logging occurred
            mock_logger.info.assert_called()

    def test_processing_time_tracking(self, processor, complete_file_set, sample_config):
        """Test that processing time is tracked correctly."""
        # Mock the extraction to make it fast and predictable
        with patch.object(processor, "_extract_all_data") as mock_extract:
            mock_extract.return_value = {
                "risks": [],
                "deliverables": [],
                "milestones": [],
                "stakeholders": [],
                "warnings": [],
                "extraction_summary": {"total_files_processed": 0},
            }

            result = processor.process(complete_file_set, sample_config)

            assert result.success is True
            assert result.processing_time_seconds >= 0
            assert isinstance(result.processing_time_seconds, float)
