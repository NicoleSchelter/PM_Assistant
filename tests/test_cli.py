"""
Tests for the command-line interface (CLI) module.

This module contains comprehensive tests for the CLI functionality including
command parsing, option handling, progress reporting, and integration with
the core engine.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from click.testing import CliRunner

from core.models import DocumentType, FileInfo, ModeRecommendation, OperationMode, ProcessingResult
from main import analyze, cli, detect_mode, list_files, status
from utils.exceptions import ConfigurationError, ValidationError


class TestCLIBasics:
    """Test basic CLI functionality and command parsing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_version_flag(self):
        """Test --version flag displays version information."""
        result = self.runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "PM Analysis Tool v" in result.output

    def test_help_command(self):
        """Test help command displays usage information."""
        result = self.runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "PM Analysis Tool" in result.output
        assert "document-check" in result.output
        assert "status-analysis" in result.output
        assert "learning-module" in result.output

    def test_subcommand_help(self):
        """Test subcommand help displays specific usage information."""
        result = self.runner.invoke(cli, ["analyze", "--help"])

        assert result.exit_code == 0
        assert "Run PM analysis" in result.output
        assert "--mode" in result.output
        assert "--project-path" in result.output


class TestAnalyzeCommand:
    """Test the main analyze command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.mock_engine = Mock()
        self.sample_result = ProcessingResult(
            success=True,
            operation="test_analysis",
            data={
                "execution_summary": {
                    "execution_id": "test_123",
                    "selected_mode": "document_check",
                    "files_discovered": 5,
                    "files_processed": 4,
                    "reports_generated": 1,
                    "total_execution_time": 2.5,
                },
                "report_summary": {
                    "markdown": {
                        "success": True,
                        "output_path": "/tmp/report.md",
                        "processing_time": 0.1,
                    }
                },
            },
            processing_time_seconds=2.5,
        )

    @patch("main.PMAnalysisEngine")
    def test_analyze_with_defaults(self, mock_engine_class):
        """Test analyze command with default parameters."""
        mock_engine_class.return_value = self.mock_engine
        self.mock_engine.run.return_value = self.sample_result

        with self.runner.isolated_filesystem():
            # Create a temporary project directory
            os.makedirs("project")

            result = self.runner.invoke(cli, ["analyze", "--project-path", "project", "--quiet"])

        assert result.exit_code == 0
        mock_engine_class.assert_called_once_with(config_path=None)
        self.mock_engine.run.assert_called_once_with(
            mode=None, project_path="project", output_formats=None
        )

    @patch("main.PMAnalysisEngine")
    def test_analyze_with_explicit_mode(self, mock_engine_class):
        """Test analyze command with explicit mode selection."""
        mock_engine_class.return_value = self.mock_engine
        self.mock_engine.run.return_value = self.sample_result

        with self.runner.isolated_filesystem():
            os.makedirs("project")

            result = self.runner.invoke(
                cli, ["analyze", "--mode", "document-check", "--project-path", "project", "--quiet"]
            )

        assert result.exit_code == 0
        self.mock_engine.run.assert_called_once_with(
            mode=OperationMode.DOCUMENT_CHECK, project_path="project", output_formats=None
        )

    @patch("main.PMAnalysisEngine")
    def test_analyze_with_multiple_output_formats(self, mock_engine_class):
        """Test analyze command with multiple output formats."""
        mock_engine_class.return_value = self.mock_engine
        self.mock_engine.run.return_value = self.sample_result

        with self.runner.isolated_filesystem():
            os.makedirs("project")

            result = self.runner.invoke(
                cli,
                [
                    "analyze",
                    "--output-format",
                    "markdown",
                    "--output-format",
                    "excel",
                    "--project-path",
                    "project",
                    "--quiet",
                ],
            )

        assert result.exit_code == 0
        self.mock_engine.run.assert_called_once_with(
            mode=None, project_path="project", output_formats=["markdown", "excel"]
        )

    @patch("main.PMAnalysisEngine")
    def test_analyze_with_custom_config(self, mock_engine_class):
        """Test analyze command with custom configuration file."""
        mock_engine_class.return_value = self.mock_engine
        self.mock_engine.run.return_value = self.sample_result

        with self.runner.isolated_filesystem():
            # Create config and project files
            with open("custom-config.yaml", "w") as f:
                f.write('project:\n  name: "Test Project"')
            os.makedirs("project")

            result = self.runner.invoke(
                cli,
                [
                    "analyze",
                    "--config",
                    "custom-config.yaml",
                    "--project-path",
                    "project",
                    "--quiet",
                ],
            )

        assert result.exit_code == 0
        mock_engine_class.assert_called_once_with(config_path="custom-config.yaml")

    @patch("main.PMAnalysisEngine")
    def test_analyze_configuration_error(self, mock_engine_class):
        """Test analyze command handles configuration errors gracefully."""
        mock_engine_class.side_effect = ConfigurationError("Invalid config")

        with self.runner.isolated_filesystem():
            os.makedirs("project")

            result = self.runner.invoke(cli, ["analyze", "--project-path", "project"])

        assert result.exit_code == 1
        assert "Configuration Error" in result.output

    @patch("main.PMAnalysisEngine")
    def test_analyze_processing_failure(self, mock_engine_class):
        """Test analyze command handles processing failures."""
        mock_engine_class.return_value = self.mock_engine
        failed_result = ProcessingResult(
            success=False,
            operation="failed_analysis",
            errors=["Processing failed"],
            processing_time_seconds=1.0,
        )
        self.mock_engine.run.return_value = failed_result

        with self.runner.isolated_filesystem():
            os.makedirs("project")

            result = self.runner.invoke(cli, ["analyze", "--project-path", "project", "--quiet"])

        assert result.exit_code == 1

    @patch("main.PMAnalysisEngine")
    def test_analyze_keyboard_interrupt(self, mock_engine_class):
        """Test analyze command handles keyboard interrupt gracefully."""
        mock_engine_class.return_value = self.mock_engine
        self.mock_engine.run.side_effect = KeyboardInterrupt()

        with self.runner.isolated_filesystem():
            os.makedirs("project")

            result = self.runner.invoke(cli, ["analyze", "--project-path", "project"])

        assert result.exit_code == 130
        assert "interrupted by user" in result.output


class TestDetectModeCommand:
    """Test the detect-mode command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.mock_engine = Mock()
        self.sample_recommendation = ModeRecommendation(
            recommended_mode=OperationMode.STATUS_ANALYSIS,
            confidence_score=0.85,
            reasoning="All required documents are present",
            available_documents=[DocumentType.PROJECT_CHARTER, DocumentType.RISK_REGISTER],
            missing_documents=[DocumentType.STAKEHOLDER_REGISTER],
            file_quality_scores={"charter.md": 0.9, "risks.xlsx": 0.8},
            alternative_modes=[OperationMode.DOCUMENT_CHECK],
        )

    @patch("main.PMAnalysisEngine")
    def test_detect_mode_success(self, mock_engine_class):
        """Test successful mode detection."""
        mock_engine_class.return_value = self.mock_engine
        self.mock_engine.detect_optimal_mode.return_value = self.sample_recommendation

        with self.runner.isolated_filesystem():
            os.makedirs("project")

            result = self.runner.invoke(cli, ["detect-mode", "--project-path", "project"])

        assert result.exit_code == 0
        assert "status-analysis" in result.output
        assert "85%" in result.output
        mock_engine_class.assert_called_once_with(config_path=None)
        self.mock_engine.detect_optimal_mode.assert_called_once_with("project")

    @patch("main.PMAnalysisEngine")
    def test_detect_mode_with_config(self, mock_engine_class):
        """Test mode detection with custom configuration."""
        mock_engine_class.return_value = self.mock_engine
        self.mock_engine.detect_optimal_mode.return_value = self.sample_recommendation

        with self.runner.isolated_filesystem():
            with open("config.yaml", "w") as f:
                f.write('project:\n  name: "Test"')
            os.makedirs("project")

            result = self.runner.invoke(
                cli, ["detect-mode", "--config", "config.yaml", "--project-path", "project"]
            )

        assert result.exit_code == 0
        mock_engine_class.assert_called_once_with(config_path="config.yaml")

    @patch("main.PMAnalysisEngine")
    def test_detect_mode_failure(self, mock_engine_class):
        """Test mode detection failure handling."""
        mock_engine_class.return_value = self.mock_engine
        self.mock_engine.detect_optimal_mode.side_effect = ValidationError("Detection failed")

        with self.runner.isolated_filesystem():
            os.makedirs("project")

            result = self.runner.invoke(cli, ["detect-mode", "--project-path", "project"])

        assert result.exit_code == 1
        assert "Mode detection failed" in result.output


class TestListFilesCommand:
    """Test the list-files command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.mock_engine = Mock()
        self.sample_files = [
            FileInfo(
                path="/project/charter.md",
                name="charter.md",
                file_format="md",
                size_bytes=1024,
                is_readable=True,
            ),
            FileInfo(
                path="/project/risks.xlsx",
                name="risks.xlsx",
                file_format="xlsx",
                size_bytes=2048,
                is_readable=True,
            ),
        ]

    @patch("main.PMAnalysisEngine")
    def test_list_files_success(self, mock_engine_class):
        """Test successful file listing."""
        mock_engine_class.return_value = self.mock_engine
        self.mock_engine.get_available_files.return_value = self.sample_files

        with self.runner.isolated_filesystem():
            os.makedirs("project")

            result = self.runner.invoke(cli, ["list-files", "--project-path", "project"])

        assert result.exit_code == 0
        assert "charter.md" in result.output
        assert "risks.xlsx" in result.output
        assert "2 total" in result.output
        self.mock_engine.get_available_files.assert_called_once_with("project")

    @patch("main.PMAnalysisEngine")
    def test_list_files_empty_directory(self, mock_engine_class):
        """Test file listing with empty directory."""
        mock_engine_class.return_value = self.mock_engine
        self.mock_engine.get_available_files.return_value = []

        with self.runner.isolated_filesystem():
            os.makedirs("project")

            result = self.runner.invoke(cli, ["list-files", "--project-path", "project"])

        assert result.exit_code == 0
        assert "No project files found" in result.output

    @patch("main.PMAnalysisEngine")
    def test_list_files_failure(self, mock_engine_class):
        """Test file listing failure handling."""
        mock_engine_class.return_value = self.mock_engine
        self.mock_engine.get_available_files.side_effect = Exception("Scan failed")

        with self.runner.isolated_filesystem():
            os.makedirs("project")

            result = self.runner.invoke(cli, ["list-files", "--project-path", "project"])

        assert result.exit_code == 1
        assert "File scanning failed" in result.output


class TestStatusCommand:
    """Test the status command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.mock_engine = Mock()
        self.sample_engine_status = {
            "initialized": True,
            "config_loaded": True,
            "processors_available": ["document_check", "status_analysis"],
            "reporters_available": ["markdown", "excel"],
            "last_scan_file_count": 5,
            "execution_count": 3,
            "last_recommended_mode": "status_analysis",
        }
        self.sample_processor_info = {
            "document_check": {"name": "Document Check Processor", "version": "1.0.0"},
            "status_analysis": {"name": "Status Analysis Processor", "version": "1.0.0"},
        }

    @patch("main.PMAnalysisEngine")
    def test_status_success(self, mock_engine_class):
        """Test successful status display."""
        mock_engine_class.return_value = self.mock_engine
        self.mock_engine.get_engine_status.return_value = self.sample_engine_status
        self.mock_engine.get_processor_info.return_value = self.sample_processor_info

        result = self.runner.invoke(cli, ["status"])

        assert result.exit_code == 0
        assert "Engine Status" in result.output
        assert "Initialized" in result.output
        assert "Available Processors" in result.output
        mock_engine_class.assert_called_once_with(config_path=None)

    @patch("main.PMAnalysisEngine")
    def test_status_with_config(self, mock_engine_class):
        """Test status command with custom configuration."""
        mock_engine_class.return_value = self.mock_engine
        self.mock_engine.get_engine_status.return_value = self.sample_engine_status
        self.mock_engine.get_processor_info.return_value = self.sample_processor_info

        with self.runner.isolated_filesystem():
            with open("config.yaml", "w") as f:
                f.write('project:\n  name: "Test"')

            result = self.runner.invoke(cli, ["status", "--config", "config.yaml"])

        assert result.exit_code == 0
        mock_engine_class.assert_called_once_with(config_path="config.yaml")

    @patch("main.PMAnalysisEngine")
    def test_status_failure(self, mock_engine_class):
        """Test status command failure handling."""
        mock_engine_class.side_effect = Exception("Status check failed")

        result = self.runner.invoke(cli, ["status"])

        assert result.exit_code == 1
        assert "Status check failed" in result.output


class TestCLIIntegration:
    """Test CLI integration scenarios and edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_invalid_project_path(self):
        """Test CLI handles invalid project paths gracefully."""
        result = self.runner.invoke(cli, ["analyze", "--project-path", "/nonexistent/path"])

        assert result.exit_code == 2  # Click validation error
        assert "does not exist" in result.output

    def test_invalid_config_path(self):
        """Test CLI handles invalid config paths gracefully."""
        result = self.runner.invoke(cli, ["analyze", "--config", "/nonexistent/config.yaml"])

        assert result.exit_code == 2  # Click validation error
        assert "does not exist" in result.output

    def test_invalid_mode_option(self):
        """Test CLI handles invalid mode options gracefully."""
        result = self.runner.invoke(cli, ["analyze", "--mode", "invalid-mode"])

        assert result.exit_code == 2  # Click validation error
        assert "Invalid value" in result.output

    def test_invalid_output_format(self):
        """Test CLI handles invalid output format options gracefully."""
        result = self.runner.invoke(cli, ["analyze", "--output-format", "invalid-format"])

        assert result.exit_code == 2  # Click validation error
        assert "Invalid value" in result.output

    @patch("main.PMAnalysisEngine")
    def test_verbose_output(self, mock_engine_class):
        """Test verbose output includes additional details."""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine

        result_with_warnings = ProcessingResult(
            success=True,
            operation="test_analysis",
            data={"execution_summary": {"execution_id": "test"}},
            warnings=["Test warning"],
            errors=["Test error"],
            processing_time_seconds=1.0,
        )
        mock_engine.run.return_value = result_with_warnings

        with self.runner.isolated_filesystem():
            os.makedirs("project")

            result = self.runner.invoke(cli, ["analyze", "--project-path", "project", "--verbose"])

        assert result.exit_code == 0
        assert "Test warning" in result.output
        assert "Test error" in result.output

    @patch("main.PMAnalysisEngine")
    def test_quiet_mode(self, mock_engine_class):
        """Test quiet mode suppresses non-essential output."""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine

        simple_result = ProcessingResult(
            success=True, operation="test_analysis", data={}, processing_time_seconds=1.0
        )
        mock_engine.run.return_value = simple_result

        with self.runner.isolated_filesystem():
            os.makedirs("project")

            result = self.runner.invoke(cli, ["analyze", "--project-path", "project", "--quiet"])

        assert result.exit_code == 0
        # In quiet mode, output should be minimal
        assert "Welcome" not in result.output

    def test_main_entry_point_without_subcommand(self):
        """Test that CLI runs analyze by default when no subcommand is provided."""
        with patch("main.PMAnalysisEngine") as mock_engine_class:
            mock_engine = Mock()
            mock_engine_class.return_value = mock_engine
            mock_engine.run.return_value = ProcessingResult(
                success=True, operation="test", data={}, processing_time_seconds=1.0
            )

            with self.runner.isolated_filesystem():
                os.makedirs("project")

                result = self.runner.invoke(cli, ["--project-path", "project", "--quiet"])

            assert result.exit_code == 0
            mock_engine.run.assert_called_once()


class TestProgressReporting:
    """Test progress reporting and user feedback functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("main.PMAnalysisEngine")
    @patch("main.time.sleep")  # Speed up tests by mocking sleep
    def test_progress_display(self, mock_sleep, mock_engine_class):
        """Test that progress is displayed during analysis."""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine
        mock_engine.run.return_value = ProcessingResult(
            success=True,
            operation="test_analysis",
            data={"execution_summary": {"execution_id": "test"}},
            processing_time_seconds=1.0,
        )

        with self.runner.isolated_filesystem():
            os.makedirs("project")

            result = self.runner.invoke(cli, ["analyze", "--project-path", "project"])

        assert result.exit_code == 0
        # Progress-related text should appear in output
        assert "Scanning project files" in result.output or "Analysis complete" in result.output

    @patch("main.PMAnalysisEngine")
    def test_no_progress_in_quiet_mode(self, mock_engine_class):
        """Test that progress is not displayed in quiet mode."""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine
        mock_engine.run.return_value = ProcessingResult(
            success=True, operation="test_analysis", data={}, processing_time_seconds=1.0
        )

        with self.runner.isolated_filesystem():
            os.makedirs("project")

            result = self.runner.invoke(cli, ["analyze", "--project-path", "project", "--quiet"])

        assert result.exit_code == 0
        # Progress text should not appear in quiet mode
        assert "Scanning project files" not in result.output
