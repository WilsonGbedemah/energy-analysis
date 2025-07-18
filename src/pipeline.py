import subprocess
import logging
import time
import os
from datetime import datetime


def run_step(name: str, command: str):
    """Run a subprocess step with logging and timing."""
    logging.info(f"🚀 Starting: {name}")
    print(f"⏳ Running {name}...")

    start = time.time()
    result = subprocess.run(command, shell=True)

    if result.returncode == 0:
        elapsed = time.time() - start
        logging.info(f"✅ Finished: {name} in {elapsed:.2f}s")
        print(f"✅ {name} completed in {elapsed:.2f} seconds.\n")
    else:
        logging.error(f"❌ Failed: {name}")
        print(f"❌ {name} failed.\n")


def is_dashboard_running() -> bool:
    """Check if a Streamlit dashboard process is already running."""
    try:
        output = subprocess.check_output("tasklist", shell=True).decode()
        return "streamlit.exe" in output.lower()
    except Exception as e:
        logging.warning(f"⚠️ Failed to check running processes: {e}")
        return False


def main():
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        filename="logs/pipeline.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    print("🔄 Running ETL pipeline with dashboard startup...")
    logging.info("🔄 Starting pipeline run")

    steps = [
        ("Data Fetching", "make fetch"),
        ("Data Processing", "make process"),
        ("Data Analysis", "make analyze")
    ]

    for name, cmd in steps:
        run_step(name, cmd)

    # Start dashboard only if not already running
    if is_dashboard_running():
        print("⚠️ Streamlit dashboard already running.")
        logging.info("⚠️ Dashboard already running. Skipping launch.")
    else:
        run_step("Launch Dashboard", "make run-dashboard")

    print("🎯 Pipeline complete.")
    logging.info("🎯 Pipeline execution complete.")


if __name__ == "__main__":
    main()
