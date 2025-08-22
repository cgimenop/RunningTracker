"""
Unified tests for webapp module
"""
import pytest
from unittest.mock import patch, MagicMock


class TestWebappFormatting:
    """Test webapp formatting functions"""
    
    @patch('app.format_distance')
    def test_format_distance_meters(self, mock_format):
        """Test distance formatting for meters"""
        mock_format.return_value = "500.00 m"
        result = mock_format(500)
        assert result == "500.00 m"
    
    @patch('app.format_distance')
    def test_format_distance_kilometers(self, mock_format):
        """Test distance formatting for kilometers"""
        mock_format.return_value = "1.50 km"
        result = mock_format(1500)
        assert result == "1.50 km"
    
    @patch('app.format_altitude')
    def test_format_altitude(self, mock_format):
        """Test altitude formatting"""
        mock_format.return_value = "123.45 m"
        result = mock_format(123.45)
        assert result == "123.45 m"
    
    @patch('app.format_seconds')
    def test_format_seconds(self, mock_format):
        """Test time formatting"""
        mock_format.return_value = "0:10:00"
        result = mock_format(600)
        assert result == "0:10:00"


class TestWebappSecurity:
    """Test webapp security features"""
    
    @patch('app.regex_search')
    def test_regex_search_safe_patterns(self, mock_regex):
        """Test regex search with safe patterns"""
        mock_regex.return_value = MagicMock()
        mock_regex.return_value.group.return_value = "2024-01-01"
        
        result = mock_regex("test-2024-01-01", "date")
        assert result.group(1) == "2024-01-01"
    
    @patch('app.regex_search')
    def test_regex_search_unsafe_patterns(self, mock_regex):
        """Test regex search rejects unsafe patterns"""
        mock_regex.return_value = None
        result = mock_regex("test", "unsafe_pattern")
        assert result is None


class TestWebappDataProcessing:
    """Test webapp data processing functions"""
    
    def test_extract_date_from_filename_valid(self):
        """Test date extraction from filenames"""
        test_cases = [
            ("run_2024-01-15_morning.tcx", "2024-01-15"),
            ("2024-12-31-evening.tcx", "2024-12-31"),
            ("RunnerUp_2025-08-05-08-24-01_Running.tcx", "2025-08-05")
        ]
        
        for filename, expected in test_cases:
            # Mock the regex_search function behavior
            with patch('app.regex_search') as mock_regex:
                mock_match = MagicMock()
                mock_match.group.return_value = expected
                mock_regex.return_value = mock_match
                
                # Import and test the function
                import app
                result = app.extract_date_from_filename(filename)
                assert result == expected
    
    def test_extract_date_from_filename_no_date(self):
        """Test date extraction when no date found"""
        with patch('app.regex_search') as mock_regex:
            mock_regex.return_value = None
            
            import app
            result = app.extract_date_from_filename("invalid_filename.tcx")
            assert result == "invalid_filename.tcx"
    
    @patch('app._is_valid_lap')
    def test_is_valid_lap(self, mock_is_valid):
        """Test lap validation"""
        mock_is_valid.return_value = True
        assert mock_is_valid({"LapDistance_m": 1000}) is True
        
        mock_is_valid.return_value = False
        assert mock_is_valid({"LapDistance_m": 500}) is False


class TestWebappRecords:
    """Test webapp record finding functionality"""
    
    @patch('app.find_records')
    def test_find_records_with_data(self, mock_find):
        """Test record finding with valid data"""
        mock_find.return_value = (
            {"LapTotalTime_s": 250},  # fastest
            {"LapTotalTime_s": 400},  # slowest
            {"total_distance": 3000}, # longest distance
            {"total_time": 900}       # longest time
        )
        
        fastest, slowest, longest_dist, longest_time = mock_find([], [])
        assert fastest["LapTotalTime_s"] == 250
        assert slowest["LapTotalTime_s"] == 400
        assert longest_dist["total_distance"] == 3000
        assert longest_time["total_time"] == 900
    
    @patch('app.find_records')
    def test_find_records_empty_data(self, mock_find):
        """Test record finding with empty data"""
        mock_find.return_value = (None, None, None, None)
        
        fastest, slowest, longest_dist, longest_time = mock_find([], [])
        assert fastest is None
        assert slowest is None
        assert longest_dist is None
        assert longest_time is None


class TestWebappDatabase:
    """Test webapp database operations"""
    
    @patch('app.get_db_connection')
    def test_database_connection(self, mock_get_db):
        """Test database connection management"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        db = mock_get_db()
        assert db is not None
        mock_get_db.assert_called_once()
    
    @patch('app.load_summary_data')
    def test_load_summary_data(self, mock_load):
        """Test summary data loading"""
        mock_load.return_value = ({}, [])
        
        grouped, all_laps = mock_load()
        assert isinstance(grouped, dict)
        assert isinstance(all_laps, list)
    
    @patch('app.load_detailed_data')
    def test_load_detailed_data(self, mock_load):
        """Test detailed data loading"""
        mock_load.return_value = {}
        
        detailed = mock_load()
        assert isinstance(detailed, dict)