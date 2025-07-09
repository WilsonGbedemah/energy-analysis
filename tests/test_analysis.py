import sys
import os
import pandas as pd
import numpy as np
import pytest
from datetime import datetime

# Add src to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
import analysis


@pytest.fixture
def sample_df():
    return pd.DataFrame([
        {"city": "New York", "date": "2024-06-01", "tmax_f": 85, "tmin_f": 65, "energy_mwh": 2100},
        {"city": "New York", "date": "2024-06-02", "tmax_f": 90, "tmin_f": 70, "energy_mwh": 2300},
        {"city": "Chicago", "date": "2024-06-01", "tmax_f": 75, "tmin_f": 55, "energy_mwh": 1900},
        {"city": "Chicago", "date": "2024-06-02", "tmax_f": 78, "tmin_f": 60, "energy_mwh": 2000},
    ])


def test_compute_correlation(sample_df):
    corr = analysis.compute_correlation(sample_df)
    assert isinstance(corr, pd.DataFrame)
    assert "energy_mwh" in corr.columns
    assert "tmax_f" in corr.index


def test_weekday_weekend_analysis(sample_df):
    result = analysis.weekday_weekend_analysis(sample_df)
    assert isinstance(result, pd.DataFrame)
    assert set(["day_type", "mean", "std", "count"]).issubset(result.columns)


def test_seasonal_pattern_analysis(sample_df):
    result = analysis.seasonal_pattern_analysis(sample_df)
    assert isinstance(result, pd.DataFrame)
    assert "avg_energy_mwh" in result.columns
    assert "month" in result.columns


def test_generate_geographic_overview(sample_df):
    result = analysis.generate_geographic_overview(sample_df)
    assert isinstance(result, pd.DataFrame)
    assert "energy_pct_change" in result.columns


def test_generate_heatmap_matrix(sample_df):
    result = analysis.generate_heatmap_matrix(sample_df)
    assert isinstance(result, pd.DataFrame)
    assert result.shape[0] > 0
    assert result.columns.tolist()[0] in [
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
    ]
