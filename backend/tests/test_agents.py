"""Test agents."""
import pytest
from agents.technical_agent import TechnicalAgent
from agents.pricing_agent import PricingAgent


@pytest.mark.asyncio
async def test_technical_agent_initialization():
    """Test technical agent initialization."""
    agent = TechnicalAgent()
    
    assert agent.agent_name == "TechnicalAgent"
    assert agent.agent_type == "technical"
    assert agent.execution_count == 0


@pytest.mark.asyncio
async def test_pricing_agent_initialization():
    """Test pricing agent initialization."""
    agent = PricingAgent()
    
    assert agent.agent_name == "PricingAgent"
    assert agent.agent_type == "pricing"
    assert agent.execution_count == 0


@pytest.mark.asyncio
async def test_agent_statistics():
    """Test agent statistics tracking."""
    agent = TechnicalAgent()
    
    stats = agent.get_statistics()
    
    assert stats["agent_name"] == "TechnicalAgent"
    assert stats["execution_count"] == 0
    assert stats["total_tokens"] == 0
