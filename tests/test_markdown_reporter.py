"""
Unit tests for MarkdownReporter class.
"""

import os
import tempfile
from datetime import date, datetime
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from core.domain import Deliverable, Milestone, Risk, RiskPriority, RiskStatus, Stakeholder
from core.models import ProcessingResult, ProjectStatus
from reporters.markdown_reporter import MarkdownReporter


class TestMarkdownReporter:
    """Test cases for MarkdownReporter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.reporter = MarkdownReporter()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up temp directory
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init(self):
        """Test reporter initialization."""
        assert self.reporter.reporter_name == "Markdown Reporter"
        assert self.reporter.output_format == "markdown"
        assert self.reporter.file_extension == ".md"

    def test_generate_report_success(self):
        """Test successful report generation."""
        # Create test data
        processing_result = ProcessingResult(
            success=True,
            operation="test_operation",
            data={
                "project_status": {
                    "project_name": "Test Project",
                    "overall_health_score": 0.85,
                    "health_percentage": 85,
                    "total_risks": 5,
                    "high_priority_risks": 2,
                    "total_deliverables": 10,
                    "completed_deliverables": 7,
                    "deliverable_completion_rate": 0.7,
                    "total_milestones": 4,
                    "completed_milestones": 2,
                    "milestone_completion_rate": 0.5,
                    "total_stakeholders": 8,
                }
            },
            processing_time_seconds=2.5,
        )

        config = {
            "title": "Test Report",
            "filename": "test_report",
            "include_timestamp": False,
            "template": "standard",
        }

        # Generate report
        report_path = self.reporter.generate_report(processing_result, self.temp_dir, config)

        # Verify file was created
        assert os.path.exists(report_path)
        assert report_path.endswith(".md")

        # Verify content
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "Test Report" in content
        assert "Test Project" in content
        assert "85%" in content
        assert "test_operation" in content
        assert "✅ Success" in content

    def test_generate_report_with_timestamp(self):
        """Test report generation with timestamp in filename."""
        processing_result = ProcessingResult(
            success=True, operation="test_operation", data={}, processing_time_seconds=1.0
        )

        config = {"filename": "timestamped_report", "include_timestamp": True}

        report_path = self.reporter.generate_report(processing_result, self.temp_dir, config)

        # Verify timestamp is in filename
        filename = Path(report_path).name
        assert "timestamped_report_" in filename
        assert filename.endswith(".md")

    def test_generate_report_invalid_path(self):
        """Test report generation with invalid output path."""
        processing_result = ProcessingResult(
            success=True, operation="test_operation", data={}, processing_time_seconds=1.0
        )

        config = {"filename": "test_report"}

        # Use invalid path that cannot be created (on Windows, use invalid characters)
        invalid_path = "C:\\invalid<>path|with*invalid?chars"

        with pytest.raises(ValueError, match="Failed to generate markdown report"):
            self.reporter.generate_report(processing_result, invalid_path, config)

    def test_format_data_standard_template(self):
        """Test data formatting with standard template."""
        data = {
            "project_status": {
                "project_name": "Test Project",
                "overall_health_score": 0.75,
                "health_percentage": 75,
                "total_risks": 3,
                "high_priority_risks": 1,
            },
            "risks": [
                {
                    "risk_id": "RISK-001",
                    "title": "Test Risk",
                    "priority": "high",
                    "status": "open",
                    "owner": "John Doe",
                    "risk_score": 0.8,
                    "description": "Test risk description",
                    "mitigation_strategy": "Test mitigation",
                }
            ],
        }

        config = {"template": "standard"}

        result = self.reporter.format_data(data, config)

        assert "## Project Status Overview" in result
        assert "Test Project" in result
        assert "75%" in result
        assert "## Risks (1 total)" in result
        assert "RISK-001" in result
        assert "Test Risk" in result
        assert "🟠 High" in result
        assert "🔴 Open" in result

    def test_format_data_detailed_template(self):
        """Test data formatting with detailed template."""
        data = {"project_status": {"project_name": "Detailed Project", "overall_health_score": 0.9}}

        config = {"template": "detailed"}

        result = self.reporter.format_data(data, config)

        assert "## Executive Summary" in result
        assert "## Project Status Overview" in result
        assert "comprehensive analysis" in result

    def test_format_data_summary_template(self):
        """Test data formatting with summary template."""
        data = {
            "project_status": {
                "project_name": "Summary Project",
                "health_percentage": 60,
                "total_risks": 5,
                "high_priority_risks": 2,
                "deliverable_completion_rate": 0.8,
                "milestone_completion_rate": 0.6,
            },
            "risks": [
                {
                    "risk_id": "RISK-001",
                    "title": "Critical Risk",
                    "priority": "critical",
                    "owner": "Jane Doe",
                    "description": "Critical issue",
                }
            ],
        }

        config = {"template": "summary"}

        result = self.reporter.format_data(data, config)

        assert "## Key Metrics" in result
        assert "60%" in result
        assert "## Critical Risks" in result
        assert "Critical Risk" in result

    def test_format_document_check_results(self):
        """Test formatting of document check results."""
        data = {
            "found_files": [
                {"filename": "risk_register.xlsx", "format": "excel", "is_readable": True},
                {"filename": "corrupted_file.xlsx", "format": "excel", "is_readable": False},
            ],
            "missing_files": ["stakeholder_register.xlsx", "project_charter.md"],
        }

        config = {"template": "standard"}

        result = self.reporter.format_data(data, config)

        assert "## Document Check Results" in result
        assert "### Found Documents" in result
        assert "risk_register.xlsx" in result
        assert "✅ Valid" in result
        assert "❌ Invalid" in result
        assert "### Missing Documents" in result
        assert "stakeholder_register.xlsx" in result
        assert "project_charter.md" in result

    def test_format_risks_section(self):
        """Test formatting of risks section."""
        risks = [
            {
                "risk_id": "RISK-001",
                "title": "Budget Risk",
                "priority": "high",
                "status": "open",
                "owner": "PM",
                "risk_score": 0.8,
                "description": "Budget overrun risk",
                "mitigation_strategy": "Monitor spending",
            },
            {
                "risk_id": "RISK-002",
                "title": "Schedule Risk",
                "priority": "medium",
                "status": "mitigated",
                "owner": "Lead Dev",
                "risk_score": 0.4,
            },
        ]

        result = self.reporter._format_risks_section(risks)

        assert "## Risks (2 total)" in result
        assert "RISK-001" in result
        assert "Budget Risk" in result
        assert "🟠 High" in result
        assert "🔴 Open" in result
        assert "### High Priority Risks" in result
        assert "Budget overrun risk" in result
        assert "Monitor spending" in result

    def test_format_deliverables_section(self):
        """Test formatting of deliverables section."""
        deliverables = [
            {
                "deliverable_id": "DEL-001",
                "name": "Requirements Doc",
                "status": "completed",
                "completion_percentage": 100.0,
                "due_date": "2024-02-01",
                "assigned_to": "Analyst",
            },
            {
                "deliverable_id": "DEL-002",
                "name": "Design Doc",
                "status": "in_progress",
                "completion_percentage": 60.0,
                "due_date": "2024-03-01",
                "assigned_to": "Designer",
            },
        ]

        result = self.reporter._format_deliverables_section(deliverables)

        assert "## Deliverables (2 total)" in result
        assert "DEL-001" in result
        assert "Requirements Doc" in result
        assert "✅ Completed" in result
        assert "100.0%" in result
        assert "60.0%" in result

    def test_format_milestones_section(self):
        """Test formatting of milestones section."""
        milestones = [
            {
                "milestone_id": "MS-001",
                "name": "Project Kickoff",
                "target_date": "2024-01-15",
                "status": "completed",
                "owner": "PM",
            },
            {
                "milestone_id": "MS-002",
                "name": "Design Review",
                "target_date": "2024-02-15",
                "status": "upcoming",
                "owner": "Lead Architect",
            },
        ]

        result = self.reporter._format_milestones_section(milestones)

        assert "## Milestones (2 total)" in result
        assert "MS-001" in result
        assert "Project Kickoff" in result
        assert "✅ Completed" in result
        assert "⚪ Upcoming" in result

    def test_format_stakeholders_section(self):
        """Test formatting of stakeholders section."""
        stakeholders = [
            {
                "name": "John Smith",
                "role": "Project Sponsor",
                "influence": "very_high",
                "interest": "high",
                "engagement_priority": "Manage Closely",
            },
            {
                "name": "Jane Doe",
                "role": "End User",
                "influence": "low",
                "interest": "high",
                "engagement_priority": "Keep Informed",
            },
        ]

        result = self.reporter._format_stakeholders_section(stakeholders)

        assert "## Stakeholders (2 total)" in result
        assert "John Smith" in result
        assert "Project Sponsor" in result
        assert "Very High" in result
        assert "Manage Closely" in result

    def test_format_learning_content(self):
        """Test formatting of learning content."""
        content = {
            "modules": [
                {
                    "title": "Risk Management Basics",
                    "content": "This module covers the fundamentals of risk management...",
                },
                {
                    "title": "Stakeholder Analysis",
                    "content": "Learn how to identify and analyze stakeholders...",
                },
            ]
        }

        result = self.reporter._format_learning_content(content)

        assert "## Learning Content" in result
        assert "### Risk Management Basics" in result
        assert "fundamentals of risk management" in result
        assert "### Stakeholder Analysis" in result
        assert "identify and analyze stakeholders" in result

    def test_format_empty_sections(self):
        """Test formatting of empty data sections."""
        # Test empty risks
        result = self.reporter._format_risks_section([])
        assert "No risks found in the analysis" in result

        # Test empty deliverables
        result = self.reporter._format_deliverables_section([])
        assert "No deliverables found in the analysis" in result

        # Test empty milestones
        result = self.reporter._format_milestones_section([])
        assert "No milestones found in the analysis" in result

        # Test empty stakeholders
        result = self.reporter._format_stakeholders_section([])
        assert "No stakeholders found in the analysis" in result

    def test_priority_icons(self):
        """Test priority icon mapping."""
        assert self.reporter._get_priority_icon("low") == "🟢"
        assert self.reporter._get_priority_icon("medium") == "🟡"
        assert self.reporter._get_priority_icon("high") == "🟠"
        assert self.reporter._get_priority_icon("critical") == "🔴"
        assert self.reporter._get_priority_icon("unknown") == "⚪"

    def test_status_icons(self):
        """Test status icon mapping."""
        assert self.reporter._get_status_icon("open") == "🔴"
        assert self.reporter._get_status_icon("in_progress") == "🟡"
        assert self.reporter._get_status_icon("mitigated") == "🟢"
        assert self.reporter._get_status_icon("closed") == "✅"
        assert self.reporter._get_status_icon("accepted") == "🔵"
        assert self.reporter._get_status_icon("unknown") == "⚪"

    def test_deliverable_status_icons(self):
        """Test deliverable status icon mapping."""
        assert self.reporter._get_deliverable_status_icon("not_started") == "⚪"
        assert self.reporter._get_deliverable_status_icon("in_progress") == "🟡"
        assert self.reporter._get_deliverable_status_icon("completed") == "✅"
        assert self.reporter._get_deliverable_status_icon("on_hold") == "⏸️"
        assert self.reporter._get_deliverable_status_icon("cancelled") == "❌"

    def test_milestone_status_icons(self):
        """Test milestone status icon mapping."""
        assert self.reporter._get_milestone_status_icon("upcoming") == "⚪"
        assert self.reporter._get_milestone_status_icon("in_progress") == "🟡"
        assert self.reporter._get_milestone_status_icon("completed") == "✅"
        assert self.reporter._get_milestone_status_icon("overdue") == "🔴"
        assert self.reporter._get_milestone_status_icon("cancelled") == "❌"

    def test_handle_processing_errors(self):
        """Test error handling in reports."""
        processing_result = ProcessingResult(
            success=False,
            operation="test_operation",
            data={},
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"],
            processing_time_seconds=1.0,
        )

        error_section = self.reporter.handle_processing_errors(processing_result)

        assert "## Errors" in error_section
        assert "1. Error 1" in error_section
        assert "2. Error 2" in error_section
        assert "## Warnings" in error_section
        assert "1. Warning 1" in error_section

    def test_extract_overdue_items(self):
        """Test extraction of overdue items."""
        data = {
            "milestones": [
                {"name": "Milestone 1", "is_overdue": True, "target_date": "2024-01-01"},
                {"name": "Milestone 2", "is_overdue": False, "target_date": "2024-03-01"},
            ],
            "deliverables": [
                {"name": "Deliverable 1", "is_overdue": True, "due_date": "2024-01-15"},
                {"name": "Deliverable 2", "is_overdue": False, "due_date": "2024-04-01"},
            ],
        }

        overdue = self.reporter._extract_overdue_items(data)

        assert len(overdue["milestones"]) == 1
        assert overdue["milestones"][0]["name"] == "Milestone 1"
        assert len(overdue["deliverables"]) == 1
        assert overdue["deliverables"][0]["name"] == "Deliverable 1"

    def test_format_overdue_items(self):
        """Test formatting of overdue items."""
        overdue_items = {
            "milestones": [{"name": "Late Milestone", "target_date": "2024-01-01"}],
            "deliverables": [{"name": "Late Deliverable", "due_date": "2024-01-15"}],
        }

        result = self.reporter._format_overdue_items(overdue_items)

        assert "## Overdue Items" in result
        assert "### Overdue Milestones" in result
        assert "Late Milestone" in result
        assert "### Overdue Deliverables" in result
        assert "Late Deliverable" in result

    def test_executive_summary_formatting(self):
        """Test executive summary formatting."""
        data = {"project_status": {"overall_health_score": 0.9}}

        result = self.reporter._format_executive_summary(data)

        assert "## Executive Summary" in result
        assert "comprehensive analysis" in result
        assert "✅ **Project Health:**" in result
        assert "performing well" in result

    def test_key_metrics_formatting(self):
        """Test key metrics formatting."""
        data = {
            "project_status": {
                "health_percentage": 85,
                "total_risks": 10,
                "high_priority_risks": 3,
                "deliverable_completion_rate": 0.75,
                "milestone_completion_rate": 0.6,
            }
        }

        result = self.reporter._format_key_metrics(data)

        assert "## Key Metrics" in result
        assert "85%" in result
        assert "10" in result
        assert "3" in result
        assert "75.0%" in result
        assert "60.0%" in result

    def test_analysis_section_formatting(self):
        """Test analysis section formatting."""
        data = {
            "risks": [{"priority": "high"}, {"priority": "medium"}, {"priority": "critical"}],
            "milestones": [
                {"status": "completed"},
                {"status": "upcoming"},
                {"status": "completed"},
            ],
        }

        result = self.reporter._format_analysis_section(data)

        assert "## Analysis & Recommendations" in result
        assert "### Risk Analysis" in result
        assert "Total risks identified: 3" in result
        assert "High/Critical priority risks: 2" in result
        assert "### Schedule Analysis" in result
        assert "Total milestones: 3" in result
        assert "Completed milestones: 2" in result

    def test_get_supported_config_options(self):
        """Test getting supported configuration options."""
        options = self.reporter.get_supported_config_options()

        # Check base options are included
        assert "include_timestamp" in options
        assert "include_errors" in options
        assert "template" in options

        # Check markdown-specific options
        assert "title" in options
        assert "filename" in options
        assert "include_icons" in options
        assert "show_details" in options

        # Verify option structure
        assert options["title"]["type"] == str
        assert options["title"]["default"] == "Project Management Analysis Report"
        assert "description" in options["title"]

    def test_create_report_header(self):
        """Test report header creation."""
        processing_result = ProcessingResult(
            success=True,
            operation="status_analysis",
            file_path=Path("test_file.xlsx"),
            processing_time_seconds=3.5,
        )

        config = {"title": "Custom Report Title"}

        header = self.reporter._create_report_header(processing_result, config)

        assert "# Custom Report Title" in header
        assert "**Operation:** status_analysis" in header
        assert "**Status:** ✅ Success" in header
        assert "**Processing Time:** 3.50 seconds" in header
        assert "**Source File:** test_file.xlsx" in header

    def test_format_critical_risks(self):
        """Test formatting of critical risks."""
        risks = [
            {
                "title": "Critical Issue 1",
                "priority": "critical",
                "owner": "Risk Manager",
                "description": "This is a critical issue",
            },
            {
                "title": "High Priority Issue",
                "priority": "high",
                "owner": "Project Manager",
                "description": "This is a high priority issue",
            },
        ]

        result = self.reporter._format_critical_risks(risks)

        assert "## Critical Risks" in result
        assert "### Critical Issue 1" in result
        assert "**Priority:** Critical" in result
        assert "**Owner:** Risk Manager" in result
        assert "**Description:** This is a critical issue" in result
        assert "### High Priority Issue" in result

    def test_string_representations(self):
        """Test string representation methods."""
        str_repr = str(self.reporter)
        assert "Markdown Reporter (markdown)" == str_repr

        repr_str = repr(self.reporter)
        assert "MarkdownReporter(" in repr_str
        assert "reporter_name='Markdown Reporter'" in repr_str
        assert "output_format='markdown'" in repr_str
        assert "file_extension='.md'" in repr_str
