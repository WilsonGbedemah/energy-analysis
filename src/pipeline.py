# src/pipeline.py

import os
import logging
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/pipeline.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Import pipeline components
from data_fetcher import fetch_last_90_days
from data_processor import process_and_merge_data
from analysis import generate_analysis_report


def run_pipeline():
    """
    Run the full end-to-end pipeline:
    1. Fetch data
    2. Process and merge
    3. Analyze
    """
    logging.info("🚀 Starting full data pipeline...")

    try:
        # 1. Fetch and save raw data
        fetch_last_90_days(save=True)

        # 2. Process and validate merged data
        merged_df = process_and_merge_data(save_output=True)

        # 3. Generate analysis outputs
        generate_analysis_report(merged_df, save=True)

        logging.info("✅ Full pipeline completed successfully")

    except Exception as e:
        logging.error(f"❌ Pipeline failed: {e}")
        raise
