import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add webapp directory to path
webapp_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, webapp_dir)

class TestWebappFunctions(unittest.TestCase):
    
    @patch('pymongo.MongoClient')
    def setUp(self, mock_mongo):
        # Mock MongoDB and config
        self.mock_client = MagicMock()
        self.mock_db = MagicMock()
        mock_mongo.return_value = self.mock_client
        self.mock_client.__getitem__.return_value = self.mock_db
        
        # Mock config modules, logging, and constants
        mock_const = MagicMock()
        mock_const.MERGE_COLUMNS = ['LapNumber', 'LapStartTime']
        mock_const.FRIENDLY_COLUMN_NAMES = {
            'LapDistance_m': 'Lap Distance',
            'LapTotalTime_s': 'Lap Time',
            'UnknownField': 'UnknownField'
        }
        mock_const.MIN_VALID_LAP_DISTANCE = 990
        mock_const.DETAILED_DATA_SAMPLE_INTERVAL = 10
        
        self.config_patches = [
            patch.dict('sys.modules', {
                'config.development': MagicMock(DEBUG=True, MONGO_URI='mongodb://localhost:27017', DATABASE_NAME='test'),
                'config.production': MagicMock(DEBUG=False, MONGO_URI='mongodb://localhost:27017', DATABASE_NAME='test'),
                'config.common': MagicMock(MONGO_URI='mongodb://localhost:27017', DATABASE_NAME='test'),
                'logging_config': MagicMock(),
                'const': mock_const
            }),
            patch.dict('os.environ', {'FLASK_ENV': 'development'}),
            patch('logging_config.setup_webapp_logging', return_value=MagicMock())
        ]
        
        for p in self.config_patches:
            p.start()
            
        # Import after mocking
        import app
        self.app_module = app
        self.app = app.app
        self.client = self.app.test_client()
    
    def tearDown(self):
        for p in self.config_patches:
            p.stop()

    def test_format_seconds_valid(self):
        result = self.app_module.format_seconds(3661)
        self.assertEqual(result, "1:01:01")

    def test_format_seconds_zero(self):
        result = self.app_module.format_seconds(0)
        self.assertEqual(result, "0:00:00")

    def test_format_seconds_invalid(self):
        result = self.app_module.format_seconds("invalid")
        self.assertEqual(result, "00:00:00")

    def test_format_seconds_none(self):
        result = self.app_module.format_seconds(None)
        self.assertEqual(result, "00:00:00")

    def test_extract_date_from_filename_valid(self):
        result = self.app_module.extract_date_from_filename("RunnerUp_2024-01-15-08-30-01_Running.tcx")
        self.assertEqual(result, "2024-01-15")

    def test_extract_date_from_filename_no_date(self):
        result = self.app_module.extract_date_from_filename("invalid_filename.tcx")
        self.assertEqual(result, "invalid_filename.tcx")

    def test_load_summary_data(self):
        # Mock database response
        self.mock_db.__getitem__.return_value.find.return_value = [
            {"_source_file": "test.tcx", "LapTotalTime_s": 600, "LapNumber": 1}
        ]
        
        grouped, all_laps = self.app_module.load_summary_data()
        
        self.assertIsInstance(grouped, dict)
        self.assertIsInstance(all_laps, list)

    def test_calculate_file_summaries(self):
        grouped = {"test.tcx": [{"LapDistance_m": 1000, "LapTotalTime_s": 600}]}
        
        summaries, all_laps, valid_laps = self.app_module.calculate_file_summaries(grouped)
        
        self.assertIsInstance(summaries, list)
        self.assertIsInstance(all_laps, dict)
        self.assertIsInstance(valid_laps, dict)

    def test_find_records(self):
        all_laps = [{"LapDistance_m": 1000, "LapTotalTime_s": 600}]
        file_summaries = [{"total_distance": 1000, "total_time": 600}]
        
        fastest, slowest, longest_dist, longest_time = self.app_module.find_records(all_laps, file_summaries)
        
        # Results can be None or valid records
        self.assertTrue(fastest is None or isinstance(fastest, dict))

    def test_load_detailed_data(self):
        # Mock database response
        self.mock_db.__getitem__.return_value.find.return_value = [
            {"_source_file": "test.tcx", "Time": "2024-01-01T10:00:00Z"}
        ]
        
        result = self.app_module.load_detailed_data()
        
        self.assertIsInstance(result, dict)

    @patch('app.load_detailed_data')
    @patch('app.find_records')
    @patch('app.calculate_file_summaries')
    @patch('app.load_summary_data')
    def test_index_route(self, mock_load_summary, mock_calc, mock_find, mock_detailed):
        # Mock all function returns
        mock_load_summary.return_value = ({}, [])
        mock_calc.return_value = ([], {}, {})
        mock_find.return_value = (None, None, None, None)
        mock_detailed.return_value = {}
        
        response = self.client.get('/')
        
        self.assertEqual(response.status_code, 200)
        mock_load_summary.assert_called_once()
        mock_calc.assert_called_once()
        mock_find.assert_called_once()
        mock_detailed.assert_called_once()

    def test_regex_search_filter(self):
        with self.app.app_context():
            result = self.app_module.regex_search("test-2024-01-01", r'(\d{4}-\d{2}-\d{2})')
            self.assertIsNotNone(result)

    def test_format_distance_meters(self):
        result = self.app_module.format_distance(500)
        self.assertEqual(result, "500.00 m")

    def test_format_distance_kilometers(self):
        result = self.app_module.format_distance(1500)
        self.assertEqual(result, "1.50 km")

    def test_format_distance_exact_kilometer(self):
        result = self.app_module.format_distance(1000)
        self.assertEqual(result, "1.00 km")

    def test_format_distance_invalid(self):
        result = self.app_module.format_distance("invalid")
        self.assertEqual(result, "0.00 m")

    def test_format_distance_filter(self):
        with self.app.app_context():
            result = self.app_module.format_distance_filter(2500)
            self.assertEqual(result, "2.50 km")

    def test_format_altitude(self):
        result = self.app_module.format_altitude(123.456)
        self.assertEqual(result, "123.46 m")

    def test_format_altitude_invalid(self):
        result = self.app_module.format_altitude("invalid")
        self.assertEqual(result, "0.00 m")

    def test_get_friendly_column_name(self):
        result = self.app_module.get_friendly_column_name("LapDistance_m")
        self.assertEqual(result, "Lap Distance")

    def test_get_friendly_column_name_unknown(self):
        result = self.app_module.get_friendly_column_name("UnknownField")
        self.assertEqual(result, "UnknownField")

    def test_friendly_name_filter(self):
        with self.app.app_context():
            result = self.app_module.friendly_name_filter("LapTotalTime_s")
            self.assertEqual(result, "Lap Time")

if __name__ == "__main__":
    unittest.main()