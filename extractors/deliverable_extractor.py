"""
Deliverable data extraction module for PM Analysis Tool.

This module provides functionality to extract deliverable information from various
document formats including Markdown, Excel, and other Work Breakdown Structure files.
"""

import logging
import re
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.domain import Deliverable, DeliverableStatus
from file_handlers.base_handler import BaseFileHandler
from file_handlers.excel_handler import ExcelHandler
from file_handlers.markdown_handler import MarkdownHandler
from utils.error_handling import ErrorAggregator, handle_errors, safe_execute
from utils.exceptions import DataExtractionError, FileProcessingError
from utils.logger import get_logger
from utils.validators import validate_date_string, validate_wbs_code

logger = get_logger(__name__)


class DeliverableExtractor:
    """
    Extracts deliverable information from various document formats.

    This class can process Work Breakdown Structure documents in multiple formats
    and extract structured deliverable data including WBS codes, dependencies,
    assignments, and completion status.
    """

    def __init__(self):
        """Initialize the deliverable extractor with file handlers."""
        self.markdown_handler = MarkdownHandler()
        self.excel_handler = ExcelHandler()

        # Common deliverable-related keywords for identification
        self.deliverable_keywords = [
            "deliverable",
            "wbs",
            "work breakdown",
            "task",
            "milestone",
            "dependency",
            "assigned",
            "completion",
            "effort",
            "duration",
        ]

        # Patterns for extracting deliverable information from text
        self.deliverable_patterns = {
            "wbs_code": re.compile(
                r"(?:wbs\s*code|wbs|code)[:=\s]*([A-Za-z0-9]+(?:\.[A-Za-z0-9]+)*)", re.IGNORECASE
            ),
            "deliverable_id": re.compile(
                r"(?:deliverable\s*(?:id)?|id)[:=\s]*([A-Za-z0-9_-]+)", re.IGNORECASE
            ),
            "status": re.compile(
                r"(?:status|state)[:=\s]*(not[_\s]started|in[_\s]progress|completed|on[_\s]hold|cancelled)",
                re.IGNORECASE,
            ),
            "assigned_to": re.compile(
                r"(?:assigned\s*to|owner|responsible)[:=\s]*([A-Za-z\s,]+)", re.IGNORECASE
            ),
            "due_date": re.compile(
                r"(?:due|deadline|target)[:=\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", re.IGNORECASE
            ),
            "completion": re.compile(r"(?:completion|progress)[:=\s]*(\d{1,3}%?)", re.IGNORECASE),
            "effort": re.compile(r"(?:effort|hours?)[:=\s]*(\d+(?:\.\d+)?)", re.IGNORECASE),
            "dependencies": re.compile(
                r"(?:depends?\s*on|prerequisites?)[:=\s]*([A-Za-z0-9_,\s-]+)", re.IGNORECASE
            ),
        }

    def extract_deliverables(self, file_path: str) -> List[Deliverable]:
        """
        Extract deliverables from a file.

        Args:
            file_path (str): Path to the file containing deliverable information

        Returns:
            List[Deliverable]: List of extracted Deliverable objects

        Raises:
            DataExtractionError: If extraction fails
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise DataExtractionError(f"File not found: {file_path}")

            logger.info(f"Extracting deliverables from {file_path}")

            # Determine file type and use appropriate handler
            if self.markdown_handler.can_handle(file_path):
                return self._extract_from_markdown(file_path)
            elif self.excel_handler.can_handle(file_path):
                return self._extract_from_excel(file_path)
            else:
                raise DataExtractionError(f"Unsupported file format: {path.suffix}")

        except Exception as e:
            error_msg = f"Failed to extract deliverables from {file_path}: {str(e)}"
            logger.error(error_msg)
            raise DataExtractionError(error_msg) from e

    def _extract_from_markdown(self, file_path: str) -> List[Deliverable]:
        """Extract deliverables from a Markdown file."""
        try:
            data = self.markdown_handler.extract_data(file_path)
            deliverables = []

            # Extract from tables first (most structured)
            for table in data.get("tables", []):
                table_deliverables = self._extract_from_table_data(table)
                deliverables.extend(table_deliverables)

            # Extract from sections if no table data found
            if not deliverables:
                for section in data.get("sections", []):
                    section_deliverables = self._extract_from_text_section(section)
                    deliverables.extend(section_deliverables)

            # If still no deliverables found, try parsing the entire content
            if not deliverables:
                content_deliverables = self._extract_from_raw_text(data.get("raw_content", ""))
                deliverables.extend(content_deliverables)

            logger.info(
                f"Extracted {len(deliverables)} deliverables from markdown file {file_path}"
            )
            return deliverables

        except Exception as e:
            raise DataExtractionError(f"Failed to extract from markdown: {str(e)}") from e

    def _extract_from_excel(self, file_path: str) -> List[Deliverable]:
        """Extract deliverables from an Excel file."""
        try:
            data = self.excel_handler.extract_data(file_path)
            deliverables = []

            # Process each sheet
            for sheet_name, sheet_data in data.get("sheets", {}).items():
                if self._is_deliverable_sheet(sheet_name, sheet_data):
                    sheet_deliverables = self._extract_from_excel_sheet(sheet_data)
                    deliverables.extend(sheet_deliverables)

            logger.info(f"Extracted {len(deliverables)} deliverables from Excel file {file_path}")
            return deliverables

        except Exception as e:
            raise DataExtractionError(f"Failed to extract from Excel: {str(e)}") from e

    def _extract_from_table_data(self, table: Dict[str, Any]) -> List[Deliverable]:
        """Extract deliverables from table data."""
        deliverables = []
        headers = [h.lower().strip() for h in table.get("headers", [])]

        # Map common column names to our fields
        column_mapping = self._create_column_mapping(headers)

        for row in table.get("rows", []):
            try:
                deliverable = self._create_deliverable_from_row(row, column_mapping, headers)
                if deliverable:
                    deliverables.append(deliverable)
            except Exception as e:
                logger.warning(f"Failed to create deliverable from row {row}: {e}")
                continue

        return deliverables

    def _extract_from_text_section(self, section: Dict[str, Any]) -> List[Deliverable]:
        """Extract deliverables from a text section."""
        deliverables = []
        content = section.get("content", "")

        # Look for deliverable entries in the text
        deliverable_entries = self._find_deliverable_entries_in_text(content)

        for entry in deliverable_entries:
            try:
                deliverable = self._create_deliverable_from_text_entry(entry)
                if deliverable:
                    deliverables.append(deliverable)
            except Exception as e:
                logger.warning(f"Failed to create deliverable from text entry: {e}")
                continue

        return deliverables

    def _extract_from_raw_text(self, content: str) -> List[Deliverable]:
        """Extract deliverables from raw text content."""
        deliverables = []

        # Split content into potential deliverable entries
        deliverable_entries = self._find_deliverable_entries_in_text(content)

        for entry in deliverable_entries:
            try:
                deliverable = self._create_deliverable_from_text_entry(entry)
                if deliverable:
                    deliverables.append(deliverable)
            except Exception as e:
                logger.warning(f"Failed to create deliverable from raw text: {e}")
                continue

        return deliverables

    def _extract_from_excel_sheet(self, sheet_data: Dict[str, Any]) -> List[Deliverable]:
        """Extract deliverables from Excel sheet data."""
        deliverables = []

        if "data" not in sheet_data:
            return deliverables

        data_rows = sheet_data["data"]
        if not data_rows:
            return deliverables

        # Assume first row contains headers
        headers = [str(cell).lower().strip() for cell in data_rows[0]]
        column_mapping = self._create_column_mapping(headers)

        # Process data rows
        for row_data in data_rows[1:]:
            try:
                # Convert row to dictionary
                row_dict = {}
                for i, cell in enumerate(row_data):
                    if i < len(headers):
                        row_dict[headers[i]] = str(cell) if cell is not None else ""

                deliverable = self._create_deliverable_from_row(row_dict, column_mapping, headers)
                if deliverable:
                    deliverables.append(deliverable)
            except Exception as e:
                logger.warning(f"Failed to create deliverable from Excel row: {e}")
                continue

        return deliverables

    def _is_deliverable_sheet(self, sheet_name: str, sheet_data: Dict[str, Any]) -> bool:
        """Check if an Excel sheet contains deliverable data."""
        sheet_name_lower = sheet_name.lower()

        # Check sheet name for deliverable-related keywords
        if any(keyword in sheet_name_lower for keyword in self.deliverable_keywords):
            return True

        # Check if sheet has deliverable-related column headers
        if "data" in sheet_data and sheet_data["data"]:
            headers = [str(cell).lower() for cell in sheet_data["data"][0] if cell]
            if any(keyword in " ".join(headers) for keyword in self.deliverable_keywords):
                return True

        return False

    def _create_column_mapping(self, headers: List[str]) -> Dict[str, str]:
        """Create mapping from column headers to deliverable fields."""
        mapping = {}

        for header in headers:
            header_lower = header.lower().strip()

            # Map common variations to standard fields
            if any(term in header_lower for term in ["id", "deliverable id", "item id"]):
                mapping["deliverable_id"] = header
            elif any(term in header_lower for term in ["name", "title", "deliverable name"]):
                mapping["name"] = header
            elif any(term in header_lower for term in ["description", "detail", "desc"]):
                mapping["description"] = header
            elif any(term in header_lower for term in ["wbs", "code", "wbs code"]):
                mapping["wbs_code"] = header
            elif any(term in header_lower for term in ["parent", "parent id"]):
                mapping["parent_id"] = header
            elif any(term in header_lower for term in ["status", "state"]):
                mapping["status"] = header
            elif any(term in header_lower for term in ["assigned", "owner", "responsible"]):
                mapping["assigned_to"] = header
            elif any(term in header_lower for term in ["start", "start date"]):
                mapping["start_date"] = header
            elif any(term in header_lower for term in ["due", "due date", "end date"]):
                mapping["due_date"] = header
            elif any(term in header_lower for term in ["completion", "complete", "progress"]):
                mapping["completion_percentage"] = header
            elif any(term in header_lower for term in ["effort", "hours", "estimated hours"]):
                mapping["estimated_effort_hours"] = header
            elif any(term in header_lower for term in ["actual", "actual hours"]):
                mapping["actual_effort_hours"] = header
            elif any(term in header_lower for term in ["dependencies", "depends on", "prereq"]):
                mapping["dependencies"] = header
            elif any(term in header_lower for term in ["type", "deliverable type"]):
                mapping["deliverable_type"] = header

        return mapping

    def _create_deliverable_from_row(
        self, row: Dict[str, str], column_mapping: Dict[str, str], headers: List[str]
    ) -> Optional[Deliverable]:
        """Create a Deliverable object from a table row."""
        try:
            # Extract basic required fields
            deliverable_id = self._extract_field_value(
                row, column_mapping, "deliverable_id", headers
            )
            if not deliverable_id:
                # Generate ID if not found
                deliverable_id = f"DEL-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            name = self._extract_field_value(row, column_mapping, "name", headers)
            if not name:
                name = "Untitled Deliverable"

            description = (
                self._extract_field_value(row, column_mapping, "description", headers) or ""
            )

            wbs_code = self._extract_field_value(row, column_mapping, "wbs_code", headers)
            if not wbs_code:
                wbs_code = deliverable_id  # Use ID as fallback

            # Extract other fields
            parent_id = self._extract_field_value(row, column_mapping, "parent_id", headers)

            status_str = self._extract_field_value(row, column_mapping, "status", headers)
            status = self._parse_status(status_str)

            assigned_to = (
                self._extract_field_value(row, column_mapping, "assigned_to", headers) or ""
            )

            # Extract dates
            start_date = self._parse_date(
                self._extract_field_value(row, column_mapping, "start_date", headers)
            )
            due_date = self._parse_date(
                self._extract_field_value(row, column_mapping, "due_date", headers)
            )

            # Extract completion percentage
            completion_str = self._extract_field_value(
                row, column_mapping, "completion_percentage", headers
            )
            completion_percentage = self._parse_completion_percentage(completion_str)

            # Extract effort hours
            estimated_effort_str = self._extract_field_value(
                row, column_mapping, "estimated_effort_hours", headers
            )
            estimated_effort_hours = self._parse_effort_hours(estimated_effort_str)

            actual_effort_str = self._extract_field_value(
                row, column_mapping, "actual_effort_hours", headers
            )
            actual_effort_hours = self._parse_effort_hours(actual_effort_str)

            # Extract dependencies
            dependencies_str = self._extract_field_value(
                row, column_mapping, "dependencies", headers
            )
            dependencies = self._parse_dependencies(dependencies_str)

            deliverable_type = (
                self._extract_field_value(row, column_mapping, "deliverable_type", headers) or ""
            )

            # Create Deliverable object
            deliverable = Deliverable(
                deliverable_id=deliverable_id,
                name=name,
                description=description,
                wbs_code=wbs_code,
                parent_id=parent_id,
                status=status,
                assigned_to=assigned_to,
                start_date=start_date,
                due_date=due_date,
                completion_percentage=completion_percentage,
                estimated_effort_hours=estimated_effort_hours,
                actual_effort_hours=actual_effort_hours,
                dependencies=dependencies,
                deliverable_type=deliverable_type,
            )

            return deliverable

        except Exception as e:
            logger.warning(f"Failed to create deliverable from row: {e}")
            return None

    def _extract_field_value(
        self, row: Dict[str, str], column_mapping: Dict[str, str], field: str, headers: List[str]
    ) -> Optional[str]:
        """Extract field value from row using column mapping."""
        if field in column_mapping:
            column_name = column_mapping[field]
            return row.get(column_name, "").strip()

        # Fallback: try to find field directly in row
        for key, value in row.items():
            if field.lower() in key.lower():
                return value.strip()

        return None

    def _find_deliverable_entries_in_text(self, content: str) -> List[str]:
        """Find potential deliverable entries in text content."""
        entries = []

        # Split by common delimiters
        sections = re.split(r"\n\s*\n|\n-{3,}|\n={3,}", content)

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # Check if section contains deliverable-related keywords
            section_lower = section.lower()
            if any(keyword in section_lower for keyword in self.deliverable_keywords):
                entries.append(section)

            # Also check for numbered/bulleted lists that might be deliverables
            if re.search(r"^\s*[\d\w]+[\.\)]\s+", section, re.MULTILINE):
                entries.append(section)

        return entries

    def _create_deliverable_from_text_entry(self, entry: str) -> Optional[Deliverable]:
        """Create a Deliverable object from a text entry."""
        try:
            # Extract information using regex patterns
            deliverable_id_match = self.deliverable_patterns["deliverable_id"].search(entry)
            deliverable_id = None

            if deliverable_id_match:
                deliverable_id = deliverable_id_match.group(1)
            else:
                # Try to extract ID from "Deliverable D001:" pattern
                deliverable_pattern = re.search(
                    r"deliverable\s+([A-Za-z0-9_-]+):", entry, re.IGNORECASE
                )
                if deliverable_pattern:
                    deliverable_id = deliverable_pattern.group(1)
                else:
                    deliverable_id = f"DEL-{len(entry.split())}"

            # Extract WBS code
            wbs_match = self.deliverable_patterns["wbs_code"].search(entry)
            wbs_code = wbs_match.group(1) if wbs_match else deliverable_id

            # Use first line or first sentence as name
            lines = [line.strip() for line in entry.split("\n") if line.strip()]
            name = lines[0][:100] if lines else "Untitled Deliverable"

            # Clean up name if it contains patterns
            if ":" in name and any(term in name.lower() for term in ["deliverable", "task", "wbs"]):
                name_parts = name.split(":", 1)
                if len(name_parts) > 1:
                    name = name_parts[1].strip()

            description = entry.strip()

            # Extract status
            status_match = self.deliverable_patterns["status"].search(entry)
            status = self._parse_status(status_match.group(1) if status_match else None)

            # Extract assigned to
            assigned_match = self.deliverable_patterns["assigned_to"].search(entry)
            if assigned_match:
                assigned_to = assigned_match.group(1).strip()
                # Clean up assigned field - remove extra text after newlines
                assigned_to = assigned_to.split("\n")[0].strip()
            else:
                assigned_to = ""

            # Extract completion percentage
            completion_match = self.deliverable_patterns["completion"].search(entry)
            completion_percentage = self._parse_completion_percentage(
                completion_match.group(1) if completion_match else None
            )

            # Extract dependencies
            deps_match = self.deliverable_patterns["dependencies"].search(entry)
            dependencies = self._parse_dependencies(deps_match.group(1) if deps_match else None)

            # Create Deliverable object
            deliverable = Deliverable(
                deliverable_id=deliverable_id,
                name=name,
                description=description,
                wbs_code=wbs_code,
                status=status,
                assigned_to=assigned_to,
                completion_percentage=completion_percentage,
                dependencies=dependencies,
            )

            return deliverable

        except Exception as e:
            logger.warning(f"Failed to create deliverable from text entry: {e}")
            return None

    def _parse_status(self, value: Optional[str]) -> DeliverableStatus:
        """Parse status value from string."""
        if not value:
            return DeliverableStatus.NOT_STARTED

        value_lower = value.lower().replace("_", " ").replace("-", " ")

        if any(term in value_lower for term in ["completed", "done", "finished"]):
            return DeliverableStatus.COMPLETED
        elif any(term in value_lower for term in ["in progress", "active", "working"]):
            return DeliverableStatus.IN_PROGRESS
        elif any(term in value_lower for term in ["on hold", "paused", "suspended"]):
            return DeliverableStatus.ON_HOLD
        elif any(term in value_lower for term in ["cancelled", "canceled", "dropped"]):
            return DeliverableStatus.CANCELLED
        else:
            return DeliverableStatus.NOT_STARTED

    def _parse_date(self, value: Optional[str]) -> Optional[date]:
        """Parse date value from string."""
        if not value:
            return None

        try:
            # Try common date formats
            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%m-%d-%Y", "%d-%m-%Y"]:
                try:
                    return datetime.strptime(value.strip(), fmt).date()
                except ValueError:
                    continue

            return None

        except Exception:
            return None

    def _parse_completion_percentage(self, value: Optional[str]) -> float:
        """Parse completion percentage from string."""
        if not value:
            return 0.0

        try:
            # Remove percentage sign and convert
            clean_value = value.strip().rstrip("%")
            percentage = float(clean_value)

            # If value is <= 1, assume it's a decimal (0.5 = 50%)
            if percentage <= 1:
                percentage = percentage * 100

            # Ensure value is between 0 and 100
            return max(0.0, min(100.0, percentage))

        except (ValueError, TypeError):
            return 0.0

    def _parse_effort_hours(self, value: Optional[str]) -> Optional[float]:
        """Parse effort hours from string."""
        if not value:
            return None

        try:
            # Extract numeric value
            clean_value = re.sub(r"[^\d\.]", "", value.strip())
            if clean_value:
                hours = float(clean_value)
                return max(0.0, hours)
            return None

        except (ValueError, TypeError):
            return None

    def _parse_dependencies(self, value: Optional[str]) -> List[str]:
        """Parse dependencies from string."""
        if not value:
            return []

        # Split by common delimiters
        deps = re.split(r"[,;|\n]", value.strip())

        # Clean up and filter dependencies
        cleaned_deps = []
        for dep in deps:
            dep = dep.strip()
            if dep and len(dep) > 1:  # Ignore single characters
                cleaned_deps.append(dep)

        return cleaned_deps
