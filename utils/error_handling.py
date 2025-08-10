"""
Comprehensive error handling utilities for PM Analysis Tool.

This module provides decorators, context managers, and utility functions
for consistent error handling, logging, and recovery throughout the application.
"""

import functools
import traceback
from contextlib import contextmanager
from typing import Any, Callable, Dict, List, Optional, Type, Union
from datetime import datetime

from utils.exceptions import (
    PMAnalysisError,
    ConfigurationError,
    FileProcessingError,
    DataExtractionError,
    ValidationError,
    ModeDetectionError,
    ReportGenerationError
)
from utils.logger import get_logger

logger = get_logger(__name__)


def handle_errors(
    default_return: Any = None,
    reraise: bool = True,
    log_level: str = "ERROR",
    custom_message: Optional[str] = None,
    exception_types: Optional[List[Type[Exception]]] = None
):
    """
    Decorator for comprehensive error handling with logging and recovery.
    
    Args:
        default_return: Value to return if error occurs and reraise=False
        reraise: Whether to reraise the exception after logging
        log_level: Logging level for error messages
        custom_message: Custom error message prefix
        exception_types: Specific exception types to handle (None = all)
    
    Returns:
        Decorated function with error handling
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Check if we should handle this exception type
                if exception_types and not isinstance(e, tuple(exception_types)):
                    raise
                
                # Create error context
                error_context = {
                    'function_name': func.__name__,
                    'module_name': func.__module__,
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys()),
                    'exception_type': type(e).__name__,
                    'exception_message': str(e),
                    'error_timestamp': datetime.now().isoformat()
                }
                
                # Log the error
                message = custom_message or f"Error in {func.__name__}"
                full_message = f"{message}: {e}"
                
                if log_level.upper() == "CRITICAL":
                    logger.critical(full_message, extra=error_context, exc_info=True)
                elif log_level.upper() == "ERROR":
                    logger.error(full_message, extra=error_context, exc_info=True)
                elif log_level.upper() == "WARNING":
                    logger.warning(full_message, extra=error_context)
                else:
                    logger.info(full_message, extra=error_context)
                
                # Reraise or return default
                if reraise:
                    raise
                else:
                    logger.info(f"Returning default value for {func.__name__}: {default_return}")
                    return default_return
        
        return wrapper
    return decorator


def safe_execute(
    func: Callable,
    *args,
    default_return: Any = None,
    log_errors: bool = True,
    error_message: Optional[str] = None,
    **kwargs
) -> Any:
    """
    Safely execute a function with error handling and logging.
    
    Args:
        func: Function to execute
        *args: Positional arguments for the function
        default_return: Value to return on error
        log_errors: Whether to log errors
        error_message: Custom error message
        **kwargs: Keyword arguments for the function
    
    Returns:
        Function result or default_return on error
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            message = error_message or f"Error executing {func.__name__}"
            logger.error(f"{message}: {e}", exc_info=True)
        return default_return


@contextmanager
def error_context(
    operation_name: str,
    reraise: bool = True,
    log_success: bool = False,
    cleanup_func: Optional[Callable] = None
):
    """
    Context manager for operation-level error handling.
    
    Args:
        operation_name: Name of the operation for logging
        reraise: Whether to reraise exceptions
        log_success: Whether to log successful completion
        cleanup_func: Optional cleanup function to call on error
    
    Yields:
        Dictionary for storing operation context data
    """
    context = {'operation': operation_name, 'start_time': datetime.now()}
    
    try:
        logger.info(f"Starting operation: {operation_name}")
        yield context
        
        if log_success:
            duration = (datetime.now() - context['start_time']).total_seconds()
            logger.info(f"Operation completed successfully: {operation_name} ({duration:.2f}s)")
            
    except Exception as e:
        duration = (datetime.now() - context['start_time']).total_seconds()
        logger.error(
            f"Operation failed: {operation_name} ({duration:.2f}s) - {e}",
            exc_info=True
        )
        
        # Run cleanup if provided
        if cleanup_func:
            try:
                cleanup_func(context)
            except Exception as cleanup_error:
                logger.error(f"Cleanup failed for {operation_name}: {cleanup_error}")
        
        if reraise:
            raise


class ErrorRecovery:
    """
    Utility class for implementing error recovery strategies.
    """
    
    @staticmethod
    def retry_with_backoff(
        func: Callable,
        max_attempts: int = 3,
        backoff_factor: float = 1.0,
        exceptions: Optional[List[Type[Exception]]] = None
    ) -> Any:
        """
        Retry a function with exponential backoff.
        
        Args:
            func: Function to retry
            max_attempts: Maximum number of attempts
            backoff_factor: Backoff multiplier
            exceptions: Exception types to retry on (None = all)
        
        Returns:
            Function result
        
        Raises:
            Last exception if all attempts fail
        """
        import time
        
        last_exception = None
        
        for attempt in range(max_attempts):
            try:
                return func()
            except Exception as e:
                last_exception = e
                
                # Check if we should retry this exception
                if exceptions and not isinstance(e, tuple(exceptions)):
                    raise
                
                if attempt < max_attempts - 1:
                    wait_time = backoff_factor * (2 ** attempt)
                    logger.warning(
                        f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {max_attempts} attempts failed")
        
        raise last_exception
    
    @staticmethod
    def partial_success_handler(
        items: List[Any],
        process_func: Callable,
        error_threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        Process a list of items with partial success handling.
        
        Args:
            items: List of items to process
            process_func: Function to process each item
            error_threshold: Maximum error rate before failing (0.0-1.0)
        
        Returns:
            Dictionary with results, errors, and success rate
        """
        results = []
        errors = []
        
        for i, item in enumerate(items):
            try:
                result = process_func(item)
                results.append({'index': i, 'item': item, 'result': result})
            except Exception as e:
                error_info = {
                    'index': i,
                    'item': item,
                    'error': str(e),
                    'exception_type': type(e).__name__
                }
                errors.append(error_info)
                logger.warning(f"Failed to process item {i}: {e}")
        
        success_rate = len(results) / len(items) if items else 0
        
        # Check if error rate exceeds threshold
        if success_rate < (1 - error_threshold):
            error_msg = (
                f"Processing failed: success rate {success_rate:.2%} "
                f"below threshold {1-error_threshold:.2%}"
            )
            logger.error(error_msg)
            raise FileProcessingError(error_msg)
        
        return {
            'results': results,
            'errors': errors,
            'success_rate': success_rate,
            'total_items': len(items),
            'successful_items': len(results),
            'failed_items': len(errors)
        }


class ErrorAggregator:
    """
    Collects and aggregates errors from multiple operations.
    """
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
    
    def add_error(self, error: Union[str, Exception], context: Optional[Dict] = None):
        """Add an error to the aggregator."""
        error_info = {
            'message': str(error),
            'type': type(error).__name__ if isinstance(error, Exception) else 'Error',
            'timestamp': datetime.now().isoformat(),
            'context': context or {}
        }
        self.errors.append(error_info)
        logger.error(f"[{self.operation_name}] {error}")
    
    def add_warning(self, warning: str, context: Optional[Dict] = None):
        """Add a warning to the aggregator."""
        warning_info = {
            'message': warning,
            'timestamp': datetime.now().isoformat(),
            'context': context or {}
        }
        self.warnings.append(warning_info)
        logger.warning(f"[{self.operation_name}] {warning}")
    
    def has_errors(self) -> bool:
        """Check if any errors were collected."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if any warnings were collected."""
        return len(self.warnings) > 0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of collected errors and warnings."""
        duration = (datetime.now() - self.start_time).total_seconds()
        
        return {
            'operation': self.operation_name,
            'duration_seconds': duration,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'errors': self.errors,
            'warnings': self.warnings,
            'success': len(self.errors) == 0
        }
    
    def raise_if_errors(self, exception_class: Type[Exception] = PMAnalysisError):
        """Raise an exception if any errors were collected."""
        if self.has_errors():
            error_messages = [error['message'] for error in self.errors]
            combined_message = f"{self.operation_name} failed with {len(self.errors)} errors: {'; '.join(error_messages)}"
            raise exception_class(combined_message)


def create_error_response(
    operation: str,
    error: Union[str, Exception],
    context: Optional[Dict] = None,
    suggestions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create a standardized error response dictionary.
    
    Args:
        operation: Name of the operation that failed
        error: Error message or exception
        context: Additional context information
        suggestions: List of suggested solutions
    
    Returns:
        Standardized error response dictionary
    """
    return {
        'success': False,
        'operation': operation,
        'error': {
            'message': str(error),
            'type': type(error).__name__ if isinstance(error, Exception) else 'Error',
            'timestamp': datetime.now().isoformat(),
            'context': context or {},
            'suggestions': suggestions or []
        },
        'data': None
    }


def log_performance_metrics(func: Callable) -> Callable:
    """
    Decorator to log performance metrics for functions.
    
    Args:
        func: Function to monitor
    
    Returns:
        Decorated function with performance logging
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        
        try:
            result = func(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"Performance: {func.__name__} completed in {duration:.3f}s",
                extra={
                    'function': func.__name__,
                    'duration_seconds': duration,
                    'success': True
                }
            )
            
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.error(
                f"Performance: {func.__name__} failed after {duration:.3f}s - {e}",
                extra={
                    'function': func.__name__,
                    'duration_seconds': duration,
                    'success': False,
                    'error': str(e)
                }
            )
            
            raise
    
    return wrapper


# Convenience functions for common error scenarios
def handle_file_error(file_path: str, operation: str, error: Exception) -> FileProcessingError:
    """Create a standardized file processing error."""
    message = f"Failed to {operation} file '{file_path}': {error}"
    logger.error(message, exc_info=True)
    return FileProcessingError(message)


def handle_data_error(data_source: str, operation: str, error: Exception) -> DataExtractionError:
    """Create a standardized data extraction error."""
    message = f"Failed to {operation} data from '{data_source}': {error}"
    logger.error(message, exc_info=True)
    return DataExtractionError(message)


def handle_validation_error(item: str, validation: str, error: Exception) -> ValidationError:
    """Create a standardized validation error."""
    message = f"Validation failed for {item} during {validation}: {error}"
    logger.error(message, exc_info=True)
    return ValidationError(message)