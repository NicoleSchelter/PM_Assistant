"""
File scanning and discovery system for PM Analysis Tool.

This module provides functionality to scan project directories, discover relevant
files, validate file formats, and extract metadata. It supports pattern-based
file discovery and comprehensive file validation.
"""

import fnmatch
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

from core.models import (
    DocumentType, 
    FileFormat, 
    FileInfo, 
    ProcessingResult,
    ProcessingStatus
)
from utils.exceptions import FileProcessingError, ValidationError
from utils.validators import validate_directory_path
from utils.logger import get_logger


logger = get_logger(__name__)


class FileScanner:
    """
    Scans project directories for relevant files and validates their formats.
    
    The FileScanner class provides comprehensive file discovery capabilities,
    including pattern-based matching, format validation, and metadata extraction.
    It supports configurable document patterns and extensible file type detection.
    """
    
    # Default file patterns for different document types
    DEFAULT_PATTERNS = {
        DocumentType.CHARTER: [
            "*charter*", "*project*charter*", "*project_charter*",
            "charter.*", "project-charter.*"
        ],
        DocumentType.RISK_REGISTER: [
            "*risk*", "*risk*register*", "*risk_register*", "*risks*",
            "risk-register.*", "risk_management.*", "*risk*plan*"
        ],
        DocumentType.STAKEHOLDER_REGISTER: [
            "*stakeholder*", "*stakeholder*register*", "*stakeholder_register*",
            "stakeholder-register.*", "*stakeholders*"
        ],
        DocumentType.WBS: [
            "*wbs*", "*work*breakdown*", "*work_breakdown*",
            "work-breakdown.*", "*deliverable*", "*scope*"
        ],
        DocumentType.ROADMAP: [
            "*roadmap*", "*timeline*", "*schedule*", "*plan*",
            "roadmap.*", "project-timeline.*", "*milestones*"
        ],
        DocumentType.PROJECT_SCHEDULE: [
            "*.mpp", "*schedule*", "*project*plan*", "*timeline*",
            "schedule.*", "project-schedule.*"
        ]
    }
    
    # Supported file extensions mapped to formats
    FORMAT_EXTENSIONS = {
        '.md': FileFormat.MARKDOWN,
        '.markdown': FileFormat.MARKDOWN,
        '.xlsx': FileFormat.EXCEL,
        '.xls': FileFormat.EXCEL_LEGACY,
        '.mpp': FileFormat.MICROSOFT_PROJECT,
        '.yaml': FileFormat.YAML,
        '.yml': FileFormat.YAML,
        '.json': FileFormat.JSON,
        '.csv': FileFormat.CSV
    }
    
    def __init__(self, 
                 custom_patterns: Optional[Dict[DocumentType, List[str]]] = None,
                 supported_formats: Optional[Set[FileFormat]] = None,
                 max_file_size_mb: int = 100):
        """
        Initialize the FileScanner with configuration options.
        
        Args:
            custom_patterns: Custom file patterns for document types
            supported_formats: Set of supported file formats
            max_file_size_mb: Maximum file size in MB to process
        """
        self.patterns = self.DEFAULT_PATTERNS.copy()
        if custom_patterns:
            self.patterns.update(custom_patterns)
        
        self.supported_formats = supported_formats or set(FileFormat)
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        
        logger.info(f"FileScanner initialized with {len(self.patterns)} document types")
        logger.debug(f"Supported formats: {[f.value for f in self.supported_formats]}")
    
    def scan_directory(self, 
                      directory_path: Union[str, Path],
                      recursive: bool = True,
                      include_hidden: bool = False) -> List[FileInfo]:
        """
        Scan a directory for project files matching configured patterns.
        
        Args:
            directory_path: Path to the directory to scan
            recursive: Whether to scan subdirectories recursively
            include_hidden: Whether to include hidden files and directories
            
        Returns:
            List of FileInfo objects for discovered files
            
        Raises:
            FileProcessingError: If directory cannot be accessed or scanned
        """
        try:
            directory_path = Path(directory_path)
            
            if not directory_path.exists():
                raise FileProcessingError(f"Directory does not exist: {directory_path}")
            
            if not directory_path.is_dir():
                raise FileProcessingError(f"Path is not a directory: {directory_path}")
            
            # Validate directory access
            validate_directory_path(directory_path)
            
            logger.info(f"Scanning directory: {directory_path}")
            discovered_files = []
            
            # Get all files in directory
            if recursive:
                file_paths = self._get_files_recursive(directory_path, include_hidden)
            else:
                file_paths = self._get_files_single_level(directory_path, include_hidden)
            
            logger.debug(f"Found {len(file_paths)} total files")
            
            # Process each file
            for file_path in file_paths:
                try:
                    file_info = self._create_file_info(file_path)
                    if file_info:
                        discovered_files.append(file_info)
                except Exception as e:
                    logger.warning(f"Error processing file {file_path}: {e}")
                    continue
            
            logger.info(f"Discovered {len(discovered_files)} relevant project files")
            return discovered_files
            
        except Exception as e:
            error_msg = f"Failed to scan directory {directory_path}: {e}"
            logger.error(error_msg)
            raise FileProcessingError(error_msg) from e
    
    def validate_file_formats(self, files: List[FileInfo]) -> ProcessingResult:
        """
        Validate discovered files against expected formats and requirements.
        
        Args:
            files: List of FileInfo objects to validate
            
        Returns:
            ProcessingResult with validation results and any issues found
        """
        start_time = datetime.now()
        result = ProcessingResult(
            success=True,
            operation="file_format_validation",
            timestamp=start_time
        )
        
        try:
            logger.info(f"Validating {len(files)} files")
            
            valid_files = 0
            invalid_files = 0
            validation_details = {}
            
            for file_info in files:
                try:
                    validation_result = self._validate_single_file(file_info)
                    validation_details[str(file_info.path)] = validation_result
                    
                    if validation_result['is_valid']:
                        valid_files += 1
                        file_info.is_readable = True
                    else:
                        invalid_files += 1
                        file_info.is_readable = False
                        file_info.error_message = validation_result.get('error')
                        result.add_warning(f"Invalid file: {file_info.filename} - {validation_result.get('error')}")
                        
                except Exception as e:
                    invalid_files += 1
                    error_msg = f"Validation error for {file_info.filename}: {e}"
                    result.add_error(error_msg)
                    file_info.is_readable = False
                    file_info.error_message = str(e)
            
            # Update result data
            result.data = {
                'total_files': len(files),
                'valid_files': valid_files,
                'invalid_files': invalid_files,
                'validation_details': validation_details,
                'supported_formats': [f.value for f in self.supported_formats]
            }
            
            # Calculate processing time
            end_time = datetime.now()
            result.processing_time_seconds = (end_time - start_time).total_seconds()
            
            logger.info(f"Validation complete: {valid_files} valid, {invalid_files} invalid")
            
            if invalid_files > 0 and valid_files == 0:
                result.success = False
                result.add_error("No valid files found")
            
            return result
            
        except Exception as e:
            error_msg = f"File validation failed: {e}"
            logger.error(error_msg)
            result.add_error(error_msg)
            result.success = False
            return result
    
    def match_document_patterns(self, 
                               filename: str, 
                               custom_patterns: Optional[Dict[DocumentType, List[str]]] = None) -> List[DocumentType]:
        """
        Match a filename against document type patterns.
        
        Args:
            filename: Name of the file to match
            custom_patterns: Optional custom patterns to use instead of defaults
            
        Returns:
            List of DocumentType matches (can be multiple if patterns overlap)
        """
        patterns_to_use = custom_patterns or self.patterns
        matches = []
        
        filename_lower = filename.lower()
        
        for doc_type, pattern_list in patterns_to_use.items():
            for pattern in pattern_list:
                if fnmatch.fnmatch(filename_lower, pattern.lower()):
                    matches.append(doc_type)
                    break  # Only add each document type once
        
        return matches if matches else [DocumentType.UNKNOWN]
    
    def get_file_statistics(self, files: List[FileInfo]) -> Dict[str, any]:
        """
        Generate statistics about discovered files.
        
        Args:
            files: List of FileInfo objects to analyze
            
        Returns:
            Dictionary containing file statistics
        """
        if not files:
            return {
                'total_files': 0,
                'by_format': {},
                'by_document_type': {},
                'total_size_mb': 0,
                'readable_files': 0,
                'unreadable_files': 0
            }
        
        stats = {
            'total_files': len(files),
            'by_format': {},
            'by_document_type': {},
            'total_size_mb': 0,
            'readable_files': 0,
            'unreadable_files': 0,
            'average_file_size_kb': 0,
            'largest_file': None,
            'smallest_file': None,
            'newest_file': None,
            'oldest_file': None
        }
        
        total_size_bytes = 0
        largest_size = 0
        smallest_size = float('inf')
        newest_date = datetime.min
        oldest_date = datetime.max
        
        for file_info in files:
            # Count by format
            format_key = file_info.format.value
            stats['by_format'][format_key] = stats['by_format'].get(format_key, 0) + 1
            
            # Count by document type
            doc_type_key = file_info.document_type.value
            stats['by_document_type'][doc_type_key] = stats['by_document_type'].get(doc_type_key, 0) + 1
            
            # Size statistics
            total_size_bytes += file_info.size_bytes
            if file_info.size_bytes > largest_size:
                largest_size = file_info.size_bytes
                stats['largest_file'] = file_info.filename
            if file_info.size_bytes < smallest_size:
                smallest_size = file_info.size_bytes
                stats['smallest_file'] = file_info.filename
            
            # Date statistics
            if file_info.last_modified > newest_date:
                newest_date = file_info.last_modified
                stats['newest_file'] = file_info.filename
            if file_info.last_modified < oldest_date:
                oldest_date = file_info.last_modified
                stats['oldest_file'] = file_info.filename
            
            # Readability count
            if file_info.is_readable:
                stats['readable_files'] += 1
            else:
                stats['unreadable_files'] += 1
        
        # Calculate derived statistics
        stats['total_size_mb'] = round(total_size_bytes / (1024 * 1024), 2)
        stats['average_file_size_kb'] = round(total_size_bytes / len(files) / 1024, 2)
        
        return stats
    
    def _get_files_recursive(self, directory: Path, include_hidden: bool) -> List[Path]:
        """Get all files recursively from directory."""
        files = []
        try:
            for root, dirs, filenames in os.walk(directory):
                # Filter out hidden directories if not including hidden files
                if not include_hidden:
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for filename in filenames:
                    if not include_hidden and filename.startswith('.'):
                        continue
                    
                    file_path = Path(root) / filename
                    if file_path.is_file():
                        files.append(file_path)
        except PermissionError as e:
            logger.warning(f"Permission denied accessing directory: {e}")
        except Exception as e:
            logger.error(f"Error walking directory {directory}: {e}")
        
        return files
    
    def _get_files_single_level(self, directory: Path, include_hidden: bool) -> List[Path]:
        """Get files from single directory level only."""
        files = []
        try:
            for item in directory.iterdir():
                if item.is_file():
                    if not include_hidden and item.name.startswith('.'):
                        continue
                    files.append(item)
        except PermissionError as e:
            logger.warning(f"Permission denied accessing directory: {e}")
        except Exception as e:
            logger.error(f"Error reading directory {directory}: {e}")
        
        return files
    
    def _create_file_info(self, file_path: Path) -> Optional[FileInfo]:
        """Create FileInfo object for a file if it matches patterns."""
        try:
            # Get file statistics
            stat_info = file_path.stat()
            file_size = stat_info.st_size
            last_modified = datetime.fromtimestamp(stat_info.st_mtime)
            
            # Check file size limit
            if file_size > self.max_file_size_bytes:
                logger.warning(f"File too large, skipping: {file_path} ({file_size / 1024 / 1024:.1f} MB)")
                return None
            
            # Determine file format
            file_format = self._determine_file_format(file_path)
            if file_format not in self.supported_formats:
                logger.debug(f"Unsupported format, skipping: {file_path}")
                return None
            
            # Match document type patterns
            document_types = self.match_document_patterns(file_path.name)
            primary_doc_type = document_types[0] if document_types else DocumentType.UNKNOWN
            
            # Skip unknown document types unless they have supported formats
            if primary_doc_type == DocumentType.UNKNOWN and file_format not in {FileFormat.EXCEL, FileFormat.MICROSOFT_PROJECT}:
                logger.debug(f"Unknown document type, skipping: {file_path}")
                return None
            
            # Create FileInfo object
            file_info = FileInfo(
                path=file_path,
                format=file_format,
                document_type=primary_doc_type,
                size_bytes=file_size,
                last_modified=last_modified,
                is_readable=True,
                metadata={
                    'matched_patterns': document_types,
                    'extension': file_path.suffix.lower()
                }
            )
            
            logger.debug(f"Created FileInfo for: {file_path.name} ({file_format.value}, {primary_doc_type.value})")
            return file_info
            
        except Exception as e:
            logger.error(f"Error creating FileInfo for {file_path}: {e}")
            return None
    
    def _determine_file_format(self, file_path: Path) -> FileFormat:
        """Determine file format based on extension."""
        extension = file_path.suffix.lower()
        return self.FORMAT_EXTENSIONS.get(extension, FileFormat.MARKDOWN)  # Default to markdown
    
    def _validate_single_file(self, file_info: FileInfo) -> Dict[str, any]:
        """Validate a single file and return validation details."""
        validation_result = {
            'is_valid': True,
            'checks_performed': [],
            'error': None,
            'warnings': []
        }
        
        try:
            # Check if file exists and is readable
            if not file_info.path.exists():
                validation_result['is_valid'] = False
                validation_result['error'] = "File does not exist"
                return validation_result
            
            validation_result['checks_performed'].append('existence')
            
            # Check if file is actually a file (not directory)
            if not file_info.path.is_file():
                validation_result['is_valid'] = False
                validation_result['error'] = "Path is not a file"
                return validation_result
            
            validation_result['checks_performed'].append('file_type')
            
            # Check file permissions
            if not os.access(file_info.path, os.R_OK):
                validation_result['is_valid'] = False
                validation_result['error'] = "File is not readable"
                return validation_result
            
            validation_result['checks_performed'].append('permissions')
            
            # Check file size
            if file_info.size_bytes == 0:
                validation_result['warnings'].append("File is empty")
            elif file_info.size_bytes > self.max_file_size_bytes:
                validation_result['is_valid'] = False
                validation_result['error'] = f"File too large ({file_info.size_bytes / 1024 / 1024:.1f} MB)"
                return validation_result
            
            validation_result['checks_performed'].append('size')
            
            # Format-specific validation
            format_validation = self._validate_file_format(file_info)
            validation_result['checks_performed'].extend(format_validation.get('checks_performed', []))
            
            if not format_validation['is_valid']:
                validation_result['is_valid'] = False
                validation_result['error'] = format_validation.get('error', 'Format validation failed')
            
            validation_result['warnings'].extend(format_validation.get('warnings', []))
            
            return validation_result
            
        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['error'] = f"Validation error: {e}"
            return validation_result
    
    def _validate_file_format(self, file_info: FileInfo) -> Dict[str, any]:
        """Perform format-specific validation."""
        validation_result = {
            'is_valid': True,
            'checks_performed': [],
            'error': None,
            'warnings': []
        }
        
        try:
            if file_info.format == FileFormat.EXCEL or file_info.format == FileFormat.EXCEL_LEGACY:
                # Basic Excel file validation
                validation_result['checks_performed'].append('excel_format')
                # Could add more specific Excel validation here
                
            elif file_info.format == FileFormat.MARKDOWN:
                # Basic Markdown file validation
                validation_result['checks_performed'].append('markdown_format')
                # Could add markdown syntax validation here
                
            elif file_info.format == FileFormat.MICROSOFT_PROJECT:
                # Basic MPP file validation
                validation_result['checks_performed'].append('mpp_format')
                # Could add MPP-specific validation here
                
            elif file_info.format in {FileFormat.YAML, FileFormat.JSON}:
                # Could add structured data validation here
                validation_result['checks_performed'].append('structured_data_format')
            
            return validation_result
            
        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['error'] = f"Format validation error: {e}"
            return validation_result