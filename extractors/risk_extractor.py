"""
Risk data extraction module for PM Analysis Tool.

This module provides functionality to extract risk information from various
document formats including Markdown, Excel, and other project management files.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
from pathlib import Path
import logging

from core.domain import Risk, RiskPriority, RiskStatus
from file_handlers.base_handler import BaseFileHandler
from file_handlers.markdown_handler import MarkdownHandler
from file_handlers.excel_handler import ExcelHandler
from utils.exceptions import DataExtractionError
from utils.validators import validate_probability, validate_date_string

logger = logging.getLogger(__name__)


class RiskExtractor:
    """
    Extracts risk information from various document formats.
    
    This class can process risk management documents in multiple formats
    and extract structured risk data including ID, description, probability,
    impact, status, mitigation strategies, and ownership information.
    """
    
    def __init__(self):
        """Initialize the risk extractor with file handlers."""
        self.markdown_handler = MarkdownHandler()
        self.excel_handler = ExcelHandler()
        
        # Common risk-related keywords for identification
        self.risk_keywords = [
            'risk', 'threat', 'opportunity', 'hazard', 'issue',
            'probability', 'impact', 'mitigation', 'contingency'
        ]
        
        # Patterns for extracting risk information from text
        self.risk_patterns = {
            'risk_id': re.compile(r'(?:risk\s*(?:id|#)?:?\s*)?([A-Z]{1,3}[-_]?\d{1,4})', re.IGNORECASE),
            'probability': re.compile(r'(?:probability|prob|likelihood)[:=\s]*([^\n\r]+)', re.IGNORECASE),
            'impact': re.compile(r'(?:impact|severity)[:=\s]*([^\n\r]+)', re.IGNORECASE),
            'status': re.compile(r'(?:status|state)[:=\s]*(open|closed|mitigated|in[_\s]progress|accepted)', re.IGNORECASE),
            'owner': re.compile(r'(?:owner|assigned\s*to|responsible)[:=\s]*([A-Za-z\s]+)', re.IGNORECASE),
            'due_date': re.compile(r'(?:due|target|deadline)[:=\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', re.IGNORECASE)
        }
    
    def extract_risks(self, file_path: str) -> List[Risk]:
        """
        Extract risks from a file.
        
        Args:
            file_path (str): Path to the file containing risk information
            
        Returns:
            List[Risk]: List of extracted Risk objects
            
        Raises:
            DataExtractionError: If extraction fails
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise DataExtractionError(f"File not found: {file_path}")
            
            logger.info(f"Extracting risks from {file_path}")
            
            # Determine file type and use appropriate handler
            if self.markdown_handler.can_handle(file_path):
                return self._extract_from_markdown(file_path)
            elif self.excel_handler.can_handle(file_path):
                return self._extract_from_excel(file_path)
            else:
                raise DataExtractionError(f"Unsupported file format: {path.suffix}")
                
        except Exception as e:
            error_msg = f"Failed to extract risks from {file_path}: {str(e)}"
            logger.error(error_msg)
            raise DataExtractionError(error_msg) from e
    
    def _extract_from_markdown(self, file_path: str) -> List[Risk]:
        """Extract risks from a Markdown file."""
        try:
            data = self.markdown_handler.extract_data(file_path)
            risks = []
            
            # Extract from tables first (most structured)
            for table in data.get('tables', []):
                table_risks = self._extract_from_table_data(table)
                risks.extend(table_risks)
            
            # Extract from sections if no table data found
            if not risks:
                for section in data.get('sections', []):
                    section_risks = self._extract_from_text_section(section)
                    risks.extend(section_risks)
            
            # If still no risks found, try parsing the entire content
            if not risks:
                content_risks = self._extract_from_raw_text(data.get('raw_content', ''))
                risks.extend(content_risks)
            
            logger.info(f"Extracted {len(risks)} risks from markdown file {file_path}")
            return risks
            
        except Exception as e:
            raise DataExtractionError(f"Failed to extract from markdown: {str(e)}") from e
    
    def _extract_from_excel(self, file_path: str) -> List[Risk]:
        """Extract risks from an Excel file."""
        try:
            data = self.excel_handler.extract_data(file_path)
            risks = []
            
            # Process each sheet
            for sheet_name, sheet_data in data.get('sheets', {}).items():
                if self._is_risk_sheet(sheet_name, sheet_data):
                    sheet_risks = self._extract_from_excel_sheet(sheet_data)
                    risks.extend(sheet_risks)
            
            logger.info(f"Extracted {len(risks)} risks from Excel file {file_path}")
            return risks
            
        except Exception as e:
            raise DataExtractionError(f"Failed to extract from Excel: {str(e)}") from e
    
    def _extract_from_table_data(self, table: Dict[str, Any]) -> List[Risk]:
        """Extract risks from table data."""
        risks = []
        headers = [h.lower().strip() for h in table.get('headers', [])]
        
        # Map common column names to our fields
        column_mapping = self._create_column_mapping(headers)
        
        for row in table.get('rows', []):
            try:
                risk = self._create_risk_from_row(row, column_mapping, headers)
                if risk:
                    risks.append(risk)
            except Exception as e:
                logger.warning(f"Failed to create risk from row {row}: {e}")
                continue
        
        return risks
    
    def _extract_from_text_section(self, section: Dict[str, Any]) -> List[Risk]:
        """Extract risks from a text section."""
        risks = []
        content = section.get('content', '')
        
        # Look for risk entries in the text
        risk_entries = self._find_risk_entries_in_text(content)
        
        for entry in risk_entries:
            try:
                risk = self._create_risk_from_text_entry(entry)
                if risk:
                    risks.append(risk)
            except Exception as e:
                logger.warning(f"Failed to create risk from text entry: {e}")
                continue
        
        return risks
    
    def _extract_from_raw_text(self, content: str) -> List[Risk]:
        """Extract risks from raw text content."""
        risks = []
        
        # Split content into potential risk entries
        risk_entries = self._find_risk_entries_in_text(content)
        
        for entry in risk_entries:
            try:
                risk = self._create_risk_from_text_entry(entry)
                if risk:
                    risks.append(risk)
            except Exception as e:
                logger.warning(f"Failed to create risk from raw text: {e}")
                continue
        
        return risks
    
    def _extract_from_excel_sheet(self, sheet_data: Dict[str, Any]) -> List[Risk]:
        """Extract risks from Excel sheet data."""
        risks = []
        
        if 'data' not in sheet_data:
            return risks
        
        data_rows = sheet_data['data']
        if not data_rows:
            return risks
        
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
                
                risk = self._create_risk_from_row(row_dict, column_mapping, headers)
                if risk:
                    risks.append(risk)
            except Exception as e:
                logger.warning(f"Failed to create risk from Excel row: {e}")
                continue
        
        return risks
    
    def _is_risk_sheet(self, sheet_name: str, sheet_data: Dict[str, Any]) -> bool:
        """Check if an Excel sheet contains risk data."""
        sheet_name_lower = sheet_name.lower()
        
        # Check sheet name for risk-related keywords
        if any(keyword in sheet_name_lower for keyword in self.risk_keywords):
            return True
        
        # Check if sheet has risk-related column headers
        if 'data' in sheet_data and sheet_data['data']:
            headers = [str(cell).lower() for cell in sheet_data['data'][0] if cell]
            if any(keyword in ' '.join(headers) for keyword in self.risk_keywords):
                return True
        
        return False
    
    def _create_column_mapping(self, headers: List[str]) -> Dict[str, str]:
        """Create mapping from column headers to risk fields."""
        mapping = {}
        
        for header in headers:
            header_lower = header.lower().strip()
            
            # Map common variations to standard fields
            if any(term in header_lower for term in ['id', 'number', '#']):
                mapping['risk_id'] = header
            elif any(term in header_lower for term in ['title', 'name', 'summary']):
                mapping['title'] = header
            elif any(term in header_lower for term in ['description', 'detail', 'desc']):
                mapping['description'] = header
            elif any(term in header_lower for term in ['category', 'type', 'class']):
                mapping['category'] = header
            elif any(term in header_lower for term in ['probability', 'prob', 'likelihood']):
                mapping['probability'] = header
            elif any(term in header_lower for term in ['impact', 'severity', 'consequence']):
                mapping['impact'] = header
            elif any(term in header_lower for term in ['priority', 'level']):
                mapping['priority'] = header
            elif any(term in header_lower for term in ['status', 'state']):
                mapping['status'] = header
            elif any(term in header_lower for term in ['owner', 'assigned', 'responsible']):
                mapping['owner'] = header
            elif any(term in header_lower for term in ['mitigation', 'response', 'action']):
                mapping['mitigation_strategy'] = header
            elif any(term in header_lower for term in ['contingency', 'backup', 'plan b']):
                mapping['contingency_plan'] = header
            elif any(term in header_lower for term in ['date', 'identified', 'created']):
                mapping['identified_date'] = header
            elif any(term in header_lower for term in ['due', 'target', 'deadline']):
                mapping['target_resolution_date'] = header
        
        return mapping
    
    def _create_risk_from_row(self, row: Dict[str, str], column_mapping: Dict[str, str], headers: List[str]) -> Optional[Risk]:
        """Create a Risk object from a table row."""
        try:
            # Extract basic required fields
            risk_id = self._extract_field_value(row, column_mapping, 'risk_id', headers)
            if not risk_id:
                # Generate ID if not found
                risk_id = f"RISK-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            title = self._extract_field_value(row, column_mapping, 'title', headers)
            if not title:
                title = "Untitled Risk"
            
            description = self._extract_field_value(row, column_mapping, 'description', headers) or ""
            category = self._extract_field_value(row, column_mapping, 'category', headers) or "General"
            
            # Extract probability and impact
            probability_str = self._extract_field_value(row, column_mapping, 'probability', headers)
            probability = self._parse_probability(probability_str)
            
            impact_str = self._extract_field_value(row, column_mapping, 'impact', headers)
            impact = self._parse_impact(impact_str)
            
            # Extract priority
            priority_str = self._extract_field_value(row, column_mapping, 'priority', headers)
            priority = self._parse_priority(priority_str, probability, impact)
            
            # Extract status
            status_str = self._extract_field_value(row, column_mapping, 'status', headers)
            status = self._parse_status(status_str)
            
            # Extract other fields
            owner = self._extract_field_value(row, column_mapping, 'owner', headers) or "Unassigned"
            mitigation_strategy = self._extract_field_value(row, column_mapping, 'mitigation_strategy', headers) or ""
            contingency_plan = self._extract_field_value(row, column_mapping, 'contingency_plan', headers) or ""
            
            # Extract dates
            identified_date = self._parse_date(self._extract_field_value(row, column_mapping, 'identified_date', headers))
            target_resolution_date = self._parse_date(self._extract_field_value(row, column_mapping, 'target_resolution_date', headers))
            
            # Create Risk object
            risk = Risk(
                risk_id=risk_id,
                title=title,
                description=description,
                category=category,
                probability=probability,
                impact=impact,
                priority=priority,
                status=status,
                owner=owner,
                identified_date=identified_date,
                mitigation_strategy=mitigation_strategy,
                contingency_plan=contingency_plan,
                target_resolution_date=target_resolution_date
            )
            
            return risk
            
        except Exception as e:
            logger.warning(f"Failed to create risk from row: {e}")
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
    
    def _find_risk_entries_in_text(self, content: str) -> List[str]:
        """Find potential risk entries in text content."""
        entries = []
        
        # Split by common delimiters
        sections = re.split(r'\n\s*\n|\n-{3,}|\n={3,}', content)
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            # Check if section contains risk-related keywords
            section_lower = section.lower()
            if any(keyword in section_lower for keyword in self.risk_keywords):
                entries.append(section)
        
        return entries
    
    def _create_risk_from_text_entry(self, entry: str) -> Optional[Risk]:
        """Create a Risk object from a text entry."""
        try:
            # Extract information using regex patterns
            risk_id_match = self.risk_patterns['risk_id'].search(entry)
            risk_id = risk_id_match.group(1) if risk_id_match else f"RISK-{len(entry.split())}"
            
            # Use first line or first sentence as title
            lines = [line.strip() for line in entry.split('\n') if line.strip()]
            title = lines[0][:100] if lines else "Untitled Risk"
            
            # If title starts with "Risk ID:", extract the part after the colon
            if ':' in title and title.lower().startswith('risk'):
                title_parts = title.split(':', 1)
                if len(title_parts) > 1:
                    title = title_parts[1].strip()
            
            description = entry.strip()
            category = "General"
            
            # Extract probability and impact
            probability_match = self.risk_patterns['probability'].search(entry)
            probability = self._parse_probability(probability_match.group(1) if probability_match else None)
            
            impact_match = self.risk_patterns['impact'].search(entry)
            impact = self._parse_impact(impact_match.group(1) if impact_match else None)
            
            # Extract status
            status_match = self.risk_patterns['status'].search(entry)
            status = self._parse_status(status_match.group(1) if status_match else None)
            
            # Extract owner
            owner_match = self.risk_patterns['owner'].search(entry)
            if owner_match:
                owner = owner_match.group(1).strip()
                # Clean up owner field - remove extra text after newlines
                owner = owner.split('\n')[0].strip()
            else:
                owner = "Unassigned"
            
            # Calculate priority
            priority = self._parse_priority(None, probability, impact)
            
            # Create Risk object
            risk = Risk(
                risk_id=risk_id,
                title=title,
                description=description,
                category=category,
                probability=probability,
                impact=impact,
                priority=priority,
                status=status,
                owner=owner,
                identified_date=date.today(),
                mitigation_strategy="",
                contingency_plan=""
            )
            
            return risk
            
        except Exception as e:
            logger.warning(f"Failed to create risk from text entry: {e}")
            return None
    
    def _parse_probability(self, value: Optional[str]) -> float:
        """Parse probability value from string."""
        if not value:
            return 0.5  # Default medium probability
        
        # Clean the value - take only the first word/token
        clean_value = value.strip().split()[0] if value.strip() else ""
        
        try:
            # Remove percentage sign and convert
            numeric_value = clean_value.rstrip('%')
            prob = float(numeric_value)
            
            # If value is > 1, assume it's a percentage
            if prob > 1:
                prob = prob / 100
            
            # Ensure value is between 0 and 1
            return max(0.0, min(1.0, prob))
            
        except (ValueError, TypeError):
            # Try to parse text values
            value_lower = clean_value.lower()
            if any(term in value_lower for term in ['high', 'likely', 'probable']):
                return 0.8
            elif any(term in value_lower for term in ['medium', 'moderate', 'possible']):
                return 0.5
            elif any(term in value_lower for term in ['low', 'unlikely', 'rare']):
                return 0.2
            else:
                return 0.5
    
    def _parse_impact(self, value: Optional[str]) -> float:
        """Parse impact value from string."""
        if not value:
            return 0.5  # Default medium impact
        
        # Clean the value - take only the first word/token
        clean_value = value.strip().split()[0] if value.strip() else ""
        
        try:
            # Remove percentage sign and convert
            numeric_value = clean_value.rstrip('%')
            impact = float(numeric_value)
            
            # If value is > 1, assume it's a percentage
            if impact > 1:
                impact = impact / 100
            
            # Ensure value is between 0 and 1
            return max(0.0, min(1.0, impact))
            
        except (ValueError, TypeError):
            # Try to parse text values
            value_lower = clean_value.lower()
            if any(term in value_lower for term in ['high', 'severe', 'critical', 'major']):
                return 0.8
            elif any(term in value_lower for term in ['medium', 'moderate', 'significant']):
                return 0.5
            elif any(term in value_lower for term in ['low', 'minor', 'negligible']):
                return 0.2
            else:
                return 0.5
    
    def _parse_priority(self, value: Optional[str], probability: float, impact: float) -> RiskPriority:
        """Parse priority value from string or calculate from probability and impact."""
        if value:
            value_lower = value.lower()
            if any(term in value_lower for term in ['critical', 'very high', 'urgent']):
                return RiskPriority.CRITICAL
            elif any(term in value_lower for term in ['high', 'important']):
                return RiskPriority.HIGH
            elif any(term in value_lower for term in ['medium', 'moderate']):
                return RiskPriority.MEDIUM
            elif any(term in value_lower for term in ['low', 'minor']):
                return RiskPriority.LOW
        
        # Calculate priority from probability and impact
        risk_score = probability * impact
        
        if risk_score >= 0.64:  # 0.8 * 0.8
            return RiskPriority.CRITICAL
        elif risk_score >= 0.36:  # 0.6 * 0.6
            return RiskPriority.HIGH
        elif risk_score >= 0.16:  # 0.4 * 0.4
            return RiskPriority.MEDIUM
        else:
            return RiskPriority.LOW
    
    def _parse_status(self, value: Optional[str]) -> RiskStatus:
        """Parse status value from string."""
        if not value:
            return RiskStatus.OPEN
        
        value_lower = value.lower().replace('_', ' ').replace('-', ' ')
        
        if any(term in value_lower for term in ['closed', 'resolved', 'complete']):
            return RiskStatus.CLOSED
        elif any(term in value_lower for term in ['mitigated', 'controlled']):
            return RiskStatus.MITIGATED
        elif any(term in value_lower for term in ['in progress', 'active', 'working']):
            return RiskStatus.IN_PROGRESS
        elif any(term in value_lower for term in ['accepted', 'acknowledged']):
            return RiskStatus.ACCEPTED
        else:
            return RiskStatus.OPEN
    
    def _parse_date(self, value: Optional[str]) -> date:
        """Parse date value from string."""
        if not value:
            return date.today()
        
        try:
            # Try common date formats
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d', '%m-%d-%Y', '%d-%m-%Y']:
                try:
                    return datetime.strptime(value.strip(), fmt).date()
                except ValueError:
                    continue
            
            # If no format matches, return today
            return date.today()
            
        except Exception:
            return date.today()