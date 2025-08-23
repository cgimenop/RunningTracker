.PHONY: test test-cov clean install-deps setup-test

# Default target
test:
	python -m pytest

# Run tests with coverage
test-cov:
	./run-coverage.sh

# Clean up generated files
clean:
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +

# Install test dependencies
install-deps:
	pip install -r requirements-test.txt

# Setup test environment
setup-test:
	python3 -m venv venv-test
	source venv-test/bin/activate && pip install -r requirements-test.txt

# Quick test without coverage
test-quick:
	python -m pytest --tb=short -q