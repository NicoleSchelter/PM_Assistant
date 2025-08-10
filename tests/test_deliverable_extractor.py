"""
Unit tests for the DeliverableExtractor class.

This module contains comprehensive tests for deliverable data extraction from various
document formats including Markdown and Excel files.
"""

from datetime import date, datetime
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from core.domain import Deliverable, DeliverableStatus
from extractors.deliverable_extractor import DeliverableExtractor
from utils.exceptions import DataExtractionError


class TestDeliverableExtractor:
    """Test cases for DeliverableExtractor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = DeliverableExtractor()

    def test_init(self):
        """Test DeliverableExtractor initialization."""
        assert self.extractor.markdown_handler is not None
        assert self.extractor.excel_handler is not None
        assert len(self.extractor.deliverable_keywords) > 0
        assert "deliverable" in self.extractor.deliverable_keywords
        assert "wbs" in self.extractor.deliverable_keywords

    def test_extract_deliverables_file_not_found(self):
        """Test extract_deliverables with non-existent file."""
        with pytest.raises(DataExtractionError, match="File not found"):
            self.extractor.extract_deliverables("nonexistent_file.md")

    @patch("pathlib.Path.exists")
    def test_extract_deliverables_unsupported_format(self, mock_exists):
        """Test extract_deliverables with unsupported file format."""
        mock_exists.return_value = True

        with pytest.raises(DataExtractionError, match="Unsupported file format"):
            self.extractor.extract_deliverables("test.txt")

    @patch("pathlib.Path.exists")
    @patch.object(DeliverableExtractor, "_extract_from_markdown")
    def test_extract_deliverables_markdown(self, mock_extract_md, mock_exists):
        """Test extract_deliverables with Markdown file."""
        mock_exists.return_value = True
        mock_deliverable = Deliverable(
            deliverable_id="D001",
            name="Test Deliverable",
            description="Test Description",
            wbs_code="1.1",
            status=DeliverableStatus.NOT_STARTED,
            assigned_to="Test Owner",
        )
        mock_extract_md.return_value = [mock_deliverable]

        deliverables = self.extractor.extract_deliverables("test.md")

        assert len(deliverables) == 1
        assert deliverables[0].deliverable_id == "D001"
        mock_extract_md.assert_called_once_with("test.md")

    @patch("pathlib.Path.exists")
    @patch.object(DeliverableExtractor, "_extract_from_excel")
    def test_extract_deliverables_excel(self, mock_extract_excel, mock_exists):
        """Test extract_deliverables with Excel file."""
        mock_exists.return_value = True
        mock_deliverable = Deliverable(
            deliverable_id="D002",
            name="Excel Deliverable",
            description="Excel Description",
            wbs_code="2.1",
            status=DeliverableStatus.IN_PROGRESS,
            assigned_to="Excel Owner",
        )
        mock_extract_excel.return_value = [mock_deliverable]

        deliverables = self.extractor.extract_deliverables("test.xlsx")

        assert len(deliverables) == 1
        assert deliverables[0].deliverable_id == "D002"
        mock_extract_excel.assert_called_once_with("test.xlsx")


class TestDeliverableExtractionFromMarkdown:
    """Test cases for Markdown deliverable extraction."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = DeliverableExtractor()

    @patch.object(DeliverableExtractor, "_extract_from_table_data")
    def test_extract_from_markdown_with_tables(self, mock_extract_table):
        """Test extraction from Markdown with tables."""
        mock_data = {
            "tables": [
                {
                    "headers": ["Deliverable ID", "Name", "WBS Code", "Status"],
                    "rows": [
                        {
                            "Deliverable ID": "D001",
                            "Name": "Test Deliverable",
                            "WBS Code": "1.1",
                            "Status": "Not Started",
                        }
                    ],
                }
            ],
            "sections": [],
            "raw_content": "Test content",
        }

        mock_deliverable = Deliverable(
            deliverable_id="D001",
            name="Test Deliverable",
            description="Test Deliverable",
            wbs_code="1.1",
            status=DeliverableStatus.NOT_STARTED,
            assigned_to="",
        )
        mock_extract_table.return_value = [mock_deliverable]

        with patch.object(self.extractor.markdown_handler, "extract_data", return_value=mock_data):
            deliverables = self.extractor._extract_from_markdown("test.md")

        assert len(deliverables) == 1
        assert deliverables[0].deliverable_id == "D001"
        mock_extract_table.assert_called_once()


class TestDeliverableExtractionFromExcel:
    """Test cases for Excel deliverable extraction."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = DeliverableExtractor()

    @patch.object(DeliverableExtractor, "_is_deliverable_sheet")
    @patch.object(DeliverableExtractor, "_extract_from_excel_sheet")
    def test_extract_from_excel(self, mock_extract_sheet, mock_is_deliverable_sheet):
        """Test extraction from Excel file."""
        mock_data = {
            "sheets": {
                "WBS": {"data": [["Deliverable ID", "Name"], ["D001", "Test Deliverable"]]},
                "Other Sheet": {"data": [["Col1", "Col2"], ["Data1", "Data2"]]},
            }
        }

        mock_is_deliverable_sheet.side_effect = lambda name, data: name == "WBS"
        mock_deliverable = Deliverable(
            deliverable_id="D001",
            name="Test Deliverable",
            description="Test Deliverable",
            wbs_code="D001",
            status=DeliverableStatus.NOT_STARTED,
            assigned_to="",
        )
        mock_extract_sheet.return_value = [mock_deliverable]

        with patch.object(self.extractor.excel_handler, "extract_data", return_value=mock_data):
            deliverables = self.extractor._extract_from_excel("test.xlsx")

        assert len(deliverables) == 1
        assert deliverables[0].deliverable_id == "D001"
        mock_extract_sheet.assert_called_once()

    def test_is_deliverable_sheet_by_name(self):
        """Test deliverable sheet identification by name."""
        assert self.extractor._is_deliverable_sheet("WBS", {})
        assert self.extractor._is_deliverable_sheet("Deliverables", {})
        assert self.extractor._is_deliverable_sheet("Work Breakdown", {})
        assert not self.extractor._is_deliverable_sheet("Budget", {})

    def test_is_deliverable_sheet_by_headers(self):
        """Test deliverable sheet identification by headers."""
        sheet_data = {
            "data": [
                ["Deliverable ID", "WBS Code", "Name", "Status"],
                ["D001", "1.1", "Test Deliverable", "Not Started"],
            ]
        }

        assert self.extractor._is_deliverable_sheet("Sheet1", sheet_data)

        sheet_data_no_deliverable = {"data": [["Name", "Age", "Department"], ["John", "30", "IT"]]}

        assert not self.extractor._is_deliverable_sheet("Sheet1", sheet_data_no_deliverable)


class TestColumnMapping:
    """Test cases for column mapping functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = DeliverableExtractor()

    def test_create_column_mapping(self):
        """Test column mapping creation."""
        headers = ["Deliverable ID", "Name", "Description", "WBS Code", "Status", "Assigned To"]
        mapping = self.extractor._create_column_mapping(headers)

        assert mapping["deliverable_id"] == "Deliverable ID"
        assert mapping["name"] == "Name"
        assert mapping["description"] == "Description"
        assert mapping["wbs_code"] == "WBS Code"
        assert mapping["status"] == "Status"
        assert mapping["assigned_to"] == "Assigned To"

    def test_create_column_mapping_variations(self):
        """Test column mapping with header variations."""
        headers = ["ID", "Title", "Desc", "Code", "State", "Owner"]
        mapping = self.extractor._create_column_mapping(headers)

        assert mapping["deliverable_id"] == "ID"
        assert mapping["name"] == "Title"
        assert mapping["description"] == "Desc"
        assert mapping["wbs_code"] == "Code"
        assert mapping["status"] == "State"
        assert mapping["assigned_to"] == "Owner"


class TestDeliverableCreation:
    """Test cases for Deliverable object creation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = DeliverableExtractor()

    def test_create_deliverable_from_row_complete(self):
        """Test creating deliverable from complete row data."""
        row = {
            "deliverable id": "D001",
            "name": "Test Deliverable",
            "description": "Test Description",
            "wbs code": "1.1",
            "status": "In Progress",
            "assigned to": "John Doe",
            "completion": "50%",
        }

        headers = list(row.keys())
        column_mapping = self.extractor._create_column_mapping(headers)

        deliverable = self.extractor._create_deliverable_from_row(row, column_mapping, headers)

        assert deliverable is not None
        assert deliverable.deliverable_id == "D001"
        assert deliverable.name == "Test Deliverable"
        assert deliverable.description == "Test Description"
        assert deliverable.wbs_code == "1.1"
        assert deliverable.status == DeliverableStatus.IN_PROGRESS
        assert deliverable.assigned_to == "John Doe"
        assert deliverable.completion_percentage == 50.0

    def test_create_deliverable_from_row_minimal(self):
        """Test creating deliverable from minimal row data."""
        row = {"name": "Minimal Deliverable"}

        headers = list(row.keys())
        column_mapping = self.extractor._create_column_mapping(headers)

        deliverable = self.extractor._create_deliverable_from_row(row, column_mapping, headers)

        assert deliverable is not None
        assert deliverable.name == "Minimal Deliverable"
        assert deliverable.status == DeliverableStatus.NOT_STARTED
        assert deliverable.assigned_to == ""
        assert deliverable.completion_percentage == 0.0


class TestValueParsing:
    """Test cases for value parsing methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = DeliverableExtractor()

    def test_parse_status(self):
        """Test status parsing."""
        assert self.extractor._parse_status("Not Started") == DeliverableStatus.NOT_STARTED
        assert self.extractor._parse_status("In Progress") == DeliverableStatus.IN_PROGRESS
        assert self.extractor._parse_status("Completed") == DeliverableStatus.COMPLETED
        assert self.extractor._parse_status("On Hold") == DeliverableStatus.ON_HOLD
        assert self.extractor._parse_status("Cancelled") == DeliverableStatus.CANCELLED
        assert self.extractor._parse_status("Unknown") == DeliverableStatus.NOT_STARTED  # Default

    def test_parse_completion_percentage(self):
        """Test completion percentage parsing."""
        assert self.extractor._parse_completion_percentage("50%") == 50.0
        assert self.extractor._parse_completion_percentage("0.75") == 75.0
        assert self.extractor._parse_completion_percentage("100") == 100.0
        assert self.extractor._parse_completion_percentage("") == 0.0
        assert self.extractor._parse_completion_percentage(None) == 0.0

    def test_parse_effort_hours(self):
        """Test effort hours parsing."""
        assert self.extractor._parse_effort_hours("40") == 40.0
        assert self.extractor._parse_effort_hours("40.5") == 40.5
        assert self.extractor._parse_effort_hours("40 hours") == 40.0
        assert self.extractor._parse_effort_hours("") is None
        assert self.extractor._parse_effort_hours(None) is None

    def test_parse_dependencies(self):
        """Test dependencies parsing."""
        assert self.extractor._parse_dependencies("D001, D002") == ["D001", "D002"]
        assert self.extractor._parse_dependencies("D001; D002") == ["D001", "D002"]
        assert self.extractor._parse_dependencies("D001|D002") == ["D001", "D002"]
        assert self.extractor._parse_dependencies("") == []
        assert self.extractor._parse_dependencies(None) == []

    def test_parse_date_formats(self):
        """Test date parsing from various formats."""
        test_date = date(2025, 3, 15)

        assert self.extractor._parse_date("2025-03-15") == test_date
        assert self.extractor._parse_date("03/15/2025") == test_date
        assert self.extractor._parse_date("15/03/2025") == test_date

        # Invalid date should return None
        assert self.extractor._parse_date("invalid-date") is None
        assert self.extractor._parse_date("") is None
        assert self.extractor._parse_date(None) is None


class TestTextExtraction:
    """Test cases for text-based deliverable extraction."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = DeliverableExtractor()

    def test_find_deliverable_entries_in_text(self):
        """Test finding deliverable entries in text."""
        content = """
        Deliverable D001: Database Design
        WBS Code: 1.1
        Status: In Progress
        
        ---
        
        Task: User Interface Development
        This deliverable involves creating the UI
        
        ===
        
        1. Requirements Analysis
        2. System Design
        3. Implementation
        """

        entries = self.extractor._find_deliverable_entries_in_text(content)

        assert len(entries) >= 2  # Should find at least 2 deliverable-related sections
        assert any("database design" in entry.lower() for entry in entries)
        assert any("user interface" in entry.lower() for entry in entries)

    def test_create_deliverable_from_text_entry(self):
        """Test creating deliverable from text entry."""
        entry = """
        Deliverable D001: Database Schema Design
        WBS Code: 1.1.1
        Status: In Progress
        Assigned To: Database Team
        Completion: 60%
        
        This deliverable involves designing the complete database schema
        for the application including all tables and relationships.
        """

        deliverable = self.extractor._create_deliverable_from_text_entry(entry)

        assert deliverable is not None
        assert deliverable.deliverable_id == "D001"
        assert "Database Schema Design" in deliverable.name
        assert deliverable.wbs_code == "1.1.1"
        assert deliverable.status == DeliverableStatus.IN_PROGRESS
        assert deliverable.assigned_to == "Database Team"
        assert deliverable.completion_percentage == 60.0

    def test_create_deliverable_from_text_entry_minimal(self):
        """Test creating deliverable from minimal text entry."""
        entry = "Create user authentication system"

        deliverable = self.extractor._create_deliverable_from_text_entry(entry)

        assert deliverable is not None
        assert deliverable.name == "Create user authentication system"
        assert deliverable.description == entry
        assert deliverable.status == DeliverableStatus.NOT_STARTED
        assert deliverable.assigned_to == ""
        assert deliverable.completion_percentage == 0.0


if __name__ == "__main__":
    pytest.main([__file__])
