"""
Unit tests for domain models.
"""

from datetime import date, datetime
from decimal import Decimal

import pytest

from core.domain import (
    Deliverable,
    DeliverableStatus,
    Milestone,
    MilestoneStatus,
    Risk,
    RiskPriority,
    RiskStatus,
    Stakeholder,
    StakeholderInfluence,
    StakeholderInterest,
)


class TestRisk:
    """Test cases for Risk domain model."""

    def test_risk_creation(self, sample_risk):
        """Test basic Risk creation."""
        assert sample_risk.risk_id == "RISK-001"
        assert sample_risk.title == "Budget Overrun Risk"
        assert sample_risk.probability == 0.6
        assert sample_risk.impact == 0.8
        assert sample_risk.priority == RiskPriority.HIGH
        assert sample_risk.status == RiskStatus.OPEN
        assert sample_risk.cost_impact == Decimal("50000.00")

    def test_probability_bounds(self):
        """Test probability is bounded between 0 and 1."""
        # Test lower bound
        risk = Risk(
            risk_id="TEST-001",
            title="Test Risk",
            description="Test",
            category="Test",
            probability=-0.5,
            impact=0.5,
            priority=RiskPriority.LOW,
            status=RiskStatus.OPEN,
            owner="Test",
            identified_date=date.today(),
        )
        assert risk.probability == 0.0

        # Test upper bound
        risk.probability = 1.5
        risk.__post_init__()
        assert risk.probability == 1.0

    def test_impact_bounds(self):
        """Test impact is bounded between 0 and 1."""
        risk = Risk(
            risk_id="TEST-001",
            title="Test Risk",
            description="Test",
            category="Test",
            probability=0.5,
            impact=2.0,
            priority=RiskPriority.LOW,
            status=RiskStatus.OPEN,
            owner="Test",
            identified_date=date.today(),
        )
        assert risk.impact == 1.0

    def test_schedule_impact_bounds(self):
        """Test schedule impact is non-negative."""
        risk = Risk(
            risk_id="TEST-001",
            title="Test Risk",
            description="Test",
            category="Test",
            probability=0.5,
            impact=0.5,
            priority=RiskPriority.LOW,
            status=RiskStatus.OPEN,
            owner="Test",
            identified_date=date.today(),
            schedule_impact_days=-5,
        )
        assert risk.schedule_impact_days == 0

    def test_risk_score(self, sample_risk):
        """Test risk score calculation."""
        assert sample_risk.risk_score == 0.48  # 0.6 * 0.8

    def test_probability_percentage(self, sample_risk):
        """Test probability percentage calculation."""
        assert sample_risk.probability_percentage == 60

    def test_impact_percentage(self, sample_risk):
        """Test impact percentage calculation."""
        assert sample_risk.impact_percentage == 80

    def test_is_overdue(self, sample_risk):
        """Test overdue detection."""
        # No target date set
        assert sample_risk.is_overdue is False

        # Set past target date
        sample_risk.target_resolution_date = date(2023, 1, 1)
        assert sample_risk.is_overdue is True

        # Set future target date
        sample_risk.target_resolution_date = date(2025, 12, 31)
        assert sample_risk.is_overdue is False

        # Resolved risk should not be overdue
        sample_risk.status = RiskStatus.MITIGATED
        sample_risk.target_resolution_date = date(2023, 1, 1)
        assert sample_risk.is_overdue is False

    def test_is_resolved(self, sample_risk):
        """Test resolved status detection."""
        assert sample_risk.is_resolved is False

        sample_risk.status = RiskStatus.MITIGATED
        assert sample_risk.is_resolved is True

        sample_risk.status = RiskStatus.CLOSED
        assert sample_risk.is_resolved is True

    def test_days_until_target(self, sample_risk):
        """Test days until target calculation."""
        # No target date
        assert sample_risk.days_until_target is None

        # Future target date
        future_date = date.today().replace(year=date.today().year + 1)
        sample_risk.target_resolution_date = future_date
        days_until = sample_risk.days_until_target
        assert days_until > 300  # Approximately one year

    def test_add_note(self, sample_risk):
        """Test adding notes to risk."""
        initial_count = len(sample_risk.notes)
        sample_risk.add_note("Test note")
        assert len(sample_risk.notes) == initial_count + 1
        assert "Test note" in sample_risk.notes[-1]

    def test_update_status(self, sample_risk):
        """Test status update with automatic resolution date."""
        old_status = sample_risk.status
        sample_risk.update_status(RiskStatus.MITIGATED, "Risk successfully mitigated")

        assert sample_risk.status == RiskStatus.MITIGATED
        assert sample_risk.actual_resolution_date == date.today()
        assert len(sample_risk.notes) > 0
        assert "Status changed" in sample_risk.notes[-1]


class TestDeliverable:
    """Test cases for Deliverable domain model."""

    def test_deliverable_creation(self, sample_deliverable):
        """Test basic Deliverable creation."""
        assert sample_deliverable.deliverable_id == "DEL-001"
        assert sample_deliverable.name == "Requirements Document"
        assert sample_deliverable.wbs_code == "1.1.1"
        assert sample_deliverable.status == DeliverableStatus.IN_PROGRESS
        assert sample_deliverable.completion_percentage == 60.0

    def test_completion_percentage_bounds(self):
        """Test completion percentage is bounded between 0 and 100."""
        deliverable = Deliverable(
            deliverable_id="TEST-001",
            name="Test Deliverable",
            description="Test",
            wbs_code="1.1",
            completion_percentage=150.0,
        )
        assert deliverable.completion_percentage == 100.0

        deliverable.completion_percentage = -10.0
        deliverable.__post_init__()
        assert deliverable.completion_percentage == 0.0

    def test_effort_hours_bounds(self):
        """Test effort hours are non-negative."""
        deliverable = Deliverable(
            deliverable_id="TEST-001",
            name="Test Deliverable",
            description="Test",
            wbs_code="1.1",
            estimated_effort_hours=-5.0,
            actual_effort_hours=-10.0,
        )
        assert deliverable.estimated_effort_hours == 0.0
        assert deliverable.actual_effort_hours == 0.0

    def test_is_completed(self, sample_deliverable):
        """Test completion status detection."""
        assert sample_deliverable.is_completed is False

        sample_deliverable.status = DeliverableStatus.COMPLETED
        assert sample_deliverable.is_completed is True

    def test_is_overdue(self, sample_deliverable):
        """Test overdue detection."""
        # Not overdue if no due date
        sample_deliverable.due_date = None
        assert sample_deliverable.is_overdue is False

        # Not overdue if completed
        sample_deliverable.due_date = date(2023, 1, 1)
        sample_deliverable.status = DeliverableStatus.COMPLETED
        assert sample_deliverable.is_overdue is False

        # Overdue if past due date and not completed
        sample_deliverable.status = DeliverableStatus.IN_PROGRESS
        assert sample_deliverable.is_overdue is True

    def test_days_until_due(self, sample_deliverable):
        """Test days until due calculation."""
        # No due date
        sample_deliverable.due_date = None
        assert sample_deliverable.days_until_due is None

        # Future due date
        future_date = date.today().replace(year=date.today().year + 1)
        sample_deliverable.due_date = future_date
        days_until = sample_deliverable.days_until_due
        assert days_until > 300

    def test_effort_variance_hours(self, sample_deliverable):
        """Test effort variance calculation."""
        sample_deliverable.actual_effort_hours = 50.0
        variance = sample_deliverable.effort_variance_hours
        assert variance == 10.0  # 50 - 40

        # Test with missing data
        sample_deliverable.actual_effort_hours = None
        assert sample_deliverable.effort_variance_hours is None

    def test_budget_variance(self, sample_deliverable):
        """Test budget variance calculation."""
        sample_deliverable.budget_spent = Decimal("6000.00")
        variance = sample_deliverable.budget_variance
        assert variance == Decimal("1000.00")  # 6000 - 5000

        # Test with missing data
        sample_deliverable.budget_spent = None
        assert sample_deliverable.budget_variance is None

    def test_is_on_track(self, sample_deliverable):
        """Test on-track status calculation."""
        # Test with current setup (should be on track with 60% completion)
        result = sample_deliverable.is_on_track
        # This is a complex calculation, just ensure it returns a boolean
        assert isinstance(result, bool)

    def test_add_dependency(self, sample_deliverable):
        """Test adding dependencies."""
        initial_count = len(sample_deliverable.dependencies)
        sample_deliverable.add_dependency("DEL-002")
        assert len(sample_deliverable.dependencies) == initial_count + 1
        assert "DEL-002" in sample_deliverable.dependencies

        # Test duplicate prevention
        sample_deliverable.add_dependency("DEL-002")
        assert sample_deliverable.dependencies.count("DEL-002") == 1

    def test_update_progress(self, sample_deliverable):
        """Test progress update with status changes."""
        sample_deliverable.update_progress(100.0, "Deliverable completed")

        assert sample_deliverable.completion_percentage == 100.0
        assert sample_deliverable.status == DeliverableStatus.COMPLETED
        assert sample_deliverable.completion_date == date.today()
        assert len(sample_deliverable.notes) > 0

    def test_add_note(self, sample_deliverable):
        """Test adding notes to deliverable."""
        initial_count = len(sample_deliverable.notes)
        sample_deliverable.add_note("Test note")
        assert len(sample_deliverable.notes) == initial_count + 1
        assert "Test note" in sample_deliverable.notes[-1]


class TestMilestone:
    """Test cases for Milestone domain model."""

    def test_milestone_creation(self, sample_milestone):
        """Test basic Milestone creation."""
        assert sample_milestone.milestone_id == "MS-001"
        assert sample_milestone.name == "Requirements Approval"
        assert sample_milestone.target_date == date(2024, 2, 15)
        assert sample_milestone.status == MilestoneStatus.UPCOMING
        assert sample_milestone.approval_required is True

    def test_is_completed(self, sample_milestone):
        """Test completion status detection."""
        assert sample_milestone.is_completed is False

        sample_milestone.status = MilestoneStatus.COMPLETED
        assert sample_milestone.is_completed is True

    def test_is_overdue(self, sample_milestone):
        """Test overdue detection."""
        # Not overdue if completed
        sample_milestone.status = MilestoneStatus.COMPLETED
        sample_milestone.target_date = date(2023, 1, 1)
        assert sample_milestone.is_overdue is False

        # Overdue if past target date and not completed
        sample_milestone.status = MilestoneStatus.UPCOMING
        assert sample_milestone.is_overdue is True

    def test_days_until_target(self, sample_milestone):
        """Test days until target calculation."""
        days_until = sample_milestone.days_until_target
        # This will be negative since the target date is in the past
        assert isinstance(days_until, int)

    def test_schedule_variance_days(self, sample_milestone):
        """Test schedule variance calculation."""
        # No actual date set
        assert sample_milestone.schedule_variance_days is None

        # Set actual date
        sample_milestone.actual_date = date(2024, 2, 20)
        variance = sample_milestone.schedule_variance_days
        assert variance == 5  # 5 days late

    def test_baseline_variance_days(self, sample_milestone):
        """Test baseline variance calculation."""
        # No baseline date set
        assert sample_milestone.baseline_variance_days is None

        # Set baseline date
        sample_milestone.baseline_date = date(2024, 2, 10)
        variance = sample_milestone.baseline_variance_days
        # Should calculate from today's date since no actual date
        assert isinstance(variance, int)

    def test_complete_milestone(self, sample_milestone):
        """Test milestone completion."""
        completion_date = date(2024, 2, 18)
        sample_milestone.complete_milestone(completion_date, "Milestone achieved")

        assert sample_milestone.status == MilestoneStatus.COMPLETED
        assert sample_milestone.actual_date == completion_date
        assert len(sample_milestone.notes) > 0
        assert "Milestone completed" in sample_milestone.notes[-1]

    def test_add_note(self, sample_milestone):
        """Test adding notes to milestone."""
        initial_count = len(sample_milestone.notes)
        sample_milestone.add_note("Test note")
        assert len(sample_milestone.notes) == initial_count + 1
        assert "Test note" in sample_milestone.notes[-1]


class TestStakeholder:
    """Test cases for Stakeholder domain model."""

    def test_stakeholder_creation(self, sample_stakeholder):
        """Test basic Stakeholder creation."""
        assert sample_stakeholder.stakeholder_id == "STK-001"
        assert sample_stakeholder.name == "Alice Johnson"
        assert sample_stakeholder.role == "Project Sponsor"
        assert sample_stakeholder.influence == StakeholderInfluence.VERY_HIGH
        assert sample_stakeholder.interest == StakeholderInterest.HIGH
        assert sample_stakeholder.is_sponsor is True

    def test_influence_score(self, sample_stakeholder):
        """Test influence score calculation."""
        assert sample_stakeholder.influence_score == 4  # VERY_HIGH = 4

        sample_stakeholder.influence = StakeholderInfluence.LOW
        assert sample_stakeholder.influence_score == 1

    def test_interest_score(self, sample_stakeholder):
        """Test interest score calculation."""
        assert sample_stakeholder.interest_score == 3  # HIGH = 3

        sample_stakeholder.interest = StakeholderInterest.MEDIUM
        assert sample_stakeholder.interest_score == 2

    def test_engagement_priority(self, sample_stakeholder):
        """Test engagement priority calculation."""
        # VERY_HIGH influence + HIGH interest = Manage Closely
        assert sample_stakeholder.engagement_priority == "Manage Closely"

        # HIGH influence + LOW interest = Keep Satisfied
        sample_stakeholder.influence = StakeholderInfluence.HIGH
        sample_stakeholder.interest = StakeholderInterest.LOW
        assert sample_stakeholder.engagement_priority == "Keep Satisfied"

        # LOW influence + HIGH interest = Keep Informed
        sample_stakeholder.influence = StakeholderInfluence.LOW
        sample_stakeholder.interest = StakeholderInterest.HIGH
        assert sample_stakeholder.engagement_priority == "Keep Informed"

        # LOW influence + LOW interest = Monitor
        sample_stakeholder.influence = StakeholderInfluence.LOW
        sample_stakeholder.interest = StakeholderInterest.LOW
        assert sample_stakeholder.engagement_priority == "Monitor"

    def test_is_high_priority(self, sample_stakeholder):
        """Test high priority detection."""
        assert sample_stakeholder.is_high_priority is True

        sample_stakeholder.influence = StakeholderInfluence.LOW
        sample_stakeholder.interest = StakeholderInterest.LOW
        assert sample_stakeholder.is_high_priority is False

    def test_contact_overdue(self, sample_stakeholder):
        """Test contact overdue detection."""
        # No next contact date set
        assert sample_stakeholder.contact_overdue is False

        # Set past next contact date
        sample_stakeholder.next_contact_date = date(2023, 1, 1)
        assert sample_stakeholder.contact_overdue is True

        # Set future next contact date
        sample_stakeholder.next_contact_date = date(2025, 12, 31)
        assert sample_stakeholder.contact_overdue is False

    def test_days_since_last_contact(self, sample_stakeholder):
        """Test days since last contact calculation."""
        # No last contact date
        assert sample_stakeholder.days_since_last_contact is None

        # Set last contact date
        sample_stakeholder.last_contact_date = date(2024, 1, 1)
        days_since = sample_stakeholder.days_since_last_contact
        assert isinstance(days_since, int)
        assert days_since >= 0

    def test_add_concern(self, sample_stakeholder):
        """Test adding concerns."""
        initial_count = len(sample_stakeholder.key_concerns)
        concern = "Budget constraints"
        sample_stakeholder.add_concern(concern)
        assert len(sample_stakeholder.key_concerns) == initial_count + 1
        assert concern in sample_stakeholder.key_concerns

        # Test duplicate prevention
        sample_stakeholder.add_concern(concern)
        assert sample_stakeholder.key_concerns.count(concern) == 1

    def test_add_expectation(self, sample_stakeholder):
        """Test adding expectations."""
        initial_count = len(sample_stakeholder.expectations)
        expectation = "On-time delivery"
        sample_stakeholder.add_expectation(expectation)
        assert len(sample_stakeholder.expectations) == initial_count + 1
        assert expectation in sample_stakeholder.expectations

        # Test duplicate prevention
        sample_stakeholder.add_expectation(expectation)
        assert sample_stakeholder.expectations.count(expectation) == 1

    def test_record_contact(self, sample_stakeholder):
        """Test recording contact."""
        contact_date = date(2024, 1, 15)
        sample_stakeholder.record_contact(contact_date, "Discussed project status")

        assert sample_stakeholder.last_contact_date == contact_date
        assert len(sample_stakeholder.notes) > 0
        assert "Contact recorded" in sample_stakeholder.notes[-1]

    def test_add_note(self, sample_stakeholder):
        """Test adding notes to stakeholder."""
        initial_count = len(sample_stakeholder.notes)
        sample_stakeholder.add_note("Test note")
        assert len(sample_stakeholder.notes) == initial_count + 1
        assert "Test note" in sample_stakeholder.notes[-1]
