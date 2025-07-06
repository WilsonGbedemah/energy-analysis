import sys
import os
import pandas as pd
import pytest
from unittest.mock import patch

# Add src to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
import data_processor


@patch("data_processor.fetch_last_90_days")
def test_process_and_merge_data(mock_fetch):
    # Mock weather and energy DataFrames
    mock_weather = pd.DataFrame([
        {"city": "New York", "date": "2024-04-01", "tmax_f": 85, "tmin_f": 60},
        {"city": "New York", "date": "2024-04-02", "tmax_f": 88, "tmin_f": 62}
    ])

    mock_energy = pd.DataFrame([
        {"city": "New York", "date": "2024-04-01", "energy_mwh": 2100},
        {"city": "New York", "date": "2024-04-02", "energy_mwh": 2200}
    ])

    mock_fetch.return_value = (mock_weather, mock_energy)

    df = data_processor.process_and_merge_data(save_output=False)

    # Assertions
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert df.shape[0] == 2
    assert set(["city", "date", "tmax_f", "tmin_f", "energy_mwh"]).issubset(df.columns)


def test_generate_data_quality_report_creates_report(tmp_path):
    # Build fake cleaned dataset
    df = pd.DataFrame([
        {"city": "Seattle", "date": "2024-04-01", "tmax_f": 100, "tmin_f": 60, "energy_mwh": 1500},
        {"city": "Seattle", "date": "2024-04-02", "tmax_f": 135, "tmin_f": 65, "energy_mwh": 1600},  # Outlier
        {"city": "Seattle", "date": "2024-04-03", "tmax_f": 75, "tmin_f": None, "energy_mwh": -50}  # Missing + invalid
    ])

    # Temporarily override the save location
    original_path = "data/processed/data_quality_report.csv"
    test_report_path = tmp_path / "data_quality_report.csv"
    os.makedirs(tmp_path, exist_ok=True)

    # Monkey patch path inside function (not ideal but effective for now)
    data_processor.generate_data_quality_report.__globals__["os"].makedirs(tmp_path, exist_ok=True)
    data_processor.generate_data_quality_report.__globals__["pd"].DataFrame.to_csv = lambda self, *args, **kwargs: self

    # Run function
    quality_df = data_processor.generate_data_quality_report(df)

    # Validate content
    assert isinstance(quality_df, pd.DataFrame)
    assert "temperature_outliers" in quality_df.index
    assert "negative_energy" in quality_df.index
    assert "missing_values" in quality_df.index
