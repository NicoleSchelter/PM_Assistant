"""
Markdown file handler for PM Analysis Tool.

This module provides functionality to parse and extract structured data from
Markdown files commonly used in project management documentation.
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging

from file_handlers.base_handler import BaseFileHandler
from core.models import ValidationResult, DocumentType
from utils.exceptions import FileProcessingError, ValidationError, DataExtractionError
from utils.logger import get_logger

logger = get_logger(__name__)


class MarkdownHandler(BaseFileHandler):
    """
    Handler for processing Markdown files.
    
    This handler can extract structured data from Markdown files including:
    - Document metadata (title, headers)
    - Tables and their data
    - Section content
    - Lists and structured information
    """
    
    def __init__(self):
        """Initialize the Markdown handler."""
        super().__init__()
        self.supported_extensions = ['md', 'markdown']
        self.handler_name = "Markdown Handler"
        
        # Regex patterns for parsing markdown elements
        self._header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        self._table_pattern = re.compile(
            r'^\|(.+)\|\s*\n\|[-\s|:]+\|\s*\n((?:\|.+\|\s*\n?)*)',
            re.MULTILINE
        )
        self._list_pattern = re.compile(r'^[\s]*[-*+]\s+(.+)$', re.MULTILINE)
        self._numbered_list_pattern = re.compile(r'^[\s]*\d+\.\s+(.+)$', re.MULTILINE)
        self._metadata_pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
    
    def can_handle(self, file_path: str) -> bool:
        """
        Check if this handler can process the given file.
        
        Args:
            file_path (str): Path to the file to check
            
        Returns:
            bool: True if file has .md or .markdown extension
        """
        try:
            path = Path(file_path)
            extension = path.suffix.lower().lstrip('.')
            return extension in self.supported_extensions
        except Exception as e:
            logger.warning(f"Error checking file compatibility for {file_path}: {e}")
            return False
    
    def extract_data(self, file_path: str) -> Dict[str, Any]:
        """
        Extract structured data from a Markdown file.
        
        Args:
            file_path (str): Path to the Markdown file
            
        Returns:
            Dict[str, Any]: Extracted data including title, sections, tables, and metadata
            
        Raises:
            FileProcessingError: If the file cannot be read or processed
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileProcessingError(f"File not found: {file_path}")
            
            # Read file content
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read()
            except UnicodeDecodeError:
                # Try with different encoding
                with open(path, 'r', encoding='latin-1') as file:
                    content = file.read()
            
            # Extract different components
            metadata = self._extract_metadata(content)
            title = self._extract_title(content)
            headers = self._extract_headers(content)
            tables = self._extract_tables(content)
            sections = self._extract_sections(content, headers)
            lists = self._extract_lists(content)
            
            # Determine document type based on content
            document_type = self._determine_document_type(content, path.name)
            
            extracted_data = {
                'file_path': str(path.absolute()),
                'filename': path.name,
                'document_type': document_type.value,
                'title': title,
                'metadata': metadata,
                'headers': headers,
                'sections': sections,
                'tables': tables,
                'lists': lists,
                'raw_content': content,
                'word_count': len(content.split()),
                'line_count': len(content.splitlines())
            }
            
            logger.info(f"Successfully extracted data from {file_path}")
            return extracted_data
            
        except Exception as e:
            error_msg = f"Failed to extract data from {file_path}: {str(e)}"
            logger.error(error_msg)
            raise FileProcessingError(error_msg) from e
    
    def validate_structure(self, file_path: str) -> ValidationResult:
        """
        Validate the Markdown file structure and content.
        
        Args:
            file_path (str): Path to the file to validate
            
        Returns:
            ValidationResult: Validation result with success status and messages
        """
        result = ValidationResult(is_valid=True)
        
        try:
            path = Path(file_path)
            
            # Check if file exists
            if not path.exists():
                result.add_error(f"File does not exist: {file_path}")
                return result
            
            # Check if file is readable
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read()
            except UnicodeDecodeError:
                try:
                    with open(path, 'r', encoding='latin-1') as file:
                        content = file.read()
                except Exception as e:
                    result.add_error(f"Cannot read file with any encoding: {e}")
                    return result
            except Exception as e:
                result.add_error(f"Cannot read file: {e}")
                return result
            
            # Check if file is empty
            if not content.strip():
                result.add_warning("File is empty")
            
            # Validate basic markdown structure
            self._validate_markdown_syntax(content, result)
            
            # Check for common project management document elements
            self._validate_pm_document_structure(content, result, path.name)
            
            logger.info(f"Validation completed for {file_path}: {'VALID' if result.is_valid else 'INVALID'}")
            
        except Exception as e:
            result.add_error(f"Validation failed: {str(e)}")
            logger.error(f"Validation error for {file_path}: {e}")
        
        return result
    
    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """Extract YAML front matter metadata from markdown content."""
        metadata = {}
        
        match = self._metadata_pattern.match(content)
        if match:
            try:
                import yaml
                metadata = yaml.safe_load(match.group(1)) or {}
            except ImportError:
                logger.warning("PyYAML not available, skipping metadata extraction")
            except Exception as e:
                logger.warning(f"Failed to parse metadata: {e}")
        
        return metadata
    
    def _extract_title(self, content: str) -> Optional[str]:
        """Extract the main title from markdown content."""
        # Look for H1 header first
        h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if h1_match:
            return h1_match.group(1).strip()
        
        # Look for title in metadata
        metadata = self._extract_metadata(content)
        if 'title' in metadata:
            return str(metadata['title'])
        
        # Look for underlined title
        underline_match = re.search(r'^(.+)\n=+\s*$', content, re.MULTILINE)
        if underline_match:
            return underline_match.group(1).strip()
        
        return None
    
    def _extract_headers(self, content: str) -> List[Dict[str, Any]]:
        """Extract all headers from markdown content."""
        headers = []
        
        for match in self._header_pattern.finditer(content):
            level = len(match.group(1))
            text = match.group(2).strip()
            
            headers.append({
                'level': level,
                'text': text,
                'position': match.start()
            })
        
        return headers
    
    def _extract_tables(self, content: str) -> List[Dict[str, Any]]:
        """Extract tables from markdown content."""
        tables = []
        
        for match in self._table_pattern.finditer(content):
            header_row = match.group(1)
            data_rows = match.group(2)
            
            # Parse header
            headers = [col.strip() for col in header_row.split('|') if col.strip()]
            
            # Parse data rows
            rows = []
            for line in data_rows.strip().split('\n'):
                if line.strip() and line.strip().startswith('|'):
                    row_data = [col.strip() for col in line.split('|')[1:-1]]
                    if len(row_data) == len(headers):
                        row_dict = dict(zip(headers, row_data))
                        rows.append(row_dict)
            
            if headers and rows:
                tables.append({
                    'headers': headers,
                    'rows': rows,
                    'row_count': len(rows),
                    'position': match.start()
                })
        
        return tables
    
    def _extract_sections(self, content: str, headers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract content sections based on headers."""
        sections = []
        
        if not headers:
            return sections
        
        content_lines = content.splitlines()
        
        for i, header in enumerate(headers):
            start_line = content[:header['position']].count('\n')
            
            # Find end position (next header of same or higher level)
            end_line = len(content_lines)
            for j in range(i + 1, len(headers)):
                if headers[j]['level'] <= header['level']:
                    end_line = content[:headers[j]['position']].count('\n')
                    break
            
            # Extract section content
            section_lines = content_lines[start_line + 1:end_line]
            section_content = '\n'.join(section_lines).strip()
            
            sections.append({
                'title': header['text'],
                'level': header['level'],
                'content': section_content,
                'word_count': len(section_content.split()) if section_content else 0,
                'start_line': start_line,
                'end_line': end_line
            })
        
        return sections
    
    def _extract_lists(self, content: str) -> Dict[str, List[str]]:
        """Extract bulleted and numbered lists from content."""
        lists = {
            'bulleted': [],
            'numbered': []
        }
        
        # Extract bulleted lists
        for match in self._list_pattern.finditer(content):
            lists['bulleted'].append(match.group(1).strip())
        
        # Extract numbered lists
        for match in self._numbered_list_pattern.finditer(content):
            lists['numbered'].append(match.group(1).strip())
        
        return lists
    
    def _determine_document_type(self, content: str, filename: str) -> DocumentType:
        """Determine the type of project management document based on content and filename."""
        content_lower = content.lower()
        filename_lower = filename.lower()
        
        # Check filename patterns first
        if any(keyword in filename_lower for keyword in ['risk', 'risks']):
            return DocumentType.RISK_REGISTER
        elif any(keyword in filename_lower for keyword in ['stakeholder', 'stakeholders']):
            return DocumentType.STAKEHOLDER_REGISTER
        elif any(keyword in filename_lower for keyword in ['wbs', 'work breakdown', 'breakdown']):
            return DocumentType.WBS
        elif any(keyword in filename_lower for keyword in ['roadmap', 'timeline', 'schedule']):
            return DocumentType.ROADMAP
        elif any(keyword in filename_lower for keyword in ['charter', 'project charter']):
            return DocumentType.CHARTER
        elif any(keyword in filename_lower for keyword in ['requirements', 'requirement']):
            return DocumentType.REQUIREMENTS
        elif any(keyword in filename_lower for keyword in ['status', 'report']):
            return DocumentType.STATUS_REPORT
        
        # Check content patterns
        if any(keyword in content_lower for keyword in ['risk register', 'risk management', 'risk assessment']):
            return DocumentType.RISK_REGISTER
        elif any(keyword in content_lower for keyword in ['stakeholder register', 'stakeholder analysis']):
            return DocumentType.STAKEHOLDER_REGISTER
        elif any(keyword in content_lower for keyword in ['work breakdown structure', 'deliverables']):
            return DocumentType.WBS
        elif any(keyword in content_lower for keyword in ['milestone', 'timeline', 'project schedule']):
            return DocumentType.ROADMAP
        elif any(keyword in content_lower for keyword in ['project charter', 'project scope']):
            return DocumentType.CHARTER
        
        return DocumentType.UNKNOWN
    
    def _validate_markdown_syntax(self, content: str, result: ValidationResult) -> None:
        """Validate basic markdown syntax."""
        lines = content.splitlines()
        
        for i, line in enumerate(lines, 1):
            # Check for malformed headers
            if line.strip().startswith('#'):
                if not re.match(r'^#{1,6}\s+.+', line):
                    result.add_warning(f"Line {i}: Malformed header - headers should have space after #")
            
            # Check for malformed tables
            if '|' in line and line.strip().startswith('|'):
                if not line.strip().endswith('|'):
                    result.add_warning(f"Line {i}: Table row should end with |")
    
    def _validate_pm_document_structure(self, content: str, result: ValidationResult, filename: str) -> None:
        """Validate project management document structure."""
        content_lower = content.lower()
        
        # Check for common PM document elements
        if 'risk' in filename.lower():
            if not any(keyword in content_lower for keyword in ['probability', 'impact', 'mitigation']):
                result.add_warning("Risk document should contain probability, impact, or mitigation information")
        
        elif 'stakeholder' in filename.lower():
            if not any(keyword in content_lower for keyword in ['role', 'influence', 'interest']):
                result.add_warning("Stakeholder document should contain role, influence, or interest information")
        
        elif 'wbs' in filename.lower() or 'breakdown' in filename.lower():
            if not any(keyword in content_lower for keyword in ['deliverable', 'task', 'work package']):
                result.add_warning("WBS document should contain deliverable, task, or work package information")
        
        # Check for tables in documents that typically need them
        tables = self._extract_tables(content)
        if not tables and any(keyword in filename.lower() for keyword in ['register', 'wbs', 'breakdown']):
            result.add_warning("Document appears to be a register or structured document but contains no tables")