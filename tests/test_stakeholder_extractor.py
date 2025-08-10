"""
Unit tests for the StakeholderExtractor class.

This module contains comprehensive tests for stakeholder data extraction from various
document formats including Markdown and Excel files.
"""

from datetime import date, datetime
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from core.domain import Stakeholder, StakeholderInfluence, StakeholderInterest
from extractors.stakeholder_extractor import StakeholderExtractor
from utils.exceptions import DataExtractionError


class TestStakeholderExtractor:
    """Test cases for StakeholderExtractor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = StakeholderExtractor()

    def test_init(self):
        """Test StakeholderExtractor initialization."""
        assert self.extractor.markdown_handler is not None
        assert self.extractor.excel_handler is not None
        assert len(self.extractor.stakeholder_keywords) > 0
        assert "stakeholder" in self.extractor.stakeholder_keywords
        assert "contact" in self.extractor.stakeholder_keywords

    def test_extract_stakeholders_file_not_found(self):
        """Test extract_stakeholders with non-existent file."""
        with pytest.raises(DataExtractionError, match="File not found"):
            self.extractor.extract_stakeholders("nonexistent_file.md")

    @patch("pathlib.Path.exists")
    def test_extract_stakeholders_unsupported_format(self, mock_exists):
        """Test extract_stakeholders with unsupported file format."""
        mock_exists.return_value = True

        with pytest.raises(DataExtractionError, match="Unsupported file format"):
            self.extractor.extract_stakeholders("test.txt")

    @patch("pathlib.Path.exists")
    @patch.object(StakeholderExtractor, "_extract_from_markdown")
    def test_extract_stakeholders_markdown(self, mock_extract_md, mock_exists):
        """Test extract_stakeholders with Markdown file."""
        mock_exists.return_value = True
        mock_stakeholder = Stakeholder(
            stakeholder_id="SH001",
            name="Test Stakeholder",
            role="Project Manager",
            organization="Test Corp",
            email="test@example.com",
            phone="123-456-7890",
            influence=StakeholderInfluence.HIGH,
            interest=StakeholderInterest.HIGH,
        )
        mock_extract_md.return_value = [mock_stakeholder]

        stakeholders = self.extractor.extract_stakeholders("test.md")

        assert len(stakeholders) == 1
        assert stakeholders[0].stakeholder_id == "SH001"
        mock_extract_md.assert_called_once_with("test.md")

    @patch("pathlib.Path.exists")
    @patch.object(StakeholderExtractor, "_extract_from_excel")
    def test_extract_stakeholders_excel(self, mock_extract_excel, mock_exists):
        """Test extract_stakeholders with Excel file."""
        mock_exists.return_value = True
        mock_stakeholder = Stakeholder(
            stakeholder_id="SH002",
            name="Excel Stakeholder",
            role="Business Analyst",
            organization="Excel Corp",
            email="excel@example.com",
            phone="987-654-3210",
            influence=StakeholderInfluence.MEDIUM,
            interest=StakeholderInterest.HIGH,
        )
        mock_extract_excel.return_value = [mock_stakeholder]

        stakeholders = self.extractor.extract_stakeholders("test.xlsx")

        assert len(stakeholders) == 1
        assert stakeholders[0].stakeholder_id == "SH002"
        mock_extract_excel.assert_called_once_with("test.xlsx")


class TestStakeholderExtractionFromMarkdown:
    """Test cases for Markdown stakeholder extraction."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = StakeholderExtractor()

    @patch.object(StakeholderExtractor, "_extract_from_table_data")
    def test_extract_from_markdown_with_tables(self, mock_extract_table):
        """Test extraction from Markdown with tables."""
        mock_data = {
            "tables": [
                {
                    "headers": ["Stakeholder ID", "Name", "Role", "Email"],
                    "rows": [
                        {
                            "Stakeholder ID": "SH001",
                            "Name": "Test Stakeholder",
                            "Role": "Manager",
                            "Email": "test@example.com",
                        }
                    ],
                }
            ],
            "sections": [],
            "raw_content": "Test content",
        }

        mock_stakeholder = Stakeholder(
            stakeholder_id="SH001",
            name="Test Stakeholder",
            role="Manager",
            organization="",
            email="test@example.com",
            phone="",
            influence=StakeholderInfluence.MEDIUM,
            interest=StakeholderInterest.MEDIUM,
        )
        mock_extract_table.return_value = [mock_stakeholder]

        with patch.object(self.extractor.markdown_handler, "extract_data", return_value=mock_data):
            stakeholders = self.extractor._extract_from_markdown("test.md")

        assert len(stakeholders) == 1
        assert stakeholders[0].stakeholder_id == "SH001"
        mock_extract_table.assert_called_once()


class TestStakeholderExtractionFromExcel:
    """Test cases for Excel stakeholder extraction."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = StakeholderExtractor()

    @patch.object(StakeholderExtractor, "_is_stakeholder_sheet")
    @patch.object(StakeholderExtractor, "_extract_from_excel_sheet")
    def test_extract_from_excel(self, mock_extract_sheet, mock_is_stakeholder_sheet):
        """Test extraction from Excel file."""
        mock_data = {
            "sheets": {
                "Stakeholders": {
                    "data": [["Stakeholder ID", "Name"], ["SH001", "Test Stakeholder"]]
                },
                "Other Sheet": {"data": [["Col1", "Col2"], ["Data1", "Data2"]]},
            }
        }

        mock_is_stakeholder_sheet.side_effect = lambda name, data: name == "Stakeholders"
        mock_stakeholder = Stakeholder(
            stakeholder_id="SH001",
            name="Test Stakeholder",
            role="",
            organization="",
            email="",
            phone="",
            influence=StakeholderInfluence.MEDIUM,
            interest=StakeholderInterest.MEDIUM,
        )
        mock_extract_sheet.return_value = [mock_stakeholder]

        with patch.object(self.extractor.excel_handler, "extract_data", return_value=mock_data):
            stakeholders = self.extractor._extract_from_excel("test.xlsx")

        assert len(stakeholders) == 1
        assert stakeholders[0].stakeholder_id == "SH001"
        mock_extract_sheet.assert_called_once()

    def test_is_stakeholder_sheet_by_name(self):
        """Test stakeholder sheet identification by name."""
        assert self.extractor._is_stakeholder_sheet("Stakeholders", {})
        assert self.extractor._is_stakeholder_sheet("Contacts", {})
        assert self.extractor._is_stakeholder_sheet("Stakeholder Register", {})
        assert not self.extractor._is_stakeholder_sheet("Budget", {})

    def test_is_stakeholder_sheet_by_headers(self):
        """Test stakeholder sheet identification by headers."""
        sheet_data = {
            "data": [
                ["Stakeholder ID", "Name", "Role", "Influence"],
                ["SH001", "John Doe", "Manager", "High"],
            ]
        }

        assert self.extractor._is_stakeholder_sheet("Sheet1", sheet_data)

        sheet_data_no_stakeholder = {
            "data": [["Product", "Price", "Quantity"], ["Widget", "10.00", "100"]]
        }

        assert not self.extractor._is_stakeholder_sheet("Sheet1", sheet_data_no_stakeholder)


class TestColumnMapping:
    """Test cases for column mapping functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = StakeholderExtractor()

    def test_create_column_mapping(self):
        """Test column mapping creation."""
        headers = [
            "Stakeholder ID",
            "Name",
            "Role",
            "Organization",
            "Email",
            "Phone",
            "Influence",
            "Interest",
        ]
        mapping = self.extractor._create_column_mapping(headers)

        assert mapping["stakeholder_id"] == "Stakeholder ID"
        assert mapping["name"] == "Name"
        assert mapping["role"] == "Role"
        assert mapping["organization"] == "Organization"
        assert mapping["email"] == "Email"
        assert mapping["phone"] == "Phone"
        assert mapping["influence"] == "Influence"
        assert mapping["interest"] == "Interest"

    def test_create_column_mapping_variations(self):
        """Test column mapping with header variations."""
        headers = [
            "ID",
            "Contact Name",
            "Position",
            "Company",
            "E-mail",
            "Mobile",
            "Power",
            "Engagement",
        ]
        mapping = self.extractor._create_column_mapping(headers)

        assert mapping["stakeholder_id"] == "ID"
        assert mapping["name"] == "Contact Name"
        assert mapping["role"] == "Position"
        assert mapping["organization"] == "Company"
        assert mapping["email"] == "E-mail"
        assert mapping["phone"] == "Mobile"
        assert mapping["influence"] == "Power"
        assert mapping["interest"] == "Engagement"


class TestStakeholderCreation:
    """Test cases for Stakeholder object creation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = StakeholderExtractor()

    def test_create_stakeholder_from_row_complete(self):
        """Test creating stakeholder from complete row data."""
        row = {
            "stakeholder id": "SH001",
            "name": "John Doe",
            "role": "Project Manager",
            "organization": "Tech Corp",
            "email": "john.doe@techcorp.com",
            "phone": "123-456-7890",
            "influence": "High",
            "interest": "Medium",
        }

        headers = list(row.keys())
        column_mapping = self.extractor._create_column_mapping(headers)

        stakeholder = self.extractor._create_stakeholder_from_row(row, column_mapping, headers)

        assert stakeholder is not None
        assert stakeholder.stakeholder_id == "SH001"
        assert stakeholder.name == "John Doe"
        assert stakeholder.role == "Project Manager"
        assert stakeholder.organization == "Tech Corp"
        assert stakeholder.email == "john.doe@techcorp.com"
        assert stakeholder.phone == "123-456-7890"
        assert stakeholder.influence == StakeholderInfluence.HIGH
        assert stakeholder.interest == StakeholderInterest.MEDIUM

    def test_create_stakeholder_from_row_minimal(self):
        """Test creating stakeholder from minimal row data."""
        row = {"name": "Jane Smith"}

        headers = list(row.keys())
        column_mapping = self.extractor._create_column_mapping(headers)

        stakeholder = self.extractor._create_stakeholder_from_row(row, column_mapping, headers)

        assert stakeholder is not None
        assert stakeholder.name == "Jane Smith"
        assert stakeholder.role == ""
        assert stakeholder.organization == ""
        assert stakeholder.email == ""
        assert stakeholder.phone == ""
        assert stakeholder.influence == StakeholderInfluence.MEDIUM
        assert stakeholder.interest == StakeholderInterest.MEDIUM

    @patch("utils.validators.validate_email")
    def test_create_stakeholder_invalid_email(self, mock_validate_email):
        """Test creating stakeholder with invalid email."""
        mock_validate_email.side_effect = Exception("Invalid email")

        row = {"name": "Test User", "email": "invalid-email"}

        headers = list(row.keys())
        column_mapping = self.extractor._create_column_mapping(headers)

        stakeholder = self.extractor._create_stakeholder_from_row(row, column_mapping, headers)

        assert stakeholder is not None
        assert stakeholder.email == ""  # Should be empty due to validation failure


class TestValueParsing:
    """Test cases for value parsing methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = StakeholderExtractor()

    def test_parse_influence(self):
        """Test influence parsing."""
        assert self.extractor._parse_influence("Very High") == StakeholderInfluence.VERY_HIGH
        assert self.extractor._parse_influence("High") == StakeholderInfluence.HIGH
        assert self.extractor._parse_influence("Medium") == StakeholderInfluence.MEDIUM
        assert self.extractor._parse_influence("Low") == StakeholderInfluence.LOW
        assert self.extractor._parse_influence("Unknown") == StakeholderInfluence.MEDIUM  # Default
        assert self.extractor._parse_influence(None) == StakeholderInfluence.MEDIUM  # Default

    def test_parse_interest(self):
        """Test interest parsing."""
        assert self.extractor._parse_interest("Very High") == StakeholderInterest.VERY_HIGH
        assert self.extractor._parse_interest("High") == StakeholderInterest.HIGH
        assert self.extractor._parse_interest("Medium") == StakeholderInterest.MEDIUM
        assert self.extractor._parse_interest("Low") == StakeholderInterest.LOW
        assert self.extractor._parse_interest("Unknown") == StakeholderInterest.MEDIUM  # Default
        assert self.extractor._parse_interest(None) == StakeholderInterest.MEDIUM  # Default

    def test_parse_list_field(self):
        """Test list field parsing."""
        assert self.extractor._parse_list_field("Item1, Item2, Item3") == [
            "Item1",
            "Item2",
            "Item3",
        ]
        assert self.extractor._parse_list_field("Item1; Item2; Item3") == [
            "Item1",
            "Item2",
            "Item3",
        ]
        assert self.extractor._parse_list_field("Item1|Item2|Item3") == ["Item1", "Item2", "Item3"]
        assert self.extractor._parse_list_field("Item1\nItem2\nItem3") == [
            "Item1",
            "Item2",
            "Item3",
        ]
        assert self.extractor._parse_list_field("") == []
        assert self.extractor._parse_list_field(None) == []


class TestTextExtraction:
    """Test cases for text-based stakeholder extraction."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = StakeholderExtractor()

    def test_find_stakeholder_entries_in_text(self):
        """Test finding stakeholder entries in text."""
        content = """
        Stakeholder SH001: John Doe
        Role: Project Manager
        Email: john.doe@example.com
        
        ---
        
        Contact Information:
        Name: Jane Smith
        Organization: Tech Corp
        Phone: 123-456-7890
        
        ===
        
        Regular text without stakeholder information
        This should not be detected
        """

        entries = self.extractor._find_stakeholder_entries_in_text(content)

        assert len(entries) >= 2  # Should find at least 2 stakeholder-related sections
        assert any("john doe" in entry.lower() for entry in entries)
        assert any("jane smith" in entry.lower() for entry in entries)

    def test_create_stakeholder_from_text_entry(self):
        """Test creating stakeholder from text entry."""
        entry = """
        Stakeholder SH001: John Doe
        Role: Senior Project Manager
        Organization: Tech Solutions Inc
        Email: john.doe@techsolutions.com
        Phone: +1-555-123-4567
        Influence: High
        Interest: Very High
        Sentiment: Supportive
        
        This stakeholder is the primary project sponsor and has
        significant decision-making authority.
        """

        stakeholder = self.extractor._create_stakeholder_from_text_entry(entry)

        assert stakeholder is not None
        assert stakeholder.stakeholder_id == "SH001"
        assert "John Doe" in stakeholder.name
        assert stakeholder.role == "Senior Project Manager"
        assert stakeholder.organization == "Tech Solutions Inc"
        assert stakeholder.email == "john.doe@techsolutions.com"
        assert stakeholder.phone == "+1-555-123-4567"
        assert stakeholder.influence == StakeholderInfluence.HIGH
        assert stakeholder.interest == StakeholderInterest.VERY_HIGH
        assert stakeholder.current_sentiment == "Supportive"

    def test_create_stakeholder_from_text_entry_minimal(self):
        """Test creating stakeholder from minimal text entry."""
        entry = "Project team member with technical expertise"

        stakeholder = self.extractor._create_stakeholder_from_text_entry(entry)

        assert stakeholder is not None
        assert stakeholder.name == "Project team member with technical expertise"
        assert stakeholder.role == ""
        assert stakeholder.organization == ""
        assert stakeholder.email == ""
        assert stakeholder.phone == ""
        assert stakeholder.influence == StakeholderInfluence.MEDIUM
        assert stakeholder.interest == StakeholderInterest.MEDIUM


if __name__ == "__main__":
    pytest.main([__file__])
