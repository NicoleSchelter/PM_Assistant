"""
Abstract base class for processors.

This module defines the BaseProcessor abstract class that provides a common
interface for all operation mode processors in the PM Analysis Tool.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.models import FileInfo, ProcessingResult


class BaseProcessor(ABC):
    """
    Abstract base class for all processors.

    This class defines the interface that all processors must implement
    to ensure consistent behavior across different operation modes.

    Attributes:
        processor_name (str): Human-readable name for this processor
        required_files (List[str]): List of file patterns required by this processor
        optional_files (List[str]): List of optional file patterns
    """

    def __init__(self):
        """Initialize the processor."""
        self.processor_name: str = self.__class__.__name__
        self.required_files: List[str] = []
        self.optional_files: List[str] = []

    @abstractmethod
    def process(self, files: List[FileInfo], config: Dict[str, Any]) -> ProcessingResult:
        """
        Process the provided files according to the processor's logic.

        Args:
            files (List[FileInfo]): List of files to process
            config (Dict[str, Any]): Configuration dictionary

        Returns:
            ProcessingResult: Result of the processing operation

        Raises:
            ProcessingError: If processing fails
            ValidationError: If input validation fails

        Example:
            >>> processor = DocumentCheckProcessor()
            >>> files = [FileInfo(...), FileInfo(...)]
            >>> config = {"output_format": "markdown"}
            >>> result = processor.process(files, config)
            >>> if result.success:
            ...     print(f"Processing completed: {result.data}")
            >>> else:
            ...     print(f"Processing failed: {result.errors}")
        """
        pass

    @abstractmethod
    def validate_inputs(self, files: List[FileInfo]) -> bool:
        """
        Validate that the provided files meet the processor's requirements.

        Args:
            files (List[FileInfo]): List of files to validate

        Returns:
            bool: True if inputs are valid, False otherwise

        Example:
            >>> processor = StatusAnalysisProcessor()
            >>> files = [FileInfo(name="risk_plan.md", ...)]
            >>> if processor.validate_inputs(files):
            ...     result = processor.process(files, config)
            >>> else:
            ...     print("Required files are missing")
        """
        pass

    def get_missing_required_files(self, files: List[FileInfo]) -> List[str]:
        """
        Get list of required files that are missing from the input.

        Args:
            files (List[FileInfo]): List of available files

        Returns:
            List[str]: List of missing required file patterns

        Example:
            >>> processor = StatusAnalysisProcessor()
            >>> files = [FileInfo(name="charter.md", ...)]
            >>> missing = processor.get_missing_required_files(files)
            >>> print(f"Missing files: {missing}")
            ['*risk*', '*stakeholder*']
        """
        available_names = [f.filename.lower() for f in files]
        missing = []

        for required_pattern in self.required_files:
            pattern_lower = required_pattern.lower()
            # Simple pattern matching - can be enhanced with regex
            if not any(self._matches_pattern(name, pattern_lower) for name in available_names):
                missing.append(required_pattern)

        return missing

    def get_available_optional_files(self, files: List[FileInfo]) -> List[FileInfo]:
        """
        Get list of optional files that are available in the input.

        Args:
            files (List[FileInfo]): List of available files

        Returns:
            List[FileInfo]: List of available optional files
        """
        available_optional = []

        for file_info in files:
            for optional_pattern in self.optional_files:
                if self._matches_pattern(file_info.filename.lower(), optional_pattern.lower()):
                    available_optional.append(file_info)
                    break

        return available_optional

    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """
        Check if filename matches the given pattern.

        This method supports simple wildcard patterns where:
        - *text* matches any filename containing 'text'
        - text* matches any filename starting with 'text'
        - *text matches any filename ending with 'text'
        - text matches any filename containing 'text'

        Args:
            filename (str): Filename to check
            pattern (str): Pattern to match against

        Returns:
            bool: True if filename matches pattern
        """
        if "*" not in pattern:
            # No wildcards - simple substring match
            return pattern in filename

        if pattern == "*":
            # Match everything
            return True

        if pattern.startswith("*") and pattern.endswith("*"):
            # *text* - contains pattern
            search_text = pattern[1:-1]
            return search_text in filename
        elif pattern.startswith("*"):
            # *text - ends with pattern
            search_text = pattern[1:]
            return filename.endswith(search_text)
        elif pattern.endswith("*"):
            # text* - starts with pattern
            search_text = pattern[:-1]
            return filename.startswith(search_text)
        else:
            # Complex pattern with * in middle - use fnmatch
            import fnmatch

            return fnmatch.fnmatch(filename, pattern)

    def get_processor_info(self) -> Dict[str, Any]:
        """
        Get information about this processor.

        Returns:
            Dict[str, Any]: Processor information
        """
        return {
            "name": self.processor_name,
            "required_files": self.required_files,
            "optional_files": self.optional_files,
            "class": self.__class__.__name__,
        }

    def can_process(self, files: List[FileInfo]) -> bool:
        """
        Check if this processor can process the given files.

        Args:
            files (List[FileInfo]): List of files to check

        Returns:
            bool: True if processor can handle the files
        """
        return self.validate_inputs(files)

    def __str__(self) -> str:
        """String representation of the processor."""
        return f"{self.processor_name}"

    def __repr__(self) -> str:
        """Detailed string representation of the processor."""
        return (
            f"{self.__class__.__name__}("
            f"processor_name='{self.processor_name}', "
            f"required_files={self.required_files}, "
            f"optional_files={self.optional_files})"
        )


# Usage Example and Documentation
"""
Usage Example:

To create a new processor, inherit from BaseProcessor and implement
the required abstract methods:

```python
from processors.base_processor import BaseProcessor
from core.domain import ProcessingResult, FileInfo

class CustomAnalysisProcessor(BaseProcessor):
    def __init__(self):
        super().__init__()
        self.processor_name = "Custom Analysis Processor"
        self.required_files = ['*charter*', '*scope*']
        self.optional_files = ['*budget*', '*timeline*']
    
    def validate_inputs(self, files: List[FileInfo]) -> bool:
        missing = self.get_missing_required_files(files)
        return len(missing) == 0
    
    def process(self, files: List[FileInfo], config: Dict[str, Any]) -> ProcessingResult:
        try:
            # Validate inputs first
            if not self.validate_inputs(files):
                missing = self.get_missing_required_files(files)
                return ProcessingResult(
                    success=False,
                    data={},
                    errors=[f"Missing required files: {missing}"],
                    warnings=[],
                    execution_time=0.0
                )
            
            # Process files
            results = {}
            for file_info in files:
                # Process each file based on your logic
                results[file_info.name] = self._process_file(file_info)
            
            return ProcessingResult(
                success=True,
                data=results,
                errors=[],
                warnings=[],
                execution_time=1.5  # Track actual execution time
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                data={},
                errors=[str(e)],
                warnings=[],
                execution_time=0.0
            )
    
    def _process_file(self, file_info: FileInfo) -> Dict[str, Any]:
        # Custom file processing logic
        return {"processed": True, "file": file_info.name}

# Usage
processor = CustomAnalysisProcessor()
files = [FileInfo(name="project_charter.md", ...)]
config = {"output_format": "json"}

if processor.can_process(files):
    result = processor.process(files, config)
    if result.success:
        print(f"Processing successful: {result.data}")
else:
    missing = processor.get_missing_required_files(files)
    print(f"Cannot process - missing files: {missing}")
```

Integration with the PM Analysis Tool:

Processors are registered with the system and selected based on the operation
mode. Each processor should:

1. Define clear required and optional file patterns
2. Implement robust input validation
3. Handle errors gracefully and return meaningful error messages
4. Track execution time for performance monitoring
5. Return structured results in the ProcessingResult format

The system uses the validate_inputs() method to determine if a processor
can handle the available files, so ensure this method accurately reflects
the processor's requirements.
"""
