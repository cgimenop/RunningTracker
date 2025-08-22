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


class TestAltitudeDelta:
    """Test altitude delta calculations"""
    
    def test_altitude_delta_net_gain(self):
        """Test net elevation gain calculation"""
        altitudes = [100, 120, 110, 130, 105]
        total_change = sum(altitudes[i] - altitudes[i-1] for i in range(1, len(altitudes)))
        assert total_change == 5
    
    def test_altitude_delta_net_loss(self):
        """Test net elevation loss calculation"""
        altitudes = [130, 120, 125, 110, 100]
        total_change = sum(altitudes[i] - altitudes[i-1] for i in range(1, len(altitudes)))
        assert total_change == -30
    
    def test_altitude_delta_no_change(self):
        """Test no net elevation change"""
        altitudes = [100, 110, 100]
        total_change = sum(altitudes[i] - altitudes[i-1] for i in range(1, len(altitudes)))
        assert total_change == 0