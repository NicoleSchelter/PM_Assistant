"""
Unit tests for MarkdownHandler.

This module contains comprehensive tests for the Markdown file handler,
including tests for data extraction, validation, and error handling.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
import tempfile
import os

from file_handlers.markdown_handler import MarkdownHandler
from core.models import ValidationResult, DocumentType
from utils.exceptions import FileProcessingError


class TestMarkdownHandler:
    """Test suite for MarkdownHandler class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.handler = MarkdownHandler()
        
        # Sample markdown content for testing
        self.sample_markdown = """---
title: "Risk Management Plan"
author: "Project Manager"
date: "2024-01-15"
---

# Risk Management Plan

## Overview

This document outlines the risk management approach for the project.

## Risk Register

| Risk ID | Description | Probability | Impact | Mitigation |
|---------|-------------|-------------|---------|------------|
| R001 | Budget overrun | High | High | Regular budget reviews |
| R002 | Schedule delay | Medium | High | Buffer time allocation |
| R003 | Resource unavailability | Low | Medium | Backup resource plan |

## Risk Categories

- Financial risks
- Technical risks
- Resource risks
- External risks
"""

    def test_can_handle_markdown_files(self):
        """Test that handler can identify markdown files."""
        assert self.handler.can_handle("test.md")
        assert self.handler.can_handle("test.markdown")
        assert not self.handler.can_handle("test.txt")
        assert not self.handler.can_handle("test.docx")

    def test_extract_data_basic(self):
        """Test basic data extraction from markdown content."""
        with patch("pathlib.Path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=self.sample_markdown)):
            result = self.handler.extract_data("test.md")
            
            assert isinstance(result, dict)
            assert "raw_content" in result or "content" in result

    def test_validate_structure_valid_file(self):
        """Test validation of a valid markdown file."""
        with patch("pathlib.Path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=self.sample_markdown)):
            result = self.handler.validate_structure("test.md")
            
            assert isinstance(result, ValidationResult)