"""
Custom exception classes for PM Analysis Tool.

This module defines the exception hierarchy used throughout the application
to provide specific error handling and meaningful error messages.
"""


class PMAnalysisError(Exception):
    """Base exception for PM Analysis Tool.

    All custom exceptions in the PM Analysis Tool should inherit from this base class.
    This allows for consistent error handling and makes it easy to catch all
    tool-specific exceptions.
    """

    pass


class ConfigurationError(PMAnalysisError):
    """Configuration-related errors.

    Raised when there are issues with configuration file loading, parsing,
    or validation. This includes missing configuration files, invalid YAML
    syntax, or missing required configuration parameters.
    """

    pass


class FileProcessingError(PMAnalysisError):
    """File processing errors.

    Raised when there are issues processing individual files, such as
    file access permissions, corrupted files, or unsupported file formats.
    """

    pass


class DataExtractionError(PMAnalysisError):
    """Data extraction errors.

    Raised when there are issues extracting structured data from files,
    such as unexpected file formats, missing expected data sections,
    or parsing failures.
    """

    pass


class ValidationError(PMAnalysisError):
    """Input validation errors.

    Raised when input validation fails, such as invalid file paths,
    unsupported operation modes, or missing required parameters.
    """

    pass


class ModeDetectionError(PMAnalysisError):
    """Mode detection errors.

    Raised when the automatic mode detection system encounters issues
    analyzing available files or determining the optimal operation mode.
    """

    pass


class ReportGenerationError(PMAnalysisError):
    """Report generation errors.

    Raised when there are issues generating output reports, such as
    file write permissions, template errors, or data formatting issues.
    """

    pass
