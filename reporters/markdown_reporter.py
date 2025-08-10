"""
Markdown report generator for PM Analysis Tool.

This module provides the MarkdownReporter class that generates structured
markdown reports from processing results.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

from reporters.base_reporter import BaseReporter
from core.models import ProcessingResult, ProjectStatus
from core.domain import Risk, Deliverable, Milestone, Stakeholder
from utils.logger import get_logger
from utils.exceptions import ReportGenerationError, FileProcessingError
from utils.error_handling import handle_errors, error_context, safe_execute

logger = get_logger(__name__)


class MarkdownReporter(BaseReporter):
    """
    Generates structured markdown reports from processing results.
    
    This reporter creates well-formatted markdown documents with consistent
    structure, including headers, tables, and sections for different data types.
    """
    
    def __init__(self):
        """Initialize the markdown reporter."""
        super().__init__()
        self.reporter_name = "Markdown Reporter"
        self.output_format = "markdown"
        self.file_extension = ".md"
    
    def generate_report(self, 
                       data: ProcessingResult, 
                       output_path: str, 
                       config: Dict[str, Any]) -> str:
        """
        Generate a markdown report from processing results.
        
        Args:
            data: Processing results to format
            output_path: Directory where report should be saved
            config: Configuration for report generation
            
        Returns:
            Path to the generated report file
            
        Raises:
            ReportGenerationError: If report generation fails
        """
        try:
            # Validate output path
            if not self.validate_output_path(output_path):
                raise ValueError(f"Cannot write to {output_path}")
            
            # Create report content
            formatted_content = self.format_data(data.data, config)
            
            # Add header and error information
            header = self._create_report_header(data, config)
            error_section = self.handle_processing_errors(data)
            
            # Combine all sections
            full_content = header + "\n\n" + formatted_content
            if error_section:
                full_content += "\n\n" + error_section
            
            # Generate filename and write file
            base_name = config.get('filename', 'analysis_report')
            filename = self.generate_filename(
                base_name, 
                config.get('include_timestamp', True)
            )
            file_path = Path(output_path) / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(full_content)
            
            return str(file_path)
            
        except Exception as e:
            raise ValueError(f"Failed to generate markdown report: {e}")
    
    def format_data(self, data: Dict[str, Any], config: Dict[str, Any]) -> str:
        """
        Format data into markdown structure.
        
        Args:
            data: Data to format
            config: Formatting configuration
            
        Returns:
            Formatted markdown content
        """
        template = config.get('template', 'standard')
        
        if template == 'detailed':
            return self._format_detailed_report(data, config)
        elif template == 'summary':
            return self._format_summary_report(data, config)
        else:
            return self._format_standard_report(data, config)
    
    def _create_report_header(self, data: ProcessingResult, config: Dict[str, Any]) -> str:
        """Create the report header section."""
        title = config.get('title', 'Project Management Analysis Report')
        
        header_lines = [
            f"# {title}",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Operation:** {data.operation}",
            f"**Status:** {'✅ Success' if data.success else '❌ Failed'}",
            f"**Processing Time:** {data.processing_time_seconds:.2f} seconds"
        ]
        
        if data.file_path:
            header_lines.append(f"**Source File:** {data.file_path}")
        
        return "\n".join(header_lines)
    
    def _format_standard_report(self, data: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Format data using the standard template."""
        sections = []
        
        # Project Status Overview
        if 'project_status' in data:
            sections.append(self._format_project_status(data['project_status']))
        
        # Document Check Results
        if 'missing_files' in data or 'found_files' in data:
            sections.append(self._format_document_check(data))
        
        # Risks Section
        if 'risks' in data:
            sections.append(self._format_risks_section(data['risks']))
        
        # Deliverables Section
        if 'deliverables' in data:
            sections.append(self._format_deliverables_section(data['deliverables']))
        
        # Milestones Section
        if 'milestones' in data:
            sections.append(self._format_milestones_section(data['milestones']))
        
        # Stakeholders Section
        if 'stakeholders' in data:
            sections.append(self._format_stakeholders_section(data['stakeholders']))
        
        # Learning Content
        if 'learning_content' in data:
            sections.append(self._format_learning_content(data['learning_content']))
        
        return "\n\n".join(sections)
    
    def _format_detailed_report(self, data: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Format data using the detailed template with additional information."""
        sections = []
        
        # Executive Summary
        sections.append(self._format_executive_summary(data))
        
        # Detailed sections with more information
        sections.append(self._format_standard_report(data, config))
        
        # Additional Analysis
        if any(key in data for key in ['risks', 'deliverables', 'milestones']):
            sections.append(self._format_analysis_section(data))
        
        return "\n\n".join(sections)
    
    def _format_summary_report(self, data: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Format data using the summary template with key metrics only."""
        sections = []
        
        # Key Metrics
        sections.append(self._format_key_metrics(data))
        
        # Critical Issues Only
        if 'risks' in data:
            high_priority_risks = [r for r in data['risks'] if r.get('priority') in ['high', 'critical']]
            if high_priority_risks:
                sections.append(self._format_critical_risks(high_priority_risks))
        
        # Overdue Items
        overdue_items = self._extract_overdue_items(data)
        if overdue_items:
            sections.append(self._format_overdue_items(overdue_items))
        
        return "\n\n".join(sections)
    
    def _format_project_status(self, status_data: Dict[str, Any]) -> str:
        """Format project status overview."""
        lines = [
            "## Project Status Overview",
            "",
            f"**Project:** {status_data.get('project_name', 'Unknown')}",
            f"**Overall Health:** {status_data.get('health_percentage', 0)}% "
            f"({'🟢 Healthy' if status_data.get('overall_health_score', 0) >= 0.7 else '🟡 At Risk'})",
            "",
            "### Key Metrics",
            "",
            f"- **Risks:** {status_data.get('total_risks', 0)} total, "
            f"{status_data.get('high_priority_risks', 0)} high priority",
            f"- **Deliverables:** {status_data.get('completed_deliverables', 0)}/"
            f"{status_data.get('total_deliverables', 0)} completed "
            f"({status_data.get('deliverable_completion_rate', 0)*100:.1f}%)",
            f"- **Milestones:** {status_data.get('completed_milestones', 0)}/"
            f"{status_data.get('total_milestones', 0)} completed "
            f"({status_data.get('milestone_completion_rate', 0)*100:.1f}%)",
            f"- **Stakeholders:** {status_data.get('total_stakeholders', 0)} identified"
        ]
        
        if status_data.get('critical_issues'):
            lines.extend([
                "",
                "### Critical Issues",
                ""
            ])
            for issue in status_data['critical_issues']:
                lines.append(f"- ⚠️ {issue}")
        
        return "\n".join(lines)
    
    def _format_document_check(self, data: Dict[str, Any]) -> str:
        """Format document check results."""
        lines = ["## Document Check Results", ""]
        
        if 'found_files' in data:
            lines.extend([
                "### Found Documents",
                "",
                "| Document | Format | Status |",
                "|----------|--------|--------|"
            ])
            
            for file_info in data['found_files']:
                status = "✅ Valid" if file_info.get('is_readable', True) else "❌ Invalid"
                lines.append(f"| {file_info.get('filename', 'Unknown')} | "
                           f"{file_info.get('format', 'Unknown')} | {status} |")
        
        if 'missing_files' in data and data['missing_files']:
            lines.extend([
                "",
                "### Missing Documents",
                ""
            ])
            for missing_file in data['missing_files']:
                lines.append(f"- ❌ {missing_file}")
        
        return "\n".join(lines)
    
    def _format_risks_section(self, risks: List[Dict[str, Any]]) -> str:
        """Format risks section."""
        if not risks:
            return "## Risks\n\nNo risks found in the analysis."
        
        lines = [
            f"## Risks ({len(risks)} total)",
            "",
            "| ID | Title | Priority | Status | Owner | Risk Score |",
            "|----|----|----------|--------|-------|------------|"
        ]
        
        for risk in risks:
            priority_icon = self._get_priority_icon(risk.get('priority', 'low'))
            status_icon = self._get_status_icon(risk.get('status', 'open'))
            risk_score = risk.get('risk_score', 0)
            
            lines.append(
                f"| {risk.get('risk_id', 'N/A')} | "
                f"{risk.get('title', 'Untitled')} | "
                f"{priority_icon} {risk.get('priority', 'Low').title()} | "
                f"{status_icon} {risk.get('status', 'Open').replace('_', ' ').title()} | "
                f"{risk.get('owner', 'Unassigned')} | "
                f"{risk_score:.2f} |"
            )
        
        # Add high priority risks details
        high_priority = [r for r in risks if r.get('priority') in ['high', 'critical']]
        if high_priority:
            lines.extend([
                "",
                "### High Priority Risks",
                ""
            ])
            for risk in high_priority:
                lines.extend([
                    f"#### {risk.get('title', 'Untitled')} ({risk.get('risk_id', 'N/A')})",
                    f"**Description:** {risk.get('description', 'No description available')}",
                    f"**Mitigation:** {risk.get('mitigation_strategy', 'No mitigation strategy defined')}",
                    ""
                ])
        
        return "\n".join(lines)
    
    def _format_deliverables_section(self, deliverables: List[Dict[str, Any]]) -> str:
        """Format deliverables section."""
        if not deliverables:
            return "## Deliverables\n\nNo deliverables found in the analysis."
        
        lines = [
            f"## Deliverables ({len(deliverables)} total)",
            "",
            "| ID | Name | Status | Progress | Due Date | Assigned To |",
            "|----|------|--------|----------|----------|-------------|"
        ]
        
        for deliverable in deliverables:
            status_icon = self._get_deliverable_status_icon(deliverable.get('status', 'not_started'))
            progress = deliverable.get('completion_percentage', 0)
            due_date = deliverable.get('due_date', 'Not set')
            
            lines.append(
                f"| {deliverable.get('deliverable_id', 'N/A')} | "
                f"{deliverable.get('name', 'Untitled')} | "
                f"{status_icon} {deliverable.get('status', 'Not Started').replace('_', ' ').title()} | "
                f"{progress:.1f}% | "
                f"{due_date} | "
                f"{deliverable.get('assigned_to', 'Unassigned')} |"
            )
        
        return "\n".join(lines)
    
    def _format_milestones_section(self, milestones: List[Dict[str, Any]]) -> str:
        """Format milestones section."""
        if not milestones:
            return "## Milestones\n\nNo milestones found in the analysis."
        
        lines = [
            f"## Milestones ({len(milestones)} total)",
            "",
            "| ID | Name | Target Date | Status | Owner |",
            "|----|------|-------------|--------|-------|"
        ]
        
        for milestone in milestones:
            status_icon = self._get_milestone_status_icon(milestone.get('status', 'upcoming'))
            target_date = milestone.get('target_date', 'Not set')
            
            lines.append(
                f"| {milestone.get('milestone_id', 'N/A')} | "
                f"{milestone.get('name', 'Untitled')} | "
                f"{target_date} | "
                f"{status_icon} {milestone.get('status', 'Upcoming').replace('_', ' ').title()} | "
                f"{milestone.get('owner', 'Unassigned')} |"
            )
        
        return "\n".join(lines)
    
    def _format_stakeholders_section(self, stakeholders: List[Dict[str, Any]]) -> str:
        """Format stakeholders section."""
        if not stakeholders:
            return "## Stakeholders\n\nNo stakeholders found in the analysis."
        
        lines = [
            f"## Stakeholders ({len(stakeholders)} total)",
            "",
            "| Name | Role | Influence | Interest | Engagement Priority |",
            "|------|------|-----------|----------|-------------------|"
        ]
        
        for stakeholder in stakeholders:
            influence = stakeholder.get('influence', 'medium').replace('_', ' ').title()
            interest = stakeholder.get('interest', 'medium').replace('_', ' ').title()
            priority = stakeholder.get('engagement_priority', 'Monitor')
            
            lines.append(
                f"| {stakeholder.get('name', 'Unknown')} | "
                f"{stakeholder.get('role', 'Unknown')} | "
                f"{influence} | "
                f"{interest} | "
                f"{priority} |"
            )
        
        return "\n".join(lines)
    
    def _format_learning_content(self, content: Dict[str, Any]) -> str:
        """Format learning content section."""
        lines = ["## Learning Content", ""]
        
        if 'modules' in content:
            for module in content['modules']:
                lines.extend([
                    f"### {module.get('title', 'Untitled Module')}",
                    "",
                    module.get('content', 'No content available'),
                    ""
                ])
        
        return "\n".join(lines)
    
    def _format_executive_summary(self, data: Dict[str, Any]) -> str:
        """Format executive summary for detailed reports."""
        lines = [
            "## Executive Summary",
            "",
            "This report provides a comprehensive analysis of the project management documents "
            "and current project status. Key findings and recommendations are highlighted below.",
            ""
        ]
        
        # Add key findings based on available data
        if 'project_status' in data:
            status = data['project_status']
            health_score = status.get('overall_health_score', 0)
            
            if health_score >= 0.8:
                lines.append("✅ **Project Health:** The project is performing well with strong metrics across all areas.")
            elif health_score >= 0.6:
                lines.append("⚠️ **Project Health:** The project shows some areas of concern that require attention.")
            else:
                lines.append("🚨 **Project Health:** The project is at risk and requires immediate intervention.")
        
        return "\n".join(lines)
    
    def _format_key_metrics(self, data: Dict[str, Any]) -> str:
        """Format key metrics for summary reports."""
        lines = ["## Key Metrics", ""]
        
        if 'project_status' in data:
            status = data['project_status']
            lines.extend([
                f"- **Overall Health:** {status.get('health_percentage', 0)}%",
                f"- **Total Risks:** {status.get('total_risks', 0)}",
                f"- **High Priority Risks:** {status.get('high_priority_risks', 0)}",
                f"- **Deliverable Completion:** {status.get('deliverable_completion_rate', 0)*100:.1f}%",
                f"- **Milestone Completion:** {status.get('milestone_completion_rate', 0)*100:.1f}%"
            ])
        
        return "\n".join(lines)
    
    def _format_critical_risks(self, risks: List[Dict[str, Any]]) -> str:
        """Format critical risks section."""
        lines = ["## Critical Risks", ""]
        
        for risk in risks:
            lines.extend([
                f"### {risk.get('title', 'Untitled')}",
                f"**Priority:** {risk.get('priority', 'Unknown').title()}",
                f"**Owner:** {risk.get('owner', 'Unassigned')}",
                f"**Description:** {risk.get('description', 'No description')}",
                ""
            ])
        
        return "\n".join(lines)
    
    def _format_overdue_items(self, overdue_items: Dict[str, List]) -> str:
        """Format overdue items section."""
        lines = ["## Overdue Items", ""]
        
        if overdue_items.get('milestones'):
            lines.extend(["### Overdue Milestones", ""])
            for milestone in overdue_items['milestones']:
                lines.append(f"- {milestone.get('name', 'Untitled')} (Due: {milestone.get('target_date', 'Unknown')})")
        
        if overdue_items.get('deliverables'):
            lines.extend(["", "### Overdue Deliverables", ""])
            for deliverable in overdue_items['deliverables']:
                lines.append(f"- {deliverable.get('name', 'Untitled')} (Due: {deliverable.get('due_date', 'Unknown')})")
        
        return "\n".join(lines)
    
    def _format_analysis_section(self, data: Dict[str, Any]) -> str:
        """Format additional analysis section for detailed reports."""
        lines = ["## Analysis & Recommendations", ""]
        
        # Risk analysis
        if 'risks' in data:
            risk_count = len(data['risks'])
            high_priority_count = len([r for r in data['risks'] if r.get('priority') in ['high', 'critical']])
            
            lines.extend([
                "### Risk Analysis",
                f"- Total risks identified: {risk_count}",
                f"- High/Critical priority risks: {high_priority_count}",
                f"- Risk exposure: {(high_priority_count/risk_count*100) if risk_count > 0 else 0:.1f}%",
                ""
            ])
        
        # Schedule analysis
        if 'milestones' in data:
            milestone_count = len(data['milestones'])
            completed_count = len([m for m in data['milestones'] if m.get('status') == 'completed'])
            
            lines.extend([
                "### Schedule Analysis",
                f"- Total milestones: {milestone_count}",
                f"- Completed milestones: {completed_count}",
                f"- Schedule progress: {(completed_count/milestone_count*100) if milestone_count > 0 else 0:.1f}%",
                ""
            ])
        
        return "\n".join(lines)
    
    def _extract_overdue_items(self, data: Dict[str, Any]) -> Dict[str, List]:
        """Extract overdue items from data."""
        overdue = {'milestones': [], 'deliverables': []}
        
        if 'milestones' in data:
            overdue['milestones'] = [m for m in data['milestones'] if m.get('is_overdue', False)]
        
        if 'deliverables' in data:
            overdue['deliverables'] = [d for d in data['deliverables'] if d.get('is_overdue', False)]
        
        return overdue
    
    def _get_priority_icon(self, priority: str) -> str:
        """Get icon for risk priority."""
        icons = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🟠',
            'critical': '🔴'
        }
        return icons.get(priority.lower(), '⚪')
    
    def _get_status_icon(self, status: str) -> str:
        """Get icon for risk status."""
        icons = {
            'open': '🔴',
            'in_progress': '🟡',
            'mitigated': '🟢',
            'closed': '✅',
            'accepted': '🔵'
        }
        return icons.get(status.lower(), '⚪')
    
    def _get_deliverable_status_icon(self, status: str) -> str:
        """Get icon for deliverable status."""
        icons = {
            'not_started': '⚪',
            'in_progress': '🟡',
            'completed': '✅',
            'on_hold': '⏸️',
            'cancelled': '❌'
        }
        return icons.get(status.lower(), '⚪')
    
    def _get_milestone_status_icon(self, status: str) -> str:
        """Get icon for milestone status."""
        icons = {
            'upcoming': '⚪',
            'in_progress': '🟡',
            'completed': '✅',
            'overdue': '🔴',
            'cancelled': '❌'
        }
        return icons.get(status.lower(), '⚪')
    
    def get_supported_config_options(self) -> Dict[str, Any]:
        """Get configuration options supported by the markdown reporter."""
        base_options = super().get_supported_config_options()
        
        markdown_options = {
            'title': {
                'type': str,
                'default': 'Project Management Analysis Report',
                'description': 'Custom title for the report'
            },
            'filename': {
                'type': str,
                'default': 'analysis_report',
                'description': 'Base filename for the report'
            },
            'include_icons': {
                'type': bool,
                'default': True,
                'description': 'Include emoji icons in the report'
            },
            'show_details': {
                'type': bool,
                'default': True,
                'description': 'Include detailed information for high priority items'
            }
        }
        
        return {**base_options, **markdown_options}