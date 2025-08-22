"""
Integration tests for core functionality
"""
import pytest
from unittest.mock import patch, MagicMock, mock_open
import pandas as pd


class TestTrainparserIntegration:
    """Integration tests for trainparser functionality"""
    
    @patch('trainparser._parse_tcx_file')
    @patch('pandas.DataFrame')
    def test_parse_tcx_file_integration(self, mock_df_class, mock_parse):
        """Test TCX file parsing integration"""
        mock_root = MagicMock()
        mock_ns = {"tcx": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}
        mock_parse.return_value = (mock_root, mock_ns)
        
        # Mock DataFrame creation
        mock_df = MagicMock()
        mock_df_class.return_value = mock_df
        
        import trainparser
        
        # Mock XML structure
        mock_lap = MagicMock()
        mock_lap.attrib = {"StartTime": "2024-01-01T10:00:00Z"}
        mock_root.findall.return_value = [mock_lap]
        
        with patch.object(trainparser, '_extract_lap_data') as mock_extract:
            mock_extract.return_value = trainparser.LapData("2024-01-01T10:00:00Z", 600.0, 1000.0, 36000.0)
            result = trainparser.parse_tcx_summary("test.tcx")
            assert result == mock_df
            mock_df_class.assert_called_once()
    
    @patch('os.path.exists')
    @patch('pandas.ExcelWriter')
    def test_write_excel_integration(self, mock_writer, mock_exists):
        """Test Excel writing integration"""
        mock_exists.return_value = False
        mock_writer_instance = MagicMock()
        mock_writer.return_value.__enter__.return_value = mock_writer_instance
        
        import trainparser
        
        mock_df = MagicMock()
        
        with patch('trainparser._validate_safe_path', return_value=True):
            trainparser.write_to_excel(mock_df, "/valid/path.xlsx", "test_sheet")
            mock_df.to_excel.assert_called_once()
    
    @patch('pymongo.MongoClient')
    def test_mongo_integration(self, mock_client):
        """Test MongoDB integration"""
        mock_client_instance = MagicMock()
        mock_collection = MagicMock()
        mock_client.return_value.__getitem__.return_value.__getitem__.return_value = mock_collection
        
        import trainparser
        
        mock_df = MagicMock()
        mock_df.to_dict.return_value = [{"key": "value", "unique_key": "test"}]
        
        trainparser.push_to_mongo(mock_df, mock_collection, ["unique_key"])
        mock_collection.bulk_write.assert_called_once()


class TestWebappIntegration:
    """Integration tests for webapp functionality"""
    
    @patch('app.get_db_connection')
    def test_data_loading_integration(self, mock_get_db):
        """Test data loading integration"""
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_collection.find.return_value.sort.return_value = [
            {"_source_file": "test.tcx", "LapDistance_m": 1000, "LapTotalTime_s": 300}
        ]
        mock_get_db.return_value = mock_db
        
        import app
        
        grouped, all_laps = app.load_summary_data()
        assert isinstance(grouped, dict)
        assert isinstance(all_laps, list)
    
    @patch('app.get_db_connection')
    def test_detailed_data_integration(self, mock_get_db):
        """Test detailed data loading integration"""
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_collection.find.return_value.sort.return_value = [
            {"_source_file": "test.tcx", "Time": "10:00:00", "Altitude_m": 100}
        ]
        mock_get_db.return_value = mock_db
        
        import app
        
        detailed = app.load_detailed_data()
        assert isinstance(detailed, dict)
    
    def test_formatting_integration(self):
        """Test formatting functions integration"""
        import app
        
        # Test distance formatting
        assert app.format_distance(1500) == "1.50 km"
        assert app.format_distance(500) == "500.00 m"
        
        # Test time formatting
        assert app.format_seconds(3661) == "1:01:01"
        
        # Test altitude formatting
        assert app.format_altitude(123.456) == "123.46 m"


class TestErrorHandlingIntegration:
    """Integration tests for error handling"""
    
    @patch('trainparser._parse_tcx_file')
    def test_parse_error_handling(self, mock_parse):
        """Test parsing error handling"""
        mock_parse.side_effect = Exception("Parse error")
        
        import trainparser
        
        result = trainparser.get_first_lap_date("invalid.tcx")
        assert result == "UnknownDate"
    
    def test_webapp_functions_exist(self):
        """Test webapp functions exist"""
        import app
        
        # Test that error handling functions exist
        assert callable(app.close_db)
        assert hasattr(app, 'app')
        assert callable(app.get_db_connection)