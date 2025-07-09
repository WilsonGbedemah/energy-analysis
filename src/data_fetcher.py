import os
import time
import yaml
import json
import logging
import requests
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

# Load environment variables
load_dotenv()

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/pipeline.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Load config.yaml
try:
    with open("config/config.yaml", "r") as f:
        config = yaml.safe_load(f)
        if config is None:
            raise ValueError("⚠️ config.yaml is empty or invalid.")
except FileNotFoundError:
    raise FileNotFoundError("❌ config/config.yaml file not found.")

# API Keys
NOAA_API_KEY = os.getenv("NOAA_API_KEY")
EIA_API_KEY = os.getenv("EIA_API_KEY")

# Exponential backoff handler
def _get_with_backoff(url, params, headers=None, max_retries=3, backoff_factor=1):
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            return resp
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else None
            if status and 500 <= status < 600 and attempt < max_retries:
                wait = backoff_factor * (2 ** (attempt - 1))
                logging.warning(f"⚠️ Attempt {attempt}: HTTP {status}, retrying in {wait}s…")
                time.sleep(wait)
                continue
            raise
        except requests.exceptions.RequestException as e:
            if attempt < max_retries:
                wait = backoff_factor * (2 ** (attempt - 1))
                logging.warning(f"⚠️ Attempt {attempt}: {e}, retrying in {wait}s…")
                time.sleep(wait)
                continue
            raise  # ✅ Re-raise the original RequestException here


# ✅ NOAA Weather Fetch
def fetch_weather_data(days=90) -> None:
    url = "https://www.ncei.noaa.gov/cdo-web/api/v2/data"
    headers = {"token": NOAA_API_KEY}
    os.makedirs("data/raw/weather", exist_ok=True)

    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=days * 2)  # get extra to ensure full 90 valid

    for city in config["cities"]:
        all_records = []
        offset = 0
        limit = 1000

        try:
            while True:
                params = {
                    "datasetid": "GHCND",
                    "stationid": city["station_id"],
                    "startdate": start.isoformat(),
                    "enddate": end.isoformat(),
                    "datatypeid": "TMAX,TMIN",
                    "limit": limit,
                    "offset": offset,
                    "units": "metric"
                }

                resp = _get_with_backoff(url, params=params, headers=headers)
                records = resp.json().get("results", [])
                if not records:
                    break

                all_records.extend(records)
                if len(records) < limit:
                    break
                offset += limit

            if not all_records:
                logging.warning(f"⚠️ No weather data for {city['name']}")
                continue

            df_raw = pd.DataFrame(all_records)
            df_pivot = df_raw.pivot_table(index="date", columns="datatype", values="value", aggfunc="first").reset_index()

            # Convert and rename
            if "TMAX" in df_pivot:
                df_pivot["tmax_f"] = df_pivot["TMAX"].apply(lambda x: (x / 10 * 9/5) + 32 if pd.notnull(x) else None)
            if "TMIN" in df_pivot:
                df_pivot["tmin_f"] = df_pivot["TMIN"].apply(lambda x: (x / 10 * 9/5) + 32 if pd.notnull(x) else None)

            df_pivot["city"] = city["name"]
            df_pivot["date"] = pd.to_datetime(df_pivot["date"])
            df_pivot = df_pivot.sort_values("date")

            # Keep only complete rows
            df_complete = df_pivot.dropna(subset=["tmax_f", "tmin_f"]).tail(days)

            if len(df_complete) < days:
                logging.warning(f"⚠️ Only {len(df_complete)} complete days found for {city['name']} (expected: {days})")

            file_path = f"data/raw/weather/{city['name'].replace(' ', '_')}_weather_90_days.csv"
            df_complete.to_csv(file_path, index=False)
            logging.info(f"✅ Weather saved: {file_path}")

        except Exception as e:
            logging.error(f"❌ Weather fetch failed for {city['name']}: {e}")

# ✅ EIA Energy Fetch
def fetch_energy_data(days=90) -> None:
    url = "https://api.eia.gov/v2/electricity/rto/daily-region-data/data/"
    os.makedirs("data/raw/energy", exist_ok=True)

    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=days - 1)

    for city in config["cities"]:
        try:
            params = {
                "api_key": EIA_API_KEY,
                "frequency": "daily",
                "start": start.isoformat(),
                "end": end.isoformat(),
                "data[0]": "value",
                "facets[respondent][]": city["region_code"],
                "sort[0][column]": "period",
                "sort[0][direction]": "asc",
                "offset": 0,
                "length": days
            }

            resp = _get_with_backoff(url, params=params)
            data = resp.json().get("response", {}).get("data", [])
            if not data:
                logging.warning(f"⚠️ No energy data for {city['name']}")
                continue

            df = pd.DataFrame(data)

            # Rename and structure
            df["city"] = city["name"]
            df["date"] = pd.to_datetime(df["period"])
            df = df.rename(columns={
                "value": "energy_mwh",
                "respondent": "region_code",
                "respondent-name": "region_name",
                "fueltype": "fuel_type",
                "unit": "unit"
            })

            # Filter required date range
            df = df.sort_values("date")
            df = df[df["date"].dt.date.between(start, end)]

            # Optional: drop unwanted columns
            keep_cols = ["city", "date", "energy_mwh", "unit", "region_code", "region_name", "fuel_type"]
            df = df[[col for col in keep_cols if col in df.columns]]

            file_path = f"data/raw/energy/{city['name'].replace(' ', '_')}_energy_90_days.csv"
            df.to_csv(file_path, index=False)
            logging.info(f"✅ Energy saved: {file_path}")

        except Exception as e:
            logging.error(f"❌ Energy fetch failed for {city['name']}: {e}")


# ✅ Merge Per-City Files
def merge_city_files() -> tuple[pd.DataFrame, pd.DataFrame]:
    weather_path = "data/raw/weather/"
    energy_path = "data/raw/energy/"

    weather_files = [os.path.join(weather_path, f) for f in os.listdir(weather_path) if f.endswith(".csv")]
    energy_files = [os.path.join(energy_path, f) for f in os.listdir(energy_path) if f.endswith(".csv")]

    try:
        weather_df = pd.concat([pd.read_csv(f) for f in weather_files], ignore_index=True)
        energy_df = pd.concat([pd.read_csv(f) for f in energy_files], ignore_index=True)
        return weather_df, energy_df
    except Exception as e:
        logging.error(f"❌ Failed to merge city files: {e}")
        raise

# ✅ 90-Day Fetch Trigger
def fetch_last_90_days(save=True) -> tuple[pd.DataFrame, pd.DataFrame]:
    fetch_weather_data(days=90)
    fetch_energy_data(days=90)

    weather_df, energy_df = merge_city_files()

    if save:
        weather_df.to_csv("data/raw/weather_last_90_days.csv", index=False)
        energy_df.to_csv("data/raw/energy_last_90_days.csv", index=False)
        logging.info("📦 Merged 90-day weather and energy saved to data/raw/")

    return weather_df, energy_df
