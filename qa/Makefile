.PHONY: install test smoke regression ui api headed lint format trace clean help

install:                          ## Install dependencies
	poetry install
	poetry run playwright install chromium

test:                             ## Run all tests
	python3 -m pytest tests/ -o addopts="" -v

smoke:                            ## Run smoke tests
	python3 -m pytest tests/ -m smoke -o addopts="" -v

regression:                       ## Run regression tests
	python3 -m pytest tests/ -m regression -o addopts="" -v

ui:                               ## Run UI tests
	python3 -m pytest tests/ -m ui -o addopts="" -v

api:                              ## Run API tests
	python3 -m pytest tests/ -m api -o addopts="" -v

headed:                           ## Run UI tests with headed browser
	python3 -m pytest tests/ -o addopts="" -v --headed

lint:                             ## Run Ruff lint checks
	python3 -m ruff check .

format:                           ## Format code using Ruff
	python3 -m ruff format .

trace:                            ## Run UI tests with tracing enabled
	python3 -m pytest tests/ -o addopts="" -v --tracing on

clean:                            ## Remove caches and generated artifacts
	rm -rf artifacts/ .pytest_cache/ __pycache__/ .ruff_cache/ app/**/__pycache__ tests/**/__pycache__ config/__pycache__ fixtures/__pycache__ flows/__pycache__ data/__pycache__ models/__pycache__ utils/__pycache__

help:                             ## Show help for tasks
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\\033[36m%-20s\\033[0m %s\\n", $$1, $$2}'
