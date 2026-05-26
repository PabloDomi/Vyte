# Makefile for Vyte development

.PHONY: test test-cov test-integration test-all install install-dev clean format lint lint-fix pre-commit security help

# Testing targets
test:
	@echo "Running unit tests..."
	pytest -q

test-cov:
	@echo "Running tests with coverage..."
	pytest --cov=vyte --cov-report=html --cov-report=term-missing

test-integration:
	@echo "Running integration tests..."
	pytest -v -m integration

test-all:
	@echo "Running all tests with coverage..."
	pytest -v --cov=vyte --cov-report=html --cov-report=xml

# Installation targets
install:
	@echo "Installing package..."
	python -m pip install --upgrade pip setuptools wheel
	python -m pip install -e .

install-dev:
	@echo "Installing package with dev dependencies..."
	python -m pip install --upgrade pip setuptools wheel
	python -m pip install -e ".[dev]"
	python -m pip install pre-commit black ruff isort mypy bandit safety

# Cleaning targets
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/ dist/ *.egg-info htmlcov/ .pytest_cache/ .coverage coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + || true
	find . -type f -name "*.pyc" -delete || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + || true

clean-all: clean
	@echo "Deep cleaning..."
	rm -rf venv/ .venv/ .mypy_cache/ .ruff_cache/

# Code quality targets
format:
	@echo "Formatting code..."
	black vyte/ tests/
	isort vyte/ tests/
	ruff check --fix vyte/ tests/ || true

lint:
	@echo "Linting code..."
	black --check vyte/ tests/
	isort --check-only vyte/ tests/
	ruff check vyte/ tests/
	mypy vyte/ --ignore-missing-imports || true

lint-fix:
	@echo "Auto-fixing lint issues..."
	black vyte/ tests/
	isort vyte/ tests/
	ruff check --fix vyte/ tests/

# Security scanning
security:
	@echo "Running security scans..."
	bandit -c pyproject.toml -r vyte/
	safety check --json || true

# Pre-commit hooks
pre-commit-install:
	@echo "Installing pre-commit hooks..."
	pre-commit install

pre-commit:
	@echo "Running pre-commit hooks..."
	pre-commit run --all-files

# Build and publish
build:
	@echo "Building package..."
	python -m pip install --upgrade build
	python -m build

publish-test:
	@echo "Publishing to TestPyPI..."
	python -m pip install --upgrade twine
	python -m twine upload --repository testpypi dist/*

publish:
	@echo "Publishing to PyPI..."
	python -m pip install --upgrade twine
	python -m twine upload dist/*

# Development helpers
check: lint test
	@echo "All checks passed!"

ci: lint security test-all
	@echo "CI checks completed!"

# Documentation
docs:
	@echo "Building documentation..."
	@echo "Documentation generation not yet implemented"

# Help
help:
	@echo "Vyte Makefile Commands:"
	@echo ""
	@echo "Testing:"
	@echo "  make test              - Run unit tests"
	@echo "  make test-cov          - Run tests with coverage report"
	@echo "  make test-integration  - Run only integration tests"
	@echo "  make test-all          - Run all tests with coverage"
	@echo ""
	@echo "Installation:"
	@echo "  make install           - Install package in editable mode"
	@echo "  make install-dev       - Install with dev dependencies"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format            - Format code with black and isort"
	@echo "  make lint              - Check code quality"
	@echo "  make lint-fix          - Auto-fix lint issues"
	@echo "  make security          - Run security scans"
	@echo ""
	@echo "Pre-commit:"
	@echo "  make pre-commit-install - Install pre-commit hooks"
	@echo "  make pre-commit        - Run pre-commit on all files"
	@echo ""
	@echo "Build & Publish:"
	@echo "  make build             - Build distribution packages"
	@echo "  make publish-test      - Publish to TestPyPI"
	@echo "  make publish           - Publish to PyPI"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean             - Remove build artifacts"
	@echo "  make clean-all         - Deep clean including venv"
	@echo "  make check             - Run lint and tests"
	@echo "  make ci                - Run full CI suite"
	@echo "  make help              - Show this help message"
