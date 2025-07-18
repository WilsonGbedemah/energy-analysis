import os
import sys
import pytest
import requests
import pandas as pd
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Add src/ path to allow import of data_fetcher
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
import data_fetcher

# --- Test: Backoff mechanism --- #

@patch("data_fetcher.requests.get")
def test_get_with_backoff_success(mock_get):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": True}
    mock_get.return_value = mock_response

    result = data_fetcher._get_with_backoff("http://example.com", params={})
    assert result.status_code == 200
    assert result.json() == {"results": True}

@patch("data_fetcher.requests.get")
def test_get_with_backoff_failure(mock_get):
    mock_get.side_effect = requests.exceptions.RequestException("Simulated failure")

    with pytest.raises(requests.exceptions.RequestException):
        data_fetcher._get_with_backoff("http://fail.com", params={}, max_retries=2)

# --- Test: fetch_historical_weather --- #

@patch("data_fetcher._get_with_backoff")
def test_fetch_historical_weather(mock_get):
    mock_get.return_value.json.return_value = {
        "results": [
            {"date": "2025-07-10", "datatype": "TMAX", "value": 300},
            {"date": "2025-07-10", "datatype": "TMIN", "value": 200},
            {"date": "2025-07-11", "datatype": "TMAX", "value": 310},
            {"date": "2025-07-11", "datatype": "TMIN", "value": 210},
        ]
    }

    df = data_fetcher.fetch_historical_weather("FAKE_STATION", days=2, city_name="TestCity")
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["date", "tmax_c", "tmin_c", "tmax_f", "tmin_f", "city"]
    assert df.shape[0] == 2
    assert df.iloc[0]["city"] == "TestCity"
    assert round(df.iloc[0]["tmax_c"], 2) == 30.00
    assert round(df.iloc[0]["tmin_f"], 2) == 68.0

# --- Test: fetch_historical_energy --- #

@patch("data_fetcher._get_with_backoff")
def test_fetch_historical_energy(mock_get):
    mock_get.return_value.json.return_value = {
        "response": {
            "data": [
                {"period": "2025-07-10", "value": "1000", "timezone": "Pacific"},
                {"period": "2025-07-11", "value": "1100", "timezone": "Pacific"},
                {"period": "2025-07-11", "value": "999", "timezone": "Eastern"},  # Should be excluded
            ]
        }
    }

    df = data_fetcher.fetch_historical_energy(region_code="TST", days=2, city_name="TestCity")
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["date", "demand", "timezone", "city"]
    assert df.shape[0] == 2
    assert df.iloc[0]["city"] == "TestCity"
    assert float(df.iloc[0]["demand"]) == 1000.0
