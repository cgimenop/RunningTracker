import unittest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestAppFunctions(unittest.TestCase):
    
    def setUp(self):
        # Mock the config imports to avoid import errors
        with patch.dict('sys.modules', {
            'config.development': MagicMock(DEBUG=True, MONGO_URI='mongodb://localhost:27017', DATABASE_NAME='test'),
            'config.production': MagicMock(DEBUG=False, MONGO_URI='mongodb://localhost:27017', DATABASE_NAME='test')
        }):
            from app import format_seconds, extract_date_from_filename
            self.format_seconds = format_seconds
            self.extract_date_from_filename = extract_date_from_filename

    def test_format_seconds_valid_input(self):
        result = self.format_seconds(3661)  # 1 hour, 1 minute, 1 second
        self.assertEqual(result, "1:01:01")

    def test_format_seconds_zero(self):
        result = self.format_seconds(0)
        self.assertEqual(result, "0:00:00")

    def test_format_seconds_invalid_input(self):
        result = self.format_seconds("invalid")
        self.assertEqual(result, "00:00:00")

    def test_format_seconds_none_input(self):
        result = self.format_seconds(None)
        self.assertEqual(result, "00:00:00")

    def test_extract_date_from_filename_valid(self):
        result = self.extract_date_from_filename("RunnerUp_2024-01-15-08-30-01_Running.tcx")
        self.assertEqual(result, "2024-01-15")

    def test_extract_date_from_filename_no_date(self):
        result = self.extract_date_from_filename("invalid_filename.tcx")
        self.assertEqual(result, "invalid_filename.tcx")

if __name__ == "__main__":
    unittest.main()