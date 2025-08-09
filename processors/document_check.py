"""
Document Check Processor for PM Analysis Tool.

This module implements the DocumentCheckProcessor class that verifies the presence
and format of required project management documents.
"""

from typing import Dict, Any, List, Set
from pathlib import Path
import time

from processors.base_processor import BaseProcessor
from core.models import FileInfo, ProcessingResult, DocumentType, FileFormat
from utils.logger import get_logger
from utils.exceptions import FileProcessingError, ValidationError

logger = get_logger(__name__)


class DocumentCheckProcessor(BaseProcessor):
    """
    Processor for checking document presence and format compliance.
    
    This processor validates that all required project management documents
    are present in the workspace and conform to expected formats.
    """
    
    def __init__(self):
        """Initialize the Document Check processor."""
        super().__init__()
        self.processor_name = "Document Check Processor"
        
        # Define required file patterns based on PM best practices
        self.required_files = [
            "*charter*",
            "*scope*", 
            "*risk*",
            "*wbs*",
            "*roadmap*",
            "*stakeholder*"
        ]
        
        # Optional files that enhance analysis
        self.optional_files = [
            "*budget*",
            "*quality*",
            "*communication*",
            "*procurement*",
            "*requirements*"
        ]
        
        # Expected document types and their acceptable formats
        self.document_format_requirements = {
            "charter": [FileFormat.MARKDOWN, FileFormat.EXCEL],
            "scope": [FileFormat.MARKDOWN, FileFormat.EXCEL],
            "risk": [FileFormat.MARKDOWN, FileFormat.EXCEL, FileFormat.EXCEL_LEGACY],
            "wbs": [FileFormat.MARKDOWN, FileFormat.EXCEL, FileFormat.MICROSOFT_PROJECT],
            "roadmap": [FileFormat.MARKDOWN, FileFormat.EXCEL, FileFormat.MICROSOFT_PROJECT],
            "stakeholder": [FileFormat.EXCEL, FileFormat.EXCEL_LEGACY, FileFormat.CSV]
        }
    
    def validate_inputs(self, files: List[FileInfo]) -> bool:
        """
        Validate that minimum required files are available for document checking.
        
        For document check mode, we don't require all files to be present
        since the purpose is to identify what's missing.
        
        Args:
            files: List of available files
            
        Returns:
            True if we have at least some files to check, False if no files
        """
        if not files:
            logger.warning("No files provided for document check")
            return False
            
        # We can perform document check as long as we have some files
        readable_files = [f for f in files if f.is_readable]
        if not readable_files:
            logger.warning("No readable files available for document check")
            return False
            
        return True
    
    def process(self, files: List[FileInfo], config: Dict[str, Any]) -> ProcessingResult:
        """
        Process files to check document presence and format compliance.
        
        Args:
            files: List of files to analyze
            config: Configuration dictionary
            
        Returns:
            ProcessingResult with document check analysis
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting document check with {len(files)} files")
            
            # Validate inputs
            if not self.validate_inputs(files):
                processing_time = max(time.time() - start_time, 0.001)  # Ensure minimum time
                return ProcessingResult(
                    success=False,
                    operation="document_check",
                    errors=["No valid files available for document check"],
                    processing_time_seconds=processing_time
                )
            
            # Get required documents from config
            required_docs_config = config.get("required_documents", [])
            if not required_docs_config:
                logger.warning("No required documents configuration found, using defaults")
                required_docs_config = self._get_default_required_documents()
            
            # Perform document analysis
            analysis_result = self._analyze_documents(files, required_docs_config)
            
            # Generate comprehensive report
            report_data = self._generate_document_report(analysis_result, files)
            
            processing_time = max(time.time() - start_time, 0.001)  # Ensure minimum time
            logger.info(f"Document check completed in {processing_time:.2f} seconds")
            
            return ProcessingResult(
                success=True,
                operation="document_check",
                data=report_data,
                warnings=analysis_result.get("warnings", []),
                processing_time_seconds=processing_time
            )
            
        except Exception as e:
            error_msg = f"Document check processing failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            processing_time = max(time.time() - start_time, 0.001)  # Ensure minimum time
            return ProcessingResult(
                success=False,
                operation="document_check",
                errors=[error_msg],
                processing_time_seconds=processing_time
            )
    
    def _analyze_documents(self, files: List[FileInfo], required_docs_config: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze available documents against requirements.
        
        Args:
            files: Available files to analyze
            required_docs_config: Configuration of required documents
            
        Returns:
            Dictionary containing analysis results
        """
        analysis = {
            "available_documents": [],
            "missing_documents": [],
            "format_mismatches": [],
            "optional_documents": [],
            "warnings": [],
            "document_coverage": {}
        }
        
        # Create lookup of available files by name patterns
        available_files_map = {}
        for file_info in files:
            filename_lower = file_info.filename.lower()
            available_files_map[filename_lower] = file_info
        
        # Check each required document
        for doc_config in required_docs_config:
            doc_name = doc_config["name"]
            patterns = doc_config["patterns"]
            expected_formats = doc_config["formats"]
            is_required = doc_config.get("required", True)
            
            # Find matching files for this document type
            matching_files = self._find_matching_files(files, patterns)
            
            if matching_files:
                # Document found - check format compliance
                for file_info in matching_files:
                    file_format = file_info.format.value
                    
                    document_entry = {
                        "name": doc_name,
                        "file_path": str(file_info.path),
                        "format": file_format,
                        "size_bytes": file_info.size_bytes,
                        "last_modified": file_info.last_modified.isoformat(),
                        "is_readable": file_info.is_readable
                    }
                    
                    if file_format in expected_formats:
                        analysis["available_documents"].append(document_entry)
                        logger.debug(f"Found valid document: {doc_name} ({file_format})")
                    else:
                        # Format mismatch
                        mismatch_entry = {
                            **document_entry,
                            "expected_formats": expected_formats,
                            "actual_format": file_format
                        }
                        analysis["format_mismatches"].append(mismatch_entry)
                        analysis["warnings"].append(
                            f"Document '{doc_name}' found but in unexpected format '{file_format}'. "
                            f"Expected formats: {expected_formats}"
                        )
                        logger.warning(f"Format mismatch for {doc_name}: got {file_format}, expected {expected_formats}")
                
                # Calculate coverage score for this document type
                valid_files = [f for f in matching_files if f.format.value in expected_formats]
                coverage_score = 1.0 if valid_files else 0.5  # Partial credit for wrong format
                analysis["document_coverage"][doc_name] = coverage_score
                
            else:
                # Document missing
                if is_required:
                    missing_entry = {
                        "name": doc_name,
                        "patterns": patterns,
                        "expected_formats": expected_formats,
                        "required": is_required
                    }
                    analysis["missing_documents"].append(missing_entry)
                    analysis["document_coverage"][doc_name] = 0.0
                    logger.info(f"Required document missing: {doc_name}")
        
        # Identify optional documents that are present
        for file_info in files:
            if not self._is_file_accounted_for(file_info, required_docs_config):
                # This might be an optional document
                optional_entry = {
                    "file_path": str(file_info.path),
                    "format": file_info.format.value,
                    "size_bytes": file_info.size_bytes,
                    "document_type": file_info.document_type.value
                }
                analysis["optional_documents"].append(optional_entry)
        
        return analysis
    
    def _find_matching_files(self, files: List[FileInfo], patterns: List[str]) -> List[FileInfo]:
        """
        Find files that match any of the given patterns.
        
        Args:
            files: List of files to search
            patterns: List of patterns to match against
            
        Returns:
            List of matching FileInfo objects
        """
        matching_files = []
        
        for file_info in files:
            filename_lower = file_info.filename.lower()
            
            for pattern in patterns:
                if self._matches_pattern(filename_lower, pattern.lower()):
                    matching_files.append(file_info)
                    break  # Don't add the same file multiple times
        
        return matching_files
    
    def _is_file_accounted_for(self, file_info: FileInfo, required_docs_config: List[Dict[str, Any]]) -> bool:
        """
        Check if a file is accounted for in the required documents configuration.
        
        Args:
            file_info: File to check
            required_docs_config: Required documents configuration
            
        Returns:
            True if file matches any required document pattern
        """
        filename_lower = file_info.filename.lower()
        
        for doc_config in required_docs_config:
            patterns = doc_config["patterns"]
            for pattern in patterns:
                if self._matches_pattern(filename_lower, pattern.lower()):
                    return True
        
        return False
    
    def _generate_document_report(self, analysis: Dict[str, Any], files: List[FileInfo]) -> Dict[str, Any]:
        """
        Generate comprehensive document check report.
        
        Args:
            analysis: Document analysis results
            files: Original file list
            
        Returns:
            Dictionary containing formatted report data
        """
        total_required = len(analysis["missing_documents"]) + len(analysis["available_documents"])
        available_count = len(analysis["available_documents"])
        missing_count = len(analysis["missing_documents"])
        format_mismatch_count = len(analysis["format_mismatches"])
        
        # Calculate overall compliance score
        compliance_score = 0.0
        if total_required > 0:
            compliance_score = available_count / total_required
        
        # Generate summary statistics
        summary = {
            "total_files_scanned": len(files),
            "total_required_documents": total_required,
            "available_documents_count": available_count,
            "missing_documents_count": missing_count,
            "format_mismatches_count": format_mismatch_count,
            "optional_documents_count": len(analysis["optional_documents"]),
            "compliance_score": compliance_score,
            "compliance_percentage": int(compliance_score * 100)
        }
        
        # Generate recommendations
        recommendations = self._generate_recommendations(analysis, summary)
        
        # Compile final report
        report = {
            "summary": summary,
            "available_documents": analysis["available_documents"],
            "missing_documents": analysis["missing_documents"],
            "format_mismatches": analysis["format_mismatches"],
            "optional_documents": analysis["optional_documents"],
            "document_coverage": analysis["document_coverage"],
            "recommendations": recommendations,
            "compliance_status": self._get_compliance_status(compliance_score)
        }
        
        return report
    
    def _generate_recommendations(self, analysis: Dict[str, Any], summary: Dict[str, Any]) -> List[str]:
        """
        Generate actionable recommendations based on document analysis.
        
        Args:
            analysis: Document analysis results
            summary: Summary statistics
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Missing documents recommendations
        if analysis["missing_documents"]:
            recommendations.append(
                f"Create {len(analysis['missing_documents'])} missing required documents to improve project compliance"
            )
            
            # Prioritize critical documents
            critical_docs = ["charter", "scope", "risk"]
            for missing_doc in analysis["missing_documents"]:
                doc_name_lower = missing_doc["name"].lower()
                if any(critical in doc_name_lower for critical in critical_docs):
                    recommendations.append(
                        f"HIGH PRIORITY: Create '{missing_doc['name']}' as it's critical for project success"
                    )
        
        # Format mismatch recommendations
        if analysis["format_mismatches"]:
            recommendations.append(
                f"Convert {len(analysis['format_mismatches'])} documents to expected formats for better tool compatibility"
            )
        
        # Low compliance recommendations
        compliance_score = summary["compliance_score"]
        if compliance_score < 0.5:
            recommendations.append(
                "URGENT: Project documentation compliance is critically low. "
                "Focus on creating missing core documents immediately."
            )
        elif compliance_score < 0.8:
            recommendations.append(
                "Project documentation needs improvement. "
                "Consider creating missing documents to enhance project management effectiveness."
            )
        
        # Optional documents recommendations
        if not analysis["optional_documents"]:
            recommendations.append(
                "Consider adding optional documents like budget plans, quality plans, "
                "or communication plans to enhance project management."
            )
        
        return recommendations
    
    def _get_compliance_status(self, compliance_score: float) -> str:
        """
        Get compliance status description based on score.
        
        Args:
            compliance_score: Compliance score between 0 and 1
            
        Returns:
            Compliance status string
        """
        if compliance_score >= 0.9:
            return "Excellent"
        elif compliance_score >= 0.8:
            return "Good"
        elif compliance_score >= 0.6:
            return "Fair"
        elif compliance_score >= 0.4:
            return "Poor"
        else:
            return "Critical"
    
    def _get_default_required_documents(self) -> List[Dict[str, Any]]:
        """
        Get default required documents configuration.
        
        Returns:
            List of default required document configurations
        """
        return [
            {
                "name": "Project Charter",
                "patterns": ["*charter*", "*project*charter*"],
                "formats": ["md", "docx"],
                "required": True
            },
            {
                "name": "Scope Statement",
                "patterns": ["*scope*", "*project*scope*"],
                "formats": ["md", "docx"],
                "required": True
            },
            {
                "name": "Risk Management Plan",
                "patterns": ["*risk*", "*risk*management*"],
                "formats": ["md", "docx"],
                "required": True
            },
            {
                "name": "Work Breakdown Structure",
                "patterns": ["*wbs*", "*work*breakdown*", "*breakdown*structure*"],
                "formats": ["md", "docx"],
                "required": True
            },
            {
                "name": "Roadmap",
                "patterns": ["*roadmap*", "*timeline*", "*schedule*"],
                "formats": ["md", "docx", "mpp"],
                "required": True
            },
            {
                "name": "Stakeholder Register",
                "patterns": ["*stakeholder*", "*stakeholder*register*"],
                "formats": ["xlsx", "csv"],
                "required": True
            }
        ]