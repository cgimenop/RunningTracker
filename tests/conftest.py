"""
Pytest configuration and fixtures for RunningTracker tests
"""
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project paths to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root / 'webapp'))

@pytest.fixture(scope="session", autouse=True)
def mock_dependencies():
    """Mock external dependencies for all tests"""
    # Create comprehensive mocks
    mock_pymongo = MagicMock()
    mock_pymongo.errors = MagicMock()
    mock_pymongo.errors.ServerSelectionTimeoutError = Exception
    mock_pymongo.MongoClient = MagicMock()
    mock_pymongo.ReplaceOne = MagicMock()
    
    mock_pandas = MagicMock()
    mock_pandas.DataFrame = MagicMock()
    mock_pandas.ExcelWriter = MagicMock()
    
    mock_defusedxml = MagicMock()
    mock_defusedxml.ElementTree = MagicMock()
    mock_defusedxml.ElementTree.parse = MagicMock()
    mock_defusedxml.ElementTree.ParseError = Exception
    
    mock_openpyxl = MagicMock()
    mock_openpyxl.load_workbook = MagicMock()
    
    mock_flask = MagicMock()
    mock_flask.Flask = MagicMock()
    
    # Mock all external dependencies
    with patch.dict('sys.modules', {
        'logging_config': MagicMock(),
        'pymongo': mock_pymongo,
        'pymongo.errors': mock_pymongo.errors,
        'pandas': mock_pandas,
        'flask': mock_flask,
        'openpyxl': mock_openpyxl,
        'defusedxml': mock_defusedxml,
        'defusedxml.ElementTree': mock_defusedxml.ElementTree,
        'const': MagicMock()
    }):
        yield

@pytest.fixture
def mock_trainparser():
    """Fixture to import trainparser with mocked dependencies"""
    import trainparser
    return trainparser

@pytest.fixture
def sample_lap_data():
    """Sample lap data for testing"""
    return [
        {"LapDistance_m": 1000, "LapTotalTime_s": 300, "LapNumber": 1},
        {"LapDistance_m": 1500, "LapTotalTime_s": 450, "LapNumber": 2},
        {"LapDistance_m": 800, "LapTotalTime_s": 240, "LapNumber": 3}
    ]

@pytest.fixture
def sample_trackpoint_data():
    """Sample trackpoint data for testing"""
    return [
        {"Time": "2024-01-01T10:00:00Z", "Latitude": 40.7128, "Longitude": -74.0060, "Altitude_m": 10.0},
        {"Time": "2024-01-01T10:00:10Z", "Latitude": 40.7129, "Longitude": -74.0061, "Altitude_m": 12.0},
        {"Time": "2024-01-01T10:00:20Z", "Latitude": 40.7130, "Longitude": -74.0062, "Altitude_m": 8.0}
    ]