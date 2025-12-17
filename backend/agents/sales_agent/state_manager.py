"""
State Management - Persistent agent state.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import os
import structlog

logger = structlog.get_logger()


@dataclass
class AgentStateData:
    """Agent state data."""
    agent_id: str
    status: str
    started_at: Optional[datetime] = None
    last_cycle_at: Optional[datetime] = None
    
    # Statistics
    total_cycles: int = 0
    total_discovered: int = 0
    total_relevant: int = 0
    total_processed: int = 0
    workflows_triggered: int = 0
    bids_generated: int = 0
    
    # Recent data
    recent_opportunities: List[Dict[str, Any]] = None
    active_workflows: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize defaults."""
        if self.recent_opportunities is None:
            self.recent_opportunities = []
        if self.active_workflows is None:
            self.active_workflows = []


class StateManager:
    """Manage and persist agent state."""
    
    def __init__(self, state_dir: str = "data/agent_state"):
        """Initialize state manager.
        
        Args:
            state_dir: Directory for state files
        """
        self.logger = logger.bind(component="StateManager")
        self.state_dir = state_dir
        self.state_file = os.path.join(state_dir, "agent_state.json")
        self.opportunities_file = os.path.join(state_dir, "opportunities.json")
        self.workflows_file = os.path.join(state_dir, "workflows.json")
        
        # Create directory
        os.makedirs(state_dir, exist_ok=True)
        
        self.logger.info("State manager initialized", state_dir=state_dir)
    
    def save_state(self, state_data: AgentStateData):
        """Save agent state to disk.
        
        Args:
            state_data: Agent state to save
        """
        try:
            # Convert to dict
            state_dict = asdict(state_data)
            
            # Convert datetime objects
            if state_data.started_at:
                state_dict['started_at'] = state_data.started_at.isoformat()
            if state_data.last_cycle_at:
                state_dict['last_cycle_at'] = state_data.last_cycle_at.isoformat()
            
            # Save to file
            with open(self.state_file, 'w') as f:
                json.dump(state_dict, f, indent=2)
            
            self.logger.debug("State saved", agent_id=state_data.agent_id)
            
        except Exception as e:
            self.logger.error("Failed to save state", error=str(e))
    
    def load_state(self, agent_id: str) -> Optional[AgentStateData]:
        """Load agent state from disk.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            AgentStateData or None
        """
        try:
            if not os.path.exists(self.state_file):
                return None
            
            with open(self.state_file, 'r') as f:
                state_dict = json.load(f)
            
            # Check agent ID
            if state_dict.get('agent_id') != agent_id:
                return None
            
            # Convert datetime strings
            if state_dict.get('started_at'):
                state_dict['started_at'] = datetime.fromisoformat(state_dict['started_at'])
            if state_dict.get('last_cycle_at'):
                state_dict['last_cycle_at'] = datetime.fromisoformat(state_dict['last_cycle_at'])
            
            state_data = AgentStateData(**state_dict)
            
            self.logger.info("State loaded", agent_id=agent_id)
            return state_data
            
        except Exception as e:
            self.logger.error("Failed to load state", error=str(e))
            return None
    
    def save_opportunities(self, opportunities: List[Dict[str, Any]]):
        """Save opportunities to disk.
        
        Args:
            opportunities: List of opportunity dicts
        """
        try:
            with open(self.opportunities_file, 'w') as f:
                json.dump(opportunities, f, indent=2)
            
            self.logger.debug("Opportunities saved", count=len(opportunities))
            
        except Exception as e:
            self.logger.error("Failed to save opportunities", error=str(e))
    
    def load_opportunities(self) -> List[Dict[str, Any]]:
        """Load opportunities from disk.
        
        Returns:
            List of opportunity dicts
        """
        try:
            if not os.path.exists(self.opportunities_file):
                return []
            
            with open(self.opportunities_file, 'r') as f:
                opportunities = json.load(f)
            
            self.logger.debug("Opportunities loaded", count=len(opportunities))
            return opportunities
            
        except Exception as e:
            self.logger.error("Failed to load opportunities", error=str(e))
            return []
    
    def save_workflows(self, workflows: List[Dict[str, Any]]):
        """Save workflows to disk.
        
        Args:
            workflows: List of workflow dicts
        """
        try:
            with open(self.workflows_file, 'w') as f:
                json.dump(workflows, f, indent=2)
            
            self.logger.debug("Workflows saved", count=len(workflows))
            
        except Exception as e:
            self.logger.error("Failed to save workflows", error=str(e))
    
    def load_workflows(self) -> List[Dict[str, Any]]:
        """Load workflows from disk.
        
        Returns:
            List of workflow dicts
        """
        try:
            if not os.path.exists(self.workflows_file):
                return []
            
            with open(self.workflows_file, 'r') as f:
                workflows = json.load(f)
            
            self.logger.debug("Workflows loaded", count=len(workflows))
            return workflows
            
        except Exception as e:
            self.logger.error("Failed to load workflows", error=str(e))
            return []
    
    def reset_state(self, agent_id: str):
        """Reset agent state.
        
        Args:
            agent_id: Agent ID
        """
        try:
            # Remove state files
            if os.path.exists(self.state_file):
                os.remove(self.state_file)
            if os.path.exists(self.opportunities_file):
                os.remove(self.opportunities_file)
            if os.path.exists(self.workflows_file):
                os.remove(self.workflows_file)
            
            self.logger.info("State reset", agent_id=agent_id)
            
        except Exception as e:
            self.logger.error("Failed to reset state", error=str(e))
    
    def archive_opportunities(self, opportunities: List[Dict[str, Any]]):
        """Archive old opportunities.
        
        Args:
            opportunities: List of opportunities to archive
        """
        try:
            archive_file = os.path.join(
                self.state_dir,
                f"opportunities_archive_{datetime.now().strftime('%Y%m%d')}.json"
            )
            
            # Load existing archive
            existing = []
            if os.path.exists(archive_file):
                with open(archive_file, 'r') as f:
                    existing = json.load(f)
            
            # Append new opportunities
            existing.extend(opportunities)
            
            # Save archive
            with open(archive_file, 'w') as f:
                json.dump(existing, f, indent=2)
            
            self.logger.info(
                "Opportunities archived",
                count=len(opportunities),
                archive_file=archive_file
            )
            
        except Exception as e:
            self.logger.error("Failed to archive opportunities", error=str(e))
