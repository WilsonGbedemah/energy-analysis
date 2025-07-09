import sys
import os
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Add src/ directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from data_fetcher import fetch_last_90_days  # Optional: fetch_daily_data

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure logging to both console and file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/fetcher_run.log"),
        logging.StreamHandler()
    ]
)

def main():
    logging.info("🚀 Starting data fetcher...")

    # ✅ Check API keys
    if not os.getenv("NOAA_API_KEY") or not os.getenv("EIA_API_KEY"):
        logging.error("❌ API keys missing in .env file. Set NOAA_API_KEY and EIA_API_KEY.")
        sys.exit(1)

    # ✅ Parse command-line argument
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["history", "daily"], help="Fetch mode override")
    args = parser.parse_args()

    # ✅ Determine fetch mode (CLI > .env > default)
    fetch_mode = args.mode or os.getenv("FETCH_MODE", "history").lower()
    logging.info(f"📁 Running in '{fetch_mode}' mode")

    try:
        if fetch_mode == "history":
            logging.info("📦 Fetching last 90 days of data...")
            fetch_last_90_days()
        elif fetch_mode == "daily":
            logging.info("📅 Daily mode is selected, but not implemented yet.")
            # fetch_daily_data()  # Uncomment when implemented
        else:
            logging.warning(f"⚠️ Unknown FETCH_MODE: {fetch_mode}. Defaulting to 'history'.")
            fetch_last_90_days()

        logging.info("✅ Data fetching completed successfully.")

    except Exception as e:
        logging.error(f"❌ Data fetching failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
