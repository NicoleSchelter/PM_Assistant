"""
Tests for the ContentLoader class.

This module contains comprehensive tests for the ContentLoader class
that handles dynamic loading of learning content from markdown files.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from learning.content_loader import ContentLoader
from utils.exceptions import FileProcessingError


class TestContentLoader:
    """Test cases for ContentLoader class."""
    
    @pytest.fixture
    def temp_content_dir(self):
        """Create a temporary content directory with sample files."""
        temp_dir = tempfile.mkdtemp()
        content_path = Path(temp_dir) / "learning_content"
        content_path.mkdir()
        
        # Create sample topic files
        (content_path / "risk_management.md").write_text("""
# Risk Management

## Overview
Risk management is essential for project success.

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
""")
        
        (content_path / "stakeholder_analysis.md").write_text("""
# Stakeholder Analysis

## Overview
Understanding stakeholders is crucial for project success.

## Key Concepts
- Stakeholder identification
- Power-interest mapping
- Engagement strategies
""")
        
        # Create guidance file
        (content_path / "project_guidance.md").write_text("""
# Project Management Guidance

This is general project management guidance content.
""")
        
        # Create templates directory
        templates_dir = content_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "risk_register_template.md").write_text("""
# Risk Register Template

## Usage Notes
Use this template to track project risks.

| Risk ID | Description | Probability | Impact |
|---------|-------------|-------------|--------|
| R001    | Sample risk | High        | Medium |
""")
        
        # Create examples directory
        examples_dir = content_path / "examples"
        examples_dir.mkdir()
        (examples_dir / "project_charter_example.md").write_text("""
# Project Charter Example

## Key Points
- Clear objectives
- Defined scope
- Success criteria

This is an example of a well-structured project charter.
""")
        
        yield str(content_path)
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_initialization_default_paths(self):
        """Test ContentLoader initialization with default paths."""
        loader = ContentLoader()
        
        assert len(loader.base_paths) == 3
        assert "./learning/modules" in loader.base_paths
        assert "./content/learning" in loader.base_paths
        assert "./docs/learning" in loader.base_paths
        assert "topics" in loader.content_patterns
        assert "templates" in loader.content_patterns
        assert "examples" in loader.content_patterns
    
    def test_initialization_custom_paths(self):
        """Test ContentLoader initialization with custom paths."""
        custom_paths = ["/custom/path1", "/custom/path2"]
        loader = ContentLoader(custom_paths)
        
        assert loader.base_paths == custom_paths
    
    def test_load_content_success(self, temp_content_dir):
        """Test successful content loading from directory."""
        loader = ContentLoader()
        topics = ["risk_management", "stakeholder_analysis"]
        
        content = loader.load_content(temp_content_dir, topics)
        
        # Verify structure
        assert "topics" in content
        assert "general_guidance" in content
        assert "templates" in content
        assert "examples" in content
        
        # Verify topics loaded
        assert "risk_management" in content["topics"]
        assert "stakeholder_analysis" in content["topics"]
        
        # Verify topic content structure
        risk_content = content["topics"]["risk_management"]
        assert "overview" in risk_content
        assert "key_concepts" in risk_content
        assert "best_practices" in risk_content
        assert "common_pitfalls" in risk_content
        
        # Verify content values
        assert "Risk management is essential" in risk_content["overview"]
        assert len(risk_content["key_concepts"]) == 3
        assert "Risk identification" in risk_content["key_concepts"]
        
        # Verify guidance loaded
        assert len(content["general_guidance"]) >= 1
        guidance_titles = [g["title"] for g in content["general_guidance"]]
        assert any("guidance" in title.lower() for title in guidance_titles)
        
        # Verify templates loaded
        assert len(content["templates"]) >= 1
        template_names = [t["name"] for t in content["templates"]]
        assert any("template" in name.lower() for name in template_names)
        
        # Verify examples loaded
        assert len(content["examples"]) >= 1
        example_names = [e["name"] for e in content["examples"]]
        assert any("example" in name.lower() for name in example_names)
    
    def test_load_content_nonexistent_directory(self):
        """Test content loading with nonexistent directory."""
        loader = ContentLoader()
        topics = ["risk_management"]
        
        content = loader.load_content("/nonexistent/path", topics)
        
        # Should return fallback content
        assert "topics" in content
        assert "risk_management" in content["topics"]
        assert "general_guidance" in content
        assert len(content["general_guidance"]) >= 1
    
    def test_load_content_empty_directory(self):
        """Test content loading with empty directory."""
        temp_dir = tempfile.mkdtemp()
        try:
            loader = ContentLoader()
            topics = ["risk_management"]
            
            content = loader.load_content(temp_dir, topics)
            
            # Should return fallback content for missing topics
            assert "topics" in content
            assert "risk_management" in content["topics"]
            # Should have default content
            assert content["topics"]["risk_management"]["overview"]
        finally:
            shutil.rmtree(temp_dir)
    
    def test_parse_topic_content_comprehensive(self):
        """Test comprehensive topic content parsing."""
        loader = ContentLoader()
        
        markdown_content = """
# Topic Title

## Overview
This is the overview section with multiple lines.
It provides context and background information.

## Key Concepts
- First concept
- Second concept
- Third concept

## Best Practices
- Practice one
- Practice two

## Common Pitfalls
- Pitfall one
- Pitfall two

## Tools Techniques
- Tool one
- Tool two

## References
- Reference one
- Reference two
"""
        
        parsed = loader._parse_topic_content(markdown_content)
        
        # Verify all sections parsed
        assert "overview" in parsed
        assert "key_concepts" in parsed
        assert "best_practices" in parsed
        assert "common_pitfalls" in parsed
        assert "tools_techniques" in parsed
        assert "references" in parsed
        
        # Verify overview is text
        assert "This is the overview section" in parsed["overview"]
        assert "background information" in parsed["overview"]
        
        # Verify lists are parsed correctly
        assert len(parsed["key_concepts"]) == 3
        assert "First concept" in parsed["key_concepts"]
        assert "Third concept" in parsed["key_concepts"]
        
        assert len(parsed["best_practices"]) == 2
        assert "Practice one" in parsed["best_practices"]
        
        assert len(parsed["common_pitfalls"]) == 2
        assert len(parsed["tools_techniques"]) == 2
        assert len(parsed["references"]) == 2
    
    def test_parse_topic_content_minimal(self):
        """Test parsing minimal topic content."""
        loader = ContentLoader()
        
        minimal_content = """
# Simple Topic

Just some basic content without sections.
"""
        
        parsed = loader._parse_topic_content(minimal_content)
        
        # Should have overview with the content
        assert "overview" in parsed
        assert "Just some basic content" in parsed["overview"]
        
        # Other sections should be empty lists
        assert parsed["key_concepts"] == []
        assert parsed["best_practices"] == []
    
    def test_map_header_to_section(self):
        """Test header to section mapping."""
        loader = ContentLoader()
        
        # Test exact matches
        assert loader._map_header_to_section("overview") == "overview"
        assert loader._map_header_to_section("key_concepts") == "key_concepts"
        assert loader._map_header_to_section("best_practices") == "best_practices"
        
        # Test alternative names
        assert loader._map_header_to_section("concepts") == "key_concepts"
        assert loader._map_header_to_section("practices") == "best_practices"
        assert loader._map_header_to_section("pitfalls") == "common_pitfalls"
        assert loader._map_header_to_section("tools") == "tools_techniques"
        assert loader._map_header_to_section("resources") == "references"
        
        # Test unknown header
        assert loader._map_header_to_section("unknown_section") == "overview"
    
    def test_format_title(self):
        """Test title formatting."""
        loader = ContentLoader()
        
        assert loader._format_title("risk_management") == "Risk Management"
        assert loader._format_title("stakeholder-analysis") == "Stakeholder Analysis"
        assert loader._format_title("simple") == "Simple"
        assert loader._format_title("multi_word_title") == "Multi Word Title"
    
    def test_get_default_topic_content(self):
        """Test default topic content generation."""
        loader = ContentLoader()
        
        # Test known topics
        risk_content = loader._get_default_topic_content("risk_management")
        assert "overview" in risk_content
        assert "key_concepts" in risk_content
        assert "Risk management involves" in risk_content["overview"]
        assert len(risk_content["key_concepts"]) > 0
        
        stakeholder_content = loader._get_default_topic_content("stakeholder_analysis")
        assert "Stakeholder analysis focuses" in stakeholder_content["overview"]
        
        scheduling_content = loader._get_default_topic_content("scheduling")
        assert "Project scheduling involves" in scheduling_content["overview"]
        
        # Test unknown topic
        unknown_content = loader._get_default_topic_content("unknown_topic")
        assert "not available" in unknown_content["overview"]
        assert unknown_content["key_concepts"] == []
    
    def test_get_fallback_content(self):
        """Test fallback content generation."""
        loader = ContentLoader()
        topics = ["risk_management", "stakeholder_analysis"]
        
        fallback = loader._get_fallback_content(topics)
        
        # Verify structure
        assert "topics" in fallback
        assert "general_guidance" in fallback
        assert "templates" in fallback
        assert "examples" in fallback
        
        # Verify topics included
        assert "risk_management" in fallback["topics"]
        assert "stakeholder_analysis" in fallback["topics"]
        
        # Verify general guidance
        assert len(fallback["general_guidance"]) >= 1
        guidance = fallback["general_guidance"][0]
        assert "title" in guidance
        assert "content" in guidance
        assert "Project Management Fundamentals" in guidance["content"]
    
    def test_read_markdown_file_success(self, temp_content_dir):
        """Test successful markdown file reading."""
        loader = ContentLoader()
        file_path = Path(temp_content_dir) / "risk_management.md"
        
        content = loader._read_markdown_file(file_path)
        
        assert "Risk Management" in content
        assert "## Overview" in content
        assert "Risk management is essential" in content
    
    def test_read_markdown_file_not_found(self):
        """Test markdown file reading with nonexistent file."""
        loader = ContentLoader()
        file_path = Path("/nonexistent/file.md")
        
        with pytest.raises(FileProcessingError, match="Cannot read file"):
            loader._read_markdown_file(file_path)
    
    def test_load_topics_partial_success(self, temp_content_dir):
        """Test loading topics with some files missing."""
        loader = ContentLoader()
        topics = ["risk_management", "nonexistent_topic", "stakeholder_analysis"]
        
        topic_content = loader._load_topics(Path(temp_content_dir), topics)
        
        # Should have all requested topics
        assert len(topic_content) == 3
        assert "risk_management" in topic_content
        assert "nonexistent_topic" in topic_content
        assert "stakeholder_analysis" in topic_content
        
        # Existing topics should have real content
        assert "Risk management is essential" in topic_content["risk_management"]["overview"]
        assert "Understanding stakeholders" in topic_content["stakeholder_analysis"]["overview"]
        
        # Missing topic should have default content
        assert "not available" in topic_content["nonexistent_topic"]["overview"]
    
    def test_load_general_guidance_multiple_files(self, temp_content_dir):
        """Test loading multiple guidance files."""
        # Create additional guidance files
        content_path = Path(temp_content_dir)
        (content_path / "best_practices.md").write_text("# Best Practices\nGeneral best practices content.")
        (content_path / "tips_and_tricks.md").write_text("# Tips\nUseful tips content.")
        
        loader = ContentLoader()
        guidance = loader._load_general_guidance(content_path)
        
        # Should find multiple guidance files
        assert len(guidance) >= 2
        
        # Verify content structure
        for item in guidance:
            assert "title" in item
            assert "content" in item
            assert len(item["content"]) > 0
    
    def test_load_templates_and_examples(self, temp_content_dir):
        """Test loading templates and examples."""
        loader = ContentLoader()
        content_path = Path(temp_content_dir)
        
        templates = loader._load_templates(content_path)
        examples = loader._load_examples(content_path)
        
        # Verify templates
        assert len(templates) >= 1
        template = templates[0]
        assert "name" in template
        assert "content" in template
        assert "template" in template["name"].lower()
        
        # Verify examples
        assert len(examples) >= 1
        example = examples[0]
        assert "name" in example
        assert "content" in example
        assert "example" in example["name"].lower()
    
    def test_save_section_content(self):
        """Test section content saving."""
        loader = ContentLoader()
        parsed = {"overview": "", "key_concepts": [], "best_practices": []}
        
        # Test overview (text) section
        loader._save_section_content(parsed, "overview", ["Line 1", "Line 2"])
        assert parsed["overview"] == "Line 1\nLine 2"
        
        # Test list section
        loader._save_section_content(parsed, "key_concepts", ["Concept 1", "Concept 2"])
        assert parsed["key_concepts"] == ["Concept 1", "Concept 2"]
    
    @patch('learning.content_loader.logger')
    def test_error_handling_and_logging(self, mock_logger, temp_content_dir):
        """Test error handling and logging behavior."""
        loader = ContentLoader()
        
        # Test with corrupted file (create a file that will cause parsing issues)
        content_path = Path(temp_content_dir)
        corrupted_file = content_path / "corrupted.md"
        
        # Create file with permission issues (simulate by mocking)
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            topics = ["corrupted"]
            content = loader.load_content(str(content_path), topics)
            
            # Should still return content (fallback)
            assert "topics" in content
            assert "corrupted" in content["topics"]
            
            # Should have logged warnings
            mock_logger.warning.assert_called()
    
    def test_content_patterns_configuration(self):
        """Test content patterns configuration."""
        loader = ContentLoader()
        
        patterns = loader.content_patterns
        assert "topics" in patterns
        assert "templates" in patterns
        assert "examples" in patterns
        assert "guidance" in patterns
        
        # Verify pattern formats
        assert patterns["topics"] == "*.md"
        assert patterns["templates"] == "templates/*.md"
        assert patterns["examples"] == "examples/*.md"
        assert "*guidance*" in patterns["guidance"]