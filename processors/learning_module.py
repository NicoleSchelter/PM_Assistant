"""
Learning Module Processor for PM Analysis Tool.

This module implements the LearningModuleProcessor class that provides
project management best practices and guidance through dynamic content loading.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import time
import re

from processors.base_processor import BaseProcessor
from core.models import FileInfo, ProcessingResult
from file_handlers.markdown_handler import MarkdownHandler
from learning.content_loader import ContentLoader
from learning.presenter import Presenter
from utils.logger import get_logger
from utils.exceptions import FileProcessingError

logger = get_logger(__name__)


class LearningModuleProcessor(BaseProcessor):
    """
    Processor for delivering project management learning content.
    
    This processor loads and presents PM best practices, guidance, and
    educational content from markdown files in a user-friendly format.
    """
    
    def __init__(self):
        """Initialize the Learning Module processor."""
        super().__init__()
        self.processor_name = "Learning Module Processor"
        
        # Learning module doesn't require specific files - it provides content
        self.required_files = []
        
        # Optional files that can enhance learning content
        self.optional_files = [
            "*learning*",
            "*guide*",
            "*best*practice*",
            "*template*",
            "*example*"
        ]
        
        # Initialize markdown handler for content processing
        self.markdown_handler = MarkdownHandler()
        
        # Initialize content loader and presenter
        self.content_loader = ContentLoader()
        self.presenter = Presenter()
        
        # Default learning content paths
        self.default_content_paths = [
            "./learning/modules",
            "./content/learning",
            "./docs/learning"
        ]
        
        # Learning module categories
        self.learning_categories = {
            "risk_management": "Risk Management Best Practices",
            "stakeholder_management": "Stakeholder Engagement Strategies", 
            "project_planning": "Project Planning Fundamentals",
            "quality_management": "Quality Assurance Guidelines",
            "communication": "Communication Management",
            "change_management": "Change Control Processes",
            "resource_management": "Resource Planning and Management",
            "schedule_management": "Schedule Development and Control"
        }
    
    def validate_inputs(self, files: List[FileInfo]) -> bool:
        """
        Validate inputs for learning module processing.
        
        Learning module can operate without any specific input files
        as it provides educational content from predefined sources.
        
        Args:
            files: List of available files (not required for learning module)
            
        Returns:
            Always True - learning module can always provide content
        """
        # Learning module can always provide content regardless of input files
        return True
    
    def process(self, files: List[FileInfo], config: Dict[str, Any]) -> ProcessingResult:
        """
        Process learning module request to provide PM guidance and best practices.
        
        Args:
            files: List of files (used to determine relevant learning content)
            config: Configuration dictionary
            
        Returns:
            ProcessingResult with learning content and guidance
        """
        start_time = time.time()
        
        try:
            logger.info("Starting learning module content generation")
            
            # Get learning content configuration
            learning_config = config.get("modes", {}).get("learning_module", {})
            content_path = learning_config.get("content_path", self.default_content_paths[0])
            
            # Determine relevant learning topics based on available files
            relevant_topics = self._identify_relevant_topics(files)
            
            # Load learning content
            learning_content = self._load_learning_content(content_path, relevant_topics)
            
            # Generate personalized recommendations
            recommendations = self._generate_learning_recommendations(files, relevant_topics)
            
            # Format content for presentation
            formatted_content = self._format_learning_content(
                learning_content, 
                recommendations,
                relevant_topics
            )
            
            # Wrap in expected structure for compatibility
            result_data = {
                "learning_content": formatted_content,
                "recommendations": recommendations,
                "relevant_topics": relevant_topics
            }
            
            processing_time = time.time() - start_time
            logger.info(f"Learning module content generated in {processing_time:.2f} seconds")
            
            return ProcessingResult(
                success=True,
                operation="learning_module",
                data=result_data,
                processing_time_seconds=processing_time
            )
            
        except Exception as e:
            error_msg = f"Learning module processing failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            return ProcessingResult(
                success=False,
                operation="learning_module",
                errors=[error_msg],
                processing_time_seconds=time.time() - start_time
            )
    
    def _identify_relevant_topics(self, files: List[FileInfo]) -> List[str]:
        """
        Identify relevant learning topics based on available project files.
        
        Args:
            files: List of available project files
            
        Returns:
            List of relevant learning topic keys
        """
        relevant_topics = []
        
        if not files:
            # If no files, provide general project management topics
            return ["project_planning", "risk_management", "stakeholder_management"]
        
        # Analyze file names and types to determine relevant topics
        file_keywords = []
        for file_info in files:
            filename_lower = file_info.filename.lower()
            file_keywords.extend(filename_lower.split())
        
        # Map keywords to learning topics
        keyword_topic_mapping = {
            "risk": "risk_management",
            "stakeholder": "stakeholder_management", 
            "wbs": "project_planning",
            "schedule": "schedule_management",
            "roadmap": "project_planning",
            "quality": "quality_management",
            "communication": "communication",
            "change": "change_management",
            "resource": "resource_management",
            "budget": "resource_management"
        }
        
        # Identify topics based on file content
        for keyword, topic in keyword_topic_mapping.items():
            if any(keyword in file_keyword for file_keyword in file_keywords):
                if topic not in relevant_topics:
                    relevant_topics.append(topic)
        
        # Always include project planning as a fundamental topic
        if "project_planning" not in relevant_topics:
            relevant_topics.insert(0, "project_planning")
        
        # Limit to top 5 most relevant topics
        return relevant_topics[:5]
    
    def _load_learning_content(self, content_path: str, relevant_topics: List[str]) -> Dict[str, Any]:
        """
        Load learning content from markdown files using ContentLoader.
        
        Args:
            content_path: Path to learning content directory
            relevant_topics: List of relevant topic keys
            
        Returns:
            Dictionary containing loaded learning content
        """
        return self.content_loader.load_content(content_path, relevant_topics)
    
    def _load_content_from_directory(self, content_dir: Path, relevant_topics: List[str]) -> Dict[str, Any]:
        """
        Load learning content from a directory of markdown files.
        
        Args:
            content_dir: Path to content directory
            relevant_topics: List of relevant topics
            
        Returns:
            Dictionary with loaded content
        """
        content = {
            "topics": {},
            "general_guidance": [],
            "templates": [],
            "examples": []
        }
        
        try:
            # Load topic-specific content
            for topic in relevant_topics:
                topic_file = content_dir / f"{topic}.md"
                if topic_file.exists():
                    try:
                        topic_content = self._read_markdown_file(str(topic_file))
                        content["topics"][topic] = self._parse_topic_content(topic_content)
                        logger.debug(f"Loaded learning content for topic: {topic}")
                    except Exception as e:
                        logger.warning(f"Failed to load content for topic {topic}: {e}")
            
            # Load general guidance files
            guidance_patterns = ["*guidance*", "*best*practice*", "*tip*"]
            for pattern in guidance_patterns:
                for guidance_file in content_dir.glob(pattern + ".md"):
                    try:
                        guidance_content = self._read_markdown_file(str(guidance_file))
                        content["general_guidance"].append({
                            "title": guidance_file.stem.replace("_", " ").title(),
                            "content": guidance_content
                        })
                    except Exception as e:
                        logger.warning(f"Failed to load guidance file {guidance_file}: {e}")
            
            # Load templates
            template_dir = content_dir / "templates"
            if template_dir.exists():
                for template_file in template_dir.glob("*.md"):
                    try:
                        template_content = self._read_markdown_file(str(template_file))
                        content["templates"].append({
                            "name": template_file.stem.replace("_", " ").title(),
                            "content": template_content
                        })
                    except Exception as e:
                        logger.warning(f"Failed to load template {template_file}: {e}")
            
            # Load examples
            examples_dir = content_dir / "examples"
            if examples_dir.exists():
                for example_file in examples_dir.glob("*.md"):
                    try:
                        example_content = self._read_markdown_file(str(example_file))
                        content["examples"].append({
                            "name": example_file.stem.replace("_", " ").title(),
                            "content": example_content
                        })
                    except Exception as e:
                        logger.warning(f"Failed to load example {example_file}: {e}")
        
        except Exception as e:
            logger.error(f"Error loading content from directory {content_dir}: {e}")
        
        return content
    
    def read_file(self, file_path: str) -> str:
        """
        Read file content - can be mocked in tests.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File content as string
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _read_markdown_file(self, file_path: str) -> str:
        """
        Read markdown file content using available handler methods.
        
        This method tries different approaches to read the file content,
        making it robust against different handler interfaces.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            Raw content string
        """
        try:
            # Try read_file method first (if it exists)
            if hasattr(self.markdown_handler, 'read_file'):
                return self.markdown_handler.read_file(file_path)
            
            # Fall back to extract_data method
            elif hasattr(self.markdown_handler, 'extract_data'):
                structured_data = self.markdown_handler.extract_data(file_path)
                return self._extract_raw_content(structured_data)
            
            # Last resort: read file directly using our own method
            else:
                return self.read_file(file_path)
                    
        except Exception as e:
            logger.warning(f"Failed to read markdown file {file_path}: {e}")
            # Return empty content rather than failing
            return ""
    
    def _extract_raw_content(self, structured_data: Dict[str, Any]) -> str:
        """
        Extract raw content from structured markdown data.
        
        Args:
            structured_data: Structured data from markdown handler
            
        Returns:
            Raw content string
        """
        # Try to reconstruct content from structured data
        content_parts = []
        
        # Add title if available
        if "title" in structured_data:
            content_parts.append(f"# {structured_data['title']}")
        
        # Add sections
        if "sections" in structured_data:
            for section in structured_data["sections"]:
                if isinstance(section, dict):
                    if "title" in section:
                        content_parts.append(f"## {section['title']}")
                    if "content" in section:
                        content_parts.append(section["content"])
                else:
                    content_parts.append(str(section))
        
        # Add any raw content if available
        if "content" in structured_data:
            content_parts.append(structured_data["content"])
        
        # If no structured content, try to get raw text
        if not content_parts and "raw_content" in structured_data:
            content_parts.append(structured_data["raw_content"])
        
        # Fallback: convert entire structure to string
        if not content_parts:
            content_parts.append(str(structured_data))
        
        return "\n\n".join(content_parts)
    
    def read_file(self, file_path: str) -> str:
        """
        Read content from a file using the markdown handler.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            Raw content string
        """
        try:
            structured_data = self.markdown_handler.extract_data(file_path)
            return self._extract_raw_content(structured_data)
        except Exception as e:
            logger.warning(f"Failed to read file {file_path}: {e}")
            # Fallback to direct file reading
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as read_error:
                logger.error(f"Failed to read file directly {file_path}: {read_error}")
                raise FileProcessingError(f"Cannot read file {file_path}: {read_error}")
    
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
                    if current_section == "overview":
                        parsed[current_section] = '\n'.join(current_content)
                    else:
                        parsed[current_section] = current_content
                
                # Start new section
                header = line[3:].lower().replace(' ', '_')
                if header in parsed:
                    current_section = header
                else:
                    current_section = "overview"
                current_content = []
            
            elif line.startswith('- ') or line.startswith('* '):
                # List item
                current_content.append(line[2:])
            
            elif line and not line.startswith('#'):
                # Regular content
                current_content.append(line)
        
        # Save final section
        if current_content:
            if current_section == "overview":
                parsed[current_section] = '\n'.join(current_content)
            else:
                parsed[current_section] = current_content
        
        return parsed
    
    def _get_default_learning_content(self, relevant_topics: List[str]) -> Dict[str, Any]:
        """
        Get default learning content when no external content is available.
        
        Args:
            relevant_topics: List of relevant topics
            
        Returns:
            Dictionary with default learning content
        """
        default_content = {
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
        
        # Generate default content for each relevant topic
        for topic in relevant_topics:
            if topic in self.learning_categories:
                default_content["topics"][topic] = self._get_default_topic_content(topic)
        
        return default_content
    
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
            "stakeholder_management": {
                "overview": "Stakeholder management focuses on identifying, analyzing, and engaging project stakeholders effectively.",
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
            "project_planning": {
                "overview": "Project planning involves defining project scope, creating work breakdown structures, and developing schedules.",
                "key_concepts": [
                    "Scope definition and management",
                    "Work breakdown structure (WBS)",
                    "Schedule development",
                    "Resource planning"
                ],
                "best_practices": [
                    "Define clear project objectives and success criteria",
                    "Create detailed work breakdown structures",
                    "Involve team members in planning activities",
                    "Establish realistic timelines and milestones"
                ],
                "common_pitfalls": [
                    "Inadequate scope definition",
                    "Overly optimistic scheduling",
                    "Insufficient resource planning"
                ]
            }
        }
        
        return topic_content_map.get(topic, {
            "overview": f"Content for {self.learning_categories.get(topic, topic)} is not available.",
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
    
    def _generate_learning_recommendations(self, files: List[FileInfo], relevant_topics: List[str]) -> List[str]:
        """
        Generate personalized learning recommendations based on project context.
        
        Args:
            files: Available project files
            relevant_topics: Identified relevant topics
            
        Returns:
            List of learning recommendations
        """
        recommendations = []
        
        # Analyze project maturity based on available documents
        document_types = {f.document_type.value for f in files}
        
        # Basic recommendations based on missing documents
        if "charter" not in str(document_types):
            recommendations.append(
                "Consider learning about project charter development - "
                "it's fundamental for project success and stakeholder alignment"
            )
        
        if "risk_register" not in str(document_types):
            recommendations.append(
                "Focus on risk management practices - "
                "proactive risk identification and mitigation are crucial"
            )
        
        if "stakeholder_register" not in str(document_types):
            recommendations.append(
                "Study stakeholder management techniques - "
                "effective stakeholder engagement drives project success"
            )
        
        # Topic-specific recommendations
        if "risk_management" in relevant_topics:
            recommendations.append(
                "Review risk response strategies and learn about quantitative risk analysis techniques"
            )
        
        if "stakeholder_management" in relevant_topics:
            recommendations.append(
                "Explore stakeholder engagement strategies and communication planning methods"
            )
        
        if "project_planning" in relevant_topics:
            recommendations.append(
                "Study advanced scheduling techniques and resource optimization methods"
            )
        
        # General recommendations
        recommendations.extend([
            "Practice using project management tools and templates",
            "Learn from case studies and real-world project examples",
            "Stay updated with industry best practices and standards (PMI, PRINCE2, Agile)"
        ])
        
        return recommendations[:8]  # Limit to top 8 recommendations
    
    def _format_learning_content(self, learning_content: Dict[str, Any], 
                                recommendations: List[str], 
                                relevant_topics: List[str]) -> Dict[str, Any]:
        """
        Format learning content for user-friendly presentation using Presenter.
        
        Args:
            learning_content: Raw learning content
            recommendations: Learning recommendations
            relevant_topics: Relevant topic keys
            
        Returns:
            Formatted content structure
        """
        return self.presenter.present_learning_content(learning_content, recommendations, relevant_topics)
    
    def _get_quick_tips(self) -> List[str]:
        """Get quick project management tips."""
        return [
            "Always define clear success criteria before starting any project",
            "Communicate early and often with all stakeholders",
            "Document decisions and assumptions to avoid confusion later",
            "Plan for risks - they will happen, be prepared",
            "Regular team check-ins prevent small issues from becoming big problems",
            "Keep project documentation simple and accessible",
            "Celebrate milestones and acknowledge team contributions",
            "Learn from every project - conduct retrospectives"
        ]
    
    def _get_additional_resources(self) -> List[Dict[str, str]]:
        """Get additional learning resources."""
        return [
            {
                "title": "Project Management Institute (PMI)",
                "description": "Professional organization with standards, certifications, and resources",
                "type": "Organization"
            },
            {
                "title": "PRINCE2 Methodology",
                "description": "Structured project management method with defined processes",
                "type": "Methodology"
            },
            {
                "title": "Agile Project Management",
                "description": "Iterative approach focusing on collaboration and adaptability",
                "type": "Methodology"
            },
            {
                "title": "Project Management Templates",
                "description": "Ready-to-use templates for common project documents",
                "type": "Tools"
            }
        ]