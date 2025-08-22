import unittest
from unittest.mock import patch, MagicMock
import sys
import os
from collections import defaultdict

# Add webapp directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestDataProcessing(unittest.TestCase):
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
    
    def test_extract_date_from_filename_valid_dates(self):
        """Test date extraction from various filename formats"""
        test_cases = [
            ("run_2024-01-15_morning.tcx", "2024-01-15"),
            ("2024-12-31-evening.tcx", "2024-12-31"),
            ("activity_2023-06-20.tcx", "2023-06-20"),
            ("RunnerUp_2025-08-05-08-24-01_Running.tcx", "2025-08-05"),
            ("workout-2022-03-10-data.tcx", "2022-03-10")
        ]
        
        for filename, expected_date in test_cases:
            with self.subTest(filename=filename):
                result = self.app_module.extract_date_from_filename(filename)
                self.assertEqual(result, expected_date)
    
    def test_extract_date_from_filename_no_date(self):
        """Test date extraction when no date pattern exists"""
        test_cases = [
            "invalid_filename.tcx",
            "run_morning.tcx",
            "activity.tcx",
            "",
            "2024-1-1.tcx",  # Invalid format
            "24-01-15.tcx"   # Invalid year format
        ]
        
        for filename in test_cases:
            with self.subTest(filename=filename):
                result = self.app_module.extract_date_from_filename(filename)
                self.assertEqual(result, filename)
    
    def test_get_friendly_column_name_known_columns(self):
        """Test friendly name mapping for known columns"""
        test_cases = [
            ("LapNumber", "Lap"),
            ("LapDistance_m", "Lap Distance"),
            ("AltitudeDelta_m", "Altitude Δ"),
            ("LapTotalTime_s", "Lap Time"),
            ("HeartRate_bpm", "Heart Rate"),
            ("Speed_ms", "Speed"),
            ("Time", "Time"),
            ("Altitude_m", "Altitude")
        ]
        
        for technical, friendly in test_cases:
            with self.subTest(technical=technical):
                result = self.app_module.get_friendly_column_name(technical)
                self.assertEqual(result, friendly)
    
    def test_get_friendly_column_name_unknown_columns(self):
        """Test friendly name mapping for unknown columns"""
        unknown_columns = [
            "UnknownField",
            "CustomColumn",
            "NewMetric_xyz",
            ""
        ]
        
        for column in unknown_columns:
            with self.subTest(column=column):
                result = self.app_module.get_friendly_column_name(column)
                self.assertEqual(result, column)
    
    def test_calculate_file_summaries_valid_data(self):
        """Test file summary calculation with valid data"""
        grouped = {
            "test1.tcx": [
                {"LapDistance_m": 1000, "LapTotalTime_s": 300},
                {"LapDistance_m": 1500, "LapTotalTime_s": 450}
            ],
            "test2.tcx": [
                {"LapDistance_m": 2000, "LapTotalTime_s": 600}
            ]
        }
        
        summaries, all_laps, valid_laps = self.app_module.calculate_file_summaries(grouped)
        
        # Check summaries structure - updated field names
        self.assertEqual(len(summaries), 2)
        self.assertIn("source", summaries[0])
        self.assertIn("date", summaries[0])
        self.assertIn("total_distance", summaries[0])
        self.assertIn("total_time", summaries[0])
        self.assertIn("total_distance_formatted", summaries[0])
        self.assertIn("total_time_formatted", summaries[0])
        
        # Check all_laps and valid_laps structure
        self.assertIn("test1.tcx", all_laps)
        self.assertIn("test2.tcx", all_laps)
        self.assertIn("test1.tcx", valid_laps)
        self.assertIn("test2.tcx", valid_laps)
    
    def test_calculate_file_summaries_invalid_data(self):
        """Test file summary calculation with invalid data"""
        grouped = {
            "test.tcx": [
                {"LapDistance_m": "invalid", "LapTotalTime_s": None},
                {"LapDistance_m": None, "LapTotalTime_s": "invalid"}
            ]
        }
        
        summaries, all_laps, valid_laps = self.app_module.calculate_file_summaries(grouped)
        
        # Should handle invalid data gracefully
        self.assertEqual(len(summaries), 1)
        self.assertEqual(summaries[0]["total_distance"], 0)
        self.assertEqual(summaries[0]["total_time"], 0)
    
    def test_find_records_with_valid_data(self):
        """Test record finding with valid lap data"""
        all_laps = [
            {"LapDistance_m": 1000, "LapTotalTime_s": 300, "_source_file": "test1.tcx"},
            {"LapDistance_m": 1000, "LapTotalTime_s": 250, "_source_file": "test2.tcx"},  # Fastest
            {"LapDistance_m": 1000, "LapTotalTime_s": 400, "_source_file": "test3.tcx"},  # Slowest
            {"LapDistance_m": 500, "LapTotalTime_s": 200, "_source_file": "test4.tcx"}   # Too short
        ]
        
        file_summaries = [
            {"total_distance": 2000, "total_time": 600},
            {"total_distance": 3000, "total_time": 800},  # Longest distance
            {"total_distance": 1500, "total_time": 900}   # Longest time
        ]
        
        fastest, slowest, longest_dist, longest_time = self.app_module.find_records(all_laps, file_summaries)
        
        # Check fastest lap (should be 250s)
        self.assertIsNotNone(fastest)
        self.assertEqual(fastest["LapTotalTime_s"], 250)
        
        # Check slowest lap (should be 400s, excluding short lap)
        self.assertIsNotNone(slowest)
        self.assertEqual(slowest["LapTotalTime_s"], 400)
        
        # Check longest distance file
        self.assertIsNotNone(longest_dist)
        self.assertEqual(longest_dist["total_distance"], 3000)
        
        # Check longest time file
        self.assertIsNotNone(longest_time)
        self.assertEqual(longest_time["total_time"], 900)
    
    def test_find_records_with_empty_data(self):
        """Test record finding with empty data"""
        fastest, slowest, longest_dist, longest_time = self.app_module.find_records([], [])
        
        self.assertIsNone(fastest)
        self.assertIsNone(slowest)
        self.assertIsNone(longest_dist)
        self.assertIsNone(longest_time)
    
    def test_find_records_with_invalid_data(self):
        """Test record finding with invalid data types"""
        all_laps = [
            {"LapDistance_m": "invalid", "LapTotalTime_s": "invalid"},
            {"LapDistance_m": None, "LapTotalTime_s": None}
        ]
        
        file_summaries = [
            {"total_distance": "invalid", "total_time": "invalid"}
        ]
        
        fastest, slowest, longest_dist, longest_time = self.app_module.find_records(all_laps, file_summaries)
        
        # Should handle invalid data gracefully
        self.assertIsNone(fastest)
        self.assertIsNone(slowest)
        # File summaries with invalid data should still return None
        self.assertIsNone(longest_dist)
        self.assertIsNone(longest_time)
    
    def test_is_valid_lap(self):
        """Test lap validation logic"""
        # Valid lap
        valid_lap = {"LapDistance_m": 1000}
        self.assertTrue(self.app_module._is_valid_lap(valid_lap))
        
        # Invalid laps
        invalid_laps = [
            {"LapDistance_m": 500},  # Too short
            {"LapDistance_m": None},  # None distance
            {"LapDistance_m": "invalid"},  # Invalid type
            {},  # Missing distance
        ]
        
        for lap in invalid_laps:
            with self.subTest(lap=lap):
                self.assertFalse(self.app_module._is_valid_lap(lap))
    
    def test_filter_data_by_interval(self):
        """Test data filtering by interval"""
        # Create test data with 120 points
        source_data = [{"index": i} for i in range(120)]
        
        filtered = self.app_module._filter_data_by_interval(source_data)
        
        # Should include first point and every 60th point
        self.assertGreater(len(filtered), 0)
        self.assertEqual(filtered[0]["index"], 0)  # First point always included
        
        # Check that filtering reduces data size
        self.assertLess(len(filtered), len(source_data))

    def test_calculate_merge_info(self):
        """Test merge info calculation for table cell merging"""
        filtered_data = [
            {"LapNumber": 1, "LapStartTime": "10:00:00"},
            {"LapNumber": 1, "LapStartTime": "10:00:00"},
            {"LapNumber": 2, "LapStartTime": "10:05:00"}
        ]
        
        # Test first row (should show with rowspan 2)
        merge_info = self.app_module._calculate_merge_info(filtered_data, 0)
        self.assertTrue(merge_info["LapNumber"]["show"])
        self.assertEqual(merge_info["LapNumber"]["rowspan"], 2)
        
        # Test second row (should not show)
        merge_info = self.app_module._calculate_merge_info(filtered_data, 1)
        self.assertFalse(merge_info["LapNumber"]["show"])
        
        # Test third row (should show with rowspan 1)
        merge_info = self.app_module._calculate_merge_info(filtered_data, 2)
        self.assertTrue(merge_info["LapNumber"]["show"])
        self.assertEqual(merge_info["LapNumber"]["rowspan"], 1)

if __name__ == '__main__':
    unittest.main()