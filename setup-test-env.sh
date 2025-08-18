#!/bin/bash
# Setup test environment

# Create virtual environment
python -m venv venv-test

# Activate virtual environment
source venv-test/bin/activate

# Install test dependencies
pip install -r requirements-test.txt

echo "Test environment ready!"
echo "To activate: source venv-test/bin/activate"
echo "To run tests: python -m pytest"