"""
Status Analysis Processor for PM Analysis Tool.

This module implements the StatusAnalysisProcessor class that integrates all data
extractors to compile consolidated project status and health metrics.
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set

from core.domain import Deliverable, Milestone, Risk, Stakeholder
from core.models import DocumentType, FileInfo, ProcessingResult, ProjectStatus
from extractors.deliverable_extractor import DeliverableExtractor
from extractors.milestone_extractor import MilestoneExtractor
from extractors.risk_extractor import RiskExtractor
from extractors.stakeholder_extractor import StakeholderExtractor
from processors.base_processor import BaseProcessor
from utils.error_handling import ErrorAggregator, error_context, handle_errors
from utils.exceptions import DataExtractionError, FileProcessingError
from utils.logger import get_logger

logger = get_logger(__name__)


class StatusAnalysisProcessor(BaseProcessor):
    """
    Processor for comprehensive project status analysis.

    This processor integrates data from all extractors to compile a consolidated
    view of project health, risks, deliverables, milestones, and stakeholder engagement.
    """

    def __init__(self):
        """Initialize the Status Analysis processor."""
        super().__init__()
        self.processor_name = "Status Analysis Processor"

        # Define required file patterns for comprehensive analysis
        self.required_files = ["*risk*", "*stakeholder*"]

        # Optional files that enhance analysis
        self.optional_files = [
            "*wbs*",
            "*roadmap*",
            "*milestone*",
            "*deliverable*",
            "*schedule*",
            "*budget*",
            "*quality*",
        ]

        # Initialize extractors
        self.risk_extractor = RiskExtractor()
        self.deliverable_extractor = DeliverableExtractor()
        self.milestone_extractor = MilestoneExtractor()
        self.stakeholder_extractor = StakeholderExtractor()

    def validate_inputs(self, files: List[FileInfo]) -> bool:
        """
        Validate that minimum required files are available for status analysis.

        For status analysis, we need at least risk and stakeholder information
        to provide meaningful project health insights.

        Args:
            files: List of available files

        Returns:
            True if minimum required files are present, False otherwise
        """
        if not files:
            logger.warning("No files provided for status analysis")
            return False

        # Check for readable files
        readable_files = [f for f in files if f.is_readable]
        if not readable_files:
            logger.warning("No readable files available for status analysis")
            return False

        # Check for minimum required document types
        available_types = {f.document_type for f in readable_files}

        # We need at least risk information for basic status analysis
        has_risk_data = any(
            doc_type in [DocumentType.RISK_REGISTER]
            or any(
                pattern.replace("*", "") in f.filename.lower()
                for pattern in ["*risk*"]
                for f in readable_files
            )
            for doc_type in available_types
        )

        if not has_risk_data:
            logger.warning("No risk data available - required for status analysis")
            return False

        return True

    def process(self, files: List[FileInfo], config: Dict[str, Any]) -> ProcessingResult:
        """
        Process files to generate comprehensive project status analysis.

        Args:
            files: List of files to analyze
            config: Configuration dictionary

        Returns:
            ProcessingResult with project status analysis
        """
        start_time = time.time()

        try:
            logger.info(f"Starting status analysis with {len(files)} files")

            # Validate inputs
            if not self.validate_inputs(files):
                return ProcessingResult(
                    success=False,
                    operation="status_analysis",
                    errors=["Insufficient files for status analysis - need at least risk data"],
                    processing_time_seconds=time.time() - start_time,
                )

            # Extract data from all available files
            extraction_results = self._extract_all_data(files)

            # Compile project status
            project_status = self._compile_project_status(
                extraction_results, config.get("project", {}).get("name", "Unknown Project")
            )

            # Generate analysis report
            analysis_report = self._generate_status_report(
                project_status, extraction_results, files
            )

            processing_time = time.time() - start_time
            logger.info(f"Status analysis completed in {processing_time:.2f} seconds")

            return ProcessingResult(
                success=True,
                operation="status_analysis",
                data=analysis_report,
                warnings=extraction_results.get("warnings", []),
                processing_time_seconds=processing_time,
            )

        except Exception as e:
            error_msg = f"Status analysis processing failed: {str(e)}"
            logger.error(error_msg, exc_info=True)

            return ProcessingResult(
                success=False,
                operation="status_analysis",
                errors=[error_msg],
                processing_time_seconds=time.time() - start_time,
            )

    def _extract_all_data(self, files: List[FileInfo]) -> Dict[str, Any]:
        """
        Extract data from all available files using appropriate extractors.

        Args:
            files: List of files to process

        Returns:
            Dictionary containing all extracted data and any warnings
        """
        extraction_results = {
            "risks": [],
            "deliverables": [],
            "milestones": [],
            "stakeholders": [],
            "warnings": [],
            "extraction_summary": {},
        }

        # Process each file with appropriate extractors
        for file_info in files:
            if not file_info.is_readable:
                extraction_results["warnings"].append(
                    f"Skipping unreadable file: {file_info.filename}"
                )
                continue

            file_path = str(file_info.path)
            filename_lower = file_info.filename.lower()

            try:
                # Extract risks (only from risk-related files)
                if any(
                    keyword in filename_lower for keyword in ["risk", "threat", "issue"]
                ) and not any(
                    keyword in filename_lower
                    for keyword in ["stakeholder", "wbs", "deliverable", "milestone", "roadmap"]
                ):
                    risks = self.risk_extractor.extract_risks(file_path)
                    extraction_results["risks"].extend(risks)
                    logger.debug(f"Extracted {len(risks)} risks from {file_info.filename}")

                # Extract deliverables (only from WBS/deliverable files)
                elif any(
                    keyword in filename_lower
                    for keyword in ["wbs", "deliverable", "work", "breakdown"]
                ):
                    deliverables = self.deliverable_extractor.extract_deliverables(file_path)
                    extraction_results["deliverables"].extend(deliverables)
                    logger.debug(
                        f"Extracted {len(deliverables)} deliverables from {file_info.filename}"
                    )

                # Extract milestones (only from roadmap/schedule files)
                elif any(
                    keyword in filename_lower
                    for keyword in ["milestone", "roadmap", "schedule", "timeline"]
                ):
                    milestones = self.milestone_extractor.extract_milestones(file_path)
                    extraction_results["milestones"].extend(milestones)
                    logger.debug(
                        f"Extracted {len(milestones)} milestones from {file_info.filename}"
                    )

                # Extract stakeholders (only from stakeholder files)
                elif (
                    any(keyword in filename_lower for keyword in ["stakeholder", "contact"])
                    and "register" in filename_lower
                ):
                    stakeholders = self.stakeholder_extractor.extract_stakeholders(file_path)
                    extraction_results["stakeholders"].extend(stakeholders)
                    logger.debug(
                        f"Extracted {len(stakeholders)} stakeholders from {file_info.filename}"
                    )

            except DataExtractionError as e:
                warning_msg = f"Failed to extract data from {file_info.filename}: {str(e)}"
                extraction_results["warnings"].append(warning_msg)
                logger.warning(warning_msg)
            except Exception as e:
                warning_msg = f"Unexpected error processing {file_info.filename}: {str(e)}"
                extraction_results["warnings"].append(warning_msg)
                logger.error(warning_msg, exc_info=True)

        # Generate extraction summary
        extraction_results["extraction_summary"] = {
            "total_files_processed": len(files),
            "risks_extracted": len(extraction_results["risks"]),
            "deliverables_extracted": len(extraction_results["deliverables"]),
            "milestones_extracted": len(extraction_results["milestones"]),
            "stakeholders_extracted": len(extraction_results["stakeholders"]),
            "warnings_count": len(extraction_results["warnings"]),
        }

        return extraction_results

    def _compile_project_status(
        self, extraction_results: Dict[str, Any], project_name: str
    ) -> ProjectStatus:
        """
        Compile comprehensive project status from extracted data.

        Args:
            extraction_results: Results from data extraction
            project_name: Name of the project

        Returns:
            ProjectStatus object with compiled metrics
        """
        risks = extraction_results["risks"]
        deliverables = extraction_results["deliverables"]
        milestones = extraction_results["milestones"]
        stakeholders = extraction_results["stakeholders"]

        # Calculate risk metrics
        total_risks = len(risks)
        high_priority_risks = len([r for r in risks if r.priority.value in ["high", "critical"]])

        # Calculate deliverable metrics
        total_deliverables = len(deliverables)
        completed_deliverables = len([d for d in deliverables if d.is_completed])

        # Calculate milestone metrics
        total_milestones = len(milestones)
        completed_milestones = len([m for m in milestones if m.is_completed])
        overdue_milestones = len([m for m in milestones if m.is_overdue])

        # Calculate stakeholder metrics
        total_stakeholders = len(stakeholders)
        high_influence_stakeholders = len([s for s in stakeholders if s.is_high_priority])
        key_stakeholder_engagement = self._calculate_stakeholder_engagement(stakeholders)

        # Calculate schedule variance (simplified)
        schedule_variance_days = self._calculate_schedule_variance(milestones)

        # Calculate overall health score
        overall_health_score = self._calculate_health_score(
            risks, deliverables, milestones, stakeholders
        )

        # Generate critical issues and recommendations
        critical_issues = self._identify_critical_issues(
            risks, deliverables, milestones, stakeholders
        )
        recommendations = self._generate_recommendations(
            risks, deliverables, milestones, stakeholders
        )

        return ProjectStatus(
            project_name=project_name,
            analysis_timestamp=datetime.now(),
            overall_health_score=overall_health_score,
            total_risks=total_risks,
            high_priority_risks=high_priority_risks,
            total_deliverables=total_deliverables,
            completed_deliverables=completed_deliverables,
            total_milestones=total_milestones,
            completed_milestones=completed_milestones,
            overdue_milestones=overdue_milestones,
            total_stakeholders=total_stakeholders,
            key_stakeholder_engagement=key_stakeholder_engagement,
            schedule_variance_days=schedule_variance_days,
            critical_issues=critical_issues,
            recommendations=recommendations,
            data_sources=[
                f"Extracted from {extraction_results.get('extraction_summary', {}).get('total_files_processed', 0)} files"
            ],
        )

    def _calculate_stakeholder_engagement(self, stakeholders: List[Stakeholder]) -> float:
        """
        Calculate overall stakeholder engagement score.

        Args:
            stakeholders: List of stakeholder objects

        Returns:
            Engagement score between 0.0 and 1.0
        """
        if not stakeholders:
            return 0.0

        # Simple engagement calculation based on influence and interest
        total_engagement = 0.0
        for stakeholder in stakeholders:
            # Weight by influence level
            influence_weight = stakeholder.influence_score / 4.0  # Normalize to 0-1
            interest_weight = stakeholder.interest_score / 4.0  # Normalize to 0-1

            # Engagement is average of influence and interest
            engagement = (influence_weight + interest_weight) / 2.0
            total_engagement += engagement

        return total_engagement / len(stakeholders)

    def _calculate_schedule_variance(self, milestones: List[Milestone]) -> int:
        """
        Calculate overall schedule variance in days.

        Args:
            milestones: List of milestone objects

        Returns:
            Schedule variance in days (positive = behind, negative = ahead)
        """
        if not milestones:
            return 0

        total_variance = 0
        variance_count = 0

        for milestone in milestones:
            if milestone.schedule_variance_days is not None:
                total_variance += milestone.schedule_variance_days
                variance_count += 1

        return total_variance // variance_count if variance_count > 0 else 0

    def _calculate_health_score(
        self,
        risks: List[Risk],
        deliverables: List[Deliverable],
        milestones: List[Milestone],
        stakeholders: List[Stakeholder],
    ) -> float:
        """
        Calculate overall project health score.

        Args:
            risks: List of risk objects
            deliverables: List of deliverable objects
            milestones: List of milestone objects
            stakeholders: List of stakeholder objects

        Returns:
            Health score between 0.0 and 1.0
        """
        scores = []

        # Risk health (lower risk = higher health)
        if risks:
            high_risk_ratio = len(
                [r for r in risks if r.priority.value in ["high", "critical"]]
            ) / len(risks)
            risk_score = max(0.0, 1.0 - high_risk_ratio)
            scores.append(risk_score)

        # Deliverable health
        if deliverables:
            completion_ratio = len([d for d in deliverables if d.is_completed]) / len(deliverables)
            on_track_ratio = len([d for d in deliverables if d.is_on_track]) / len(deliverables)
            deliverable_score = (completion_ratio + on_track_ratio) / 2.0
            scores.append(deliverable_score)

        # Milestone health
        if milestones:
            completed_ratio = len([m for m in milestones if m.is_completed]) / len(milestones)
            overdue_ratio = len([m for m in milestones if m.is_overdue]) / len(milestones)
            milestone_score = completed_ratio - (overdue_ratio * 0.5)  # Penalize overdue
            milestone_score = max(0.0, min(1.0, milestone_score))
            scores.append(milestone_score)

        # Stakeholder engagement health
        if stakeholders:
            engagement_score = self._calculate_stakeholder_engagement(stakeholders)
            scores.append(engagement_score)

        # Return average of all available scores
        return sum(scores) / len(scores) if scores else 0.5

    def _identify_critical_issues(
        self,
        risks: List[Risk],
        deliverables: List[Deliverable],
        milestones: List[Milestone],
        stakeholders: List[Stakeholder],
    ) -> List[str]:
        """
        Identify critical issues that need immediate attention.

        Args:
            risks: List of risk objects
            deliverables: List of deliverable objects
            milestones: List of milestone objects
            stakeholders: List of stakeholder objects

        Returns:
            List of critical issue descriptions
        """
        issues = []

        # Critical risks
        critical_risks = [r for r in risks if r.priority.value == "critical"]
        if critical_risks:
            issues.append(f"{len(critical_risks)} critical risks require immediate attention")

        # Overdue milestones
        overdue_milestones = [m for m in milestones if m.is_overdue]
        if overdue_milestones:
            issues.append(f"{len(overdue_milestones)} milestones are overdue")

        # Significantly delayed deliverables
        delayed_deliverables = [d for d in deliverables if d.is_overdue]
        if delayed_deliverables:
            issues.append(f"{len(delayed_deliverables)} deliverables are overdue")

        # High-influence stakeholders with low engagement
        disengaged_stakeholders = [
            s for s in stakeholders if s.influence_score >= 3 and s.interest_score <= 2
        ]
        if disengaged_stakeholders:
            issues.append(
                f"{len(disengaged_stakeholders)} high-influence stakeholders show low engagement"
            )

        return issues

    def _generate_recommendations(
        self,
        risks: List[Risk],
        deliverables: List[Deliverable],
        milestones: List[Milestone],
        stakeholders: List[Stakeholder],
    ) -> List[str]:
        """
        Generate actionable recommendations based on project status.

        Args:
            risks: List of risk objects
            deliverables: List of deliverable objects
            milestones: List of milestone objects
            stakeholders: List of stakeholder objects

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Risk-based recommendations
        open_risks = [r for r in risks if not r.is_resolved]
        if len(open_risks) > len(risks) * 0.7:  # More than 70% risks are open
            recommendations.append("Focus on risk mitigation - high number of unresolved risks")

        # Deliverable-based recommendations
        if deliverables:
            completion_rate = len([d for d in deliverables if d.is_completed]) / len(deliverables)
            if completion_rate < 0.5:
                recommendations.append(
                    "Accelerate deliverable completion - project is behind schedule"
                )

        # Milestone-based recommendations
        if milestones:
            overdue_count = len([m for m in milestones if m.is_overdue])
            if overdue_count > 0:
                recommendations.append("Address overdue milestones to get project back on track")

        # Stakeholder-based recommendations
        if stakeholders:
            high_influence_low_interest = [
                s for s in stakeholders if s.influence_score >= 3 and s.interest_score <= 2
            ]
            if high_influence_low_interest:
                recommendations.append(
                    "Increase engagement with high-influence, low-interest stakeholders"
                )

        # General recommendations if no specific issues
        if not recommendations:
            recommendations.append(
                "Continue current project management practices - project appears healthy"
            )

        return recommendations

    def _generate_status_report(
        self,
        project_status: ProjectStatus,
        extraction_results: Dict[str, Any],
        files: List[FileInfo],
    ) -> Dict[str, Any]:
        """
        Generate comprehensive status analysis report.

        Args:
            project_status: Compiled project status
            extraction_results: Raw extraction results
            files: Original file list

        Returns:
            Dictionary containing formatted report data
        """
        report = {
            "project_overview": {
                "project_name": project_status.project_name,
                "analysis_date": project_status.analysis_timestamp.isoformat(),
                "overall_health_score": project_status.overall_health_score,
                "health_percentage": project_status.health_percentage,
                "compliance_status": project_status.get_status_summary(),
                "data_sources_count": len(files),
            },
            "risk_analysis": {
                "total_risks": project_status.total_risks,
                "high_priority_risks": project_status.high_priority_risks,
                "risk_severity_ratio": project_status.risk_severity_ratio,
                "risk_details": [
                    self._serialize_risk(r) for r in extraction_results["risks"][:10]
                ],  # Top 10
            },
            "deliverable_analysis": {
                "total_deliverables": project_status.total_deliverables,
                "completed_deliverables": project_status.completed_deliverables,
                "completion_rate": project_status.deliverable_completion_rate,
                "deliverable_details": [
                    self._serialize_deliverable(d) for d in extraction_results["deliverables"][:10]
                ],
            },
            "milestone_analysis": {
                "total_milestones": project_status.total_milestones,
                "completed_milestones": project_status.completed_milestones,
                "overdue_milestones": project_status.overdue_milestones,
                "completion_rate": project_status.milestone_completion_rate,
                "schedule_variance_days": project_status.schedule_variance_days,
                "milestone_details": [
                    self._serialize_milestone(m) for m in extraction_results["milestones"][:10]
                ],
            },
            "stakeholder_analysis": {
                "total_stakeholders": project_status.total_stakeholders,
                "key_stakeholder_engagement": project_status.key_stakeholder_engagement,
                "engagement_percentage": int(project_status.key_stakeholder_engagement * 100),
                "stakeholder_details": [
                    self._serialize_stakeholder(s) for s in extraction_results["stakeholders"][:10]
                ],
            },
            "critical_issues": project_status.critical_issues,
            "recommendations": project_status.recommendations,
            "extraction_summary": extraction_results["extraction_summary"],
            "warnings": extraction_results["warnings"],
        }

        return report

    def _serialize_risk(self, risk: Risk) -> Dict[str, Any]:
        """Serialize a Risk object for JSON output."""
        return {
            "risk_id": risk.risk_id,
            "title": risk.title,
            "priority": risk.priority.value,
            "status": risk.status.value,
            "probability": risk.probability,
            "impact": risk.impact,
            "risk_score": risk.risk_score,
            "owner": risk.owner,
        }

    def _serialize_deliverable(self, deliverable: Deliverable) -> Dict[str, Any]:
        """Serialize a Deliverable object for JSON output."""
        return {
            "deliverable_id": deliverable.deliverable_id,
            "name": deliverable.name,
            "wbs_code": deliverable.wbs_code,
            "status": deliverable.status.value,
            "completion_percentage": deliverable.completion_percentage,
            "assigned_to": deliverable.assigned_to,
            "is_overdue": deliverable.is_overdue,
        }

    def _serialize_milestone(self, milestone: Milestone) -> Dict[str, Any]:
        """Serialize a Milestone object for JSON output."""
        return {
            "milestone_id": milestone.milestone_id,
            "name": milestone.name,
            "target_date": milestone.target_date.isoformat(),
            "status": milestone.status.value,
            "is_overdue": milestone.is_overdue,
            "days_until_target": milestone.days_until_target,
            "owner": milestone.owner,
        }

    def _serialize_stakeholder(self, stakeholder: Stakeholder) -> Dict[str, Any]:
        """Serialize a Stakeholder object for JSON output."""
        return {
            "stakeholder_id": stakeholder.stakeholder_id,
            "name": stakeholder.name,
            "role": stakeholder.role,
            "organization": stakeholder.organization,
            "influence": stakeholder.influence.value,
            "interest": stakeholder.interest.value,
            "engagement_priority": stakeholder.engagement_priority,
            "is_high_priority": stakeholder.is_high_priority,
        }
