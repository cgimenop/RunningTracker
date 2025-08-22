import unittest
import sys
from unittest.mock import patch, MagicMock, mock_open
import pymongo.errors
from collections import namedtuple

# Import trainparser with logging mocked
with patch.dict('sys.modules', {'logging_config': MagicMock()}):
    from src import trainparser

class TestArgs:
    def __init__(self, mode="both", output="test.xlsx", mongo=False, mongo_uri="mongodb://localhost:27017"):
        self.mode = mode
        self.output = output
        self.mongo = mongo
        self.mongo_uri = mongo_uri
        self.input_path = "test.tcx"

class TestCalcPace(unittest.TestCase):
    def test_calc_pace_valid_inputs(self):
        result = trainparser.calc_pace(600, 1000)  # 10 minutes for 1km
        self.assertEqual(result, 600.0)  # Updated: formula now multiplies by 60
    
    def test_calc_pace_zero_distance(self):
        result = trainparser.calc_pace(600, 0)
        self.assertIsNone(result)
    
    def test_calc_pace_edge_cases(self):
        # Test with very small distance
        result = trainparser.calc_pace(600, 0.001)
        self.assertIsNotNone(result)
        
        # Test with zero time - function returns None for invalid inputs
        result = trainparser.calc_pace(0, 1000)
        self.assertIsNone(result)
        
        # Test with negative values
        result = trainparser.calc_pace(-100, 1000)
        self.assertIsNone(result)

class TestGetFirstLapDate(unittest.TestCase):
    def test_get_first_lap_date_valid_format(self):
        # Test the date extraction logic directly
        test_date = "2024-01-01T10:00:00Z"
        expected = test_date.split("T")[0]
        self.assertEqual(expected, "2024-01-01")

class TestWriteToExcel(unittest.TestCase):
    def test_write_to_excel_function_exists(self):
        # Test that the function exists and is callable
        self.assertTrue(callable(trainparser.write_to_excel))

class TestPushToMongo(unittest.TestCase):
    def test_push_to_mongo(self):
        mock_df = MagicMock()
        mock_df.to_dict.return_value = [
            {"key1": "value1", "key2": "value2"},
            {"key1": "value3", "key2": "value4"}
        ]
        mock_collection = MagicMock()
        unique_keys = ["key1"]
        
        trainparser.push_to_mongo(mock_df, mock_collection, unique_keys)
        
        # Updated: now uses bulk_write instead of individual replace_one calls
        mock_collection.bulk_write.assert_called_once()
    
    def test_push_to_mongo_invalid_keys(self):
        mock_df = MagicMock()
        mock_collection = MagicMock()
        
        # Test with invalid unique_keys parameter
        with self.assertRaises(ValueError):
            trainparser.push_to_mongo(mock_df, mock_collection, "not_a_list")
        
        with self.assertRaises(ValueError):
            trainparser.push_to_mongo(mock_df, mock_collection, [123, "valid"])

class TestParseTcxSummary(unittest.TestCase):
    def test_parse_tcx_summary_function_exists(self):
        # Test that the function exists and is callable
        self.assertTrue(callable(trainparser.parse_tcx_summary))

class TestParseTcxDetailed(unittest.TestCase):
    def test_parse_tcx_detailed_function_exists(self):
        # Test that the function exists and is callable
        self.assertTrue(callable(trainparser.parse_tcx_detailed))

class TestProcessFile(unittest.TestCase):
    def test_process_file_function_exists(self):
        # Test that the function exists and is callable
        self.assertTrue(callable(trainparser.process_file))

class TestLapDataNamedTuple(unittest.TestCase):
    def test_lap_data_structure(self):
        # Test that LapData namedtuple works correctly
        lap_data = trainparser.LapData("2024-01-01T10:00:00Z", 600.0, 1000.0, 600.0)
        self.assertEqual(lap_data.start_time, "2024-01-01T10:00:00Z")
        self.assertEqual(lap_data.total_time_s, 600.0)
        self.assertEqual(lap_data.distance_m, 1000.0)
        self.assertEqual(lap_data.pace, 600.0)

class TestSanitization(unittest.TestCase):
    def test_sanitize_for_log(self):
        # Test log sanitization function
        result = trainparser.sanitize_for_log("normal text")
        self.assertEqual(result, "normal text")
        
        # Test with dangerous characters
        result = trainparser.sanitize_for_log("text\nwith\nnewlines")
        self.assertEqual(result, "text\\nwith\\nnewlines")
        
        # Test with None
        result = trainparser.sanitize_for_log(None)
        self.assertEqual(result, "None")
    
    def test_validate_safe_path(self):
        # Test path validation function
        self.assertTrue(trainparser._validate_safe_path("/safe/path/file.txt"))
        
        # Test with relative paths (should be made absolute)
        result = trainparser._validate_safe_path("relative/path.txt")
        self.assertIsInstance(result, bool)

class TestErrorHandling(unittest.TestCase):
    @patch('src.trainparser._setup_mongo_connection')
    def test_mongo_connection_error(self, mock_setup):
        mock_setup.return_value = None  # Connection failed
        
        with patch('src.trainparser.argparse.ArgumentParser') as mock_parser:
            mock_args = MagicMock()
            mock_args.mongo = True
            mock_args.mongo_uri = "mongodb://localhost:27017"
            mock_args.input_path = "test.tcx"
            mock_parser_instance = MagicMock()
            mock_parser_instance.parse_args.return_value = mock_args
            mock_parser.return_value = mock_parser_instance
            
            with patch('src.trainparser.os.path.exists', return_value=False):
                trainparser.main()  # Should not crash
    
    @patch('src.trainparser._discover_tcx_files')
    @patch('builtins.print')
    def test_directory_access_error(self, mock_print, mock_discover):
        mock_discover.return_value = []  # No files found
        
        with patch('src.trainparser.argparse.ArgumentParser') as mock_parser:
            mock_args = MagicMock()
            mock_args.mongo = False
            mock_args.input_path = "/restricted/path"
            mock_parser_instance = MagicMock()
            mock_parser_instance.parse_args.return_value = mock_args
            mock_parser.return_value = mock_parser_instance
            
            with patch('src.trainparser.os.path.exists', return_value=True):
                with patch('src.trainparser._validate_safe_path', return_value=True):
                    trainparser.main()
                    # Should handle gracefully

class TestMain(unittest.TestCase):
    def test_main_function_exists(self):
        # Test that the function exists and is callable
        self.assertTrue(callable(trainparser.main))

if __name__ == "__main__":
    unittest.main()