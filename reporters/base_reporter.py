"""
Abstract base class for report generators.

This module defines the BaseReporter abstract class that provides a common
interface for all report generators in the PM Analysis Tool.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime

from core.models import ProcessingResult


class BaseReporter(ABC):
    """
    Abstract base class for report generators.
    
    This class defines the interface that all reporters must implement
    to ensure consistent behavior across different output formats.
    
    Attributes:
        reporter_name (str): Human-readable name for this reporter
        output_format (str): The output format this reporter generates
        file_extension (str): File extension for generated reports
    """
    
    def __init__(self):
        """Initialize the reporter."""
        self.reporter_name: str = self.__class__.__name__
        self.output_format: str = "unknown"
        self.file_extension: str = ".txt"
    
    @abstractmethod
    def generate_report(self, 
                       data: ProcessingResult, 
                       output_path: str, 
                       config: Dict[str, Any]) -> str:
        """
        Generate a report from the processing results.
        
        Args:
            data (ProcessingResult): Results from a processor
            output_path (str): Path where the report should be saved
            config (Dict[str, Any]): Configuration for report generation
            
        Returns:
            str: Path to the generated report file
            
        Raises:
            ReportGenerationError: If report generation fails
            FileWriteError: If the report cannot be written to disk
            
        Example:
            >>> reporter = MarkdownReporter()
            >>> result = ProcessingResult(success=True, data={...})
            >>> config = {"include_timestamp": True, "template": "detailed"}
            >>> report_path = reporter.generate_report(result, "./reports", config)
            >>> print(f"Report generated: {report_path}")
        """
        pass
    
    @abstractmethod
    def format_data(self, data: Dict[str, Any], config: Dict[str, Any]) -> str:
        """
        Format the data into the reporter's output format.
        
        Args:
            data (Dict[str, Any]): Data to format
            config (Dict[str, Any]): Formatting configuration
            
        Returns:
            str: Formatted data as a string
            
        Example:
            >>> reporter = ExcelReporter()
            >>> data = {"risks": [...], "milestones": [...]}
            >>> config = {"include_charts": True}
            >>> formatted = reporter.format_data(data, config)
        """
        pass
    
    def validate_output_path(self, output_path: str) -> bool:
        """
        Validate that the output path is writable.
        
        Args:
            output_path (str): Path to validate
            
        Returns:
            bool: True if path is valid and writable
        """
        try:
            path = Path(output_path)
            
            # Create directory if it doesn't exist
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
            
            # Check if directory is writable
            test_file = path / "test_write.tmp"
            test_file.touch()
            test_file.unlink()
            
            return True
        except (OSError, PermissionError):
            return False
    
    def generate_filename(self, 
                         base_name: str, 
                         timestamp: bool = True,
                         suffix: Optional[str] = None) -> str:
        """
        Generate a filename for the report.
        
        Args:
            base_name (str): Base name for the file
            timestamp (bool): Whether to include timestamp
            suffix (Optional[str]): Additional suffix to add
            
        Returns:
            str: Generated filename with extension
            
        Example:
            >>> reporter = MarkdownReporter()
            >>> filename = reporter.generate_filename("status_report", True, "v2")
            >>> print(filename)
            "status_report_20240108_143022_v2.md"
        """
        parts = [base_name]
        
        if timestamp:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            parts.append(ts)
        
        if suffix:
            parts.append(suffix)
        
        filename = "_".join(parts) + self.file_extension
        return filename
    
    def create_report_header(self, 
                           title: str, 
                           processing_result: ProcessingResult,
                           config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create standard header information for reports.
        
        Args:
            title (str): Report title
            processing_result (ProcessingResult): Processing results
            config (Dict[str, Any]): Configuration
            
        Returns:
            Dict[str, Any]: Header information
        """
        return {
            'title': title,
            'generated_at': datetime.now().isoformat(),
            'generator': self.reporter_name,
            'format': self.output_format,
            'processing_success': processing_result.success,
            'execution_time': processing_result.processing_time_seconds,
            'errors_count': len(processing_result.errors),
            'warnings_count': len(processing_result.warnings),
            'config': config
        }
    
    def handle_processing_errors(self, processing_result: ProcessingResult) -> str:
        """
        Format processing errors for inclusion in reports.
        
        Args:
            processing_result (ProcessingResult): Processing results with potential errors
            
        Returns:
            str: Formatted error information
        """
        if not processing_result.errors and not processing_result.warnings:
            return ""
        
        error_section = []
        
        if processing_result.errors:
            error_section.append("## Errors")
            for i, error in enumerate(processing_result.errors, 1):
                error_section.append(f"{i}. {error}")
            error_section.append("")
        
        if processing_result.warnings:
            error_section.append("## Warnings")
            for i, warning in enumerate(processing_result.warnings, 1):
                error_section.append(f"{i}. {warning}")
            error_section.append("")
        
        return "\n".join(error_section)
    
    def get_supported_config_options(self) -> Dict[str, Any]:
        """
        Get the configuration options supported by this reporter.
        
        Returns:
            Dict[str, Any]: Supported configuration options with descriptions
        """
        return {
            'include_timestamp': {
                'type': bool,
                'default': True,
                'description': 'Include timestamp in filename'
            },
            'include_errors': {
                'type': bool,
                'default': True,
                'description': 'Include error section in report'
            },
            'template': {
                'type': str,
                'default': 'standard',
                'description': 'Report template to use',
                'options': ['standard', 'detailed', 'summary']
            }
        }
    
    def __str__(self) -> str:
        """String representation of the reporter."""
        return f"{self.reporter_name} ({self.output_format})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the reporter."""
        return (f"{self.__class__.__name__}("
                f"reporter_name='{self.reporter_name}', "
                f"output_format='{self.output_format}', "
                f"file_extension='{self.file_extension}')")


# Usage Example and Documentation
"""
Usage Example:

To create a new reporter, inherit from BaseReporter and implement
the required abstract methods:

```python
from reporters.base_reporter import BaseReporter
from core.domain import ProcessingResult
import json

class JSONReporter(BaseReporter):
    def __init__(self):
        super().__init__()
        self.reporter_name = "JSON Reporter"
        self.output_format = "json"
        self.file_extension = ".json"
    
    def format_data(self, data: Dict[str, Any], config: Dict[str, Any]) -> str:
        # Format data as JSON
        if config.get('pretty_print', True):
            return json.dumps(data, indent=2, default=str)
        else:
            return json.dumps(data, default=str)
    
    def generate_report(self, 
                       data: ProcessingResult, 
                       output_path: str, 
                       config: Dict[str, Any]) -> str:
        try:
            # Validate output path
            if not self.validate_output_path(output_path):
                raise ReportGenerationError(f"Cannot write to {output_path}")
            
            # Create report content
            report_data = {
                'header': self.create_report_header("Analysis Report", data, config),
                'results': data.data,
                'errors': data.errors,
                'warnings': data.warnings
            }
            
            # Format the data
            formatted_content = self.format_data(report_data, config)
            
            # Generate filename and write file
            filename = self.generate_filename("analysis_report", 
                                            config.get('include_timestamp', True))
            file_path = Path(output_path) / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
            
            return str(file_path)
            
        except Exception as e:
            raise ReportGenerationError(f"Failed to generate report: {e}")

# Usage
reporter = JSONReporter()
processing_result = ProcessingResult(
    success=True,
    data={"risks": [{"id": "R001", "description": "Budget overrun"}]},
    errors=[],
    warnings=[],
    execution_time=2.5
)
config = {"pretty_print": True, "include_timestamp": True}

report_path = reporter.generate_report(processing_result, "./reports", config)
print(f"JSON report generated: {report_path}")
```

Integration with the PM Analysis Tool:

Reporters are used by processors to generate output in various formats.
Each reporter should:

1. Define a clear output format and file extension
2. Implement robust error handling for file I/O operations
3. Support configurable formatting options
4. Generate consistent report structures with headers and metadata
5. Handle processing errors gracefully in the output

The system can use multiple reporters simultaneously to generate reports
in different formats from the same processing results.

Common Configuration Options:

- include_timestamp: Add timestamp to filenames
- include_errors: Include error sections in reports
- template: Choose report template (standard, detailed, summary)
- pretty_print: Format output for readability (where applicable)
- custom_title: Override default report title
- output_filename: Specify custom filename

Error Handling:

Reporters should handle various error conditions:
- Invalid output paths
- Permission errors
- Disk space issues
- Data formatting errors
- Template rendering errors

All errors should be wrapped in appropriate exception types and include
meaningful error messages for debugging.
"""