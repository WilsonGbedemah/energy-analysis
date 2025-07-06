import os
import pandas as pd
import numpy as np
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    filename='logs/pipeline.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Ensure output directory exists
os.makedirs("data/processed", exist_ok=True)


def compute_correlation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute correlation between temperature and energy consumption.
    Returns a DataFrame with Pearson correlation values.
    """
    corr = df[["tmax_f", "tmin_f", "energy_mwh"]].corr(method="pearson")
    logging.info("✅ Computed correlation matrix")
    return corr


def weekday_weekend_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compare energy usage on weekdays vs weekends.
    Returns a DataFrame with average usage by category.
    """
    df["date"] = pd.to_datetime(df["date"])
    df["day_type"] = df["date"].dt.weekday.apply(lambda x: "Weekend" if x >= 5 else "Weekday")
    grouped = df.groupby("day_type")["energy_mwh"].agg(["mean", "std", "count"]).reset_index()
    logging.info("✅ Completed weekday vs weekend analysis")
    return grouped


def seasonal_pattern_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze seasonal energy patterns by month.
    Returns average energy usage per city per month.
    """
    df["month"] = pd.to_datetime(df["date"]).dt.month
    monthly = df.groupby(["city", "month"])["energy_mwh"].mean().reset_index()
    monthly.rename(columns={"energy_mwh": "avg_energy_mwh"}, inplace=True)
    logging.info("✅ Completed seasonal pattern analysis")
    return monthly


def generate_analysis_report(df: pd.DataFrame, save=True) -> dict:
    """
    Run all analyses and optionally save the outputs to disk.
    Returns all analysis results as a dictionary.
    """
    results = {}

    results["correlation_matrix"] = compute_correlation(df)
    results["weekday_weekend"] = weekday_weekend_analysis(df)
    results["seasonal_patterns"] = seasonal_pattern_analysis(df)

    if save:
        results["correlation_matrix"].to_csv("data/processed/correlation_matrix.csv")
        results["weekday_weekend"].to_csv("data/processed/weekday_weekend_summary.csv", index=False)
        results["seasonal_patterns"].to_csv("data/processed/seasonal_pattern_summary.csv", index=False)
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
