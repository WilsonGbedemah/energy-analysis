# run_pipeline.py

import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.abspath("src"))

from pipeline import run_pipeline

# Setup logging to both file + console
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler("logs/pipeline_run.log"),
        logging.StreamHandler()
    ],
    format="%(asctime)s - %(levelname)s - %(message)s"
)

if __name__ == "__main__":
    print("🔄 Running full pipeline...")
    try:
        run_pipeline()
        print("✅ Pipeline finished successfully.")
    except Exception as e:
        print("❌ Pipeline failed:", e)
