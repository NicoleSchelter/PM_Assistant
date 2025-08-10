"""
Tests for abstract base classes.

This module tests the abstract base classes to ensure they provide
the correct interfaces and behavior for extensibility.
"""

from abc import ABC
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pytest

from core.models import FileInfo, ProcessingResult, ValidationResult
from file_handlers.base_handler import BaseFileHandler
from processors.base_processor import BaseProcessor
from reporters.base_reporter import BaseReporter


class TestBaseFileHandler:
    """Test the BaseFileHandler abstract class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that BaseFileHandler cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseFileHandler()

    def test_concrete_implementation_works(self):
        """Test that a concrete implementation of BaseFileHandler works."""

        class TestHandler(BaseFileHandler):
            def __init__(self):
                super().__init__()
                self.supported_extensions = ["test"]
                self.handler_name = "Test Handler"

            def can_handle(self, file_path: str) -> bool:
                return file_path.endswith(".test")

            def extract_data(self, file_path: str) -> Dict[str, Any]:
                return {"test": "data"}

            def validate_structure(self, file_path: str) -> ValidationResult:
                return ValidationResult(is_valid=True, errors=[], warnings=[])

        handler = TestHandler()
        assert handler.handler_name == "Test Handler"
        assert handler.supported_extensions == ["test"]
        assert handler.can_handle("file.test") is True
        assert handler.can_handle("file.txt") is False
        assert handler.extract_data("test.test") == {"test": "data"}

        result = handler.validate_structure("test.test")
        assert result.is_valid is True

    def test_get_supported_extensions(self):
        """Test the get_supported_extensions method."""

        class TestHandler(BaseFileHandler):
            def __init__(self):
                super().__init__()
                self.supported_extensions = ["md", "txt"]

            def can_handle(self, file_path: str) -> bool:
                return True

            def extract_data(self, file_path: str) -> Dict[str, Any]:
                return {}

            def validate_structure(self, file_path: str) -> ValidationResult:
                return ValidationResult(is_valid=True, errors=[], warnings=[])

        handler = TestHandler()
        extensions = handler.get_supported_extensions()
        assert extensions == ["md", "txt"]

        # Ensure it returns a copy
        extensions.append("xlsx")
        assert handler.supported_extensions == ["md", "txt"]

    def test_string_representations(self):
        """Test string representations of the handler."""

        class TestHandler(BaseFileHandler):
            def __init__(self):
                super().__init__()
                self.supported_extensions = ["test"]
                self.handler_name = "Test Handler"

            def can_handle(self, file_path: str) -> bool:
                return True

            def extract_data(self, file_path: str) -> Dict[str, Any]:
                return {}

            def validate_structure(self, file_path: str) -> ValidationResult:
                return ValidationResult(is_valid=True, errors=[], warnings=[])

        handler = TestHandler()
        assert str(handler) == "Test Handler(extensions=['test'])"
        assert "TestHandler" in repr(handler)
        assert "Test Handler" in repr(handler)


class TestBaseProcessor:
    """Test the BaseProcessor abstract class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that BaseProcessor cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseProcessor()

    def test_concrete_implementation_works(self):
        """Test that a concrete implementation of BaseProcessor works."""

        class TestProcessor(BaseProcessor):
            def __init__(self):
                super().__init__()
                self.processor_name = "Test Processor"
                self.required_files = ["*charter*"]
                self.optional_files = ["*risk*"]

            def validate_inputs(self, files: List[FileInfo]) -> bool:
                return len(self.get_missing_required_files(files)) == 0

            def process(self, files: List[FileInfo], config: Dict[str, Any]) -> ProcessingResult:
                return ProcessingResult(
                    success=True,
                    operation="test_processing",
                    data={"processed": len(files)},
                    errors=[],
                    warnings=[],
                    processing_time_seconds=1.0,
                )

        processor = TestProcessor()
        assert processor.processor_name == "Test Processor"
        assert processor.required_files == ["*charter*"]
        assert processor.optional_files == ["*risk*"]

        # Test with valid files
        from core.models import DocumentType, FileFormat

        files = [
            FileInfo(
                path=Path("/test/charter.md"),
                format=FileFormat.MARKDOWN,
                document_type=DocumentType.CHARTER,
                size_bytes=1000,
                last_modified=datetime.now(),
                is_readable=True,
            )
        ]

        assert processor.validate_inputs(files) is True
        result = processor.process(files, {})
        assert result.success is True
        assert result.data["processed"] == 1

    def test_missing_required_files(self):
        """Test the get_missing_required_files method."""

        class TestProcessor(BaseProcessor):
            def __init__(self):
                super().__init__()
                self.required_files = ["*charter*", "*scope*"]

            def validate_inputs(self, files: List[FileInfo]) -> bool:
                return True

            def process(self, files: List[FileInfo], config: Dict[str, Any]) -> ProcessingResult:
                return ProcessingResult(
                    success=True,
                    operation="test",
                    data={},
                    errors=[],
                    warnings=[],
                    processing_time_seconds=0.0,
                )

        processor = TestProcessor()

        # No files - should have missing files
        missing = processor.get_missing_required_files([])
        assert len(missing) == 2
        assert "*charter*" in missing
        assert "*scope*" in missing

        # One matching file
        from core.models import DocumentType, FileFormat

        files = [
            FileInfo(
                path=Path("/test/project_charter.md"),
                format=FileFormat.MARKDOWN,
                document_type=DocumentType.CHARTER,
                size_bytes=1000,
                last_modified=datetime.now(),
                is_readable=True,
            )
        ]

        missing = processor.get_missing_required_files(files)
        assert len(missing) == 1
        assert "*scope*" in missing

    def test_pattern_matching(self):
        """Test the pattern matching functionality."""

        class TestProcessor(BaseProcessor):
            def __init__(self):
                super().__init__()

            def validate_inputs(self, files: List[FileInfo]) -> bool:
                return True

            def process(self, files: List[FileInfo], config: Dict[str, Any]) -> ProcessingResult:
                return ProcessingResult(
                    success=True,
                    operation="test",
                    data={},
                    errors=[],
                    warnings=[],
                    processing_time_seconds=0.0,
                )

        processor = TestProcessor()

        # Test different pattern types
        assert processor._matches_pattern("charter.md", "*charter*") is True
        assert processor._matches_pattern("project_charter.md", "*charter*") is True
        assert processor._matches_pattern("scope.md", "*charter*") is False

        assert processor._matches_pattern("risk_plan.md", "risk*") is True
        assert processor._matches_pattern("plan.md", "risk*") is False

        assert processor._matches_pattern("my_document", "*document") is True
        assert processor._matches_pattern("document.txt", "*document") is False

    def test_processor_info(self):
        """Test the get_processor_info method."""

        class TestProcessor(BaseProcessor):
            def __init__(self):
                super().__init__()
                self.processor_name = "Test Processor"
                self.required_files = ["*test*"]
                self.optional_files = ["*optional*"]

            def validate_inputs(self, files: List[FileInfo]) -> bool:
                return True

            def process(self, files: List[FileInfo], config: Dict[str, Any]) -> ProcessingResult:
                return ProcessingResult(
                    success=True,
                    operation="test",
                    data={},
                    errors=[],
                    warnings=[],
                    processing_time_seconds=0.0,
                )

        processor = TestProcessor()
        info = processor.get_processor_info()

        assert info["name"] == "Test Processor"
        assert info["required_files"] == ["*test*"]
        assert info["optional_files"] == ["*optional*"]
        assert info["class"] == "TestProcessor"


class TestBaseReporter:
    """Test the BaseReporter abstract class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that BaseReporter cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseReporter()

    def test_concrete_implementation_works(self):
        """Test that a concrete implementation of BaseReporter works."""

        class TestReporter(BaseReporter):
            def __init__(self):
                super().__init__()
                self.reporter_name = "Test Reporter"
                self.output_format = "test"
                self.file_extension = ".test"

            def format_data(self, data: Dict[str, Any], config: Dict[str, Any]) -> str:
                return f"Test report: {data}"

            def generate_report(
                self, data: ProcessingResult, output_path: str, config: Dict[str, Any]
            ) -> str:
                return "/test/report.test"

        reporter = TestReporter()
        assert reporter.reporter_name == "Test Reporter"
        assert reporter.output_format == "test"
        assert reporter.file_extension == ".test"

        formatted = reporter.format_data({"key": "value"}, {})
        assert "Test report:" in formatted

        result = ProcessingResult(
            success=True,
            operation="test",
            data={},
            errors=[],
            warnings=[],
            processing_time_seconds=1.0,
        )
        report_path = reporter.generate_report(result, "/test", {})
        assert report_path == "/test/report.test"

    def test_filename_generation(self):
        """Test the generate_filename method."""

        class TestReporter(BaseReporter):
            def __init__(self):
                super().__init__()
                self.file_extension = ".test"

            def format_data(self, data: Dict[str, Any], config: Dict[str, Any]) -> str:
                return ""

            def generate_report(
                self, data: ProcessingResult, output_path: str, config: Dict[str, Any]
            ) -> str:
                return ""

        reporter = TestReporter()

        # Test without timestamp
        filename = reporter.generate_filename("report", timestamp=False)
        assert filename == "report.test"

        # Test with suffix
        filename = reporter.generate_filename("report", timestamp=False, suffix="v1")
        assert filename == "report_v1.test"

        # Test with timestamp (just check format)
        filename = reporter.generate_filename("report", timestamp=True)
        assert filename.startswith("report_")
        assert filename.endswith(".test")
        assert len(filename.split("_")) >= 3  # report_YYYYMMDD_HHMMSS.test

    def test_report_header_creation(self):
        """Test the create_report_header method."""

        class TestReporter(BaseReporter):
            def __init__(self):
                super().__init__()
                self.reporter_name = "Test Reporter"
                self.output_format = "test"

            def format_data(self, data: Dict[str, Any], config: Dict[str, Any]) -> str:
                return ""

            def generate_report(
                self, data: ProcessingResult, output_path: str, config: Dict[str, Any]
            ) -> str:
                return ""

        reporter = TestReporter()
        result = ProcessingResult(
            success=True,
            operation="test",
            data={},
            errors=["error1"],
            warnings=["warning1", "warning2"],
            processing_time_seconds=2.5,
        )
        config = {"test": "value"}

        header = reporter.create_report_header("Test Report", result, config)

        assert header["title"] == "Test Report"
        assert header["generator"] == "Test Reporter"
        assert header["format"] == "test"
        assert header["processing_success"] is True
        assert header["execution_time"] == 2.5
        assert header["errors_count"] == 1
        assert header["warnings_count"] == 2
        assert header["config"] == config
        assert "generated_at" in header

    def test_error_handling_formatting(self):
        """Test the handle_processing_errors method."""

        class TestReporter(BaseReporter):
            def __init__(self):
                super().__init__()

            def format_data(self, data: Dict[str, Any], config: Dict[str, Any]) -> str:
                return ""

            def generate_report(
                self, data: ProcessingResult, output_path: str, config: Dict[str, Any]
            ) -> str:
                return ""

        reporter = TestReporter()

        # Test with no errors or warnings
        result = ProcessingResult(
            success=True,
            operation="test",
            data={},
            errors=[],
            warnings=[],
            processing_time_seconds=1.0,
        )
        error_text = reporter.handle_processing_errors(result)
        assert error_text == ""

        # Test with errors and warnings
        result = ProcessingResult(
            success=False,
            operation="test",
            data={},
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"],
            processing_time_seconds=1.0,
        )
        error_text = reporter.handle_processing_errors(result)

        assert "## Errors" in error_text
        assert "1. Error 1" in error_text
        assert "2. Error 2" in error_text
        assert "## Warnings" in error_text
        assert "1. Warning 1" in error_text

    def test_supported_config_options(self):
        """Test the get_supported_config_options method."""

        class TestReporter(BaseReporter):
            def __init__(self):
                super().__init__()

            def format_data(self, data: Dict[str, Any], config: Dict[str, Any]) -> str:
                return ""

            def generate_report(
                self, data: ProcessingResult, output_path: str, config: Dict[str, Any]
            ) -> str:
                return ""

        reporter = TestReporter()
        options = reporter.get_supported_config_options()

        assert "include_timestamp" in options
        assert "include_errors" in options
        assert "template" in options

        # Check structure of options
        timestamp_option = options["include_timestamp"]
        assert timestamp_option["type"] == bool
        assert timestamp_option["default"] is True
        assert "description" in timestamp_option
