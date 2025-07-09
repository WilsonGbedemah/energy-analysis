import os
import sys
import pytest
import requests
import pandas as pd
from unittest.mock import patch, MagicMock

# Add src/ to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
import data_fetcher


# -------------------- BACKOFF REQUEST -------------------- #

@patch("data_fetcher.requests.get")
def test_get_with_backoff_success(mock_get):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"results": True}
    mock_get.return_value = mock_response

    result = data_fetcher._get_with_backoff("http://example.com", params={})
    assert result.json() == {"results": True}


@patch("data_fetcher.requests.get")
def test_get_with_backoff_failure(mock_get):
    mock_get.side_effect = requests.exceptions.RequestException("Simulated failure")

    with pytest.raises(requests.exceptions.RequestException):
        data_fetcher._get_with_backoff("http://fail.com", params={}, max_retries=2)


# -------------------- WEATHER FETCH -------------------- #

@patch("data_fetcher._get_with_backoff")
@patch("pandas.DataFrame.to_csv")
@patch.dict("data_fetcher.config", {"cities": [{"name": "TestCity", "station_id": "FAKE_ID"}]})
def test_fetch_weather_data(mock_to_csv, mock_get):
    # Simulate NOAA API response for both TMAX and TMIN
    mock_get.return_value.json.return_value = {
        "results": [
            {"date": "2024-07-01", "datatype": "TMAX", "value": 300},
            {"date": "2024-07-01", "datatype": "TMIN", "value": 200},
            {"date": "2024-07-02", "datatype": "TMAX", "value": 310},
            {"date": "2024-07-02", "datatype": "TMIN", "value": 210},
        ]
    }

    data_fetcher.fetch_weather_data(days=2)
    mock_to_csv.assert_called_once()

    # Check if correct structure is created
    args, _ = mock_to_csv.call_args
    df_saved = args[0]
    assert isinstance(df_saved, str)  # It's the file path

# -------------------- ENERGY FETCH -------------------- #

@patch("data_fetcher._get_with_backoff")
@patch("pandas.DataFrame.to_csv")
@patch.dict("data_fetcher.config", {"cities": [{"name": "TestCity", "region_code": "TST"}]})
def test_fetch_energy_data(mock_to_csv, mock_get):
    mock_get.return_value.json.return_value = {
        "response": {
            "data": [
                {
                    "period": "2024-07-01",
                    "value": 2300,
                    "unit": "MWh",
                    "respondent": "TST",
                    "respondent-name": "Test Region",
                    "fueltype": "All"
                }
            ]
        }
    }

    data_fetcher.fetch_energy_data(days=1)
    mock_to_csv.assert_called_once()

    # Check correct CSV structure
    args, _ = mock_to_csv.call_args
    df_saved = args[0]
    assert isinstance(df_saved, str)


# -------------------- MERGE -------------------- #

@patch("os.listdir")
@patch("pandas.read_csv")
def test_merge_city_files(mock_read_csv, mock_listdir):
    mock_listdir.side_effect = [
        ["TestCity_weather_90_days.csv"],  # weather
        ["TestCity_energy_90_days.csv"]   # energy
    ]
    mock_df = pd.DataFrame([{"city": "TestCity", "date": "2024-07-01"}])
    mock_read_csv.return_value = mock_df

    weather_df, energy_df = data_fetcher.merge_city_files()
    assert isinstance(weather_df, pd.DataFrame)
    assert isinstance(energy_df, pd.DataFrame)
    assert not weather_df.empty
    assert not energy_df.empty


# -------------------- FULL FETCH -------------------- #

@patch("data_fetcher.merge_city_files")
@patch("data_fetcher.fetch_weather_data")
@patch("data_fetcher.fetch_energy_data")
def test_fetch_last_90_days(mock_energy, mock_weather, mock_merge):
    mock_merge.return_value = (
        pd.DataFrame([{"city": "TestCity", "date": "2024-07-01", "tmax_f": 90, "tmin_f": 60}]),
        pd.DataFrame([{"city": "TestCity", "date": "2024-07-01", "energy_mwh": 2000}])
    )

    weather_df, energy_df = data_fetcher.fetch_last_90_days(save=False)

    assert not weather_df.empty
    assert not energy_df.empty
    assert "tmax_f" in weather_df.columns
    assert "energy_mwh" in energy_df.columns
