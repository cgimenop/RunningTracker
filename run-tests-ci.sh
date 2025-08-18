#!/bin/bash
# CI Test Runner Script

set -e

echo "🧪 Running RunningTracker Test Suite"

# Setup test environment
if [ ! -d "venv-test" ]; then
    echo "📦 Setting up test environment..."
    python3 -m venv venv-test
fi

source venv-test/bin/activate
pip install -r requirements-test.txt

echo "🔬 Running trainparser tests..."
python -m pytest src/test/test_trainparser.py -v

echo "🌐 Running webapp tests..."
cd webapp && python -m pytest test/test_app.py -v
cd ..

echo "📊 Generating coverage report..."
python -m pytest --cov=src --cov=webapp --cov-report=term --cov-report=html --cov-branch src/test/test_trainparser.py

echo "✅ All tests completed successfully!"
echo "📈 Coverage report: htmlcov/index.html"