import os
import pandas as pd
from datetime import datetime
from data_fetcher import fetch_last_90_days

# Ensure output directory exists
os.makedirs("data/processed", exist_ok=True)


def generate_data_quality_report(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform data quality checks and return a summary DataFrame.
    Saves report to CSV as well.
    """
    report = {}

    # 🔍 Missing values
    missing = df.isnull().sum()
    report["missing_values"] = missing[missing > 0].to_dict()

    # 🌡️ Temperature outliers
    temp_outliers = df[
        (df["tmax_f"] > 130) | (df["tmax_f"] < -50) |
        (df["tmin_f"] > 130) | (df["tmin_f"] < -50)
    ]
    report["temperature_outliers"] = {"count": len(temp_outliers)}

    # ⚡ Negative energy consumption
    energy_outliers = df[df["energy_mwh"] < 0]
    report["negative_energy"] = {"count": len(energy_outliers)}

    # ⏱️ Data freshness
    max_date = pd.to_datetime(df["date"]).max().date()
    today = datetime.today().date()
    freshness_days = (today - max_date).days
    report["data_freshness"] = {
        "days_since_last_data": freshness_days,
        "is_fresh": freshness_days <= 2
    }

    # ✅ Convert to DataFrame
    quality_df = pd.DataFrame.from_dict(report, orient="index")

    # ✅ Save
    quality_df.to_csv("data/processed/data_quality_report.csv")

    return quality_df


def process_and_merge_data(save_output=True) -> pd.DataFrame:
    """
    Fetches last 90 days of data, cleans, merges, validates, and saves output.
    Returns cleaned DataFrame.
    """
    # ✅ Step 1: Fetch last 90 days (already built in data_fetcher)
    weather_df, energy_df = fetch_last_90_days(save=True)

    # ✅ Step 2: Standardize dates
    if "date" in weather_df.columns:
        weather_df["date"] = pd.to_datetime(weather_df["date"]).dt.date
    else:
        raise ValueError("❌ 'date' column missing in weather_df.")

    if "date" in energy_df.columns:
        energy_df["date"] = pd.to_datetime(energy_df["date"]).dt.date
    else:
        raise ValueError("❌ 'date' column missing in energy_df — check your EIA API response.")

    # ✅ Step 3: Merge on city + date
    merged_df = pd.merge(weather_df, energy_df, on=["city", "date"], how="inner")

    # ✅ Step 4: Drop incomplete rows
    merged_df = merged_df.dropna(subset=["tmax_f", "tmin_f", "energy_mwh"])

    # ✅ Step 5: Generate and save data quality report
    generate_data_quality_report(merged_df)

    # ✅ Step 6: Save cleaned merged data
    if save_output:
        merged_df.to_csv("data/processed/merged_data.csv", index=False)
        print("✅ Merged data saved to data/processed/merged_data.csv")

    return merged_df
