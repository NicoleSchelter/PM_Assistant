"""
Abstract base class for file handlers.

This module defines the BaseFileHandler abstract class that provides a common
interface for all file format handlers in the PM Analysis Tool.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.models import DocumentType, FileFormat, FileInfo, ValidationResult


class BaseFileHandler(ABC):
    """
    Abstract base class for file format handlers.

    This class defines the interface that all file handlers must implement
    to ensure consistent behavior across different file formats.

    Attributes:
        supported_extensions (List[str]): List of file extensions this handler supports
        handler_name (str): Human-readable name for this handler
    """

    def __init__(self):
        """Initialize the file handler."""
        self.supported_extensions: List[str] = []
        self.handler_name: str = self.__class__.__name__

    @abstractmethod
    def can_handle(self, file_path: str) -> bool:
        """
        Check if this handler can process the given file.

        Args:
            file_path (str): Path to the file to check

        Returns:
            bool: True if this handler can process the file, False otherwise

        Example:
            >>> handler = MarkdownHandler()
            >>> handler.can_handle("document.md")
            True
            >>> handler.can_handle("document.xlsx")
            False
        """
        pass

    @abstractmethod
    def extract_data(self, file_path: str) -> Dict[str, Any]:
        """
        Extract structured data from the file.

        Args:
            file_path (str): Path to the file to process

        Returns:
            Dict[str, Any]: Extracted data in a structured format

        Raises:
            FileProcessingError: If the file cannot be processed
            ValidationError: If the file format is invalid

        Example:
            >>> handler = MarkdownHandler()
            >>> data = handler.extract_data("risk_plan.md")
            >>> print(data.keys())
            dict_keys(['title', 'sections', 'tables', 'metadata'])
        """
        pass

    @abstractmethod
    def validate_structure(self, file_path: str) -> ValidationResult:
        """
        Validate the file structure and content.

        Args:
            file_path (str): Path to the file to validate

        Returns:
            ValidationResult: Validation result with success status and messages

        Example:
            >>> handler = ExcelHandler()
            >>> result = handler.validate_structure("stakeholder_register.xlsx")
            >>> if result.is_valid:
            ...     print("File structure is valid")
            >>> else:
            ...     print(f"Validation errors: {result.errors}")
        """
        pass

    def get_file_info(self, file_path: str) -> FileInfo:
        """
        Get basic information about the file.

        Args:
            file_path (str): Path to the file

        Returns:
            FileInfo: Basic file information

        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        from datetime import datetime

        stat = path.stat()

        # Determine file format
        extension = path.suffix.lower().lstrip(".")
        try:
            file_format = FileFormat(extension)
        except ValueError:
            # If extension is not in FileFormat enum, default to a generic format
            file_format = FileFormat.MARKDOWN  # or handle unknown formats differently

        return FileInfo(
            path=path,
            format=file_format,
            document_type=DocumentType.UNKNOWN,  # Will be determined by content analysis
            size_bytes=stat.st_size,
            last_modified=datetime.fromtimestamp(stat.st_mtime),
            is_readable=self.validate_structure(file_path).is_valid,
        )

    def get_supported_extensions(self) -> List[str]:
        """
        Get list of file extensions supported by this handler.

        Returns:
            List[str]: List of supported file extensions (without dots)

        Example:
            >>> handler = MarkdownHandler()
            >>> handler.get_supported_extensions()
            ['md', 'markdown']
        """
        return self.supported_extensions.copy()

    def __str__(self) -> str:
        """String representation of the handler."""
        return f"{self.handler_name}(extensions={self.supported_extensions})"

    def __repr__(self) -> str:
        """Detailed string representation of the handler."""
        return (
            f"{self.__class__.__name__}("
            f"handler_name='{self.handler_name}', "
            f"supported_extensions={self.supported_extensions})"
        )


# Usage Example and Documentation
"""
Usage Example:

To create a new file handler, inherit from BaseFileHandler and implement
the required abstract methods:

```python
from file_handlers.base_handler import BaseFileHandler
from core.domain import ValidationResult

class CSVHandler(BaseFileHandler):
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['csv']
        self.handler_name = "CSV Handler"
    
    def can_handle(self, file_path: str) -> bool:
        return file_path.lower().endswith('.csv')
    
    def extract_data(self, file_path: str) -> Dict[str, Any]:
        import pandas as pd
        df = pd.read_csv(file_path)
        return {
            'rows': df.to_dict('records'),
            'columns': df.columns.tolist(),
            'shape': df.shape
        }
    
    def validate_structure(self, file_path: str) -> ValidationResult:
        try:
            import pandas as pd
            df = pd.read_csv(file_path)
            return ValidationResult(
                is_valid=True,
                errors=[],
                warnings=[]
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[str(e)],
                warnings=[]
            )

# Usage
handler = CSVHandler()
if handler.can_handle("data.csv"):
    data = handler.extract_data("data.csv")
    validation = handler.validate_structure("data.csv")
```

Integration with the PM Analysis Tool:

File handlers are automatically discovered and registered by the system.
Each handler should be placed in the file_handlers package and imported
in the __init__.py file for automatic discovery.

The system uses the can_handle() method to determine which handler to use
for each file, so ensure this method accurately identifies supported files.
"""
