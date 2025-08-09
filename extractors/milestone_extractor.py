"""
Milestone data extraction module for PM Analysis Tool.

This module provides functionality to extract milestone information from various
document formats including Markdown, Excel, and Microsoft Project (.mpp) files.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
from pathlib import Path
import logging

from core.domain import Milestone, MilestoneStatus
from file_handlers.base_handler import BaseFileHandler
from file_handlers.markdown_handler import MarkdownHandler
from file_handlers.excel_handler import ExcelHandler
from file_handlers.mpp_handler import MPPHandler
from utils.exceptions import DataExtractionError
from utils.validators import validate_date_string

logger = logging.getLogger(__name__)


class MilestoneExtractor:
    """
    Extracts milestone information from various document formats.
    
    This class can process roadmap documents and project files in multiple formats
    and extract structured milestone data including dates, dependencies,
    and completion status.
    """
    
    def __init__(self):
        """Initialize the milestone extractor with file handlers."""
        self.markdown_handler = MarkdownHandler()
        self.excel_handler = ExcelHandler()
        self.mpp_handler = MPPHandler()
        
        # Common milestone-related keywords for identification
        self.milestone_keywords = [
            'milestone', 'deadline', 'target', 'completion', 'delivery',
            'phase', 'gate', 'checkpoint', 'review', 'approval', 'timeline'
        ]
        
        # Patterns for extracting milestone information from text
        self.milestone_patterns = {
            'milestone_id': re.compile(r'(?:milestone\s*(?:id)?|id)[:=\s]*([A-Za-z0-9_-]+)', re.IGNORECASE),
            'target_date': re.compile(r'(?:target\s*date|due|deadline|date)[:=\s]*(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', re.IGNORECASE),
            'status': re.compile(r'(?:status|state)[:=\s]*(upcoming|in[_\s]progress|completed|overdue|cancelled)', re.IGNORECASE),
            'owner': re.compile(r'(?:owner|responsible|assigned\s*to)[:=\s]*([A-Za-z\s,]+)', re.IGNORECASE),
            'milestone_type': re.compile(r'(?:type|category)[:=\s]*([A-Za-z\s]+)', re.IGNORECASE),
            'dependencies': re.compile(r'(?:dependencies|depends?\s*on|prerequisites?)[:=\s]*([A-Za-z0-9_,\s-]+?)(?:\n|$)', re.IGNORECASE),
            'approval': re.compile(r'(?:approval|approver)[:=\s]*([A-Za-z\s]+)', re.IGNORECASE)
        }
    
    def extract_milestones(self, file_path: str) -> List[Milestone]:
        """
        Extract milestones from a file.
        
        Args:
            file_path (str): Path to the file containing milestone information
            
        Returns:
            List[Milestone]: List of extracted Milestone objects
            
        Raises:
            DataExtractionError: If extraction fails
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise DataExtractionError(f"File not found: {file_path}")
            
            logger.info(f"Extracting milestones from {file_path}")
            
            # Determine file type and use appropriate handler
            if self.mpp_handler.can_handle(file_path):
                return self._extract_from_mpp(file_path)
            elif self.markdown_handler.can_handle(file_path):
                return self._extract_from_markdown(file_path)
            elif self.excel_handler.can_handle(file_path):
                return self._extract_from_excel(file_path)
            else:
                raise DataExtractionError(f"Unsupported file format: {path.suffix}")
                
        except Exception as e:
            error_msg = f"Failed to extract milestones from {file_path}: {str(e)}"
            logger.error(error_msg)
            raise DataExtractionError(error_msg) from e
    
    def _extract_from_mpp(self, file_path: str) -> List[Milestone]:
        """Extract milestones from a Microsoft Project file."""
        try:
            data = self.mpp_handler.extract_data(file_path)
            milestones = []
            
            # Extract milestones from project tasks
            for task in data.get('tasks', []):
                if self._is_milestone_task(task):
                    milestone = self._create_milestone_from_mpp_task(task)
                    if milestone:
                        milestones.append(milestone)
            
            logger.info(f"Extracted {len(milestones)} milestones from MPP file {file_path}")
            return milestones
            
        except Exception as e:
            raise DataExtractionError(f"Failed to extract from MPP: {str(e)}") from e
    
    def _extract_from_markdown(self, file_path: str) -> List[Milestone]:
        """Extract milestones from a Markdown file."""
        try:
            data = self.markdown_handler.extract_data(file_path)
            milestones = []
            
            # Extract from tables first (most structured)
            for table in data.get('tables', []):
                table_milestones = self._extract_from_table_data(table)
                milestones.extend(table_milestones)
            
            # Extract from sections if no table data found
            if not milestones:
                for section in data.get('sections', []):
                    section_milestones = self._extract_from_text_section(section)
                    milestones.extend(section_milestones)
            
            # If still no milestones found, try parsing the entire content
            if not milestones:
                content_milestones = self._extract_from_raw_text(data.get('raw_content', ''))
                milestones.extend(content_milestones)
            
            logger.info(f"Extracted {len(milestones)} milestones from markdown file {file_path}")
            return milestones
            
        except Exception as e:
            raise DataExtractionError(f"Failed to extract from markdown: {str(e)}") from e
    
    def _extract_from_excel(self, file_path: str) -> List[Milestone]:
        """Extract milestones from an Excel file."""
        try:
            data = self.excel_handler.extract_data(file_path)
            milestones = []
            
            # Process each sheet
            for sheet_name, sheet_data in data.get('sheets', {}).items():
                if self._is_milestone_sheet(sheet_name, sheet_data):
                    sheet_milestones = self._extract_from_excel_sheet(sheet_data)
                    milestones.extend(sheet_milestones)
            
            logger.info(f"Extracted {len(milestones)} milestones from Excel file {file_path}")
            return milestones
            
        except Exception as e:
            raise DataExtractionError(f"Failed to extract from Excel: {str(e)}") from e
    
    def _is_milestone_task(self, task: Dict[str, Any]) -> bool:
        """Check if a project task is a milestone."""
        # Check if task is marked as milestone
        if task.get('is_milestone', False):
            return True
        
        # Check if task has zero duration (typical milestone characteristic)
        if task.get('duration', 0) == 0:
            return True
        
        # Check if task name contains milestone keywords
        task_name = task.get('name', '').lower()
        if any(keyword in task_name for keyword in self.milestone_keywords):
            return True
        
        return False
    
    def _create_milestone_from_mpp_task(self, task: Dict[str, Any]) -> Optional[Milestone]:
        """Create a Milestone object from an MPP task."""
        try:
            milestone_id = task.get('id', f"MS-{task.get('unique_id', 'unknown')}")
            name = task.get('name', 'Untitled Milestone')
            description = task.get('notes', '')
            
            # Extract dates
            target_date = self._parse_date(task.get('finish_date'))
            if not target_date:
                target_date = self._parse_date(task.get('start_date'))
            
            actual_date = self._parse_date(task.get('actual_finish'))
            
            # Determine status
            status = self._determine_status_from_task(task)
            
            # Extract other fields
            owner = task.get('resource_names', '')
            if isinstance(owner, list):
                owner = ', '.join(owner)
            
            # Extract dependencies
            dependencies = []
            if 'predecessors' in task:
                dependencies = [str(pred) for pred in task['predecessors']]
            
            milestone = Milestone(
                milestone_id=milestone_id,
                name=name,
                description=description,
                target_date=target_date or date.today(),
                actual_date=actual_date,
                status=status,
                owner=owner,
                dependencies=dependencies
            )
            
            return milestone
            
        except Exception as e:
            logger.warning(f"Failed to create milestone from MPP task: {e}")
            return None
    
    def _extract_from_table_data(self, table: Dict[str, Any]) -> List[Milestone]:
        """Extract milestones from table data."""
        milestones = []
        headers = [h.lower().strip() for h in table.get('headers', [])]
        
        # Map common column names to our fields
        column_mapping = self._create_column_mapping(headers)
        
        for row in table.get('rows', []):
            try:
                milestone = self._create_milestone_from_row(row, column_mapping, headers)
                if milestone:
                    milestones.append(milestone)
            except Exception as e:
                logger.warning(f"Failed to create milestone from row {row}: {e}")
                continue
        
        return milestones
    
    def _extract_from_text_section(self, section: Dict[str, Any]) -> List[Milestone]:
        """Extract milestones from a text section."""
        milestones = []
        content = section.get('content', '')
        
        # Look for milestone entries in the text
        milestone_entries = self._find_milestone_entries_in_text(content)
        
        for entry in milestone_entries:
            try:
                milestone = self._create_milestone_from_text_entry(entry)
                if milestone:
                    milestones.append(milestone)
            except Exception as e:
                logger.warning(f"Failed to create milestone from text entry: {e}")
                continue
        
        return milestones
    
    def _extract_from_raw_text(self, content: str) -> List[Milestone]:
        """Extract milestones from raw text content."""
        milestones = []
        
        # Split content into potential milestone entries
        milestone_entries = self._find_milestone_entries_in_text(content)
        
        for entry in milestone_entries:
            try:
                milestone = self._create_milestone_from_text_entry(entry)
                if milestone:
                    milestones.append(milestone)
            except Exception as e:
                logger.warning(f"Failed to create milestone from raw text: {e}")
                continue
        
        return milestones
    
    def _extract_from_excel_sheet(self, sheet_data: Dict[str, Any]) -> List[Milestone]:
        """Extract milestones from Excel sheet data."""
        milestones = []
        
        if 'data' not in sheet_data:
            return milestones
        
        data_rows = sheet_data['data']
        if not data_rows:
            return milestones
        
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
                        row_dict[headers[i]] = str(cell) if cell is not None else ''
                
                milestone = self._create_milestone_from_row(row_dict, column_mapping, headers)
                if milestone:
                    milestones.append(milestone)
            except Exception as e:
                logger.warning(f"Failed to create milestone from Excel row: {e}")
                continue
        
        return milestones
    
    def _is_milestone_sheet(self, sheet_name: str, sheet_data: Dict[str, Any]) -> bool:
        """Check if an Excel sheet contains milestone data."""
        sheet_name_lower = sheet_name.lower()
        
        # Check sheet name for milestone-related keywords
        if any(keyword in sheet_name_lower for keyword in self.milestone_keywords):
            return True
        
        # Check if sheet has milestone-related column headers
        if 'data' in sheet_data and sheet_data['data']:
            headers = [str(cell).lower() for cell in sheet_data['data'][0] if cell]
            if any(keyword in ' '.join(headers) for keyword in self.milestone_keywords):
                return True
        
        return False
    
    def _create_column_mapping(self, headers: List[str]) -> Dict[str, str]:
        """Create mapping from column headers to milestone fields."""
        mapping = {}
        
        for header in headers:
            header_lower = header.lower().strip()
            
            # Map common variations to standard fields
            if any(term in header_lower for term in ['id', 'milestone id']):
                mapping['milestone_id'] = header
            elif any(term in header_lower for term in ['name', 'title', 'milestone name']):
                mapping['name'] = header
            elif any(term in header_lower for term in ['description', 'detail', 'desc']):
                mapping['description'] = header
            elif any(term in header_lower for term in ['target', 'due', 'deadline', 'target date']):
                mapping['target_date'] = header
            elif any(term in header_lower for term in ['actual', 'actual date', 'completion date']):
                mapping['actual_date'] = header
            elif any(term in header_lower for term in ['status', 'state']):
                mapping['status'] = header
            elif any(term in header_lower for term in ['owner', 'responsible', 'assigned']):
                mapping['owner'] = header
            elif any(term in header_lower for term in ['type', 'category', 'milestone type']):
                mapping['milestone_type'] = header
            elif any(term in header_lower for term in ['dependencies', 'depends on', 'prereq']):
                mapping['dependencies'] = header
            elif any(term in header_lower for term in ['approval', 'approver']):
                mapping['approver'] = header
        
        return mapping
    
    def _create_milestone_from_row(self, row: Dict[str, str], column_mapping: Dict[str, str], headers: List[str]) -> Optional[Milestone]:
        """Create a Milestone object from a table row."""
        try:
            # Extract basic required fields
            milestone_id = self._extract_field_value(row, column_mapping, 'milestone_id', headers)
            if not milestone_id:
                # Generate ID if not found
                milestone_id = f"MS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            name = self._extract_field_value(row, column_mapping, 'name', headers)
            if not name:
                name = "Untitled Milestone"
            
            description = self._extract_field_value(row, column_mapping, 'description', headers) or ""
            
            # Extract dates
            target_date_str = self._extract_field_value(row, column_mapping, 'target_date', headers)
            target_date = self._parse_date(target_date_str)
            if not target_date:
                target_date = date.today()
            
            actual_date_str = self._extract_field_value(row, column_mapping, 'actual_date', headers)
            actual_date = self._parse_date(actual_date_str)
            
            # Extract status
            status_str = self._extract_field_value(row, column_mapping, 'status', headers)
            status = self._parse_status(status_str)
            
            # Extract other fields
            owner = self._extract_field_value(row, column_mapping, 'owner', headers) or ""
            milestone_type = self._extract_field_value(row, column_mapping, 'milestone_type', headers) or ""
            approver = self._extract_field_value(row, column_mapping, 'approver', headers) or ""
            
            # Extract dependencies
            dependencies_str = self._extract_field_value(row, column_mapping, 'dependencies', headers)
            dependencies = self._parse_dependencies(dependencies_str)
            
            # Create Milestone object
            milestone = Milestone(
                milestone_id=milestone_id,
                name=name,
                description=description,
                target_date=target_date,
                actual_date=actual_date,
                status=status,
                milestone_type=milestone_type,
                owner=owner,
                dependencies=dependencies,
                approver=approver
            )
            
            return milestone
            
        except Exception as e:
            logger.warning(f"Failed to create milestone from row: {e}")
            return None
    
    def _extract_field_value(self, row: Dict[str, str], column_mapping: Dict[str, str], field: str, headers: List[str]) -> Optional[str]:
        """Extract field value from row using column mapping."""
        if field in column_mapping:
            column_name = column_mapping[field]
            return row.get(column_name, '').strip()
        
        # Fallback: try to find field directly in row
        for key, value in row.items():
            if field.lower() in key.lower():
                return value.strip()
        
        return None
    
    def _find_milestone_entries_in_text(self, content: str) -> List[str]:
        """Find potential milestone entries in text content."""
        entries = []
        
        # Split by common delimiters
        sections = re.split(r'\n\s*\n|\n-{3,}|\n={3,}', content)
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            # Check if section contains milestone-related keywords
            section_lower = section.lower()
            if any(keyword in section_lower for keyword in self.milestone_keywords):
                entries.append(section)
            
            # Also check for date patterns that might indicate milestones
            if re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', section):
                entries.append(section)
        
        return entries
    
    def _create_milestone_from_text_entry(self, entry: str) -> Optional[Milestone]:
        """Create a Milestone object from a text entry."""
        try:
            # Extract information using regex patterns
            milestone_id_match = self.milestone_patterns['milestone_id'].search(entry)
            milestone_id = None
            
            if milestone_id_match:
                milestone_id = milestone_id_match.group(1)
            else:
                # Try to extract ID from "Milestone M001:" pattern
                milestone_pattern = re.search(r'milestone\s+([A-Za-z0-9_-]+):', entry, re.IGNORECASE)
                if milestone_pattern:
                    milestone_id = milestone_pattern.group(1)
                else:
                    milestone_id = f"MS-{len(entry.split())}"
            
            # Use first line or first sentence as name
            lines = [line.strip() for line in entry.split('\n') if line.strip()]
            name = lines[0][:100] if lines else "Untitled Milestone"
            
            # Clean up name if it contains patterns
            if ':' in name and any(term in name.lower() for term in ['milestone', 'deadline', 'target']):
                name_parts = name.split(':', 1)
                if len(name_parts) > 1:
                    name = name_parts[1].strip()
            
            description = entry.strip()
            
            # Extract target date
            target_date_match = self.milestone_patterns['target_date'].search(entry)
            target_date = self._parse_date(target_date_match.group(1) if target_date_match else None)
            if not target_date:
                target_date = date.today()
            
            # Extract status
            status_match = self.milestone_patterns['status'].search(entry)
            status = self._parse_status(status_match.group(1) if status_match else None)
            
            # Extract owner
            owner_match = self.milestone_patterns['owner'].search(entry)
            if owner_match:
                owner = owner_match.group(1).strip()
                # Clean up owner field - remove extra text after newlines
                owner = owner.split('\n')[0].strip()
            else:
                owner = ""
            
            # Extract dependencies
            deps_match = self.milestone_patterns['dependencies'].search(entry)
            dependencies = self._parse_dependencies(deps_match.group(1) if deps_match else None)
            
            # Create Milestone object
            milestone = Milestone(
                milestone_id=milestone_id,
                name=name,
                description=description,
                target_date=target_date,
                status=status,
                owner=owner,
                dependencies=dependencies
            )
            
            return milestone
            
        except Exception as e:
            logger.warning(f"Failed to create milestone from text entry: {e}")
            return None
    
    def _determine_status_from_task(self, task: Dict[str, Any]) -> MilestoneStatus:
        """Determine milestone status from MPP task data."""
        # Check if task is completed
        if task.get('percent_complete', 0) >= 100:
            return MilestoneStatus.COMPLETED
        
        # Check if task is in progress
        if task.get('percent_complete', 0) > 0:
            return MilestoneStatus.IN_PROGRESS
        
        # Check if task is overdue
        finish_date = self._parse_date(task.get('finish_date'))
        if finish_date and finish_date < date.today():
            return MilestoneStatus.OVERDUE
        
        return MilestoneStatus.UPCOMING
    
    def _parse_status(self, value: Optional[str]) -> MilestoneStatus:
        """Parse status value from string."""
        if not value:
            return MilestoneStatus.UPCOMING
        
        value_lower = value.lower().replace('_', ' ').replace('-', ' ')
        
        if any(term in value_lower for term in ['completed', 'done', 'finished']):
            return MilestoneStatus.COMPLETED
        elif any(term in value_lower for term in ['in progress', 'active', 'working']):
            return MilestoneStatus.IN_PROGRESS
        elif any(term in value_lower for term in ['overdue', 'late', 'delayed']):
            return MilestoneStatus.OVERDUE
        elif any(term in value_lower for term in ['cancelled', 'canceled', 'dropped']):
            return MilestoneStatus.CANCELLED
        else:
            return MilestoneStatus.UPCOMING
    
    def _parse_date(self, value: Optional[str]) -> Optional[date]:
        """Parse date value from string."""
        if not value:
            return None
        
        # Handle datetime objects from MPP files
        if isinstance(value, datetime):
            return value.date()
        elif isinstance(value, date):
            return value
        
        try:
            # Try common date formats
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d', '%m-%d-%Y', '%d-%m-%Y']:
                try:
                    return datetime.strptime(str(value).strip(), fmt).date()
                except ValueError:
                    continue
            
            return None
            
        except Exception:
            return None
    
    def _parse_dependencies(self, value: Optional[str]) -> List[str]:
        """Parse dependencies from string."""
        if not value:
            return []
        
        # Split by common delimiters
        deps = re.split(r'[,;|\n]', value.strip())
        
        # Clean up and filter dependencies
        cleaned_deps = []
        for dep in deps:
            dep = dep.strip()
            if dep and len(dep) > 1:  # Ignore single characters
                cleaned_deps.append(dep)
        
        return cleaned_deps