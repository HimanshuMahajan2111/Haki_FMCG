"""
URL Monitor - Monitors websites for new RFP announcements.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re
import structlog
import time
import hashlib
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = structlog.get_logger()


@dataclass
class MonitoredSite:
    """Configuration for a monitored website."""
    name: str
    url: str
    site_type: str  # government, private, portal
    
    # Scraping configuration
    rfp_list_selector: str = ""  # CSS selector for RFP list
    rfp_link_selector: str = "a"  # CSS selector for RFP links
    title_selector: str = ""
    date_selector: str = ""
    
    # Filters
    keywords: List[str] = None
    exclude_keywords: List[str] = None
    
    # Settings
    enabled: bool = True
    check_interval_minutes: int = 60
    max_pages: int = 1
    
    # Authentication
    requires_auth: bool = False
    auth_type: str = "none"  # none, basic, bearer, session
    auth_credentials: Dict[str, str] = None
    
    # Rate limiting
    rate_limit_seconds: int = 2
    
    # Selenium support
    use_selenium: bool = False
    wait_for_selector: str = ""
    wait_timeout: int = 10
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.exclude_keywords is None:
            self.exclude_keywords = []
        if self.auth_credentials is None:
            self.auth_credentials = {}


class URLMonitor:
    """Monitor URLs for new RFP announcements."""
    
    def __init__(self):
        """Initialize URL monitor."""
        self.logger = logger.bind(component="URLMonitor")
        self.monitored_sites: List[MonitoredSite] = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        self.logger.info("URL monitor initialized")
    
    def add_site(self, site: MonitoredSite):
        """Add a site to monitor.
        
        Args:
            site: MonitoredSite configuration
        """
        self.monitored_sites.append(site)
        self.logger.info("Site added to monitoring", site=site.name)
    
    def remove_site(self, site_name: str):
        """Remove a site from monitoring.
        
        Args:
            site_name: Name of site to remove
        """
        self.monitored_sites = [s for s in self.monitored_sites if s.name != site_name]
        self.logger.info("Site removed from monitoring", site=site_name)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.RequestException, ConnectionError))
    )
    def check_site(self, site: MonitoredSite) -> List[Dict[str, Any]]:
        """Check a site for new RFPs.
        
        Args:
            site: MonitoredSite to check
            
        Returns:
            List of discovered RFPs
        """
        if not site.enabled:
            self.logger.debug("Site disabled, skipping", site=site.name)
            return []
        
        self.logger.info("Checking site for RFPs", site=site.name)
        
        try:
            # Fetch page
            response = self.session.get(site.url, timeout=30)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract RFPs
            rfps = self._extract_rfps(soup, site)
            
            # Filter duplicates
            unique_rfps = []
            duplicates = 0
            for rfp in rfps:
                if not self._is_duplicate(rfp):
                    unique_rfps.append(rfp)
                else:
                    duplicates += 1
            
            self.logger.info(
                "Site checked successfully",
                site=site.name,
                rfps_found=len(rfps),
                unique=len(unique_rfps),
                duplicates=duplicates
            )
            
            return unique_rfps
        except requests.RequestException as e:
            self.logger.error(
                "Failed to check site",
                site=site.name,
                error=str(e)
            )
            raise  # Re-raise for retry logic
        except Exception as e:
            self.logger.error(
                "Unexpected error checking site",
                site=site.name,
                error=str(e)
            )
            return []
    
    def _scrape_with_selenium(self, site: MonitoredSite) -> BeautifulSoup:
        """Scrape dynamic page with Selenium.
        
        Args:
            site: Site configuration
            
        Returns:
            BeautifulSoup object
        """
        if not self.selenium_driver:
            self._init_selenium()
            if not self.selenium_driver:
                raise Exception("Selenium not available")
        
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            self.logger.info("Using Selenium for dynamic page", site=site.name)
            
            # Load page
            self.selenium_driver.get(site.url)
            
            # Wait for dynamic content
            if site.wait_for_selector:
                wait = WebDriverWait(self.selenium_driver, site.wait_timeout)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, site.wait_for_selector)))
            else:
                # Default wait for page load
                time.sleep(3)
            
            # Get page source
            html = self.selenium_driver.page_source
            
            return BeautifulSoup(html, 'html.parser')
            
        except Exception as e:
            self.logger.error("Selenium scraping failed", error=str(e))
            raise
        except requests.RequestException as e:
            self.logger.error(
                "Failed to fetch site",
                site=site.name,
                error=str(e)
            )
            return []
        except Exception as e:
            self.logger.error(
                "Error checking site",
                site=site.name,
                error=str(e)
            )
            return []
    
    def check_all_sites(self) -> Dict[str, List[Dict[str, Any]]]:
        """Check all monitored sites.
        
        Returns:
            Dictionary mapping site names to discovered RFPs
        """
        results = {}
        
        for site in self.monitored_sites:
            rfps = self.check_site(site)
            results[site.name] = rfps
        
        total_rfps = sum(len(rfps) for rfps in results.values())
        self.logger.info(
            "All sites checked",
            sites=len(self.monitored_sites),
            total_rfps=total_rfps
        )
        
        return results
    
    def _extract_rfps(self, soup: BeautifulSoup, site: MonitoredSite) -> List[Dict[str, Any]]:
        """Extract RFP information from parsed HTML.
        
        Args:
            soup: BeautifulSoup object
            site: MonitoredSite configuration
            
        Returns:
            List of RFP dictionaries
        """
        rfps = []
        
        # Use site-specific selectors or fallback to generic
        if site.rfp_list_selector:
            containers = soup.select(site.rfp_list_selector)
        else:
            # Fallback: look for common patterns
            containers = soup.find_all(['div', 'tr', 'li'], class_=re.compile(r'(tender|rfp|opportunity)', re.I))
        
        for container in containers:
            try:
                rfp_data = self._parse_rfp_container(container, site)
                
                if rfp_data and self._passes_filters(rfp_data, site):
                    rfps.append(rfp_data)
                    
            except Exception as e:
                self.logger.debug(
                    "Failed to parse RFP container",
                    error=str(e)
                )
        
        return rfps
    
    def _parse_rfp_container(self, container, site: MonitoredSite) -> Optional[Dict[str, Any]]:
        """Parse individual RFP container.
        
        Args:
            container: BeautifulSoup element
            site: MonitoredSite configuration
            
        Returns:
            RFP data dictionary or None
        """
        # Extract link
        link_elem = container.select_one(site.rfp_link_selector) if site.rfp_link_selector else container.find('a')
        if not link_elem:
            return None
        
        url = link_elem.get('href', '')
        if not url:
            return None
        
        # Make URL absolute
        if url.startswith('/'):
            from urllib.parse import urljoin
            url = urljoin(site.url, url)
        
        # Extract title
        if site.title_selector:
            title_elem = container.select_one(site.title_selector)
            title = title_elem.get_text(strip=True) if title_elem else link_elem.get_text(strip=True)
        else:
            title = link_elem.get_text(strip=True)
        
        # Extract date if available
        published_date = None
        if site.date_selector:
            date_elem = container.select_one(site.date_selector)
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                published_date = self._parse_date(date_text)
        
        return {
            'url': url,
            'title': title,
            'published_date': published_date,
            'source_site': site.name,
            'discovered_at': datetime.now().isoformat()
        }
    
    def _passes_filters(self, rfp_data: Dict[str, Any], site: MonitoredSite) -> bool:
        """Check if RFP passes keyword filters.
        
        Args:
            rfp_data: RFP data dictionary
            site: MonitoredSite configuration
            
        Returns:
            True if RFP passes filters
        """
        title_lower = rfp_data['title'].lower()
        
        # Check include keywords
        if site.keywords:
            if not any(keyword.lower() in title_lower for keyword in site.keywords):
                return False
        
        # Check exclude keywords
        if site.exclude_keywords:
            if any(keyword.lower() in title_lower for keyword in site.exclude_keywords):
                return False
        
        return True
    
    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """Parse date from text.
        
        Args:
            date_text: Date string
            
        Returns:
            datetime object or None
        """
        # Try common date formats
        formats = [
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%Y-%m-%d',
            '%d %b %Y',
            '%d %B %Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_text, fmt)
            except ValueError:
                continue
        
        return None
