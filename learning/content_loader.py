"""
Content Loader for PM Analysis Tool Learning System.

This module implements the ContentLoader class that dynamically loads
learning content from markdown files and other sources.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import re

from utils.logger import get_logger
from utils.exceptions import FileProcessingError

logger = get_logger(__name__)


class ContentLoader:
    """
    Dynamic content loader for learning modules.
    
    This class handles loading and parsing of learning content from
    various sources including markdown files, templates, and examples.
    """
    
    def __init__(self, base_paths: Optional[List[str]] = None):
        """
        Initialize the content loader.
        
        Args:
            base_paths: List of base paths to search for content
        """
        self.base_paths = base_paths or [
            "./learning/modules",
            "./content/learning", 
            "./docs/learning"
        ]
        
        # Content type patterns
        self.content_patterns = {
            "topics": "*.md",
            "templates": "templates/*.md",
            "examples": "examples/*.md",
            "guidance": "*guidance*.md"
        }
    
    def load_content(self, content_path: str, topics: List[str]) -> Dict[str, Any]:
        """
        Load learning content from specified path.
        
        Args:
            content_path: Path to content directory
            topics: List of topics to load
            
        Returns:
            Dictionary containing loaded content
        """
        logger.info(f"Loading learning content from: {content_path}")
        
        content_dir = Path(content_path)
        
        if not content_dir.exists() or not content_dir.is_dir():
            logger.warning(f"Content directory not found: {content_path}")
            return self._get_fallback_content(topics)
        
        try:
            content = {
                "topics": self._load_topics(content_dir, topics),
                "general_guidance": self._load_general_guidance(content_dir),
                "templates": self._load_templates(content_dir),
                "examples": self._load_examples(content_dir)
            }
            
            logger.info(f"Successfully loaded content for {len(content['topics'])} topics")
            return content
            
        except Exception as e:
            logger.error(f"Error loading content from {content_path}: {e}")
            return self._get_fallback_content(topics)
    
    def _load_topics(self, content_dir: Path, topics: List[str]) -> Dict[str, Any]:
        """
        Load topic-specific content from markdown files.
        
        Args:
            content_dir: Content directory path
            topics: List of topics to load
            
        Returns:
            Dictionary of topic content
        """
        topic_content = {}
        
        for topic in topics:
            topic_file = content_dir / f"{topic}.md"
            if topic_file.exists():
                try:
                    content = self._read_markdown_file(topic_file)
                    topic_content[topic] = self._parse_topic_content(content)
                    logger.debug(f"Loaded content for topic: {topic}")
                except Exception as e:
                    logger.warning(f"Failed to load topic {topic}: {e}")
                    topic_content[topic] = self._get_default_topic_content(topic)
            else:
                logger.debug(f"Topic file not found: {topic_file}")
                topic_content[topic] = self._get_default_topic_content(topic)
        
        return topic_content
    
    def _load_general_guidance(self, content_dir: Path) -> List[Dict[str, str]]:
        """
        Load general guidance files.
        
        Args:
            content_dir: Content directory path
            
        Returns:
            List of guidance content
        """
        guidance_content = []
        
        # Look for guidance files
        guidance_patterns = ["*guidance*", "*best*practice*", "*tip*"]
        
        for pattern in guidance_patterns:
            for guidance_file in content_dir.glob(pattern + ".md"):
                try:
                    content = self._read_markdown_file(guidance_file)
                    guidance_content.append({
                        "title": self._format_title(guidance_file.stem),
                        "content": content
                    })
                    logger.debug(f"Loaded guidance: {guidance_file.name}")
                except Exception as e:
                    logger.warning(f"Failed to load guidance file {guidance_file}: {e}")
        
        return guidance_content
    
    def _load_templates(self, content_dir: Path) -> List[Dict[str, str]]:
        """
        Load template files.
        
        Args:
            content_dir: Content directory path
            
        Returns:
            List of template content
        """
        templates = []
        
        template_dir = content_dir / "templates"
        if template_dir.exists() and template_dir.is_dir():
            for template_file in template_dir.glob("*.md"):
                try:
                    content = self._read_markdown_file(template_file)
                    templates.append({
                        "name": self._format_title(template_file.stem),
                        "content": content
                    })
                    logger.debug(f"Loaded template: {template_file.name}")
                except Exception as e:
                    logger.warning(f"Failed to load template {template_file}: {e}")
        
        return templates
    
    def _load_examples(self, content_dir: Path) -> List[Dict[str, str]]:
        """
        Load example files.
        
        Args:
            content_dir: Content directory path
            
        Returns:
            List of example content
        """
        examples = []
        
        examples_dir = content_dir / "examples"
        if examples_dir.exists() and examples_dir.is_dir():
            for example_file in examples_dir.glob("*.md"):
                try:
                    content = self._read_markdown_file(example_file)
                    examples.append({
                        "name": self._format_title(example_file.stem),
                        "content": content
                    })
                    logger.debug(f"Loaded example: {example_file.name}")
                except Exception as e:
                    logger.warning(f"Failed to load example {example_file}: {e}")
        
        return examples
    
    def _read_markdown_file(self, file_path: Path) -> str:
        """
        Read content from a markdown file.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            File content as string
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise FileProcessingError(f"Cannot read file {file_path}: {e}")
    
    def _parse_topic_content(self, content: str) -> Dict[str, Any]:
        """
        Parse topic content from markdown text.
        
        Args:
            content: Raw markdown content
            
        Returns:
            Parsed content structure
        """
        parsed = {
            "overview": "",
            "key_concepts": [],
            "best_practices": [],
            "common_pitfalls": [],
            "tools_techniques": [],
            "references": []
        }
        
        # Simple parsing based on markdown headers
        current_section = "overview"
        current_content = []
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            
            # Check for section headers
            if line.startswith('## '):
                # Save previous section
                if current_content:
                    self._save_section_content(parsed, current_section, current_content)
                
                # Start new section
                header = line[3:].lower().replace(' ', '_').replace('-', '_')
                current_section = self._map_header_to_section(header)
                current_content = []
            
            elif line.startswith('- ') or line.startswith('* '):
                # List item
                current_content.append(line[2:])
            
            elif line and not line.startswith('#'):
                # Regular content
                current_content.append(line)
        
        # Save final section
        if current_content:
            self._save_section_content(parsed, current_section, current_content)
        
        return parsed
    
    def _save_section_content(self, parsed: Dict[str, Any], section: str, content: List[str]):
        """
        Save section content to the parsed structure.
        
        Args:
            parsed: Parsed content dictionary
            section: Section name
            content: Content lines
        """
        if section == "overview":
            parsed[section] = '\n'.join(content)
        else:
            parsed[section] = content
    
    def _map_header_to_section(self, header: str) -> str:
        """
        Map markdown header to content section.
        
        Args:
            header: Header text
            
        Returns:
            Section name
        """
        header_mapping = {
            "overview": "overview",
            "key_concepts": "key_concepts",
            "concepts": "key_concepts",
            "best_practices": "best_practices",
            "practices": "best_practices",
            "common_pitfalls": "common_pitfalls",
            "pitfalls": "common_pitfalls",
            "tools_techniques": "tools_techniques",
            "tools": "tools_techniques",
            "techniques": "tools_techniques",
            "references": "references",
            "resources": "references"
        }
        
        return header_mapping.get(header, "overview")
    
    def _format_title(self, filename: str) -> str:
        """
        Format filename to readable title.
        
        Args:
            filename: File name without extension
            
        Returns:
            Formatted title
        """
        return filename.replace("_", " ").replace("-", " ").title()
    
    def _get_fallback_content(self, topics: List[str]) -> Dict[str, Any]:
        """
        Get fallback content when files cannot be loaded.
        
        Args:
            topics: List of topics
            
        Returns:
            Fallback content structure
        """
        logger.info("Using fallback content")
        
        fallback_content = {
            "topics": {},
            "general_guidance": [
                {
                    "title": "Project Management Fundamentals",
                    "content": self._get_pm_fundamentals_content()
                }
            ],
            "templates": [],
            "examples": []
        }
        
        # Generate fallback content for each topic
        for topic in topics:
            fallback_content["topics"][topic] = self._get_default_topic_content(topic)
        
        return fallback_content
    
    def _get_default_topic_content(self, topic: str) -> Dict[str, Any]:
        """
        Get default content for a specific topic.
        
        Args:
            topic: Topic key
            
        Returns:
            Default content structure for the topic
        """
        topic_content_map = {
            "risk_management": {
                "overview": "Risk management involves identifying, analyzing, and responding to project risks throughout the project lifecycle.",
                "key_concepts": [
                    "Risk identification and assessment",
                    "Probability and impact analysis", 
                    "Risk response strategies (avoid, mitigate, transfer, accept)",
                    "Risk monitoring and control"
                ],
                "best_practices": [
                    "Conduct regular risk assessments",
                    "Maintain a comprehensive risk register",
                    "Involve stakeholders in risk identification",
                    "Develop contingency plans for high-priority risks"
                ],
                "common_pitfalls": [
                    "Ignoring low-probability, high-impact risks",
                    "Failing to update risk assessments regularly",
                    "Not communicating risks to stakeholders"
                ]
            },
            "stakeholder_analysis": {
                "overview": "Stakeholder analysis focuses on identifying, analyzing, and engaging project stakeholders effectively.",
                "key_concepts": [
                    "Stakeholder identification and analysis",
                    "Influence and interest mapping",
                    "Communication planning",
                    "Engagement strategies"
                ],
                "best_practices": [
                    "Create a comprehensive stakeholder register",
                    "Regularly assess stakeholder influence and interest",
                    "Develop tailored communication strategies",
                    "Monitor stakeholder engagement levels"
                ],
                "common_pitfalls": [
                    "Overlooking internal stakeholders",
                    "One-size-fits-all communication approach",
                    "Failing to manage stakeholder expectations"
                ]
            },
            "scheduling": {
                "overview": "Project scheduling involves creating and managing project timelines, dependencies, and resource allocation.",
                "key_concepts": [
                    "Work breakdown structure (WBS)",
                    "Activity sequencing and dependencies",
                    "Duration estimation",
                    "Critical path method (CPM)"
                ],
                "best_practices": [
                    "Create detailed work breakdown structures",
                    "Identify and manage critical path activities",
                    "Build in buffer time for uncertainties",
                    "Regularly update and monitor schedules"
                ],
                "common_pitfalls": [
                    "Overly optimistic time estimates",
                    "Ignoring resource constraints",
                    "Poor dependency management"
                ]
            }
        }
        
        return topic_content_map.get(topic, {
            "overview": f"Content for {topic.replace('_', ' ').title()} is not available.",
            "key_concepts": [],
            "best_practices": [],
            "common_pitfalls": []
        })
    
    def _get_pm_fundamentals_content(self) -> str:
        """Get fundamental project management guidance content."""
        return """
# Project Management Fundamentals

Project management is the application of knowledge, skills, tools, and techniques to project activities to meet project requirements.

## Key Areas of Focus:

1. **Integration Management**: Coordinating all aspects of the project
2. **Scope Management**: Defining and controlling what is included in the project
3. **Schedule Management**: Planning and controlling project timelines
4. **Cost Management**: Planning and controlling project budget
5. **Quality Management**: Ensuring project deliverables meet requirements
6. **Resource Management**: Managing project team and resources
7. **Communications Management**: Ensuring effective information flow
8. **Risk Management**: Identifying and managing project uncertainties
9. **Procurement Management**: Managing external suppliers and contracts
10. **Stakeholder Management**: Engaging and managing stakeholder expectations

## Success Factors:

- Clear project objectives and success criteria
- Strong stakeholder engagement and communication
- Effective risk management
- Regular monitoring and control
- Adaptive leadership and team management
"""