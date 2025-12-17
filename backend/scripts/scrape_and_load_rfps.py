"""
Scrape and Load RFPs - Monitor websites and load RFPs to database

This script runs the web scrapers and saves discovered RFPs to the database.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from agents.web_scrapers import WebScraperOrchestrator
import structlog

logger = structlog.get_logger()


async def main():
    """Main entry point for RFP scraping."""
    
    logger.info("="*80)
    logger.info("WEB SCRAPING - RFP DISCOVERY")
    logger.info("="*80)
    
    # Create orchestrator
    orchestrator = WebScraperOrchestrator()
    
    # Scrape and save to database
    await orchestrator.scrape_and_save_to_db()
    
    logger.info("\n" + "="*80)
    logger.info("SCRAPING COMPLETE")
    logger.info("="*80)


if __name__ == "__main__":
    asyncio.run(main())
