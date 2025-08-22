import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import re

# Add webapp directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestTemplateFilters(unittest.TestCase):
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
        self.app = app.app
    
    def tearDown(self):
        for p in self.patches:
            p.stop()
    
    def test_regex_search_filter_valid_patterns(self):
        """Test regex_search filter with valid patterns"""
        with self.app.app_context():
            # Test date pattern matching - updated to use safe pattern names
            result = self.app_module.regex_search("test-2024-01-01", "date")
            self.assertIsNotNone(result)
            self.assertEqual(result.group(1), "2024-01-01")
            
            # Test filename pattern matching
            result = self.app_module.regex_search("RunnerUp_2025-08-05-08-24-01_Running.tcx", "date")
            self.assertIsNotNone(result)
            self.assertEqual(result.group(1), "2025-08-05")
            
            # Test no match
            result = self.app_module.regex_search("no-date-here", "date")
            self.assertIsNone(result)
            
            # Test time pattern
            result = self.app_module.regex_search("time-12:34:56", "time")
            self.assertIsNotNone(result)
            self.assertEqual(result.group(1), "12:34:56")
            
            # Test number pattern
            result = self.app_module.regex_search("value-123.45", "number")
            self.assertIsNotNone(result)
            self.assertEqual(result.group(1), "123.45")
    
    def test_regex_search_filter_edge_cases(self):
        """Test regex_search filter with edge cases"""
        with self.app.app_context():
            # Empty string
            result = self.app_module.regex_search("", "date")
            self.assertIsNone(result)
            
            # Multiple matches (should return first)
            result = self.app_module.regex_search("2024-01-01 and 2024-12-31", "date")
            self.assertIsNotNone(result)
            self.assertEqual(result.group(1), "2024-01-01")
            
            # Test unsafe pattern rejection
            result = self.app_module.regex_search("test", "unsafe_pattern")
            self.assertIsNone(result)
            
            # Test non-string input
            result = self.app_module.regex_search(123, "date")
            self.assertIsNone(result)
    
    def test_format_distance_filter(self):
        """Test format_distance template filter"""
        with self.app.app_context():
            # Test meter values
            result = self.app_module.format_distance_filter(500)
            self.assertEqual(result, "500.00 m")
            
            # Test kilometer values
            result = self.app_module.format_distance_filter(1500)
            self.assertEqual(result, "1.50 km")
            
            # Test invalid values
            result = self.app_module.format_distance_filter(None)
            self.assertEqual(result, "0.00 m")
    
    def test_format_altitude_filter(self):
        """Test format_altitude template filter"""
        with self.app.app_context():
            # Test valid values
            result = self.app_module.format_altitude_filter(123.45)
            self.assertEqual(result, "123.45 m")
            
            # Test negative values
            result = self.app_module.format_altitude_filter(-50.5)
            self.assertEqual(result, "-50.50 m")
            
            # Test invalid values
            result = self.app_module.format_altitude_filter(None)
            self.assertEqual(result, "0.00 m")
    
    def test_friendly_name_filter(self):
        """Test friendly_name template filter"""
        with self.app.app_context():
            # Test known column names
            result = self.app_module.friendly_name_filter("LapNumber")
            self.assertEqual(result, "Lap")
            
            result = self.app_module.friendly_name_filter("AltitudeDelta_m")
            self.assertEqual(result, "Altitude Δ")
            
            # Test unknown column names
            result = self.app_module.friendly_name_filter("UnknownColumn")
            self.assertEqual(result, "UnknownColumn")
    
    def test_template_filters_registration(self):
        """Test that all template filters are properly registered"""
        with self.app.app_context():
            # Check that filters are registered in Flask app
            self.assertIn('regex_search', self.app.jinja_env.filters)
            self.assertIn('format_distance', self.app.jinja_env.filters)
            self.assertIn('format_altitude', self.app.jinja_env.filters)
            self.assertIn('friendly_name', self.app.jinja_env.filters)
    
    def test_template_filters_in_context(self):
        """Test template filters work in template context"""
        with self.app.app_context():
            # Test that filters can be called through Jinja environment
            distance_filter = self.app.jinja_env.filters['format_distance']
            result = distance_filter(1000)
            self.assertEqual(result, "1.00 km")
            
            altitude_filter = self.app.jinja_env.filters['format_altitude']
            result = altitude_filter(100.5)
            self.assertEqual(result, "100.50 m")
            
            friendly_filter = self.app.jinja_env.filters['friendly_name']
            result = friendly_filter("LapDistance_m")
            self.assertEqual(result, "Lap Distance")

if __name__ == '__main__':
    unittest.main()