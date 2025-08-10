"""
Unit tests for the MilestoneExtractor class.

This module contains comprehensive tests for milestone data extraction from various
document formats including Markdown, Excel, and Microsoft Project files.
"""

from datetime import date, datetime
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from core.domain import Milestone, MilestoneStatus
from extractors.milestone_extractor import MilestoneExtractor
from utils.exceptions import DataExtractionError


class TestMilestoneExtractor:
    """Test cases for MilestoneExtractor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = MilestoneExtractor()

    def test_init(self):
        """Test MilestoneExtractor initialization."""
        assert self.extractor.markdown_handler is not None
        assert self.extractor.excel_handler is not None
        assert self.extractor.mpp_handler is not None
        assert len(self.extractor.milestone_keywords) > 0
        assert "milestone" in self.extractor.milestone_keywords
        assert "deadline" in self.extractor.milestone_keywords

    def test_extract_milestones_file_not_found(self):
        """Test extract_milestones with non-existent file."""
        with pytest.raises(DataExtractionError, match="File not found"):
            self.extractor.extract_milestones("nonexistent_file.md")

    @patch("pathlib.Path.exists")
    def test_extract_milestones_unsupported_format(self, mock_exists):
        """Test extract_milestones with unsupported file format."""
        mock_exists.return_value = True

        with pytest.raises(DataExtractionError, match="Unsupported file format"):
            self.extractor.extract_milestones("test.txt")

    @patch("pathlib.Path.exists")
    @patch.object(MilestoneExtractor, "_extract_from_markdown")
    def test_extract_milestones_markdown(self, mock_extract_md, mock_exists):
        """Test extract_milestones with Markdown file."""
        mock_exists.return_value = True
        mock_milestone = Milestone(
            milestone_id="M001",
            name="Test Milestone",
            description="Test Description",
            target_date=date(2025, 12, 31),
            status=MilestoneStatus.UPCOMING,
            owner="Test Owner",
        )
        mock_extract_md.return_value = [mock_milestone]

        milestones = self.extractor.extract_milestones("test.md")

        assert len(milestones) == 1
        assert milestones[0].milestone_id == "M001"
        mock_extract_md.assert_called_once_with("test.md")

    @patch("pathlib.Path.exists")
    @patch.object(MilestoneExtractor, "_extract_from_excel")
    def test_extract_milestones_excel(self, mock_extract_excel, mock_exists):
        """Test extract_milestones with Excel file."""
        mock_exists.return_value = True
        mock_milestone = Milestone(
            milestone_id="M002",
            name="Excel Milestone",
            description="Excel Description",
            target_date=date(2025, 6, 30),
            status=MilestoneStatus.IN_PROGRESS,
            owner="Excel Owner",
        )
        mock_extract_excel.return_value = [mock_milestone]

        milestones = self.extractor.extract_milestones("test.xlsx")

        assert len(milestones) == 1
        assert milestones[0].milestone_id == "M002"
        mock_extract_excel.assert_called_once_with("test.xlsx")

    @patch("pathlib.Path.exists")
    @patch.object(MilestoneExtractor, "_extract_from_mpp")
    def test_extract_milestones_mpp(self, mock_extract_mpp, mock_exists):
        """Test extract_milestones with MPP file."""
        mock_exists.return_value = True
        mock_milestone = Milestone(
            milestone_id="M003",
            name="MPP Milestone",
            description="MPP Description",
            target_date=date(2025, 9, 15),
            status=MilestoneStatus.COMPLETED,
            owner="MPP Owner",
        )
        mock_extract_mpp.return_value = [mock_milestone]

        milestones = self.extractor.extract_milestones("test.mpp")

        assert len(milestones) == 1
        assert milestones[0].milestone_id == "M003"
        mock_extract_mpp.assert_called_once_with("test.mpp")


class TestMilestoneExtractionFromMPP:
    """Test cases for MPP milestone extraction."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = MilestoneExtractor()

    def test_is_milestone_task_by_flag(self):
        """Test milestone task identification by is_milestone flag."""
        task = {"is_milestone": True, "name": "Test Task"}
        assert self.extractor._is_milestone_task(task)

    def test_is_milestone_task_by_duration(self):
        """Test milestone task identification by zero duration."""
        task = {"duration": 0, "name": "Test Task"}
        assert self.extractor._is_milestone_task(task)

    def test_is_milestone_task_by_name(self):
        """Test milestone task identification by name keywords."""
        task = {"name": "Project Milestone Review", "duration": 5}
        assert self.extractor._is_milestone_task(task)

        task = {"name": "Regular Task", "duration": 5}
        assert not self.extractor._is_milestone_task(task)

    def test_create_milestone_from_mpp_task(self):
        """Test creating milestone from MPP task."""
        task = {
            "id": "T001",
            "unique_id": 123,
            "name": "Project Completion",
            "notes": "Final project milestone",
            "finish_date": "2025-12-31",
            "start_date": "2025-12-31",
            "actual_finish": None,
            "resource_names": ["Project Manager", "Team Lead"],
            "predecessors": ["T100", "T101"],
            "percent_complete": 0,
        }

        milestone = self.extractor._create_milestone_from_mpp_task(task)

        assert milestone is not None
        assert milestone.milestone_id == "T001"
        assert milestone.name == "Project Completion"
        assert milestone.description == "Final project milestone"
        assert milestone.owner == "Project Manager, Team Lead"
        assert milestone.dependencies == ["T100", "T101"]
        assert milestone.status == MilestoneStatus.UPCOMING


class TestMilestoneExtractionFromMarkdown:
    """Test cases for Markdown milestone extraction."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = MilestoneExtractor()

    @patch.object(MilestoneExtractor, "_extract_from_table_data")
    def test_extract_from_markdown_with_tables(self, mock_extract_table):
        """Test extraction from Markdown with tables."""
        mock_data = {
            "tables": [
                {
                    "headers": ["Milestone ID", "Name", "Target Date", "Status"],
                    "rows": [
                        {
                            "Milestone ID": "M001",
                            "Name": "Test Milestone",
                            "Target Date": "2025-12-31",
                            "Status": "Upcoming",
                        }
                    ],
                }
            ],
            "sections": [],
            "raw_content": "Test content",
        }

        mock_milestone = Milestone(
            milestone_id="M001",
            name="Test Milestone",
            description="Test Milestone",
            target_date=date(2025, 12, 31),
            status=MilestoneStatus.UPCOMING,
            owner="",
        )
        mock_extract_table.return_value = [mock_milestone]

        with patch.object(self.extractor.markdown_handler, "extract_data", return_value=mock_data):
            milestones = self.extractor._extract_from_markdown("test.md")

        assert len(milestones) == 1
        assert milestones[0].milestone_id == "M001"
        mock_extract_table.assert_called_once()


class TestMilestoneExtractionFromExcel:
    """Test cases for Excel milestone extraction."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = MilestoneExtractor()

    @patch.object(MilestoneExtractor, "_is_milestone_sheet")
    @patch.object(MilestoneExtractor, "_extract_from_excel_sheet")
    def test_extract_from_excel(self, mock_extract_sheet, mock_is_milestone_sheet):
        """Test extraction from Excel file."""
        mock_data = {
            "sheets": {
                "Milestones": {"data": [["Milestone ID", "Name"], ["M001", "Test Milestone"]]},
                "Other Sheet": {"data": [["Col1", "Col2"], ["Data1", "Data2"]]},
            }
        }

        mock_is_milestone_sheet.side_effect = lambda name, data: name == "Milestones"
        mock_milestone = Milestone(
            milestone_id="M001",
            name="Test Milestone",
            description="Test Milestone",
            target_date=date.today(),
            status=MilestoneStatus.UPCOMING,
            owner="",
        )
        mock_extract_sheet.return_value = [mock_milestone]

        with patch.object(self.extractor.excel_handler, "extract_data", return_value=mock_data):
            milestones = self.extractor._extract_from_excel("test.xlsx")

        assert len(milestones) == 1
        assert milestones[0].milestone_id == "M001"
        mock_extract_sheet.assert_called_once()

    def test_is_milestone_sheet_by_name(self):
        """Test milestone sheet identification by name."""
        assert self.extractor._is_milestone_sheet("Milestones", {})
        assert self.extractor._is_milestone_sheet("Timeline", {})
        assert self.extractor._is_milestone_sheet("Deadlines", {})
        assert not self.extractor._is_milestone_sheet("Budget", {})

    def test_is_milestone_sheet_by_headers(self):
        """Test milestone sheet identification by headers."""
        sheet_data = {
            "data": [
                ["Milestone ID", "Target Date", "Name", "Status"],
                ["M001", "2025-12-31", "Test Milestone", "Upcoming"],
            ]
        }

        assert self.extractor._is_milestone_sheet("Sheet1", sheet_data)

        sheet_data_no_milestone = {"data": [["Name", "Age", "Department"], ["John", "30", "IT"]]}

        assert not self.extractor._is_milestone_sheet("Sheet1", sheet_data_no_milestone)


class TestColumnMapping:
    """Test cases for column mapping functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = MilestoneExtractor()

    def test_create_column_mapping(self):
        """Test column mapping creation."""
        headers = ["Milestone ID", "Name", "Description", "Target Date", "Status", "Owner"]
        mapping = self.extractor._create_column_mapping(headers)

        assert mapping["milestone_id"] == "Milestone ID"
        assert mapping["name"] == "Name"
        assert mapping["description"] == "Description"
        assert mapping["target_date"] == "Target Date"
        assert mapping["status"] == "Status"
        assert mapping["owner"] == "Owner"

    def test_create_column_mapping_variations(self):
        """Test column mapping with header variations."""
        headers = ["ID", "Title", "Desc", "Due Date", "State", "Responsible"]
        mapping = self.extractor._create_column_mapping(headers)

        assert mapping["milestone_id"] == "ID"
        assert mapping["name"] == "Title"
        assert mapping["description"] == "Desc"
        assert mapping["target_date"] == "Due Date"
        assert mapping["status"] == "State"
        assert mapping["owner"] == "Responsible"


class TestMilestoneCreation:
    """Test cases for Milestone object creation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = MilestoneExtractor()

    def test_create_milestone_from_row_complete(self):
        """Test creating milestone from complete row data."""
        row = {
            "milestone id": "M001",
            "name": "Test Milestone",
            "description": "Test Description",
            "target date": "2025-12-31",
            "status": "In Progress",
            "owner": "John Doe",
        }

        headers = list(row.keys())
        column_mapping = self.extractor._create_column_mapping(headers)

        milestone = self.extractor._create_milestone_from_row(row, column_mapping, headers)

        assert milestone is not None
        assert milestone.milestone_id == "M001"
        assert milestone.name == "Test Milestone"
        assert milestone.description == "Test Description"
        assert milestone.target_date == date(2025, 12, 31)
        assert milestone.status == MilestoneStatus.IN_PROGRESS
        assert milestone.owner == "John Doe"

    def test_create_milestone_from_row_minimal(self):
        """Test creating milestone from minimal row data."""
        row = {"name": "Minimal Milestone"}

        headers = list(row.keys())
        column_mapping = self.extractor._create_column_mapping(headers)

        milestone = self.extractor._create_milestone_from_row(row, column_mapping, headers)

        assert milestone is not None
        assert milestone.name == "Minimal Milestone"
        assert milestone.status == MilestoneStatus.UPCOMING
        assert milestone.owner == ""
        assert milestone.target_date == date.today()


class TestValueParsing:
    """Test cases for value parsing methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = MilestoneExtractor()

    def test_parse_status(self):
        """Test status parsing."""
        assert self.extractor._parse_status("Upcoming") == MilestoneStatus.UPCOMING
        assert self.extractor._parse_status("In Progress") == MilestoneStatus.IN_PROGRESS
        assert self.extractor._parse_status("Completed") == MilestoneStatus.COMPLETED
        assert self.extractor._parse_status("Overdue") == MilestoneStatus.OVERDUE
        assert self.extractor._parse_status("Cancelled") == MilestoneStatus.CANCELLED
        assert self.extractor._parse_status("Unknown") == MilestoneStatus.UPCOMING  # Default

    def test_parse_date_formats(self):
        """Test date parsing from various formats."""
        test_date = date(2025, 3, 15)

        assert self.extractor._parse_date("2025-03-15") == test_date
        assert self.extractor._parse_date("03/15/2025") == test_date
        assert self.extractor._parse_date("15/03/2025") == test_date

        # Test datetime object
        test_datetime = datetime(2025, 3, 15, 10, 30)
        assert self.extractor._parse_date(test_datetime) == test_date

        # Test date object
        assert self.extractor._parse_date(test_date) == test_date

        # Invalid date should return None
        assert self.extractor._parse_date("invalid-date") is None
        assert self.extractor._parse_date("") is None
        assert self.extractor._parse_date(None) is None

    def test_parse_dependencies(self):
        """Test dependencies parsing."""
        assert self.extractor._parse_dependencies("M001, M002") == ["M001", "M002"]
        assert self.extractor._parse_dependencies("M001; M002") == ["M001", "M002"]
        assert self.extractor._parse_dependencies("M001|M002") == ["M001", "M002"]
        assert self.extractor._parse_dependencies("") == []
        assert self.extractor._parse_dependencies(None) == []

    def test_determine_status_from_task(self):
        """Test status determination from MPP task."""
        # Completed task
        task = {"percent_complete": 100}
        assert self.extractor._determine_status_from_task(task) == MilestoneStatus.COMPLETED

        # In progress task
        task = {"percent_complete": 50}
        assert self.extractor._determine_status_from_task(task) == MilestoneStatus.IN_PROGRESS

        # Overdue task
        yesterday = date.today().replace(day=date.today().day - 1)
        task = {"percent_complete": 0, "finish_date": yesterday.strftime("%Y-%m-%d")}
        assert self.extractor._determine_status_from_task(task) == MilestoneStatus.OVERDUE

        # Upcoming task
        task = {"percent_complete": 0}
        assert self.extractor._determine_status_from_task(task) == MilestoneStatus.UPCOMING


class TestTextExtraction:
    """Test cases for text-based milestone extraction."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = MilestoneExtractor()

    def test_find_milestone_entries_in_text(self):
        """Test finding milestone entries in text."""
        content = """
        Milestone M001: Project Kickoff
        Target Date: 2025-01-15
        Status: Completed
        
        ---
        
        Deadline: System Go-Live
        This milestone marks the system deployment
        Date: 2025-06-30
        
        ===
        
        Regular task without milestone keywords
        This should not be detected
        """

        entries = self.extractor._find_milestone_entries_in_text(content)

        assert len(entries) >= 2  # Should find at least 2 milestone-related sections
        assert any("project kickoff" in entry.lower() for entry in entries)
        assert any("system go-live" in entry.lower() for entry in entries)

    def test_create_milestone_from_text_entry(self):
        """Test creating milestone from text entry."""
        entry = """
        Milestone M001: System Integration Complete
        Target Date: 2025-08-15
        Status: In Progress
        Owner: Integration Team
        Dependencies: M100, M101
        
        This milestone represents the completion of all system
        integration activities and successful testing.
        """

        milestone = self.extractor._create_milestone_from_text_entry(entry)

        assert milestone is not None
        assert milestone.milestone_id == "M001"
        assert "System Integration Complete" in milestone.name
        assert milestone.target_date == date(2025, 8, 15)
        assert milestone.status == MilestoneStatus.IN_PROGRESS
        assert milestone.owner == "Integration Team"
        assert milestone.dependencies == ["M100", "M101"]

    def test_create_milestone_from_text_entry_minimal(self):
        """Test creating milestone from minimal text entry."""
        entry = "Project completion deadline"

        milestone = self.extractor._create_milestone_from_text_entry(entry)

        assert milestone is not None
        assert milestone.name == "Project completion deadline"
        assert milestone.description == entry
        assert milestone.status == MilestoneStatus.UPCOMING
        assert milestone.owner == ""
        assert milestone.target_date == date.today()


if __name__ == "__main__":
    pytest.main([__file__])
