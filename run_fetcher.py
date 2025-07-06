# run_fetcher.py

import sys
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from data_fetcher import fetch_last_90_days, fetch_daily_data

# Setup logging to file and console
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/fetcher_run.log"),
        logging.StreamHandler()
    ]
)

def main():
    logging.info("🚀 Running data fetcher pipeline...")

    fetch_mode = os.getenv("FETCH_MODE", "daily").lower()

    try:
        if fetch_mode == "history":
            logging.info("📦 Fetching last 90 days of data")
            fetch_last_90_days()
        else:
            logging.info("📅 Fetching today's data")
            fetch_daily_data()

        logging.info("✅ Data fetching completed successfully")
    except Exception as e:
        logging.error(f"❌ Data fetching failed: {e}")

if __name__ == "__main__":
    main()
