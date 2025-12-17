"""
Website Scanner for Procurement Portals

Scans mock procurement websites and extracts RFP data for agent processing.
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from pathlib import Path

from .mock_procurement_sites import get_all_mock_websites, get_all_rfps

logger = logging.getLogger(__name__)


class WebsiteScanner:
    """Scanner for procurement websites."""
    
    def __init__(self):
        self.websites = get_all_mock_websites()
        self.scan_history = []
    
    async def scan_all_websites(self, category: str = None) -> List[Dict[str, Any]]:
        """
        Scan all procurement websites for RFPs.
        
        Args:
            category: Filter by category (e.g., "Power Cables", "Solar Cables")
        
        Returns:
            List of RFP data dictionaries
        """
        logger.info(f"Starting scan of {len(self.websites)} procurement websites")
        
        all_rfps = []
        for website in self.websites:
            try:
                logger.info(f"Scanning {website.name}...")
                rfps = website.get_rfps(category=category)
                all_rfps.extend(rfps)
                logger.info(f"Found {len(rfps)} RFPs on {website.name}")
            except Exception as e:
                logger.error(f"Error scanning {website.name}: {e}")
        
        # Record scan
        self.scan_history.append({
            'timestamp': datetime.now().isoformat(),
            'rfps_found': len(all_rfps),
            'category_filter': category
        })
        
        logger.info(f"Scan complete. Total RFPs found: {len(all_rfps)}")
        return all_rfps
    
    async def scan_single_website(self, website_name: str, category: str = None) -> List[Dict[str, Any]]:
        """
        Scan a specific procurement website.
        
        Args:
            website_name: Name of website (e.g., "eProcure", "GEM")
            category: Filter by category
        
        Returns:
            List of RFP data dictionaries
        """
        website = next((w for w in self.websites if w.name == website_name), None)
        if not website:
            logger.error(f"Website {website_name} not found")
            return []
        
        logger.info(f"Scanning {website_name}...")
        rfps = website.get_rfps(category=category)
        logger.info(f"Found {len(rfps)} RFPs on {website_name}")
        return rfps
    
    async def get_new_rfps(self, since_date: datetime = None) -> List[Dict[str, Any]]:
        """
        Get RFPs published after a specific date.
        
        Args:
            since_date: Filter RFPs published after this date
        
        Returns:
            List of RFP data dictionaries
        """
        all_rfps = await self.scan_all_websites()
        
        if not since_date:
            return all_rfps
        
        new_rfps = []
        for rfp in all_rfps:
            publish_date = datetime.fromisoformat(rfp['publish_date'])
            if publish_date > since_date:
                new_rfps.append(rfp)
        
        logger.info(f"Found {len(new_rfps)} new RFPs since {since_date}")
        return new_rfps
    
    def get_rfp_by_id(self, rfp_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific RFP by ID.
        
        Args:
            rfp_id: RFP identifier (e.g., "EPRO-2025-001")
        
        Returns:
            RFP data dictionary or None
        """
        all_rfps = get_all_rfps()
        for rfp in all_rfps:
            if rfp['rfp_id'] == rfp_id:
                return rfp
        return None
    
    async def continuous_scan(self, interval_minutes: int = 60, category: str = None):
        """
        Continuously scan websites at specified interval.
        
        Args:
            interval_minutes: Scan interval in minutes
            category: Filter by category
        """
        logger.info(f"Starting continuous scan (interval: {interval_minutes} minutes)")
        
        while True:
            try:
                rfps = await self.scan_all_websites(category=category)
                logger.info(f"Continuous scan found {len(rfps)} RFPs")
                await asyncio.sleep(interval_minutes * 60)
            except Exception as e:
                logger.error(f"Error in continuous scan: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    def get_scan_statistics(self) -> Dict[str, Any]:
        """Get scanning statistics."""
        total_scans = len(self.scan_history)
        if total_scans == 0:
            return {
                'total_scans': 0,
                'total_rfps_found': 0,
                'last_scan': None
            }
        
        total_rfps = sum(scan['rfps_found'] for scan in self.scan_history)
        last_scan = self.scan_history[-1]
        
        return {
            'total_scans': total_scans,
            'total_rfps_found': total_rfps,
            'avg_rfps_per_scan': total_rfps / total_scans if total_scans > 0 else 0,
            'last_scan': last_scan['timestamp'],
            'last_scan_rfps': last_scan['rfps_found']
        }


async def scan_and_process_rfps(scanner: WebsiteScanner, category: str = None) -> List[Dict[str, Any]]:
    """
    Scan websites and prepare RFPs for agent processing.
    
    Args:
        scanner: WebsiteScanner instance
        category: Filter by category
    
    Returns:
        List of RFPs ready for agent processing
    """
    rfps = await scanner.scan_all_websites(category=category)
    
    # Transform to agent-friendly format
    processed_rfps = []
    for rfp in rfps:
        processed_rfp = {
            'rfp_id': rfp['rfp_id'],
            'title': rfp['title'],
            'buyer': rfp['buyer'],
            'category': rfp['category'],
            'description': rfp['description'],
            'estimated_value': rfp['estimated_value'],
            'specifications': rfp['specifications'],
            'submission_deadline': rfp['submission_deadline'],
            'source': rfp['website'],
            'source_type': 'procurement_portal',
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        processed_rfps.append(processed_rfp)
    
    return processed_rfps


if __name__ == "__main__":
    # Test scanner
    async def test_scanner():
        scanner = WebsiteScanner()
        
        print("=== Testing Website Scanner ===\n")
        
        # Scan all websites
        print("1. Scanning all websites...")
        all_rfps = await scanner.scan_all_websites()
        print(f"   Found {len(all_rfps)} total RFPs\n")
        
        # Scan by category
        print("2. Scanning for Solar Cables...")
        solar_rfps = await scanner.scan_all_websites(category="Solar")
        print(f"   Found {len(solar_rfps)} solar-related RFPs\n")
        
        # Scan single website
        print("3. Scanning eProcure portal...")
        eprocure_rfps = await scanner.scan_single_website("eProcure")
        print(f"   Found {len(eprocure_rfps)} RFPs on eProcure\n")
        
        # Get specific RFP
        print("4. Getting specific RFP...")
        rfp = scanner.get_rfp_by_id("EPRO-2025-001")
        if rfp:
            print(f"   RFP: {rfp['title']}")
            print(f"   Buyer: {rfp['buyer']}")
            print(f"   Value: ₹{rfp['estimated_value']:,.0f}\n")
        
        # Statistics
        print("5. Scan statistics:")
        stats = scanner.get_scan_statistics()
        for key, value in stats.items():
            print(f"   {key}: {value}")
    
    asyncio.run(test_scanner())
