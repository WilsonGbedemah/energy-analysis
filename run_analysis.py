# run_analysis.py

import os
import sys
import logging
import pandas as pd

# Add src to the path
sys.path.insert(0, os.path.abspath("src"))
from analysis import generate_analysis_report

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler("logs/analysis_run.log"),
        logging.StreamHandler()
    ],
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def main():
    print("📊 Starting analysis...")
    try:
        df = pd.read_csv("data/processed/merged_data.csv")
        generate_analysis_report(df)
        print("✅ Analysis complete. Results saved to data/processed/")
    except FileNotFoundError:
        logging.error("❌ merged_data.csv not found. Please run the processor first.")
        print("❌ Error: merged_data.csv not found. Run the processor first.")

if __name__ == "__main__":
    main()
