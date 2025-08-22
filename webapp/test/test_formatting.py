import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add webapp directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestFormatting(unittest.TestCase):
    def setUp(self):
        # Mock dependencies before importing app
        self.patches = [
            patch.dict('sys.modules', {
                'logging_config': MagicMock(),
                'pymongo': MagicMock()
            }),
            patch.dict('os.environ', {'FLASK_ENV': 'development'})
        ]
        
        for p in self.patches:
            p.start()
        
        import app
        self.app_module = app
    
    def tearDown(self):
        for p in self.patches:
            p.stop()
    
    def test_format_seconds_valid_inputs(self):
        """Test format_seconds with valid inputs"""
        self.assertEqual(self.app_module.format_seconds(0), "0:00:00")
        self.assertEqual(self.app_module.format_seconds(59), "0:00:59")
        self.assertEqual(self.app_module.format_seconds(60), "0:01:00")
        self.assertEqual(self.app_module.format_seconds(3600), "1:00:00")
        self.assertEqual(self.app_module.format_seconds(3661), "1:01:01")
        self.assertEqual(self.app_module.format_seconds(7200), "2:00:00")
    
    def test_format_seconds_string_inputs(self):
        """Test format_seconds with string inputs"""
        self.assertEqual(self.app_module.format_seconds("60"), "0:01:00")
        self.assertEqual(self.app_module.format_seconds("3600.5"), "1:00:00")
    
    def test_format_seconds_invalid_inputs(self):
        """Test format_seconds with invalid inputs"""
        self.assertEqual(self.app_module.format_seconds(None), "00:00:00")
        self.assertEqual(self.app_module.format_seconds("invalid"), "00:00:00")
        self.assertEqual(self.app_module.format_seconds(""), "00:00:00")
        self.assertEqual(self.app_module.format_seconds([]), "00:00:00")
    
    def test_format_distance_meters(self):
        """Test format_distance for meter values"""
        self.assertEqual(self.app_module.format_distance(0), "0.00 m")
        self.assertEqual(self.app_module.format_distance(500), "500.00 m")
        self.assertEqual(self.app_module.format_distance(999), "999.00 m")
        self.assertEqual(self.app_module.format_distance(999.99), "999.99 m")
    
    def test_format_distance_kilometers(self):
        """Test format_distance for kilometer values"""
        self.assertEqual(self.app_module.format_distance(1000), "1.00 km")
        self.assertEqual(self.app_module.format_distance(1500), "1.50 km")
        self.assertEqual(self.app_module.format_distance(2500.75), "2.50 km")
        self.assertEqual(self.app_module.format_distance(10000), "10.00 km")
    
    def test_format_distance_string_inputs(self):
        """Test format_distance with string inputs"""
        self.assertEqual(self.app_module.format_distance("1000"), "1.00 km")
        self.assertEqual(self.app_module.format_distance("500.5"), "500.50 m")
    
    def test_format_distance_invalid_inputs(self):
        """Test format_distance with invalid inputs"""
        self.assertEqual(self.app_module.format_distance(None), "0.00 m")
        self.assertEqual(self.app_module.format_distance("invalid"), "0.00 m")
        self.assertEqual(self.app_module.format_distance(""), "0.00 m")
        self.assertEqual(self.app_module.format_distance([]), "0.00 m")
    
    def test_format_altitude_valid_inputs(self):
        """Test format_altitude with valid inputs"""
        self.assertEqual(self.app_module.format_altitude(0), "0.00 m")
        self.assertEqual(self.app_module.format_altitude(100), "100.00 m")
        self.assertEqual(self.app_module.format_altitude(123.456), "123.46 m")
        self.assertEqual(self.app_module.format_altitude(-50.5), "-50.50 m")
    
    def test_format_altitude_string_inputs(self):
        """Test format_altitude with string inputs"""
        self.assertEqual(self.app_module.format_altitude("100.5"), "100.50 m")
        self.assertEqual(self.app_module.format_altitude("-25"), "-25.00 m")
    
    def test_format_altitude_invalid_inputs(self):
        """Test format_altitude with invalid inputs"""
        self.assertEqual(self.app_module.format_altitude(None), "0.00 m")
        self.assertEqual(self.app_module.format_altitude("invalid"), "0.00 m")
        self.assertEqual(self.app_module.format_altitude(""), "0.00 m")
        self.assertEqual(self.app_module.format_altitude([]), "0.00 m")

if __name__ == '__main__':
    unittest.main()