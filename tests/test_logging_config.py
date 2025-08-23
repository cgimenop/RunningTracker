"""
Tests for webapp logging configuration
"""
import pytest
from unittest.mock import patch, MagicMock
import logging


class TestWebappLoggingConfig:
    """Test webapp logging configuration"""
    
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_get_webapp_logging_config_development(self, mock_exists, mock_makedirs):
        """Test webapp logging config in development mode"""
        mock_exists.return_value = False
        
        from webapp.logging_config import get_webapp_logging_config
        config = get_webapp_logging_config('development')
        
        assert config['version'] == 1
        assert 'handlers' in config
        assert 'loggers' in config
        mock_makedirs.assert_called_once_with('logs')
    
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_get_webapp_logging_config_production(self, mock_exists, mock_makedirs):
        """Test webapp logging config in production mode"""
        mock_exists.return_value = True
        
        from webapp.logging_config import get_webapp_logging_config
        config = get_webapp_logging_config('production')
        
        assert config['version'] == 1
        assert 'handlers' in config
        assert 'loggers' in config
        mock_makedirs.assert_not_called()
    
    @patch('logging.config.dictConfig')
    @patch('logging.getLogger')
    @patch('os.path.exists')
    def test_setup_webapp_logging_with_env(self, mock_exists, mock_get_logger, mock_dict_config):
        """Test webapp logging setup with environment"""
        mock_exists.return_value = True
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        from webapp.logging_config import setup_webapp_logging
        logger = setup_webapp_logging('development')
        
        assert logger == mock_logger
        mock_dict_config.assert_called_once()
        mock_logger.info.assert_called_once()
    
    def test_logging_levels(self):
        """Test logging level constants"""
        assert logging.DEBUG == 10
        assert logging.INFO == 20
        assert logging.WARNING == 30
        assert logging.ERROR == 40
    
    @patch('os.path.exists')
    def test_logging_config_structure(self, mock_exists):
        """Test logging configuration structure"""
        mock_exists.return_value = True
        
        from webapp.logging_config import get_webapp_logging_config
        config = get_webapp_logging_config()
        
        # Test required keys
        assert 'version' in config
        assert 'handlers' in config
        assert 'loggers' in config
        assert 'formatters' in config
        
        # Test handlers
        assert 'file' in config['handlers']
        assert 'console' in config['handlers']
        
        # Test formatters
        assert 'detailed' in config['formatters']
        assert 'simple' in config['formatters']