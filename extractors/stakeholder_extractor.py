"""
Stakeholder data extraction module for PM Analysis Tool.

This module provides functionality to extract stakeholder information from various
document formats including Markdown, Excel, and other stakeholder register files.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
from pathlib import Path
import logging

from core.domain import Stakeholder, StakeholderInfluence, StakeholderInterest
from file_handlers.base_handler import BaseFileHandler
from file_handlers.markdown_handler import MarkdownHandler
from file_handlers.excel_handler import ExcelHandler
from utils.exceptions import DataExtractionError, FileProcessingError
from utils.validators import validate_email, validate_phone_number
from utils.logger import get_logger
from utils.error_handling import handle_errors, safe_execute, ErrorAggregator

logger = get_logger(__name__)


class StakeholderExtractor:
    """
    Extracts stakeholder information from various document formats.
    
    This class can process stakeholder register documents in multiple formats
    and extract structured stakeholder data including roles, contact details,
    influence levels, and engagement information.
    """
    
    def __init__(self):
        """Initialize the stakeholder extractor with file handlers."""
        self.markdown_handler = MarkdownHandler()
        self.excel_handler = ExcelHandler()
        
        # Common stakeholder-related keywords for identification
        self.stakeholder_keywords = [
            'stakeholder', 'contact', 'role', 'influence', 'interest',
            'engagement', 'communication', 'sponsor', 'user', 'customer'
        ]
        
        # Patterns for extracting stakeholder information from text
        self.stakeholder_patterns = {
            'stakeholder_id': re.compile(r'(?:stakeholder\s*(?:id)?|id)[:=\s]*([A-Za-z0-9_-]+)', re.IGNORECASE),
            'email': re.compile(r'(?:email|e-mail)[:=\s]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', re.IGNORECASE),
            'phone': re.compile(r'(?:phone|tel|mobile)[:=\s]*([\+]?[\d\s\-\(\)\.]{7,20})', re.IGNORECASE),
            'role': re.compile(r'(?:role|position|title)[:=\s]*([A-Za-z\s]+)', re.IGNORECASE),
            'organization': re.compile(r'(?:organization|company|org)[:=\s]*([A-Za-z\s&.,]+)', re.IGNORECASE),
            'influence': re.compile(r'(?:influence|power)[:=\s]*(high|medium|low|very\s*high)', re.IGNORECASE),
            'interest': re.compile(r'(?:interest|engagement)[:=\s]*(high|medium|low|very\s*high)', re.IGNORECASE),
            'sentiment': re.compile(r'(?:sentiment|attitude)[:=\s]*(supportive|neutral|resistant)', re.IGNORECASE)
        }
    
    def extract_stakeholders(self, file_path: str) -> List[Stakeholder]:
        """
        Extract stakeholders from a file.
        
        Args:
            file_path (str): Path to the file containing stakeholder information
            
        Returns:
            List[Stakeholder]: List of extracted Stakeholder objects
            
        Raises:
            DataExtractionError: If extraction fails
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise DataExtractionError(f"File not found: {file_path}")
            
            logger.info(f"Extracting stakeholders from {file_path}")
            
            # Determine file type and use appropriate handler
            if self.markdown_handler.can_handle(file_path):
                return self._extract_from_markdown(file_path)
            elif self.excel_handler.can_handle(file_path):
                return self._extract_from_excel(file_path)
            else:
                raise DataExtractionError(f"Unsupported file format: {path.suffix}")
                
        except Exception as e:
            error_msg = f"Failed to extract stakeholders from {file_path}: {str(e)}"
            logger.error(error_msg)
            raise DataExtractionError(error_msg) from e
    
    def _extract_from_markdown(self, file_path: str) -> List[Stakeholder]:
        """Extract stakeholders from a Markdown file."""
        try:
            data = self.markdown_handler.extract_data(file_path)
            stakeholders = []
            
            # Extract from tables first (most structured)
            for table in data.get('tables', []):
                table_stakeholders = self._extract_from_table_data(table)
                stakeholders.extend(table_stakeholders)
            
            # Extract from sections if no table data found
            if not stakeholders:
                for section in data.get('sections', []):
                    section_stakeholders = self._extract_from_text_section(section)
                    stakeholders.extend(section_stakeholders)
            
            # If still no stakeholders found, try parsing the entire content
            if not stakeholders:
                content_stakeholders = self._extract_from_raw_text(data.get('raw_content', ''))
                stakeholders.extend(content_stakeholders)
            
            logger.info(f"Extracted {len(stakeholders)} stakeholders from markdown file {file_path}")
            return stakeholders
            
        except Exception as e:
            raise DataExtractionError(f"Failed to extract from markdown: {str(e)}") from e
    
    def _extract_from_excel(self, file_path: str) -> List[Stakeholder]:
        """Extract stakeholders from an Excel file."""
        try:
            data = self.excel_handler.extract_data(file_path)
            stakeholders = []
            
            # Process each sheet
            for sheet_name, sheet_data in data.get('sheets', {}).items():
                if self._is_stakeholder_sheet(sheet_name, sheet_data):
                    sheet_stakeholders = self._extract_from_excel_sheet(sheet_data)
                    stakeholders.extend(sheet_stakeholders)
            
            logger.info(f"Extracted {len(stakeholders)} stakeholders from Excel file {file_path}")
            return stakeholders
            
        except Exception as e:
            raise DataExtractionError(f"Failed to extract from Excel: {str(e)}") from e
    
    def _extract_from_table_data(self, table: Dict[str, Any]) -> List[Stakeholder]:
        """Extract stakeholders from table data."""
        stakeholders = []
        headers = [h.lower().strip() for h in table.get('headers', [])]
        
        # Map common column names to our fields
        column_mapping = self._create_column_mapping(headers)
        
        for row in table.get('rows', []):
            try:
                stakeholder = self._create_stakeholder_from_row(row, column_mapping, headers)
                if stakeholder:
                    stakeholders.append(stakeholder)
            except Exception as e:
                logger.warning(f"Failed to create stakeholder from row {row}: {e}")
                continue
        
        return stakeholders
    
    def _extract_from_text_section(self, section: Dict[str, Any]) -> List[Stakeholder]:
        """Extract stakeholders from a text section."""
        stakeholders = []
        content = section.get('content', '')
        
        # Look for stakeholder entries in the text
        stakeholder_entries = self._find_stakeholder_entries_in_text(content)
        
        for entry in stakeholder_entries:
            try:
                stakeholder = self._create_stakeholder_from_text_entry(entry)
                if stakeholder:
                    stakeholders.append(stakeholder)
            except Exception as e:
                logger.warning(f"Failed to create stakeholder from text entry: {e}")
                continue
        
        return stakeholders
    
    def _extract_from_raw_text(self, content: str) -> List[Stakeholder]:
        """Extract stakeholders from raw text content."""
        stakeholders = []
        
        # Split content into potential stakeholder entries
        stakeholder_entries = self._find_stakeholder_entries_in_text(content)
        
        for entry in stakeholder_entries:
            try:
                stakeholder = self._create_stakeholder_from_text_entry(entry)
                if stakeholder:
                    stakeholders.append(stakeholder)
            except Exception as e:
                logger.warning(f"Failed to create stakeholder from raw text: {e}")
                continue
        
        return stakeholders
    
    def _extract_from_excel_sheet(self, sheet_data: Dict[str, Any]) -> List[Stakeholder]:
        """Extract stakeholders from Excel sheet data."""
        stakeholders = []
        
        if 'data' not in sheet_data:
            return stakeholders
        
        data_rows = sheet_data['data']
        if not data_rows:
            return stakeholders
        
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
                
                stakeholder = self._create_stakeholder_from_row(row_dict, column_mapping, headers)
                if stakeholder:
                    stakeholders.append(stakeholder)
            except Exception as e:
                logger.warning(f"Failed to create stakeholder from Excel row: {e}")
                continue
        
        return stakeholders
    
    def _is_stakeholder_sheet(self, sheet_name: str, sheet_data: Dict[str, Any]) -> bool:
        """Check if an Excel sheet contains stakeholder data."""
        sheet_name_lower = sheet_name.lower()
        
        # Check sheet name for stakeholder-related keywords
        if any(keyword in sheet_name_lower for keyword in self.stakeholder_keywords):
            return True
        
        # Check if sheet has stakeholder-related column headers
        if 'data' in sheet_data and sheet_data['data']:
            headers = [str(cell).lower() for cell in sheet_data['data'][0] if cell]
            if any(keyword in ' '.join(headers) for keyword in self.stakeholder_keywords):
                return True
        
        return False
    
    def _create_column_mapping(self, headers: List[str]) -> Dict[str, str]:
        """Create mapping from column headers to stakeholder fields."""
        mapping = {}
        
        for header in headers:
            header_lower = header.lower().strip()
            
            # Map common variations to standard fields
            if any(term in header_lower for term in ['id', 'stakeholder id']):
                mapping['stakeholder_id'] = header
            elif any(term in header_lower for term in ['name', 'stakeholder name', 'contact name']):
                mapping['name'] = header
            elif any(term in header_lower for term in ['role', 'position', 'title']):
                mapping['role'] = header
            elif any(term in header_lower for term in ['organization', 'company', 'org']):
                mapping['organization'] = header
            elif any(term in header_lower for term in ['email', 'e-mail', 'mail']):
                mapping['email'] = header
            elif any(term in header_lower for term in ['phone', 'telephone', 'mobile', 'contact']):
                mapping['phone'] = header
            elif any(term in header_lower for term in ['influence', 'power']):
                mapping['influence'] = header
            elif any(term in header_lower for term in ['interest', 'engagement']):
                mapping['interest'] = header
            elif any(term in header_lower for term in ['strategy', 'engagement strategy']):
                mapping['engagement_strategy'] = header
            elif any(term in header_lower for term in ['communication', 'comm frequency']):
                mapping['communication_frequency'] = header
            elif any(term in header_lower for term in ['sentiment', 'attitude']):
                mapping['current_sentiment'] = header
            elif any(term in header_lower for term in ['concerns', 'issues']):
                mapping['key_concerns'] = header
            elif any(term in header_lower for term in ['expectations', 'expect']):
                mapping['expectations'] = header
        
        return mapping
    
    def _create_stakeholder_from_row(self, row: Dict[str, str], column_mapping: Dict[str, str], headers: List[str]) -> Optional[Stakeholder]:
        """Create a Stakeholder object from a table row."""
        try:
            # Extract basic required fields
            stakeholder_id = self._extract_field_value(row, column_mapping, 'stakeholder_id', headers)
            if not stakeholder_id:
                # Generate ID if not found
                stakeholder_id = f"SH-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            name = self._extract_field_value(row, column_mapping, 'name', headers)
            if not name:
                name = "Unnamed Stakeholder"
            
            role = self._extract_field_value(row, column_mapping, 'role', headers) or ""
            organization = self._extract_field_value(row, column_mapping, 'organization', headers) or ""
            
            # Extract contact information
            email = self._extract_field_value(row, column_mapping, 'email', headers) or ""
            phone = self._extract_field_value(row, column_mapping, 'phone', headers) or ""
            
            # Validate contact information
            if email:
                try:
                    email = validate_email(email)
                except:
                    email = ""  # Invalid email, set to empty
            
            if phone:
                try:
                    phone = validate_phone_number(phone)
                except:
                    phone = ""  # Invalid phone, set to empty
            
            # Extract influence and interest
            influence_str = self._extract_field_value(row, column_mapping, 'influence', headers)
            influence = self._parse_influence(influence_str)
            
            interest_str = self._extract_field_value(row, column_mapping, 'interest', headers)
            interest = self._parse_interest(interest_str)
            
            # Extract other fields
            engagement_strategy = self._extract_field_value(row, column_mapping, 'engagement_strategy', headers) or ""
            communication_frequency = self._extract_field_value(row, column_mapping, 'communication_frequency', headers) or ""
            current_sentiment = self._extract_field_value(row, column_mapping, 'current_sentiment', headers) or ""
            
            # Extract concerns and expectations
            concerns_str = self._extract_field_value(row, column_mapping, 'key_concerns', headers)
            key_concerns = self._parse_list_field(concerns_str)
            
            expectations_str = self._extract_field_value(row, column_mapping, 'expectations', headers)
            expectations = self._parse_list_field(expectations_str)
            
            # Create Stakeholder object
            stakeholder = Stakeholder(
                stakeholder_id=stakeholder_id,
                name=name,
                role=role,
                organization=organization,
                email=email,
                phone=phone,
                influence=influence,
                interest=interest,
                engagement_strategy=engagement_strategy,
                communication_frequency=communication_frequency,
                current_sentiment=current_sentiment,
                key_concerns=key_concerns,
                expectations=expectations
            )
            
            return stakeholder
            
        except Exception as e:
            logger.warning(f"Failed to create stakeholder from row: {e}")
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
    
    def _find_stakeholder_entries_in_text(self, content: str) -> List[str]:
        """Find potential stakeholder entries in text content."""
        entries = []
        
        # Split by common delimiters
        sections = re.split(r'\n\s*\n|\n-{3,}|\n={3,}', content)
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            # Check if section contains stakeholder-related keywords
            section_lower = section.lower()
            if any(keyword in section_lower for keyword in self.stakeholder_keywords):
                entries.append(section)
            
            # Also check for email patterns that might indicate stakeholder info
            if re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', section):
                entries.append(section)
        
        return entries
    
    def _create_stakeholder_from_text_entry(self, entry: str) -> Optional[Stakeholder]:
        """Create a Stakeholder object from a text entry."""
        try:
            # Extract information using regex patterns
            stakeholder_id_match = self.stakeholder_patterns['stakeholder_id'].search(entry)
            stakeholder_id = None
            
            if stakeholder_id_match:
                stakeholder_id = stakeholder_id_match.group(1)
            else:
                # Try to extract ID from "Stakeholder SH001:" pattern
                stakeholder_pattern = re.search(r'stakeholder\s+([A-Za-z0-9_-]+):', entry, re.IGNORECASE)
                if stakeholder_pattern:
                    stakeholder_id = stakeholder_pattern.group(1)
                else:
                    stakeholder_id = f"SH-{len(entry.split())}"
            
            # Use first line or first sentence as name
            lines = [line.strip() for line in entry.split('\n') if line.strip()]
            name = lines[0][:100] if lines else "Unnamed Stakeholder"
            
            # Clean up name if it contains patterns
            if ':' in name and any(term in name.lower() for term in ['stakeholder', 'contact', 'name']):
                name_parts = name.split(':', 1)
                if len(name_parts) > 1:
                    name = name_parts[1].strip()
            
            # Extract role
            role_match = self.stakeholder_patterns['role'].search(entry)
            if role_match:
                role = role_match.group(1).strip()
                # Clean up role field - remove extra text after newlines
                role = role.split('\n')[0].strip()
            else:
                role = ""
            
            # Extract organization
            org_match = self.stakeholder_patterns['organization'].search(entry)
            if org_match:
                organization = org_match.group(1).strip()
                organization = organization.split('\n')[0].strip()
            else:
                organization = ""
            
            # Extract contact information
            email_match = self.stakeholder_patterns['email'].search(entry)
            email = email_match.group(1).strip() if email_match else ""
            
            phone_match = self.stakeholder_patterns['phone'].search(entry)
            phone = phone_match.group(1).strip() if phone_match else ""
            
            # Extract influence and interest
            influence_match = self.stakeholder_patterns['influence'].search(entry)
            influence = self._parse_influence(influence_match.group(1) if influence_match else None)
            
            interest_match = self.stakeholder_patterns['interest'].search(entry)
            interest = self._parse_interest(interest_match.group(1) if interest_match else None)
            
            # Extract sentiment
            sentiment_match = self.stakeholder_patterns['sentiment'].search(entry)
            current_sentiment = sentiment_match.group(1).strip() if sentiment_match else ""
            
            # Create Stakeholder object
            stakeholder = Stakeholder(
                stakeholder_id=stakeholder_id,
                name=name,
                role=role,
                organization=organization,
                email=email,
                phone=phone,
                influence=influence,
                interest=interest,
                current_sentiment=current_sentiment
            )
            
            return stakeholder
            
        except Exception as e:
            logger.warning(f"Failed to create stakeholder from text entry: {e}")
            return None
    
    def _parse_influence(self, value: Optional[str]) -> StakeholderInfluence:
        """Parse influence value from string."""
        if not value:
            return StakeholderInfluence.MEDIUM
        
        value_lower = value.lower().strip()
        
        if any(term in value_lower for term in ['very high', 'very_high', 'critical']):
            return StakeholderInfluence.VERY_HIGH
        elif any(term in value_lower for term in ['high', 'strong']):
            return StakeholderInfluence.HIGH
        elif any(term in value_lower for term in ['medium', 'moderate', 'average']):
            return StakeholderInfluence.MEDIUM
        elif any(term in value_lower for term in ['low', 'weak', 'minimal']):
            return StakeholderInfluence.LOW
        else:
            return StakeholderInfluence.MEDIUM
    
    def _parse_interest(self, value: Optional[str]) -> StakeholderInterest:
        """Parse interest value from string."""
        if not value:
            return StakeholderInterest.MEDIUM
        
        value_lower = value.lower().strip()
        
        if any(term in value_lower for term in ['very high', 'very_high', 'critical']):
            return StakeholderInterest.VERY_HIGH
        elif any(term in value_lower for term in ['high', 'strong']):
            return StakeholderInterest.HIGH
        elif any(term in value_lower for term in ['medium', 'moderate', 'average']):
            return StakeholderInterest.MEDIUM
        elif any(term in value_lower for term in ['low', 'weak', 'minimal']):
            return StakeholderInterest.LOW
        else:
            return StakeholderInterest.MEDIUM
    
    def _parse_list_field(self, value: Optional[str]) -> List[str]:
        """Parse list field from string."""
        if not value:
            return []
        
        # Split by common delimiters
        items = re.split(r'[,;|\n]', value.strip())
        
        # Clean up and filter items
        cleaned_items = []
        for item in items:
            item = item.strip()
            if item and len(item) > 1:  # Ignore single characters
                cleaned_items.append(item)
        
        return cleaned_items