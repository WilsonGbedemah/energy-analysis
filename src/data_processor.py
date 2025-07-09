import os
import logging
import pandas as pd
from datetime import datetime

# ✅ Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/processor_run.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ✅ Ensure output directory exists
os.makedirs("data/processed", exist_ok=True)


def generate_data_quality_report(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate a report summarizing key data quality metrics:
    1. Missing values
    2. Temperature outliers
    3. Negative/missing energy
    4. Freshness
    """
    report = {}

    # 1️⃣ Missing values
    missing = df.isnull().sum()
    missing_dict = missing[missing > 0].to_dict()
    report["missing_values"] = missing_dict
    if missing_dict:
        logging.warning(f"⚠️ Missing values found: {missing_dict}")

    # 2️⃣ Temperature outliers
    temp_outliers = df[
        (df["tmax_f"] > 130) | (df["tmax_f"] < -50) |
        (df["tmin_f"] > 130) | (df["tmin_f"] < -50)
    ]
    report["temperature_outliers"] = {"count": len(temp_outliers)}
    if len(temp_outliers) > 0:
        logging.warning(f"🌡️ Temperature outliers found: {len(temp_outliers)} rows")

    # 3️⃣ Negative or missing energy
    energy_issues = df[(df["energy_mwh"].isnull()) | (df["energy_mwh"] < 0)]
    report["energy_issues"] = {"count": len(energy_issues)}
    if len(energy_issues) > 0:
        logging.warning(f"⚡ Energy issues found: {len(energy_issues)} rows")

    # 4️⃣ Freshness
    max_date = pd.to_datetime(df["date"]).max().date()
    today = datetime.today().date()
    freshness_days = (today - max_date).days
    report["data_freshness"] = {
        "last_record_date": str(max_date),
        "days_since_last_data": freshness_days,
        "is_fresh": freshness_days <= 2
    }

    logging.info(f"⏱️ Data freshness: {freshness_days} days since last record")

    # ✅ Save report
    quality_df = pd.DataFrame.from_dict(report, orient="index")
    quality_df.to_csv("data/processed/data_quality_report.csv")
    logging.info("📋 Data quality report saved to data/processed/data_quality_report.csv")

    return quality_df


def process_and_merge_data(save_output=True) -> pd.DataFrame:
    """
    Loads raw weather and energy data, merges, validates, logs, and saves cleaned output.
    """
    weather_path = "data/raw/weather_last_90_days.csv"
    energy_path = "data/raw/energy_last_90_days.csv"

    logging.info("🔄 Starting data processing...")

    if not os.path.exists(weather_path) or not os.path.exists(energy_path):
        logging.error("❌ Required raw data files not found. Please run the fetcher.")
        raise FileNotFoundError("Raw data missing")

    # ✅ Load data
    weather_df = pd.read_csv(weather_path)
    energy_df = pd.read_csv(energy_path)
    logging.info("✅ Raw data loaded")

    # ✅ Date standardization
    try:
        weather_df["date"] = pd.to_datetime(weather_df["date"]).dt.date
        energy_df["date"] = pd.to_datetime(energy_df["date"]).dt.date
    except Exception as e:
        logging.error(f"❌ Date conversion error: {e}")
        raise

    # ✅ Merge on city + date
    merged_df = pd.merge(weather_df, energy_df, on=["city", "date"], how="inner")
    logging.info(f"🔗 Merged dataset shape: {merged_df.shape}")

    # ✅ Remove incomplete rows
    merged_df = merged_df.dropna(subset=["tmax_f", "tmin_f", "energy_mwh"])
    logging.info(f"🧹 After dropping nulls: {merged_df.shape[0]} rows")

    # ✅ Generate quality report
    generate_data_quality_report(merged_df)

    # ✅ Save merged output
    if save_output:
        output_path = "data/processed/merged_data.csv"
        merged_df.to_csv(output_path, index=False)
        logging.info(f"✅ Cleaned data saved to {output_path}")

    return merged_df
