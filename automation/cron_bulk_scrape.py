#!/usr/bin/env python3
import logging
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from services.aggregator import bulk_scrape, run_maintenance
from services.database import optimize_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(PROJECT_ROOT / "cron_bulk_scrape.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("cron_job")

def main():
    logger.info("Starting scheduled bulk scrape...")
    
    try:
        # Run maintenance before scraping
        logger.info("Maintenance: Checking and fixing district mismatches...")
        run_maintenance()
        
        # Run bulk scrape
        # We use 2 pages per query for the daily run to get good coverage
        logger.info("Running bulk scrape (2 pages per query)...")
        bulk_scrape(pages_per_query=2)
        
        # Optimize database after all operations
        logger.info("Maintenance: Optimizing database (VACUUM)...")
        optimize_db()
        
        logger.info("Scheduled bulk scrape completed successfully.")
    except Exception as e:
        logger.error(f"Cron job failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
