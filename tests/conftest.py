"""
Pytest configuration and shared fixtures for PM Analysis Tool tests.
"""

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

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
from core.models import (
    DocumentType,
    FileFormat,
    FileInfo,
    ModeRecommendation,
    OperationMode,
    ProcessingResult,
    ProcessingStatus,
    ProjectStatus,
)


@pytest.fixture
def sample_file_info():
    """Create a sample FileInfo object for testing."""
    return FileInfo(
        path=Path("test_file.xlsx"),
        format=FileFormat.EXCEL,
        document_type=DocumentType.RISK_REGISTER,
        size_bytes=1024,
        last_modified=datetime(2024, 1, 15, 10, 30, 0),
        is_readable=True,
    )


@pytest.fixture
def sample_processing_result():
    """Create a sample ProcessingResult object for testing."""
    return ProcessingResult(
        success=True,
        operation="file_processing",
        file_path=Path("test_file.xlsx"),
        data={"records": 10, "errors": 0},
        processing_time_seconds=2.5,
    )


@pytest.fixture
def sample_mode_recommendation():
    """Create a sample ModeRecommendation object for testing."""
    return ModeRecommendation(
        recommended_mode=OperationMode.STATUS_ANALYSIS,
        confidence_score=0.85,
        reasoning="All required documents are available with good quality",
        available_documents=[DocumentType.RISK_REGISTER, DocumentType.WBS],
        missing_documents=[DocumentType.STAKEHOLDER_REGISTER],
        file_quality_scores={DocumentType.RISK_REGISTER: 0.95, DocumentType.WBS: 0.8},
    )


@pytest.fixture
def sample_project_status():
    """Create a sample ProjectStatus object for testing."""
    return ProjectStatus(
        project_name="Test Project",
        analysis_timestamp=datetime(2024, 1, 15, 14, 30, 0),
        overall_health_score=0.75,
        total_risks=15,
        high_priority_risks=3,
        total_deliverables=25,
        completed_deliverables=10,
        total_milestones=8,
        completed_milestones=3,
        overdue_milestones=1,
        total_stakeholders=12,
        key_stakeholder_engagement=0.8,
    )


@pytest.fixture
def sample_risk():
    """Create a sample Risk object for testing."""
    return Risk(
        risk_id="RISK-001",
        title="Budget Overrun Risk",
        description="Risk of exceeding project budget due to scope creep",
        category="Financial",
        probability=0.6,
        impact=0.8,
        priority=RiskPriority.HIGH,
        status=RiskStatus.OPEN,
        owner="John Doe",
        identified_date=date(2024, 1, 10),
        mitigation_strategy="Implement strict change control process",
        cost_impact=Decimal("50000.00"),
        schedule_impact_days=14,
    )


@pytest.fixture
def sample_deliverable():
    """Create a sample Deliverable object for testing."""
    return Deliverable(
        deliverable_id="DEL-001",
        name="Requirements Document",
        description="Comprehensive requirements specification",
        wbs_code="1.1.1",
        status=DeliverableStatus.IN_PROGRESS,
        assigned_to="Jane Smith",
        start_date=date(2024, 1, 1),
        due_date=date(2024, 2, 1),
        estimated_effort_hours=40.0,
        completion_percentage=60.0,
        budget_allocated=Decimal("5000.00"),
    )


@pytest.fixture
def sample_milestone():
    """Create a sample Milestone object for testing."""
    return Milestone(
        milestone_id="MS-001",
        name="Requirements Approval",
        description="All requirements approved by stakeholders",
        target_date=date(2024, 2, 15),
        status=MilestoneStatus.UPCOMING,
        milestone_type="Approval",
        owner="Project Manager",
        approval_required=True,
        approver="Sponsor",
    )


@pytest.fixture
def sample_stakeholder():
    """Create a sample Stakeholder object for testing."""
    return Stakeholder(
        stakeholder_id="STK-001",
        name="Alice Johnson",
        role="Project Sponsor",
        organization="ABC Corp",
        email="alice.johnson@example.com",
        phone="+1-555-0123",
        influence=StakeholderInfluence.VERY_HIGH,
        interest=StakeholderInterest.HIGH,
        is_decision_maker=True,
        is_sponsor=True,
        engagement_strategy="Weekly status meetings and monthly reviews",
    )
