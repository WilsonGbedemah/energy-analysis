import sys
import os
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock
from io import StringIO
import logging

# Add src to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
import data_processor


@patch("pandas.read_csv")
@patch("os.path.exists", return_value=True)
def test_process_and_merge_data(mock_exists, mock_read_csv):
    """Test merging of weather and energy data from raw files"""
    # Mock weather and energy DataFrames
    mock_weather = pd.DataFrame([
        {"city": "New York", "date": "2024-04-01", "tmax_f": 85, "tmin_f": 60},
        {"city": "New York", "date": "2024-04-02", "tmax_f": 88, "tmin_f": 62}
    ])

    mock_energy = pd.DataFrame([
        {"city": "New York", "date": "2024-04-01", "energy_mwh": 2100},
        {"city": "New York", "date": "2024-04-02", "energy_mwh": 2200}
    ])

    # Return weather first, then energy
    mock_read_csv.side_effect = [mock_weather, mock_energy]

    df = data_processor.process_and_merge_data(save_output=False)

    # Assertions
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert df.shape[0] == 2
    assert set(["city", "date", "tmax_f", "tmin_f", "energy_mwh"]).issubset(df.columns)


def test_generate_data_quality_report_creates_report():
    """Test quality check logic and return structure"""
    df = pd.DataFrame([
        {"city": "Seattle", "date": "2024-04-01", "tmax_f": 100, "tmin_f": 60, "energy_mwh": 1500},
        {"city": "Seattle", "date": "2024-04-02", "tmax_f": 135, "tmin_f": 65, "energy_mwh": 1600},  # Outlier
        {"city": "Seattle", "date": "2024-04-03", "tmax_f": 75, "tmin_f": None, "energy_mwh": -50}  # Missing + negative
    ])

    with patch.object(pd.DataFrame, "to_csv") as mock_to_csv:
        quality_df = data_processor.generate_data_quality_report(df)

    assert isinstance(quality_df, pd.DataFrame)
    assert "temperature_outliers" in quality_df.index
    assert "energy_issues" in quality_df.index  # updated from "negative_energy"
    assert "missing_values" in quality_df.index
    assert "data_freshness" in quality_df.index


def test_process_and_merge_data_missing_files(tmp_path):
    """Ensure FileNotFoundError is raised if raw files are missing"""
    # Temporarily change to an empty directory
    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    with pytest.raises(FileNotFoundError):
        data_processor.process_and_merge_data()

    os.chdir(original_cwd)


@patch("pandas.read_csv")
@patch("os.path.exists", return_value=True)
def test_logging_for_data_processing(mock_exists, mock_read_csv, caplog):
    """Ensure logs are written during the process"""
    caplog.set_level(logging.INFO)

    mock_weather = pd.DataFrame([
        {"city": "New York", "date": "2024-04-01", "tmax_f": 85, "tmin_f": 60}
    ])
    mock_energy = pd.DataFrame([
        {"city": "New York", "date": "2024-04-01", "energy_mwh": 2100}
    ])
    mock_read_csv.side_effect = [mock_weather, mock_energy]

    data_processor.process_and_merge_data(save_output=False)

    assert any("Merged dataset shape" in record.message for record in caplog.records)
    assert any("Data quality report saved" in record.message for record in caplog.records)
