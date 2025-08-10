"""
Unit tests for the RiskExtractor class.

This module contains comprehensive tests for risk data extraction from various
document formats including Markdown and Excel files.
"""

from datetime import date, datetime
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from core.domain import Risk, RiskPriority, RiskStatus
from extractors.risk_extractor import RiskExtractor
from utils.exceptions import DataExtractionError


class TestRiskExtractor:
    """Test cases for RiskExtractor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = RiskExtractor()

    def test_init(self):
        """Test RiskExtractor initialization."""
        assert self.extractor.markdown_handler is not None
        assert self.extractor.excel_handler is not None
        assert len(self.extractor.risk_keywords) > 0
        assert "risk" in self.extractor.risk_keywords
        assert "probability" in self.extractor.risk_keywords

    def test_extract_risks_file_not_found(self):
        """Test extract_risks with non-existent file."""
        with pytest.raises(DataExtractionError, match="File not found"):
            self.extractor.extract_risks("nonexistent_file.md")

    @patch("pathlib.Path.exists")
    def test_extract_risks_unsupported_format(self, mock_exists):
        """Test extract_risks with unsupported file format."""
        mock_exists.return_value = True

        with pytest.raises(DataExtractionError, match="Unsupported file format"):
            self.extractor.extract_risks("test.txt")

    @patch("pathlib.Path.exists")
    @patch.object(RiskExtractor, "_extract_from_markdown")
    def test_extract_risks_markdown(self, mock_extract_md, mock_exists):
        """Test extract_risks with Markdown file."""
        mock_exists.return_value = True
        mock_risk = Risk(
            risk_id="R001",
            title="Test Risk",
            description="Test Description",
            category="Technical",
            probability=0.5,
            impact=0.7,
            priority=RiskPriority.MEDIUM,
            status=RiskStatus.OPEN,
            owner="Test Owner",
            identified_date=date.today(),
        )
        mock_extract_md.return_value = [mock_risk]

        risks = self.extractor.extract_risks("test.md")

        assert len(risks) == 1
        assert risks[0].risk_id == "R001"
        mock_extract_md.assert_called_once_with("test.md")

    @patch("pathlib.Path.exists")
    @patch.object(RiskExtractor, "_extract_from_excel")
    def test_extract_risks_excel(self, mock_extract_excel, mock_exists):
        """Test extract_risks with Excel file."""
        mock_exists.return_value = True
        mock_risk = Risk(
            risk_id="R002",
            title="Excel Risk",
            description="Excel Description",
            category="Financial",
            probability=0.8,
            impact=0.6,
            priority=RiskPriority.HIGH,
            status=RiskStatus.IN_PROGRESS,
            owner="Excel Owner",
            identified_date=date.today(),
        )
        mock_extract_excel.return_value = [mock_risk]

        risks = self.extractor.extract_risks("test.xlsx")

        assert len(risks) == 1
        assert risks[0].risk_id == "R002"
        mock_extract_excel.assert_called_once_with("test.xlsx")


class TestRiskExtractionFromMarkdown:
    """Test cases for Markdown risk extraction."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = RiskExtractor()

    @patch.object(RiskExtractor, "_extract_from_table_data")
    def test_extract_from_markdown_with_tables(self, mock_extract_table):
        """Test extraction from Markdown with tables."""
        mock_data = {
            "tables": [
                {
                    "headers": ["Risk ID", "Description", "Probability", "Impact"],
                    "rows": [
                        {
                            "Risk ID": "R001",
                            "Description": "Test Risk",
                            "Probability": "50%",
                            "Impact": "70%",
                        }
                    ],
                }
            ],
            "sections": [],
            "raw_content": "Test content",
        }

        mock_risk = Risk(
            risk_id="R001",
            title="Test Risk",
            description="Test Risk",
            category="General",
            probability=0.5,
            impact=0.7,
            priority=RiskPriority.MEDIUM,
            status=RiskStatus.OPEN,
            owner="Unassigned",
            identified_date=date.today(),
        )
        mock_extract_table.return_value = [mock_risk]

        with patch.object(self.extractor.markdown_handler, "extract_data", return_value=mock_data):
            risks = self.extractor._extract_from_markdown("test.md")

        assert len(risks) == 1
        assert risks[0].risk_id == "R001"
        mock_extract_table.assert_called_once()

    @patch.object(RiskExtractor, "_extract_from_text_section")
    def test_extract_from_markdown_with_sections(self, mock_extract_section):
        """Test extraction from Markdown sections when no tables."""
        mock_data = {
            "tables": [],
            "sections": [{"title": "Risk Section", "content": "Risk content with probability 60%"}],
            "raw_content": "Test content",
        }

        mock_risk = Risk(
            risk_id="R001",
            title="Risk Section",
            description="Risk content",
            category="General",
            probability=0.6,
            impact=0.5,
            priority=RiskPriority.MEDIUM,
            status=RiskStatus.OPEN,
            owner="Unassigned",
            identified_date=date.today(),
        )
        mock_extract_section.return_value = [mock_risk]

        with patch.object(self.extractor.markdown_handler, "extract_data", return_value=mock_data):
            risks = self.extractor._extract_from_markdown("test.md")

        assert len(risks) == 1
        mock_extract_section.assert_called_once()


class TestRiskExtractionFromExcel:
    """Test cases for Excel risk extraction."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = RiskExtractor()

    @patch.object(RiskExtractor, "_is_risk_sheet")
    @patch.object(RiskExtractor, "_extract_from_excel_sheet")
    def test_extract_from_excel(self, mock_extract_sheet, mock_is_risk_sheet):
        """Test extraction from Excel file."""
        mock_data = {
            "sheets": {
                "Risk Register": {"data": [["Risk ID", "Description"], ["R001", "Test Risk"]]},
                "Other Sheet": {"data": [["Col1", "Col2"], ["Data1", "Data2"]]},
            }
        }

        mock_is_risk_sheet.side_effect = lambda name, data: name == "Risk Register"
        mock_risk = Risk(
            risk_id="R001",
            title="Test Risk",
            description="Test Risk",
            category="General",
            probability=0.5,
            impact=0.5,
            priority=RiskPriority.MEDIUM,
            status=RiskStatus.OPEN,
            owner="Unassigned",
            identified_date=date.today(),
        )
        mock_extract_sheet.return_value = [mock_risk]

        with patch.object(self.extractor.excel_handler, "extract_data", return_value=mock_data):
            risks = self.extractor._extract_from_excel("test.xlsx")

        assert len(risks) == 1
        assert risks[0].risk_id == "R001"
        mock_extract_sheet.assert_called_once()

    def test_is_risk_sheet_by_name(self):
        """Test risk sheet identification by name."""
        assert self.extractor._is_risk_sheet("Risk Register", {})
        assert self.extractor._is_risk_sheet("Risks", {})
        assert self.extractor._is_risk_sheet("Threat Analysis", {})
        assert not self.extractor._is_risk_sheet("Budget", {})

    def test_is_risk_sheet_by_headers(self):
        """Test risk sheet identification by headers."""
        sheet_data = {
            "data": [
                ["Risk ID", "Probability", "Impact", "Mitigation"],
                ["R001", "50%", "70%", "Test mitigation"],
            ]
        }

        assert self.extractor._is_risk_sheet("Sheet1", sheet_data)

        sheet_data_no_risk = {"data": [["Name", "Age", "Department"], ["John", "30", "IT"]]}

        assert not self.extractor._is_risk_sheet("Sheet1", sheet_data_no_risk)


class TestColumnMapping:
    """Test cases for column mapping functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = RiskExtractor()

    def test_create_column_mapping(self):
        """Test column mapping creation."""
        headers = ["Risk ID", "Title", "Description", "Probability", "Impact", "Status", "Owner"]
        mapping = self.extractor._create_column_mapping(headers)

        assert mapping["risk_id"] == "Risk ID"
        assert mapping["title"] == "Title"
        assert mapping["description"] == "Description"
        assert mapping["probability"] == "Probability"
        assert mapping["impact"] == "Impact"
        assert mapping["status"] == "Status"
        assert mapping["owner"] == "Owner"

    def test_create_column_mapping_variations(self):
        """Test column mapping with header variations."""
        headers = ["Risk #", "Risk Name", "Desc", "Prob", "Severity", "State", "Assigned To"]
        mapping = self.extractor._create_column_mapping(headers)

        assert mapping["risk_id"] == "Risk #"
        assert mapping["title"] == "Risk Name"
        assert mapping["description"] == "Desc"
        assert mapping["probability"] == "Prob"
        assert mapping["impact"] == "Severity"
        assert mapping["status"] == "State"
        assert mapping["owner"] == "Assigned To"


class TestRiskCreation:
    """Test cases for Risk object creation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = RiskExtractor()

    def test_create_risk_from_row_complete(self):
        """Test creating risk from complete row data."""
        row = {
            "risk id": "R001",
            "title": "Test Risk",
            "description": "Test Description",
            "category": "Technical",
            "probability": "60%",
            "impact": "80%",
            "status": "Open",
            "owner": "John Doe",
        }

        headers = list(row.keys())
        column_mapping = self.extractor._create_column_mapping(headers)

        risk = self.extractor._create_risk_from_row(row, column_mapping, headers)

        assert risk is not None
        assert risk.risk_id == "R001"
        assert risk.title == "Test Risk"
        assert risk.description == "Test Description"
        assert risk.category == "Technical"
        assert risk.probability == 0.6
        assert risk.impact == 0.8
        assert risk.status == RiskStatus.OPEN
        assert risk.owner == "John Doe"

    def test_create_risk_from_row_minimal(self):
        """Test creating risk from minimal row data."""
        row = {"description": "Minimal Risk Description"}

        headers = list(row.keys())
        column_mapping = self.extractor._create_column_mapping(headers)

        risk = self.extractor._create_risk_from_row(row, column_mapping, headers)

        assert risk is not None
        assert risk.title == "Untitled Risk"
        assert risk.description == "Minimal Risk Description"
        assert risk.category == "General"
        assert risk.probability == 0.5  # Default
        assert risk.impact == 0.5  # Default
        assert risk.owner == "Unassigned"


class TestValueParsing:
    """Test cases for value parsing methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = RiskExtractor()

    def test_parse_probability_percentage(self):
        """Test probability parsing from percentage."""
        assert self.extractor._parse_probability("50%") == 0.5
        assert self.extractor._parse_probability("75%") == 0.75
        assert self.extractor._parse_probability("100%") == 1.0

    def test_parse_probability_decimal(self):
        """Test probability parsing from decimal."""
        assert self.extractor._parse_probability("0.3") == 0.3
        assert self.extractor._parse_probability("0.85") == 0.85
        assert self.extractor._parse_probability("1.0") == 1.0

    def test_parse_probability_text(self):
        """Test probability parsing from text."""
        assert self.extractor._parse_probability("High") == 0.8
        assert self.extractor._parse_probability("Medium") == 0.5
        assert self.extractor._parse_probability("Low") == 0.2
        assert self.extractor._parse_probability("Likely") == 0.8

    def test_parse_impact_percentage(self):
        """Test impact parsing from percentage."""
        assert self.extractor._parse_impact("40%") == 0.4
        assert self.extractor._parse_impact("90%") == 0.9

    def test_parse_impact_text(self):
        """Test impact parsing from text."""
        assert self.extractor._parse_impact("High") == 0.8
        assert self.extractor._parse_impact("Critical") == 0.8
        assert self.extractor._parse_impact("Medium") == 0.5
        assert self.extractor._parse_impact("Low") == 0.2
        assert self.extractor._parse_impact("Minor") == 0.2

    def test_parse_priority_text(self):
        """Test priority parsing from text."""
        assert self.extractor._parse_priority("Critical", 0.5, 0.5) == RiskPriority.CRITICAL
        assert self.extractor._parse_priority("High", 0.5, 0.5) == RiskPriority.HIGH
        assert self.extractor._parse_priority("Medium", 0.5, 0.5) == RiskPriority.MEDIUM
        assert self.extractor._parse_priority("Low", 0.5, 0.5) == RiskPriority.LOW

    def test_parse_priority_calculated(self):
        """Test priority calculation from probability and impact."""
        assert self.extractor._parse_priority(None, 0.9, 0.8) == RiskPriority.CRITICAL
        assert self.extractor._parse_priority(None, 0.7, 0.6) == RiskPriority.HIGH
        assert self.extractor._parse_priority(None, 0.5, 0.4) == RiskPriority.MEDIUM
        assert self.extractor._parse_priority(None, 0.2, 0.3) == RiskPriority.LOW

    def test_parse_status(self):
        """Test status parsing."""
        assert self.extractor._parse_status("Open") == RiskStatus.OPEN
        assert self.extractor._parse_status("Closed") == RiskStatus.CLOSED
        assert self.extractor._parse_status("Mitigated") == RiskStatus.MITIGATED
        assert self.extractor._parse_status("In Progress") == RiskStatus.IN_PROGRESS
        assert self.extractor._parse_status("Accepted") == RiskStatus.ACCEPTED
        assert self.extractor._parse_status("Unknown") == RiskStatus.OPEN  # Default

    def test_parse_date_formats(self):
        """Test date parsing from various formats."""
        test_date = date(2025, 3, 15)

        assert self.extractor._parse_date("2025-03-15") == test_date
        assert self.extractor._parse_date("03/15/2025") == test_date
        assert self.extractor._parse_date("15/03/2025") == test_date

        # Invalid date should return today
        today = date.today()
        assert self.extractor._parse_date("invalid-date") == today
        assert self.extractor._parse_date("") == today
        assert self.extractor._parse_date(None) == today


class TestTextExtraction:
    """Test cases for text-based risk extraction."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = RiskExtractor()

    def test_find_risk_entries_in_text(self):
        """Test finding risk entries in text."""
        content = """
        Risk R001: Database failure
        Probability: 30%
        Impact: High
        
        ---
        
        Another risk: Network outage
        This is a threat with medium probability
        
        ===
        
        Opportunity: Cost savings
        This could reduce expenses
        """

        entries = self.extractor._find_risk_entries_in_text(content)

        assert len(entries) >= 2  # Should find at least 2 risk-related sections
        assert any("database failure" in entry.lower() for entry in entries)
        assert any("network outage" in entry.lower() for entry in entries)

    def test_create_risk_from_text_entry(self):
        """Test creating risk from text entry."""
        entry = """
        Risk R001: Database Server Failure
        Probability: 25%
        Impact: High
        Status: Open
        Owner: IT Team
        
        This risk involves potential database server hardware failure
        that could impact system availability.
        """

        risk = self.extractor._create_risk_from_text_entry(entry)

        assert risk is not None
        assert risk.risk_id == "R001"
        assert "Database Server Failure" in risk.title
        assert risk.probability == 0.25
        assert risk.impact == 0.8  # High
        assert risk.status == RiskStatus.OPEN
        assert risk.owner == "IT Team"

    def test_create_risk_from_text_entry_minimal(self):
        """Test creating risk from minimal text entry."""
        entry = "System might fail due to high load"

        risk = self.extractor._create_risk_from_text_entry(entry)

        assert risk is not None
        assert risk.title == "System might fail due to high load"
        assert risk.description == entry
        assert risk.probability == 0.5  # Default
        assert risk.impact == 0.5  # Default
        assert risk.status == RiskStatus.OPEN
        assert risk.owner == "Unassigned"


if __name__ == "__main__":
    pytest.main([__file__])
