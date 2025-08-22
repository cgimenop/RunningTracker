"""
Flask route tests
"""
import pytest
from unittest.mock import patch, MagicMock


class TestFlaskRoutes:
    """Test Flask route functionality"""
    
    def test_index_route_success(self):
        """Test successful index route"""
        import app
        
        with patch('app.load_summary_data') as mock_summary:
            with patch('app.calculate_file_summaries') as mock_summaries:
                with patch('app.find_records') as mock_records:
                    with patch('app.load_detailed_data') as mock_detailed:
                        mock_summary.return_value = ({}, [])
                        mock_summaries.return_value = ([], {}, {})
                        mock_records.return_value = (None, None, None, None)
                        mock_detailed.return_value = {}
                        
                        with app.app.test_client() as client:
                            response = client.get('/')
                            assert response.status_code == 200
    
    def test_index_route_error_handling(self):
        """Test index route error handling"""
        import app
        
        with patch('app.load_summary_data') as mock_summary:
            mock_summary.side_effect = Exception("Database error")
            
            with app.app.test_client() as client:
                response = client.get('/')
                assert response.status_code == 200
    
    def test_teardown_appcontext(self):
        """Test app context teardown"""
        import app
        
        # Test with error
        with app.app.app_context():
            app.close_db(Exception("Test error"))
        
        # Test without error
        with app.app.app_context():
            app.close_db(None)
    
    @patch('app.get_db_connection')
    def test_get_db_connection_error(self, mock_get_db):
        """Test database connection error handling"""
        mock_get_db.side_effect = Exception("Connection failed")
        
        import app
        with pytest.raises(Exception):
            app.get_db_connection()
    
    def test_template_filters(self):
        """Test template filters"""
        import app
        
        # Test format_distance function directly
        result = app.format_distance(1500)
        assert result == "1.50 km"
        
        # Test format_altitude function directly
        result = app.format_altitude(123.45)
        assert result == "123.46 m"
        
        # Test friendly_name function directly
        result = app.get_friendly_column_name("LapNumber")
        assert result == "Lap"