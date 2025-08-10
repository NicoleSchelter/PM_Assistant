"""
Domain-specific models for PM Analysis Tool.

This module defines the business domain objects that represent core project
management concepts like risks, deliverables, milestones, and stakeholders.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class RiskPriority(Enum):
    """Risk priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskStatus(Enum):
    """Risk status values."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    MITIGATED = "mitigated"
    CLOSED = "closed"
    ACCEPTED = "accepted"


class DeliverableStatus(Enum):
    """Deliverable status values."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"


class MilestoneStatus(Enum):
    """Milestone status values."""

    UPCOMING = "upcoming"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class StakeholderInfluence(Enum):
    """Stakeholder influence levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class StakeholderInterest(Enum):
    """Stakeholder interest levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class Risk:
    """
    Represents a project risk with all associated metadata.

    This class encapsulates all information about a project risk including
    identification, assessment, mitigation strategies, and current status.
    """

    risk_id: str
    title: str
    description: str
    category: str
    probability: float  # 0.0 to 1.0
    impact: float  # 0.0 to 1.0
    priority: RiskPriority
    status: RiskStatus
    owner: str
    identified_date: date
    mitigation_strategy: str = ""
    contingency_plan: str = ""
    target_resolution_date: Optional[date] = None
    actual_resolution_date: Optional[date] = None
    cost_impact: Optional[Decimal] = None
    schedule_impact_days: Optional[int] = None
    last_updated: datetime = field(default_factory=datetime.now)
    notes: List[str] = field(default_factory=list)
    related_deliverables: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate risk data after initialization."""
        # Ensure probability and impact are between 0 and 1
        if self.probability < 0.0:
            self.probability = 0.0
        elif self.probability > 1.0:
            self.probability = 1.0

        if self.impact < 0.0:
            self.impact = 0.0
        elif self.impact > 1.0:
            self.impact = 1.0

        # Ensure schedule impact is non-negative
        if self.schedule_impact_days is not None and self.schedule_impact_days < 0:
            self.schedule_impact_days = 0

    @property
    def risk_score(self) -> float:
        """Calculate overall risk score (probability × impact)."""
        return self.probability * self.impact

    @property
    def probability_percentage(self) -> int:
        """Get probability as a percentage."""
        return int(self.probability * 100)

    @property
    def impact_percentage(self) -> int:
        """Get impact as a percentage."""
        return int(self.impact * 100)

    @property
    def is_overdue(self) -> bool:
        """Check if risk resolution is overdue."""
        if self.target_resolution_date is None:
            return False
        return (
            self.status in [RiskStatus.OPEN, RiskStatus.IN_PROGRESS]
            and date.today() > self.target_resolution_date
        )

    @property
    def is_resolved(self) -> bool:
        """Check if risk is resolved."""
        return self.status in [RiskStatus.MITIGATED, RiskStatus.CLOSED]

    @property
    def days_until_target(self) -> Optional[int]:
        """Calculate days until target resolution date."""
        if self.target_resolution_date is None:
            return None
        delta = self.target_resolution_date - date.today()
        return delta.days

    def add_note(self, note: str) -> None:
        """Add a note to the risk."""
        self.notes.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M')}: {note}")
        self.last_updated = datetime.now()

    def update_status(self, new_status: RiskStatus, note: str = "") -> None:
        """Update risk status with optional note."""
        old_status = self.status
        self.status = new_status
        self.last_updated = datetime.now()

        status_note = f"Status changed from {old_status.value} to {new_status.value}"
        if note:
            status_note += f": {note}"
        self.add_note(status_note)

        # Set resolution date if risk is being resolved
        if (
            new_status in [RiskStatus.MITIGATED, RiskStatus.CLOSED]
            and self.actual_resolution_date is None
        ):
            self.actual_resolution_date = date.today()


@dataclass
class Deliverable:
    """
    Represents a project deliverable with work breakdown structure information.

    This class encapsulates information about project deliverables including
    their hierarchical structure, dependencies, and completion status.
    """

    deliverable_id: str
    name: str
    description: str
    wbs_code: str
    parent_id: Optional[str] = None
    status: DeliverableStatus = DeliverableStatus.NOT_STARTED
    assigned_to: str = ""
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    completion_date: Optional[date] = None
    estimated_effort_hours: Optional[float] = None
    actual_effort_hours: Optional[float] = None
    completion_percentage: float = 0.0
    dependencies: List[str] = field(default_factory=list)
    deliverable_type: str = ""
    acceptance_criteria: List[str] = field(default_factory=list)
    quality_metrics: Dict[str, Any] = field(default_factory=dict)
    budget_allocated: Optional[Decimal] = None
    budget_spent: Optional[Decimal] = None
    last_updated: datetime = field(default_factory=datetime.now)
    notes: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate deliverable data after initialization."""
        # Ensure completion percentage is between 0 and 100
        if self.completion_percentage < 0.0:
            self.completion_percentage = 0.0
        elif self.completion_percentage > 100.0:
            self.completion_percentage = 100.0

        # Ensure effort hours are non-negative
        if self.estimated_effort_hours is not None and self.estimated_effort_hours < 0:
            self.estimated_effort_hours = 0.0
        if self.actual_effort_hours is not None and self.actual_effort_hours < 0:
            self.actual_effort_hours = 0.0

    @property
    def is_completed(self) -> bool:
        """Check if deliverable is completed."""
        return self.status == DeliverableStatus.COMPLETED

    @property
    def is_overdue(self) -> bool:
        """Check if deliverable is overdue."""
        if self.due_date is None or self.is_completed:
            return False
        return date.today() > self.due_date

    @property
    def days_until_due(self) -> Optional[int]:
        """Calculate days until due date."""
        if self.due_date is None:
            return None
        delta = self.due_date - date.today()
        return delta.days

    @property
    def effort_variance_hours(self) -> Optional[float]:
        """Calculate effort variance (actual - estimated)."""
        if self.estimated_effort_hours is None or self.actual_effort_hours is None:
            return None
        return self.actual_effort_hours - self.estimated_effort_hours

    @property
    def budget_variance(self) -> Optional[Decimal]:
        """Calculate budget variance (spent - allocated)."""
        if self.budget_allocated is None or self.budget_spent is None:
            return None
        return self.budget_spent - self.budget_allocated

    @property
    def is_on_track(self) -> bool:
        """Determine if deliverable is on track based on completion and timeline."""
        if self.due_date is None:
            return True

        days_remaining = self.days_until_due
        if days_remaining is None or days_remaining < 0:
            return self.is_completed

        # Simple heuristic: completion percentage should be proportional to time elapsed
        if self.start_date is None:
            return True

        total_days = (self.due_date - self.start_date).days
        if total_days <= 0:
            return True

        elapsed_days = (date.today() - self.start_date).days
        expected_completion = (elapsed_days / total_days) * 100

        # Allow 10% tolerance
        return self.completion_percentage >= (expected_completion - 10)

    def add_dependency(self, deliverable_id: str) -> None:
        """Add a dependency to this deliverable."""
        if deliverable_id not in self.dependencies:
            self.dependencies.append(deliverable_id)
            self.last_updated = datetime.now()

    def update_progress(self, completion_percentage: float, note: str = "") -> None:
        """Update deliverable progress."""
        old_percentage = self.completion_percentage
        self.completion_percentage = max(0.0, min(100.0, completion_percentage))
        self.last_updated = datetime.now()

        progress_note = f"Progress updated from {old_percentage}% to {self.completion_percentage}%"
        if note:
            progress_note += f": {note}"
        self.add_note(progress_note)

        # Auto-update status based on completion
        if self.completion_percentage == 100.0 and self.status != DeliverableStatus.COMPLETED:
            self.status = DeliverableStatus.COMPLETED
            self.completion_date = date.today()
        elif self.completion_percentage > 0.0 and self.status == DeliverableStatus.NOT_STARTED:
            self.status = DeliverableStatus.IN_PROGRESS

    def add_note(self, note: str) -> None:
        """Add a note to the deliverable."""
        self.notes.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M')}: {note}")


@dataclass
class Milestone:
    """
    Represents a project milestone with timeline information.

    This class encapsulates information about project milestones including
    their dates, dependencies, and completion status.
    """

    milestone_id: str
    name: str
    description: str
    target_date: date
    actual_date: Optional[date] = None
    status: MilestoneStatus = MilestoneStatus.UPCOMING
    milestone_type: str = ""
    owner: str = ""
    dependencies: List[str] = field(default_factory=list)
    related_deliverables: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    approval_required: bool = False
    approver: str = ""
    approval_date: Optional[date] = None
    baseline_date: Optional[date] = None
    last_updated: datetime = field(default_factory=datetime.now)
    notes: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_completed(self) -> bool:
        """Check if milestone is completed."""
        return self.status == MilestoneStatus.COMPLETED

    @property
    def is_overdue(self) -> bool:
        """Check if milestone is overdue."""
        if self.is_completed:
            return False
        return date.today() > self.target_date

    @property
    def days_until_target(self) -> int:
        """Calculate days until target date."""
        delta = self.target_date - date.today()
        return delta.days

    @property
    def schedule_variance_days(self) -> Optional[int]:
        """Calculate schedule variance in days (actual - target)."""
        if self.actual_date is None:
            return None
        delta = self.actual_date - self.target_date
        return delta.days

    @property
    def baseline_variance_days(self) -> Optional[int]:
        """Calculate variance from baseline date."""
        if self.baseline_date is None:
            return None
        current_date = self.actual_date if self.actual_date else date.today()
        delta = current_date - self.baseline_date
        return delta.days

    def complete_milestone(self, completion_date: Optional[date] = None, note: str = "") -> None:
        """Mark milestone as completed."""
        self.status = MilestoneStatus.COMPLETED
        self.actual_date = completion_date or date.today()
        self.last_updated = datetime.now()

        completion_note = f"Milestone completed on {self.actual_date}"
        if note:
            completion_note += f": {note}"
        self.add_note(completion_note)

    def add_note(self, note: str) -> None:
        """Add a note to the milestone."""
        self.notes.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M')}: {note}")


@dataclass
class Stakeholder:
    """
    Represents a project stakeholder with contact and engagement information.

    This class encapsulates information about project stakeholders including
    their roles, contact details, influence levels, and engagement status.
    """

    stakeholder_id: str
    name: str
    role: str
    organization: str = ""
    email: str = ""
    phone: str = ""
    influence: StakeholderInfluence = StakeholderInfluence.MEDIUM
    interest: StakeholderInterest = StakeholderInterest.MEDIUM
    engagement_strategy: str = ""
    communication_frequency: str = ""
    preferred_communication_method: str = ""
    current_sentiment: str = ""  # e.g., "supportive", "neutral", "resistant"
    key_concerns: List[str] = field(default_factory=list)
    expectations: List[str] = field(default_factory=list)
    deliverables_interested_in: List[str] = field(default_factory=list)
    last_contact_date: Optional[date] = None
    next_contact_date: Optional[date] = None
    is_decision_maker: bool = False
    is_sponsor: bool = False
    is_end_user: bool = False
    escalation_path: str = ""
    last_updated: datetime = field(default_factory=datetime.now)
    notes: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)

    @property
    def influence_score(self) -> int:
        """Get numerical influence score (1-4)."""
        influence_map = {
            StakeholderInfluence.LOW: 1,
            StakeholderInfluence.MEDIUM: 2,
            StakeholderInfluence.HIGH: 3,
            StakeholderInfluence.VERY_HIGH: 4,
        }
        return influence_map[self.influence]

    @property
    def interest_score(self) -> int:
        """Get numerical interest score (1-4)."""
        interest_map = {
            StakeholderInterest.LOW: 1,
            StakeholderInterest.MEDIUM: 2,
            StakeholderInterest.HIGH: 3,
            StakeholderInterest.VERY_HIGH: 4,
        }
        return interest_map[self.interest]

    @property
    def engagement_priority(self) -> str:
        """Calculate engagement priority based on influence and interest."""
        if self.influence_score >= 3 and self.interest_score >= 3:
            return "Manage Closely"
        elif self.influence_score >= 3 and self.interest_score < 3:
            return "Keep Satisfied"
        elif self.influence_score < 3 and self.interest_score >= 3:
            return "Keep Informed"
        else:
            return "Monitor"

    @property
    def is_high_priority(self) -> bool:
        """Check if stakeholder is high priority for engagement."""
        return self.engagement_priority in ["Manage Closely", "Keep Satisfied"]

    @property
    def contact_overdue(self) -> bool:
        """Check if stakeholder contact is overdue."""
        if self.next_contact_date is None:
            return False
        return date.today() > self.next_contact_date

    @property
    def days_since_last_contact(self) -> Optional[int]:
        """Calculate days since last contact."""
        if self.last_contact_date is None:
            return None
        delta = date.today() - self.last_contact_date
        return delta.days

    def add_concern(self, concern: str) -> None:
        """Add a concern to the stakeholder."""
        if concern not in self.key_concerns:
            self.key_concerns.append(concern)
            self.last_updated = datetime.now()

    def add_expectation(self, expectation: str) -> None:
        """Add an expectation to the stakeholder."""
        if expectation not in self.expectations:
            self.expectations.append(expectation)
            self.last_updated = datetime.now()

    def record_contact(self, contact_date: Optional[date] = None, note: str = "") -> None:
        """Record a contact with the stakeholder."""
        self.last_contact_date = contact_date or date.today()
        self.last_updated = datetime.now()

        contact_note = f"Contact recorded for {self.last_contact_date}"
        if note:
            contact_note += f": {note}"
        self.add_note(contact_note)

    def add_note(self, note: str) -> None:
        """Add a note to the stakeholder."""
        self.notes.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M')}: {note}")
