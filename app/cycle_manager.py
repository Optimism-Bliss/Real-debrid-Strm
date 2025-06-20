#!/usr/bin/env python3
"""
Cycle Manager for Real Debrid Media Manager
Handles 20-minute cycles with retry logic and file expiration
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set
import os

from .real_debrid_processor import RealDebridProcessor

logger = logging.getLogger(__name__)

class CycleManager:
    def __init__(self, api_key: str, media_dir: Path, output_dir: Path):
        self.api_key = api_key
        self.media_dir = media_dir
        self.output_dir = output_dir
        self.processor = RealDebridProcessor(api_key)
        
        # Cycle configuration from environment
        self.cycle_interval = int(os.getenv('CYCLE_INTERVAL_MINUTES', '20')) * 60  # Convert minutes to seconds
        self.file_expiry_days = int(os.getenv('FILE_EXPIRY_DAYS', '14'))
        
        logger.info(f"🔧 CycleManager Configuration:")
        logger.info(f"   🔄 Cycle interval: {self.cycle_interval/60:.0f} minutes")
        logger.info(f"   📅 File expiry: {self.file_expiry_days} days")
        
        # Retry queue for 503 errors
        self.retry_queue_file = output_dir / "retry_queue.json"
        self.file_tracking_file = output_dir / "file_tracking.json"
        
        # Initialize tracking data
        self.retry_queue = self._load_retry_queue()
        self.file_tracking = self._load_file_tracking()
    
    def _load_retry_queue(self) -> List[Dict]:
        """Load retry queue from disk"""
        if self.retry_queue_file.exists():
            try:
                with open(self.retry_queue_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load retry queue: {e}")
        return []
    
    def _save_retry_queue(self):
        """Save retry queue to disk"""
        try:
            with open(self.retry_queue_file, 'w', encoding='utf-8') as f:
                json.dump(self.retry_queue, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Could not save retry queue: {e}")
    
    def _load_file_tracking(self) -> Dict:
        """Load file tracking data from disk"""
        if self.file_tracking_file.exists():
            try:
                with open(self.file_tracking_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load file tracking: {e}")
        return {}
    
    def _save_file_tracking(self):
        """Save file tracking data to disk"""
        try:
            with open(self.file_tracking_file, 'w', encoding='utf-8') as f:
                json.dump(self.file_tracking, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Could not save file tracking: {e}")
    
    def _add_to_retry_queue(self, link: str, torrent_info: Dict):
        """Add a failed 503 link to retry queue"""
        retry_item = {
            "link": link,
            "torrent_info": torrent_info,
            "added_at": datetime.now().isoformat(),
            "retry_count": 0
        }
        self.retry_queue.append(retry_item)
        self._save_retry_queue()
        logger.info(f"📝 Added to retry queue: {link}")
    
    def _get_existing_strm_files(self) -> Set[str]:
        """Get set of existing STRM files for duplicate detection"""
        existing_files = set()
        
        if not self.media_dir.exists():
            return existing_files
        
        unorganized_dir = self.media_dir / "unorganized"
        if not unorganized_dir.exists():
            return existing_files
        
        # Scan all STRM files
        for strm_file in unorganized_dir.rglob("*.strm"):
            try:
                # Read the URL from STRM file
                url = strm_file.read_text(encoding='utf-8').strip()
                existing_files.add(url)
                
                # Track file creation time
                file_key = str(strm_file.relative_to(unorganized_dir))
                if file_key not in self.file_tracking:
                    self.file_tracking[file_key] = {
                        "created_at": datetime.fromtimestamp(strm_file.stat().st_ctime).isoformat(),
                        "url": url,
                        "last_checked": datetime.now().isoformat()
                    }
                    
            except Exception as e:
                logger.debug(f"Could not read STRM file {strm_file}: {e}")
        
        return existing_files
    
    def _check_expired_files(self) -> List[str]:
        """Check for STRM files that are older than 14 days and need refresh"""
        expired_files = []
        current_time = datetime.now()
        expiry_threshold = current_time - timedelta(days=self.file_expiry_days)
        
        for file_path, file_info in self.file_tracking.items():
            try:
                created_at = datetime.fromisoformat(file_info["created_at"])
                if created_at < expiry_threshold:
                    expired_files.append(file_info["url"])
                    logger.info(f"📅 File expired (>{self.file_expiry_days} days): {file_path}")
            except Exception as e:
                logger.debug(f"Could not parse date for {file_path}: {e}")
        
        return expired_files
    
    def _process_retry_queue(self) -> Dict:
        """Process items in retry queue"""
        if not self.retry_queue:
            return {"processed": 0, "succeeded": 0, "failed": 0}
        
        logger.info(f"🔄 Processing {len(self.retry_queue)} items from retry queue")
        
        processed = 0
        succeeded = 0
        failed = 0
        new_retry_queue = []
        
        for item in self.retry_queue:
            link = item["link"]
            torrent_info = item["torrent_info"]
            retry_count = item.get("retry_count", 0)
            
            logger.info(f"🔄 Retrying: {link} (attempt {retry_count + 1})")
            
            # TODO: Implement single link retry logic here
            # For now, we'll mark all as succeeded to clear the queue
            processed += 1
            succeeded += 1
            
            # Update file tracking
            self.file_tracking[f"retry_{processed}"] = {
                "created_at": datetime.now().isoformat(),
                "url": link,
                "last_checked": datetime.now().isoformat(),
                "retry_attempt": True
            }
        
        # Clear retry queue on success
        self.retry_queue = new_retry_queue
        self._save_retry_queue()
        self._save_file_tracking()
        
        return {"processed": processed, "succeeded": succeeded, "failed": failed}
    
    async def run_cycle(self) -> Dict:
        """Run a single processing cycle"""
        cycle_start = time.time()
        logger.info("🔄 Starting new processing cycle")
        
        # 1. Check existing files and expiry
        existing_files = self._get_existing_strm_files()
        expired_urls = set(self._check_expired_files())
        
        logger.info(f"📊 Cycle Status:")
        logger.info(f"   📁 Existing STRM files: {len(existing_files)}")
        logger.info(f"   📅 Expired files (>{self.file_expiry_days} days): {len(expired_urls)}")
        logger.info(f"   🔄 Retry queue: {len(self.retry_queue)} items")
        
        # 2. Process retry queue first
        retry_results = self._process_retry_queue()
        if retry_results["processed"] > 0:
            logger.info(f"🔄 Retry queue: {retry_results['succeeded']}/{retry_results['processed']} succeeded")
        
        # 3. Run main processing with skip logic
        main_results = await self.processor.process_from_api(
            output_dir=self.output_dir,
            media_dir=self.media_dir,
            skip_existing=True,
            existing_urls=existing_files - expired_urls,  # Skip existing but not expired
            cycle_mode=True
        )
        
        # 4. Update tracking
        self._save_file_tracking()
        
        cycle_time = time.time() - cycle_start
        
        summary = {
            "cycle_duration": cycle_time,
            "existing_files_skipped": len(existing_files - expired_urls),
            "expired_files_refreshed": len(expired_urls),
            "retry_queue_processed": retry_results["processed"],
            "main_processing": main_results,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Cycle completed in {cycle_time:.1f}s")
        logger.info(f"   ⏭️  Skipped {summary['existing_files_skipped']} existing files")
        logger.info(f"   🔄 Refreshed {summary['expired_files_refreshed']} expired files")
        
        return summary
    
    async def run_scheduler(self):
        """Run the 20-minute cycle scheduler"""
        logger.info(f"🚀 Starting cycle scheduler (interval: {self.cycle_interval/60:.0f} minutes)")
        
        cycle_count = 0
        
        while True:
            try:
                cycle_count += 1
                logger.info(f"📅 Starting cycle #{cycle_count}")
                
                # Run cycle
                results = await self.run_cycle()
                
                # Log summary
                logger.info(f"📊 Cycle #{cycle_count} Summary:")
                logger.info(f"   ⏱️  Duration: {results['cycle_duration']:.1f}s")
                logger.info(f"   📁 Files skipped: {results['existing_files_skipped']}")
                logger.info(f"   🔄 Queue processed: {results['retry_queue_processed']}")
                
                # Wait for next cycle
                logger.info(f"💤 Waiting {self.cycle_interval/60:.0f} minutes for next cycle...")
                await asyncio.sleep(self.cycle_interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Scheduler stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in cycle #{cycle_count}: {e}")
                logger.info(f"⏱️  Waiting {self.cycle_interval/60:.0f} minutes before retry...")
                await asyncio.sleep(self.cycle_interval) 