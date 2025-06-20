#!/usr/bin/env python3
"""
Real Debrid Media Manager - Main Application
Runs 20-minute cycles with retry logic and file expiration tracking
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

from .config import load_config
from .cycle_manager import CycleManager

# Ensure log directory exists before setting up logging
Path('/app/logs').mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/logs/realdebrid.log')
    ]
)

logger = logging.getLogger(__name__)

class RealDebridManager:
    def __init__(self):
        self.config = load_config()
        self.running = True
        self.cycle_manager = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"📡 Received signal {signum}, initiating graceful shutdown...")
        self.running = False
    
    async def run(self):
        """Main application entry point with cycle management"""
        
        try:
            logger.info("🚀 Real Debrid Media Manager Starting")
            logger.info("=" * 60)
            
            # Validate configuration
            if not self.config.get("real_debrid", {}).get("api_key"):
                logger.error("❌ REAL_DEBRID_API_KEY not configured")
                return
            
            # Setup paths
            media_dir = Path(self.config["paths"]["media_dir"])
            output_dir = Path(self.config["paths"]["output_dir"])
            log_dir = Path(self.config["paths"]["log_dir"])
            
            # Create directories
            for directory in [media_dir, output_dir, log_dir]:
                directory.mkdir(parents=True, exist_ok=True)
                logger.info(f"📁 Directory ready: {directory}")
            
            # Initialize cycle manager
            api_key = self.config["real_debrid"]["api_key"]
            self.cycle_manager = CycleManager(
                api_key=api_key,
                media_dir=media_dir,
                output_dir=output_dir
            )
            
            logger.info("🔧 Configuration:")
            logger.info(f"   📡 API Key: {'*' * 20}...{api_key[-4:]}")
            logger.info(f"   📁 Media Directory: {media_dir}")
            logger.info(f"   📊 Output Directory: {output_dir}")
            logger.info(f"   🔄 Cycle Interval: 20 minutes")
            logger.info(f"   📅 File Expiry: 14 days")
            logger.info("")
            
            # Check if this is first run or continuing from previous state
            retry_queue_file = output_dir / "retry_queue.json"
            file_tracking_file = output_dir / "file_tracking.json"
            
            if retry_queue_file.exists() or file_tracking_file.exists():
                logger.info("🔄 Continuing from previous state")
                logger.info(f"   📝 Retry queue exists: {retry_queue_file.exists()}")
                logger.info(f"   📊 File tracking exists: {file_tracking_file.exists()}")
            else:
                logger.info("🆕 First run - initializing fresh state")
            
            logger.info("")
            logger.info("🚀 Starting cycle scheduler...")
            logger.info("   ⏱️  Cycles run every 20 minutes")
            logger.info("   🔄 503 errors retry 2 times per cycle")
            logger.info("   📅 Files expire after 14 days")
            logger.info("   ⏭️  Existing files are skipped until expiry")
            logger.info("")
            
            # Start the cycle scheduler
            await self.cycle_manager.run_scheduler()
            
        except KeyboardInterrupt:
            logger.info("🛑 Shutdown requested by user")
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
            raise
        finally:
            logger.info("📴 Real Debrid Media Manager stopped")

def main():
    """Entry point for the application"""
    manager = RealDebridManager()
    
    try:
        # Run the async main function
        asyncio.run(manager.run())
    except KeyboardInterrupt:
        logger.info("🛑 Application interrupted")
    except Exception as e:
        logger.error(f"❌ Application failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 