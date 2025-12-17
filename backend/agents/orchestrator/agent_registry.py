"""
Agent Registry System
Manages registration, discovery, and lifecycle of all agents in the system.
"""
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import structlog
from collections import defaultdict

logger = structlog.get_logger()


class AgentType(Enum):
    """Types of agents in the system."""
    SALES = "sales"
    TECHNICAL = "technical"
    PRICING = "pricing"
    MONITORING = "monitoring"
    ANALYSIS = "analysis"
    REPORTING = "reporting"
    CUSTOM = "custom"


class AgentCapability(Enum):
    """Agent capabilities."""
    RFP_ANALYSIS = "rfp_analysis"
    PRODUCT_MATCHING = "product_matching"
    PRICE_CALCULATION = "price_calculation"
    DOCUMENT_GENERATION = "document_generation"
    DATA_EXTRACTION = "data_extraction"
    QUALITY_CHECK = "quality_check"
    COMPLIANCE_VALIDATION = "compliance_validation"
    MARKET_ANALYSIS = "market_analysis"


@dataclass
class AgentMetadata:
    """Metadata for registered agents."""
    agent_id: str
    agent_name: str
    agent_type: AgentType
    version: str
    capabilities: List[AgentCapability]
    description: str
    registered_at: str
    last_health_check: Optional[str] = None
    is_active: bool = True
    is_healthy: bool = True
    execution_count: int = 0
    total_execution_time: float = 0.0
    error_count: int = 0
    success_rate: float = 100.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentRegistration:
    """Agent registration details."""
    metadata: AgentMetadata
    agent_instance: Any
    health_check_fn: Optional[Callable] = None
    priority: int = 100  # Lower = higher priority


class AgentRegistry:
    """
    Central registry for all agents in the system.
    
    Features:
    - Agent registration and deregistration
    - Agent discovery by type/capability
    - Health monitoring
    - Load balancing
    - Agent lifecycle management
    """
    
    def __init__(self):
        """Initialize agent registry."""
        self.logger = logger.bind(component="AgentRegistry")
        
        # Storage
        self._agents: Dict[str, AgentRegistration] = {}
        self._agents_by_type: Dict[AgentType, List[str]] = defaultdict(list)
        self._agents_by_capability: Dict[AgentCapability, List[str]] = defaultdict(list)
        
        # Statistics
        self.total_registrations = 0
        self.active_agents = 0
        
        self.logger.info("Agent Registry initialized")
    
    def register_agent(
        self,
        agent_instance: Any,
        agent_name: str,
        agent_type: AgentType,
        capabilities: List[AgentCapability],
        version: str = "1.0.0",
        description: str = "",
        health_check_fn: Optional[Callable] = None,
        priority: int = 100,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Register a new agent.
        
        Args:
            agent_instance: Agent instance
            agent_name: Agent name
            agent_type: Type of agent
            capabilities: List of capabilities
            version: Agent version
            description: Agent description
            health_check_fn: Optional health check function
            priority: Agent priority (lower = higher priority)
            metadata: Additional metadata
            
        Returns:
            Agent ID
        """
        # Generate agent ID
        agent_id = f"{agent_type.value}_{agent_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create metadata
        agent_metadata = AgentMetadata(
            agent_id=agent_id,
            agent_name=agent_name,
            agent_type=agent_type,
            version=version,
            capabilities=capabilities,
            description=description,
            registered_at=datetime.now().isoformat(),
            metadata=metadata or {}
        )
        
        # Create registration
        registration = AgentRegistration(
            metadata=agent_metadata,
            agent_instance=agent_instance,
            health_check_fn=health_check_fn,
            priority=priority
        )
        
        # Store registration
        self._agents[agent_id] = registration
        self._agents_by_type[agent_type].append(agent_id)
        
        for capability in capabilities:
            self._agents_by_capability[capability].append(agent_id)
        
        # Update statistics
        self.total_registrations += 1
        self.active_agents += 1
        
        self.logger.info(
            "Agent registered",
            agent_id=agent_id,
            agent_name=agent_name,
            agent_type=agent_type.value,
            capabilities=[c.value for c in capabilities]
        )
        
        return agent_id
    
    def deregister_agent(self, agent_id: str) -> bool:
        """Deregister an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Success status
        """
        if agent_id not in self._agents:
            self.logger.warning("Agent not found", agent_id=agent_id)
            return False
        
        registration = self._agents[agent_id]
        metadata = registration.metadata
        
        # Remove from type index
        if agent_id in self._agents_by_type[metadata.agent_type]:
            self._agents_by_type[metadata.agent_type].remove(agent_id)
        
        # Remove from capability index
        for capability in metadata.capabilities:
            if agent_id in self._agents_by_capability[capability]:
                self._agents_by_capability[capability].remove(agent_id)
        
        # Remove from main registry
        del self._agents[agent_id]
        
        # Update statistics
        self.active_agents -= 1
        
        self.logger.info("Agent deregistered", agent_id=agent_id)
        return True
    
    def get_agent(self, agent_id: str) -> Optional[Any]:
        """Get agent instance by ID.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent instance or None
        """
        registration = self._agents.get(agent_id)
        return registration.agent_instance if registration else None
    
    def get_agent_metadata(self, agent_id: str) -> Optional[AgentMetadata]:
        """Get agent metadata.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent metadata or None
        """
        registration = self._agents.get(agent_id)
        return registration.metadata if registration else None
    
    def find_agents_by_type(
        self,
        agent_type: AgentType,
        only_active: bool = True,
        only_healthy: bool = True
    ) -> List[str]:
        """Find agents by type.
        
        Args:
            agent_type: Agent type to search for
            only_active: Only return active agents
            only_healthy: Only return healthy agents
            
        Returns:
            List of agent IDs
        """
        agent_ids = self._agents_by_type.get(agent_type, [])
        
        if only_active or only_healthy:
            filtered_ids = []
            for agent_id in agent_ids:
                metadata = self.get_agent_metadata(agent_id)
                if metadata:
                    if only_active and not metadata.is_active:
                        continue
                    if only_healthy and not metadata.is_healthy:
                        continue
                    filtered_ids.append(agent_id)
            return filtered_ids
        
        return agent_ids
    
    def find_agents_by_capability(
        self,
        capability: AgentCapability,
        only_active: bool = True,
        only_healthy: bool = True
    ) -> List[str]:
        """Find agents by capability.
        
        Args:
            capability: Capability to search for
            only_active: Only return active agents
            only_healthy: Only return healthy agents
            
        Returns:
            List of agent IDs
        """
        agent_ids = self._agents_by_capability.get(capability, [])
        
        if only_active or only_healthy:
            filtered_ids = []
            for agent_id in agent_ids:
                metadata = self.get_agent_metadata(agent_id)
                if metadata:
                    if only_active and not metadata.is_active:
                        continue
                    if only_healthy and not metadata.is_healthy:
                        continue
                    filtered_ids.append(agent_id)
            return filtered_ids
        
        return agent_ids
    
    def get_best_agent(
        self,
        agent_type: Optional[AgentType] = None,
        capability: Optional[AgentCapability] = None,
        selection_strategy: str = "priority"  # priority, success_rate, round_robin
    ) -> Optional[str]:
        """Get best agent based on selection strategy.
        
        Args:
            agent_type: Optional agent type filter
            capability: Optional capability filter
            selection_strategy: Strategy for selection
            
        Returns:
            Best agent ID or None
        """
        # Get candidate agents
        candidates = []
        
        if agent_type:
            candidates = self.find_agents_by_type(agent_type)
        elif capability:
            candidates = self.find_agents_by_capability(capability)
        else:
            candidates = list(self._agents.keys())
        
        if not candidates:
            return None
        
        # Apply selection strategy
        if selection_strategy == "priority":
            # Sort by priority
            candidates_with_priority = [
                (agent_id, self._agents[agent_id].priority)
                for agent_id in candidates
            ]
            candidates_with_priority.sort(key=lambda x: x[1])
            return candidates_with_priority[0][0]
        
        elif selection_strategy == "success_rate":
            # Sort by success rate
            candidates_with_rate = [
                (agent_id, self.get_agent_metadata(agent_id).success_rate)
                for agent_id in candidates
            ]
            candidates_with_rate.sort(key=lambda x: x[1], reverse=True)
            return candidates_with_rate[0][0]
        
        elif selection_strategy == "round_robin":
            # Simple round robin - return first
            return candidates[0]
        
        return candidates[0]
    
    def update_agent_health(self, agent_id: str, is_healthy: bool):
        """Update agent health status.
        
        Args:
            agent_id: Agent ID
            is_healthy: Health status
        """
        if agent_id in self._agents:
            self._agents[agent_id].metadata.is_healthy = is_healthy
            self._agents[agent_id].metadata.last_health_check = datetime.now().isoformat()
            
            self.logger.info(
                "Agent health updated",
                agent_id=agent_id,
                is_healthy=is_healthy
            )
    
    def update_agent_stats(
        self,
        agent_id: str,
        execution_time: float,
        success: bool
    ):
        """Update agent execution statistics.
        
        Args:
            agent_id: Agent ID
            execution_time: Execution time in seconds
            success: Whether execution was successful
        """
        if agent_id not in self._agents:
            return
        
        metadata = self._agents[agent_id].metadata
        
        metadata.execution_count += 1
        metadata.total_execution_time += execution_time
        
        if not success:
            metadata.error_count += 1
        
        # Update success rate
        if metadata.execution_count > 0:
            metadata.success_rate = (
                (metadata.execution_count - metadata.error_count) /
                metadata.execution_count * 100
            )
    
    def perform_health_checks(self) -> Dict[str, bool]:
        """Perform health checks on all registered agents.
        
        Returns:
            Dictionary of agent_id -> health_status
        """
        health_results = {}
        
        for agent_id, registration in self._agents.items():
            if registration.health_check_fn:
                try:
                    is_healthy = registration.health_check_fn()
                    self.update_agent_health(agent_id, is_healthy)
                    health_results[agent_id] = is_healthy
                except Exception as e:
                    self.logger.error(
                        "Health check failed",
                        agent_id=agent_id,
                        error=str(e)
                    )
                    self.update_agent_health(agent_id, False)
                    health_results[agent_id] = False
            else:
                # No health check function - assume healthy
                health_results[agent_id] = True
        
        return health_results
    
    def get_registry_status(self) -> Dict[str, Any]:
        """Get registry status and statistics.
        
        Returns:
            Registry status dictionary
        """
        active_by_type = {}
        for agent_type, agent_ids in self._agents_by_type.items():
            active_count = sum(
                1 for aid in agent_ids
                if self.get_agent_metadata(aid).is_active
            )
            active_by_type[agent_type.value] = active_count
        
        return {
            'total_registrations': self.total_registrations,
            'active_agents': self.active_agents,
            'agents_by_type': active_by_type,
            'healthy_agents': sum(
                1 for reg in self._agents.values()
                if reg.metadata.is_healthy
            ),
            'total_executions': sum(
                reg.metadata.execution_count
                for reg in self._agents.values()
            ),
            'total_errors': sum(
                reg.metadata.error_count
                for reg in self._agents.values()
            )
        }
    
    def list_all_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents with their details.
        
        Returns:
            List of agent information dictionaries
        """
        agents_list = []
        
        for agent_id, registration in self._agents.items():
            metadata = registration.metadata
            agents_list.append({
                'agent_id': agent_id,
                'agent_name': metadata.agent_name,
                'agent_type': metadata.agent_type.value,
                'version': metadata.version,
                'capabilities': [c.value for c in metadata.capabilities],
                'is_active': metadata.is_active,
                'is_healthy': metadata.is_healthy,
                'execution_count': metadata.execution_count,
                'success_rate': metadata.success_rate,
                'priority': registration.priority
            })
        
        return agents_list


# Global registry instance
_global_registry = None


def get_global_registry() -> AgentRegistry:
    """Get global agent registry instance.
    
    Returns:
        Global AgentRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = AgentRegistry()
    return _global_registry
