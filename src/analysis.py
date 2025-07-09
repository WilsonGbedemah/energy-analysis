import os
import pandas as pd
import numpy as np
import logging
from datetime import datetime

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename='logs/pipeline.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Ensure output directory exists
os.makedirs("data/processed", exist_ok=True)


def compute_correlation(df: pd.DataFrame) -> pd.DataFrame:
    corr = df[["tmax_f", "tmin_f", "energy_mwh"]].corr(method="pearson")
    logging.info("✅ Computed correlation matrix")
    return corr


def weekday_weekend_analysis(df: pd.DataFrame) -> pd.DataFrame:
    df["date"] = pd.to_datetime(df["date"])
    df["day_type"] = df["date"].dt.weekday.apply(lambda x: "Weekend" if x >= 5 else "Weekday")
    result = df.groupby("day_type")["energy_mwh"].agg(["mean", "std", "count"]).reset_index()
    logging.info("✅ Completed weekday vs weekend analysis")
    return result


def seasonal_pattern_analysis(df: pd.DataFrame) -> pd.DataFrame:
    df["month"] = pd.to_datetime(df["date"]).dt.month
    monthly = df.groupby(["city", "month"])["energy_mwh"].mean().reset_index()
    monthly.rename(columns={"energy_mwh": "avg_energy_mwh"}, inplace=True)
    logging.info("✅ Completed seasonal pattern analysis")
    return monthly


def generate_geographic_overview(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each city, get current temperature and energy usage and % change from yesterday
    """
    df["date"] = pd.to_datetime(df["date"])
    latest = df[df["date"] == df["date"].max()]
    prev_day = df[df["date"] == df["date"].max() - pd.Timedelta(days=1)]

    merged = pd.merge(
        latest,
        prev_day[["city", "energy_mwh"]],
        on="city",
        suffixes=("", "_yesterday")
    )
    merged["energy_pct_change"] = (
        (merged["energy_mwh"] - merged["energy_mwh_yesterday"]) / merged["energy_mwh_yesterday"]
    ) * 100

    result = merged[["city", "date", "tmax_f", "tmin_f", "energy_mwh", "energy_pct_change"]]
    logging.info("✅ Geographic overview computed")
    return result


def generate_heatmap_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create pivot table of energy usage by temp range and weekday.
    """
    df["date"] = pd.to_datetime(df["date"])
    df["weekday"] = df["date"].dt.day_name()

    # Create temperature bands
    def temp_range(val):
        if val < 50:
            return "<50°F"
        elif val < 60:
            return "50-60°F"
        elif val < 70:
            return "60-70°F"
        elif val < 80:
            return "70-80°F"
        elif val < 90:
            return "80-90°F"
        else:
            return ">90°F"

    df["temp_range"] = df["tmax_f"].apply(temp_range)

    pivot = df.pivot_table(
        values="energy_mwh",
        index="temp_range",
        columns="weekday",
        aggfunc="mean"
    ).fillna(0)

    pivot = pivot.sort_index()
    logging.info("✅ Heatmap matrix created")
    return pivot


def generate_analysis_report(df: pd.DataFrame, save=True) -> dict:
    """
    Run all analyses and optionally save outputs to disk
    """
    results = {}

    results["correlation_matrix"] = compute_correlation(df)
    results["weekday_weekend"] = weekday_weekend_analysis(df)
    results["seasonal_patterns"] = seasonal_pattern_analysis(df)
    results["geographic_overview"] = generate_geographic_overview(df)
    results["heatmap_matrix"] = generate_heatmap_matrix(df)

    if save:
        results["correlation_matrix"].to_csv("data/processed/correlation_matrix.csv")
        results["weekday_weekend"].to_csv("data/processed/weekday_weekend_summary.csv", index=False)
        results["seasonal_patterns"].to_csv("data/processed/seasonal_pattern_summary.csv", index=False)
        results["geographic_overview"].to_csv("data/processed/geographic_overview.csv", index=False)
        results["heatmap_matrix"].to_csv("data/processed/heatmap_matrix.csv")
        logging.info("📁 Analysis outputs saved to data/processed/")

    return results


if __name__ == "__main__":
    try:
        df = pd.read_csv("data/processed/merged_data.csv")
        generate_analysis_report(df)
        print("✅ Analysis complete. Results saved in data/processed/")
    except FileNotFoundError:
        logging.error("❌ merged_data.csv not found. Please run data processor first.")
        print("❌ merged_data.csv not found. Run the processor first.")
