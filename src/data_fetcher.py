import os
import time
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import logging

# ─── Setup logging ───────────────────────────────────────────── #
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/fetcher_run.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Load API keys
load_dotenv()
NOAA_API_KEY = os.getenv("NOAA_API_KEY")
EIA_API_KEY = os.getenv("EIA_API_KEY")

def _get_with_backoff(url, params, headers=None, max_retries=3, backoff_factor=1):
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            return resp
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response else None
            msg = f"HTTP error {status} on attempt {attempt}: {e}"
            if status and 500 <= status < 600 and attempt < max_retries:
                wait = backoff_factor * (2 ** (attempt - 1))
                logging.warning(f"{msg} - Retrying in {wait}s")
                time.sleep(wait)
            else:
                logging.error(msg)
                raise
        except requests.exceptions.RequestException as e:
            msg = f"Request exception on attempt {attempt}: {e}"
            if attempt < max_retries:
                wait = backoff_factor * (2 ** (attempt - 1))
                logging.warning(f"{msg} - Retrying in {wait}s")
                time.sleep(wait)
            else:
                logging.error(msg)
                raise


def fetch_historical_weather(station_id: str, days: int, city_name: str) -> pd.DataFrame:
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=days * 2)

    url = "https://www.ncei.noaa.gov/cdo-web/api/v2/data"
    headers = {"token": NOAA_API_KEY}
    params = {
        "datasetid": "GHCND",
        "stationid": station_id,
        "startdate": start.isoformat(),
        "enddate": end.isoformat(),
        "datatypeid": "TMAX,TMIN",
        "limit": 1000,
        "units": "metric"
    }

    logging.info(f"Fetching weather for {city_name} from {start} to {end}")
    resp = _get_with_backoff(url, params=params, headers=headers)
    data = resp.json().get("results", [])
    df = pd.DataFrame(data)

    if df.empty:
        logging.warning(f"No weather data returned for {city_name}")
        return pd.DataFrame(columns=["date", "tmax_c", "tmin_c", "tmax_f", "tmin_f", "city"])

    df = df.pivot(index="date", columns="datatype", values="value").reset_index()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df = df.dropna(subset=["TMAX", "TMIN"])

    df["tmax_c"] = (df["TMAX"] / 10).round(2)
    df["tmin_c"] = (df["TMIN"] / 10).round(2)
    df["tmax_f"] = ((df["tmax_c"] * 9 / 5) + 32).round(2)
    df["tmin_f"] = ((df["tmin_c"] * 9 / 5) + 32).round(2)
    df["city"] = city_name

    df = df.sort_values("date", ascending=False).drop_duplicates("date").head(days)
    df = df.sort_values("date")

    latest = df["date"].max()
    if latest < end:
        logging.warning(f"{city_name}: Weather data not up-to-date (latest: {latest})")

    logging.info(f"✅ Weather data ready for {city_name}: {len(df)} records")
    return df[["date", "tmax_c", "tmin_c", "tmax_f", "tmin_f", "city"]]


def fetch_historical_energy(region_code: str, days: int, city_name: str) -> pd.DataFrame:
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=days * 2)

    url = "https://api.eia.gov/v2/electricity/rto/daily-region-data/data/"
    params = {
        "api_key": EIA_API_KEY,
        "frequency": "daily",
        "start": start.isoformat(),
        "end": end.isoformat(),
        "data[0]": "value",
        "facets[respondent][]": region_code,
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
        "offset": 0,
        "length": 5000
    }

    logging.info(f"Fetching energy for {city_name} from {start} to {end}")
    resp = _get_with_backoff(url, params)
    data = resp.json().get("response", {}).get("data", [])
    df = pd.DataFrame(data)

    if df.empty:
        logging.warning(f"No energy data for {city_name}")
        return pd.DataFrame(columns=["date", "demand", "city"])

    df = df[df["timezone"] == "Pacific"]
    df = df.rename(columns={"period": "date", "value": "demand"})
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["demand"] = pd.to_numeric(df["demand"], errors="coerce")
    df = df.dropna(subset=["demand"]).drop_duplicates("date")

    df = df.sort_values("date", ascending=False).head(days).sort_values("date")
    df["city"] = city_name

    logging.info(f"✅ Energy data ready for {city_name}: {len(df)} records")
    return df


def main():
    cities = [
        ("new_york", "GHCND:USW00094728", "NYIS"),
        ("chicago", "GHCND:USW00094846", "PJM"),
        ("houston", "GHCND:USW00012960", "ERCO"),
        ("phoenix", "GHCND:USW00023183", "AZPS"),
        ("seattle", "GHCND:USW00024233", "SCL")
    ]

    for city, station_id, region_code in cities:
        print(f"\n📡 Fetching weather data for {city}...")
        weather_df = fetch_historical_weather(station_id, days=90, city_name=city)
        os.makedirs("data/raw/weather", exist_ok=True)
        weather_path = f"data/raw/weather/{city}_weather_90_days.csv"
        weather_df.to_csv(weather_path, index=False)
        logging.info(f"✅ Saved weather data: {weather_path}")

        print(f"⚡ Fetching energy data for {city}...")
        energy_df = fetch_historical_energy(region_code, days=90, city_name=city)
        os.makedirs("data/raw/energy", exist_ok=True)
        energy_path = f"data/raw/energy/{city}_energy_90_days.csv"
        energy_df.to_csv(energy_path, index=False)
        logging.info(f"✅ Saved energy data: {energy_path}")


if __name__ == "__main__":
    main()
