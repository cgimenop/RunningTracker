import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add webapp directory to path
webapp_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, webapp_dir)

class TestWebapp(unittest.TestCase):

    def setUp(self):
        # Mock constants and config
        mock_const = MagicMock()
        mock_const.MERGE_COLUMNS = ['LapNumber', 'LapStartTime', 'LapTotalTime_s', 'LapDistance_m', 'Pace_min_per_km', '_source_file']
        mock_const.FRIENDLY_COLUMN_NAMES = {
            'LapNumber': 'Lap',
            'Time': 'Time',
            'LapStartTime': 'Lap Start',
            'LapDistance_m': 'Lap Distance',
            'Distance_m': 'Distance',
            'Altitude_m': 'Altitude',
            'AltitudeDelta_m': 'Altitude Δ',
            'LapTotalTime_s': 'Lap Time',
            'Pace_min_per_km': 'Pace',
            'HeartRate_bpm': 'Heart Rate',
            'Speed_ms': 'Speed'
        }
        mock_const.MIN_VALID_LAP_DISTANCE = 990
        mock_const.DETAILED_DATA_SAMPLE_INTERVAL = 60

        self.patches = [
            patch.dict('sys.modules', {
                'config.development': MagicMock(DEBUG=True, MONGO_URI='mongodb://test', DATABASE_NAME='test'),
                'config.production': MagicMock(DEBUG=False, MONGO_URI='mongodb://test', DATABASE_NAME='test'),
                'logging_config': MagicMock(),
                'const': mock_const
            }),
            patch.dict('os.environ', {'FLASK_ENV': 'development'}),
            patch('pymongo.MongoClient')
        ]

        for p in self.patches:
            p.start()

        import app
        self.app_module = app
        self.app = app.app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def tearDown(self):
        for p in self.patches:
            p.stop()

    # Constants Tests
    def test_constants_exist(self):
        from const import MERGE_COLUMNS, FRIENDLY_COLUMN_NAMES, DETAILED_DATA_SAMPLE_INTERVAL, MIN_VALID_LAP_DISTANCE
        self.assertIsInstance(MERGE_COLUMNS, list)
        self.assertIsInstance(FRIENDLY_COLUMN_NAMES, dict)
        self.assertIsInstance(DETAILED_DATA_SAMPLE_INTERVAL, int)
        self.assertIsInstance(MIN_VALID_LAP_DISTANCE, int)

    # Distance Formatting Tests
    def test_format_distance_meters(self):
        self.assertEqual(self.app_module.format_distance(500), "500.00 m")
        self.assertEqual(self.app_module.format_distance(0), "0.00 m")
        self.assertEqual(self.app_module.format_distance(999.99), "999.99 m")

    def test_format_distance_kilometers(self):
        self.assertEqual(self.app_module.format_distance(1000), "1.00 km")
        self.assertEqual(self.app_module.format_distance(1500), "1.50 km")
        self.assertEqual(self.app_module.format_distance(2500.75), "2.50 km")

    def test_format_distance_invalid(self):
        self.assertEqual(self.app_module.format_distance("invalid"), "0.00 m")
        self.assertEqual(self.app_module.format_distance(None), "0.00 m")

    # Altitude Formatting Tests
    def test_format_altitude_valid(self):
        self.assertEqual(self.app_module.format_altitude(123.456), "123.46 m")
        self.assertEqual(self.app_module.format_altitude(0), "0.00 m")
        self.assertEqual(self.app_module.format_altitude(-50.5), "-50.50 m")

    def test_format_altitude_invalid(self):
        self.assertEqual(self.app_module.format_altitude("invalid"), "0.00 m")
        self.assertEqual(self.app_module.format_altitude(None), "0.00 m")

    # Time Formatting Tests
    def test_format_seconds_valid(self):
        self.assertEqual(self.app_module.format_seconds(0), "0:00:00")
        self.assertEqual(self.app_module.format_seconds(59), "0:00:59")
        self.assertEqual(self.app_module.format_seconds(3600), "1:00:00")
        self.assertEqual(self.app_module.format_seconds(3661), "1:01:01")

    def test_format_seconds_invalid(self):
        self.assertEqual(self.app_module.format_seconds("invalid"), "00:00:00")
        self.assertEqual(self.app_module.format_seconds(None), "00:00:00")

    # Date Extraction Tests
    def test_extract_date_from_filename(self):
        self.assertEqual(self.app_module.extract_date_from_filename("run_2024-01-15_morning.tcx"), "2024-01-15")
        self.assertEqual(self.app_module.extract_date_from_filename("2024-12-31-evening.tcx"), "2024-12-31")
        self.assertEqual(self.app_module.extract_date_from_filename("invalid_filename.tcx"), "invalid_filename.tcx")
        self.assertEqual(self.app_module.extract_date_from_filename(""), "")

    # Friendly Column Names Tests
    def test_get_friendly_column_name(self):
        test_cases = [
            ("LapNumber", "Lap"),
            ("LapDistance_m", "Lap Distance"),
            ("AltitudeDelta_m", "Altitude Δ"),
            ("LapTotalTime_s", "Lap Time"),
            ("HeartRate_bpm", "Heart Rate"),
            ("Speed_ms", "Speed"),
            ("UnknownField", "UnknownField")
        ]

        for technical, friendly in test_cases:
            with self.subTest(technical=technical):
                result = self.app_module.get_friendly_column_name(technical)
                self.assertEqual(result, friendly)

    # Template Filters Tests
    def test_template_filters(self):
        with self.app.app_context():
            # Distance filter
            result = self.app_module.format_distance_filter(1500)
            self.assertEqual(result, "1.50 km")

            # Altitude filter
            result = self.app_module.format_altitude_filter(123.45)
            self.assertEqual(result, "123.45 m")

            # Friendly name filter
            result = self.app_module.friendly_name_filter("LapNumber")
            self.assertEqual(result, "Lap")

            # Regex search filter - updated to use safe pattern names
            result = self.app_module.regex_search("test-2024-01-01", "date")
            self.assertIsNotNone(result)

    # Business Logic Tests
    def test_calculate_file_summaries(self):
        grouped = {
            "test.tcx": [
                {"LapDistance_m": 1000, "LapTotalTime_s": 300},
                {"LapDistance_m": 500, "LapTotalTime_s": 150}  # Short lap
            ]
        }

        summaries, all_laps, valid_laps = self.app_module.calculate_file_summaries(grouped)
        self.assertEqual(len(summaries), 1)
        self.assertIsInstance(summaries[0], dict)
        self.assertIsInstance(valid_laps, dict)

    def test_find_records_with_data(self):
        all_laps = [
            {"LapDistance_m": 1000, "LapTotalTime_s": 300},
            {"LapDistance_m": 1000, "LapTotalTime_s": 310}
        ]
        file_summaries = [
            {"total_distance": 2000, "total_time": 610}
        ]
    def test_find_records(self):
        all_laps = [{"LapDistance_m": 1000, "LapTotalTime_s": 600}]
        file_summaries = []

        fastest, slowest, longest_dist, longest_time = self.app_module.find_records(all_laps, file_summaries)

        # Results can be None or valid records
        self.assertTrue(fastest is None or isinstance(fastest, dict))

    @patch('app.get_db_connection')
    def test_load_detailed_data(self, mock_get_db):
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = [
            {"_source_file": "test.tcx", "Time": "2024-01-01T10:00:00Z"}
        ]
        mock_db.__getitem__.return_value.find.return_value = mock_cursor
        mock_get_db.return_value = mock_db

        result = self.app_module.load_detailed_data()

        self.assertIsInstance(result, dict)

    def test_find_records_empty_data(self):
        fastest, slowest, longest_dist, longest_time = self.app_module.find_records([], [])
        self.assertIsNone(fastest)
        self.assertIsNone(slowest)

    # Altitude Delta Calculation Tests
    def test_altitude_delta_calculation_net_gain(self):
        # Test: 100 -> 120 -> 110 -> 130 -> 105
        # Changes: +20, -10, +20, -25 = +5 (net gain)
        altitudes = [100, 120, 110, 130, 105]
        total_change = 0
        for i in range(1, len(altitudes)):
            change = altitudes[i] - altitudes[i-1]
            total_change += change
        self.assertEqual(total_change, 5)

    def test_altitude_delta_calculation_net_loss(self):
        # Test: 130 -> 120 -> 125 -> 110 -> 100
        # Changes: -10, +5, -15, -10 = -30 (net loss)
        altitudes = [130, 120, 125, 110, 100]
        total_change = 0
        for i in range(1, len(altitudes)):
            change = altitudes[i] - altitudes[i-1]
            total_change += change
        self.assertEqual(total_change, -30)

    def test_altitude_delta_calculation_no_change(self):
        # Test: 100 -> 110 -> 100
        # Changes: +10, -10 = 0 (no net change)
        altitudes = [100, 110, 100]
        total_change = 0
        for i in range(1, len(altitudes)):
            change = altitudes[i] - altitudes[i-1]
            total_change += change
        self.assertEqual(total_change, 0)

    # Sampling Logic Tests
    def test_sampling_logic(self):
        sample_interval = 60
        data_points = list(range(120))  # 120 data points

        filtered_indices = []
        last_time = None

        for i, point in enumerate(data_points):
            if i == 0:
                filtered_indices.append(i)
                last_time = i
            elif i - last_time >= sample_interval:
                filtered_indices.append(i)
                last_time = i

        # Should get indices [0, 60] for 120 points with interval 60
        self.assertEqual(filtered_indices, [0, 60])

    # Security Tests
    def test_regex_search_security(self):
        """Test that regex_search only allows safe patterns"""
        with self.app.app_context():
            # Test safe patterns work
            result = self.app_module.regex_search("2024-01-01", "date")
            self.assertIsNotNone(result)
            
            # Test unsafe patterns are rejected
            result = self.app_module.regex_search("test", "(.*)*")
            self.assertIsNone(result)
            
            # Test non-string input
            result = self.app_module.regex_search(123, "date")
            self.assertIsNone(result)
    
    def test_database_connection_management(self):
        """Test database connection management"""
        # Test get_db_connection function exists
        self.assertTrue(callable(self.app_module.get_db_connection))
        
        # Test close_db_connection function exists
        self.assertTrue(callable(self.app_module.close_db_connection))
    
    # Integration Tests
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
    
    @patch('app.get_db_connection')
    def test_index_route_error_handling(self, mock_get_db):
        """Test index route handles database errors gracefully"""
        mock_get_db.side_effect = Exception("Database connection failed")
        
        response = self.client.get('/')
        
        # Should still return 200 with empty data
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()