import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Add src/ to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from pipeline import run_pipeline


@patch("pipeline.generate_analysis_report")
@patch("pipeline.process_and_merge_data")
@patch("pipeline.fetch_last_90_days")
def test_run_pipeline_success(mock_fetch, mock_process, mock_analyze):
    # Mock return values
    mock_fetch.return_value = None
    mock_df = MagicMock(name="merged_df")
    mock_process.return_value = mock_df
    mock_analyze.return_value = {}

    # Run pipeline
    run_pipeline()

    # Assert calls
    mock_fetch.assert_called_once()
    mock_process.assert_called_once()
    mock_analyze.assert_called_once_with(mock_df, save=True)
