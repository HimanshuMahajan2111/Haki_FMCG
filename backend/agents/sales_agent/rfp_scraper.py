"""
RFP Scraper - Scrapes detailed RFP information from URLs.
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re
import structlog

logger = structlog.get_logger()


@dataclass
class ScrapedRFP:
    """Scraped RFP data."""
    url: str
    title: str = ""
    organization: str = ""
    tender_number: str = ""
    
    # Dates
    published_date: Optional[datetime] = None
    submission_deadline: Optional[datetime] = None
    opening_date: Optional[datetime] = None
    
    # Content
    description: str = ""
    categories: List[str] = None
    estimated_value: Optional[float] = None
    
    # Requirements
    technical_requirements: List[str] = None
    certifications: List[str] = None
    
    # Documents
    document_urls: List[str] = None
    
    # Metadata
    scraped_at: datetime = None
    html_content: str = ""
    
    def __post_init__(self):
        if self.categories is None:
            self.categories = []
        if self.technical_requirements is None:
            self.technical_requirements = []
        if self.certifications is None:
            self.certifications = []
        if self.document_urls is None:
            self.document_urls = []
        if self.scraped_at is None:
            self.scraped_at = datetime.now()


class RFPScraper:
    """Scrape RFP details from websites."""
    
    def __init__(self):
        """Initialize RFP scraper."""
        self.logger = logger.bind(component="RFPScraper")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        self.logger.info("RFP scraper initialized")
    
    def scrape_rfp(self, url: str) -> ScrapedRFP:
        """Scrape RFP details from URL.
        
        Args:
            url: RFP URL to scrape
            
        Returns:
            ScrapedRFP object
        """
        self.logger.info("Scraping RFP", url=url)
        
        try:
            # Fetch page
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract RFP data
            rfp = self._extract_rfp_data(soup, url)
            rfp.html_content = str(soup)[:10000]  # Store first 10k chars
            
            self.logger.info(
                "RFP scraped successfully",
                url=url,
                title=rfp.title[:50] if rfp.title else "N/A"
            )
            
            return rfp
            
        except requests.RequestException as e:
            self.logger.error("Failed to fetch RFP", url=url, error=str(e))
            return ScrapedRFP(url=url, title="Error fetching RFP")
            
        except Exception as e:
            self.logger.error("Error scraping RFP", url=url, error=str(e))
            return ScrapedRFP(url=url, title="Error parsing RFP")
    
    def _extract_rfp_data(self, soup: BeautifulSoup, url: str) -> ScrapedRFP:
        """Extract RFP data from parsed HTML.
        
        Args:
            soup: BeautifulSoup object
            url: RFP URL
            
        Returns:
            ScrapedRFP object
        """
        rfp = ScrapedRFP(url=url)
        
        # Extract title
        rfp.title = self._extract_title(soup)
        
        # Extract organization
        rfp.organization = self._extract_organization(soup)
        
        # Extract tender number
        rfp.tender_number = self._extract_tender_number(soup)
        
        # Extract dates
        rfp.published_date = self._extract_date(soup, ['publish', 'release', 'issue'])
        rfp.submission_deadline = self._extract_date(soup, ['deadline', 'due', 'last date', 'submission'])
        rfp.opening_date = self._extract_date(soup, ['opening', 'evaluation'])
        
        # Extract description
        rfp.description = self._extract_description(soup)
        
        # Extract categories
        rfp.categories = self._extract_categories(soup)
        
        # Extract estimated value
        rfp.estimated_value = self._extract_value(soup)
        
        # Extract requirements
        rfp.technical_requirements = self._extract_requirements(soup)
        
        # Extract certifications
        rfp.certifications = self._extract_certifications(soup)
        
        # Extract document URLs
        rfp.document_urls = self._extract_documents(soup, url)
        
        return rfp
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract RFP title."""
        # Try common title patterns
        title_elem = (
            soup.find('h1') or
            soup.find('title') or
            soup.find(class_=re.compile(r'(title|heading|rfp.*title)', re.I)) or
            soup.find('meta', {'property': 'og:title'})
        )
        
        if title_elem:
            if title_elem.name == 'meta':
                return title_elem.get('content', '').strip()
            return title_elem.get_text(strip=True)
        
        return ""
    
    def _extract_organization(self, soup: BeautifulSoup) -> str:
        """Extract organization name."""
        # Look for organization patterns
        org_elem = soup.find(text=re.compile(r'(organization|department|ministry|corporation)', re.I))
        
        if org_elem:
            parent = org_elem.parent
            if parent:
                return parent.get_text(strip=True)
        
        return ""
    
    def _extract_tender_number(self, soup: BeautifulSoup) -> str:
        """Extract tender/RFP number."""
        # Look for tender number patterns
        text = soup.get_text()
        
        patterns = [
            r'Tender\s*(?:No|Number|ID)[:\s]*([A-Z0-9\-/]+)',
            r'RFP\s*(?:No|Number|ID)[:\s]*([A-Z0-9\-/]+)',
            r'NIT\s*(?:No|Number|ID)[:\s]*([A-Z0-9\-/]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_date(self, soup: BeautifulSoup, keywords: List[str]) -> Optional[datetime]:
        """Extract date based on keywords."""
        text = soup.get_text()
        
        # Build pattern
        keyword_pattern = '|'.join(keywords)
        date_pattern = r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
        
        pattern = f'(?:{keyword_pattern})[:\\s]*{date_pattern}'
        match = re.search(pattern, text, re.I)
        
        if match:
            date_str = match.group(1)
            return self._parse_date(date_str)
        
        return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string."""
        formats = [
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%d-%m-%y',
            '%d/%m/%y',
            '%Y-%m-%d'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract RFP description."""
        # Look for description sections
        desc_elem = (
            soup.find(class_=re.compile(r'(description|summary|scope)', re.I)) or
            soup.find('meta', {'name': 'description'}) or
            soup.find('p')
        )
        
        if desc_elem:
            if desc_elem.name == 'meta':
                return desc_elem.get('content', '').strip()
            return desc_elem.get_text(strip=True)[:1000]  # First 1000 chars
        
        return ""
    
    def _extract_categories(self, soup: BeautifulSoup) -> List[str]:
        """Extract categories/sectors."""
        categories = []
        
        text = soup.get_text().lower()
        
        # Common categories
        category_keywords = [
            'electrical', 'electronics', 'civil', 'mechanical',
            'it', 'software', 'hardware', 'construction',
            'medical', 'furniture', 'stationery', 'catering',
            'security', 'transportation', 'maintenance'
        ]
        
        for keyword in category_keywords:
            if keyword in text:
                categories.append(keyword.title())
        
        return categories
    
    def _extract_value(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract estimated contract value."""
        text = soup.get_text()
        
        # Look for value patterns
        patterns = [
            r'(?:value|amount|budget)[:\s]*(?:INR|Rs\.?|₹)\s*([\d,]+(?:\.\d{2})?)',
            r'(?:INR|Rs\.?|₹)\s*([\d,]+(?:\.\d{2})?)\s*(?:lakh|lac|crore)?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                value_str = match.group(1).replace(',', '')
                try:
                    value = float(value_str)
                    
                    # Convert lakhs/crores to base value
                    if 'lakh' in text[match.start():match.end()+20].lower():
                        value *= 100000
                    elif 'crore' in text[match.start():match.end()+20].lower():
                        value *= 10000000
                    
                    return value
                except ValueError:
                    pass
        
        return None
    
    def _extract_requirements(self, soup: BeautifulSoup) -> List[str]:
        """Extract technical requirements."""
        requirements = []
        
        # Look for requirements section
        req_section = soup.find(text=re.compile(r'(requirement|specification|eligibility)', re.I))
        
        if req_section:
            parent = req_section.find_parent(['div', 'section', 'table'])
            if parent:
                items = parent.find_all(['li', 'p'])
                for item in items[:10]:  # Max 10
                    req_text = item.get_text(strip=True)
                    if len(req_text) > 10:
                        requirements.append(req_text)
        
        return requirements
    
    def _extract_certifications(self, soup: BeautifulSoup) -> List[str]:
        """Extract certification requirements."""
        certifications = []
        
        text = soup.get_text()
        
        # Common certifications
        cert_patterns = [
            r'(ISI\s*(?:mark|certified)?)',
            r'(ISO\s*\d{4,5})',
            r'(BEE\s*(?:rating|star)?)',
            r'(CE\s*(?:mark|certified)?)',
            r'(UL\s*(?:listed|certified)?)',
            r'(RoHS\s*compliant)'
        ]
        
        for pattern in cert_patterns:
            matches = re.findall(pattern, text, re.I)
            certifications.extend(matches)
        
        return list(set(certifications))  # Remove duplicates
    
    def _extract_documents(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract document URLs."""
        documents = []
        
        # Find all PDF/DOC links
        links = soup.find_all('a', href=re.compile(r'\.(pdf|doc|docx|xls|xlsx)$', re.I))
        
        for link in links[:10]:  # Max 10 documents
            url = link.get('href', '')
            if url:
                # Make absolute URL
                if url.startswith('/'):
                    from urllib.parse import urljoin
                    url = urljoin(base_url, url)
                documents.append(url)
        
        return documents
