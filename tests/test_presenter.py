"""
Tests for the Presenter class.

This module contains comprehensive tests for the Presenter class
that handles formatting and display of learning content.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from learning.presenter import Presenter


class TestPresenter:
    """Test cases for Presenter class."""

    @pytest.fixture
    def sample_learning_content(self):
        """Sample learning content for testing."""
        return {
            "topics": {
                "risk_management": {
                    "overview": "Risk management is essential for project success.",
                    "key_concepts": ["Risk identification", "Risk assessment", "Risk mitigation"],
                    "best_practices": ["Regular risk reviews", "Stakeholder involvement"],
                    "common_pitfalls": ["Ignoring low-probability risks"],
                    "tools_techniques": [],
                    "references": [],
                },
                "stakeholder_analysis": {
                    "overview": "Understanding stakeholders is crucial.",
                    "key_concepts": ["Stakeholder identification", "Power-interest mapping"],
                    "best_practices": [],
                    "common_pitfalls": [],
                    "tools_techniques": [],
                    "references": [],
                },
            },
            "general_guidance": [
                {
                    "title": "Project Management Fundamentals",
                    "content": "# PM Fundamentals\n\n## Key Areas\n- Planning\n- Execution",
                }
            ],
            "templates": [
                {
                    "name": "Risk Register Template",
                    "content": "# Risk Register\n\n## Usage Notes\nUse this template for tracking risks.",
                }
            ],
            "examples": [
                {
                    "name": "Project Charter Example",
                    "content": "# Charter Example\n\n## Key Points\n- Clear objectives\n- Defined scope",
                }
            ],
        }

    @pytest.fixture
    def sample_recommendations(self):
        """Sample recommendations for testing."""
        return [
            "Focus on risk management - it's crucial for project success",
            "Consider stakeholder engagement strategies",
            "Review project planning fundamentals",
            "Study advanced scheduling techniques",
        ]

    @pytest.fixture
    def sample_relevant_topics(self):
        """Sample relevant topics for testing."""
        return ["risk_management", "stakeholder_analysis"]

    def test_initialization(self):
        """Test Presenter initialization."""
        presenter = Presenter()

        assert hasattr(presenter, "learning_categories")
        assert "risk_management" in presenter.learning_categories
        assert "stakeholder_analysis" in presenter.learning_categories
        assert "scheduling" in presenter.learning_categories

        # Verify category titles
        assert presenter.learning_categories["risk_management"] == "Risk Management Best Practices"
        assert (
            presenter.learning_categories["stakeholder_analysis"]
            == "Stakeholder Analysis Strategies"
        )

    def test_present_learning_content_complete(
        self, sample_learning_content, sample_recommendations, sample_relevant_topics
    ):
        """Test complete learning content presentation."""
        presenter = Presenter()

        result = presenter.present_learning_content(
            sample_learning_content, sample_recommendations, sample_relevant_topics
        )

        # Verify main structure
        assert "learning_overview" in result
        assert "topic_content" in result
        assert "general_guidance" in result
        assert "templates" in result
        assert "examples" in result
        assert "personalized_recommendations" in result
        assert "quick_tips" in result
        assert "additional_resources" in result
        assert "presentation_metadata" in result

        # Verify metadata
        metadata = result["presentation_metadata"]
        assert "generated_at" in metadata
        assert metadata["total_topics"] == 2
        assert "content_sections" in metadata

    def test_create_learning_overview(self, sample_learning_content, sample_relevant_topics):
        """Test learning overview creation."""
        presenter = Presenter()

        overview = presenter._create_learning_overview(
            sample_learning_content, sample_relevant_topics
        )

        # Verify structure
        assert "relevant_topics" in overview
        assert "total_topics" in overview
        assert "content_sources" in overview
        assert "summary" in overview

        # Verify topics info
        topics_info = overview["relevant_topics"]
        assert len(topics_info) == 2

        risk_topic = next(t for t in topics_info if t["key"] == "risk_management")
        assert risk_topic["title"] == "Risk Management Best Practices"
        assert risk_topic["available"] is True
        assert risk_topic["content_sections"] > 0

        stakeholder_topic = next(t for t in topics_info if t["key"] == "stakeholder_analysis")
        assert stakeholder_topic["title"] == "Stakeholder Analysis Strategies"
        assert stakeholder_topic["available"] is True

        # Verify summary
        assert "All 2 relevant learning topics have content available" in overview["summary"]

    def test_create_learning_overview_missing_topics(self):
        """Test learning overview with missing topics."""
        presenter = Presenter()

        # Empty content
        empty_content = {"topics": {}}
        topics = ["risk_management", "stakeholder_analysis"]

        overview = presenter._create_learning_overview(empty_content, topics)

        # Verify topics marked as unavailable
        topics_info = overview["relevant_topics"]
        assert len(topics_info) == 2

        for topic_info in topics_info:
            assert topic_info["available"] is False
            assert topic_info["content_sections"] == 0

        # Verify summary reflects missing content
        assert "0 of 2 relevant topics have detailed content available" in overview["summary"]

    def test_format_topic_content(self, sample_learning_content):
        """Test topic content formatting."""
        presenter = Presenter()

        topics = sample_learning_content["topics"]
        formatted = presenter._format_topic_content(topics)

        # Verify structure
        assert "risk_management" in formatted
        assert "stakeholder_analysis" in formatted

        # Verify risk management topic
        risk_topic = formatted["risk_management"]
        assert "title" in risk_topic
        assert "content" in risk_topic
        assert "sections" in risk_topic

        assert risk_topic["title"] == "Risk Management Best Practices"

        # Verify content sections
        content = risk_topic["content"]
        assert "overview" in content
        assert "key_concepts" in content
        assert "best_practices" in content

        # Verify section types
        assert content["overview"]["type"] == "text"
        assert content["key_concepts"]["type"] == "list"
        assert len(content["key_concepts"]["items"]) == 3

        # Verify sections list
        sections = risk_topic["sections"]
        assert "overview" in sections
        assert "key_concepts" in sections
        assert "best_practices" in sections
        # Empty sections should not be included
        assert "tools_techniques" not in sections

    def test_format_single_topic_content(self):
        """Test single topic content formatting."""
        presenter = Presenter()

        topic_content = {
            "overview": "This is the overview text.",
            "key_concepts": ["Concept 1", "Concept 2"],
            "best_practices": [],  # Empty list
            "common_pitfalls": ["Pitfall 1"],
        }

        formatted = presenter._format_single_topic_content(topic_content)

        # Verify text content
        assert "overview" in formatted
        assert formatted["overview"]["type"] == "text"
        assert formatted["overview"]["content"] == "This is the overview text."

        # Verify list content
        assert "key_concepts" in formatted
        assert formatted["key_concepts"]["type"] == "list"
        assert formatted["key_concepts"]["items"] == ["Concept 1", "Concept 2"]

        # Verify empty sections are excluded
        assert "best_practices" not in formatted

        # Verify single-item list
        assert "common_pitfalls" in formatted
        assert formatted["common_pitfalls"]["type"] == "list"
        assert formatted["common_pitfalls"]["items"] == ["Pitfall 1"]

    def test_get_topic_sections(self):
        """Test topic sections extraction."""
        presenter = Presenter()

        topic_content = {
            "overview": "Overview text",
            "key_concepts": ["Concept 1"],
            "best_practices": [],  # Empty
            "common_pitfalls": ["Pitfall 1"],
            "tools_techniques": [],  # Empty
            "references": ["Ref 1"],
        }

        sections = presenter._get_topic_sections(topic_content)

        # Should only include non-empty sections in order
        expected_sections = ["overview", "key_concepts", "common_pitfalls", "references"]
        assert sections == expected_sections

    def test_format_general_guidance(self, sample_learning_content):
        """Test general guidance formatting."""
        presenter = Presenter()

        guidance = sample_learning_content["general_guidance"]
        formatted = presenter._format_general_guidance(guidance)

        assert len(formatted) == 1

        guidance_item = formatted[0]
        assert "title" in guidance_item
        assert "content" in guidance_item
        assert "sections" in guidance_item

        assert guidance_item["title"] == "Project Management Fundamentals"

        # Verify content formatting
        content = guidance_item["content"]
        assert "type" in content
        assert "content" in content
        assert "has_headers" in content
        assert "has_lists" in content
        assert "word_count" in content

        # Should detect structured content
        assert content["type"] == "structured"
        assert content["has_headers"] is True
        assert content["has_lists"] is True
        assert content["word_count"] > 0

    def test_format_templates(self, sample_learning_content):
        """Test template formatting."""
        presenter = Presenter()

        templates = sample_learning_content["templates"]
        formatted = presenter._format_templates(templates)

        assert len(formatted) == 1

        template = formatted[0]
        assert "name" in template
        assert "content" in template
        assert "type" in template
        assert "usage_notes" in template

        assert template["name"] == "Risk Register Template"
        assert template["type"] == "template"

        # Verify usage notes extraction
        usage_notes = template["usage_notes"]
        assert len(usage_notes) >= 1
        assert any("usage" in note.lower() for note in usage_notes)

    def test_format_examples(self, sample_learning_content):
        """Test example formatting."""
        presenter = Presenter()

        examples = sample_learning_content["examples"]
        formatted = presenter._format_examples(examples)

        assert len(formatted) == 1

        example = formatted[0]
        assert "name" in example
        assert "content" in example
        assert "type" in example
        assert "key_points" in example

        assert example["name"] == "Project Charter Example"
        assert example["type"] == "example"

        # Verify key points extraction
        key_points = example["key_points"]
        assert len(key_points) >= 1

    def test_format_recommendations(self, sample_recommendations):
        """Test recommendations formatting."""
        presenter = Presenter()

        formatted = presenter._format_recommendations(sample_recommendations)

        assert len(formatted) == 4

        # Verify first recommendation
        rec1 = formatted[0]
        assert "id" in rec1
        assert "text" in rec1
        assert "priority" in rec1
        assert "category" in rec1

        assert rec1["id"] == 1
        assert rec1["text"] == "Focus on risk management - it's crucial for project success"
        assert rec1["priority"] in ["high", "medium", "low"]
        assert rec1["category"] in [
            "risk_management",
            "stakeholder_management",
            "project_planning",
            "quality_management",
            "general",
        ]

    def test_determine_recommendation_priority(self):
        """Test recommendation priority determination."""
        presenter = Presenter()

        # High priority keywords
        high_rec = "This is crucial for project success"
        assert presenter._determine_recommendation_priority(high_rec) == "high"

        essential_rec = "Essential project management practices"
        assert presenter._determine_recommendation_priority(essential_rec) == "high"

        # Medium priority keywords
        medium_rec = "You should consider this approach"
        assert presenter._determine_recommendation_priority(medium_rec) == "medium"

        important_rec = "This is important for success"
        assert presenter._determine_recommendation_priority(important_rec) == "medium"

        # Low priority (no keywords)
        low_rec = "This might be helpful"
        assert presenter._determine_recommendation_priority(low_rec) == "low"

    def test_categorize_recommendation(self):
        """Test recommendation categorization."""
        presenter = Presenter()

        # Risk management
        risk_rec = "Focus on risk management strategies"
        assert presenter._categorize_recommendation(risk_rec) == "risk_management"

        # Stakeholder management
        stakeholder_rec = "Improve stakeholder communication"
        assert presenter._categorize_recommendation(stakeholder_rec) == "stakeholder_management"

        # Project planning
        planning_rec = "Review your project schedule"
        assert presenter._categorize_recommendation(planning_rec) == "project_planning"

        # Quality management
        quality_rec = "Implement quality standards"
        assert presenter._categorize_recommendation(quality_rec) == "quality_management"

        # General
        general_rec = "This is a general recommendation"
        assert presenter._categorize_recommendation(general_rec) == "general"

    def test_format_text_content(self):
        """Test text content formatting."""
        presenter = Presenter()

        # Empty content
        empty_result = presenter._format_text_content("")
        assert empty_result["type"] == "empty"
        assert empty_result["content"] == ""

        # Plain text
        plain_text = "This is plain text without structure."
        plain_result = presenter._format_text_content(plain_text)
        assert plain_result["type"] == "plain"
        assert plain_result["content"] == plain_text
        assert plain_result["has_headers"] is False
        assert plain_result["has_lists"] is False
        assert plain_result["word_count"] == 7

        # Structured content with headers
        structured_text = "# Header\n\nContent with structure.\n\n## Subheader\n\n- List item"
        structured_result = presenter._format_text_content(structured_text)
        assert structured_result["type"] == "structured"
        assert structured_result["has_headers"] is True
        assert structured_result["has_lists"] is True

    def test_extract_sections_from_text(self):
        """Test section extraction from text."""
        presenter = Presenter()

        text_with_sections = """
# Main Header

Some content here.

## Section One

Content for section one.

## Section Two

Content for section two.

### Subsection

Subsection content.
"""

        sections = presenter._extract_sections_from_text(text_with_sections)

        assert len(sections) == 4
        assert "Main Header" in sections
        assert "Section One" in sections
        assert "Section Two" in sections
        assert "Subsection" in sections

    def test_extract_usage_notes(self):
        """Test usage notes extraction."""
        presenter = Presenter()

        content_with_notes = """
# Template

## Usage Instructions
Follow these steps to use the template.

## Note
This is an important note.

Some other content.

## Usage Guidelines
Additional usage information.
"""

        notes = presenter._extract_usage_notes(content_with_notes)

        assert len(notes) <= 3  # Limited to 3 notes
        assert any("usage" in note.lower() for note in notes)
        assert any("note" in note.lower() for note in notes)

    def test_extract_key_points(self):
        """Test key points extraction."""
        presenter = Presenter()

        content_with_points = """
# Example

This is an example with key points:

- First important point
- Second key consideration
- Third critical aspect

Some other content.

Key takeaway: This is important.

- Another bullet point
- Final point
"""

        key_points = presenter._extract_key_points(content_with_points)

        assert len(key_points) <= 5  # Limited to 5 points
        assert "First important point" in key_points
        assert "Second key consideration" in key_points
        assert any("key takeaway" in point.lower() for point in key_points)

    def test_get_quick_tips(self):
        """Test quick tips generation."""
        presenter = Presenter()

        tips = presenter._get_quick_tips()

        assert len(tips) == 8

        # Verify structure
        for tip in tips:
            assert "id" in tip
            assert "tip" in tip
            assert isinstance(tip["id"], int)
            assert isinstance(tip["tip"], str)
            assert len(tip["tip"]) > 10  # Reasonable length

        # Verify IDs are sequential
        ids = [tip["id"] for tip in tips]
        assert ids == list(range(1, 9))

    def test_get_additional_resources(self):
        """Test additional resources generation."""
        presenter = Presenter()

        resources = presenter._get_additional_resources()

        assert len(resources) == 4

        # Verify structure
        for resource in resources:
            assert "title" in resource
            assert "description" in resource
            assert "type" in resource
            assert "url" in resource
            assert resource["url"].startswith("https://")

        # Verify specific resources
        titles = [r["title"] for r in resources]
        assert "Project Management Institute (PMI)" in titles
        assert "PRINCE2 Methodology" in titles
        assert "Agile Alliance" in titles
        assert "Project Management Body of Knowledge (PMBOK)" in titles

    def test_format_topic_title(self):
        """Test topic title formatting."""
        presenter = Presenter()

        assert presenter._format_topic_title("risk_management") == "Risk Management"
        assert presenter._format_topic_title("stakeholder_analysis") == "Stakeholder Analysis"
        assert presenter._format_topic_title("simple") == "Simple"

    def test_create_overview_summary_variations(self):
        """Test overview summary creation with different scenarios."""
        presenter = Presenter()

        # All topics available
        all_available = [{"available": True}, {"available": True}]
        summary = presenter._create_overview_summary(all_available)
        assert "All 2 relevant learning topics have content available" in summary

        # Partial availability
        partial_available = [{"available": True}, {"available": False}]
        summary = presenter._create_overview_summary(partial_available)
        assert "1 of 2 relevant topics have detailed content available" in summary

        # None available
        none_available = [{"available": False}, {"available": False}]
        summary = presenter._create_overview_summary(none_available)
        assert "0 of 2 relevant topics have detailed content available" in summary

        # No topics
        no_topics = []
        summary = presenter._create_overview_summary(no_topics)
        assert "No specific learning topics identified" in summary

    def test_count_content_sections(self):
        """Test content sections counting."""
        presenter = Presenter()

        learning_content = {
            "topics": {"topic1": {}, "topic2": {}},
            "general_guidance": [{"title": "Guide 1"}],
            "templates": [{"name": "Template 1"}, {"name": "Template 2"}],
            "examples": [],
        }

        counts = presenter._count_content_sections(learning_content)

        assert counts["topics"] == 2
        assert counts["guidance"] == 1
        assert counts["templates"] == 2
        assert counts["examples"] == 0

    @patch("learning.presenter.datetime")
    def test_presentation_metadata_timestamp(self, mock_datetime):
        """Test that presentation metadata includes correct timestamp."""
        # Mock datetime
        mock_now = datetime(2024, 1, 8, 14, 30, 22)
        mock_datetime.now.return_value = mock_now

        presenter = Presenter()

        result = presenter.present_learning_content({}, [], [])

        metadata = result["presentation_metadata"]
        assert metadata["generated_at"] == "2024-01-08T14:30:22"
