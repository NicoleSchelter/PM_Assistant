"""
Core engine and orchestration for PM Analysis Tool.

This module implements the PMAnalysisEngine class that serves as the main orchestrator
for the PM Analysis Tool, coordinating all components including mode detection,
file scanning, and processing.
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from core.config_manager import ConfigManager
from core.file_scanner import FileScanner
from core.mode_detector import ModeDetector
from core.models import (
    FileInfo,
    ModeRecommendation,
    OperationMode,
    ProcessingResult,
    ProcessingStatus,
)
from processors.document_check import DocumentCheckProcessor
from processors.learning_module import LearningModuleProcessor
from processors.status_analysis import StatusAnalysisProcessor
from reporters.excel_reporter import ExcelReporter
from reporters.markdown_reporter import MarkdownReporter
from utils.exceptions import (
    ConfigurationError,
    FileProcessingError,
    PMAnalysisError,
    ValidationError,
)
from utils.logger import get_logger

logger = get_logger(__name__)


class PMAnalysisEngine:
    """
    Main orchestrator for the PM Analysis Tool.

    The PMAnalysisEngine coordinates all system components including configuration
    management, file scanning, mode detection, processing, and report generation.
    It provides the primary interface for executing analysis workflows.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the PM Analysis Engine.

        Args:
            config_path: Optional path to configuration file. If None, uses default config.yaml

        Raises:
            ConfigurationError: If configuration cannot be loaded or is invalid
        """
        try:
            logger.info("Initializing PM Analysis Engine")

            # Initialize configuration manager
            self.config_manager = ConfigManager(config_path)
            self.config = self.config_manager.load_config()

            # Initialize file scanner
            self.file_scanner = FileScanner()

            # Initialize mode detector with required documents configuration
            required_docs = self.config_manager.get_required_documents()
            self.mode_detector = ModeDetector(required_docs)

            # Initialize processors
            self.processors = {
                OperationMode.DOCUMENT_CHECK: DocumentCheckProcessor(),
                OperationMode.STATUS_ANALYSIS: StatusAnalysisProcessor(),
                OperationMode.LEARNING_MODULE: LearningModuleProcessor(),
            }

            # Initialize reporters
            self.reporters = {"markdown": MarkdownReporter(), "excel": ExcelReporter()}

            # Track engine state
            self.last_scan_results: List[FileInfo] = []
            self.last_mode_recommendation: Optional[ModeRecommendation] = None
            self.execution_history: List[Dict[str, Any]] = []

            logger.info("PM Analysis Engine initialized successfully")

        except Exception as e:
            error_msg = f"Failed to initialize PM Analysis Engine: {e}"
            logger.error(error_msg, exc_info=True)
            raise ConfigurationError(error_msg) from e

    def run(
        self,
        mode: Optional[Union[str, OperationMode]] = None,
        project_path: Optional[str] = None,
        output_formats: Optional[List[str]] = None,
    ) -> ProcessingResult:
        """
        Execute analysis with optional mode override and configuration.

        Args:
            mode: Optional operation mode override. If None, uses intelligent mode detection
            project_path: Optional project path override. If None, uses configured default
            output_formats: Optional output formats override. If None, uses mode defaults

        Returns:
            ProcessingResult with execution results and generated reports

        Raises:
            ValidationError: If input parameters are invalid
            FileProcessingError: If file scanning or processing fails
            PMAnalysisError: If execution fails for other reasons
        """
        start_time = time.time()
        execution_id = f"exec_{int(start_time)}"

        try:
            logger.info(f"Starting PM Analysis execution {execution_id}")

            # Validate and normalize inputs
            validated_inputs = self._validate_and_normalize_inputs(
                mode, project_path, output_formats
            )
            mode_override = validated_inputs["mode"]
            target_project_path = validated_inputs["project_path"]
            target_output_formats = validated_inputs["output_formats"]

            # Step 1: Scan for project files
            logger.info(f"Scanning project directory: {target_project_path}")
            discovered_files = self._scan_project_files(target_project_path)

            # Step 2: Determine operation mode
            if mode_override:
                logger.info(f"Using explicit mode override: {mode_override.value}")
                selected_mode = mode_override
                mode_recommendation = None
            else:
                logger.info("Detecting optimal operation mode")
                mode_recommendation = self._detect_optimal_mode(
                    discovered_files, target_project_path
                )
                selected_mode = mode_recommendation.recommended_mode
                logger.info(
                    f"Recommended mode: {selected_mode.value} (confidence: {mode_recommendation.confidence_percentage}%)"
                )

            # Step 3: Execute processing
            logger.info(f"Executing {selected_mode.value} processing")
            processing_result = self._execute_processing(selected_mode, discovered_files)

            # Step 4: Generate reports
            logger.info("Generating output reports")
            report_results = self._generate_reports(
                processing_result, selected_mode, target_output_formats, mode_recommendation
            )

            # Step 5: Compile final results
            execution_time = time.time() - start_time
            final_result = self._compile_execution_results(
                execution_id=execution_id,
                selected_mode=selected_mode,
                mode_recommendation=mode_recommendation,
                discovered_files=discovered_files,
                processing_result=processing_result,
                report_results=report_results,
                execution_time=execution_time,
            )

            # Update engine state
            self._update_engine_state(discovered_files, mode_recommendation, final_result)

            logger.info(
                f"PM Analysis execution {execution_id} completed successfully in {execution_time:.2f} seconds"
            )
            return final_result

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"PM Analysis execution {execution_id} failed: {e}"
            logger.error(error_msg, exc_info=True)

            # Return failed result with error details
            return ProcessingResult(
                success=False,
                operation="pm_analysis_execution",
                errors=[error_msg],
                processing_time_seconds=execution_time,
                metadata={
                    "execution_id": execution_id,
                    "failure_stage": self._determine_failure_stage(e),
                },
            )

    def detect_optimal_mode(self, project_path: Optional[str] = None) -> ModeRecommendation:
        """
        Detect the optimal operation mode based on available files.

        Args:
            project_path: Optional project path. If None, uses configured default

        Returns:
            ModeRecommendation with suggested mode and reasoning

        Raises:
            FileProcessingError: If file scanning fails
            ValidationError: If project path is invalid
        """
        try:
            logger.info("Detecting optimal operation mode")

            # Use provided path or default from configuration
            target_path = project_path or self.config_manager.get_project_path()

            # Scan for available files
            discovered_files = self._scan_project_files(target_path)

            # Analyze files and recommend mode
            mode_recommendation = self._detect_optimal_mode(discovered_files, target_path)

            logger.info(
                f"Mode detection complete: {mode_recommendation.recommended_mode.value} "
                f"(confidence: {mode_recommendation.confidence_percentage}%)"
            )

            return mode_recommendation

        except Exception as e:
            error_msg = f"Mode detection failed: {e}"
            logger.error(error_msg, exc_info=True)
            raise ValidationError(error_msg) from e

    def get_available_files(self, project_path: Optional[str] = None) -> List[FileInfo]:
        """
        Get list of available project files without processing them.

        Args:
            project_path: Optional project path. If None, uses configured default

        Returns:
            List of FileInfo objects for discovered files

        Raises:
            FileProcessingError: If file scanning fails
        """
        try:
            target_path = project_path or self.config_manager.get_project_path()
            return self._scan_project_files(target_path)
        except Exception as e:
            error_msg = f"File scanning failed: {e}"
            logger.error(error_msg, exc_info=True)
            raise FileProcessingError(error_msg) from e

    def get_processor_info(self) -> Dict[str, Any]:
        """
        Get information about available processors.

        Returns:
            Dictionary containing processor information
        """
        processor_info = {}
        for mode, processor in self.processors.items():
            processor_info[mode.value] = processor.get_processor_info()

        return processor_info

    def get_engine_status(self) -> Dict[str, Any]:
        """
        Get current engine status and statistics.

        Returns:
            Dictionary containing engine status information
        """
        return {
            "initialized": True,
            "config_loaded": bool(self.config),
            "processors_available": list(self.processors.keys()),
            "reporters_available": list(self.reporters.keys()),
            "last_scan_file_count": len(self.last_scan_results),
            "execution_count": len(self.execution_history),
            "last_recommended_mode": (
                self.last_mode_recommendation.recommended_mode.value
                if self.last_mode_recommendation
                else None
            ),
        }

    def _validate_and_normalize_inputs(
        self,
        mode: Optional[Union[str, OperationMode]],
        project_path: Optional[str],
        output_formats: Optional[List[str]],
    ) -> Dict[str, Any]:
        """
        Validate and normalize input parameters.

        Args:
            mode: Operation mode (string or enum)
            project_path: Project directory path
            output_formats: List of output format strings

        Returns:
            Dictionary with normalized inputs

        Raises:
            ValidationError: If inputs are invalid
        """
        validated = {}

        # Validate and normalize mode
        if mode is not None:
            if isinstance(mode, str):
                try:
                    validated["mode"] = OperationMode(mode.lower())
                except ValueError:
                    valid_modes = [m.value for m in OperationMode]
                    raise ValidationError(f"Invalid mode '{mode}'. Valid modes: {valid_modes}")
            elif isinstance(mode, OperationMode):
                validated["mode"] = mode
            else:
                raise ValidationError(
                    f"Mode must be string or OperationMode enum, got {type(mode)}"
                )
        else:
            validated["mode"] = None

        # Validate and normalize project path
        if project_path is not None:
            path_obj = Path(project_path)
            if not path_obj.exists():
                raise ValidationError(f"Project path does not exist: {project_path}")
            if not path_obj.is_dir():
                raise ValidationError(f"Project path is not a directory: {project_path}")
            validated["project_path"] = str(path_obj.resolve())
        else:
            validated["project_path"] = self.config_manager.get_project_path()

        # Validate and normalize output formats
        if output_formats is not None:
            if not isinstance(output_formats, list):
                raise ValidationError("Output formats must be a list")

            valid_formats = list(self.reporters.keys())
            invalid_formats = [f for f in output_formats if f not in valid_formats]
            if invalid_formats:
                raise ValidationError(
                    f"Invalid output formats: {invalid_formats}. Valid formats: {valid_formats}"
                )

            validated["output_formats"] = output_formats
        else:
            validated["output_formats"] = None

        return validated

    def _scan_project_files(self, project_path: str) -> List[FileInfo]:
        """
        Scan project directory for relevant files.

        Args:
            project_path: Path to project directory

        Returns:
            List of discovered FileInfo objects

        Raises:
            FileProcessingError: If scanning fails
        """
        try:
            # Scan directory for files
            discovered_files = self.file_scanner.scan_directory(
                directory_path=project_path, recursive=True, include_hidden=False
            )

            # Validate file formats
            validation_result = self.file_scanner.validate_file_formats(discovered_files)

            if not validation_result.success:
                logger.warning(f"File validation issues: {validation_result.errors}")

            # Log scan results
            logger.info(f"Discovered {len(discovered_files)} project files")
            if validation_result.warnings:
                for warning in validation_result.warnings:
                    logger.warning(warning)

            return discovered_files

        except Exception as e:
            error_msg = f"File scanning failed for path {project_path}: {e}"
            logger.error(error_msg, exc_info=True)
            raise FileProcessingError(error_msg) from e

    def _detect_optimal_mode(self, files: List[FileInfo], project_path: str) -> ModeRecommendation:
        """
        Detect optimal operation mode based on available files.

        Args:
            files: List of discovered files
            project_path: Project directory path

        Returns:
            ModeRecommendation with analysis results
        """
        try:
            return self.mode_detector.analyze_files(files, project_path)
        except Exception as e:
            error_msg = f"Mode detection failed: {e}"
            logger.error(error_msg, exc_info=True)
            # Return default learning mode recommendation on failure
            return ModeRecommendation(
                recommended_mode=OperationMode.LEARNING_MODULE,
                confidence_score=0.5,
                reasoning=f"Mode detection failed ({str(e)}), defaulting to learning module",
                available_documents=[],
                missing_documents=[],
                file_quality_scores={},
                alternative_modes=[OperationMode.DOCUMENT_CHECK],
            )

    def _execute_processing(self, mode: OperationMode, files: List[FileInfo]) -> ProcessingResult:
        """
        Execute processing using the appropriate processor.

        Args:
            mode: Selected operation mode
            files: List of files to process

        Returns:
            ProcessingResult from the processor

        Raises:
            ValidationError: If mode is not supported or processor validation fails
            PMAnalysisError: If processing fails
        """
        try:
            # Get the appropriate processor
            processor = self.processors.get(mode)
            if not processor:
                raise ValidationError(f"No processor available for mode: {mode.value}")

            # Validate that processor can handle the files
            if not processor.validate_inputs(files):
                missing_files = processor.get_missing_required_files(files)
                if missing_files:
                    logger.warning(f"Processor validation failed - missing files: {missing_files}")
                    # Continue with processing but log the warning
                else:
                    logger.warning("Processor validation failed for unknown reasons")

            # Execute processing
            logger.info(f"Executing {processor.processor_name}")
            result = processor.process(files, self.config)

            # Mark files as processed
            if result.success:
                for file_info in files:
                    if file_info.is_readable:
                        file_info.mark_as_processed()

            return result

        except Exception as e:
            error_msg = f"Processing execution failed for mode {mode.value}: {e}"
            logger.error(error_msg, exc_info=True)
            raise PMAnalysisError(error_msg) from e

    def _generate_reports(
        self,
        processing_result: ProcessingResult,
        mode: OperationMode,
        output_formats: Optional[List[str]],
        mode_recommendation: Optional[ModeRecommendation],
    ) -> Dict[str, ProcessingResult]:
        """
        Generate output reports in specified formats.

        Args:
            processing_result: Result from processing
            mode: Operation mode that was executed
            output_formats: List of output formats to generate
            mode_recommendation: Mode recommendation (if available)

        Returns:
            Dictionary mapping format names to report generation results
        """
        report_results = {}

        try:
            # Determine output formats to use
            if output_formats is None:
                # Use default formats from mode configuration
                mode_config = self.config.get("modes", {}).get(mode.value, {})
                output_formats = mode_config.get("output_formats", ["markdown"])

            # Generate reports in each requested format
            for format_name in output_formats:
                reporter = self.reporters.get(format_name)
                if not reporter:
                    logger.warning(f"No reporter available for format: {format_name}")
                    report_results[format_name] = ProcessingResult(
                        success=False,
                        operation=f"report_generation_{format_name}",
                        errors=[f"No reporter available for format: {format_name}"],
                    )
                    continue

                try:
                    logger.info(f"Generating {format_name} report")

                    # Prepare report data
                    report_data = self._prepare_report_data(
                        processing_result, mode, mode_recommendation
                    )

                    # Generate report
                    output_config = self.config.get("output", {})
                    output_path = output_config.get("directory", "./reports")

                    # Create a ProcessingResult for the reporter
                    report_processing_result = ProcessingResult(
                        success=processing_result.success,
                        operation=f"{mode.value}_report",
                        data=report_data,
                        errors=processing_result.errors,
                        warnings=processing_result.warnings,
                        processing_time_seconds=processing_result.processing_time_seconds,
                    )

                    report_file_path = reporter.generate_report(
                        data=report_processing_result, output_path=output_path, config=output_config
                    )

                    # Create a ProcessingResult for the report generation
                    report_result = ProcessingResult(
                        success=True,
                        operation=f"report_generation_{format_name}",
                        data={"output_path": report_file_path},
                        processing_time_seconds=0.1,  # Placeholder
                    )

                    report_results[format_name] = report_result

                    if report_result.success:
                        logger.info(f"Successfully generated {format_name} report")
                    else:
                        logger.warning(
                            f"Failed to generate {format_name} report: {report_result.errors}"
                        )

                except Exception as e:
                    error_msg = f"Report generation failed for format {format_name}: {e}"
                    logger.error(error_msg, exc_info=True)
                    report_results[format_name] = ProcessingResult(
                        success=False,
                        operation=f"report_generation_{format_name}",
                        errors=[error_msg],
                        processing_time_seconds=0.0,
                    )

            return report_results

        except Exception as e:
            error_msg = f"Report generation process failed: {e}"
            logger.error(error_msg, exc_info=True)
            return {
                "error": ProcessingResult(
                    success=False, operation="report_generation", errors=[error_msg]
                )
            }

    def _prepare_report_data(
        self,
        processing_result: ProcessingResult,
        mode: OperationMode,
        mode_recommendation: Optional[ModeRecommendation],
    ) -> Dict[str, Any]:
        """
        Prepare data for report generation.

        Args:
            processing_result: Result from processing
            mode: Operation mode that was executed
            mode_recommendation: Mode recommendation (if available)

        Returns:
            Dictionary containing data for report generation
        """
        report_data = {
            "processing_result": processing_result,
            "operation_mode": mode.value,
            "execution_timestamp": datetime.now(),
            "project_config": self.config_manager.get_project_config(),
            "engine_version": "1.0.0",  # Could be made configurable
        }

        # Add mode recommendation if available
        if mode_recommendation:
            report_data["mode_recommendation"] = {
                "recommended_mode": mode_recommendation.recommended_mode.value,
                "confidence_percentage": mode_recommendation.confidence_percentage,
                "reasoning": mode_recommendation.reasoning,
                "available_documents": [
                    doc.value for doc in mode_recommendation.available_documents
                ],
                "missing_documents": [doc.value for doc in mode_recommendation.missing_documents],
                "alternative_modes": [mode.value for mode in mode_recommendation.alternative_modes],
            }

        return report_data

    def _compile_execution_results(
        self,
        execution_id: str,
        selected_mode: OperationMode,
        mode_recommendation: Optional[ModeRecommendation],
        discovered_files: List[FileInfo],
        processing_result: ProcessingResult,
        report_results: Dict[str, ProcessingResult],
        execution_time: float,
    ) -> ProcessingResult:
        """
        Compile final execution results.

        Args:
            execution_id: Unique execution identifier
            selected_mode: Operation mode that was executed
            mode_recommendation: Mode recommendation (if available)
            discovered_files: List of discovered files
            processing_result: Result from processing
            report_results: Results from report generation
            execution_time: Total execution time

        Returns:
            Compiled ProcessingResult with all execution information
        """
        # Determine overall success
        overall_success = processing_result.success
        successful_reports = sum(1 for result in report_results.values() if result.success)

        # Compile all errors and warnings
        all_errors = processing_result.errors.copy()
        all_warnings = processing_result.warnings.copy()

        for format_name, report_result in report_results.items():
            if report_result.errors:
                all_errors.extend(
                    [f"Report {format_name}: {error}" for error in report_result.errors]
                )
            if report_result.warnings:
                all_warnings.extend(
                    [f"Report {format_name}: {warning}" for warning in report_result.warnings]
                )

        # Compile execution data
        execution_data = {
            "execution_summary": {
                "execution_id": execution_id,
                "selected_mode": selected_mode.value,
                "files_discovered": len(discovered_files),
                "files_processed": len([f for f in discovered_files if f.is_processed()]),
                "reports_generated": successful_reports,
                "total_execution_time": execution_time,
            },
            "processing_data": processing_result.data,
            "file_summary": {
                "total_files": len(discovered_files),
                "readable_files": len([f for f in discovered_files if f.is_readable]),
                "processed_files": len([f for f in discovered_files if f.is_processed()]),
                "failed_files": len([f for f in discovered_files if f.has_error()]),
            },
            "report_summary": {
                format_name: {
                    "success": result.success,
                    "output_path": result.data.get("output_path") if result.success else None,
                    "processing_time": result.processing_time_seconds,
                }
                for format_name, result in report_results.items()
            },
        }

        # Add mode recommendation if available
        if mode_recommendation:
            execution_data["mode_analysis"] = {
                "recommended_mode": mode_recommendation.recommended_mode.value,
                "confidence_percentage": mode_recommendation.confidence_percentage,
                "reasoning": mode_recommendation.reasoning,
                "was_recommendation_followed": selected_mode
                == mode_recommendation.recommended_mode,
            }

        return ProcessingResult(
            success=overall_success,
            operation="pm_analysis_execution",
            data=execution_data,
            errors=all_errors,
            warnings=all_warnings,
            processing_time_seconds=execution_time,
            metadata={"execution_id": execution_id, "engine_version": "1.0.0"},
        )

    def _update_engine_state(
        self,
        discovered_files: List[FileInfo],
        mode_recommendation: Optional[ModeRecommendation],
        execution_result: ProcessingResult,
    ) -> None:
        """
        Update engine state after execution.

        Args:
            discovered_files: Files discovered during execution
            mode_recommendation: Mode recommendation (if available)
            execution_result: Final execution result
        """
        # Update last scan results
        self.last_scan_results = discovered_files

        # Update last mode recommendation
        self.last_mode_recommendation = mode_recommendation

        # Add to execution history (keep last 10 executions)
        execution_summary = {
            "timestamp": datetime.now(),
            "execution_id": execution_result.metadata.get("execution_id"),
            "success": execution_result.success,
            "mode": execution_result.data.get("execution_summary", {}).get("selected_mode"),
            "files_processed": execution_result.data.get("execution_summary", {}).get(
                "files_processed", 0
            ),
            "execution_time": execution_result.processing_time_seconds,
        }

        self.execution_history.append(execution_summary)
        if len(self.execution_history) > 10:
            self.execution_history.pop(0)

    def _determine_failure_stage(self, exception: Exception) -> str:
        """
        Determine which stage of execution failed based on exception type.

        Args:
            exception: Exception that caused the failure

        Returns:
            String describing the failure stage
        """
        if isinstance(exception, ConfigurationError):
            return "configuration"
        elif isinstance(exception, FileProcessingError):
            return "file_scanning"
        elif isinstance(exception, ValidationError):
            return "input_validation"
        else:
            return "processing"
