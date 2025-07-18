# Makefile for Energy Analysis Project (using uv, no pre-commit)

.PHONY: install check test fetch process analyze pipeline run-dashboard clean help
.DEFAULT_GOAL := help

VENV = .venv
PYTHON = $(VENV)/Scripts/python.exe

install: ## Create venv and install dependencies using uv
	@echo "🚀 Creating virtual environment and syncing dependencies with uv..."
	@if exist "$(VENV)" rmdir /s /q $(VENV)
	@uv venv $(VENV)
	@uv sync --dev

check: ## Run code quality checks
	@echo "🔐 Checking lock file consistency..."
	@uv lock --locked
	@echo "🔍 Linting with Ruff..."
	@$(PYTHON) -m ruff check src/ tests/
	@echo "🧪 Checking dependencies with deptry..."
	@$(PYTHON) -m deptry .

test: ## Run unit tests
	@echo "🧪 Running tests with pytest..."
	@$(PYTHON) -m pytest tests/

fetch: ## Fetch raw weather and energy data
	@echo "📦 Fetching raw weather + energy data..."
	@$(PYTHON) src/data_fetcher.py

process: ## Clean and validate raw data
	@echo "🧼 Running data processor..."
	@$(PYTHON) src/data_processor.py

analyze: ## Run data analysis
	@echo "📊 Running analysis..."
	@$(PYTHON) src/analysis.py

pipeline: ## Run full ETL
	@echo "🔄 Running complete pipeline..."
	@$(PYTHON) src/pipeline.py

run-dashboard: ## Start Streamlit dashboard
	@echo "🚀 Launching Streamlit dashboard..."
	@cmd /C "set STREAMLIT_BROWSER_GATHER_USAGE_STATS=false && set STREAMLIT_SERVER_HEADLESS=true && .venv\\Scripts\\python.exe -m streamlit run dashboards\\app.py"

clean: ## Remove temp files and logs
	@echo "🧹 Cleaning up artifacts..."
	@del /q /s __pycache__ >nul 2>&1
	@del /q /s .pytest_cache .ruff_cache logs\*.log data\processed\*.csv >nul 2>&1

help: ## Show available Make targets
	@$(PYTHON) -c "import re; \
	[[print(f'\033[36m{m[0]:<20}\033[0m {m[1]}') for m in re.findall(r'^([a-zA-Z_-]+):.*?## (.*)$$', open('Makefile').read(), re.M)] for makefile in ('$(MAKEFILE_LIST)').strip().split()]"
