import logging
import logging.config
import os
from datetime import datetime

def get_webapp_logging_config(env='production'):
    """Get webapp logging configuration based on environment"""
    
    # Ensure logs directory exists
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Generate log filename with date
    log_filename = os.path.join(log_dir, f'webapp_{datetime.now().strftime("%Y%m%d")}.log')
    
    # Set log level based on environment
    log_level = 'DEBUG' if env == 'development' else 'WARNING'
    
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            },
            'simple': {
                'format': '%(asctime)s - %(levelname)s - %(message)s'
            }
        },
        'handlers': {
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': log_filename,
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'formatter': 'detailed',
                'level': log_level
            },
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
                'level': 'INFO'
            }
        },
        'loggers': {
            '': {  # root logger
                'handlers': ['file', 'console'],
                'level': log_level,
                'propagate': False
            },
            'werkzeug': {  # Flask's built-in server
                'handlers': ['file'],
                'level': 'WARNING',
                'propagate': False
            }
        }
    }
    
    return config

def setup_webapp_logging(env=None):
    """Setup webapp logging configuration"""
    if env is None:
        env = os.getenv('FLASK_ENV', 'production')
    
    config = get_webapp_logging_config(env)
    logging.config.dictConfig(config)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Webapp logging configured for {env} environment")
    
    return logger