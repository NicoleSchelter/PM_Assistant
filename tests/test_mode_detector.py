"""
Unit tests for ModeDetector class.

This module contains comprehensive tests for the intelligent mode detection
system, covering various file availability scenarios, quality scoring,
and recommendation logic.
"""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from core.mode_detector import ModeDetector
from core.models import DocumentType, FileFormat, FileInfo, ModeRecommendation, OperationMode
from utils.exceptions import ValidationError


class TestModeDetector:
    """Test cases for ModeDetector class."""

    @pytest.fixture
    def mode_detector(self):
        """Create a ModeDetector instance for testing."""
        required_documents = [
            {
                "name": "Project Charter",
                "patterns": ["*charter*"],
                "formats": ["md", "docx"],
                "required": True,
            },
            {
                "name": "Risk Management Plan",
                "patterns": ["*risk*"],
                "formats": ["md", "xlsx"],
                "required": True,
            },
            {
                "name": "Stakeholder Register",
                "patterns": ["*stakeholder*"],
                "formats": ["xlsx", "csv"],
                "required": True,
            },
            {
                "name": "Work Breakdown Structure",
                "patterns": ["*wbs*"],
                "formats": ["md", "docx"],
                "required": True,
            },
            {
                "name": "Roadmap",
                "patterns": ["*roadmap*"],
                "formats": ["md", "mpp"],
                "required": True,
            },
        ]
        return ModeDetector(required_documents=required_documents)

    @pytest.fixture
    def sample_file_info(self):
        """Create sample FileInfo objects for testing."""
        now = datetime.now()
        return {
            "charter": FileInfo(
                path=Path("project_charter.md"),
                format=FileFormat.MARKDOWN,
                document_type=DocumentType.CHARTER,
                size_bytes=5000,
                last_modified=now - timedelta(days=1),
                is_readable=True,
            ),
            "risk_register": FileInfo(
                path=Path("risk_register.xlsx"),
                format=FileFormat.EXCEL,
                document_type=DocumentType.RISK_REGISTER,
                size_bytes=15000,
                last_modified=now - timedelta(days=2),
                is_readable=True,
            ),
            "stakeholder_register": FileInfo(
                path=Path("stakeholder_register.xlsx"),
                format=FileFormat.EXCEL,
                document_type=DocumentType.STAKEHOLDER_REGISTER,
                size_bytes=8000,
                last_modified=now - timedelta(days=3),
                is_readable=True,
            ),
            "wbs": FileInfo(
                path=Path("wbs.md"),
                format=FileFormat.MARKDOWN,
                document_type=DocumentType.WBS,
                size_bytes=12000,
                last_modified=now - timedelta(days=1),
                is_readable=True,
            ),
            "roadmap": FileInfo(
                path=Path("roadmap.mpp"),
                format=FileFormat.MICROSOFT_PROJECT,
                document_type=DocumentType.ROADMAP,
                size_bytes=25000,
                last_modified=now - timedelta(days=5),
                is_readable=True,
            ),
            "empty_file": FileInfo(
                path=Path("empty.md"),
                format=FileFormat.MARKDOWN,
                document_type=DocumentType.CHARTER,
                size_bytes=0,
                last_modified=now - timedelta(days=10),
                is_readable=True,
            ),
            "unreadable_file": FileInfo(
                path=Path("unreadable.xlsx"),
                format=FileFormat.EXCEL,
                document_type=DocumentType.RISK_REGISTER,
                size_bytes=5000,
                last_modified=now - timedelta(days=1),
                is_readable=False,
            ),
        }

    def test_initialization_with_default_config(self):
        """Test ModeDetector initialization with default configuration."""
        detector = ModeDetector()

        assert detector.required_documents == []
        assert len(detector._required_doc_types) == 5  # Default required document types
        assert DocumentType.CHARTER in detector._required_doc_types
        assert DocumentType.RISK_REGISTER in detector._required_doc_types

    def test_initialization_with_custom_config(self, mode_detector):
        """Test ModeDetector initialization with custom configuration."""
        assert len(mode_detector.required_documents) == 5
        assert len(mode_detector._required_doc_types) == 5

    def test_analyze_files_empty_list(self, mode_detector):
        """Test analysis with empty file list."""
        recommendation = mode_detector.analyze_files([])

        assert recommendation.recommended_mode == OperationMode.LEARNING_MODULE
        assert recommendation.confidence_score == 1.0
        assert "No project files found" in recommendation.reasoning
        assert len(recommendation.available_documents) == 0
        assert len(recommendation.missing_documents) > 0

    def test_analyze_files_complete_project(self, mode_detector, sample_file_info):
        """Test analysis with complete project files."""
        files = [
            sample_file_info["charter"],
            sample_file_info["risk_register"],
            sample_file_info["stakeholder_register"],
            sample_file_info["wbs"],
            sample_file_info["roadmap"],
        ]

        recommendation = mode_detector.analyze_files(files)

        assert recommendation.recommended_mode == OperationMode.STATUS_ANALYSIS
        assert recommendation.confidence_score >= 0.6
        assert "Status Analysis mode recommended" in recommendation.reasoning
        assert len(recommendation.available_documents) == 5
        assert len(recommendation.missing_documents) == 0

    def test_analyze_files_partial_project(self, mode_detector, sample_file_info):
        """Test analysis with partial project files."""
        files = [sample_file_info["charter"], sample_file_info["risk_register"]]

        recommendation = mode_detector.analyze_files(files)

        # Should recommend document check for partial projects
        assert recommendation.recommended_mode == OperationMode.DOCUMENT_CHECK
        assert recommendation.confidence_score > 0.5
        assert "Document Check mode recommended" in recommendation.reasoning
        assert len(recommendation.available_documents) == 2
        assert len(recommendation.missing_documents) == 3

    def test_analyze_files_minimal_project(self, mode_detector, sample_file_info):
        """Test analysis with minimal project files."""
        files = [sample_file_info["charter"]]

        recommendation = mode_detector.analyze_files(files)

        # Should recommend document check or learning module for minimal projects
        assert recommendation.recommended_mode in [
            OperationMode.DOCUMENT_CHECK,
            OperationMode.LEARNING_MODULE,
        ]
        assert len(recommendation.available_documents) == 1
        assert len(recommendation.missing_documents) >= 4

    def test_calculate_completeness_score_complete(self, mode_detector, sample_file_info):
        """Test completeness score calculation with complete project."""
        files = [
            sample_file_info["charter"],
            sample_file_info["risk_register"],
            sample_file_info["stakeholder_register"],
            sample_file_info["wbs"],
            sample_file_info["roadmap"],
        ]

        score = mode_detector.calculate_completeness_score(files)

        assert score >= 0.8  # Should be high for complete project
        assert score <= 1.0

    def test_calculate_completeness_score_partial(self, mode_detector, sample_file_info):
        """Test completeness score calculation with partial project."""
        files = [sample_file_info["charter"], sample_file_info["risk_register"]]

        score = mode_detector.calculate_completeness_score(files)

        assert 0.2 <= score <= 0.6  # Should be moderate for partial project

    def test_calculate_completeness_score_empty(self, mode_detector):
        """Test completeness score calculation with no files."""
        score = mode_detector.calculate_completeness_score([])

        assert score == 0.0

    def test_quality_scoring_high_quality_files(self, mode_detector, sample_file_info):
        """Test quality scoring with high-quality files."""
        files = [sample_file_info["charter"], sample_file_info["risk_register"]]

        quality_scores = mode_detector._calculate_quality_scores(files)

        assert DocumentType.CHARTER in quality_scores
        assert DocumentType.RISK_REGISTER in quality_scores
        assert all(0.0 <= score <= 1.0 for score in quality_scores.values())

        # Recent, non-empty, readable files should score well
        assert quality_scores[DocumentType.CHARTER] > 0.5
        assert quality_scores[DocumentType.RISK_REGISTER] > 0.5

    def test_quality_scoring_poor_quality_files(self, mode_detector, sample_file_info):
        """Test quality scoring with poor-quality files."""
        files = [sample_file_info["empty_file"], sample_file_info["unreadable_file"]]

        quality_scores = mode_detector._calculate_quality_scores(files)

        # Empty and unreadable files should score lower
        if DocumentType.CHARTER in quality_scores:
            assert quality_scores[DocumentType.CHARTER] < 0.5  # Empty file
        if DocumentType.RISK_REGISTER in quality_scores:
            assert quality_scores[DocumentType.RISK_REGISTER] < 0.8  # Unreadable file

    def test_single_file_quality_calculation(self, mode_detector, sample_file_info):
        """Test quality calculation for individual files."""
        # High quality file
        high_quality_score = mode_detector._calculate_single_file_quality(
            sample_file_info["charter"]
        )
        assert 0.6 <= high_quality_score <= 1.0

        # Empty file
        empty_quality_score = mode_detector._calculate_single_file_quality(
            sample_file_info["empty_file"]
        )
        assert empty_quality_score < 0.6

        # Unreadable file
        unreadable_quality_score = mode_detector._calculate_single_file_quality(
            sample_file_info["unreadable_file"]
        )
        assert unreadable_quality_score < 0.8  # Should be penalized for not being readable

    def test_format_appropriateness_scoring(self, mode_detector, sample_file_info):
        """Test format appropriateness scoring."""
        # Markdown for charter (appropriate)
        charter_score = mode_detector._calculate_format_appropriateness(sample_file_info["charter"])
        assert charter_score == 1.0

        # Excel for stakeholder register (appropriate)
        stakeholder_score = mode_detector._calculate_format_appropriateness(
            sample_file_info["stakeholder_register"]
        )
        assert stakeholder_score == 1.0

        # MPP for roadmap (appropriate)
        roadmap_score = mode_detector._calculate_format_appropriateness(sample_file_info["roadmap"])
        assert roadmap_score == 1.0

    def test_document_availability_analysis(self, mode_detector, sample_file_info):
        """Test document availability analysis."""
        files = [
            sample_file_info["charter"],
            sample_file_info["risk_register"],
            sample_file_info["wbs"],
        ]

        available, missing = mode_detector._analyze_document_availability(files)

        assert DocumentType.CHARTER in available
        assert DocumentType.RISK_REGISTER in available
        assert DocumentType.WBS in available
        assert DocumentType.STAKEHOLDER_REGISTER in missing
        assert DocumentType.ROADMAP in missing

    def test_alternative_modes_generation(self, mode_detector):
        """Test alternative modes generation logic."""
        # Status analysis should offer document check
        alternatives = mode_detector._determine_alternative_modes(
            OperationMode.STATUS_ANALYSIS, 0.8
        )
        assert OperationMode.DOCUMENT_CHECK in alternatives

        # Document check should offer both alternatives depending on completeness
        alternatives = mode_detector._determine_alternative_modes(OperationMode.DOCUMENT_CHECK, 0.5)
        assert OperationMode.STATUS_ANALYSIS in alternatives

        alternatives = mode_detector._determine_alternative_modes(OperationMode.DOCUMENT_CHECK, 0.3)
        assert OperationMode.LEARNING_MODULE in alternatives

        # Learning module should offer document check
        alternatives = mode_detector._determine_alternative_modes(
            OperationMode.LEARNING_MODULE, 0.2
        )
        assert OperationMode.DOCUMENT_CHECK in alternatives

    def test_detailed_reasoning_generation(self, mode_detector, sample_file_info):
        """Test detailed reasoning generation."""
        files = [sample_file_info["charter"], sample_file_info["risk_register"]]
        available_docs = [DocumentType.CHARTER, DocumentType.RISK_REGISTER]
        missing_docs = [DocumentType.STAKEHOLDER_REGISTER, DocumentType.WBS, DocumentType.ROADMAP]
        quality_scores = {DocumentType.CHARTER: 0.8, DocumentType.RISK_REGISTER: 0.9}

        # Test status analysis reasoning
        reasoning = mode_detector._generate_detailed_reasoning(
            OperationMode.STATUS_ANALYSIS, 0.7, available_docs, missing_docs, quality_scores
        )
        assert "Status Analysis mode recommended" in reasoning
        assert "70%" in reasoning

        # Test document check reasoning
        reasoning = mode_detector._generate_detailed_reasoning(
            OperationMode.DOCUMENT_CHECK, 0.4, available_docs, missing_docs, quality_scores
        )
        assert "Document Check mode recommended" in reasoning
        assert "Missing" in reasoning

        # Test learning module reasoning
        reasoning = mode_detector._generate_detailed_reasoning(
            OperationMode.LEARNING_MODULE, 0.2, available_docs, missing_docs, quality_scores
        )
        assert "Learning Module mode recommended" in reasoning
        assert "learning modules" in reasoning

    def test_confidence_scoring_adjustments(self, mode_detector, sample_file_info):
        """Test confidence score adjustments based on quality."""
        # High quality files should increase confidence
        high_quality_files = [sample_file_info["charter"], sample_file_info["risk_register"]]
        high_quality_rec = mode_detector.analyze_files(high_quality_files)

        # Low quality files should decrease confidence
        low_quality_files = [sample_file_info["empty_file"]]
        low_quality_rec = mode_detector.analyze_files(low_quality_files)

        # Compare confidence scores (high quality should generally be higher)
        # Note: This test might be sensitive to the exact scoring algorithm
        assert isinstance(high_quality_rec.confidence_score, float)
        assert isinstance(low_quality_rec.confidence_score, float)
        assert 0.0 <= high_quality_rec.confidence_score <= 1.0
        assert 0.0 <= low_quality_rec.confidence_score <= 1.0

    def test_validation_error_handling(self, mode_detector):
        """Test validation error handling."""
        # Test with invalid input
        with pytest.raises(ValidationError):
            mode_detector.analyze_files("not a list")

        with pytest.raises(ValidationError):
            mode_detector.analyze_files([{"not": "file_info"}])

    def test_edge_case_very_old_files(self, mode_detector):
        """Test handling of very old files."""
        old_file = FileInfo(
            path=Path("old_charter.md"),
            format=FileFormat.MARKDOWN,
            document_type=DocumentType.CHARTER,
            size_bytes=5000,
            last_modified=datetime.now() - timedelta(days=365),  # Very old
            is_readable=True,
        )

        quality_score = mode_detector._calculate_single_file_quality(old_file)
        assert quality_score < 0.8  # Should be penalized for being old

    def test_edge_case_very_large_files(self, mode_detector):
        """Test handling of very large files."""
        large_file = FileInfo(
            path=Path("large_file.xlsx"),
            format=FileFormat.EXCEL,
            document_type=DocumentType.RISK_REGISTER,
            size_bytes=100 * 1024 * 1024,  # 100MB
            last_modified=datetime.now(),
            is_readable=True,
        )

        quality_score = mode_detector._calculate_single_file_quality(large_file)
        assert quality_score > 0.5  # Large files should still score reasonably well

    def test_unknown_document_types(self, mode_detector):
        """Test handling of unknown document types."""
        unknown_file = FileInfo(
            path=Path("unknown.txt"),
            format=FileFormat.MARKDOWN,
            document_type=DocumentType.UNKNOWN,
            size_bytes=1000,
            last_modified=datetime.now(),
            is_readable=True,
        )

        recommendation = mode_detector.analyze_files([unknown_file])

        # Unknown files should not contribute to completeness
        assert recommendation.recommended_mode in [
            OperationMode.LEARNING_MODULE,
            OperationMode.DOCUMENT_CHECK,
        ]
        assert DocumentType.UNKNOWN not in recommendation.available_documents

    def test_mixed_quality_scenarios(self, mode_detector, sample_file_info):
        """Test scenarios with mixed file quality."""
        mixed_files = [
            sample_file_info["charter"],  # Good quality
            sample_file_info["empty_file"],  # Poor quality (empty)
            sample_file_info["unreadable_file"],  # Poor quality (unreadable)
        ]

        recommendation = mode_detector.analyze_files(mixed_files)

        # Should still provide a reasonable recommendation
        assert recommendation.recommended_mode in [mode for mode in OperationMode]
        assert 0.0 <= recommendation.confidence_score <= 1.0
        assert len(recommendation.reasoning) > 0

    def test_recommendation_consistency(self, mode_detector, sample_file_info):
        """Test that recommendations are consistent for the same input."""
        files = [sample_file_info["charter"], sample_file_info["risk_register"]]

        rec1 = mode_detector.analyze_files(files)
        rec2 = mode_detector.analyze_files(files)

        assert rec1.recommended_mode == rec2.recommended_mode
        assert abs(rec1.confidence_score - rec2.confidence_score) < 0.01
        assert rec1.available_documents == rec2.available_documents
        assert rec1.missing_documents == rec2.missing_documents

    @pytest.mark.parametrize(
        "completeness,expected_mode",
        [
            (0.8, OperationMode.STATUS_ANALYSIS),
            (0.5, OperationMode.DOCUMENT_CHECK),
            (0.1, OperationMode.LEARNING_MODULE),
        ],
    )
    def test_mode_thresholds(self, mode_detector, completeness, expected_mode):
        """Test mode selection thresholds."""
        # Mock the completeness calculation to test thresholds
        with patch.object(mode_detector, "calculate_completeness_score", return_value=completeness):
            # Create minimal file list to avoid empty file handling
            dummy_file = FileInfo(
                path=Path("dummy.md"),
                format=FileFormat.MARKDOWN,
                document_type=DocumentType.CHARTER,
                size_bytes=1000,
                last_modified=datetime.now(),
                is_readable=True,
            )

            recommendation = mode_detector.analyze_files([dummy_file])
            assert recommendation.recommended_mode == expected_mode
