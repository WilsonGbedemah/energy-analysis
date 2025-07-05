# Makefile to automate project setup and commands

ENV_NAME = .venv

.PHONY: help install test run-dashboard format

help:
	@echo "Available commands:"
	@echo "  make install        Create venv and install dependencies using uv"
	@echo "  make test           Run pytest on tests/"
	@echo "  make run-dashboard  Start Streamlit dashboard"
	@echo "  make format         Format code using black and ruff"

install:
	@echo "🔧 Creating virtual environment and installing dependencies..."
	uv venv $(ENV_NAME)
	. $(ENV_NAME)/bin/activate && uv pip install -r pyproject.toml

test:
	. $(ENV_NAME)/bin/activate && pytest tests/

run-dashboard:
	. $(ENV_NAME)/bin/activate && streamlit run dashboards/app.py

format:
	. $(ENV_NAME)/bin/activate && black src/ tests/ && ruff check src/ tests/ --fix
