"""
Comprehensive Test Suite for Orchestration System
Tests all components and integration.
"""
import pytest
from typing import Dict, Any
from datetime import datetime
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.orchestrator.agent_registry import (
    AgentRegistry, AgentType, AgentCapability, AgentMetadata
)
from agents.orchestrator.message_queue import (
    AgentMessageQueue, MessagePriority, MessageStatus
)
from agents.orchestrator.communication_protocol import (
    AgentCommunicationProtocol, ProtocolMessageType
)
from agents.orchestrator.quality_validation import (
    QualityValidationSystem, CompletenessChecker,
    ConsistencyValidator, OutputFormatter
)
from agents.orchestrator.context_summarization import (
    ContextAwareSummarizer, AudienceRole
)
from agents.orchestrator.audit_trail import (
    AuditTrailGenerator, AuditEventType, AuditSeverity
)
from agents.orchestrator.enhanced_orchestrator import EnhancedMainOrchestrator


class TestAgentRegistry:
    """Test Agent Registry."""
    
    def test_agent_registration(self):
        """Test registering agents."""
        registry = AgentRegistry()
        
        # Mock agent
        mock_agent = {"type": "sales", "name": "Sales Agent"}
        
        agent_id = registry.register_agent(
            agent_instance=mock_agent,
            agent_name="SalesAgent",
            agent_type=AgentType.SALES,
            capabilities=[AgentCapability.RFP_ANALYSIS],
            priority=100
        )
        
        assert agent_id is not None
        assert registry.active_agents == 1
        
        # Retrieve agent
        retrieved = registry.get_agent(agent_id)
        assert retrieved == mock_agent
        
        print("✓ Agent registration test passed")
    
    def test_find_agents_by_type(self):
        """Test finding agents by type."""
        registry = AgentRegistry()
        
        # Register multiple agents
        sales_id = registry.register_agent(
            agent_instance={},
            agent_name="SalesAgent",
            agent_type=AgentType.SALES,
            capabilities=[AgentCapability.RFP_ANALYSIS]
        )
        
        tech_id = registry.register_agent(
            agent_instance={},
            agent_name="TechnicalAgent",
            agent_type=AgentType.TECHNICAL,
            capabilities=[AgentCapability.PRODUCT_MATCHING]
        )
        
        # Find sales agents
        sales_agents = registry.find_agents_by_type(AgentType.SALES)
        assert len(sales_agents) == 1
        assert sales_id in sales_agents
        
        # Find technical agents
        tech_agents = registry.find_agents_by_type(AgentType.TECHNICAL)
        assert len(tech_agents) == 1
        assert tech_id in tech_agents
        
        print("✓ Find agents by type test passed")
    
    def test_agent_stats_update(self):
        """Test updating agent statistics."""
        registry = AgentRegistry()
        
        agent_id = registry.register_agent(
            agent_instance={},
            agent_name="TestAgent",
            agent_type=AgentType.SALES,
            capabilities=[AgentCapability.RFP_ANALYSIS]
        )
        
        # Update stats
        registry.update_agent_stats(agent_id, execution_time=1.5, success=True)
        registry.update_agent_stats(agent_id, execution_time=2.0, success=True)
        registry.update_agent_stats(agent_id, execution_time=1.0, success=False)
        
        metadata = registry.get_agent_metadata(agent_id)
        assert metadata.execution_count == 3
        assert metadata.error_count == 1
        assert metadata.success_rate == pytest.approx(66.67, rel=0.1)
        
        print("✓ Agent stats update test passed")


class TestMessageQueue:
    """Test Message Queue System."""
    
    def test_message_sending(self):
        """Test sending messages."""
        queue = AgentMessageQueue()
        
        queue.register_agent_queue("agent1")
        queue.register_agent_queue("agent2")
        
        message_id = queue.send_message(
            from_agent="agent1",
            to_agent="agent2",
            message_type="test_message",
            payload={"data": "test"},
            priority=MessagePriority.NORMAL
        )
        
        assert message_id is not None
        assert queue.get_queue_size("agent2") == 1
        
        print("✓ Message sending test passed")
    
    def test_message_receiving(self):
        """Test receiving messages."""
        queue = AgentMessageQueue()
        
        queue.register_agent_queue("agent1")
        queue.register_agent_queue("agent2")
        
        # Send message
        message_id = queue.send_message(
            from_agent="agent1",
            to_agent="agent2",
            message_type="test",
            payload={"data": "test"}
        )
        
        # Receive message
        message = queue.receive_message("agent2", timeout=1.0)
        
        assert message is not None
        assert message.message_id == message_id
        assert message.status == MessageStatus.DELIVERED
        
        print("✓ Message receiving test passed")
    
    def test_pub_sub(self):
        """Test pub/sub pattern."""
        queue = AgentMessageQueue()
        
        queue.register_agent_queue("subscriber1")
        queue.register_agent_queue("subscriber2")
        queue.register_agent_queue("publisher")
        
        # Subscribe
        queue.subscribe("subscriber1", "test_topic")
        queue.subscribe("subscriber2", "test_topic")
        
        # Publish
        message_ids = queue.publish(
            from_agent="publisher",
            topic="test_topic",
            message_type="broadcast",
            payload={"data": "broadcast_test"}
        )
        
        assert len(message_ids) == 2
        assert queue.get_queue_size("subscriber1") == 1
        assert queue.get_queue_size("subscriber2") == 1
        
        print("✓ Pub/sub test passed")


class TestCommunicationProtocol:
    """Test Communication Protocol."""
    
    def test_request_response(self):
        """Test request/response pattern."""
        queue = AgentMessageQueue()
        protocol = AgentCommunicationProtocol(queue)
        
        queue.register_agent_queue("requester")
        queue.register_agent_queue("responder")
        
        # Send request
        correlation_id = protocol.send_request(
            from_agent="requester",
            to_agent="responder",
            request_type=ProtocolMessageType.REQUEST_ANALYSIS,
            payload={"request_data": "test"}
        )
        
        assert correlation_id is not None
        
        # Receive request
        message = queue.receive_message("responder", timeout=1.0)
        assert message is not None
        
        # Send response
        response_id = protocol.send_response(
            from_agent="responder",
            to_agent="requester",
            correlation_id=correlation_id,
            response_type=ProtocolMessageType.RESPONSE_SUCCESS,
            payload={"response_data": "success"}
        )
        
        assert response_id is not None
        
        print("✓ Request/response test passed")


class TestQualityValidation:
    """Test Quality Validation System."""
    
    def test_completeness_checker(self):
        """Test completeness checking."""
        checker = CompletenessChecker()
        
        data = {
            'rfp_id': 'RFP-001',
            'customer_name': 'Test Customer',
            'technical_proposal': {}
        }
        
        required_fields = ['rfp_id', 'customer_name', 'executive_summary']
        
        issues = checker.check_required_fields(data, required_fields)
        
        # Should have 1 issue (missing executive_summary)
        assert len(issues) == 1
        assert any('executive_summary' in issue.field for issue in issues)
        
        print("✓ Completeness checker test passed")
    
    def test_consistency_validator(self):
        """Test consistency validation."""
        validator = ConsistencyValidator()
        
        pricing_data = {
            'bid_summary': {
                'grand_total': -1000,  # Invalid
                'margin_percent': 150  # Invalid
            }
        }
        
        issues = validator.check_total_calculations(pricing_data)
        
        assert len(issues) >= 2  # Should find both issues
        
        print("✓ Consistency validator test passed")
    
    def test_quality_validation_system(self):
        """Test complete quality validation."""
        validator = QualityValidationSystem()
        
        rfp_response = {
            'rfp_id': 'RFP-001',
            'response_id': 'RESP-001',
            'customer_name': 'Test Customer',
            'executive_summary': 'Test summary',
            'technical_proposal': {'comparisons': []},
            'commercial_proposal': {
                'bid_summary': {
                    'grand_total': 100000,
                    'margin_percent': 20
                }
            },
            'terms_and_conditions': 'Standard terms'
        }
        
        consolidated_data = {
            'sales_analysis': {'rfp_analysis': {'customer_name': 'Test Customer'}},
            'technical_proposal': {'comparisons': []},
            'commercial_proposal': {'bid_summary': {'grand_total': 100000}}
        }
        
        result = validator.validate_rfp_response(rfp_response, consolidated_data)
        
        assert result.score > 0
        assert isinstance(result.is_valid, bool)
        
        print(f"✓ Quality validation test passed (score: {result.score:.2f})")


class TestContextSummarization:
    """Test Context-Aware Summarization."""
    
    def test_executive_summary_generation(self):
        """Test executive summary generation."""
        summarizer = ContextAwareSummarizer()
        
        consolidated_data = {
            'sales_analysis': {
                'rfp_analysis': {
                    'customer_name': 'Test Customer',
                    'rfp_type': 'Standard',
                    'estimated_value': 1000000
                }
            },
            'technical_proposal': {
                'technical_summary': {
                    'compliance_level': 'Full Compliance'
                }
            },
            'commercial_proposal': {
                'bid_summary': {
                    'grand_total': 1000000,
                    'payment_terms': 'Net 30 days',
                    'validity_days': 90
                }
            }
        }
        
        customer_info = {'name': 'Test Customer'}
        
        summary = summarizer.generate_executive_summary(
            consolidated_data,
            customer_info
        )
        
        assert len(summary) > 0
        assert 'Test Customer' in summary
        assert '1,000,000' in summary
        
        print("✓ Executive summary generation test passed")
    
    def test_role_specific_formatting(self):
        """Test role-specific formatting."""
        summarizer = ContextAwareSummarizer()
        
        consolidated_data = {
            'sales_analysis': {'rfp_analysis': {}},
            'technical_proposal': {'technical_summary': {}},
            'commercial_proposal': {'bid_summary': {'grand_total': 1000000}}
        }
        
        customer_info = {'name': 'Test Customer'}
        
        # Test each role
        for role in AudienceRole:
            formatted = summarizer.format_for_audience(
                consolidated_data,
                role,
                customer_info
            )
            
            assert formatted.summary is not None
            assert len(formatted.key_points) > 0
            assert len(formatted.recommendations) > 0
        
        print("✓ Role-specific formatting test passed")


class TestAuditTrail:
    """Test Audit Trail System."""
    
    def test_audit_trail_creation(self):
        """Test creating audit trail."""
        audit_gen = AuditTrailGenerator()
        
        trail_id = audit_gen.start_audit_trail(
            workflow_id="WF-001",
            metadata={'test': True}
        )
        
        assert trail_id is not None
        
        print("✓ Audit trail creation test passed")
    
    def test_event_logging(self):
        """Test event logging."""
        audit_gen = AuditTrailGenerator()
        
        trail_id = audit_gen.start_audit_trail("WF-001")
        
        # Log various events
        event_id = audit_gen.log_event(
            trail_id=trail_id,
            event_type=AuditEventType.AGENT_STARTED,
            severity=AuditSeverity.INFO,
            component="TestAgent",
            description="Test event"
        )
        
        assert event_id is not None
        
        # Complete trail
        audit_gen.complete_audit_trail(trail_id, success=True)
        
        # Load and verify
        trail = audit_gen.load_trail(trail_id)
        assert trail is not None
        
        print("✓ Event logging test passed")
    
    def test_audit_report_generation(self):
        """Test audit report generation."""
        audit_gen = AuditTrailGenerator()
        
        trail_id = audit_gen.start_audit_trail("WF-001")
        
        # Log some events
        audit_gen.log_agent_start(trail_id, "SalesAgent", "agent-1", {})
        audit_gen.log_agent_completion(trail_id, "SalesAgent", "agent-1", {}, 1.5)
        
        audit_gen.complete_audit_trail(trail_id, success=True)
        
        # Generate report
        report = audit_gen.generate_audit_report(trail_id, include_details=True)
        
        assert len(report) > 0
        assert 'AUDIT TRAIL REPORT' in report
        
        print("✓ Audit report generation test passed")


class TestEnhancedOrchestrator:
    """Test Enhanced Orchestrator Integration."""
    
    def test_orchestrator_initialization(self):
        """Test orchestrator initialization."""
        orchestrator = EnhancedMainOrchestrator(
            use_global_registry=False
        )
        
        assert orchestrator.agent_registry is not None
        assert orchestrator.message_queue is not None
        assert orchestrator.quality_validator is not None
        
        print("✓ Orchestrator initialization test passed")
    
    def test_agent_registration_integration(self):
        """Test agent registration with orchestrator."""
        orchestrator = EnhancedMainOrchestrator(use_global_registry=False)
        
        mock_agent = {"name": "TestAgent"}
        
        agent_id = orchestrator.register_agent_with_registry(
            agent_instance=mock_agent,
            agent_name="TestAgent",
            agent_type=AgentType.SALES,
            capabilities=[AgentCapability.RFP_ANALYSIS]
        )
        
        assert agent_id is not None
        assert orchestrator.agent_registry.active_agents == 1
        
        print("✓ Agent registration integration test passed")
    
    def test_health_check(self):
        """Test health check."""
        orchestrator = EnhancedMainOrchestrator(use_global_registry=False)
        
        health = orchestrator.health_check()
        
        assert 'status' in health
        assert 'timestamp' in health
        assert 'statistics' in health
        
        print("✓ Health check test passed")
    
    def test_enhanced_statistics(self):
        """Test enhanced statistics."""
        orchestrator = EnhancedMainOrchestrator(use_global_registry=False)
        
        stats = orchestrator.get_enhanced_statistics()
        
        assert 'orchestrator_stats' in stats
        assert 'registry_stats' in stats
        assert 'queue_stats' in stats
        
        print("✓ Enhanced statistics test passed")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("RUNNING COMPREHENSIVE ORCHESTRATION SYSTEM TESTS")
    print("="*60 + "\n")
    
    # Agent Registry Tests
    print("\n--- Agent Registry Tests ---")
    test_registry = TestAgentRegistry()
    test_registry.test_agent_registration()
    test_registry.test_find_agents_by_type()
    test_registry.test_agent_stats_update()
    
    # Message Queue Tests
    print("\n--- Message Queue Tests ---")
    test_queue = TestMessageQueue()
    test_queue.test_message_sending()
    test_queue.test_message_receiving()
    test_queue.test_pub_sub()
    
    # Communication Protocol Tests
    print("\n--- Communication Protocol Tests ---")
    test_protocol = TestCommunicationProtocol()
    test_protocol.test_request_response()
    
    # Quality Validation Tests
    print("\n--- Quality Validation Tests ---")
    test_validation = TestQualityValidation()
    test_validation.test_completeness_checker()
    test_validation.test_consistency_validator()
    test_validation.test_quality_validation_system()
    
    # Context Summarization Tests
    print("\n--- Context Summarization Tests ---")
    test_summarization = TestContextSummarization()
    test_summarization.test_executive_summary_generation()
    test_summarization.test_role_specific_formatting()
    
    # Audit Trail Tests
    print("\n--- Audit Trail Tests ---")
    test_audit = TestAuditTrail()
    test_audit.test_audit_trail_creation()
    test_audit.test_event_logging()
    test_audit.test_audit_report_generation()
    
    # Enhanced Orchestrator Tests
    print("\n--- Enhanced Orchestrator Tests ---")
    test_orchestrator = TestEnhancedOrchestrator()
    test_orchestrator.test_orchestrator_initialization()
    test_orchestrator.test_agent_registration_integration()
    test_orchestrator.test_health_check()
    test_orchestrator.test_enhanced_statistics()
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED SUCCESSFULLY! ✓")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_all_tests()
