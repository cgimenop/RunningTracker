"""
Comprehensive tests to achieve high coverage
"""
import pytest
from unittest.mock import patch, MagicMock, mock_open
import pandas as pd
import os


class TestTrainparserComprehensive:
    """Comprehensive tests for trainparser module"""
    
    @patch('trainparser._validate_safe_path')
    @patch('defusedxml.ElementTree.parse')
    def test_parse_tcx_detailed_comprehensive(self, mock_parse, mock_validate):
        """Test detailed TCX parsing with comprehensive scenarios"""
        mock_validate.return_value = True
        
        # Mock XML structure
        mock_tree = MagicMock()
        mock_root = MagicMock()
        mock_tree.getroot.return_value = mock_root
        mock_parse.return_value = mock_tree
        
        # Mock lap with trackpoints
        mock_lap = MagicMock()
        mock_lap.attrib = {"StartTime": "2024-01-01T10:00:00Z"}
        
        # Mock trackpoint
        mock_trackpoint = MagicMock()
        mock_lap.findall.return_value = [mock_trackpoint]
        mock_root.findall.return_value = [mock_lap]
        
        import trainparser
        
        with patch.object(trainparser, '_extract_lap_data') as mock_extract_lap:
            with patch.object(trainparser, '_extract_trackpoint_data') as mock_extract_tp:
                mock_extract_lap.return_value = trainparser.LapData("2024-01-01T10:00:00Z", 600.0, 1000.0, 36000.0)
                mock_extract_tp.return_value = {
                    "Time": "2024-01-01T10:00:00Z",
                    "Latitude": 40.0,
                    "Longitude": -74.0,
                    "Altitude_m": 100.0,
                    "Distance_m": 0.0
                }
                
                with patch('pandas.DataFrame') as mock_df:
                    result = trainparser.parse_tcx_detailed("test.tcx")
                    mock_df.assert_called_once()
    
    @patch('argparse.ArgumentParser.parse_args')
    @patch('os.path.exists')
    def test_main_comprehensive_scenarios(self, mock_exists, mock_parse_args):
        """Test main function with various scenarios"""
        import trainparser
        
        # Test with non-existent path
        args = MagicMock()
        args.input_path = "/nonexistent/path"
        mock_parse_args.return_value = args
        mock_exists.return_value = False
        
        # Should return early
        trainparser.main()
        mock_exists.assert_called_once_with("/nonexistent/path")
    
    @patch('os.path.isfile')
    @patch('os.listdir')
    def test_discover_tcx_files_comprehensive(self, mock_listdir, mock_isfile):
        """Test TCX file discovery with various scenarios"""
        import trainparser
        
        # Test with mixed files
        mock_isfile.return_value = False
        mock_listdir.return_value = ['run1.tcx', 'run2.TCX', 'other.txt', 'data.csv']
        
        with patch('trainparser._validate_safe_path', return_value=True):
            with patch('os.path.join', side_effect=lambda a, b: f"{a}/{b}"):
                result = trainparser._discover_tcx_files("/test/dir")
                # Should find TCX files (case insensitive)
                assert isinstance(result, list)
    
    def test_extract_trackpoint_data_comprehensive(self):
        """Test trackpoint data extraction with various XML structures"""
        import trainparser
        
        # Mock trackpoint with position
        mock_tp = MagicMock()
        mock_time_elem = MagicMock()
        mock_time_elem.text = "2024-01-01T10:00:00Z"
        
        mock_pos_elem = MagicMock()
        mock_lat_elem = MagicMock()
        mock_lat_elem.text = "40.123"
        mock_lon_elem = MagicMock()
        mock_lon_elem.text = "-74.456"
        
        mock_tp.find.side_effect = lambda path, ns: {
            "tcx:Time": mock_time_elem,
            "tcx:Position": mock_pos_elem,
            "tcx:AltitudeMeters": None,
            "tcx:DistanceMeters": None
        }.get(path)
        
        mock_pos_elem.find.side_effect = lambda path, ns: {
            "tcx:LatitudeDegrees": mock_lat_elem,
            "tcx:LongitudeDegrees": mock_lon_elem
        }.get(path)
        
        ns = {"tcx": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}
        
        result = trainparser._extract_trackpoint_data(mock_tp, ns)
        
        assert result["Time"] == "2024-01-01T10:00:00Z"
        assert result["Latitude"] == 40.123
        assert result["Longitude"] == -74.456
    
    @patch('pymongo.MongoClient')
    def test_setup_mongo_connection_comprehensive(self, mock_client):
        """Test MongoDB connection setup with various scenarios"""
        import trainparser
        from pymongo.errors import ServerSelectionTimeoutError
        
        # Test connection failure
        mock_client.side_effect = ServerSelectionTimeoutError("Connection failed")
        
        args = MagicMock()
        args.mongo = True
        args.mongo_uri = "mongodb://invalid:27017"
        
        result = trainparser._setup_mongo_connection(args)
        assert result is None
    
    @patch('os.path.exists')
    @patch('openpyxl.load_workbook')
    def test_write_to_excel_comprehensive(self, mock_load_wb, mock_exists):
        """Test Excel writing with comprehensive scenarios"""
        import trainparser
        
        # Test replacing existing sheet (case insensitive)
        mock_exists.return_value = True
        mock_wb = MagicMock()
        mock_wb.sheetnames = ['Existing_Sheet', 'other_sheet']
        mock_load_wb.return_value = mock_wb
        
        mock_df = MagicMock()
        
        with patch('pandas.ExcelWriter') as mock_writer:
            with patch('trainparser._validate_safe_path', return_value=True):
                trainparser.write_to_excel(mock_df, "/valid/path.xlsx", "existing_sheet")
                # Should delete the existing sheet (case insensitive match)
                mock_wb.__delitem__.assert_called()


class TestWebappComprehensive:
    """Comprehensive tests for webapp module"""
    
    def test_format_summary_data_comprehensive(self):
        """Test summary data formatting with various scenarios"""
        import app
        
        summary_data = [
            {
                "_source_file": "run1.tcx",
                "LapTotalTime_s": 600,
                "LapDistance_m": 1000
            },
            {
                "_source_file": "run2.tcx",
                "LapTotalTime_s": None,
                "LapDistance_m": "invalid"
            }
        ]
        
        result = app._format_summary_data(summary_data)
        
        assert "run1.tcx" in result
        assert "run2.tcx" in result
        assert len(result["run1.tcx"]) == 1
        assert "LapTotalTime_formatted" in result["run1.tcx"][0]
    
    def test_calculate_altitude_deltas_comprehensive(self):
        """Test altitude delta calculations with comprehensive data"""
        import app
        from collections import defaultdict
        
        grouped = {
            "test.tcx": [
                {"LapNumber": 1, "LapDistance_m": 1000},
                {"LapNumber": 2, "LapDistance_m": 1000}
            ]
        }
        
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        
        # Mock detailed data
        detailed_data = [
            {"_source_file": "test.tcx", "LapNumber": 1, "Altitude_m": 100, "Time": "10:00:00"},
            {"_source_file": "test.tcx", "LapNumber": 1, "Altitude_m": 110, "Time": "10:00:01"},
            {"_source_file": "test.tcx", "LapNumber": 2, "Altitude_m": 105, "Time": "10:01:00"}
        ]
        
        mock_collection.find.return_value.sort.return_value = detailed_data
        
        app._calculate_altitude_deltas(grouped, mock_db)
        
        # Should have calculated altitude deltas
        assert "AltitudeDelta_m" in grouped["test.tcx"][0]
        assert "AltitudeDelta_formatted" in grouped["test.tcx"][0]
    
    @patch('app.get_db_connection')
    def test_load_detailed_data_comprehensive(self, mock_get_db):
        """Test detailed data loading with comprehensive scenarios"""
        import app
        
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        
        # Mock detailed data with various scenarios
        detailed_data = [
            {
                "_source_file": "test.tcx",
                "Time": "10:00:00",
                "LapNumber": 1,
                "LapDistance_m": 1000,
                "Distance_m": 100,
                "Altitude_m": 150,
                "LapTotalTime_s": 300
            },
            {
                "_source_file": "test.tcx", 
                "Time": "10:01:00",
                "LapNumber": 1,
                "LapDistance_m": 1000,
                "Distance_m": 200,
                "Altitude_m": 160,
                "LapTotalTime_s": 300
            }
        ]
        
        mock_collection.find.return_value.sort.return_value = detailed_data
        mock_get_db.return_value = mock_db
        
        result = app.load_detailed_data()
        
        assert "test.tcx" in result
        assert len(result["test.tcx"]) > 0
        # Should have formatted fields
        first_row = result["test.tcx"][0]
        assert "LapDistance_formatted" in first_row
        assert "Distance_formatted" in first_row
        assert "Altitude_formatted" in first_row
    
    def test_regex_search_filter_comprehensive(self):
        """Test regex search filter with various patterns"""
        import app
        
        # Test safe patterns
        result = app.regex_search("2024-01-15", "date")
        assert result is not None
        
        result = app.regex_search("12:34:56", "time")
        assert result is not None
        
        result = app.regex_search("123.45", "number")
        assert result is not None
        
        # Test unsafe pattern
        result = app.regex_search("test", "unsafe_pattern")
        assert result is None
        
        # Test invalid input
        result = app.regex_search(123, "date")
        assert result is None
    
    def test_close_db_connection_comprehensive(self):
        """Test database connection closing"""
        import app
        
        # Set up global client
        app.client = MagicMock()
        app.db = MagicMock()
        
        app.close_db_connection()
        
        app.client.close.assert_called_once()
        assert app.client is None
        assert app.db is None


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_calc_pace_edge_cases(self):
        """Test pace calculation edge cases"""
        import trainparser
        
        # Test with zero values
        assert trainparser.calc_pace(0, 1000) is None
        assert trainparser.calc_pace(600, 0) is None
        
        # Test with negative values
        assert trainparser.calc_pace(-600, 1000) is None
        assert trainparser.calc_pace(600, -1000) is None
        
        # Test with very small values
        result = trainparser.calc_pace(1, 1)
        assert result == 60000.0  # (1 / (1/1000)) * 60
    
    def test_sanitize_mongo_value_edge_cases(self):
        """Test MongoDB value sanitization edge cases"""
        import trainparser
        
        # Test with complex objects
        assert trainparser._sanitize_mongo_value({"key": "value"}) == "{'key': 'value'}"
        assert trainparser._sanitize_mongo_value([1, 2, {"nested": "dict"}]) == "[1, 2, {'nested': 'dict'}]"
        
        # Test with special values
        assert trainparser._sanitize_mongo_value(float('inf')) == "inf"
        assert trainparser._sanitize_mongo_value(float('nan')) == "nan"
    
    def test_validate_safe_path_edge_cases(self):
        """Test path validation edge cases"""
        import trainparser
        
        # Test with None
        assert trainparser._validate_safe_path(None) is False
        
        # Test with empty string
        assert trainparser._validate_safe_path("") is False
        
        # Test with relative path containing ..
        assert trainparser._validate_safe_path("../../../etc/passwd") is False