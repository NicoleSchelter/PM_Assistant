"""
Reporters package for generating output reports.

This package provides abstract base classes and concrete implementations
for generating reports in different formats from processing results.
"""

from .base_reporter import BaseReporter

__all__ = ["BaseReporter"]
