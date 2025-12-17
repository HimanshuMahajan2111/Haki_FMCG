"""
Sales Agent Worker - Identifies and selects RFPs for processing.

Responsibilities:
1. Identifies RFPs due for submission in next 3 months
2. Scans identified web URLs to summarize RFPs with due dates
3. Selects one RFP to be sent to Main Agent
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()


@dataclass
class IdentifiedRFP:
    """RFP identified by Sales Agent."""
    rfp_id: int
    title: str
    source_url: str
    organization: str
    submission_deadline: datetime
    days_remaining: int
    estimated_value: float
    category: str
    summary: str
    priority_score: float


class SalesAgentWorker:
    """
    Sales Agent - Identifies and prioritizes RFPs.
    
    Workflow:
    1. Scan configured websites for RFP announcements
    2. Identify RFPs due in next 3 months
    3. Summarize each RFP with due dates
    4. Prioritize based on criteria
    5. Select one RFP to send to Master Agent
    """
    
    def __init__(self):
        """Initialize Sales Agent Worker."""
        self.logger = logger.bind(component="SalesAgentWorker")
        
        # Configure monitored websites
        self.monitored_websites = [
            {
                'name': 'NTPC Tender Portal',
                'url': 'https://www.ntpctender.com',
                'category': 'Power/Energy'
            },
            {
                'name': 'IREPS (Railways)',
                'url': 'https://www.ireps.gov.in',
                'category': 'Railways'
            },
            {
                'name': 'GeM Portal',
                'url': 'https://gem.gov.in',
                'category': 'Government'
            },
            {
                'name': 'PWD Maharashtra',
                'url': 'https://pwd.maharashtra.gov.in',
                'category': 'Public Works'
            }
        ]
    
    async def identify_rfps_for_next_3_months(self, db) -> List[Dict[str, Any]]:
        """Identify all RFPs due for submission in next 3 months.
        
        Args:
            db: Async database session
            
        Returns:
            List of RFP dictionaries
        """
        self.logger.info("Identifying RFPs for next 3 months", action="search")
        
        # Calculate date range
        today = datetime.now()
        three_months_later = today + timedelta(days=90)
        
        # Query database for RFPs in date range
        from db.models import RFP
        from sqlalchemy import select, and_
        
        result = await db.execute(
            select(RFP).where(
                and_(
                    RFP.due_date >= today,
                    RFP.due_date <= three_months_later
                )
            )
        )
        rfps = result.scalars().all()
        
        identified_rfps = []
        for rfp in rfps:
            days_remaining = (rfp.due_date - today).days if rfp.due_date else 0
            
            structured = rfp.structured_data or {}
            estimated_value = self._estimate_value(rfp)
            priority_score = self._calculate_priority(rfp, days_remaining)
            
            identified = {
                'id': rfp.id,
                'rfp_id': rfp.id,  # Add rfp_id for compatibility
                'title': rfp.title,
                'source_url': rfp.source or '',
                'organization': structured.get('buyer', structured.get('organization', 'Unknown')),
                'due_date': rfp.due_date,
                'days_remaining': days_remaining,
                'days_until_deadline': days_remaining,  # Add for compatibility
                'estimated_value': estimated_value,
                'category': structured.get('category', 'General'),
                'summary': self._create_summary(rfp),
                'priority_score': priority_score,
                'status': rfp.status.value if hasattr(rfp.status, 'value') else str(rfp.status),
                'structured_data': structured,  # Include full structured data
                'requirements': rfp.requirements or {},  # Include requirements
                'file_path': rfp.file_path or '',  # Include file path
                'raw_text': rfp.raw_text or ''  # Include raw text
            }
            
            identified_rfps.append(identified)
        
        self.logger.info(
            f"Identified {len(identified_rfps)} RFPs in next 3 months",
            status="success"
        )
        
        return identified_rfps
    
    def scan_web_urls_and_summarize(self) -> List[Dict[str, Any]]:
        """Scan identified web URLs to summarize RFPs with due dates.
        
        Returns:
            List of RFP summaries from web scraping
        """
        self.logger.info("🌐 Scanning web URLs for new RFPs")
        
        summaries = []
        
        for website in self.monitored_websites:
            self.logger.info(f"Scanning {website['name']}")
            
            # In real implementation, this would scrape the website
            # For now, we simulate finding RFPs
            found_rfps = self._simulate_web_scraping(website)
            summaries.extend(found_rfps)
        
        self.logger.info(f"Found {len(summaries)} RFPs from web scraping", status="success")
        
        return summaries
    
    async def select_one_rfp_for_processing(
        self, 
        identified_rfps: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Select one RFP to send to Master Agent based on priority.
        
        Args:
            identified_rfps: List of identified RFP dictionaries
            
        Returns:
            Selected RFP data for Master Agent
        """
        if not identified_rfps:
            self.logger.warning("No RFPs available for selection")
            return None
        
        # Sort by priority score (highest first)
        sorted_rfps = sorted(
            identified_rfps,
            key=lambda x: x['priority_score'],
            reverse=True
        )
        
        selected_rfp = sorted_rfps[0]
        
        self.logger.info(
            f"Selected RFP for processing",
            status="success",
            rfp_id=selected_rfp['id'],
            title=selected_rfp['title'],
            priority_score=selected_rfp['priority_score'],
            days_remaining=selected_rfp['days_remaining']
        )
        
        # Return the selected RFP data (already contains all needed fields)
        return selected_rfp
    
    def _create_summary(self, rfp) -> str:
        """Create concise RFP summary."""
        structured = rfp.structured_data or {}
        category = structured.get('category', 'Electrical Products')
        quantity = structured.get('quantity', 'Not specified')
        
        summary = (
            f"{category} procurement for {structured.get('buyer', 'Unknown organization')}. "
            f"Quantity: {quantity}. "
            f"Due: {rfp.due_date.strftime('%d-%b-%Y') if rfp.due_date else 'TBD'}."
        )
        
        return summary
    
    def _estimate_value(self, rfp) -> float:
        """Estimate RFP value based on category and quantity."""
        structured = rfp.structured_data or {}
        category = structured.get('category', '').lower()
        
        # Base values by category (in INR)
        category_values = {
            'solar': 15000000,  # 1.5 Cr
            'power': 12000000,  # 1.2 Cr
            'signaling': 8000000,  # 80 L
            'telecom': 10000000,  # 1 Cr
            'electrical': 5000000  # 50 L
        }
        
        for key, value in category_values.items():
            if key in category:
                return value
        
        return 5000000  # Default 50 L
    
    def _calculate_priority(self, rfp, days_remaining: int) -> float:
        """Calculate priority score for RFP.
        
        Factors:
        - Days remaining (urgent = higher priority)
        - Estimated value (higher = higher priority)
        - Category match (our expertise = higher priority)
        - Status (discovered/new = higher priority)
        
        Score range: 0-100
        """
        score = 50.0  # Base score
        
        # Urgency score (0-30 points)
        if days_remaining <= 7:
            score += 30
        elif days_remaining <= 14:
            score += 25
        elif days_remaining <= 30:
            score += 20
        elif days_remaining <= 60:
            score += 15
        else:
            score += 10
        
        # Value score (0-30 points)
        estimated_value = self._estimate_value(rfp)
        if estimated_value >= 10000000:  # >= 1 Cr
            score += 30
        elif estimated_value >= 5000000:  # >= 50 L
            score += 20
        else:
            score += 10
        
        # Status score (0-20 points)
        if rfp.status.value == 'discovered':
            score += 20
        elif rfp.status.value == 'processing':
            score += 10
        
        return min(score, 100.0)
    
    def _simulate_web_scraping(self, website: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Simulate web scraping (placeholder for real implementation)."""
        # In production, this would use beautifulsoup4, selenium, or scrapy
        # For now, return empty list
        return []
