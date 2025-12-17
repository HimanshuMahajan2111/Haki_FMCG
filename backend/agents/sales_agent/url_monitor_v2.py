"""
URL Monitor V2 - Complete implementation with all features.
Includes: Selenium, proxy rotation, duplicate detection, retry logic.
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
    rfp_list_selector: str = ""
    rfp_link_selector: str = "a"
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
    auth_type: str = "none"
    auth_credentials: Dict[str, str] = None
    
    # Rate limiting
    rate_limit_seconds: int = 2
    
    # Selenium support (NEW)
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


class ProxyPool:
    """Manage proxy rotation (NEW)."""
    
    def __init__(self, proxies: List[str] = None):
        """Initialize proxy pool.
        
        Args:
            proxies: List of proxy URLs
        """
        self.proxies = proxies or []
        self.current_index = 0
        self.failed_proxies = set()
        
    def get_next_proxy(self) -> Optional[Dict[str, str]]:
        """Get next working proxy."""
        if not self.proxies:
            return None
        
        attempts = 0
        max_attempts = len(self.proxies)
        
        while attempts < max_attempts:
            proxy = self.proxies[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxies)
            
            if proxy not in self.failed_proxies:
                return {'http': proxy, 'https': proxy}
            
            attempts += 1
        
        return None
    
    def mark_failed(self, proxy: str):
        """Mark proxy as failed."""
        self.failed_proxies.add(proxy)
    
    def reset_failed(self):
        """Reset failed proxies."""
        self.failed_proxies.clear()


class URLMonitor:
    """Monitor URLs for new RFP announcements with full features."""
    
    def __init__(self, proxy_pool: Optional[ProxyPool] = None, use_selenium: bool = False):
        """Initialize URL monitor.
        
        Args:
            proxy_pool: Optional proxy pool for rotation
            use_selenium: Whether to use Selenium for dynamic pages
        """
        self.logger = logger.bind(component="URLMonitor")
        self.monitored_sites: Dict[str, MonitoredSite] = {}
        self.proxy_pool = proxy_pool
        self.use_selenium_global = use_selenium
        self.selenium_driver = None
        self.seen_rfp_hashes = set()  # For duplicate detection
        
        # Initialize Selenium if requested
        if use_selenium:
            self._init_selenium()
        
        self.logger.info(
            "URL monitor initialized",
            use_selenium=use_selenium,
            has_proxies=proxy_pool is not None
        )
    
    def _init_selenium(self):
        """Initialize Selenium WebDriver."""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            self.selenium_driver = webdriver.Chrome(options=options)
            self.logger.info("Selenium WebDriver initialized")
        except Exception as e:
            self.logger.error("Failed to initialize Selenium", error=str(e))
            self.selenium_driver = None
    
    def _generate_rfp_hash(self, rfp: Dict[str, Any]) -> str:
        """Generate hash for duplicate detection.
        
        Args:
            rfp: RFP dictionary
            
        Returns:
            MD5 hash string
        """
        content = f"{rfp.get('title', '')}|{rfp.get('url', '')}|{rfp.get('date', '')}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _is_duplicate(self, rfp: Dict[str, Any]) -> bool:
        """Check if RFP is duplicate.
        
        Args:
            rfp: RFP dictionary
            
        Returns:
            True if duplicate
        """
        rfp_hash = self._generate_rfp_hash(rfp)
        if rfp_hash in self.seen_rfp_hashes:
            return True
        self.seen_rfp_hashes.add(rfp_hash)
        return False
    
    def add_site(self, site: MonitoredSite):
        """Add site to monitoring."""
        self.monitored_sites[site.name] = site
        self.logger.info("Site added to monitoring", site=site.name)
    
    def remove_site(self, site_name: str):
        """Remove site from monitoring."""
        if site_name in self.monitored_sites:
            del self.monitored_sites[site_name]
            self.logger.info("Site removed from monitoring", site=site_name)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.RequestException, ConnectionError))
    )
    def check_site(self, site: MonitoredSite) -> List[Dict[str, Any]]:
        """Check site for new RFPs with retry logic.
        
        Args:
            site: MonitoredSite to check
            
        Returns:
            List of discovered RFPs
        """
        if not site.enabled:
            self.logger.debug("Site disabled, skipping", site=site.name)
            return []
        
        try:
            self.logger.info("Checking site for new RFPs", site=site.name)
            
            # Get proxy if available
            proxies = None
            proxy_url = None
            if self.proxy_pool:
                proxy_dict = self.proxy_pool.get_next_proxy()
                if proxy_dict:
                    proxies = proxy_dict
                    proxy_url = proxy_dict.get('http', '')
            
            # Use Selenium for dynamic pages or BeautifulSoup for static
            if site.use_selenium or self.use_selenium_global:
                soup = self._scrape_with_selenium(site)
            else:
                response = requests.get(site.url, timeout=30, proxies=proxies)
                response.raise_for_status()
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
            
            # Rate limiting
            time.sleep(site.rate_limit_seconds)
            
            return unique_rfps
            
        except requests.RequestException as e:
            # Mark proxy as failed
            if self.proxy_pool and proxy_url:
                self.proxy_pool.mark_failed(proxy_url)
                self.logger.warning("Marked proxy as failed", proxy=proxy_url)
            
            self.logger.error("Failed to check site", site=site.name, error=str(e))
            raise  # Re-raise for retry logic
            
        except Exception as e:
            self.logger.error("Unexpected error checking site", site=site.name, error=str(e))
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
                time.sleep(3)  # Default wait
            
            # Get rendered HTML
            html = self.selenium_driver.page_source
            
            return BeautifulSoup(html, 'html.parser')
            
        except Exception as e:
            self.logger.error("Selenium scraping failed", error=str(e))
            raise
    
    def check_all_sites(self) -> Dict[str, List[Dict[str, Any]]]:
        """Check all monitored sites."""
        results = {}
        
        for site_name, site in self.monitored_sites.items():
            try:
                rfps = self.check_site(site)
                results[site_name] = rfps
            except Exception as e:
                self.logger.error("Failed to check site", site=site_name, error=str(e))
                results[site_name] = []
        
        return results
    
    def _extract_rfps(self, soup: BeautifulSoup, site: MonitoredSite) -> List[Dict[str, Any]]:
        """Extract RFPs from HTML."""
        rfps = []
        
        try:
            # Find RFP containers
            if site.rfp_list_selector:
                containers = soup.select(site.rfp_list_selector)
            else:
                containers = soup.find_all('div', class_=re.compile('tender|rfp|notice', re.I))
            
            for container in containers:
                rfp = self._parse_rfp_container(container, site)
                if rfp and self._passes_filters(rfp, site):
                    rfps.append(rfp)
        
        except Exception as e:
            self.logger.error("Error extracting RFPs", error=str(e))
        
        return rfps
    
    def _parse_rfp_container(self, container, site: MonitoredSite) -> Optional[Dict[str, Any]]:
        """Parse individual RFP container."""
        try:
            # Extract link
            link_elem = container.select_one(site.rfp_link_selector) if site.rfp_link_selector else container.find('a')
            if not link_elem:
                return None
            
            url = link_elem.get('href', '')
            if not url.startswith('http'):
                from urllib.parse import urljoin
                url = urljoin(site.url, url)
            
            # Extract title
            title = ''
            if site.title_selector:
                title_elem = container.select_one(site.title_selector)
                title = title_elem.get_text(strip=True) if title_elem else ''
            else:
                title = link_elem.get_text(strip=True)
            
            # Extract date
            date_str = ''
            if site.date_selector:
                date_elem = container.select_one(site.date_selector)
                date_str = date_elem.get_text(strip=True) if date_elem else ''
            
            parsed_date = self._parse_date(date_str) if date_str else None
            
            return {
                'url': url,
                'title': title,
                'date': parsed_date,
                'site': site.name,
                'discovered_at': datetime.now()
            }
        
        except Exception as e:
            self.logger.debug("Error parsing RFP container", error=str(e))
            return None
    
    def _passes_filters(self, rfp: Dict[str, Any], site: MonitoredSite) -> bool:
        """Check if RFP passes keyword filters."""
        title = rfp.get('title', '').lower()
        
        # Check exclude keywords
        if site.exclude_keywords:
            for keyword in site.exclude_keywords:
                if keyword.lower() in title:
                    return False
        
        # Check required keywords
        if site.keywords:
            has_keyword = any(keyword.lower() in title for keyword in site.keywords)
            if not has_keyword:
                return False
        
        return True
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string."""
        date_formats = [
            '%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d',
            '%d %b %Y', '%d %B %Y', '%b %d, %Y', '%B %d, %Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except:
                continue
        
        return None
    
    def clear_duplicate_cache(self):
        """Clear duplicate detection cache."""
        self.seen_rfp_hashes.clear()
        self.logger.info("Duplicate cache cleared")
    
    def __del__(self):
        """Cleanup Selenium driver."""
        if self.selenium_driver:
            try:
                self.selenium_driver.quit()
            except:
                pass
