import requests
import logging
from typing import List, Dict, Optional
from .config import config

logger = logging.getLogger(__name__)

class RealDebridAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = config.rd_base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'User-Agent': 'RealDB-Media/1.0'
        })
    
    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            response = self.session.get(f'{self.base_url}/user')
            response.raise_for_status()
            logger.info("Real Debrid API connection successful")
            return True
        except requests.RequestException as e:
            logger.error(f"Real Debrid API connection failed: {e}")
            return False
    
    def get_user_info(self) -> Optional[Dict]:
        """Get user information"""
        try:
            response = self.session.get(f'{self.base_url}/user')
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get user info: {e}")
            return None
    
    def get_downloads(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get list of downloads"""
        try:
            params = {'limit': limit, 'offset': offset}
            response = self.session.get(f'{self.base_url}/downloads', params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get downloads: {e}")
            return []
    
    def get_download_info(self, download_id: str) -> Optional[Dict]:
        """Get detailed download information"""
        try:
            response = self.session.get(f'{self.base_url}/downloads/{download_id}')
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get download info for {download_id}: {e}")
            return None
    
    def get_torrents(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get list of torrents"""
        try:
            params = {'limit': limit, 'offset': offset}
            response = self.session.get(f'{self.base_url}/torrents', params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get torrents: {e}")
            return []
    
    def get_torrent_info(self, torrent_id: str) -> Optional[Dict]:
        """Get detailed torrent information"""
        try:
            response = self.session.get(f'{self.base_url}/torrents/info/{torrent_id}')
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get torrent info for {torrent_id}: {e}")
            return None
    
    def unrestrict_link(self, link: str) -> Optional[str]:
        """Unrestrict a link to get direct download URL"""
        try:
            data = {'link': link}
            response = self.session.post(f'{self.base_url}/unrestrict/link', data=data)
            response.raise_for_status()
            result = response.json()
            return result.get('download')
        except requests.RequestException as e:
            logger.error(f"Failed to unrestrict link {link}: {e}")
            return None
    
    def get_streaming_transcode(self, download_id: str) -> Optional[Dict]:
        """Get streaming/transcode info for a download"""
        try:
            response = self.session.get(f'{self.base_url}/streaming/transcode/{download_id}')
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get streaming info for {download_id}: {e}")
            return None 