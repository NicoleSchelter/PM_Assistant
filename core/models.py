"""
Core data models for PM Analysis Tool.

This module defines the primary data structures used throughout the application
for representing file information, processing results, and system state.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union


class OperationMode(Enum):
    """Enumeration of available operation modes."""
    DOCUMENT_CHECK = "document_check"
    STATUS_ANALYSIS = "status_analysis"
    LEARNING_MODULE = "learning_module"


class FileFormat(Enum):
    """Enumeration of supported file formats."""
    MARKDOWN = "md"
    EXCEL = "xlsx"
    EXCEL_LEGACY = "xls"
    MICROSOFT_PROJECT = "mpp"
    YAML = "yaml"
    JSON = "json"
    CSV = "csv"


class ProcessingStatus(Enum):
    """Enumeration of processing status values."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class DocumentType(Enum):
    """Enumeration of project document types."""
    RISK_REGISTER = "risk_register"
    STAKEHOLDER_REGISTER = "stakeholder_register"
    WBS = "wbs"
    PROJECT_SCHEDULE = "project_schedule"
    ROADMAP = "roadmap"
    STATUS_REPORT = "status_report"
    CHARTER = "charter"
    REQUIREMENTS = "requirements"
    UNKNOWN = "unknown"


@dataclass
class FileInfo:
    """
    Information about a discovered project file.
    
    This dataclass contains metadata about files found during project scanning,
    including their location, format, type, and processing status.
    """
    path: Path
    format: FileFormat
    document_type: DocumentType
    size_bytes: int
    last_modified: datetime
    is_readable: bool = True
    processing_status: ProcessingStatus = ProcessingStatus.NOT_STARTED
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate and normalize file information after initialization."""
        if not isinstance(self.path, Path):
            self.path = Path(self.path)
        
        # Ensure size is non-negative
        if self.size_bytes < 0:
            self.size_bytes = 0
    
    @property
    def filename(self) -> str:
        """Get the filename without path."""
        return self.path.name
    
    @property
    def extension(self) -> str:
        """Get the file extension."""
        return self.path.suffix.lower()
    
    def is_processed(self) -> bool:
        """Check if the file has been successfully processed."""
        return self.processing_status == ProcessingStatus.COMPLETED
    
    def has_error(self) -> bool:
        """Check if the file processing encountered an error."""
        return self.processing_status == ProcessingStatus.FAILED
    
    def mark_as_processed(self) -> None:
        """Mark the file as successfully processed."""
        self.processing_status = ProcessingStatus.COMPLETED
        self.error_message = None
    
    def mark_as_failed(self, error_message: str) -> None:
        """Mark the file as failed with an error message."""
        self.processing_status = ProcessingStatus.FAILED
        self.error_message = error_message


@dataclass
class ProcessingResult:
    """
    Result of processing a file or operation.
    
    This dataclass encapsulates the outcome of any processing operation,
    including success/failure status, extracted data, and any errors encountered.
    """
    success: bool
    operation: str
    file_path: Optional[Path] = None
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    processing_time_seconds: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate processing result after initialization."""
        if self.processing_time_seconds < 0:
            self.processing_time_seconds = 0.0
    
    def add_error(self, error_message: str) -> None:
        """Add an error message to the result."""
        self.errors.append(error_message)
        self.success = False
    
    def add_warning(self, warning_message: str) -> None:
        """Add a warning message to the result."""
        self.warnings.append(warning_message)
    
    def has_errors(self) -> bool:
        """Check if the result contains any errors."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if the result contains any warnings."""
        return len(self.warnings) > 0
    
    def get_summary(self) -> str:
        """Get a summary string of the processing result."""
        status = "SUCCESS" if self.success else "FAILED"
        error_count = len(self.errors)
        warning_count = len(self.warnings)
        
        summary = f"{self.operation}: {status}"
        if error_count > 0:
            summary += f" ({error_count} errors)"
        if warning_count > 0:
            summary += f" ({warning_count} warnings)"
        
        return summary


@dataclass
class ModeRecommendation:
    """
    Recommendation for operation mode based on available files.
    
    This dataclass contains the system's recommendation for which operation mode
    to use based on the analysis of available project files.
    """
    recommended_mode: OperationMode
    confidence_score: float
    reasoning: str
    available_documents: List[DocumentType] = field(default_factory=list)
    missing_documents: List[DocumentType] = field(default_factory=list)
    file_quality_scores: Dict[DocumentType, float] = field(default_factory=dict)
    alternative_modes: List[OperationMode] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Validate mode recommendation after initialization."""
        # Ensure confidence score is between 0 and 1
        if self.confidence_score < 0.0:
            self.confidence_score = 0.0
        elif self.confidence_score > 1.0:
            self.confidence_score = 1.0
        
        # Ensure file quality scores are between 0 and 1
        for doc_type, score in self.file_quality_scores.items():
            if score < 0.0:
                self.file_quality_scores[doc_type] = 0.0
            elif score > 1.0:
                self.file_quality_scores[doc_type] = 1.0
    
    @property
    def confidence_percentage(self) -> int:
        """Get confidence score as a percentage."""
        return int(self.confidence_score * 100)
    
    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if the recommendation has high confidence."""
        return self.confidence_score >= threshold
    
    def _quality_label(self, score: float) -> str:
        """
        Convert a quality score to a descriptive label.
        
        Args:
            score: Quality score between 0.0 and 1.0
            
        Returns:
            Quality label string
        """
        if score > 0.90:
            return "Excellent"
        elif score >= 0.75:
            return "Good"
        elif score >= 0.60:
            return "Fair"
        else:
            return "Poor"
    
    def get_quality_summary(self) -> Dict[str, str]:
        """Get a summary of file quality scores as descriptive strings."""
        summary = {}
        for doc_type, score in self.file_quality_scores.items():
            summary[doc_type.value] = self._quality_label(score)
        
        return summary


@dataclass
class ProjectStatus:
    """
    Overall project status and health metrics.
    
    This dataclass represents the consolidated status of a project based on
    analysis of all available project documents and data.
    """
    project_name: str
    analysis_timestamp: datetime
    overall_health_score: float
    total_risks: int = 0
    high_priority_risks: int = 0
    total_deliverables: int = 0
    completed_deliverables: int = 0
    total_milestones: int = 0
    completed_milestones: int = 0
    overdue_milestones: int = 0
    total_stakeholders: int = 0
    key_stakeholder_engagement: float = 0.0
    schedule_variance_days: int = 0
    budget_variance_percentage: float = 0.0
    quality_metrics: Dict[str, float] = field(default_factory=dict)
    critical_issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    data_sources: List[str] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Validate project status after initialization."""
        # Ensure health score is between 0 and 1
        if self.overall_health_score < 0.0:
            self.overall_health_score = 0.0
        elif self.overall_health_score > 1.0:
            self.overall_health_score = 1.0
        
        # Ensure stakeholder engagement is between 0 and 1
        if self.key_stakeholder_engagement < 0.0:
            self.key_stakeholder_engagement = 0.0
        elif self.key_stakeholder_engagement > 1.0:
            self.key_stakeholder_engagement = 1.0
        
        # Ensure counts are non-negative
        for attr in ['total_risks', 'high_priority_risks', 'total_deliverables', 
                     'completed_deliverables', 'total_milestones', 'completed_milestones',
                     'overdue_milestones', 'total_stakeholders']:
            value = getattr(self, attr)
            if value < 0:
                setattr(self, attr, 0)
    
    @property
    def health_percentage(self) -> int:
        """Get overall health score as a percentage."""
        return int(self.overall_health_score * 100)
    
    @property
    def deliverable_completion_rate(self) -> float:
        """Calculate deliverable completion rate."""
        if self.total_deliverables == 0:
            return 0.0
        return self.completed_deliverables / self.total_deliverables
    
    @property
    def milestone_completion_rate(self) -> float:
        """Calculate milestone completion rate."""
        if self.total_milestones == 0:
            return 0.0
        return self.completed_milestones / self.total_milestones
    
    @property
    def risk_severity_ratio(self) -> float:
        """Calculate ratio of high priority risks to total risks."""
        if self.total_risks == 0:
            return 0.0
        return self.high_priority_risks / self.total_risks
    
    def is_healthy(self, threshold: float = 0.7) -> bool:
        """Check if project is considered healthy based on threshold."""
        return self.overall_health_score >= threshold
    
    def has_critical_issues(self) -> bool:
        """Check if project has critical issues."""
        return len(self.critical_issues) > 0
    
    def get_status_summary(self) -> str:
        """Get a brief status summary string."""
        health_desc = "Healthy" if self.is_healthy() else "At Risk"
        return f"{self.project_name}: {health_desc} ({self.health_percentage}%)"
    
    def add_critical_issue(self, issue: str) -> None:
        """Add a critical issue to the project status."""
        if issue not in self.critical_issues:
            self.critical_issues.append(issue)
    
    def add_recommendation(self, recommendation: str) -> None:
        """Add a recommendation to the project status."""
        if recommendation not in self.recommendations:
            self.recommendations.append(recommendation)