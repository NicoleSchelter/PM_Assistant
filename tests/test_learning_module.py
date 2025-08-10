"""
Unit tests for LearningModuleProcessor.

This module contains comprehensive tests for the learning module processor
functionality including content loading and presentation.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from core.models import DocumentType, FileFormat, FileInfo
from processors.learning_module import LearningModuleProcessor
from utils.exceptions import FileProcessingError


class TestLearningModuleProcessor:
    """Test cases for LearningModuleProcessor class."""

    @pytest.fixture
    def processor(self):
        """Create a LearningModuleProcessor instance for testing."""
        return LearningModuleProcessor()

    @pytest.fixture
    def sample_config(self):
        """Create sample configuration for testing."""
        return {"modes": {"learning_module": {"content_path": "./test_learning"}}}

    @pytest.fixture
    def sample_files(self):
        """Create sample project files for testing."""
        return [
            FileInfo(
                path=Path("risk_register.xlsx"),
                format=FileFormat.EXCEL,
                document_type=DocumentType.RISK_REGISTER,
                size_bytes=4096,
                last_modified=datetime(2024, 1, 15, 10, 0, 0),
                is_readable=True,
            ),
            FileInfo(
                path=Path("stakeholder_register.xlsx"),
                format=FileFormat.EXCEL,
                document_type=DocumentType.STAKEHOLDER_REGISTER,
                size_bytes=3072,
                last_modified=datetime(2024, 1, 15, 11, 0, 0),
                is_readable=True,
            ),
            FileInfo(
                path=Path("project_wbs.md"),
                format=FileFormat.MARKDOWN,
                document_type=DocumentType.WBS,
                size_bytes=2048,
                last_modified=datetime(2024, 1, 15, 12, 0, 0),
                is_readable=True,
            ),
        ]

    @pytest.fixture
    def sample_markdown_content(self):
        """Create sample markdown content for testing."""
        return """
# Risk Management

## Overview
Risk management is crucial for project success.

## Key Concepts
- Risk identification
- Risk assessment
- Risk mitigation

## Best Practices
- Regular risk reviews
- Stakeholder involvement
- Documentation

## Common Pitfalls
- Ignoring low-probability risks
- Poor communication
"""

    def test_processor_initialization(self, processor):
        """Test that processor initializes correctly."""
        assert processor.processor_name == "Learning Module Processor"
        assert len(processor.required_files) == 0  # No required files
        assert len(processor.optional_files) > 0
        assert processor.markdown_handler is not None
        assert len(processor.learning_categories) > 0
        assert "risk_management" in processor.learning_categories
        assert "stakeholder_management" in processor.learning_categories

    def test_validate_inputs_always_true(self, processor):
        """Test that input validation always returns True."""
        # Empty files
        assert processor.validate_inputs([]) is True

        # With files
        sample_files = [
            FileInfo(
                path=Path("test.md"),
                format=FileFormat.MARKDOWN,
                document_type=DocumentType.UNKNOWN,
                size_bytes=1024,
                last_modified=datetime.now(),
                is_readable=True,
            )
        ]
        assert processor.validate_inputs(sample_files) is True

        # Unreadable files
        unreadable_files = [
            FileInfo(
                path=Path("test.md"),
                format=FileFormat.MARKDOWN,
                document_type=DocumentType.UNKNOWN,
                size_bytes=1024,
                last_modified=datetime.now(),
                is_readable=False,
            )
        ]
        assert processor.validate_inputs(unreadable_files) is True

    def test_identify_relevant_topics_empty_files(self, processor):
        """Test topic identification with empty file list."""
        topics = processor._identify_relevant_topics([])

        assert isinstance(topics, list)
        assert len(topics) >= 3  # Should return default topics
        assert "project_planning" in topics
        assert "risk_management" in topics
        assert "stakeholder_management" in topics

    def test_identify_relevant_topics_with_files(self, processor, sample_files):
        """Test topic identification with project files."""
        topics = processor._identify_relevant_topics(sample_files)

        assert isinstance(topics, list)
        assert len(topics) > 0
        assert "risk_management" in topics  # Should identify from risk_register.xlsx
        assert "stakeholder_management" in topics  # Should identify from stakeholder_register.xlsx
        assert "project_planning" in topics  # Should be included as fundamental

    def test_identify_relevant_topics_limits_results(self, processor):
        """Test that topic identification limits results to 5."""
        # Create files that would match many topics
        many_topic_files = [
            FileInfo(
                path=Path("risk_budget_quality_schedule_stakeholder_wbs_communication.md"),
                format=FileFormat.MARKDOWN,
                document_type=DocumentType.UNKNOWN,
                size_bytes=1024,
                last_modified=datetime.now(),
                is_readable=True,
            )
        ]

        topics = processor._identify_relevant_topics(many_topic_files)
        assert len(topics) <= 5

    def test_parse_topic_content(self, processor, sample_markdown_content):
        """Test parsing of topic content from markdown."""
        parsed = processor._parse_topic_content(sample_markdown_content)

        assert isinstance(parsed, dict)
        assert "overview" in parsed
        assert "key_concepts" in parsed
        assert "best_practices" in parsed
        assert "common_pitfalls" in parsed

        # Check that content was parsed correctly
        assert "Risk management is crucial" in parsed["overview"]
        assert len(parsed["key_concepts"]) == 3
        assert "Risk identification" in parsed["key_concepts"]
        assert len(parsed["best_practices"]) == 3
        assert "Regular risk reviews" in parsed["best_practices"]

    def test_get_default_topic_content(self, processor):
        """Test generation of default topic content."""
        # Test known topic
        risk_content = processor._get_default_topic_content("risk_management")

        assert isinstance(risk_content, dict)
        assert "overview" in risk_content
        assert "key_concepts" in risk_content
        assert "best_practices" in risk_content
        assert "common_pitfalls" in risk_content
        assert len(risk_content["key_concepts"]) > 0
        assert len(risk_content["best_practices"]) > 0

        # Test unknown topic
        unknown_content = processor._get_default_topic_content("unknown_topic")
        assert "not available" in unknown_content["overview"].lower()

    def test_get_default_learning_content(self, processor):
        """Test generation of default learning content."""
        topics = ["risk_management", "stakeholder_management"]
        content = processor._get_default_learning_content(topics)

        assert isinstance(content, dict)
        assert "topics" in content
        assert "general_guidance" in content
        assert "templates" in content
        assert "examples" in content

        # Check that topics were included
        assert "risk_management" in content["topics"]
        assert "stakeholder_management" in content["topics"]

        # Check general guidance
        assert len(content["general_guidance"]) > 0
        assert "title" in content["general_guidance"][0]
        assert "content" in content["general_guidance"][0]

    def test_generate_learning_recommendations_empty_files(self, processor):
        """Test recommendation generation with empty files."""
        recommendations = processor._generate_learning_recommendations([], [])

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        # Should include general recommendations
        assert any("project management" in rec.lower() for rec in recommendations)

    def test_generate_learning_recommendations_with_files(self, processor, sample_files):
        """Test recommendation generation with project files."""
        topics = ["risk_management", "stakeholder_management"]
        recommendations = processor._generate_learning_recommendations(sample_files, topics)

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert len(recommendations) <= 8  # Should limit recommendations

        # Should include topic-specific recommendations
        assert any("risk" in rec.lower() for rec in recommendations)
        assert any("stakeholder" in rec.lower() for rec in recommendations)

    def test_format_learning_content(self, processor):
        """Test formatting of learning content."""
        learning_content = {
            "topics": {
                "risk_management": {
                    "overview": "Risk management overview",
                    "key_concepts": ["Concept 1", "Concept 2"],
                }
            },
            "general_guidance": [{"title": "Test Guidance", "content": "Test content"}],
            "templates": [],
            "examples": [],
        }
        recommendations = ["Test recommendation"]
        relevant_topics = ["risk_management"]

        formatted = processor._format_learning_content(
            learning_content, recommendations, relevant_topics
        )

        assert isinstance(formatted, dict)
        assert "learning_overview" in formatted
        assert "topic_content" in formatted
        assert "general_guidance" in formatted
        assert "personalized_recommendations" in formatted
        assert "quick_tips" in formatted
        assert "additional_resources" in formatted

        # Check learning overview
        overview = formatted["learning_overview"]
        assert "relevant_topics" in overview
        assert "total_topics" in overview
        assert len(overview["relevant_topics"]) == 1
        assert overview["relevant_topics"][0]["key"] == "risk_management"

        # Check topic content formatting
        assert "risk_management" in formatted["topic_content"]
        topic_content = formatted["topic_content"]["risk_management"]
        assert "title" in topic_content
        assert "content" in topic_content

    def test_get_quick_tips(self, processor):
        """Test quick tips generation."""
        tips = processor._get_quick_tips()

        assert isinstance(tips, list)
        assert len(tips) > 0
        assert all(isinstance(tip, str) for tip in tips)
        assert any("success criteria" in tip.lower() for tip in tips)

    def test_get_additional_resources(self, processor):
        """Test additional resources generation."""
        resources = processor._get_additional_resources()

        assert isinstance(resources, list)
        assert len(resources) > 0

        for resource in resources:
            assert isinstance(resource, dict)
            assert "title" in resource
            assert "description" in resource
            assert "type" in resource

        # Check for expected resources
        titles = [r["title"] for r in resources]
        assert any("PMI" in title for title in titles)
        assert any("PRINCE2" in title for title in titles)

    def test_get_pm_fundamentals_content(self, processor):
        """Test PM fundamentals content generation."""
        content = processor._get_pm_fundamentals_content()

        assert isinstance(content, str)
        assert len(content) > 0
        assert "Project Management Fundamentals" in content
        assert "Integration Management" in content
        assert "Success Factors" in content

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_dir")
    def test_load_learning_content_directory_not_found(self, mock_is_dir, mock_exists, processor):
        """Test loading content when directory doesn't exist."""
        mock_exists.return_value = False
        mock_is_dir.return_value = False

        content = processor._load_learning_content("./nonexistent", ["risk_management"])

        # Should fall back to default content
        assert isinstance(content, dict)
        assert "topics" in content
        assert "risk_management" in content["topics"]

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_dir")
    @patch("pathlib.Path.glob")
    def test_load_content_from_directory(self, mock_glob, mock_is_dir, mock_exists, processor):
        """Test loading content from directory."""
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        mock_glob.return_value = []  # No files found

        # Mock the markdown handler
        with patch.object(processor, "read_file", return_value="Test content"):
            content_dir = Path("./test_content")
            content = processor._load_content_from_directory(content_dir, ["risk_management"])

            assert isinstance(content, dict)
            assert "topics" in content
            assert "general_guidance" in content
            assert "templates" in content
            assert "examples" in content

    def test_process_successful(self, processor, sample_files, sample_config):
        """Test successful processing."""
        # Mock the content loading to avoid file system dependencies
        with patch.object(processor, "_load_learning_content") as mock_load:
            mock_load.return_value = {
                "topics": {
                    "risk_management": {"overview": "Test overview", "key_concepts": ["Concept 1"]}
                },
                "general_guidance": [],
                "templates": [],
                "examples": [],
            }

            result = processor.process(sample_files, sample_config)

            assert result.success is True
            assert result.operation == "learning_module"
            assert "learning_overview" in result.data
            assert "topic_content" in result.data
            assert "personalized_recommendations" in result.data
            assert result.processing_time_seconds >= 0

    def test_process_with_empty_files(self, processor, sample_config):
        """Test processing with empty file list."""
        with patch.object(processor, "_load_learning_content") as mock_load:
            mock_load.return_value = {
                "topics": {},
                "general_guidance": [],
                "templates": [],
                "examples": [],
            }

            result = processor.process([], sample_config)

            assert result.success is True
            assert result.operation == "learning_module"
            assert "learning_overview" in result.data

    def test_process_with_no_config(self, processor, sample_files):
        """Test processing with no configuration."""
        with patch.object(processor, "_load_learning_content") as mock_load:
            mock_load.return_value = {
                "topics": {},
                "general_guidance": [],
                "templates": [],
                "examples": [],
            }

            result = processor.process(sample_files, {})

            assert result.success is True
            # Should use default content path
            mock_load.assert_called_once()
            args = mock_load.call_args[0]
            assert args[0] == processor.default_content_paths[0]

    def test_process_with_exception(self, processor, sample_files, sample_config):
        """Test processing when an exception occurs."""
        with patch.object(
            processor, "_identify_relevant_topics", side_effect=Exception("Test error")
        ):
            result = processor.process(sample_files, sample_config)

            assert result.success is False
            assert len(result.errors) > 0
            assert "Test error" in result.errors[0]

    @patch("processors.learning_module.logger")
    def test_logging_behavior(self, mock_logger, processor, sample_files, sample_config):
        """Test that appropriate logging occurs during processing."""
        with patch.object(processor, "_load_learning_content") as mock_load:
            mock_load.return_value = {
                "topics": {},
                "general_guidance": [],
                "templates": [],
                "examples": [],
            }

            processor.process(sample_files, sample_config)

            # Verify that info logging occurred
            mock_logger.info.assert_called()

    def test_processing_time_tracking(self, processor, sample_files, sample_config):
        """Test that processing time is tracked correctly."""
        with patch.object(processor, "_load_learning_content") as mock_load:
            mock_load.return_value = {
                "topics": {},
                "general_guidance": [],
                "templates": [],
                "examples": [],
            }

            result = processor.process(sample_files, sample_config)

            assert result.success is True
            assert result.processing_time_seconds >= 0
            assert isinstance(result.processing_time_seconds, float)

    def test_learning_categories_completeness(self, processor):
        """Test that learning categories are comprehensive."""
        categories = processor.learning_categories

        # Should have key PM knowledge areas
        expected_categories = [
            "risk_management",
            "stakeholder_management",
            "project_planning",
            "quality_management",
            "communication",
        ]

        for category in expected_categories:
            assert category in categories
            assert isinstance(categories[category], str)
            assert len(categories[category]) > 0

    def test_default_content_paths(self, processor):
        """Test that default content paths are defined."""
        paths = processor.default_content_paths

        assert isinstance(paths, list)
        assert len(paths) > 0
        assert all(isinstance(path, str) for path in paths)
        assert "./learning/modules" in paths
