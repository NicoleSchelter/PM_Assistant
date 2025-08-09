"""
Intelligent mode detection system for PM Analysis Tool.

This module provides functionality to analyze available project files and
recommend the most appropriate operation mode based on file availability,
quality, and completeness. It implements a scoring algorithm to determine
the optimal mode with confidence levels and reasoning.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from core.models import (
    DocumentType,
    FileInfo,
    ModeRecommendation,
    OperationMode,
    ProcessingResult
)
from utils.exceptions import ValidationError
from utils.logger import get_logger

logger = get_logger(__name__)


class ModeDetector:
    """
    Analyzes available files to suggest optimal operation mode.
    
    The ModeDetector class implements intelligent mode selection logic by
    analyzing file availability, quality, and completeness to recommend
    the most appropriate operation mode for the PM Analysis Tool.
    """
    
    # Document importance weights for scoring (higher = more important)
    DOCUMENT_WEIGHTS = {
        DocumentType.CHARTER: 0.15,
        DocumentType.RISK_REGISTER: 0.20,
        DocumentType.STAKEHOLDER_REGISTER: 0.15,
        DocumentType.WBS: 0.20,
        DocumentType.ROADMAP: 0.15,
        DocumentType.PROJECT_SCHEDULE: 0.15
    }
    
    # Minimum thresholds for mode recommendations
    STATUS_ANALYSIS_THRESHOLD = 0.60  # 60% completeness for status analysis
    DOCUMENT_CHECK_THRESHOLD = 0.20   # 20% completeness for document check
    HIGH_CONFIDENCE_THRESHOLD = 0.80  # 80% confidence for high confidence
    
    # Quality scoring factors
    QUALITY_FACTORS = {
        'file_size': 0.25,      # Non-empty files score higher
        'recent_modification': 0.25,  # Recently modified files score higher
        'format_appropriateness': 0.30,  # Appropriate format for document type
        'readability': 0.20     # File is readable and accessible
    }
    
    def __init__(self, required_documents: Optional[List[Dict]] = None):
        """
        Initialize ModeDetector with configuration.
        
        Args:
            required_documents: List of required document configurations
        """
        self.required_documents = required_documents or []
        self._required_doc_types = self._extract_required_document_types()
        
        logger.info(f"ModeDetector initialized with {len(self._required_doc_types)} required document types")
        logger.debug(f"Required document types: {[dt.value for dt in self._required_doc_types]}")
    
    def analyze_files(self, 
                     files: List[FileInfo], 
                     project_path: Optional[str] = None) -> ModeRecommendation:
        """
        Analyze available files and recommend operation mode.
        
        Args:
            files: List of FileInfo objects representing available files
            project_path: Optional project path for context
            
        Returns:
            ModeRecommendation with suggested mode and reasoning
            
        Raises:
            ValidationError: If input files are invalid
        """
        try:
            logger.info(f"Analyzing {len(files)} files for mode recommendation")
            
            if not files:
                return self._recommend_learning_mode(
                    reason="No project files found in the specified directory",
                    confidence=1.0
                )
            
            # Validate input files
            self._validate_file_list(files)
            
            # Calculate completeness and quality scores
            completeness_score = self.calculate_completeness_score(files)
            quality_scores = self._calculate_quality_scores(files)
            
            # Analyze document availability
            available_docs, missing_docs = self._analyze_document_availability(files)
            
            # Generate mode recommendation
            recommendation = self._generate_mode_recommendation(
                completeness_score=completeness_score,
                quality_scores=quality_scores,
                available_docs=available_docs,
                missing_docs=missing_docs,
                files=files
            )
            
            logger.info(f"Mode recommendation: {recommendation.recommended_mode.value} "
                       f"(confidence: {recommendation.confidence_percentage}%)")
            
            return recommendation
            
        except Exception as e:
            error_msg = f"Failed to analyze files for mode detection: {e}"
            logger.error(error_msg)
            raise ValidationError(error_msg) from e
    
    def calculate_completeness_score(self, files: List[FileInfo]) -> float:
        """
        Calculate project completeness score based on available documents.
        
        Args:
            files: List of FileInfo objects to analyze
            
        Returns:
            Completeness score between 0.0 and 1.0
        """
        if not self._required_doc_types:
            logger.warning("No required document types configured, returning default score")
            return 0.5
        
        available_doc_types = {file_info.document_type for file_info in files 
                              if file_info.document_type != DocumentType.UNKNOWN}
        
        # Calculate weighted completeness score
        total_weight = 0.0
        achieved_weight = 0.0
        
        for doc_type in self._required_doc_types:
            weight = self.DOCUMENT_WEIGHTS.get(doc_type, 0.1)  # Default weight for unknown types
            total_weight += weight
            
            if doc_type in available_doc_types:
                # Find the best quality file for this document type
                matching_files = [f for f in files if f.document_type == doc_type]
                if matching_files:
                    best_file = max(matching_files, key=lambda f: self._calculate_single_file_quality(f))
                    file_quality = self._calculate_single_file_quality(best_file)
                    achieved_weight += weight * file_quality
        
        completeness_score = achieved_weight / total_weight if total_weight > 0 else 0.0
        
        logger.debug(f"Completeness score: {completeness_score:.2f} "
                    f"({len(available_doc_types)}/{len(self._required_doc_types)} document types)")
        
        return min(1.0, max(0.0, completeness_score))
    
    def _generate_mode_recommendation(self,
                                    completeness_score: float,
                                    quality_scores: Dict[DocumentType, float],
                                    available_docs: List[DocumentType],
                                    missing_docs: List[DocumentType],
                                    files: List[FileInfo]) -> ModeRecommendation:
        """
        Generate mode recommendation based on analysis results.
        
        Args:
            completeness_score: Overall project completeness score
            quality_scores: Quality scores for each document type
            available_docs: List of available document types
            missing_docs: List of missing document types
            files: Original list of files
            
        Returns:
            ModeRecommendation with suggested mode and details
        """
        # Determine recommended mode based on completeness score
        if completeness_score >= self.STATUS_ANALYSIS_THRESHOLD:
            recommended_mode = OperationMode.STATUS_ANALYSIS
            confidence_base = completeness_score
            reasoning_parts = [
                f"Project appears {completeness_score:.0%} complete with sufficient documents for comprehensive analysis"
            ]
        elif completeness_score >= self.DOCUMENT_CHECK_THRESHOLD:
            recommended_mode = OperationMode.DOCUMENT_CHECK
            confidence_base = 0.8  # High confidence for document check when some files exist
            reasoning_parts = [
                f"Project is {completeness_score:.0%} complete, suggesting document verification is needed"
            ]
        else:
            recommended_mode = OperationMode.LEARNING_MODULE
            confidence_base = 0.9  # High confidence for learning mode when few/no files
            reasoning_parts = [
                f"Project appears {completeness_score:.0%} complete with minimal documentation available"
            ]
        
        # Adjust confidence based on quality scores
        if quality_scores:
            avg_quality = sum(quality_scores.values()) / len(quality_scores)
            confidence_adjustment = (avg_quality - 0.5) * 0.2  # ±10% adjustment based on quality
            confidence_base += confidence_adjustment
        
        # Generate detailed reasoning
        reasoning = self._generate_detailed_reasoning(
            recommended_mode, completeness_score, available_docs, missing_docs, quality_scores
        )
        
        # Determine alternative modes
        alternative_modes = self._determine_alternative_modes(recommended_mode, completeness_score)
        
        # Create recommendation
        recommendation = ModeRecommendation(
            recommended_mode=recommended_mode,
            confidence_score=min(1.0, max(0.0, confidence_base)),
            reasoning=reasoning,
            available_documents=available_docs,
            missing_documents=missing_docs,
            file_quality_scores=quality_scores,
            alternative_modes=alternative_modes
        )
        
        return recommendation
    
    def _generate_detailed_reasoning(self,
                                   mode: OperationMode,
                                   completeness_score: float,
                                   available_docs: List[DocumentType],
                                   missing_docs: List[DocumentType],
                                   quality_scores: Dict[DocumentType, float]) -> str:
        """Generate detailed reasoning for the mode recommendation."""
        reasoning_parts = []
        
        # Base reasoning based on mode
        if mode == OperationMode.STATUS_ANALYSIS:
            reasoning_parts.append(
                f"Status Analysis mode recommended due to {completeness_score:.0%} project completeness. "
                f"Found {len(available_docs)} of {len(self._required_doc_types)} required document types."
            )
            
            # Highlight key available documents
            key_docs = [doc for doc in available_docs 
                       if doc in {DocumentType.RISK_REGISTER, DocumentType.WBS, DocumentType.STAKEHOLDER_REGISTER}]
            if key_docs:
                doc_names = [doc.value.replace('_', ' ').title() for doc in key_docs]
                reasoning_parts.append(f"Key documents available: {', '.join(doc_names)}.")
            
            # Mention quality if high
            if quality_scores:
                high_quality_docs = [doc for doc, score in quality_scores.items() if score > 0.8]
                if high_quality_docs:
                    reasoning_parts.append(f"High-quality documents detected for comprehensive analysis.")
        
        elif mode == OperationMode.DOCUMENT_CHECK:
            reasoning_parts.append(
                f"Document Check mode recommended due to {completeness_score:.0%} project completeness. "
                f"Missing {len(missing_docs)} required document types."
            )
            
            # List critical missing documents
            critical_missing = [doc for doc in missing_docs 
                              if doc in {DocumentType.CHARTER, DocumentType.RISK_REGISTER, DocumentType.WBS}]
            if critical_missing:
                doc_names = [doc.value.replace('_', ' ').title() for doc in critical_missing[:3]]
                reasoning_parts.append(f"Critical missing documents: {', '.join(doc_names)}.")
        
        else:  # LEARNING_MODULE
            reasoning_parts.append(
                f"Learning Module mode recommended due to {completeness_score:.0%} project completeness. "
                f"Only {len(available_docs)} document types found."
            )
            reasoning_parts.append(
                "Consider using learning modules to understand project management documentation requirements."
            )
        
        # Add quality assessment if available
        if quality_scores:
            avg_quality = sum(quality_scores.values()) / len(quality_scores)
            if avg_quality > 0.8:
                reasoning_parts.append("Document quality is excellent for reliable analysis.")
            elif avg_quality < 0.5:
                reasoning_parts.append("Document quality concerns may affect analysis reliability.")
        
        return " ".join(reasoning_parts)
    
    def _determine_alternative_modes(self, 
                                   primary_mode: OperationMode, 
                                   completeness_score: float) -> List[OperationMode]:
        """Determine alternative operation modes."""
        alternatives = []
        
        if primary_mode == OperationMode.STATUS_ANALYSIS:
            # Always offer document check as alternative
            alternatives.append(OperationMode.DOCUMENT_CHECK)
            if completeness_score < 0.8:  # If not very complete, offer learning
                alternatives.append(OperationMode.LEARNING_MODULE)
        
        elif primary_mode == OperationMode.DOCUMENT_CHECK:
            # Offer learning if very incomplete, status analysis if reasonably complete
            if completeness_score < 0.4:
                alternatives.append(OperationMode.LEARNING_MODULE)
            if completeness_score > 0.4:
                alternatives.append(OperationMode.STATUS_ANALYSIS)
        
        else:  # LEARNING_MODULE
            # Always offer document check, status analysis if some files exist
            alternatives.append(OperationMode.DOCUMENT_CHECK)
            if completeness_score > 0.3:
                alternatives.append(OperationMode.STATUS_ANALYSIS)
        
        return alternatives
    
    def _calculate_quality_scores(self, files: List[FileInfo]) -> Dict[DocumentType, float]:
        """Calculate quality scores for each document type."""
        quality_scores = {}
        
        # Group files by document type
        files_by_type = {}
        for file_info in files:
            if file_info.document_type != DocumentType.UNKNOWN:
                if file_info.document_type not in files_by_type:
                    files_by_type[file_info.document_type] = []
                files_by_type[file_info.document_type].append(file_info)
        
        # Calculate quality score for each document type
        for doc_type, doc_files in files_by_type.items():
            # Use the highest quality file for each document type
            best_quality = max(self._calculate_single_file_quality(f) for f in doc_files)
            quality_scores[doc_type] = best_quality
        
        return quality_scores
    
    def _calculate_single_file_quality(self, file_info: FileInfo) -> float:
        """Calculate quality score for a single file."""
        quality_score = 0.0
        
        # File size factor (non-empty files score higher)
        size_factor = self.QUALITY_FACTORS['file_size']
        if file_info.size_bytes > 0:
            # Logarithmic scaling for file size (1KB = 0.5, 10KB = 0.75, 100KB+ = 1.0)
            size_score = min(1.0, 0.3 + 0.2 * (file_info.size_bytes / 1024) ** 0.3)
        else:
            size_score = 0.0  # Empty files get 0 for size
        quality_score += size_factor * size_score
        
        # Recent modification factor
        modification_factor = self.QUALITY_FACTORS['recent_modification']
        days_since_modified = (datetime.now() - file_info.last_modified).days
        if days_since_modified <= 7:
            modification_score = 1.0
        elif days_since_modified <= 30:
            modification_score = 0.8
        elif days_since_modified <= 90:
            modification_score = 0.6
        else:
            modification_score = 0.4
        quality_score += modification_factor * modification_score
        
        # Format appropriateness factor
        format_factor = self.QUALITY_FACTORS['format_appropriateness']
        format_score = self._calculate_format_appropriateness(file_info)
        quality_score += format_factor * format_score
        
        # Readability factor
        readability_factor = self.QUALITY_FACTORS['readability']
        readability_score = 1.0 if file_info.is_readable else 0.0
        quality_score += readability_factor * readability_score
        
        # Apply penalty for empty files - significantly reduce score
        if file_info.size_bytes == 0:
            quality_score *= 0.3  # Reduce score by 70% for empty files
        
        # Apply penalty for unreadable files
        if not file_info.is_readable:
            quality_score *= 0.5  # Reduce score by 50% for unreadable files
        
        return min(1.0, max(0.0, quality_score))
    
    def _calculate_format_appropriateness(self, file_info: FileInfo) -> float:
        """Calculate how appropriate the file format is for the document type."""
        # Define preferred formats for each document type
        preferred_formats = {
            DocumentType.CHARTER: {'md', 'docx'},
            DocumentType.RISK_REGISTER: {'xlsx', 'csv', 'md'},
            DocumentType.STAKEHOLDER_REGISTER: {'xlsx', 'csv'},
            DocumentType.WBS: {'md', 'docx', 'xlsx'},
            DocumentType.ROADMAP: {'md', 'docx', 'mpp'},
            DocumentType.PROJECT_SCHEDULE: {'mpp', 'xlsx'}
        }
        
        doc_type = file_info.document_type
        file_format = file_info.format.value
        
        if doc_type in preferred_formats:
            if file_format in preferred_formats[doc_type]:
                return 1.0  # Perfect format match
            else:
                return 0.6  # Acceptable but not ideal
        
        return 0.8  # Default score for unknown document types
    
    def _analyze_document_availability(self, files: List[FileInfo]) -> Tuple[List[DocumentType], List[DocumentType]]:
        """Analyze which document types are available and missing."""
        available_types = set()
        
        for file_info in files:
            if file_info.document_type != DocumentType.UNKNOWN:
                available_types.add(file_info.document_type)
        
        available_docs = list(available_types)
        missing_docs = [doc_type for doc_type in self._required_doc_types 
                       if doc_type not in available_types]
        
        return available_docs, missing_docs
    
    def _extract_required_document_types(self) -> List[DocumentType]:
        """Extract required document types from configuration."""
        if not self.required_documents:
            # Return default required document types
            return [
                DocumentType.CHARTER,
                DocumentType.RISK_REGISTER,
                DocumentType.STAKEHOLDER_REGISTER,
                DocumentType.WBS,
                DocumentType.ROADMAP
            ]
        
        # Map document names to DocumentType enum values
        name_mapping = {
            'project charter': DocumentType.CHARTER,
            'charter': DocumentType.CHARTER,
            'risk management plan': DocumentType.RISK_REGISTER,
            'risk register': DocumentType.RISK_REGISTER,
            'risk': DocumentType.RISK_REGISTER,
            'stakeholder register': DocumentType.STAKEHOLDER_REGISTER,
            'stakeholder': DocumentType.STAKEHOLDER_REGISTER,
            'work breakdown structure': DocumentType.WBS,
            'wbs': DocumentType.WBS,
            'roadmap': DocumentType.ROADMAP,
            'timeline': DocumentType.ROADMAP,
            'schedule': DocumentType.PROJECT_SCHEDULE,
            'project schedule': DocumentType.PROJECT_SCHEDULE
        }
        
        required_types = []
        for doc_config in self.required_documents:
            if doc_config.get('required', False):
                doc_name = doc_config.get('name', '').lower()
                for key, doc_type in name_mapping.items():
                    if key in doc_name:
                        if doc_type not in required_types:
                            required_types.append(doc_type)
                        break
        
        return required_types if required_types else [
            DocumentType.CHARTER,
            DocumentType.RISK_REGISTER,
            DocumentType.STAKEHOLDER_REGISTER,
            DocumentType.WBS,
            DocumentType.ROADMAP
        ]
    
    def _validate_file_list(self, files: List[FileInfo]) -> None:
        """Validate the input file list."""
        if not isinstance(files, list):
            raise ValidationError("Files parameter must be a list")
        
        for i, file_info in enumerate(files):
            if not isinstance(file_info, FileInfo):
                raise ValidationError(f"File {i} must be a FileInfo object")
    
    def _recommend_learning_mode(self, reason: str, confidence: float) -> ModeRecommendation:
        """Create a learning mode recommendation."""
        return ModeRecommendation(
            recommended_mode=OperationMode.LEARNING_MODULE,
            confidence_score=confidence,
            reasoning=f"{reason}. Learning Module mode will provide guidance on project management documentation and best practices.",
            available_documents=[],
            missing_documents=list(self._required_doc_types),
            file_quality_scores={},
            alternative_modes=[OperationMode.DOCUMENT_CHECK]
        )