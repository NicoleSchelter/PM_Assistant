"""
Unit tests for the FileScanner class.

This module contains comprehensive tests for file scanning, pattern matching,
format validation, and metadata extraction functionality.
"""

import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from core.file_scanner import FileScanner
from core.models import DocumentType, FileFormat, FileInfo, ProcessingStatus
from utils.exceptions import FileProcessingError, ValidationError


class TestFileScanner:
    """Test cases for FileScanner class."""

    @pytest.fixture
    def scanner(self):
        """Create a FileScanner instance for testing."""
        return FileScanner()

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary directory with sample project files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create sample files
            files_to_create = [
                "Project Charter.md",
                "Risk Register.xlsx",
                "Stakeholder Register.xlsx",
                "Work Breakdown Structure.md",
                "Project Roadmap.md",
                "Project Schedule.mpp",
                "random_file.txt",
                "config.yaml",
                "data.json",
                ".hidden_charter.md",
            ]

            for filename in files_to_create:
                file_path = temp_path / filename
                file_path.write_text(f"Sample content for {filename}")

            # Create subdirectory with files
            subdir = temp_path / "documents"
            subdir.mkdir()
            (subdir / "Additional Charter.md").write_text("Additional charter content")
            (subdir / "Risk Analysis.xlsx").write_text("Risk analysis content")

            yield temp_path

    @pytest.fixture
    def empty_dir(self):
        """Create an empty temporary directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_init_default_configuration(self):
        """Test FileScanner initialization with default configuration."""
        scanner = FileScanner()

        assert len(scanner.patterns) >= 6  # Should have default patterns
        assert DocumentType.CHARTER in scanner.patterns
        assert DocumentType.RISK_REGISTER in scanner.patterns
        assert len(scanner.supported_formats) > 0
        assert scanner.max_file_size_bytes == 100 * 1024 * 1024  # 100 MB

    def test_init_custom_configuration(self):
        """Test FileScanner initialization with custom configuration."""
        custom_patterns = {DocumentType.CHARTER: ["*custom*charter*"]}
        supported_formats = {FileFormat.MARKDOWN, FileFormat.EXCEL}

        scanner = FileScanner(
            custom_patterns=custom_patterns,
            supported_formats=supported_formats,
            max_file_size_mb=50,
        )

        assert scanner.patterns[DocumentType.CHARTER] == ["*custom*charter*"]
        assert scanner.supported_formats == supported_formats
        assert scanner.max_file_size_bytes == 50 * 1024 * 1024

    def test_scan_directory_recursive(self, scanner, temp_project_dir):
        """Test recursive directory scanning."""
        files = scanner.scan_directory(temp_project_dir, recursive=True)

        assert len(files) > 0

        # Check that files from subdirectories are included
        file_names = [f.filename for f in files]
        assert "Additional Charter.md" in file_names

        # Verify FileInfo objects are properly created
        for file_info in files:
            assert isinstance(file_info, FileInfo)
            assert file_info.path.exists()
            assert file_info.size_bytes >= 0
            assert isinstance(file_info.last_modified, datetime)

    def test_scan_directory_non_recursive(self, scanner, temp_project_dir):
        """Test non-recursive directory scanning."""
        files = scanner.scan_directory(temp_project_dir, recursive=False)

        # Should not include files from subdirectories
        file_names = [f.filename for f in files]
        assert "Additional Charter.md" not in file_names
        assert "Project Charter.md" in file_names

    def test_scan_directory_include_hidden(self, scanner, temp_project_dir):
        """Test scanning with hidden files included."""
        files_with_hidden = scanner.scan_directory(temp_project_dir, include_hidden=True)
        files_without_hidden = scanner.scan_directory(temp_project_dir, include_hidden=False)

        hidden_files = [f for f in files_with_hidden if f.filename.startswith(".")]
        assert len(hidden_files) > 0
        assert len(files_with_hidden) > len(files_without_hidden)

    def test_scan_nonexistent_directory(self, scanner):
        """Test scanning a non-existent directory."""
        with pytest.raises(
            FileProcessingError, match="Failed to scan directory.*Directory does not exist"
        ):
            scanner.scan_directory("/nonexistent/directory")

    def test_scan_file_instead_of_directory(self, scanner, temp_project_dir):
        """Test scanning when path points to a file instead of directory."""
        file_path = temp_project_dir / "Project Charter.md"

        with pytest.raises(FileProcessingError, match="Path is not a directory"):
            scanner.scan_directory(file_path)

    def test_match_document_patterns_charter(self, scanner):
        """Test pattern matching for charter documents."""
        test_cases = [
            ("Project Charter.md", [DocumentType.CHARTER]),
            ("project_charter.docx", [DocumentType.CHARTER]),
            ("charter.pdf", [DocumentType.CHARTER]),
            ("Charter Document.md", [DocumentType.CHARTER]),
            ("random_file.txt", [DocumentType.UNKNOWN]),
        ]

        for filename, expected_types in test_cases:
            matches = scanner.match_document_patterns(filename)
            assert matches == expected_types, f"Failed for {filename}"

    def test_match_document_patterns_risk_register(self, scanner):
        """Test pattern matching for risk register documents."""
        test_cases = [
            ("Risk Register.xlsx", [DocumentType.RISK_REGISTER]),
            ("risk_management_plan.md", [DocumentType.RISK_REGISTER]),
            ("risks.csv", [DocumentType.RISK_REGISTER]),
            ("project_risks.xlsx", [DocumentType.RISK_REGISTER]),
        ]

        for filename, expected_types in test_cases:
            matches = scanner.match_document_patterns(filename)
            assert DocumentType.RISK_REGISTER in matches, f"Failed for {filename}"

    def test_match_document_patterns_multiple_matches(self, scanner):
        """Test files that might match multiple document type patterns."""
        # A file that could match multiple patterns
        matches = scanner.match_document_patterns("project_risk_plan.md")

        # Should match at least risk register
        assert DocumentType.RISK_REGISTER in matches

    def test_match_document_patterns_custom_patterns(self, scanner):
        """Test pattern matching with custom patterns."""
        custom_patterns = {DocumentType.CHARTER: ["*custom*", "*special*"]}

        matches = scanner.match_document_patterns(
            "custom_document.md", custom_patterns=custom_patterns
        )

        assert DocumentType.CHARTER in matches

    def test_validate_file_formats_all_valid(self, scanner, temp_project_dir):
        """Test file format validation with all valid files."""
        files = scanner.scan_directory(temp_project_dir)
        result = scanner.validate_file_formats(files)

        assert result.success
        assert result.data["total_files"] == len(files)
        assert result.data["valid_files"] > 0
        assert result.processing_time_seconds > 0

    def test_validate_file_formats_with_invalid_files(self, scanner):
        """Test file format validation with some invalid files."""
        # Create FileInfo objects with invalid paths
        invalid_file = FileInfo(
            path=Path("/nonexistent/file.md"),
            format=FileFormat.MARKDOWN,
            document_type=DocumentType.CHARTER,
            size_bytes=1000,
            last_modified=datetime.now(),
        )

        result = scanner.validate_file_formats([invalid_file])

        assert not result.success or len(result.warnings) > 0
        assert result.data["invalid_files"] > 0

    def test_validate_file_formats_empty_list(self, scanner):
        """Test file format validation with empty file list."""
        result = scanner.validate_file_formats([])

        assert result.success
        assert result.data["total_files"] == 0
        assert result.data["valid_files"] == 0
        assert result.data["invalid_files"] == 0

    def test_get_file_statistics_comprehensive(self, scanner, temp_project_dir):
        """Test comprehensive file statistics generation."""
        files = scanner.scan_directory(temp_project_dir)
        stats = scanner.get_file_statistics(files)

        assert stats["total_files"] == len(files)
        assert "by_format" in stats
        assert "by_document_type" in stats
        assert stats["total_size_mb"] >= 0
        assert stats["readable_files"] >= 0
        assert stats["unreadable_files"] >= 0
        assert "largest_file" in stats
        assert "smallest_file" in stats
        assert "newest_file" in stats
        assert "oldest_file" in stats

    def test_get_file_statistics_empty_list(self, scanner):
        """Test file statistics with empty file list."""
        stats = scanner.get_file_statistics([])

        expected_empty_stats = {
            "total_files": 0,
            "by_format": {},
            "by_document_type": {},
            "total_size_mb": 0,
            "readable_files": 0,
            "unreadable_files": 0,
        }

        for key, value in expected_empty_stats.items():
            assert stats[key] == value

    def test_determine_file_format(self, scanner):
        """Test file format determination based on extensions."""
        test_cases = [
            ("document.md", FileFormat.MARKDOWN),
            ("spreadsheet.xlsx", FileFormat.EXCEL),
            ("legacy.xls", FileFormat.EXCEL_LEGACY),
            ("project.mpp", FileFormat.MICROSOFT_PROJECT),
            ("config.yaml", FileFormat.YAML),
            ("config.yml", FileFormat.YAML),
            ("data.json", FileFormat.JSON),
            ("data.csv", FileFormat.CSV),
            ("unknown.xyz", FileFormat.MARKDOWN),  # Default fallback
        ]

        for filename, expected_format in test_cases:
            file_path = Path(filename)
            format_result = scanner._determine_file_format(file_path)
            assert format_result == expected_format, f"Failed for {filename}"

    def test_create_file_info_valid_file(self, scanner, temp_project_dir):
        """Test FileInfo creation for valid files."""
        file_path = temp_project_dir / "Project Charter.md"
        file_info = scanner._create_file_info(file_path)

        assert file_info is not None
        assert file_info.path == file_path
        assert file_info.format == FileFormat.MARKDOWN
        assert file_info.document_type == DocumentType.CHARTER
        assert file_info.size_bytes > 0
        assert file_info.is_readable
        assert "matched_patterns" in file_info.metadata

    def test_create_file_info_unsupported_format(self, scanner, temp_project_dir):
        """Test FileInfo creation for unsupported file formats."""
        # Create a file with unsupported extension
        unsupported_file = temp_project_dir / "document.xyz"
        unsupported_file.write_text("content")

        # Configure scanner to not support markdown (default fallback)
        scanner.supported_formats = {FileFormat.EXCEL}

        file_info = scanner._create_file_info(unsupported_file)
        assert file_info is None

    def test_create_file_info_large_file(self, scanner, temp_project_dir):
        """Test FileInfo creation for files exceeding size limit."""
        # Set a very small file size limit
        scanner.max_file_size_bytes = 10

        large_file = temp_project_dir / "large_file.md"
        large_file.write_text("This content exceeds the 10 byte limit")

        file_info = scanner._create_file_info(large_file)
        assert file_info is None

    def test_validate_single_file_valid(self, scanner, temp_project_dir):
        """Test single file validation for valid file."""
        file_path = temp_project_dir / "Project Charter.md"
        file_info = FileInfo(
            path=file_path,
            format=FileFormat.MARKDOWN,
            document_type=DocumentType.CHARTER,
            size_bytes=file_path.stat().st_size,
            last_modified=datetime.now(),
        )

        validation_result = scanner._validate_single_file(file_info)

        assert validation_result["is_valid"]
        assert len(validation_result["checks_performed"]) > 0
        assert validation_result["error"] is None

    def test_validate_single_file_nonexistent(self, scanner):
        """Test single file validation for non-existent file."""
        file_info = FileInfo(
            path=Path("/nonexistent/file.md"),
            format=FileFormat.MARKDOWN,
            document_type=DocumentType.CHARTER,
            size_bytes=1000,
            last_modified=datetime.now(),
        )

        validation_result = scanner._validate_single_file(file_info)

        assert not validation_result["is_valid"]
        assert validation_result["error"] == "File does not exist"

    def test_validate_single_file_empty_file(self, scanner, temp_project_dir):
        """Test single file validation for empty file."""
        empty_file = temp_project_dir / "empty.md"
        empty_file.touch()  # Create empty file

        file_info = FileInfo(
            path=empty_file,
            format=FileFormat.MARKDOWN,
            document_type=DocumentType.CHARTER,
            size_bytes=0,
            last_modified=datetime.now(),
        )

        validation_result = scanner._validate_single_file(file_info)

        assert validation_result["is_valid"]  # Empty files are valid but warned
        assert "File is empty" in validation_result["warnings"]

    @patch("os.access")
    def test_validate_single_file_permission_denied(self, mock_access, scanner, temp_project_dir):
        """Test single file validation when file is not readable."""
        mock_access.return_value = False

        file_path = temp_project_dir / "Project Charter.md"
        file_info = FileInfo(
            path=file_path,
            format=FileFormat.MARKDOWN,
            document_type=DocumentType.CHARTER,
            size_bytes=1000,
            last_modified=datetime.now(),
        )

        validation_result = scanner._validate_single_file(file_info)

        assert not validation_result["is_valid"]
        assert validation_result["error"] == "File is not readable"

    def test_scan_directory_with_permission_error(self, scanner, temp_project_dir):
        """Test directory scanning with permission errors."""
        with patch("os.walk") as mock_walk:
            mock_walk.side_effect = PermissionError("Permission denied")

            # Should not raise exception, but return empty list
            files = scanner.scan_directory(temp_project_dir)
            assert files == []

    def test_file_scanner_integration(self, scanner, temp_project_dir):
        """Test complete file scanning workflow integration."""
        # Scan directory
        files = scanner.scan_directory(temp_project_dir, recursive=True)
        assert len(files) > 0

        # Validate files
        validation_result = scanner.validate_file_formats(files)
        assert validation_result.success

        # Get statistics
        stats = scanner.get_file_statistics(files)
        assert stats["total_files"] == len(files)

        # Verify we found expected document types
        doc_types = [f.document_type for f in files]
        assert DocumentType.CHARTER in doc_types
        assert DocumentType.RISK_REGISTER in doc_types

    def test_pattern_matching_case_insensitive(self, scanner):
        """Test that pattern matching is case insensitive."""
        test_cases = [
            "PROJECT CHARTER.MD",
            "project charter.md",
            "Project Charter.Md",
            "PROJECT_CHARTER.MD",
        ]

        for filename in test_cases:
            matches = scanner.match_document_patterns(filename)
            assert DocumentType.CHARTER in matches, f"Failed for {filename}"

    def test_format_specific_validation(self, scanner, temp_project_dir):
        """Test format-specific validation logic."""
        # Create files of different formats
        md_file = temp_project_dir / "test.md"
        xlsx_file = temp_project_dir / "test.xlsx"

        md_file.write_text("# Markdown content")
        xlsx_file.write_bytes(b"fake excel content")  # Not real Excel, but for testing

        md_info = FileInfo(
            path=md_file,
            format=FileFormat.MARKDOWN,
            document_type=DocumentType.CHARTER,
            size_bytes=md_file.stat().st_size,
            last_modified=datetime.now(),
        )

        xlsx_info = FileInfo(
            path=xlsx_file,
            format=FileFormat.EXCEL,
            document_type=DocumentType.RISK_REGISTER,
            size_bytes=xlsx_file.stat().st_size,
            last_modified=datetime.now(),
        )

        # Test format-specific validation
        md_validation = scanner._validate_file_format(md_info)
        xlsx_validation = scanner._validate_file_format(xlsx_info)

        assert md_validation["is_valid"]
        assert "markdown_format" in md_validation["checks_performed"]

        assert xlsx_validation["is_valid"]
        assert "excel_format" in xlsx_validation["checks_performed"]


class TestFileScannerEdgeCases:
    """Test edge cases and error conditions for FileScanner."""

    @pytest.fixture
    def scanner(self):
        """Create a FileScanner instance for testing."""
        return FileScanner()

    def test_scanner_with_no_supported_formats(self):
        """Test scanner behavior with no supported formats."""
        scanner = FileScanner(supported_formats=set())

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "test.md").write_text("content")

            files = scanner.scan_directory(temp_path)
            assert len(files) == 0  # No files should be discovered

    def test_scanner_with_very_restrictive_patterns(self):
        """Test scanner with very restrictive custom patterns."""
        custom_patterns = {DocumentType.CHARTER: ["exactly_this_name.md"]}

        scanner = FileScanner(custom_patterns=custom_patterns)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "exactly_this_name.md").write_text("content")
            (temp_path / "other_charter.md").write_text("content")

            files = scanner.scan_directory(temp_path)

            # Should only find the exactly matching file
            charter_files = [f for f in files if f.document_type == DocumentType.CHARTER]
            assert len(charter_files) == 1
            assert charter_files[0].filename == "exactly_this_name.md"

    def test_scanner_with_corrupted_directory_structure(self, scanner):
        """Test scanner behavior with unusual directory structures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create some unusual scenarios
            (temp_path / "file_with_no_extension").write_text("content")
            (temp_path / ".hidden_with_extension.md").write_text("content")

            # Create a directory that looks like a file
            fake_file_dir = temp_path / "looks_like_file.md"
            fake_file_dir.mkdir()

            files = scanner.scan_directory(temp_path, include_hidden=True)

            # Should handle these cases gracefully
            assert isinstance(files, list)

            # Directory should not be included as a file
            file_paths = [f.path for f in files]
            assert fake_file_dir not in file_paths

    def test_file_modification_during_scan(self, scanner):
        """Test behavior when files are modified during scanning."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "test.md"
            test_file.write_text("initial content")

            # Mock file modification during scan
            original_create_file_info = scanner._create_file_info

            def mock_create_file_info(file_path):
                if file_path.name == "test.md":
                    # Simulate file being modified during processing
                    file_path.write_text("modified content during scan")
                return original_create_file_info(file_path)

            scanner._create_file_info = mock_create_file_info

            # Should handle this gracefully
            files = scanner.scan_directory(temp_path)
            assert len(files) >= 0  # Should not crash
