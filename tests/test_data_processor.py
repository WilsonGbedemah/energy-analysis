import os
import shutil
import pandas as pd
from datetime import datetime, timedelta
from data_processor import (
    process_city_data,
    generate_data_quality_report,
    process_all_cities
)

# Setup test directories
TEST_DATA_DIR = "tests/test_data"
TEST_WEATHER_PATH = f"{TEST_DATA_DIR}/weather.csv"
TEST_ENERGY_PATH = f"{TEST_DATA_DIR}/energy.csv"
TEST_PROCESSED_DIR = "data/processed"
TEST_LOG_FILE = "logs/processor_run.log"

def setup_module(module):
    os.makedirs(TEST_DATA_DIR, exist_ok=True)

    today = datetime.today().date()
    dates = [(today - timedelta(days=i)) for i in range(3)]

    # Weather test data
    weather_df = pd.DataFrame({
        "date": [d.isoformat() for d in dates],
        "tmax_f": [100, 95, 105],
        "tmin_f": [70, 68, 65],
        "tmax_c": [37.78, 35.0, 40.56],
        "tmin_c": [21.1, 20.0, 18.33]
    })
    weather_df.to_csv(TEST_WEATHER_PATH, index=False)

    # Energy test data
    energy_df = pd.DataFrame({
        "date": [d.isoformat() for d in dates],
        "energy_mwh": [1000, 980, 1020]
    })
    energy_df.to_csv(TEST_ENERGY_PATH, index=False)


def teardown_module(module):
    if os.path.exists(TEST_DATA_DIR):
        shutil.rmtree(TEST_DATA_DIR)
    for file in os.listdir(TEST_PROCESSED_DIR):
        if file.startswith("test_city"):
            os.remove(os.path.join(TEST_PROCESSED_DIR, file))


def test_process_city_data_creates_cleaned_file():
    df = process_city_data(TEST_WEATHER_PATH, TEST_ENERGY_PATH, city="test_city")
    assert not df.empty
    assert "energy_mwh" in df.columns
    assert "tmax_f" in df.columns

    out_file = os.path.join(TEST_PROCESSED_DIR, "test_city_cleaned.csv")
    assert os.path.exists(out_file)


def test_generate_data_quality_report_outputs_expected_fields():
    df = pd.read_csv(os.path.join(TEST_PROCESSED_DIR, "test_city_cleaned.csv"))
    report = generate_data_quality_report(df, "test_city")
    assert not report.empty
    assert set(["check", "column", "count", "note"]).issubset(report.columns)


def test_process_city_data_with_missing_energy_column():
    # Simulate missing 'energy_mwh', fallback to 'demand'
    energy_df = pd.read_csv(TEST_ENERGY_PATH)
    energy_df.rename(columns={"energy_mwh": "demand"}, inplace=True)
    path = f"{TEST_DATA_DIR}/energy_renamed.csv"
    energy_df.to_csv(path, index=False)

    df = process_city_data(TEST_WEATHER_PATH, path, city="test_city_renamed")
    assert "energy_mwh" in df.columns


def test_process_city_data_with_outliers_and_nulls():
    # Insert nulls and outliers
    weather_df = pd.read_csv(TEST_WEATHER_PATH)
    weather_df.loc[0, "tmax_f"] = 150  # Outlier
    weather_df.loc[1, "tmin_f"] = -60  # Outlier
    weather_df.loc[2, "tmax_f"] = None  # Missing

    energy_df = pd.read_csv(TEST_ENERGY_PATH)
    energy_df.loc[2, "energy_mwh"] = -5  # Invalid
    weather_df.to_csv(TEST_WEATHER_PATH, index=False)
    energy_df.to_csv(TEST_ENERGY_PATH, index=False)

    df = process_city_data(TEST_WEATHER_PATH, TEST_ENERGY_PATH, city="test_city_invalid")
    report_file = os.path.join(TEST_PROCESSED_DIR, "test_city_invalid_quality_report.csv")
    report_df = pd.read_csv(report_file)
    assert "temperature_outliers" in report_df["check"].values
    assert "energy_issues" in report_df["check"].values


def test_process_all_cities_runs_without_error():
    process_all_cities()
    # Should not raise error
