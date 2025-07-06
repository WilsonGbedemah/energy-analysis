import os
import sys
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

# Add src/ to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
import data_fetcher


# -------------------- WEATHER DATA -------------------- #

@patch("data_fetcher.retry_request")
def test_fetch_weather_data_success(mock_retry_request):
    mock_retry_request.return_value = {
        "results": [
            {"station": "GHCND:USW00094728", "date": "2024-04-01T00:00:00", "datatype": "TMAX", "value": 180},
            {"station": "GHCND:USW00094728", "date": "2024-04-01T00:00:00", "datatype": "TMIN", "value": 40}
        ]
    }

    df = data_fetcher.fetch_weather_data("2024-04-01", "2024-04-02")

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert set(["city", "date", "tmax_f", "tmin_f"]).issubset(df.columns)
    assert df.iloc[0]["tmax_f"] == data_fetcher.fahrenheit(180)
    assert df.iloc[0]["tmin_f"] == data_fetcher.fahrenheit(40)


@patch("data_fetcher.retry_request")
def test_fetch_weather_data_empty_result(mock_retry_request):
    mock_retry_request.return_value = {"results": []}
    df = data_fetcher.fetch_weather_data("2024-04-01", "2024-04-02")
    assert df.empty


# -------------------- ENERGY DATA -------------------- #

@patch("data_fetcher.retry_request")
def test_fetch_energy_data_success(mock_retry_request):
    mock_retry_request.return_value = {
        "response": {
            "data": [
                {"period": "2024-04-01", "value": 2541.3, "respondent": "NYIS"}
            ]
        }
    }

    df = data_fetcher.fetch_energy_data()

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "city" in df.columns
    assert "date" in df.columns
    assert "energy_mwh" in df.columns
    assert df.iloc[0]["energy_mwh"] == 2541.3


@patch("data_fetcher.retry_request")
def test_fetch_energy_data_missing_response(mock_retry_request):
    mock_retry_request.return_value = {}  # No 'response'

    with pytest.raises(ValueError, match="No energy data was fetched"):
        data_fetcher.fetch_energy_data()



@patch("data_fetcher.retry_request")
def test_fetch_energy_data_missing_data_key(mock_retry_request):
    mock_retry_request.return_value = {"response": {}}

    with pytest.raises(ValueError, match="No energy data was fetched"):
        data_fetcher.fetch_energy_data()



# -------------------- RETRY REQUEST -------------------- #

@patch("data_fetcher.requests.get")
def test_retry_request_success(mock_get):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"ok": True}
    mock_get.return_value = mock_response

    result = data_fetcher.retry_request("http://example.com")
    assert result == {"ok": True}


@patch("data_fetcher.requests.get")
def test_retry_request_failure(mock_get):
    mock_get.side_effect = Exception("Simulated failure")

    result = data_fetcher.retry_request("http://fail.com", max_retries=2)
    assert result is None


# -------------------- BULK FETCHING -------------------- #

@patch("data_fetcher.fetch_weather_data")
@patch("data_fetcher.fetch_energy_data")
def test_fetch_last_90_days(mock_energy, mock_weather):
    mock_weather.return_value = pd.DataFrame([
        {"city": "New York", "date": "2024-04-01", "tmax_f": 80, "tmin_f": 60}
    ])
    mock_energy.return_value = pd.DataFrame([
        {"city": "New York", "date": "2024-04-01", "energy_mwh": 2000}
    ])

    weather_df, energy_df = data_fetcher.fetch_last_90_days(save=False)

    assert not weather_df.empty
    assert not energy_df.empty
    assert "tmax_f" in weather_df.columns
    assert "energy_mwh" in energy_df.columns


@patch("data_fetcher.fetch_weather_data")
@patch("data_fetcher.fetch_energy_data")
def test_fetch_daily_data(mock_energy, mock_weather):
    mock_weather.return_value = pd.DataFrame([
        {"city": "Chicago", "date": "2024-07-01", "tmax_f": 90, "tmin_f": 70}
    ])
    mock_energy.return_value = pd.DataFrame([
        {"city": "Chicago", "date": "2024-07-01", "energy_mwh": 2400}
    ])

    weather_df, energy_df = data_fetcher.fetch_daily_data()

    assert not weather_df.empty
    assert not energy_df.empty
    assert "tmax_f" in weather_df.columns
    assert "energy_mwh" in energy_df.columns
