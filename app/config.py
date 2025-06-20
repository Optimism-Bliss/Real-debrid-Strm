import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    def __init__(self):
        self.rd_api_key = os.getenv('REAL_DEBRID_API_KEY')
        self.media_path = Path(os.getenv('MEDIA_PATH', '/media'))
        self.sync_interval = int(os.getenv('SYNC_INTERVAL', '3600'))
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        
        # API endpoints
        self.rd_base_url = 'https://api.real-debrid.com/rest/1.0'
        
        # Media categories
        self.categories = {
            'movies': ['mp4', 'mkv', 'avi', 'mov', 'wmv'],
            'tv': ['mp4', 'mkv', 'avi', 'mov', 'wmv'],
            'other': []
        }
        
        self.validate()
    
    def validate(self):
        """Validate configuration"""
        if not self.rd_api_key:
            raise ValueError("REAL_DEBRID_API_KEY environment variable is required")
        
        # Create unorganized media directory only
        self.media_path.mkdir(parents=True, exist_ok=True)
        (self.media_path / 'unorganized').mkdir(exist_ok=True)
    
    def load_settings(self, config_file='config/settings.yaml'):
        """Load additional settings from YAML file"""
        try:
            with open(config_file, 'r', encoding='utf-8') as file:
                settings = yaml.safe_load(file)
                
            # Update categories if defined in config
            if 'categories' in settings:
                self.categories.update(settings['categories'])
                
            return settings
        except FileNotFoundError:
            return {}

# Global config instance
config = Config()

def load_config():
    """Load configuration and return as dictionary for main.py"""
    return {
        "real_debrid": {
            "api_key": config.rd_api_key
        },
        "paths": {
            "media_dir": str(config.media_path),
            "output_dir": "/app/output",
            "log_dir": "/app/logs"
        },
        "processing": {
            "sync_interval": config.sync_interval
        },
        "logging": {
            "level": config.log_level,
            "file": "/app/logs/realdebrid.log"
        }
    } 