import requests
import logging
import time
from typing import List, Dict, Optional
from .config import config

logger = logging.getLogger(__name__)

class RealDebridAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = 'https://api.real-debrid.com/rest/1.0'
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
    
    def get_user_info(self) -> Dict:
        """Get user information"""
        try:
            response = self.session.get(f'{self.base_url}/user')
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get user info: {e}")
            return {}
    
    def get_torrents(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Get list of torrents
        
        Args:
            limit: Number of torrents to return (max 100)
            offset: Offset for pagination
        """
        try:
            params = {
                'offset': offset,
                'limit': min(limit, 100)  # API max is 100
            }
            
            response = self.session.get(f'{self.base_url}/torrents', params=params)
            response.raise_for_status()
            
            torrents = response.json()
            logger.info(f"Retrieved {len(torrents)} torrents")
            return torrents
            
        except requests.RequestException as e:
            logger.error(f"Failed to get torrents: {e}")
            return []
    
    def get_all_torrents(self) -> List[Dict]:
        """Get ALL torrents using pagination"""
        all_torrents = []
        offset = 0
        limit = 100
        
        while True:
            batch = self.get_torrents(limit=limit, offset=offset)
            if not batch:
                break
                
            all_torrents.extend(batch)
            
            if len(batch) < limit:
                # Last page
                break
                
            offset += limit
            time.sleep(0.1)  # Rate limiting
        
        logger.info(f"Retrieved total {len(all_torrents)} torrents")
        return all_torrents
    
    def unrestrict_link(self, link: str) -> Optional[Dict]:
        """
        Unrestrict a Real Debrid link to get direct download URL
        
        Args:
            link: RD link like "https://real-debrid.com/d/XXXXX"
            
        Returns:
            Dict with download info including direct URL and filename
        """
        try:
            data = {'link': link}
            response = self.session.post(f'{self.base_url}/unrestrict/link', data=data)
            response.raise_for_status()
            
            result = response.json()
            logger.debug(f"Unrestricted link: {link} -> {result.get('download', 'N/A')}")
            return result
            
        except requests.RequestException as e:
            logger.error(f"Failed to unrestrict link {link}: {e}")
            return None
    
    def unrestrict_links_batch(self, links: List[str], delay: float = 0.1) -> List[Dict]:
        """
        Unrestrict multiple links with rate limiting
        
        Args:
            links: List of RD links
            delay: Delay between requests (seconds)
        """
        results = []
        
        for i, link in enumerate(links):
            logger.debug(f"Unrestricting link {i+1}/{len(links)}: {link}")
            
            result = self.unrestrict_link(link)
            if result:
                results.append(result)
            
            # Rate limiting
            if i < len(links) - 1:
                time.sleep(delay)
        
        logger.info(f"Successfully unrestricted {len(results)}/{len(links)} links")
        return results
    
    def process_torrent_to_direct_urls(self, torrent: Dict) -> List[Dict]:
        """
        Process a torrent entry to get all direct download URLs
        
        Args:
            torrent: Torrent dict from /torrents API
            
        Returns:
            List of dicts with direct URLs and metadata
        """
        if torrent.get('status') != 'downloaded':
            logger.debug(f"Skipping torrent {torrent.get('id')} - status: {torrent.get('status')}")
            return []
        
        links = torrent.get('links', [])
        if not links:
            logger.debug(f"No links found for torrent {torrent.get('id')}")
            return []
        
        logger.info(f"Processing torrent: {torrent.get('filename')} ({len(links)} files)")
        
        # Unrestrict all links
        direct_urls = self.unrestrict_links_batch(links)
        
        # Add torrent metadata to each result
        for result in direct_urls:
            result['torrent_id'] = torrent.get('id')
            result['torrent_name'] = torrent.get('filename')
            result['torrent_added'] = torrent.get('added')
        
        return direct_urls
    
    def get_all_direct_urls(self) -> List[Dict]:
        """
        Main method: Get ALL direct download URLs from ALL torrents
        
        This is the complete workflow:
        1. Get all torrents
        2. For each downloaded torrent
        3. Unrestrict all links to get direct URLs
        4. Return list of all direct URLs with metadata
        """
        logger.info("🔄 Starting complete Real Debrid processing...")
        
        # Step 1: Get all torrents
        torrents = self.get_all_torrents()
        if not torrents:
            logger.error("No torrents found")
            return []
        
        logger.info(f"📊 Found {len(torrents)} total torrents")
        
        # Filter downloaded torrents
        downloaded_torrents = [t for t in torrents if t.get('status') == 'downloaded']
        logger.info(f"📥 {len(downloaded_torrents)} downloaded torrents")
        
        # Step 2 & 3: Process each torrent to get direct URLs
        all_direct_urls = []
        
        for i, torrent in enumerate(downloaded_torrents):
            logger.info(f"Processing torrent {i+1}/{len(downloaded_torrents)}: {torrent.get('filename')}")
            
            direct_urls = self.process_torrent_to_direct_urls(torrent)
            all_direct_urls.extend(direct_urls)
            
            # Rate limiting between torrents
            if i < len(downloaded_torrents) - 1:
                time.sleep(0.2)
        
        logger.info(f"✅ Complete! Retrieved {len(all_direct_urls)} direct download URLs")
        return all_direct_urls 