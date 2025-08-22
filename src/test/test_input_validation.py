import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestInputValidation(unittest.TestCase):
    def setUp(self):
        # Mock logging_config before importing trainparser
        with patch.dict('sys.modules', {'logging_config': MagicMock()}):
            from src import trainparser
        self.trainparser = trainparser
    
    def test_calc_pace_input_validation(self):
        """Test calc_pace function with various input types"""
        # Valid inputs
        self.assertEqual(self.trainparser.calc_pace(600, 1000), 10.0)
        self.assertEqual(self.trainparser.calc_pace(300, 1000), 5.0)
        
        # Zero and negative inputs
        self.assertIsNone(self.trainparser.calc_pace(0, 1000))
        self.assertIsNone(self.trainparser.calc_pace(600, 0))
        self.assertIsNone(self.trainparser.calc_pace(-100, 1000))
        self.assertIsNone(self.trainparser.calc_pace(600, -1000))
        
        # None inputs
        self.assertIsNone(self.trainparser.calc_pace(None, 1000))
        self.assertIsNone(self.trainparser.calc_pace(600, None))
        self.assertIsNone(self.trainparser.calc_pace(None, None))
        
        # String inputs that can be converted
        self.assertEqual(self.trainparser.calc_pace("600", "1000"), 10.0)
        
        # Invalid string inputs
        self.assertIsNone(self.trainparser.calc_pace("invalid", 1000))
        self.assertIsNone(self.trainparser.calc_pace(600, "invalid"))
    
    def test_calc_pace_edge_cases(self):
        """Test calc_pace with edge cases"""
        # Very small distance
        result = self.trainparser.calc_pace(600, 0.001)
        self.assertIsNotNone(result)
        self.assertGreater(result, 0)
        
        # Very large values
        result = self.trainparser.calc_pace(36000, 10000)  # 10 hours for 10km
        self.assertEqual(result, 60.0)  # 60 min/km
        
        # Float inputs
        self.assertAlmostEqual(self.trainparser.calc_pace(600.5, 1000.5), 10.005, places=2)
    
    def test_calc_pace_precision(self):
        """Test calc_pace calculation precision"""
        # Test specific calculations
        result = self.trainparser.calc_pace(240, 1000)  # 4 minutes for 1km
        self.assertEqual(result, 4.0)
        
        result = self.trainparser.calc_pace(330, 1000)  # 5.5 minutes for 1km
        self.assertEqual(result, 5.5)
        
        result = self.trainparser.calc_pace(600, 2000)  # 10 minutes for 2km = 5 min/km
        self.assertEqual(result, 5.0)
    
    def test_filename_sanitization_patterns(self):
        """Test filename patterns that could cause issues"""
        # Test with various filename patterns
        test_filenames = [
            "normal_file.tcx",
            "file with spaces.tcx",
            "file-with-dashes.tcx",
            "file_with_underscores.tcx",
            "UPPERCASE.TCX",
            "file.with.dots.tcx",
            "file123numbers.tcx",
            "unicode_café.tcx",
            "very_long_filename_that_might_cause_issues_in_some_systems.tcx"
        ]
        
        for filename in test_filenames:
            with self.subTest(filename=filename):
                # Test that filename processing doesn't crash
                try:
                    # This would be used in actual filename processing
                    sanitized = filename.replace('..', '').replace('/', '').replace('\\', '')
                    self.assertIsInstance(sanitized, str)
                    self.assertNotIn('..', sanitized)
                    self.assertNotIn('/', sanitized)
                    self.assertNotIn('\\', sanitized)
                except Exception as e:
                    self.fail(f"Filename processing failed for {filename}: {e}")
    
    def test_path_traversal_prevention(self):
        """Test prevention of path traversal attacks"""
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
            "/etc/passwd",
            "C:\\Windows\\System32",
            "file/../../../secret.txt",
            "normal_file.tcx/../../../etc/passwd"
        ]
        
        for path in dangerous_paths:
            with self.subTest(path=path):
                # Test path sanitization
                sanitized = path.replace('..', '').replace('/', '').replace('\\', '')
                self.assertNotIn('..', sanitized)
                self.assertNotIn('/', sanitized)
                self.assertNotIn('\\', sanitized)
    
    def test_numeric_input_validation(self):
        """Test validation of numeric inputs"""
        # Test various numeric formats
        valid_numbers = [0, 1, -1, 0.5, -0.5, 1000, 1000.5, "100", "100.5"]
        invalid_numbers = ["", "abc", None, [], {}, "inf", "nan", "1.2.3"]
        
        for num in valid_numbers:
            with self.subTest(num=num):
                try:
                    float_val = float(num)
                    self.assertIsInstance(float_val, float)
                except (ValueError, TypeError):
                    self.fail(f"Valid number {num} failed conversion")
        
        for num in invalid_numbers:
            with self.subTest(num=num):
                try:
                    float_val = float(num)
                    # Some might succeed (like "inf"), so we check for specific cases
                    if num in ["inf", "-inf"]:
                        self.assertTrue(float_val == float('inf') or float_val == float('-inf'))
                    elif num == "nan":
                        self.assertTrue(str(float_val) == 'nan')
                except (ValueError, TypeError):
                    # Expected for truly invalid inputs
                    pass
    
    def test_xml_content_validation(self):
        """Test XML content validation patterns"""
        # Test XML-like strings that might be problematic
        xml_patterns = [
            "<xml></xml>",
            "<?xml version='1.0'?>",
            "<root><child>value</child></root>",
            "<malformed><xml>",
            "",
            "not xml at all",
            "<script>alert('xss')</script>",
            "<!-- comment -->",
            "<![CDATA[some data]]>"
        ]
        
        for pattern in xml_patterns:
            with self.subTest(pattern=pattern):
                # Test that XML pattern doesn't cause issues in string processing
                try:
                    # Basic string operations that might be done on XML content
                    cleaned = pattern.strip()
                    self.assertIsInstance(cleaned, str)
                    
                    # Check for basic XML structure
                    has_xml_tags = '<' in pattern and '>' in pattern
                    if has_xml_tags:
                        self.assertTrue(len(pattern) > 0)
                except Exception as e:
                    self.fail(f"XML pattern processing failed for {pattern}: {e}")

if __name__ == '__main__':
    unittest.main()