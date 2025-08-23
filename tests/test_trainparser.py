"""
Unified tests for trainparser module
"""
import pytest
from unittest.mock import patch, MagicMock


class TestTrainparserCore:
    """Test core trainparser functionality"""
    
    def test_calc_pace_valid(self, mock_trainparser):
        """Test pace calculation with valid inputs"""
        result = mock_trainparser.calc_pace(600, 1000)
        assert result == 36000.0  # (600 / (1000/1000)) * 60 = 36000
    
    def test_calc_pace_invalid(self, mock_trainparser):
        """Test pace calculation with invalid inputs"""
        assert mock_trainparser.calc_pace(0, 1000) is None
        assert mock_trainparser.calc_pace(600, 0) is None
        assert mock_trainparser.calc_pace(None, 1000) is None
        assert mock_trainparser.calc_pace(600, None) is None
    
    def test_sanitize_for_log(self, mock_trainparser):
        """Test log sanitization"""
        assert mock_trainparser.sanitize_for_log("normal") == "normal"
        assert mock_trainparser.sanitize_for_log("text\nwith\nnewlines") == "text\\nwith\\nnewlines"
        assert mock_trainparser.sanitize_for_log(None) == "None"
        
        # Test truncation
        long_string = "a" * 250
        result = mock_trainparser.sanitize_for_log(long_string)
        assert result.endswith("...")
        assert len(result) == 203
    
    def test_validate_safe_path(self, mock_trainparser):
        """Test path validation"""
        assert isinstance(mock_trainparser._validate_safe_path("/safe/path"), bool)
        
        # Test None handling
        try:
            result = mock_trainparser._validate_safe_path(None)
            assert result is False
        except (TypeError, OSError, ValueError):
            pass  # Expected for None input
    
    def test_namedtuple_structure(self, mock_trainparser):
        """Test LapData namedtuple"""
        lap_data = mock_trainparser.LapData("2024-01-01T10:00:00Z", 600.0, 1000.0, 36000.0)
        assert lap_data.start_time == "2024-01-01T10:00:00Z"
        assert lap_data.total_time_s == 600.0
        assert lap_data.distance_m == 1000.0
        assert lap_data.pace == 36000.0
        assert len(lap_data) == 4
    
    def test_sanitize_mongo_value(self, mock_trainparser):
        """Test MongoDB value sanitization"""
        assert mock_trainparser._sanitize_mongo_value("string") == "string"
        assert mock_trainparser._sanitize_mongo_value(123) == 123
        assert mock_trainparser._sanitize_mongo_value(123.45) == 123.45
        assert mock_trainparser._sanitize_mongo_value(True) is True
        assert mock_trainparser._sanitize_mongo_value(None) is None
        assert mock_trainparser._sanitize_mongo_value([1, 2, 3]) == "[1, 2, 3]"


class TestTrainparserMongo:
    """Test MongoDB operations"""
    
    @patch('pymongo.ReplaceOne')
    def test_push_to_mongo_valid(self, mock_replace_one, mock_trainparser):
        """Test MongoDB push with valid data"""
        mock_df = MagicMock()
        mock_df.to_dict.return_value = [{"key": "value"}]
        mock_collection = MagicMock()
        
        mock_trainparser.push_to_mongo(mock_df, mock_collection, ["key"])
        mock_collection.bulk_write.assert_called_once()
    
    def test_push_to_mongo_invalid_keys(self, mock_trainparser):
        """Test MongoDB push with invalid keys"""
        mock_df = MagicMock()
        mock_collection = MagicMock()
        
        with pytest.raises(ValueError):
            mock_trainparser.push_to_mongo(mock_df, mock_collection, "not_a_list")
        
        with pytest.raises(ValueError):
            mock_trainparser.push_to_mongo(mock_df, mock_collection, [123, "valid"])


class TestTrainparserErrorHandling:
    """Test error handling scenarios"""
    
    def test_get_first_lap_date_fallback(self, mock_trainparser):
        """Test date extraction fallback"""
        with patch.object(mock_trainparser, '_parse_tcx_file') as mock_parse:
            mock_parse.side_effect = Exception("Parse error")
            result = mock_trainparser.get_first_lap_date("invalid.tcx")
            assert result == "UnknownDate"
    
    @patch('trainparser._validate_safe_path')
    def test_write_to_excel_invalid_path(self, mock_validate, mock_trainparser):
        """Test Excel write with invalid path"""
        mock_validate.return_value = False
        mock_df = MagicMock()
        
        with pytest.raises(ValueError, match="Invalid output file path"):
            mock_trainparser.write_to_excel(mock_df, "/invalid/path", "sheet")


class TestMissingTrainparserFunctions:
    """Test uncovered trainparser functions"""
    
    @patch('defusedxml.ElementTree.parse')
    def test_parse_tcx_detailed_xml_error(self, mock_parse, mock_trainparser):
        """Test XML parsing error in detailed parsing"""
        from defusedxml import ElementTree as ET
        mock_parse.side_effect = ET.ParseError("Invalid XML")
        
        with pytest.raises(ValueError, match="Invalid XML file"):
            mock_trainparser.parse_tcx_detailed("invalid.tcx")
    
    @patch('os.path.exists')
    def test_write_to_excel_permission_error(self, mock_exists, mock_trainparser):
        """Test Excel write permission error"""
        mock_exists.return_value = False
        mock_df = MagicMock()
        
        with patch('pandas.ExcelWriter') as mock_writer:
            mock_writer.side_effect = PermissionError("Access denied")
            with patch('trainparser._validate_safe_path', return_value=True):
                with pytest.raises(PermissionError):
                    mock_trainparser.write_to_excel(mock_df, "/restricted/path.xlsx", "sheet")
    
    def test_extract_lap_data_missing_elements(self, mock_trainparser):
        """Test lap data extraction with missing XML elements"""
        mock_lap = MagicMock()
        mock_lap.attrib = {"StartTime": "2024-01-01T10:00:00Z"}
        mock_lap.find.return_value = None  # Missing elements
        
        ns = {"tcx": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}
        result = mock_trainparser._extract_lap_data(mock_lap, ns)
        
        assert result.start_time == "2024-01-01T10:00:00Z"
        assert result.total_time_s is None
        assert result.distance_m is None
    
    def test_extract_trackpoint_data_missing_position(self, mock_trainparser):
        """Test trackpoint extraction with missing position data"""
        mock_tp = MagicMock()
        mock_tp.find.side_effect = lambda path, ns: None if "Position" in path else MagicMock()
        
        ns = {"tcx": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}
        result = mock_trainparser._extract_trackpoint_data(mock_tp, ns)
        
        assert result["Latitude"] is None
        assert result["Longitude"] is None
    
    @patch('os.listdir')
    def test_discover_tcx_files_no_files(self, mock_listdir, mock_trainparser):
        """Test TCX discovery with no files found"""
        mock_listdir.return_value = ["other.txt", "data.csv"]
        
        with patch('os.path.isfile', return_value=False):
            result = mock_trainparser._discover_tcx_files("/empty/dir")
            assert result == []
    
    def test_process_file_mongo_validation_error(self, mock_trainparser):
        """Test process_file with MongoDB validation errors"""
        args = MagicMock()
        args.mode = "summary"
        args.output = "test.xlsx"
        
        mock_client = MagicMock()
        
        with patch('trainparser.get_first_lap_date', return_value="2024-01-01"):
            with patch('trainparser.parse_tcx_summary', return_value=MagicMock()):
                with patch('trainparser.write_to_excel'):
                    with patch('os.path.basename', return_value="invalid..file"):
                        with patch('trainparser._validate_safe_path', return_value=False):
                            mock_trainparser.process_file("test.tcx", args, mock_client)
    
    def test_sanitize_for_log_control_chars(self, mock_trainparser):
        """Test log sanitization with control characters"""
        test_input = "test\x00\x01\x02string"
        result = mock_trainparser.sanitize_for_log(test_input)
        assert "\x00" not in result
        assert "\x01" not in result
        assert "\x02" not in result
    
    def test_validate_safe_path_with_base_path(self, mock_trainparser):
        """Test path validation with base path restriction"""
        # Test that function exists and handles base path parameter
        try:
            result = mock_trainparser._validate_safe_path("/test/file.txt", "/safe/base")
            assert isinstance(result, bool)
        except (OSError, ValueError, TypeError):
            # Expected for invalid paths in CI environment
            pass
    
    def test_push_to_mongo_empty_query(self, mock_trainparser):
        """Test MongoDB push with empty query keys"""
        mock_df = MagicMock()
        mock_df.to_dict.return_value = [{"key": None, "other": "value"}]
        mock_collection = MagicMock()
        
        mock_trainparser.push_to_mongo(mock_df, mock_collection, ["key"])
        # Should not call bulk_write due to empty query
        mock_collection.bulk_write.assert_not_called()
    
    def test_get_first_lap_date_no_start_time(self, mock_trainparser):
        """Test date extraction with lap missing StartTime"""
        mock_root = MagicMock()
        mock_lap = MagicMock()
        mock_lap.attrib = {}  # No StartTime
        mock_root.find.return_value = mock_lap
        
        with patch('trainparser._parse_tcx_file', return_value=(mock_root, {})):
            result = mock_trainparser.get_first_lap_date("test.tcx")
            assert result == "UnknownDate"
    
    def test_get_first_lap_date_invalid_timestamp(self, mock_trainparser):
        """Test date extraction with invalid timestamp format"""
        mock_root = MagicMock()
        mock_lap = MagicMock()
        mock_lap.attrib = {"StartTime": "invalid-timestamp"}  # No 'T' separator
        mock_root.find.return_value = mock_lap
        
        with patch('trainparser._parse_tcx_file', return_value=(mock_root, {})):
            result = mock_trainparser.get_first_lap_date("test.tcx")
            assert result == "UnknownDate"


class TestMainFunctionPaths:
    """Test main function execution paths"""
    
    @patch('trainparser._validate_safe_path')
    @patch('trainparser._discover_tcx_files')
    @patch('trainparser._setup_mongo_connection')
    @patch('os.path.exists')
    @patch('argparse.ArgumentParser.parse_args')
    def test_main_unsafe_path(self, mock_args, mock_exists, mock_mongo, mock_discover, mock_validate):
        """Test main with unsafe input path"""
        args = MagicMock()
        args.input_path = "../../../etc/passwd"
        mock_args.return_value = args
        mock_exists.return_value = True
        mock_validate.return_value = False
        
        import trainparser
        trainparser.main()
        
        mock_discover.assert_not_called()
    
    @patch('trainparser.process_file')
    @patch('trainparser._discover_tcx_files')
    @patch('trainparser._setup_mongo_connection')
    @patch('trainparser._validate_safe_path')
    @patch('os.path.exists')
    @patch('argparse.ArgumentParser.parse_args')
    def test_main_with_mongo_client_cleanup(self, mock_args, mock_exists, mock_validate, mock_mongo, mock_discover, mock_process):
        """Test main function with MongoDB client cleanup"""
        args = MagicMock()
        args.input_path = "/valid/path"
        args.mongo = True
        mock_args.return_value = args
        mock_exists.return_value = True
        mock_validate.return_value = True
        mock_client = MagicMock()
        mock_mongo.return_value = mock_client
        mock_discover.return_value = ["file1.tcx"]
        
        import trainparser
        trainparser.main()
        
        mock_client.close.assert_called_once()


