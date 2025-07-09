# Makefile for Energy Analysis Project

ENV = .venv

.PHONY: help install lint format check test fetch process run-dashboard clean

help:
	@echo "Usage:"
	@echo "  make install         Install dependencies into virtual environment"
	@echo "  make lint            Lint code using ruff"
	@echo "  make format          Format code using black and ruff"
	@echo "  make check           Lint + format check (without fixing)"
	@echo "  make test            Run tests with pytest"
	@echo "  make fetch           Fetch latest weather and energy data"
	@echo "  make process         Merge and validate 90-day data"
	@echo "  make run-dashboard   Launch Streamlit dashboard"
	@echo "  make clean           Remove generated artifacts"

install:
	@echo "🔧 Setting up virtual environment and installing dependencies..."
	uv venv $(ENV)
	. $(ENV)/bin/activate && uv pip install -r pyproject.toml

lint:
	@echo "🔍 Running Ruff for linting..."
	. $(ENV)/bin/activate && ruff check src/ tests/

format:
	@echo "🎨 Formatting code with Black and Ruff..."
	. $(ENV)/bin/activate && black src/ tests/
	. $(ENV)/bin/activate && ruff check src/ tests/ --fix

check:
	@echo "🔍 Running Ruff and Black in check mode..."
	. $(ENV)/bin/activate && ruff check src/ tests/
	. $(ENV)/bin/activate && black --check src/ tests/

test:
	@echo "🧪 Running tests with pytest..."
	PYTHONPATH=src . $(ENV)/bin/activate && pytest tests/

fetch:
	@echo "📦 Fetching latest daily weather + energy data..."
	. $(ENV)/bin/activate && python run_fetcher.py

process:
	@echo "🧼 Processing 90-day data and generating quality report..."
	. $(ENV)/bin/activate && python run_processor.py

analyze:
	@echo "📊 Running analysis pipeline..."
	. $(ENV)/bin/activate && python run_analysis.py

pipeline:
	@echo "🔄 Running full end-to-end pipeline..."
	. $(ENV)/bin/activate && python run_pipeline.py

run-dashboard:
	@echo "🚀 Launching Streamlit dashboard..."
	. $(ENV)/bin/activate && streamlit run dashboards/app.py

clean:
	@echo "🧹 Cleaning temporary files and logs..."
	rm -rf __pycache__ .pytest_cache .ruff_cache data/processed/*.csv logs/pipeline.log
