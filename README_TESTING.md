# Testing Guide

## Unified Test Structure

The project now uses a unified test structure with pytest:

```
tests/
├── conftest.py          # Pytest configuration and fixtures
├── test_trainparser.py  # Tests for trainparser module
└── test_webapp.py       # Tests for webapp module
```

## Running Tests

### Quick Test Run
```bash
make test
# or
python -m pytest
```

### Test with Coverage
```bash
make test-cov
# or
./run-coverage.sh
```

### Quick Test (minimal output)
```bash
make test-quick
```

## Test Categories

### TrainParser Tests
- **Core functionality**: pace calculation, sanitization, path validation
- **MongoDB operations**: bulk operations, data sanitization
- **Error handling**: fallback scenarios, invalid inputs
- **Altitude calculations**: elevation gain/loss calculations

### WebApp Tests
- **Formatting**: distance, altitude, time formatting
- **Security**: regex pattern validation, input sanitization
- **Data processing**: date extraction, lap validation
- **Database operations**: connection management, data loading

## Coverage

Current coverage: **20%** (617 statements, 491 missing)

Coverage reports are generated in `htmlcov/` directory.
Open `htmlcov/index.html` to view detailed coverage report.

## Configuration

- **pytest.ini**: Main pytest configuration
- **.coveragerc**: Coverage configuration
- **conftest.py**: Test fixtures and mocking setup

## Dependencies

Test dependencies are managed in `requirements-test.txt`:
- pytest>=7.0.0
- pytest-mock>=3.10.0  
- pytest-cov>=4.0.0
- coverage>=7.0.0

## Makefile Targets

- `make test`: Run all tests
- `make test-cov`: Run tests with coverage
- `make test-quick`: Quick test run
- `make clean`: Clean generated files
- `make install-deps`: Install test dependencies
- `make setup-test`: Setup test environment