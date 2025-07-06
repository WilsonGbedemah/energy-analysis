import os
import time
import yaml
import logging
import requests
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load .env variables
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

# API keys
NOAA_API_KEY = os.getenv("NOAA_API_KEY")
EIA_API_KEY = os.getenv("EIA_API_KEY")


# Convert tenths of °C to °F
def fahrenheit(c_tenths):
    return round((c_tenths / 10) * 9 / 5 + 32, 2)


# Retry-safe HTTP request
def retry_request(url, headers=None, params=None, max_retries=5):
    delay = 1
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.warning(f"Retry {attempt + 1}/{max_retries} failed: {e}")
            time.sleep(delay)
            delay *= 2
    logging.error(f"❌ Request failed after {max_retries} attempts: {url}")
    return None


# ✅ NOAA Weather Fetch
def fetch_weather_data(start_date: str, end_date: str) -> pd.DataFrame:
    base_url = "https://www.ncei.noaa.gov/cdo-web/api/v2"
    headers = {"token": NOAA_API_KEY}
    all_weather = []

    for city in config["cities"]:
        try:
            params = {
                "datasetid": "GHCND",
                "stationid": city["station_id"],
                "startdate": start_date,
                "enddate": end_date,
                "datatypeid": "TMAX,TMIN",
                "limit": 1000,
                "units": "metric"
            }

            result = retry_request(base_url, headers=headers, params=params)

            if result and "results" in result:
                records = result["results"]
                daily_data = {}

                for record in records:
                    date = record["date"][:10]
                    if date not in daily_data:
                        daily_data[date] = {"city": city["name"], "date": date}

                    if record["datatype"] == "TMAX":
                        daily_data[date]["tmax_f"] = fahrenheit(record["value"])
                    elif record["datatype"] == "TMIN":
                        daily_data[date]["tmin_f"] = fahrenheit(record["value"])

                all_weather.extend(daily_data.values())
                logging.info(f"✅ Weather data fetched for {city['name']}")
            else:
                logging.warning(f"⚠️ No weather data for {city['name']}")
        except Exception as e:
            logging.error(f"❌ Weather fetch failed for {city['name']}: {e}")

    return pd.DataFrame(all_weather)


# ✅ EIA Energy Fetch with Robust Validation
def fetch_energy_data() -> pd.DataFrame:
    base_url = "https://www.eia.gov/electricity/data/browser/"
    all_energy = []

    for city in config["cities"]:
        try:
            params = {
                "api_key": EIA_API_KEY,
                "frequency": "daily",
                "data[0]": "value",
                "facets[respondent]": city["region_code"],
                "sort[0][column]": "period",
                "sort[0][direction]": "desc",
                "offset": 0,
                "length": 90
            }

            result = retry_request(base_url, params=params)

            # ✅ Validate EIA structure
            if not result:
                logging.warning(f"⚠️ Empty EIA response for {city['name']}")
                continue

            if "response" not in result or "data" not in result["response"]:
                logging.error(f"❌ Invalid EIA structure for {city['name']}: {result}")
                continue

            records = result["response"]["data"]
            if not records:
                logging.warning(f"⚠️ No energy records returned for {city['name']}")
                continue

            for record in records:
                all_energy.append({
                    "city": city["name"],
                    "date": record.get("period"),
                    "energy_mwh": record.get("value")
                })

            logging.info(f"✅ Energy data fetched for {city['name']}")

        except Exception as e:
            logging.error(f"❌ Energy fetch failed for {city['name']}: {e}")

    if not all_energy:
        raise ValueError("❌ No energy data was fetched for any city. Check API or config.")

    return pd.DataFrame(all_energy)


# ✅ Save 90-Day Snapshot
def fetch_last_90_days(save=True) -> tuple[pd.DataFrame, pd.DataFrame]:
    end_date = datetime.today().date()
    start_date = end_date - timedelta(days=90)

    weather_df = fetch_weather_data(str(start_date), str(end_date))
    energy_df = fetch_energy_data()

    if save:
        os.makedirs("data/raw", exist_ok=True)
        weather_df.to_csv("data/raw/weather_last_90_days.csv", index=False)
        energy_df.to_csv("data/raw/energy_last_90_days.csv", index=False)
        logging.info("📦 Saved 90-day weather and energy data")

    return weather_df, energy_df


# ✅ Save Daily Data
def fetch_daily_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    today = datetime.today().date()
    weather_df = fetch_weather_data(str(today), str(today))
    energy_df = fetch_energy_data()

    if not weather_df.empty:
        os.makedirs("data/raw/weather", exist_ok=True)
        weather_df.to_csv(f"data/raw/weather/weather_{today}.csv", index=False)
        logging.info("📅 Daily weather saved")
    else:
        logging.warning("⚠️ No weather data to save today")

    if not energy_df.empty:
        os.makedirs("data/raw/energy", exist_ok=True)
        energy_df.to_csv(f"data/raw/energy/energy_{today}.csv", index=False)
        logging.info("📅 Daily energy saved")
    else:
        logging.warning("⚠️ No energy data to save today")

    return weather_df, energy_df
