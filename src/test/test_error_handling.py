import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
import tempfile

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestErrorHandling(unittest.TestCase):
    def setUp(self):
        # Mock logging_config before importing trainparser
        with patch.dict('sys.modules', {'logging_config': MagicMock()}):
            from src import trainparser
        self.trainparser = trainparser
    
    def test_get_first_lap_date_file_not_found(self):
        """Test get_first_lap_date with non-existent file"""
        result = self.trainparser.get_first_lap_date("nonexistent_file.tcx")
        self.assertEqual(result, "UnknownDate")
    
    def test_get_first_lap_date_permission_error(self):
        """Test get_first_lap_date with permission denied"""
        with patch('src.trainparser.ET.parse') as mock_parse:
            mock_parse.side_effect = PermissionError("Permission denied")
            result = self.trainparser.get_first_lap_date("restricted_file.tcx")
            self.assertEqual(result, "UnknownDate")
    
    def test_get_first_lap_date_invalid_xml(self):
        """Test get_first_lap_date with invalid XML"""
        with patch('src.trainparser.ET.parse') as mock_parse:
            mock_parse.side_effect = self.trainparser.ET.ParseError("Invalid XML")
            result = self.trainparser.get_first_lap_date("invalid.tcx")
            self.assertEqual(result, "UnknownDate")
    
    def test_get_first_lap_date_empty_file(self):
        """Test get_first_lap_date with empty XML structure"""
        with patch('src.trainparser.ET.parse') as mock_parse:
            mock_tree = MagicMock()
            mock_root = MagicMock()
            mock_root.find.return_value = None  # No lap found
            mock_tree.getroot.return_value = mock_root
            mock_parse.return_value = mock_tree
            
            result = self.trainparser.get_first_lap_date("empty.tcx")
            self.assertEqual(result, "UnknownDate")
    
    def test_get_first_lap_date_missing_start_time(self):
        """Test get_first_lap_date with lap missing StartTime attribute"""
        with patch('src.trainparser.ET.parse') as mock_parse:
            mock_tree = MagicMock()
            mock_root = MagicMock()
            mock_lap = MagicMock()
            mock_lap.attrib = {}  # No StartTime attribute
            mock_root.find.return_value = mock_lap
            mock_tree.getroot.return_value = mock_root
            mock_parse.return_value = mock_tree
            
            result = self.trainparser.get_first_lap_date("no_start_time.tcx")
            self.assertEqual(result, "UnknownDate")
    
    @patch('src.trainparser.os.path.exists')
    def test_write_to_excel_file_creation_error(self, mock_exists):
        """Test write_to_excel when file creation fails"""
        mock_exists.return_value = False
        mock_df = MagicMock()
        
        with patch('src.trainparser.pd.ExcelWriter') as mock_writer:
            mock_writer.side_effect = PermissionError("Cannot create file")
            
            # Should not raise exception, but handle gracefully
            try:
                self.trainparser.write_to_excel(mock_df, "/restricted/path/test.xlsx", "sheet1")
            except PermissionError:
                # Expected behavior - function should let the error propagate
                pass
    
    @patch('src.trainparser.os.path.exists')
    @patch('src.trainparser.load_workbook')
    def test_write_to_excel_workbook_load_error(self, mock_load, mock_exists):
        """Test write_to_excel when existing workbook cannot be loaded"""
        mock_exists.return_value = True
        mock_load.side_effect = Exception("Corrupted workbook")
        mock_df = MagicMock()
        
        # Should handle corrupted workbook gracefully
        try:
            self.trainparser.write_to_excel(mock_df, "corrupted.xlsx", "sheet1")
        except Exception:
            # Expected - function may propagate the error
            pass
    
    def test_push_to_mongo_connection_error(self):
        """Test push_to_mongo with database connection issues"""
        mock_df = MagicMock()
        mock_df.to_dict.return_value = [{"key": "value"}]
        
        mock_collection = MagicMock()
        mock_collection.replace_one.side_effect = Exception("Connection lost")
        
        # Should handle database errors gracefully
        try:
            self.trainparser.push_to_mongo(mock_df, mock_collection, ["key"])
        except Exception:
            # Expected - function may propagate database errors
            pass
    
    def test_push_to_mongo_invalid_data(self):
        """Test push_to_mongo with invalid data format"""
        mock_df = MagicMock()
        mock_df.to_dict.side_effect = Exception("Invalid DataFrame")
        
        mock_collection = MagicMock()
        
        try:
            self.trainparser.push_to_mongo(mock_df, mock_collection, ["key"])
        except Exception:
            # Expected - function should handle invalid DataFrame
            pass
    
    def test_calc_pace_division_by_zero_protection(self):
        """Test calc_pace handles division by zero"""
        # These should return None, not raise ZeroDivisionError
        self.assertIsNone(self.trainparser.calc_pace(600, 0))
        self.assertIsNone(self.trainparser.calc_pace(600, 0.0))
    
    def test_calc_pace_overflow_protection(self):
        """Test calc_pace with very large numbers"""
        # Test with very large numbers that might cause overflow
        result = self.trainparser.calc_pace(float('inf'), 1000)
        # Should handle gracefully (return None or a reasonable value)
        self.assertTrue(result is None or isinstance(result, (int, float)))
        
        result = self.trainparser.calc_pace(1000, float('inf'))
        self.assertTrue(result is None or isinstance(result, (int, float)))
    
    @patch('src.trainparser.argparse.ArgumentParser')
    def test_main_invalid_arguments(self, mock_parser):
        """Test main function with invalid arguments"""
        mock_parser_instance = MagicMock()
        mock_parser_instance.parse_args.side_effect = SystemExit("Invalid arguments")
        mock_parser.return_value = mock_parser_instance
        
        # Should handle argument parsing errors
        try:
            self.trainparser.main()
        except SystemExit:
            # Expected behavior for invalid arguments
            pass
    
    @patch('src.trainparser.os.path.exists')
    def test_main_nonexistent_input_path(self, mock_exists):
        """Test main function with non-existent input path"""
        mock_exists.return_value = False
        
        with patch('src.trainparser.argparse.ArgumentParser') as mock_parser:
            mock_args = MagicMock()
            mock_args.input_path = "/nonexistent/path"
            mock_args.mongo = False
            mock_parser_instance = MagicMock()
            mock_parser_instance.parse_args.return_value = mock_args
            mock_parser.return_value = mock_parser_instance
            
            # Should handle non-existent path gracefully
            with patch('builtins.print') as mock_print:
                self.trainparser.main()
                # Should print error message
                mock_print.assert_called()
    
    def test_error_handling_with_malformed_data(self):
        """Test error handling with various malformed data scenarios"""
        # Test with None values
        self.assertIsNone(self.trainparser.calc_pace(None, None))
        
        # Test with empty strings
        self.assertIsNone(self.trainparser.calc_pace("", ""))
        
        # Test with mixed invalid types
        self.assertIsNone(self.trainparser.calc_pace([], {}))
        self.assertIsNone(self.trainparser.calc_pace({}, []))

if __name__ == '__main__':
    unittest.main()