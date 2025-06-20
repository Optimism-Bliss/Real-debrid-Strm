#!/usr/bin/env python3
"""
Real Debrid Processor - New workflow with torrent grouping
Combines the best of old Node.js approach with new grouping logic
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import unquote
import subprocess
import os

from .real_debrid_api_client import RealDebridAPIClient, run_real_debrid_sync
from .strm_manager import STRMManager

logger = logging.getLogger(__name__)

class RealDebridProcessor:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.strm_manager = STRMManager()
        
        # File filtering settings
        self.min_video_size_mb = 300  # Minimum video size to avoid ads/junk
        self.allowed_video_extensions = {'.mkv', '.mp4', '.avi', '.mov', '.wmv', '.m4v', '.webm', '.flv'}
        self.allowed_subtitle_extensions = {'.srt', '.ass', '.vtt', '.sub', '.idx', '.ssa', '.smi'}
        self.allowed_mime_types = {
            'video/x-matroska',
            'video/mp4', 
            'video/x-msvideo',
            'video/quicktime',
            'video/x-ms-wmv',
            'video/webm',
            'video/x-flv',
            'application/x-subrip',  # SRT
            'text/vtt',              # VTT
            'text/plain',            # Generic subtitle
        }
        
    def sanitize_folder_name(self, name: str) -> str:
        """Sanitize folder name, removing extensions for single files"""
        if not name:
            return "Unknown"
        
        # Remove extension if it's a video or subtitle file (for single file torrents)
        name_path = Path(name)
        if name_path.suffix.lower() in (self.allowed_video_extensions | self.allowed_subtitle_extensions):
            # Remove extension for single files
            name = name_path.stem
            logger.debug(f"📂 Removed extension from folder name: {name_path.name} → {name}")
        
        # Remove problematic characters for folder names
        clean_name = re.sub(r'[<>:"/\\|?*]', '_', name)
        clean_name = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', clean_name)  # Remove control chars
        clean_name = re.sub(r'\.+$', '', clean_name)  # Remove trailing dots
        clean_name = clean_name.strip()
        
        return clean_name or "Unknown"
    
    def sanitize_filename(self, name: str) -> str:
        """
        Sanitize filename for STRM files - create clean, readable names
        Removes extension and creates filesystem-safe names
        """
        if not name:
            return "unknown"
        
        # Start with the original name
        clean_name = name
        
        # Decode URL encoding if present
        try:
            # Sometimes filenames are still encoded
            for _ in range(3):
                temp = unquote(clean_name)
                if temp == clean_name:
                    break
                clean_name = temp
        except:
            pass
        
        # Remove file extension first
        clean_name = re.sub(r'\.[^.]+$', '', clean_name)
        
        # Handle common patterns to make cleaner names
        # Remove common prefixes/suffixes
        clean_name = re.sub(r'^(hhd\d+\.com@|hdd\d+\.com@)', '', clean_name)  # Remove site prefixes
        clean_name = re.sub(r'(\.mp4|\.mkv|\.avi)$', '', clean_name, flags=re.IGNORECASE)  # Remove any remaining extensions
        
        # Replace URL encoding artifacts
        clean_name = re.sub(r'%[0-9A-Fa-f]{2}', ' ', clean_name)  # Replace any remaining % encoding
        
        # Clean up brackets and special chars but preserve important ones
        clean_name = re.sub(r'[<>:"/\\|?*]', '_', clean_name)  # Replace truly problematic chars
        clean_name = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', clean_name)  # Remove control characters
        
        # Normalize spaces and separators
        clean_name = re.sub(r'[._-]+', ' ', clean_name)  # Replace dots, dashes, underscores with spaces
        clean_name = re.sub(r'\s+', ' ', clean_name)  # Collapse multiple spaces
        clean_name = clean_name.strip()
        
        # Remove trailing dots (Windows compatibility)
        clean_name = re.sub(r'\.+$', '', clean_name)
        
        # Intelligent truncation - keep important parts
        if len(clean_name) > 100:  # Shorter limit for readability
            # Try to break at word boundaries
            words = clean_name.split()
            truncated = ""
            for word in words:
                if len(truncated + " " + word) <= 95:
                    truncated += (" " + word) if truncated else word
                else:
                    break
            
            if truncated:
                clean_name = truncated
            else:
                # Fallback: just cut at character limit
                clean_name = clean_name[:95]
        
        # Final cleanup
        clean_name = clean_name.strip()
        
        # Ensure we have something valid
        if not clean_name or len(clean_name) < 3:
            # Try to extract something meaningful from the original
            fallback = re.sub(r'[^\w\s-]', '', name)[:50]
            if fallback.strip():
                clean_name = fallback.strip()
            else:
                clean_name = "media_file"
        
        return clean_name
    
    def extract_filename_from_url(self, url: str) -> str:
        """Extract and decode filename from direct download URL"""
        if not url:
            return "unknown"
        
        try:
            # URLs format: https://sgp1.download.real-debrid.com/d/LINKID/filename.ext
            if "/d/" in url:
                parts = url.split("/")
                if len(parts) > 0:
                    # Get last part (encoded filename)
                    encoded_filename = parts[-1]
                    if encoded_filename and encoded_filename != parts[-2]:  # Not just the link ID
                        # Decode URL encoding multiple times if needed
                        decoded_filename = encoded_filename
                        # Sometimes URLs are double/triple encoded
                        for _ in range(3):
                            try:
                                temp = unquote(decoded_filename)
                                if temp == decoded_filename:
                                    break  # No more decoding needed
                                decoded_filename = temp
                            except:
                                break
                        
                        # Clean up common URL artifacts
                        decoded_filename = decoded_filename.split('?')[0]  # Remove query params
                        decoded_filename = decoded_filename.split('#')[0]  # Remove fragments
                        
                        return decoded_filename
            
            return "unknown"
        except Exception as e:
            logger.debug(f"Failed to extract filename from {url}: {e}")
            return "unknown"
    
    def process_from_api(self, output_dir: Path, media_dir: Path, skip_existing: bool = False, existing_urls: set = None, cycle_mode: bool = False) -> Dict:
        """
        Process via Real Debrid API with optional skip existing files logic
        
        Args:
            output_dir: Directory to save API data
            media_dir: Directory to create STRM files  
            skip_existing: Whether to skip URLs that already have STRM files
            existing_urls: Set of URLs to skip (used with skip_existing)
            cycle_mode: Whether running in cycle mode (affects logging)
        """
        if cycle_mode:
            logger.info("🔄 Running API processing in cycle mode")
        else:
            logger.info("📡 Running API processing in standalone mode")
        
        if not self.api_key:
            return {"success": False, "error": "No API key provided"}
        
        try:
            # Step 1: Load or fetch API data
            torrents_file = output_dir / "realdebrid_torrents.json"
            unrestricted_file = output_dir / "realdebrid_unrestricted.json"
            
            # Use existing data if available and not in cycle mode
            if not cycle_mode and torrents_file.exists() and unrestricted_file.exists():
                logger.info("📁 Using existing API data files")
                with open(torrents_file, 'r', encoding='utf-8') as f:
                    torrents = json.load(f)
                with open(unrestricted_file, 'r', encoding='utf-8') as f:
                    unrestricted_data = json.load(f)
                
                result = {"success": True, "source": "existing_files"}
            else:
                # Fetch fresh data from API
                from .real_debrid_api_client import run_real_debrid_sync
                logger.info("📡 Fetching fresh data from Real Debrid API")
                result = run_real_debrid_sync(self.api_key, output_dir)
                
                if not result.get("success"):
                    return result
                
                # Load the fresh data
                with open(torrents_file, 'r', encoding='utf-8') as f:
                    torrents = json.load(f)
                with open(unrestricted_file, 'r', encoding='utf-8') as f:
                    unrestricted_data = json.load(f)
            
            # Step 2: Create torrent grouping with skip logic
            logger.info("📂 Creating torrent grouping...")
            torrent_groups = self._create_torrent_groups_with_skip(
                torrents, 
                unrestricted_data, 
                skip_existing=skip_existing,
                existing_urls=existing_urls or set()
            )
            
            # Step 3: Create STRM files
            logger.info("📄 Creating STRM files...")
            strm_results = self._create_grouped_strm_files(torrent_groups, media_dir)
            
            # Step 4: Generate summary
            summary = {
                "success": True,
                "source": result.get("source", "api"),
                "cycle_mode": cycle_mode,
                "torrents_processed": len(torrent_groups),
                "total_files": sum(len(group['files']) for group in torrent_groups.values()),
                "strm_files_created": strm_results['created'],
                "strm_files_skipped": strm_results['skipped'],
                "folders_created": len([g for g in torrent_groups.values() if g['files']]),
                "api_data": result,
                "skip_stats": {
                    "skip_existing_enabled": skip_existing,
                    "existing_urls_provided": len(existing_urls) if existing_urls else 0
                }
            }
            
            if cycle_mode:
                logger.info(f"🔄 Cycle completed: {summary['strm_files_created']} files, {summary['folders_created']} folders")
            else:
                logger.info(f"✅ Processing completed: {summary['strm_files_created']} files, {summary['folders_created']} folders")
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error in API processing: {e}")
            return {"success": False, "error": str(e)}
    
    def _create_torrent_groups_with_skip(self, torrents: List[Dict], unrestricted_data: List[Dict], skip_existing: bool = False, existing_urls: set = None) -> Dict:
        """Create groups of files by torrent ID with skip existing logic"""
        
        existing_urls = existing_urls or set()
        
        # Create lookup maps
        torrent_map = {t['id']: t for t in torrents if t.get('status') == 'downloaded'}
        link_to_unrestricted = {r['link']: r.get('result', {}) for r in unrestricted_data if 'result' in r}
        
        groups = {}
        filtering_stats = {
            "total_files": 0,
            "processed_files": 0,
            "skipped_existing": 0,
            "filtered_out": {
                "video_small": 0,
                "other_types": 0,
                "no_filename": 0
            }
        }
        
        for torrent_id, torrent in torrent_map.items():
            torrent_name = torrent.get('filename', f"torrent_{torrent_id}")
            folder_name = self.sanitize_folder_name(torrent_name)
            
            files = []
            for link in torrent.get('links', []):
                if link in link_to_unrestricted:
                    unrestricted = link_to_unrestricted[link]
                    if unrestricted.get('download') and unrestricted.get('filename'):
                        filtering_stats["total_files"] += 1
                        
                        download_url = unrestricted['download']
                        
                        # Skip existing files if enabled
                        if skip_existing and download_url in existing_urls:
                            filtering_stats["skipped_existing"] += 1
                            logger.debug(f"⏭️  Skipping existing: {unrestricted['filename']}")
                            continue
                        
                        # Apply filtering
                        filename = unrestricted['filename']
                        filesize = unrestricted.get('filesize', 0)
                        mime_type = unrestricted.get('mimeType', '')
                        
                        filter_result = self.should_process_file(filename, filesize, mime_type)
                        
                        if filter_result["should_process"]:
                            files.append({
                                'original_link': link,
                                'download_url': download_url,
                                'filename': filename,
                                'filesize': filesize,
                                'mime_type': mime_type,
                                'category': filter_result["category"],
                                'sanitized_name': self.sanitize_filename(filename)
                            })
                            filtering_stats["processed_files"] += 1
                            logger.debug(f"✅ Processing: {filename} - {filter_result['reason']}")
                        else:
                            # Track filtering reasons
                            if filter_result["category"] == "video_small":
                                filtering_stats["filtered_out"]["video_small"] += 1
                            elif filter_result["category"] == "other":
                                filtering_stats["filtered_out"]["other_types"] += 1
                            else:
                                filtering_stats["filtered_out"]["no_filename"] += 1
                            
                            logger.debug(f"⏭️  Skipping: {filename} - {filter_result['reason']}")
            
            if files:  # Only include torrents with valid files
                groups[torrent_id] = {
                    'torrent_name': torrent_name,
                    'folder_name': folder_name,
                    'files': files
                }
                logger.info(f"📦 {folder_name}: {len(files)} valid files")
        
        # Log filtering statistics
        logger.info(f"🔍 Filtering Results:")
        logger.info(f"   📂 Total files found: {filtering_stats['total_files']}")
        logger.info(f"   ✅ Files processed: {filtering_stats['processed_files']}")
        if skip_existing and filtering_stats['skipped_existing'] > 0:
            logger.info(f"   ⏭️  Skipped existing: {filtering_stats['skipped_existing']}")
        logger.info(f"   🚫 Filtered out:")
        logger.info(f"      📼 Small videos (<300MB): {filtering_stats['filtered_out']['video_small']}")
        logger.info(f"      📄 Other file types: {filtering_stats['filtered_out']['other_types']}")
        logger.info(f"      ❓ No filename: {filtering_stats['filtered_out']['no_filename']}")
        
        return groups
    
    def _create_grouped_strm_files(self, torrent_groups: Dict, media_dir: Path) -> Dict:
        """Create STRM files grouped by torrent folders under /unorganized/"""
        
        # Create unorganized directory
        unorganized_dir = media_dir / "unorganized"
        unorganized_dir.mkdir(parents=True, exist_ok=True)
        
        created_count = 0
        skipped_count = 0
        
        for torrent_id, group in torrent_groups.items():
            folder_name = group['folder_name']
            # Create folder under /unorganized/
            folder_path = unorganized_dir / folder_name
            
            # Create folder if needed
            folder_path.mkdir(parents=True, exist_ok=True)
            
            for file_info in group['files']:
                strm_filename = f"{file_info['sanitized_name']}.strm"
                strm_path = folder_path / strm_filename
                
                # Skip if file exists and has same URL
                if strm_path.exists():
                    try:
                        existing_url = strm_path.read_text(encoding='utf-8').strip()
                        if existing_url == file_info['download_url']:
                            logger.debug(f"⏭️  Skipping {strm_path}: Same URL exists")
                            skipped_count += 1
                            continue
                    except Exception:
                        pass  # If we can't read, just overwrite
                
                # Create STRM file
                try:
                    strm_path.write_text(file_info['download_url'], encoding='utf-8')
                    logger.debug(f"✅ Created {strm_path}")
                    created_count += 1
                except Exception as e:
                    logger.error(f"❌ Failed to create {strm_path}: {e}")
        
        return {"created": created_count, "skipped": skipped_count}
    
    def process_from_files(self, data_dir: Path, media_dir: Path) -> Dict:
        """
        Process by combining torrents.json + links.txt (new workflow)
        This is the main production workflow!
        """
        logger.info("📁 Processing by combining torrents.json + links.txt...")
        
        # Load required files
        torrents_file = data_dir / "realdebrid_torrents.json"
        links_file = data_dir / "realdebrid_links.txt"
        
        if not torrents_file.exists():
            return {"success": False, "error": f"Torrents file not found: {torrents_file}"}
        
        if not links_file.exists():
            return {"success": False, "error": f"Links file not found: {links_file}"}
        
        try:
            # Load torrents metadata (for folder names and grouping)
            with open(torrents_file, 'r', encoding='utf-8') as f:
                torrents = json.load(f)
            
            # Load direct links (final URLs to put in STRM files)
            with open(links_file, 'r', encoding='utf-8') as f:
                direct_links = [line.strip() for line in f if line.strip()]
                
        except Exception as e:
            return {"success": False, "error": f"Failed to load data files: {e}"}
        
        logger.info(f"Loaded {len(torrents)} torrents and {len(direct_links)} direct links")
        
        # Create mapping: Real Debrid link ID -> torrent info
        link_to_torrent = {}
        for torrent in torrents:
            if torrent.get('status') != 'downloaded':
                continue
                
            torrent_id = torrent.get("id")
            torrent_filename = torrent.get("filename", "")
            torrent_links = torrent.get("links", [])
            
            for rd_link in torrent_links:
                # Extract link ID from Real Debrid URL
                # Format: https://real-debrid.com/d/LINKID
                if "/d/" in rd_link:
                    link_id = rd_link.split("/d/")[-1]
                    link_to_torrent[link_id] = {
                        "torrent_id": torrent_id,
                        "folder_name": self.sanitize_folder_name(torrent_filename),
                        "torrent_filename": torrent_filename
                    }
        
        # Group direct links by torrent
        torrent_groups = {}
        unmatched_links = []
        filtering_stats = {
            "total_files": 0,
            "processed_files": 0,
            "filtered_out": {
                "unsupported_types": 0,
                "no_filename": 0
            }
        }
        
        for direct_url in direct_links:
            # Extract filename from direct URL
            filename = self.extract_filename_from_url(direct_url)
            filtering_stats["total_files"] += 1
            
            if not filename or filename == "unknown":
                filtering_stats["filtered_out"]["no_filename"] += 1
                logger.debug(f"⏭️  Skipping: Could not extract filename from: {direct_url}")
                continue
            
            # Apply basic filtering (extension-based only, no filesize available)
            filter_result = self.should_process_file(filename, filesize=0, mime_type="")
            
            # For file workflow, accept videos even without size check (we can't verify size)
            if not filter_result["should_process"] and filter_result["category"] == "video_small":
                # Override for videos when we can't check size
                file_ext = Path(filename).suffix.lower()
                if file_ext in self.allowed_video_extensions:
                    filter_result = {
                        "should_process": True,
                        "reason": f"Video file (size unknown, {file_ext})",
                        "category": "video"
                    }
            
            if filter_result["should_process"]:
                # Try to find torrent info by checking link ID in direct URL
                link_id = None
                if "/d/" in direct_url:
                    # Extract link ID from direct URL
                    # Format: https://sgp1.download.real-debrid.com/d/LINKID/filename
                    url_parts = direct_url.split("/d/")
                    if len(url_parts) > 1:
                        link_id = url_parts[1].split("/")[0]
                
                if link_id and link_id in link_to_torrent:
                    torrent_info = link_to_torrent[link_id]
                    folder_name = torrent_info["folder_name"]
                    
                    if folder_name not in torrent_groups:
                        torrent_groups[folder_name] = {
                            "torrent_id": torrent_info["torrent_id"],
                            "torrent_name": torrent_info["torrent_filename"],
                            "files": []
                        }
                    
                    torrent_groups[folder_name]["files"].append({
                        "url": direct_url,
                        "filename": filename,
                        "category": filter_result["category"],
                        "sanitized_name": self.sanitize_filename(filename)
                    })
                    filtering_stats["processed_files"] += 1
                    logger.debug(f"✅ Processing: {filename} - {filter_result['reason']}")
                else:
                    unmatched_links.append({
                        "url": direct_url, 
                        "filename": filename,
                        "category": filter_result["category"]
                    })
                    filtering_stats["processed_files"] += 1
                    logger.debug(f"✅ Processing (unmatched): {filename} - {filter_result['reason']}")
            else:
                filtering_stats["filtered_out"]["unsupported_types"] += 1
                logger.debug(f"⏭️  Skipping: {filename} - {filter_result['reason']}")
        
        # Log filtering statistics for file workflow
        logger.info(f"🔍 File Workflow Filtering Results:")
        logger.info(f"   📂 Total files found: {filtering_stats['total_files']}")
        logger.info(f"   ✅ Files processed: {filtering_stats['processed_files']}")
        logger.info(f"   🚫 Filtered out:")
        logger.info(f"      📄 Unsupported types: {filtering_stats['filtered_out']['unsupported_types']}")
        logger.info(f"      ❓ No filename: {filtering_stats['filtered_out']['no_filename']}")
        logger.info(f"   ⚠️  Note: Size filtering not available in file workflow")
        
        # Create STRM files grouped by torrent
        strm_results = self._create_strm_files_from_groups(torrent_groups, media_dir)
        
        # Handle unmatched links (fallback)
        if unmatched_links:
            logger.info(f"📦 Processing {len(unmatched_links)} unmatched links to unorganized/Misc folder")
            
            # Create unorganized directory
            unorganized_dir = media_dir / "unorganized"
            unorganized_dir.mkdir(parents=True, exist_ok=True)
            
            # Create Misc folder under unorganized
            misc_folder = unorganized_dir / "Misc"
            misc_folder.mkdir(parents=True, exist_ok=True)
            
            processed_misc = 0
            for file_info in unmatched_links:
                # Apply filtering for misc files too
                filter_result = self.should_process_file(file_info["filename"], filesize=0, mime_type="")
                
                # For file workflow, accept videos even without size check  
                if not filter_result["should_process"] and filter_result["category"] == "video_small":
                    file_ext = Path(file_info["filename"]).suffix.lower()
                    if file_ext in self.allowed_video_extensions:
                        filter_result["should_process"] = True
                
                if filter_result["should_process"]:
                    strm_filename = self.sanitize_filename(file_info["filename"]) + ".strm"
                    strm_path = misc_folder / strm_filename
                    
                    if not strm_path.exists():
                        try:
                            strm_path.write_text(file_info["url"], encoding='utf-8')
                            strm_results["created"] += 1
                            processed_misc += 1
                            logger.debug(f"✅ Created misc STRM: {strm_path}")
                        except Exception as e:
                            logger.error(f"❌ Failed to create misc STRM {strm_path}: {e}")
                    else:
                        strm_results["skipped"] += 1
                else:
                    logger.debug(f"⏭️  Skipping misc file: {file_info['filename']} - {filter_result['reason']}")
            
            if processed_misc > 0:
                logger.info(f"📁 {processed_misc} valid unmatched files placed in unorganized/Misc folder")
            else:
                # Remove empty Misc folder
                try:
                    misc_folder.rmdir()
                except:
                    pass
        
        # Generate summary
        summary = {
            "success": True,
            "source": "combined_files",
            "torrents_processed": len(torrent_groups),
            "total_files": sum(len(group['files']) for group in torrent_groups.values()),
            "strm_files_created": strm_results['created'],
            "strm_files_skipped": strm_results['skipped'],
            "folders_created": len(torrent_groups),
            "unmatched_links": len([f for f in unmatched_links if self.should_process_file(f["filename"], 0, "")["should_process"]]),
            "filtering_stats": filtering_stats
        }
        
        logger.info(f"✅ Processed {summary['strm_files_created']} STRM files in {summary['folders_created']} folders")
        if summary["unmatched_links"] > 0:
            logger.info(f"📁 {summary['unmatched_links']} valid unmatched files placed in unorganized/Misc folder")
        
        # Show filtering summary
        filtered_count = filtering_stats["total_files"] - filtering_stats["processed_files"]
        if filtered_count > 0:
            logger.info(f"🗑️  Filtered out {filtered_count} unwanted files")
        
        return summary
    
    def _create_strm_files_from_groups(self, torrent_groups: Dict, media_dir: Path) -> Dict:
        """Create STRM files from torrent groups under /unorganized/ (for combined workflow)"""
        
        # Create unorganized directory
        unorganized_dir = media_dir / "unorganized"
        unorganized_dir.mkdir(parents=True, exist_ok=True)
        
        created_count = 0
        skipped_count = 0
        
        for folder_name, group in torrent_groups.items():
            # Create folder under /unorganized/
            folder_path = unorganized_dir / folder_name
            folder_path.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"📦 {folder_name}: {len(group['files'])} files")
            
            for file_info in group['files']:
                strm_filename = f"{file_info['sanitized_name']}.strm"
                strm_path = folder_path / strm_filename
                
                # Skip if file exists and has same URL
                if strm_path.exists():
                    try:
                        existing_url = strm_path.read_text(encoding='utf-8').strip()
                        if existing_url == file_info['url']:
                            logger.debug(f"⏭️  Skipping {strm_path}: Same URL exists")
                            skipped_count += 1
                            continue
                    except Exception:
                        pass  # If we can't read, just overwrite
                
                # Create STRM file
                try:
                    strm_path.write_text(file_info['url'], encoding='utf-8')
                    logger.debug(f"✅ Created {strm_path}")
                    created_count += 1
                except Exception as e:
                    logger.error(f"❌ Failed to create {strm_path}: {e}")
        
        return {"created": created_count, "skipped": skipped_count}
    
    def get_summary(self, media_dir: Path) -> Dict:
        """Get summary of current STRM files organized by folders"""
        
        if not media_dir.exists():
            return {"folders": 0, "files": 0, "details": []}
        
        folders = []
        total_files = 0
        
        for folder_path in media_dir.iterdir():
            if folder_path.is_dir():
                strm_files = list(folder_path.glob("*.strm"))
                if strm_files:
                    folders.append({
                        "name": folder_path.name,
                        "files": len(strm_files),
                        "sample_files": [f.stem for f in strm_files[:3]]
                    })
                    total_files += len(strm_files)
        
        # Sort by file count descending
        folders.sort(key=lambda x: x['files'], reverse=True)
        
        return {
            "folders": len(folders),
            "files": total_files,
            "details": folders[:10]  # Top 10 folders
        }
    
    def should_process_file(self, filename: str, filesize: int = 0, mime_type: str = "") -> Dict:
        """
        Determine if a file should be processed based on type and size
        Returns: {"should_process": bool, "reason": str, "category": str}
        """
        if not filename:
            return {"should_process": False, "reason": "No filename", "category": "unknown"}
        
        filename_lower = filename.lower()
        file_ext = Path(filename).suffix.lower()
        filesize_mb = filesize / (1024 * 1024) if filesize > 0 else 0
        
        # Check for subtitle files - always process
        if file_ext in self.allowed_subtitle_extensions:
            return {
                "should_process": True, 
                "reason": f"Subtitle file ({file_ext})", 
                "category": "subtitle"
            }
        
        # Check for video files
        is_video = False
        if file_ext in self.allowed_video_extensions:
            is_video = True
        elif mime_type and any(video_type in mime_type.lower() for video_type in ['video/', 'matroska']):
            is_video = True
        
        if is_video:
            # Check minimum size for video files
            if filesize_mb >= self.min_video_size_mb:
                return {
                    "should_process": True,
                    "reason": f"Video file {filesize_mb:.1f}MB ({file_ext})",
                    "category": "video"
                }
            else:
                return {
                    "should_process": False,
                    "reason": f"Video too small: {filesize_mb:.1f}MB < {self.min_video_size_mb}MB (likely ads/junk)",
                    "category": "video_small"
                }
        
        # Reject other file types
        return {
            "should_process": False,
            "reason": f"Unsupported file type: {file_ext} ({mime_type})",
            "category": "other"
        }
    
    def configure_filtering(self, min_video_size_mb: int = None, additional_video_exts: List[str] = None, additional_subtitle_exts: List[str] = None):
        """
        Configure file filtering settings
        
        Args:
            min_video_size_mb: Minimum video file size in MB (default: 300)
            additional_video_exts: Additional video extensions to accept
            additional_subtitle_exts: Additional subtitle extensions to accept
        """
        if min_video_size_mb is not None:
            self.min_video_size_mb = min_video_size_mb
            logger.info(f"🔧 Updated minimum video size: {min_video_size_mb}MB")
        
        if additional_video_exts:
            for ext in additional_video_exts:
                if not ext.startswith('.'):
                    ext = '.' + ext
                self.allowed_video_extensions.add(ext.lower())
            logger.info(f"🔧 Added video extensions: {additional_video_exts}")
        
        if additional_subtitle_exts:
            for ext in additional_subtitle_exts:
                if not ext.startswith('.'):
                    ext = '.' + ext
                self.allowed_subtitle_extensions.add(ext.lower())
            logger.info(f"🔧 Added subtitle extensions: {additional_subtitle_exts}")
    
    def get_filtering_config(self) -> Dict:
        """Get current filtering configuration"""
        return {
            "min_video_size_mb": self.min_video_size_mb,
            "allowed_video_extensions": sorted(list(self.allowed_video_extensions)),
            "allowed_subtitle_extensions": sorted(list(self.allowed_subtitle_extensions)),
            "total_allowed_extensions": len(self.allowed_video_extensions) + len(self.allowed_subtitle_extensions)
        }

    def _create_torrent_groups(self, torrents: List[Dict], unrestricted_data: List[Dict]) -> Dict:
        """Create groups of files by torrent ID (backwards compatibility wrapper)"""
        return self._create_torrent_groups_with_skip(torrents, unrestricted_data, skip_existing=False, existing_urls=set()) 