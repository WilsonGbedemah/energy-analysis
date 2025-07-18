import os
import logging
import pandas as pd
from datetime import datetime, timedelta

# ─── Setup logging ───────────────────────────────────────────── #
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/processor_run.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ─── Ensure output directory exists ──────────────────────────── #
os.makedirs("data/processed", exist_ok=True)

# ─── Quality Check Documentation ─────────────────────────────── #
QUALITY_DOC = {
    "missing_values": "Counts columns with missing values. Missing data can affect model training and reliability.",
    "temperature_outliers": "Flags TMAX or TMIN values above 130°F or below -50°F — likely sensor errors or corrupt readings.",
    "energy_issues": "Detects missing or negative electricity demand values, which are invalid for usage analytics.",
    "data_freshness": "Checks if the most recent entry is within 2 days. Older data may signal fetch failure or API lag."
}

def generate_data_quality_report(df: pd.DataFrame, city: str) -> pd.DataFrame:
    """
    Evaluates data quality of merged weather and energy dataframe.
    Returns a report as DataFrame and saves it as CSV in data/processed.
    """
    report = []

    # 1️⃣ Missing values
    missing = df.isnull().sum()
    for col, count in missing[missing > 0].items():
        report.append({
            "check": "missing_values",
            "column": col,
            "count": count,
            "note": QUALITY_DOC["missing_values"]
        })
        logging.warning(f"⚠️ Missing {count} values in '{col}' for {city}")

    # 2️⃣ Temperature outliers
    temp_outliers = df[
        (df["tmax_f"] > 130) | (df["tmax_f"] < -50) |
        (df["tmin_f"] > 130) | (df["tmin_f"] < -50)
    ]
    if not temp_outliers.empty:
        report.append({
            "check": "temperature_outliers",
            "column": "tmax_f / tmin_f",
            "count": len(temp_outliers),
            "note": QUALITY_DOC["temperature_outliers"]
        })
        logging.warning(f"🌡️ {len(temp_outliers)} temperature outliers in {city}")

    # 3️⃣ Negative or missing energy
    if "energy_mwh" not in df.columns and "demand" in df.columns:
        df.rename(columns={"demand": "energy_mwh"}, inplace=True)

    demand_issues = df[(df["energy_mwh"].isnull()) | (df["energy_mwh"] < 0)]
    if not demand_issues.empty:
        report.append({
            "check": "energy_issues",
            "column": "energy_mwh",
            "count": len(demand_issues),
            "note": QUALITY_DOC["energy_issues"]
        })
        logging.warning(f"⚡ {len(demand_issues)} energy issues in {city}")

    # 4️⃣ Freshness check
    latest_date = pd.to_datetime(df["date"]).max().date()
    days_old = (datetime.today().date() - latest_date).days
    report.append({
        "check": "data_freshness",
        "column": "date",
        "count": days_old,
        "note": QUALITY_DOC["data_freshness"],
        "is_fresh": days_old <= 2
    })
    if days_old > 2:
        logging.warning(f"📆 {city} data is {days_old} days old (latest: {latest_date})")

    # Save report
    report_df = pd.DataFrame(report)
    out_path = f"data/processed/{city.replace(' ', '_')}_quality_report.csv"
    report_df.to_csv(out_path, index=False)
    logging.info(f"📋 Quality report saved: {out_path}")
    return report_df

def process_city_data(weather_path: str, energy_path: str, city: str) -> pd.DataFrame:
    """
    Merges weather and energy data for a single city, checks data quality, and saves output.
    """
    try:
        weather_df = pd.read_csv(weather_path)
        energy_df = pd.read_csv(energy_path)
    except Exception as e:
        logging.error(f"❌ Failed to read data for {city}: {e}")
        return pd.DataFrame()

    try:
        weather_df["date"] = pd.to_datetime(weather_df["date"]).dt.date
        energy_df["date"] = pd.to_datetime(energy_df["date"]).dt.date
    except Exception as e:
        logging.error(f"❌ Date parsing failed for {city}: {e}")
        return pd.DataFrame()

    # Standardize last 90 days
    start_date = datetime.today().date() - timedelta(days=89)
    weather_df = weather_df[weather_df["date"] >= start_date].drop_duplicates("date")
    energy_df = energy_df[energy_df["date"] >= start_date].drop_duplicates("date")

    # Rename demand column if necessary
    if "demand" in energy_df.columns:
        energy_df.rename(columns={"demand": "energy_mwh"}, inplace=True)

    # Merge full data (even with problems)
    merged = pd.merge(weather_df, energy_df, on="date", how="inner")
    merged["city"] = city

    # ✅ Run quality report before dropping invalids
    generate_data_quality_report(merged.copy(), city)

    # 🔍 Drop unusable rows for saving cleaned version
    cleaned = merged.dropna(subset=["tmax_f", "tmin_f", "energy_mwh"])
    cleaned = cleaned[cleaned["energy_mwh"] >= 0]
    cleaned = cleaned.drop_duplicates("date")

    # Save cleaned data
    out_path = f"data/processed/{city.replace(' ', '_')}_cleaned.csv"
    cleaned.to_csv(out_path, index=False)
    logging.info(f"✅ Cleaned data saved: {out_path}")

    return cleaned

def process_all_cities():
    """
    Iterates over raw files, processes each city's data, and logs outcomes.
    """
    logging.info("🚀 Starting full processing job")

    raw_weather = "data/raw/weather"
    raw_energy = "data/raw/energy"
    cities = [f for f in os.listdir(raw_weather) if f.endswith(".csv")]

    count = 0
    for weather_file in cities:
        city = weather_file.replace("_weather_90_days.csv", "")
        energy_file = f"{city}_energy_90_days.csv"

        wp = os.path.join(raw_weather, weather_file)
        ep = os.path.join(raw_energy, energy_file)

        if not os.path.exists(ep):
            logging.warning(f"⚠️ Missing energy file for {city}, skipping.")
            continue

        process_city_data(wp, ep, city)
        count += 1

    logging.info(f"🎯 Done! {count} cities processed.")

# ─── Entrypoint for `make process` ───────────────────────────── #
if __name__ == "__main__":
    process_all_cities()
