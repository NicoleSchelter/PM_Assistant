"""
Presenter for PM Analysis Tool Learning System.

This module implements the Presenter class that formats and displays
learning content in a user-friendly manner.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from utils.logger import get_logger

logger = get_logger(__name__)


class Presenter:
    """
    Learning content presenter for user-friendly display.
    
    This class handles formatting and presentation of learning content
    including topics, guidance, templates, and recommendations.
    """
    
    def __init__(self):
        """Initialize the presenter."""
        self.learning_categories = {
            "risk_management": "Risk Management Best Practices",
            "stakeholder_analysis": "Stakeholder Analysis Strategies", 
            "scheduling": "Project Scheduling Fundamentals",
            "project_planning": "Project Planning Fundamentals",
            "quality_management": "Quality Assurance Guidelines",
            "communication": "Communication Management",
            "change_management": "Change Control Processes",
            "resource_management": "Resource Planning and Management"
        }
    
    def present_learning_content(self, learning_content: Dict[str, Any], 
                                recommendations: List[str],
                                relevant_topics: List[str]) -> Dict[str, Any]:
        """
        Present learning content in a user-friendly format.
        
        Args:
            learning_content: Raw learning content
            recommendations: Learning recommendations
            relevant_topics: Relevant topic keys
            
        Returns:
            Formatted presentation structure
        """
        logger.info("Formatting learning content for presentation")
        
        presentation = {
            "learning_overview": self._create_learning_overview(learning_content, relevant_topics),
            "topic_content": self._format_topic_content(learning_content.get("topics", {})),
            "general_guidance": self._format_general_guidance(learning_content.get("general_guidance", [])),
            "templates": self._format_templates(learning_content.get("templates", [])),
            "examples": self._format_examples(learning_content.get("examples", [])),
            "personalized_recommendations": self._format_recommendations(recommendations),
            "quick_tips": self._get_quick_tips(),
            "additional_resources": self._get_additional_resources(),
            "presentation_metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_topics": len(relevant_topics),
                "content_sections": self._count_content_sections(learning_content)
            }
        }
        
        logger.info(f"Formatted presentation with {len(relevant_topics)} topics")
        return presentation
    
    def _create_learning_overview(self, learning_content: Dict[str, Any], 
                                 relevant_topics: List[str]) -> Dict[str, Any]:
        """
        Create learning overview section.
        
        Args:
            learning_content: Raw learning content
            relevant_topics: Relevant topic keys
            
        Returns:
            Learning overview structure
        """
        topics_info = []
        available_topics = learning_content.get("topics", {})
        
        for topic in relevant_topics:
            topic_info = {
                "key": topic,
                "title": self.learning_categories.get(topic, self._format_topic_title(topic)),
                "available": topic in available_topics,
                "content_sections": 0
            }
            
            # Count content sections for this topic
            if topic in available_topics:
                topic_content = available_topics[topic]
                topic_info["content_sections"] = sum(1 for section in topic_content.values() 
                                                   if section and (isinstance(section, str) and section.strip() or 
                                                                 isinstance(section, list) and section))
            
            topics_info.append(topic_info)
        
        return {
            "relevant_topics": topics_info,
            "total_topics": len(relevant_topics),
            "content_sources": (len(learning_content.get("general_guidance", [])) + 
                              len(learning_content.get("topics", {})) +
                              len(learning_content.get("templates", [])) +
                              len(learning_content.get("examples", []))),
            "summary": self._create_overview_summary(topics_info)
        }
    
    def _format_topic_content(self, topics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format topic content for presentation.
        
        Args:
            topics: Raw topic content
            
        Returns:
            Formatted topic content
        """
        formatted_topics = {}
        
        for topic_key, topic_content in topics.items():
            formatted_topics[topic_key] = {
                "title": self.learning_categories.get(topic_key, self._format_topic_title(topic_key)),
                "content": self._format_single_topic_content(topic_content),
                "sections": self._get_topic_sections(topic_content)
            }
        
        return formatted_topics
    
    def _format_single_topic_content(self, topic_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format content for a single topic.
        
        Args:
            topic_content: Raw topic content
            
        Returns:
            Formatted topic content
        """
        formatted = {}
        
        # Format each section
        for section_key, section_content in topic_content.items():
            if section_content:  # Only include non-empty sections
                if isinstance(section_content, str):
                    formatted[section_key] = {
                        "type": "text",
                        "content": section_content.strip()
                    }
                elif isinstance(section_content, list) and section_content:
                    formatted[section_key] = {
                        "type": "list",
                        "items": [item.strip() for item in section_content if item.strip()]
                    }
        
        return formatted
    
    def _get_topic_sections(self, topic_content: Dict[str, Any]) -> List[str]:
        """
        Get list of available sections for a topic.
        
        Args:
            topic_content: Topic content
            
        Returns:
            List of section names
        """
        sections = []
        section_order = ["overview", "key_concepts", "best_practices", "common_pitfalls", 
                        "tools_techniques", "references"]
        
        for section in section_order:
            if section in topic_content and topic_content[section]:
                sections.append(section)
        
        return sections
    
    def _format_general_guidance(self, guidance: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Format general guidance content.
        
        Args:
            guidance: Raw guidance content
            
        Returns:
            Formatted guidance content
        """
        formatted_guidance = []
        
        for item in guidance:
            formatted_item = {
                "title": item.get("title", "General Guidance"),
                "content": self._format_text_content(item.get("content", "")),
                "sections": self._extract_sections_from_text(item.get("content", ""))
            }
            formatted_guidance.append(formatted_item)
        
        return formatted_guidance
    
    def _format_templates(self, templates: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Format template content.
        
        Args:
            templates: Raw template content
            
        Returns:
            Formatted template content
        """
        formatted_templates = []
        
        for template in templates:
            formatted_template = {
                "name": template.get("name", "Template"),
                "content": self._format_text_content(template.get("content", "")),
                "type": "template",
                "usage_notes": self._extract_usage_notes(template.get("content", ""))
            }
            formatted_templates.append(formatted_template)
        
        return formatted_templates
    
    def _format_examples(self, examples: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Format example content.
        
        Args:
            examples: Raw example content
            
        Returns:
            Formatted example content
        """
        formatted_examples = []
        
        for example in examples:
            formatted_example = {
                "name": example.get("name", "Example"),
                "content": self._format_text_content(example.get("content", "")),
                "type": "example",
                "key_points": self._extract_key_points(example.get("content", ""))
            }
            formatted_examples.append(formatted_example)
        
        return formatted_examples
    
    def _format_recommendations(self, recommendations: List[str]) -> List[Dict[str, Any]]:
        """
        Format learning recommendations.
        
        Args:
            recommendations: Raw recommendations
            
        Returns:
            Formatted recommendations
        """
        formatted_recommendations = []
        
        for i, recommendation in enumerate(recommendations, 1):
            formatted_recommendations.append({
                "id": i,
                "text": recommendation.strip(),
                "priority": self._determine_recommendation_priority(recommendation),
                "category": self._categorize_recommendation(recommendation)
            })
        
        return formatted_recommendations
    
    def _format_text_content(self, content: str) -> Dict[str, Any]:
        """
        Format text content with structure.
        
        Args:
            content: Raw text content
            
        Returns:
            Formatted text structure
        """
        if not content.strip():
            return {"type": "empty", "content": ""}
        
        # Check if content has markdown structure
        lines = content.strip().split('\n')
        has_headers = any(line.strip().startswith('#') for line in lines)
        has_lists = any(line.strip().startswith(('- ', '* ', '1. ')) for line in lines)
        
        return {
            "type": "structured" if has_headers or has_lists else "plain",
            "content": content.strip(),
            "has_headers": has_headers,
            "has_lists": has_lists,
            "word_count": len(content.strip().split())
        }
    
    def _extract_sections_from_text(self, content: str) -> List[str]:
        """
        Extract section headers from text content.
        
        Args:
            content: Text content
            
        Returns:
            List of section headers
        """
        sections = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('###'):
                sections.append(line[3:].strip())
            elif line.startswith('##'):
                sections.append(line[2:].strip())
            elif line.startswith('#'):
                sections.append(line[1:].strip())
        
        return sections
    
    def _extract_usage_notes(self, content: str) -> List[str]:
        """
        Extract usage notes from template content.
        
        Args:
            content: Template content
            
        Returns:
            List of usage notes
        """
        notes = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if 'usage' in line.lower() or 'note' in line.lower() or 'instruction' in line.lower():
                notes.append(line)
        
        return notes[:3]  # Limit to top 3 notes
    
    def _extract_key_points(self, content: str) -> List[str]:
        """
        Extract key points from example content.
        
        Args:
            content: Example content
            
        Returns:
            List of key points
        """
        key_points = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith(('- ', '* ')) and len(line) > 10:
                key_points.append(line[2:])
            elif 'key' in line.lower() or 'important' in line.lower():
                key_points.append(line)
        
        return key_points[:5]  # Limit to top 5 key points
    
    def _determine_recommendation_priority(self, recommendation: str) -> str:
        """
        Determine priority level of a recommendation.
        
        Args:
            recommendation: Recommendation text
            
        Returns:
            Priority level (high, medium, low)
        """
        high_priority_keywords = ['fundamental', 'crucial', 'critical', 'essential', 'must']
        medium_priority_keywords = ['important', 'should', 'consider', 'focus']
        
        recommendation_lower = recommendation.lower()
        
        if any(keyword in recommendation_lower for keyword in high_priority_keywords):
            return "high"
        elif any(keyword in recommendation_lower for keyword in medium_priority_keywords):
            return "medium"
        else:
            return "low"
    
    def _categorize_recommendation(self, recommendation: str) -> str:
        """
        Categorize a recommendation by topic area.
        
        Args:
            recommendation: Recommendation text
            
        Returns:
            Category name
        """
        recommendation_lower = recommendation.lower()
        
        if any(keyword in recommendation_lower for keyword in ['risk', 'uncertainty']):
            return "risk_management"
        elif any(keyword in recommendation_lower for keyword in ['stakeholder', 'communication']):
            return "stakeholder_management"
        elif any(keyword in recommendation_lower for keyword in ['schedule', 'timeline', 'planning']):
            return "project_planning"
        elif any(keyword in recommendation_lower for keyword in ['quality', 'standard']):
            return "quality_management"
        else:
            return "general"
    
    def _get_quick_tips(self) -> List[Dict[str, str]]:
        """Get formatted quick project management tips."""
        tips = [
            "Always define clear success criteria before starting any project",
            "Communicate early and often with all stakeholders",
            "Document decisions and assumptions to avoid confusion later",
            "Plan for risks - they will happen, be prepared",
            "Regular team check-ins prevent small issues from becoming big problems",
            "Keep project documentation simple and accessible",
            "Celebrate milestones and acknowledge team contributions",
            "Learn from every project - conduct retrospectives"
        ]
        
        return [{"id": i+1, "tip": tip} for i, tip in enumerate(tips)]
    
    def _get_additional_resources(self) -> List[Dict[str, str]]:
        """Get formatted additional learning resources."""
        return [
            {
                "title": "Project Management Institute (PMI)",
                "description": "Professional organization with standards, certifications, and resources",
                "type": "Organization",
                "url": "https://www.pmi.org"
            },
            {
                "title": "PRINCE2 Methodology",
                "description": "Structured project management method with defined processes",
                "type": "Methodology",
                "url": "https://www.prince2.com"
            },
            {
                "title": "Agile Alliance",
                "description": "Resources and guidance for agile project management approaches",
                "type": "Organization",
                "url": "https://www.agilealliance.org"
            },
            {
                "title": "Project Management Body of Knowledge (PMBOK)",
                "description": "Comprehensive guide to project management practices and standards",
                "type": "Guide",
                "url": "https://www.pmi.org/pmbok-guide-standards"
            }
        ]
    
    def _format_topic_title(self, topic_key: str) -> str:
        """
        Format topic key to readable title.
        
        Args:
            topic_key: Topic key
            
        Returns:
            Formatted title
        """
        return topic_key.replace("_", " ").title()
    
    def _create_overview_summary(self, topics_info: List[Dict[str, Any]]) -> str:
        """
        Create summary text for learning overview.
        
        Args:
            topics_info: Topic information
            
        Returns:
            Summary text
        """
        total_topics = len(topics_info)
        available_topics = sum(1 for topic in topics_info if topic["available"])
        
        if total_topics == 0:
            return "No specific learning topics identified. General project management guidance is available."
        
        if available_topics == total_topics:
            return f"All {total_topics} relevant learning topics have content available."
        elif available_topics > 0:
            return f"{available_topics} of {total_topics} relevant topics have detailed content available."
        else:
            return f"{available_topics} of {total_topics} relevant topics have detailed content available."
    
    def _count_content_sections(self, learning_content: Dict[str, Any]) -> Dict[str, int]:
        """
        Count content sections for metadata.
        
        Args:
            learning_content: Learning content
            
        Returns:
            Section counts
        """
        return {
            "topics": len(learning_content.get("topics", {})),
            "guidance": len(learning_content.get("general_guidance", [])),
            "templates": len(learning_content.get("templates", [])),
            "examples": len(learning_content.get("examples", []))
        }