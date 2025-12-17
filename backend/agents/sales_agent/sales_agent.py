"""
Sales Agent - Main orchestration agent for RFP monitoring and processing.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import structlog

from agents.url_monitor_v2 import URLMonitor, MonitoredSite, ProxyPool
from agents.rfp_scraper import RFPScraper, ScrapedRFP
from agents.relevance_filter import RelevanceFilter, FilterCriteria
from agents.workflow_trigger import WorkflowTrigger, WorkflowStatus
from agents.scheduler import AgentScheduler, ScheduleConfig
from agents.alerting import AlertSystem, Alert, AlertChannel, AlertPriority
from agents.state_manager import StateManager, AgentStateData
from agents.dashboard import DashboardDataExporter
from agents.rfp_summarizer import RFPSummarizer, RFPSummary
from agents.config_reloader import ConfigReloader
from agents.health_api import HealthAPI

logger = structlog.get_logger()


class AgentState(Enum):
    """Agent operational states."""
    IDLE = "idle"
    MONITORING = "monitoring"
    SCRAPING = "scraping"
    FILTERING = "filtering"
    PROCESSING = "processing"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class AgentConfig:
    """Configuration for Sales Agent."""
    # Monitoring settings
    monitored_sites: List[MonitoredSite] = field(default_factory=list)
    check_interval_minutes: int = 60
    
    # Filter settings
    filter_criteria: Optional[FilterCriteria] = None
    min_relevance_score: float = 0.6
    
    # Alert settings
    alert_channels: List[AlertChannel] = field(default_factory=list)
    alert_on_new_rfp: bool = True
    alert_on_high_value: bool = True
    high_value_threshold: float = 1000000.0  # INR
    
    # Workflow settings
    auto_trigger_workflow: bool = True
    auto_generate_bid: bool = False
    
    # Agent settings
    agent_name: str = "SalesAgent-001"
    max_concurrent_scrapes: int = 5
    retry_attempts: int = 3
    
    # Storage
    state_file: str = "./agent_state.json"
    rfp_archive_dir: str = "./rfp_archive"


@dataclass
class RFPOpportunity:
    """Discovered RFP opportunity."""
    opportunity_id: str
    source_url: str
    title: str
    organization: str
    tender_number: str
    
    # Dates
    published_date: Optional[datetime] = None
    submission_deadline: Optional[datetime] = None
    discovered_date: datetime = field(default_factory=datetime.now)
    
    # Content
    description: str = ""
    estimated_value: Optional[float] = None
    categories: List[str] = field(default_factory=list)
    
    # Analysis
    relevance_score: float = 0.0
    relevance_reasons: List[str] = field(default_factory=list)
    
    # Status
    status: str = "discovered"  # discovered, filtered, processing, completed, rejected
    workflow_triggered: bool = False
    bid_generated: bool = False
    
    # Scraped data
    scraped_rfp: Optional[ScrapedRFP] = None
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'opportunity_id': self.opportunity_id,
            'source_url': self.source_url,
            'title': self.title,
            'organization': self.organization,
            'tender_number': self.tender_number,
            'published_date': self.published_date.isoformat() if self.published_date else None,
            'submission_deadline': self.submission_deadline.isoformat() if self.submission_deadline else None,
            'discovered_date': self.discovered_date.isoformat(),
            'description': self.description,
            'estimated_value': self.estimated_value,
            'categories': self.categories,
            'relevance_score': self.relevance_score,
            'relevance_reasons': self.relevance_reasons,
            'status': self.status,
            'workflow_triggered': self.workflow_triggered,
            'bid_generated': self.bid_generated,
            'tags': self.tags,
            'notes': self.notes
        }


class SalesAgent:
    """
    Main Sales Agent for RFP monitoring and workflow automation.
    
    Responsibilities:
    1. Monitor configured URLs for RFP announcements
    2. Scrape RFP details from discovered opportunities
    3. Filter opportunities based on relevance
    4. Trigger workflow for qualified opportunities
    5. Send alerts for important events
    6. Maintain agent state and history
    """
    
    def __init__(self, config: AgentConfig, proxy_pool: Optional[ProxyPool] = None,
                 use_selenium: bool = False, config_file: Optional[str] = None,
                 enable_health_api: bool = False, health_api_port: int = 5000):
        """Initialize Sales Agent.
        
        Args:
            config: Agent configuration
            proxy_pool: Optional proxy pool for scraping
            use_selenium: Whether to use Selenium for dynamic pages
            config_file: Optional path to config file for hot reload
            enable_health_api: Whether to start health check API
            health_api_port: Port for health API
        """
        self.config = config
        self.state = AgentState.IDLE
        self.logger = logger.bind(component="SalesAgent", agent=config.agent_name)
        
        # Initialize components with advanced features
        self.url_monitor = URLMonitor(
            proxy_pool=proxy_pool,
            use_selenium=use_selenium
        )
        self.scraper = RFPScraper()
        self.relevance_filter = RelevanceFilter(
            min_score=config.min_relevance_score
        )
        self.workflow_trigger = WorkflowTrigger()
        self.alert_system = AlertSystem()
        self.scheduler = AgentScheduler()
        self.state_manager = StateManager()
        self.dashboard_exporter = DashboardDataExporter(self)
        
        # NEW: RFP Summarizer with NLP
        self.summarizer = RFPSummarizer(use_transformers=False)  # Can enable transformers if installed
        
        # NEW: Config reloader for hot reload
        self.config_reloader = None
        if config_file:
            self.config_reloader = ConfigReloader(config_file)
            self.config_reloader.register_callback(self._on_config_updated)
            self.config_reloader.start_watching()
        
        # NEW: Health API for monitoring
        self.health_api = None
        if enable_health_api:
            self.health_api = HealthAPI(port=health_api_port)
            self._register_health_callbacks()
            self.health_api.run_background()
        
        # State management
        self.opportunities: List[RFPOpportunity] = []
        self.summaries: List[RFPSummary] = []  # NEW: Store RFP summaries
        self.processed_urls: set = set()
        self.statistics = {
            'total_discovered': 0,
            'total_relevant': 0,
            'total_processed': 0,
            'total_workflows_triggered': 0,
            'total_bids_generated': 0,
            'total_summaries': 0,  # NEW
            'last_run': None,
            'errors': 0
        }
        
        # Configure alert channels
        for channel in config.alert_channels:
            from agents.alerting import ChannelConfig
            self.alert_system.configure_channel(
                ChannelConfig(channel=channel, enabled=True)
            )
        
        # Add monitored sites
        for site in config.monitored_sites:
            self.url_monitor.add_site(site)
        
        # Load saved state
        saved_state = self.state_manager.load_state(config.agent_name)
        if saved_state:
            self.statistics = {
                'total_discovered': saved_state.total_discovered,
                'total_relevant': saved_state.total_relevant,
                'total_processed': saved_state.total_processed,
                'total_workflows_triggered': saved_state.workflows_triggered,
                'total_bids_generated': saved_state.bids_generated,
                'last_run': saved_state.last_cycle_at,
                'errors': 0
            }
            self.logger.info("Loaded saved state", statistics=self.statistics)
        
        self.logger.info("Sales agent initialized", sites=len(config.monitored_sites))
    
    def start(self):
        """Start the sales agent."""
        self.logger.info("Starting sales agent")
        self.state = AgentState.MONITORING
        
        # Schedule monitoring tasks
        schedule = ScheduleConfig(
            task_id="monitor_rfps",
            interval_minutes=self.config.check_interval_minutes,
            task_name="RFP Monitoring"
        )
        
        self.scheduler.add_schedule(schedule, self.run_monitoring_cycle)
        self.scheduler.start()
        
        # Send startup alert
        alert_id = f"ALERT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.alert_system.send_alert(Alert(
            alert_id=alert_id,
            title="Sales Agent Started",
            message=f"Agent {self.config.agent_name} is now monitoring {len(self.config.monitored_sites)} sites",
            priority=AlertPriority.MEDIUM,
            channels=[AlertChannel.CONSOLE]
        ))
        
        # Save initial state
        self._save_state()
        
        self.logger.info("Sales agent started successfully")
    
    def stop(self):
        """Stop the sales agent."""
        self.logger.info("Stopping sales agent")
        self.state = AgentState.STOPPED
        
        self.scheduler.stop()
        
        # Save state before stopping
        self._save_state()
        
        # Send shutdown alert
        alert_id = f"ALERT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.alert_system.send_alert(Alert(
            alert_id=alert_id,
            title="Sales Agent Stopped",
            message=f"Agent {self.config.agent_name} has been stopped",
            priority=AlertPriority.MEDIUM,
            channels=[AlertChannel.CONSOLE]
        ))
        
        self.logger.info("Sales agent stopped")
    
    def run_monitoring_cycle(self):
        """Run one complete monitoring cycle."""
        self.logger.info("Starting monitoring cycle")
        cycle_start = datetime.now()
        
        try:
            # Phase 1: Monitor URLs for new RFPs
            self.state = AgentState.MONITORING
            new_rfps = self._monitor_urls()
            self.logger.info("URL monitoring completed", new_rfps=len(new_rfps))
            
            # Phase 2: Scrape RFP details
            if new_rfps:
                self.state = AgentState.SCRAPING
                scraped_opportunities = self._scrape_rfps(new_rfps)
                self.logger.info("RFP scraping completed", scraped=len(scraped_opportunities))
                
                # Phase 3: Filter relevant opportunities
                self.state = AgentState.FILTERING
                relevant_opportunities = self._filter_opportunities(scraped_opportunities)
                self.logger.info("Relevance filtering completed", relevant=len(relevant_opportunities))
                
                # Phase 4: Process relevant opportunities
                if relevant_opportunities:
                    self.state = AgentState.PROCESSING
                    self._process_opportunities(relevant_opportunities)
                    
                    # Send summary alert
                    if self.config.alert_on_new_rfp:
                        self._send_discovery_alert(relevant_opportunities)
            
            # Update statistics
            self.statistics['last_run'] = datetime.now().isoformat()
            self.state = AgentState.IDLE
            
            cycle_duration = (datetime.now() - cycle_start).total_seconds()
            self.logger.info(
                "Monitoring cycle completed",
                duration_seconds=cycle_duration,
                new_opportunities=len(new_rfps) if new_rfps else 0
            )
            
        except Exception as e:
            self.state = AgentState.ERROR
            self.statistics['errors'] += 1
            self.logger.error("Monitoring cycle failed", error=str(e))
            
            # Send error alert
            alert_id = f"ALERT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            self.alert_system.send_alert(Alert(
                alert_id=alert_id,
                title="Sales Agent Error",
                message=f"Monitoring cycle failed: {str(e)}",
                priority=AlertPriority.HIGH,
                channels=self.config.alert_channels
            ))
        
        finally:
            # Save state after each cycle
            self._save_state()
    
    def _monitor_urls(self) -> List[Dict[str, Any]]:
        """Monitor configured URLs for new RFPs."""
        self.logger.info("Monitoring URLs for new RFPs")
        
        new_rfps = []
        
        for site in self.config.monitored_sites:
            try:
                rfps = self.url_monitor.check_site(site)
                
                # Filter out already processed URLs
                for rfp in rfps:
                    if rfp['url'] not in self.processed_urls:
                        new_rfps.append(rfp)
                        self.processed_urls.add(rfp['url'])
                
                self.logger.debug(
                    "Site monitored",
                    site=site.name,
                    new_rfps=len(rfps)
                )
                
            except Exception as e:
                self.logger.error(
                    "Failed to monitor site",
                    site=site.name,
                    error=str(e)
                )
        
        self.statistics['total_discovered'] += len(new_rfps)
        return new_rfps
    
    def _scrape_rfps(self, rfp_list: List[Dict[str, Any]]) -> List[RFPOpportunity]:
        """Scrape detailed information from RFP URLs."""
        self.logger.info("Scraping RFP details", count=len(rfp_list))
        
        opportunities = []
        
        for rfp_data in rfp_list:
            try:
                # Scrape RFP details
                scraped = self.scraper.scrape_rfp(rfp_data['url'])
                
                # Create opportunity object
                opportunity = RFPOpportunity(
                    opportunity_id=f"OPP-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{len(opportunities)}",
                    source_url=rfp_data['url'],
                    title=scraped.title or rfp_data.get('title', 'Unknown'),
                    organization=scraped.organization or 'Unknown',
                    tender_number=scraped.tender_number or '',
                    published_date=scraped.published_date,
                    submission_deadline=scraped.submission_deadline,
                    description=scraped.description,
                    estimated_value=scraped.estimated_value,
                    categories=scraped.categories,
                    scraped_rfp=scraped
                )
                
                opportunities.append(opportunity)
                
                self.logger.debug(
                    "RFP scraped successfully",
                    opportunity_id=opportunity.opportunity_id,
                    title=opportunity.title
                )
                
            except Exception as e:
                self.logger.error(
                    "Failed to scrape RFP",
                    url=rfp_data['url'],
                    error=str(e)
                )
        
        return opportunities
    
    def _filter_opportunities(self, opportunities: List[RFPOpportunity]) -> List[RFPOpportunity]:
        """Filter opportunities based on relevance."""
        self.logger.info("Filtering opportunities", count=len(opportunities))
        
        relevant = []
        
        for opp in opportunities:
            try:
                # Apply relevance filter
                is_relevant, score, reasons = self.relevance_filter.filter_opportunity(
                    title=opp.title,
                    description=opp.description,
                    categories=opp.categories,
                    estimated_value=opp.estimated_value,
                    criteria=self.config.filter_criteria
                )
                
                opp.relevance_score = score
                opp.relevance_reasons = reasons
                
                if is_relevant:
                    opp.status = "relevant"
                    relevant.append(opp)
                    self.logger.info(
                        "Relevant opportunity found",
                        opportunity_id=opp.opportunity_id,
                        score=score,
                        title=opp.title[:50]
                    )
                else:
                    opp.status = "rejected"
                    self.logger.debug(
                        "Opportunity filtered out",
                        opportunity_id=opp.opportunity_id,
                        score=score
                    )
                
                # Store all opportunities
                self.discovered_opportunities.append(opp)
                
            except Exception as e:
                self.logger.error(
                    "Failed to filter opportunity",
                    opportunity_id=opp.opportunity_id,
                    error=str(e)
                )
        
        self.statistics['total_relevant'] += len(relevant)
        return relevant
    
    def _process_opportunities(self, opportunities: List[RFPOpportunity]):
        """Process relevant opportunities."""
        self.logger.info("Processing opportunities", count=len(opportunities))
        
        for opp in opportunities:
            try:
                opp.status = "processing"
                
                # Trigger workflow if enabled
                if self.config.auto_trigger_workflow:
                    workflow_status = self.workflow_trigger.trigger(
                        opportunity=opp,
                        auto_generate_bid=self.config.auto_generate_bid
                    )
                    
                    opp.workflow_triggered = workflow_status.triggered
                    opp.status = workflow_status.status
                    
                    if workflow_status.triggered:
                        self.statistics['total_workflows_triggered'] += 1
                        
                        if workflow_status.bid_generated:
                            opp.bid_generated = True
                            self.statistics['total_bids_generated'] += 1
                    
                    self.logger.info(
                        "Workflow triggered",
                        opportunity_id=opp.opportunity_id,
                        status=workflow_status.status
                    )
                
                # Send high-value alert
                if (self.config.alert_on_high_value and 
                    opp.estimated_value and 
                    opp.estimated_value >= self.config.high_value_threshold):
                    self._send_high_value_alert(opp)
                
                self.statistics['total_processed'] += 1
                
            except Exception as e:
                opp.status = "error"
                self.logger.error(
                    "Failed to process opportunity",
                    opportunity_id=opp.opportunity_id,
                    error=str(e)
                )
    
    def _send_discovery_alert(self, opportunities: List[RFPOpportunity]):
        """Send alert for newly discovered opportunities."""
        summary = f"Discovered {len(opportunities)} relevant RFP opportunities:\n\n"
        
        for i, opp in enumerate(opportunities[:5], 1):  # Top 5
            summary += f"{i}. {opp.title}\n"
            summary += f"   Organization: {opp.organization}\n"
            summary += f"   Relevance: {opp.relevance_score:.2f}\n"
            if opp.estimated_value:
                summary += f"   Value: INR {opp.estimated_value:,.0f}\n"
            summary += f"   Deadline: {opp.submission_deadline.strftime('%Y-%m-%d') if opp.submission_deadline else 'TBD'}\n\n"
        
        if len(opportunities) > 5:
            summary += f"... and {len(opportunities) - 5} more opportunities"
        
        alert_id = f"ALERT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.alert_system.send_alert(Alert(
            alert_id=alert_id,
            title=f"🎯 {len(opportunities)} New RFP Opportunities",
            message=summary,
            priority=AlertPriority.MEDIUM,
            channels=self.config.alert_channels
        ))
    
    def _send_high_value_alert(self, opportunity: RFPOpportunity):
        """Send alert for high-value opportunity."""
        message = f"""
High-Value RFP Opportunity Detected!

Title: {opportunity.title}
Organization: {opportunity.organization}
Estimated Value: INR {opportunity.estimated_value:,.0f}
Relevance Score: {opportunity.relevance_score:.2f}
Deadline: {opportunity.submission_deadline.strftime('%Y-%m-%d') if opportunity.submission_deadline else 'TBD'}

URL: {opportunity.source_url}

Reasons for relevance:
"""
        for reason in opportunity.relevance_reasons:
            message += f"• {reason}\n"
        
        alert_id = f"ALERT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.alert_system.send_alert(Alert(
            alert_id=alert_id,
            title=f"💰 High-Value RFP: {opportunity.title[:50]}",
            message=message,
            priority=AlertPriority.HIGH,
            channels=self.config.alert_channels
        ))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get agent statistics."""
        return {
            **self.statistics,
            'state': self.state.value,
            'monitored_sites': len(self.config.monitored_sites),
            'discovered_opportunities': len(self.opportunities),
            'processed_urls': len(self.processed_urls)
        }
    
    def get_recent_opportunities(self, limit: int = 10) -> List[RFPOpportunity]:
        """Get recent opportunities."""
        sorted_opps = sorted(
            self.opportunities,
            key=lambda x: x.discovered_date,
            reverse=True
        )
        return sorted_opps[:limit]
    
    def get_relevant_opportunities(self, limit: int = 10) -> List[RFPOpportunity]:
        """Get relevant opportunities sorted by score."""
        relevant = [opp for opp in self.opportunities if opp.status == "relevant"]
        sorted_opps = sorted(relevant, key=lambda x: x.relevance_score, reverse=True)
        return sorted_opps[:limit]
    
    def _save_state(self):
        """Save current agent state."""
        state_data = AgentStateData(
            agent_id=self.config.agent_name,
            status=self.state.value,
            started_at=datetime.fromisoformat(self.statistics['last_run']) if self.statistics.get('last_run') else None,
            last_cycle_at=datetime.now(),
            total_cycles=self.statistics.get('total_cycles', 0),
            total_discovered=self.statistics['total_discovered'],
            total_relevant=self.statistics['total_relevant'],
            total_processed=self.statistics['total_processed'],
            workflows_triggered=self.statistics['total_workflows_triggered'],
            bids_generated=self.statistics['total_bids_generated'],
            recent_opportunities=[opp.to_dict() for opp in self.get_recent_opportunities(limit=50)],
            active_workflows=[w['result'].to_dict() for w in self.workflow_trigger.get_active_workflows()]
        )
        
        self.state_manager.save_state(state_data)
        self.state_manager.save_opportunities([opp.to_dict() for opp in self.opportunities])
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard."""
        return self.dashboard_exporter.export_full_dashboard()
    
    def _on_config_updated(self, new_config: Dict[str, Any]):
        """Handle configuration update.
        
        Args:
            new_config: New configuration dictionary
        """
        self.logger.info("Configuration updated, applying changes")
        
        # Update monitoring interval
        if 'monitoring' in new_config and 'interval' in new_config['monitoring']:
            self.config.check_interval_minutes = new_config['monitoring']['interval']
            self.logger.info("Updated monitoring interval", 
                           interval=self.config.check_interval_minutes)
        
        # Update filtering settings
        if 'filtering' in new_config:
            if 'min_relevance_score' in new_config['filtering']:
                self.config.min_relevance_score = new_config['filtering']['min_relevance_score']
                self.relevance_filter.min_score = self.config.min_relevance_score
                self.logger.info("Updated min relevance score", 
                               score=self.config.min_relevance_score)
        
        # Update alerting settings
        if 'alerting' in new_config:
            if 'min_alert_score' in new_config['alerting']:
                # Update alert thresholds
                pass
        
        # Update Selenium settings
        if 'selenium' in new_config:
            if 'enabled' in new_config['selenium']:
                self.url_monitor.use_selenium = new_config['selenium']['enabled']
                if new_config['selenium']['enabled'] and not self.url_monitor.selenium_driver:
                    self.url_monitor._init_selenium()
        
        # Update proxy settings
        if 'proxy' in new_config and 'proxies' in new_config['proxy']:
            if self.url_monitor.proxy_pool:
                self.url_monitor.proxy_pool.proxies = new_config['proxy']['proxies']
                self.url_monitor.proxy_pool.current_index = 0
        
        self.logger.info("Configuration update complete")
    
    def _register_health_callbacks(self):
        """Register health check callbacks."""
        if not self.health_api:
            return
        
        # Agent status callback
        def agent_status():
            return {
                'status': self.state.value,
                'uptime_seconds': (datetime.now() - datetime.fromisoformat(
                    self.statistics['last_run'])).total_seconds() if self.statistics.get('last_run') else 0,
                'metrics': {
                    'total_discovered': self.statistics['total_discovered'],
                    'total_relevant': self.statistics['total_relevant'],
                    'total_processed': self.statistics['total_processed'],
                    'total_workflows': self.statistics['total_workflows_triggered'],
                    'total_summaries': self.statistics.get('total_summaries', 0),
                    'errors': self.statistics['errors']
                }
            }
        
        # URL monitor status
        def monitor_status():
            return {
                'status': 'active' if self.state in [AgentState.MONITORING, AgentState.SCRAPING] else 'idle',
                'metrics': {
                    'monitored_sites': len(self.config.monitored_sites),
                    'processed_urls': len(self.processed_urls),
                    'duplicate_cache_size': len(self.url_monitor.seen_rfp_hashes) if hasattr(self.url_monitor, 'seen_rfp_hashes') else 0
                }
            }
        
        # Workflow status
        def workflow_status():
            active = self.workflow_trigger.get_active_workflows()
            return {
                'status': 'active' if active else 'idle',
                'metrics': {
                    'active_workflows': len(active),
                    'total_triggered': self.statistics['total_workflows_triggered']
                }
            }
        
        # Control callback
        def control_handler(action_data):
            action = action_data.get('action')
            if action == 'start':
                if self.state == AgentState.STOPPED:
                    self.start()
                return {'status': 'started', 'state': self.state.value}
            elif action == 'stop':
                self.stop()
                return {'status': 'stopped', 'state': self.state.value}
            elif action == 'check':
                self.run_monitoring_cycle()
                return {'status': 'check_completed', 'discoveries': self.statistics['total_discovered']}
            return {'error': 'Unknown action'}
        
        # Register all callbacks
        self.health_api.register_status_callback('agent', agent_status)
        self.health_api.register_status_callback('monitor', monitor_status)
        self.health_api.register_status_callback('workflow', workflow_status)
        self.health_api.register_status_callback('control', control_handler)
        
        self.logger.info("Health API callbacks registered")
    
    def generate_rfp_summary(self, scraped_rfp: ScrapedRFP) -> RFPSummary:
        """Generate NLP summary for an RFP.
        
        Args:
            scraped_rfp: ScrapedRFP object
            
        Returns:
            RFPSummary object
        """
        summary = self.summarizer.generate_summary(scraped_rfp)
        self.summaries.append(summary)
        self.statistics['total_summaries'] = len(self.summaries)
        
        self.logger.info("Generated RFP summary", 
                       rfp_id=summary.rfp_id, 
                       opportunity_score=summary.opportunity_score)
        
        return summary
    
    def get_summary_comparison(self, limit: int = 10) -> Dict[str, Any]:
        """Get comparison report for recent RFP summaries.
        
        Args:
            limit: Maximum number of summaries to compare
            
        Returns:
            Comparison dictionary
        """
        recent_summaries = self.summaries[-limit:]
        return self.summarizer.generate_comparison(recent_summaries)
