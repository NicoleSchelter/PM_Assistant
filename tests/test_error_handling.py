"""
Tests for comprehensive error handling and logging functionality.

This module tests the error handling utilities, decorators, and recovery
mechanisms implemented throughout the PM Analysis Tool.
"""

import logging
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from utils.error_handling import (
    ErrorAggregator,
    ErrorRecovery,
    create_error_response,
    error_context,
    handle_data_error,
    handle_errors,
    handle_file_error,
    handle_validation_error,
    log_performance_metrics,
    safe_execute,
)
from utils.exceptions import (
    DataExtractionError,
    FileProcessingError,
    PMAnalysisError,
    ValidationError,
)


class TestErrorHandlingDecorator:
    """Test the handle_errors decorator."""

    def test_handle_errors_success(self):
        """Test decorator with successful function execution."""

        @handle_errors(reraise=False)
        def successful_function():
            return "success"

        result = successful_function()
        assert result == "success"

    def test_handle_errors_with_exception_reraise(self):
        """Test decorator with exception and reraise=True."""

        @handle_errors(reraise=True)
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            failing_function()

    def test_handle_errors_with_exception_no_reraise(self):
        """Test decorator with exception and reraise=False."""

        @handle_errors(reraise=False, default_return="default")
        def failing_function():
            raise ValueError("Test error")

        result = failing_function()
        assert result == "default"

    def test_handle_errors_specific_exception_types(self):
        """Test decorator with specific exception types."""

        @handle_errors(exception_types=[ValueError], reraise=False, default_return="handled")
        def function_with_specific_error():
            raise ValueError("Specific error")

        result = function_with_specific_error()
        assert result == "handled"

        # Test with unhandled exception type
        @handle_errors(exception_types=[ValueError], reraise=False, default_return="handled")
        def function_with_unhandled_error():
            raise TypeError("Unhandled error")

        with pytest.raises(TypeError):
            function_with_unhandled_error()

    def test_handle_errors_custom_message(self):
        """Test decorator with custom error message."""
        with patch("utils.error_handling.logger") as mock_logger:

            @handle_errors(reraise=False, custom_message="Custom error occurred")
            def failing_function():
                raise ValueError("Test error")

            failing_function()
            mock_logger.error.assert_called_once()
            args, kwargs = mock_logger.error.call_args
            assert "Custom error occurred" in args[0]


class TestSafeExecute:
    """Test the safe_execute function."""

    def test_safe_execute_success(self):
        """Test safe execution with successful function."""

        def successful_function(x, y):
            return x + y

        result = safe_execute(successful_function, 2, 3)
        assert result == 5

    def test_safe_execute_with_error(self):
        """Test safe execution with error."""

        def failing_function():
            raise ValueError("Test error")

        result = safe_execute(failing_function, default_return="default", log_errors=False)
        assert result == "default"

    def test_safe_execute_with_kwargs(self):
        """Test safe execution with keyword arguments."""

        def function_with_kwargs(a, b=10):
            return a * b

        result = safe_execute(function_with_kwargs, 5, b=3)
        assert result == 15


class TestErrorContext:
    """Test the error_context context manager."""

    def test_error_context_success(self):
        """Test error context with successful operation."""
        with patch("utils.error_handling.logger") as mock_logger:
            with error_context("test_operation", log_success=True) as context:
                context["result"] = "success"

            # Check that success was logged
            mock_logger.info.assert_called()
            success_call = [
                call
                for call in mock_logger.info.call_args_list
                if "completed successfully" in str(call)
            ]
            assert len(success_call) > 0

    def test_error_context_with_exception(self):
        """Test error context with exception."""
        with patch("utils.error_handling.logger") as mock_logger:
            with pytest.raises(ValueError):
                with error_context("test_operation") as context:
                    raise ValueError("Test error")

            # Check that error was logged
            mock_logger.error.assert_called()
            error_call = [
                call for call in mock_logger.error.call_args_list if "Operation failed" in str(call)
            ]
            assert len(error_call) > 0

    def test_error_context_with_cleanup(self):
        """Test error context with cleanup function."""
        cleanup_called = False

        def cleanup_func(context):
            nonlocal cleanup_called
            cleanup_called = True

        with pytest.raises(ValueError):
            with error_context("test_operation", cleanup_func=cleanup_func):
                raise ValueError("Test error")

        assert cleanup_called


class TestErrorRecovery:
    """Test the ErrorRecovery utility class."""

    def test_retry_with_backoff_success(self):
        """Test retry with successful execution."""
        call_count = 0

        def function_that_succeeds():
            nonlocal call_count
            call_count += 1
            return "success"

        result = ErrorRecovery.retry_with_backoff(function_that_succeeds)
        assert result == "success"
        assert call_count == 1

    def test_retry_with_backoff_eventual_success(self):
        """Test retry with eventual success after failures."""
        call_count = 0

        def function_that_eventually_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"

        result = ErrorRecovery.retry_with_backoff(
            function_that_eventually_succeeds,
            max_attempts=3,
            backoff_factor=0.01,  # Small backoff for testing
        )
        assert result == "success"
        assert call_count == 3

    def test_retry_with_backoff_all_attempts_fail(self):
        """Test retry when all attempts fail."""
        call_count = 0

        def function_that_always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Persistent error")

        with pytest.raises(ValueError, match="Persistent error"):
            ErrorRecovery.retry_with_backoff(
                function_that_always_fails, max_attempts=3, backoff_factor=0.01
            )

        assert call_count == 3

    def test_partial_success_handler_all_success(self):
        """Test partial success handler with all items succeeding."""
        items = [1, 2, 3, 4, 5]

        def process_func(item):
            return item * 2

        result = ErrorRecovery.partial_success_handler(items, process_func)

        assert result["success_rate"] == 1.0
        assert result["successful_items"] == 5
        assert result["failed_items"] == 0
        assert len(result["results"]) == 5
        assert len(result["errors"]) == 0

    def test_partial_success_handler_partial_success(self):
        """Test partial success handler with some failures."""
        items = [1, 2, 3, 4, 5]

        def process_func(item):
            if item == 3:
                raise ValueError("Error processing 3")
            return item * 2

        result = ErrorRecovery.partial_success_handler(
            items, process_func, error_threshold=0.3  # Allow up to 30% errors
        )

        assert result["success_rate"] == 0.8  # 4/5 success
        assert result["successful_items"] == 4
        assert result["failed_items"] == 1
        assert len(result["results"]) == 4
        assert len(result["errors"]) == 1

    def test_partial_success_handler_exceeds_threshold(self):
        """Test partial success handler when error threshold is exceeded."""
        items = [1, 2, 3, 4, 5]

        def process_func(item):
            if item in [2, 3, 4]:
                raise ValueError(f"Error processing {item}")
            return item * 2

        with pytest.raises(FileProcessingError):
            ErrorRecovery.partial_success_handler(
                items, process_func, error_threshold=0.3  # Only allow 30% errors, but we have 60%
            )


class TestErrorAggregator:
    """Test the ErrorAggregator class."""

    def test_error_aggregator_basic_usage(self):
        """Test basic error aggregator functionality."""
        aggregator = ErrorAggregator("test_operation")

        aggregator.add_error("First error")
        aggregator.add_warning("First warning")
        aggregator.add_error(ValueError("Second error"))

        assert aggregator.has_errors()
        assert aggregator.has_warnings()

        summary = aggregator.get_summary()
        assert summary["operation"] == "test_operation"
        assert summary["error_count"] == 2
        assert summary["warning_count"] == 1
        assert not summary["success"]

    def test_error_aggregator_raise_if_errors(self):
        """Test error aggregator raise_if_errors method."""
        aggregator = ErrorAggregator("test_operation")

        # Should not raise when no errors
        aggregator.raise_if_errors()

        # Should raise when errors exist
        aggregator.add_error("Test error")
        with pytest.raises(PMAnalysisError):
            aggregator.raise_if_errors()

    def test_error_aggregator_custom_exception(self):
        """Test error aggregator with custom exception type."""
        aggregator = ErrorAggregator("test_operation")
        aggregator.add_error("Test error")

        with pytest.raises(ValidationError):
            aggregator.raise_if_errors(ValidationError)


class TestUtilityFunctions:
    """Test utility functions for error handling."""

    def test_create_error_response(self):
        """Test create_error_response function."""
        response = create_error_response(
            operation="test_operation",
            error="Test error message",
            context={"key": "value"},
            suggestions=["Try this", "Or this"],
        )

        assert not response["success"]
        assert response["operation"] == "test_operation"
        assert response["error"]["message"] == "Test error message"
        assert response["error"]["context"] == {"key": "value"}
        assert response["error"]["suggestions"] == ["Try this", "Or this"]
        assert response["data"] is None

    def test_log_performance_metrics_success(self):
        """Test performance metrics logging for successful function."""
        with patch("utils.error_handling.logger") as mock_logger:

            @log_performance_metrics
            def test_function():
                return "result"

            result = test_function()
            assert result == "result"

            # Check that performance was logged
            mock_logger.info.assert_called()
            args, kwargs = mock_logger.info.call_args
            assert "Performance:" in args[0]
            assert "completed" in args[0]

    def test_log_performance_metrics_failure(self):
        """Test performance metrics logging for failing function."""
        with patch("utils.error_handling.logger") as mock_logger:

            @log_performance_metrics
            def failing_function():
                raise ValueError("Test error")

            with pytest.raises(ValueError):
                failing_function()

            # Check that performance failure was logged
            mock_logger.error.assert_called()
            args, kwargs = mock_logger.error.call_args
            assert "Performance:" in args[0]
            assert "failed" in args[0]

    def test_handle_file_error(self):
        """Test handle_file_error convenience function."""
        original_error = IOError("Permission denied")

        with patch("utils.error_handling.logger") as mock_logger:
            result = handle_file_error("/path/to/file", "read", original_error)

            assert isinstance(result, FileProcessingError)
            assert "Failed to read file '/path/to/file'" in str(result)
            mock_logger.error.assert_called_once()

    def test_handle_data_error(self):
        """Test handle_data_error convenience function."""
        original_error = ValueError("Invalid format")

        with patch("utils.error_handling.logger") as mock_logger:
            result = handle_data_error("data_source", "parse", original_error)

            assert isinstance(result, DataExtractionError)
            assert "Failed to parse data from 'data_source'" in str(result)
            mock_logger.error.assert_called_once()

    def test_handle_validation_error(self):
        """Test handle_validation_error convenience function."""
        original_error = TypeError("Wrong type")

        with patch("utils.error_handling.logger") as mock_logger:
            result = handle_validation_error("item", "type_check", original_error)

            assert isinstance(result, ValidationError)
            assert "Validation failed for item during type_check" in str(result)
            mock_logger.error.assert_called_once()


class TestIntegrationScenarios:
    """Test integration scenarios with multiple error handling components."""

    def test_complex_error_scenario(self):
        """Test a complex scenario with multiple error handling components."""
        aggregator = ErrorAggregator("complex_operation")

        # Simulate a complex operation with multiple steps
        with error_context("step_1") as context:
            try:
                # Step that might fail
                result = safe_execute(
                    lambda: 10 / 0, default_return=None, log_errors=False  # Division by zero
                )
                if result is None:
                    aggregator.add_error("Division by zero in step 1")
            except Exception as e:
                aggregator.add_error(f"Unexpected error in step 1: {e}")

        # Another step with partial success
        items = [1, 2, 3, 4, 5]
        try:
            partial_result = ErrorRecovery.partial_success_handler(
                items, lambda x: x if x != 3 else 1 / 0, error_threshold=0.3  # Fail on item 3
            )
            aggregator.add_warning(f"Partial success: {partial_result['success_rate']:.1%}")
        except Exception as e:
            aggregator.add_error(f"Partial processing failed: {e}")

        # Check final state
        assert aggregator.has_errors()
        assert aggregator.has_warnings()

        summary = aggregator.get_summary()
        assert summary["error_count"] >= 1
        assert summary["warning_count"] >= 1
        assert not summary["success"]

    def test_recovery_with_logging(self):
        """Test error recovery with comprehensive logging."""
        with patch("utils.error_handling.logger") as mock_logger:
            call_count = 0

            def unreliable_function():
                nonlocal call_count
                call_count += 1
                if call_count < 3:
                    raise ConnectionError("Network error")
                return "success"

            # Use retry with backoff
            result = ErrorRecovery.retry_with_backoff(
                unreliable_function,
                max_attempts=3,
                backoff_factor=0.01,
                exceptions=[ConnectionError],
            )

            assert result == "success"
            assert call_count == 3

            # Check that warnings were logged for retries
            warning_calls = [
                call for call in mock_logger.warning.call_args_list if "retrying" in str(call)
            ]
            assert len(warning_calls) == 2  # Two retries before success


if __name__ == "__main__":
    pytest.main([__file__])
