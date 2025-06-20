import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional
from .config import config

logger = logging.getLogger(__name__)

class STRMManager:
    def __init__(self, media_path: Path = None):
        self.media_path = Path(media_path) if media_path else config.media_path
        self.categories = config.categories
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem"""
        # Remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Replace multiple spaces with single space
        filename = re.sub(r'\s+', ' ', filename)
        # Remove leading/trailing spaces and dots
        filename = filename.strip('. ')
        return filename
    
    def detect_category(self, filename: str) -> str:
        """Detect media category based on filename"""
        filename_lower = filename.lower()
        
        # TV Show patterns
        tv_patterns = [
            r's\d+e\d+',  # S01E01
            r'season\s*\d+',  # Season 1
            r'\d+x\d+',  # 1x01
        ]
        
        for pattern in tv_patterns:
            if re.search(pattern, filename_lower):
                return 'tv'
        
        # Movie patterns (default to movies if not TV)
        movie_extensions = self.categories.get('movies', [])
        file_ext = Path(filename).suffix.lower().lstrip('.')
        
        if file_ext in movie_extensions:
            return 'movies'
        
        return 'other'
    
    def parse_tv_info(self, filename: str) -> Dict[str, str]:
        """Parse TV show information from filename"""
        info = {
            'show_name': '',
            'season': '',
            'episode': '',
            'episode_title': ''
        }
        
        filename_clean = Path(filename).stem
        
        # Real Debrid format: "Show Name (Year) - S01E01 - Episode Title (Quality)"
        rd_pattern = re.search(r'^(.+?)\s*(?:\(\d{4}\))?\s*-\s*S(\d+)E(\d+)\s*-\s*(.+?)\s*\(.*?\)$', filename_clean, re.IGNORECASE)
        if rd_pattern:
            info['show_name'] = rd_pattern.group(1).strip()
            info['season'] = rd_pattern.group(2).zfill(2)
            info['episode'] = rd_pattern.group(3).zfill(2)
            info['episode_title'] = rd_pattern.group(4).strip()
            return info
        
        # Extract season and episode - Standard pattern: S01E01 or s01e01
        se_match = re.search(r'S(\d+)E(\d+)', filename_clean, re.IGNORECASE)
        if se_match:
            info['season'] = se_match.group(1).zfill(2)
            info['episode'] = se_match.group(2).zfill(2)
            
            # Extract show name (everything before SxxExx)
            show_part = filename_clean[:se_match.start()].strip(' .-_')
            
            # Clean up show name - remove year if present
            year_pattern = r'\s*\(\d{4}\)\s*'
            show_part = re.sub(year_pattern, ' ', show_part)
            info['show_name'] = re.sub(r'[._-]', ' ', show_part).strip()
            
            # Extract episode title (everything after SxxExx)
            episode_part = filename_clean[se_match.end():].strip(' .-_')
            if episode_part:
                # Remove quality info in parentheses
                episode_part = re.sub(r'\s*\([^)]*\)\s*', ' ', episode_part)
                # Clean up separators
                episode_part = re.sub(r'^[-.\s]+', '', episode_part)
                episode_part = re.sub(r'[-.\s]+$', '', episode_part)
                info['episode_title'] = re.sub(r'[._-]', ' ', episode_part).strip()
        
        # Pattern: 1x01 (fallback)
        x_match = re.search(r'(\d+)x(\d+)', filename_clean, re.IGNORECASE)
        if x_match and not se_match:
            info['season'] = x_match.group(1).zfill(2)
            info['episode'] = x_match.group(2).zfill(2)
            
            show_part = filename_clean[:x_match.start()].strip(' .-_')
            # Remove year if present
            year_pattern = r'\s*\(\d{4}\)\s*'
            show_part = re.sub(year_pattern, ' ', show_part)
            info['show_name'] = re.sub(r'[._-]', ' ', show_part).strip()
        
        return info
    
    def create_strm_file(self, url: str, filename: str, category: str = None) -> Optional[Path]:
        """Create STRM file for media"""
        try:
            if not category:
                category = self.detect_category(filename)
            
            category_path = self.media_path / category
            category_path.mkdir(parents=True, exist_ok=True)
            
            # Clean filename
            clean_name = self.sanitize_filename(filename)
            strm_filename = Path(clean_name).with_suffix('.strm')
            
            # For TV shows, create show/season directory structure
            if category == 'tv':
                tv_info = self.parse_tv_info(filename)
                if tv_info['show_name'] and tv_info['season']:
                    show_dir = category_path / self.sanitize_filename(tv_info['show_name'])
                    season_dir = show_dir / f"Season {int(tv_info['season'])}"
                    season_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Create episode filename
                    episode_name = f"S{tv_info['season']}E{tv_info['episode']}"
                    if tv_info['episode_title']:
                        episode_name += f" - {tv_info['episode_title']}"
                    
                    strm_path = season_dir / f"{episode_name}.strm"
                else:
                    strm_path = category_path / strm_filename
            else:
                strm_path = category_path / strm_filename
            
            # Write URL to STRM file
            with open(strm_path, 'w', encoding='utf-8') as f:
                f.write(url)
            
            logger.info(f"Created STRM file: {strm_path}")
            return strm_path
            
        except Exception as e:
            logger.error(f"Failed to create STRM file for {filename}: {e}")
            return None
    
    def create_strm_file_in_folder(self, url: str, filename: str, folder_name: str) -> Optional[Path]:
        """Create a STRM file in a specific torrent folder"""
        
        try:
            # Sanitize filename for filesystem
            safe_filename = self.sanitize_filename(filename)
            
            # Remove extension and add .strm
            name_without_ext = Path(safe_filename).stem
            strm_filename = f"{name_without_ext}.strm"
            
            # Create folder path 
            folder_path = self.media_path / folder_name
            folder_path.mkdir(parents=True, exist_ok=True)
            
            # Create STRM file path
            strm_path = folder_path / strm_filename
            
            # Write URL to STRM file
            with open(strm_path, 'w', encoding='utf-8') as f:
                f.write(url)
            
            logger.info(f"Created STRM file: {strm_path}")
            return strm_path
            
        except Exception as e:
            logger.error(f"Failed to create STRM file in folder {folder_name} for {filename}: {e}")
            return None
    
    def update_strm_file(self, strm_path: Path, new_url: str) -> bool:
        """Update existing STRM file with new URL"""
        try:
            with open(strm_path, 'w', encoding='utf-8') as f:
                f.write(new_url)
            logger.info(f"Updated STRM file: {strm_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to update STRM file {strm_path}: {e}")
            return False
    
    def cleanup_orphaned_strm(self, valid_files: List[str]) -> None:
        """Remove STRM files that no longer have corresponding downloads"""
        try:
            for category_dir in self.media_path.iterdir():
                if category_dir.is_dir():
                    self._cleanup_directory(category_dir, valid_files)
        except Exception as e:
            logger.error(f"Failed to cleanup orphaned STRM files: {e}")
    
    def _cleanup_directory(self, directory: Path, valid_files: List[str]) -> None:
        """Recursively cleanup directory"""
        for item in directory.iterdir():
            if item.is_dir():
                self._cleanup_directory(item, valid_files)
                # Remove empty directories
                try:
                    if not any(item.iterdir()):
                        item.rmdir()
                        logger.info(f"Removed empty directory: {item}")
                except OSError:
                    pass
            elif item.suffix == '.strm':
                # Check if this STRM file is still valid
                stem_name = item.stem
                if not any(stem_name in valid_file for valid_file in valid_files):
                    item.unlink()
                    logger.info(f"Removed orphaned STRM file: {item}")
    
    def get_existing_strm_files(self) -> Dict[str, Path]:
        """Get mapping of filename to STRM file path"""
        strm_files = {}
        try:
            for category_dir in self.media_path.iterdir():
                if category_dir.is_dir():
                    self._collect_strm_files(category_dir, strm_files)
        except Exception as e:
            logger.error(f"Failed to collect existing STRM files: {e}")
        
        return strm_files
    
    def _collect_strm_files(self, directory: Path, strm_files: Dict[str, Path]) -> None:
        """Recursively collect STRM files"""
        for item in directory.iterdir():
            if item.is_dir():
                self._collect_strm_files(item, strm_files)
            elif item.suffix == '.strm':
                strm_files[item.stem] = item 