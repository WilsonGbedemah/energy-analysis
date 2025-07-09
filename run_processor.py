import os
import sys
import logging

# 🔧 Add src/ directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from data_processor import process_and_merge_data

# 📁 Ensure logs and processed directories exist
os.makedirs("logs", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)

# 🛠️ Setup logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/processor_run.log"),
        logging.StreamHandler()  # Also print to terminal
    ]
)

def main():
    print("🧼 Starting data cleaning and merging process...")
    logging.info("⚙️ Data processor started.")

    try:
        df = process_and_merge_data()
        print("✅ Processing complete.")
        print(f"📄 Saved {len(df)} cleaned records to data/processed/merged_data.csv")
        print("📊 Quality report saved to data/processed/data_quality_report.csv")
        logging.info("✅ Processing completed successfully. Rows: %d", len(df))
    except Exception as e:
        print("❌ An error occurred during processing.")
        logging.error("❌ Data processing failed: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
