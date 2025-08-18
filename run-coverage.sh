#!/bin/bash
# Test Coverage Analysis Script

echo "Setting up test environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv-test" ]; then
    python3 -m venv venv-test
fi

# Activate virtual environment
source venv-test/bin/activate

# Install dependencies
pip install -r requirements-test.txt

echo "Running test coverage analysis..."

# Run tests with coverage
python -m pytest --cov=src --cov=webapp --cov-report=term-missing --cov-report=html --cov-branch src/test/tests.py webapp/test/test_app.py

echo "Coverage report generated in htmlcov/ directory"
echo "Open htmlcov/index.html in browser to view detailed report"