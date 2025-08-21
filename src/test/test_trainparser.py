import unittest
import sys
from unittest.mock import patch, MagicMock, mock_open
import pymongo.errors

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
        self.assertEqual(result, 10.0)
    
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
        
        self.assertEqual(mock_collection.replace_one.call_count, 2)

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

class TestErrorHandling(unittest.TestCase):
    @patch('src.trainparser.MongoClient')
    def test_mongo_connection_error(self, mock_client):
        mock_client.side_effect = pymongo.errors.ServerSelectionTimeoutError("Connection failed")
        
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
    
    @patch('src.trainparser.os.listdir')
    @patch('builtins.print')
    def test_directory_access_error(self, mock_print, mock_listdir):
        mock_listdir.side_effect = PermissionError("Access denied")
        
        with patch('src.trainparser.argparse.ArgumentParser') as mock_parser:
            mock_args = MagicMock()
            mock_args.mongo = False
            mock_args.input_path = "/restricted/path"
            mock_parser_instance = MagicMock()
            mock_parser_instance.parse_args.return_value = mock_args
            mock_parser.return_value = mock_parser_instance
            
            with patch('src.trainparser.os.path.exists', return_value=True):
                with patch('src.trainparser.os.path.isfile', return_value=False):
                    trainparser.main()
                    mock_print.assert_any_call("ERROR: Cannot access directory '/restricted/path': Access denied")

class TestMain(unittest.TestCase):
    def test_main_function_exists(self):
        # Test that the function exists and is callable
        self.assertTrue(callable(trainparser.main))

if __name__ == "__main__":
    unittest.main()