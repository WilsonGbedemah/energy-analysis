import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from src import analysis


@pytest.fixture
def sample_data():
    """Create a dummy DataFrame with valid structure."""
    today = datetime.today().date()
    dates = [today - timedelta(days=i) for i in range(90)]

    data = {
        "date": dates * 2,
        "tmax_f": np.random.uniform(60, 95, 180),
        "tmin_f": np.random.uniform(40, 70, 180),
        "energy_mwh": np.random.uniform(800, 2000, 180),
        "city": ["CityA"] * 90 + ["CityB"] * 90
    }
    return pd.DataFrame(data)


def test_compute_correlation(sample_data):
    corr = analysis.compute_correlation(sample_data)
    assert isinstance(corr, pd.DataFrame)
    assert "tmax_f" in corr.columns
    assert "energy_mwh" in corr.columns


def test_weekday_weekend_analysis(sample_data):
    summary = analysis.weekday_weekend_analysis(sample_data)
    assert "day_type" in summary.columns
    assert set(summary["day_type"]) <= {"Weekday", "Weekend"}


def test_seasonal_pattern_analysis(sample_data):
    result = analysis.seasonal_pattern_analysis(sample_data)
    assert "month" in result.columns
    assert "avg_energy_mwh" in result.columns
    assert result["avg_energy_mwh"].dtype == float


def test_generate_geographic_overview(sample_data):
    overview = analysis.generate_geographic_overview(sample_data)
    assert "energy_pct_change" in overview.columns
    assert "tmax_f" in overview.columns
    assert "city" in overview.columns
    assert overview["energy_pct_change"].dtype in [float, np.float64]


def test_generate_heatmap_matrix(sample_data):
    heatmap = analysis.generate_heatmap_matrix(sample_data)
    assert isinstance(heatmap, pd.DataFrame)
    assert not heatmap.empty
    assert all(isinstance(i, str) for i in heatmap.index)
    assert heatmap.columns.dtype == "object"


def test_generate_analysis_report(sample_data, tmp_path):
    output_dir = tmp_path / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(analysis, "os", os)
        mp.setattr(analysis, "pd", pd)
        mp.setattr(analysis, "np", np)

        results = analysis.generate_analysis_report(sample_data, save=False)
        assert "correlation_matrix" in results
        assert "heatmap_matrix" in results
        assert isinstance(results["correlation_matrix"], pd.DataFrame)
