"""
Performance tests for large file processing.

This module contains performance tests to ensure the PM Analysis Tool
can handle large files efficiently within acceptable time limits.
"""

import os
import tempfile
import time
from pathlib import Path

import pandas as pd
import pytest

from core.engine import PMAnalysisEngine
from core.models import FileInfo, FileFormat, DocumentType
from file_handlers.excel_handler import ExcelHandler
from file_handlers.markdown_handler import MarkdownHandler
from processors.status_analysis import StatusAnalysisProcessor


class TestPerformance:
    """Performance tests for large file processing."""

    @pytest.mark.slow
    def test_large_excel_file_processing(self):
        """Test processing of large Excel files."""
        temp_path = None
        try:
            # Create a large Excel file with 5,000 rows (reduced for reliability)
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as temp_file:
                temp_path = Path(temp_file.name)

            # Generate large dataset
            size = 5000
            data = {
                "Risk ID": [f"R{i:05d}" for i in range(size)],
                "Risk Description": [f"Risk description {i}" for i in range(size)],
                "Probability": (["High", "Medium", "Low"] * (size // 3 + 1))[:size],
                "Impact": (["High", "Medium", "Low"] * (size // 3 + 1))[:size],
                "Status": (["Open", "Closed", "Mitigated"] * (size // 3 + 1))[:size],
                "Owner": [f"Owner {i % 100}" for i in range(size)],
            }

            df = pd.DataFrame(data)
            df.to_excel(temp_path, index=False)

            # Test processing time
            handler = ExcelHandler()
            start_time = time.time()

            result = handler.extract_data(temp_path)

            processing_time = time.time() - start_time

            # Assertions - Excel handler returns dict, not ProcessingResult
            assert isinstance(result, dict), "Expected dict result from excel handler"
            assert processing_time < 30.0, f"Processing took too long: {processing_time:.2f}s"
            assert "structured_data" in result, "No structured data extracted"

        finally:
            # Cleanup
            if temp_path and temp_path.exists():
                try:
                    os.unlink(temp_path)
                except (PermissionError, OSError):
                    # File might be locked on Windows, ignore cleanup error
                    pass

    @pytest.mark.slow
    def test_status_analysis_performance(self):
        """Test performance of status analysis with large datasets."""
        # Create large file info list
        file_infos = []
        for i in range(100):
            file_info = FileInfo(
                path=Path(f"test_file_{i}.xlsx"),
                format=FileFormat.EXCEL,
                document_type=DocumentType.RISK_REGISTER,
                size_bytes=1024 * 1024,  # 1MB each
                is_readable=True,
            )
            file_infos.append(file_info)

        # Test status analysis processing time
        processor = StatusAnalysisProcessor()
        config = {
            "analysis": {
                "risk_thresholds": {"high": 0.7, "medium": 0.4},
                "deliverable_thresholds": {"on_track": 0.8, "at_risk": 0.6},
            }
        }

        start_time = time.time()
        result = processor.process(file_infos, config)
        processing_time = time.time() - start_time

        # Assertions
        assert result.success, f"Status analysis failed: {result.errors}"
        assert processing_time < 10.0, f"Status analysis took too long: {processing_time:.2f}s"