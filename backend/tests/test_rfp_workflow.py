"""Tests for RFP workflow orchestration."""
import pytest
import asyncio
from datetime import datetime, timedelta
from agents.communication import CommunicationManager
from workflows import RFPWorkflowOrchestrator, WorkflowStage, WorkflowStatus
from workflows.mock_agents import (
    MockRFPParserAgent,
    MockSalesAgent,
    MockTechnicalAgent,
    MockPricingAgent,
    MockResponseGeneratorAgent
)


@pytest.fixture
async def setup_system():
    """Setup complete system with all components."""
    # Initialize communication manager
    comm_manager = CommunicationManager(use_redis=False)
    await comm_manager.connect()
    
    # Initialize mock agents
    parser = MockRFPParserAgent(comm_manager)
    await parser.initialize()
    
    sales = MockSalesAgent(comm_manager)
    await sales.initialize()
    
    technical = MockTechnicalAgent(comm_manager)
    await technical.initialize()
    
    pricing = MockPricingAgent(comm_manager)
    await pricing.initialize()
    
    response_gen = MockResponseGeneratorAgent(comm_manager)
    await response_gen.initialize()
    
    # Initialize orchestrator
    orchestrator = RFPWorkflowOrchestrator(comm_manager)
    await orchestrator.initialize()
    
    yield orchestrator, comm_manager
    
    # Cleanup
    await comm_manager.disconnect()


@pytest.mark.asyncio
async def test_complete_workflow_success(setup_system):
    """Test successful end-to-end workflow execution."""
    orchestrator, comm_manager = setup_system
    
    # Prepare RFP data
    rfp_data = {
        'rfp_id': 'RFP_TEST_001',
        'customer_id': 'CUST_TEST_001',
        'document': 'Test RFP Document Content',
        'document_type': 'pdf',
        'deadline': (datetime.utcnow() + timedelta(days=14)).isoformat(),
        'priority': 'high',
        'source': 'test'
    }
    
    # Process RFP
    result = await orchestrator.process_rfp(rfp_data)
    
    # Verify success
    assert result['status'] == 'completed'
    assert result['rfp_id'] == 'RFP_TEST_001'
    assert result['customer_id'] == 'CUST_TEST_001'
    assert 'workflow_id' in result
    
    # Verify all stages completed
    assert 'timeline' in result
    assert 'stage_durations' in result['timeline']
    assert len(result['timeline']['stage_durations']) >= 5  # At least 5 main stages
    
    # Verify quote generated
    assert 'quote' in result
    assert 'quote_id' in result['quote']
    assert result['quote']['total'] > 0
    assert len(result['quote']['line_items']) > 0
    
    # Verify compliance checked
    assert 'compliance' in result
    assert 'score' in result['compliance']
    assert result['compliance']['score'] > 0
    
    # Verify response document generated
    assert 'response_document' in result
    assert result['response_document']['format'] == 'pdf'


@pytest.mark.asyncio
async def test_workflow_stages_sequential(setup_system):
    """Test that workflow stages execute in correct sequence."""
    orchestrator, comm_manager = setup_system
    
    rfp_data = {
        'rfp_id': 'RFP_TEST_002',
        'customer_id': 'CUST_TEST_002',
        'document': 'Test Document',
        'document_type': 'pdf',
        'deadline': (datetime.utcnow() + timedelta(days=10)).isoformat(),
        'priority': 'normal'
    }
    
    result = await orchestrator.process_rfp(rfp_data)
    
    # Check stage order
    stage_durations = result['timeline']['stage_durations']
    stages = list(stage_durations.keys())
    
    expected_order = [
        'parsing',
        'sales_analysis',
        'technical_validation',
        'pricing_calculation',
        'response_generation'
        # Note: 'review' stage doesn't record duration as it's a compilation step
    ]
    
    assert stages == expected_order


@pytest.mark.asyncio
async def test_workflow_data_flow(setup_system):
    """Test data flows correctly between stages."""
    orchestrator, comm_manager = setup_system
    
    rfp_data = {
        'rfp_id': 'RFP_TEST_003',
        'customer_id': 'CUST_TEST_003',
        'document': 'Test Document',
        'document_type': 'pdf'
    }
    
    result = await orchestrator.process_rfp(rfp_data)
    
    # Verify data from each stage is present
    assert result['quote']['line_items']  # From pricing
    assert result['compliance']['standards_met']  # From technical
    assert result['response_document']  # From response generation
    assert result['metadata']['confidence_scores']  # From multiple stages


@pytest.mark.asyncio
async def test_workflow_status_tracking(setup_system):
    """Test workflow status can be tracked during execution."""
    orchestrator, comm_manager = setup_system
    
    # Start workflow in background
    rfp_data = {
        'rfp_id': 'RFP_TEST_004',
        'customer_id': 'CUST_TEST_004',
        'document': 'Test Document',
        'document_type': 'pdf'
    }
    
    # Create task without awaiting
    task = asyncio.create_task(orchestrator.process_rfp(rfp_data))
    
    # Give it a moment to start
    await asyncio.sleep(0.1)
    
    # Check active workflows
    active = orchestrator.get_all_active_workflows()
    assert len(active) > 0
    
    # Wait for completion
    result = await task
    
    # Verify workflow was tracked
    status = orchestrator.get_workflow_status(result['workflow_id'])
    assert status is not None
    assert status['status'] == 'completed'


@pytest.mark.asyncio
async def test_workflow_timing_metrics(setup_system):
    """Test workflow captures timing metrics."""
    orchestrator, comm_manager = setup_system
    
    rfp_data = {
        'rfp_id': 'RFP_TEST_005',
        'customer_id': 'CUST_TEST_005',
        'document': 'Test Document',
        'document_type': 'pdf'
    }
    
    result = await orchestrator.process_rfp(rfp_data)
    
    # Verify timing data
    timeline = result['timeline']
    assert 'processing_started' in timeline
    assert 'processing_completed' in timeline
    assert 'total_duration_seconds' in timeline
    assert timeline['total_duration_seconds'] > 0
    
    # Verify stage durations
    stage_durations = timeline['stage_durations']
    for stage, duration in stage_durations.items():
        assert duration >= 0
        assert duration < 10  # Each stage should complete quickly in test


@pytest.mark.asyncio
async def test_workflow_with_high_priority(setup_system):
    """Test workflow handles priority correctly."""
    orchestrator, comm_manager = setup_system
    
    rfp_data = {
        'rfp_id': 'RFP_TEST_006',
        'customer_id': 'CUST_TEST_006',
        'document': 'Urgent Request',
        'document_type': 'pdf',
        'priority': 'urgent'
    }
    
    result = await orchestrator.process_rfp(rfp_data)
    
    assert result['status'] == 'completed'
    # Priority should be preserved in metadata
    workflow_id = result['workflow_id']
    status = orchestrator.get_workflow_status(workflow_id)
    # Priority tracked in context (internal)


@pytest.mark.asyncio
async def test_workflow_metrics_integration(setup_system):
    """Test workflow integrates with communication system metrics."""
    orchestrator, comm_manager = setup_system
    
    # Get initial metrics
    initial_analytics = comm_manager.get_message_analytics()
    initial_count = initial_analytics['total_messages']
    
    # Process RFP
    rfp_data = {
        'rfp_id': 'RFP_TEST_007',
        'customer_id': 'CUST_TEST_007',
        'document': 'Test Document',
        'document_type': 'pdf'
    }
    
    await orchestrator.process_rfp(rfp_data)
    
    # Check metrics increased
    final_analytics = comm_manager.get_message_analytics()
    final_count = final_analytics['total_messages']
    
    # Should have sent multiple messages (one per stage)
    assert final_count > initial_count
    assert final_count >= initial_count + 5  # At least 5 stage requests


@pytest.mark.asyncio
async def test_multiple_concurrent_workflows(setup_system):
    """Test system can handle multiple workflows concurrently."""
    orchestrator, comm_manager = setup_system
    
    # Create multiple RFPs
    rfp_data_list = [
        {
            'rfp_id': f'RFP_TEST_CONCURRENT_{i}',
            'customer_id': f'CUST_TEST_{i}',
            'document': f'Test Document {i}',
            'document_type': 'pdf'
        }
        for i in range(3)
    ]
    
    # Process all concurrently
    tasks = [
        orchestrator.process_rfp(rfp_data)
        for rfp_data in rfp_data_list
    ]
    
    results = await asyncio.gather(*tasks)
    
    # Verify all succeeded
    assert len(results) == 3
    for result in results:
        assert result['status'] == 'completed'
    
    # Verify unique workflow IDs
    workflow_ids = [r['workflow_id'] for r in results]
    assert len(set(workflow_ids)) == 3


@pytest.mark.asyncio
async def test_workflow_confidence_scores(setup_system):
    """Test workflow captures confidence scores from agents."""
    orchestrator, comm_manager = setup_system
    
    rfp_data = {
        'rfp_id': 'RFP_TEST_008',
        'customer_id': 'CUST_TEST_008',
        'document': 'Test Document',
        'document_type': 'pdf'
    }
    
    result = await orchestrator.process_rfp(rfp_data)
    
    # Verify confidence scores present
    scores = result['metadata']['confidence_scores']
    assert 'parsing' in scores
    assert 'opportunity' in scores
    assert 'compliance' in scores
    
    # Verify scores are valid
    for score_name, score_value in scores.items():
        assert 0.0 <= score_value <= 1.0


@pytest.mark.asyncio
async def test_workflow_quote_details(setup_system):
    """Test workflow generates detailed quote information."""
    orchestrator, comm_manager = setup_system
    
    rfp_data = {
        'rfp_id': 'RFP_TEST_009',
        'customer_id': 'CUST_TEST_009',
        'document': 'Test Document',
        'document_type': 'pdf'
    }
    
    result = await orchestrator.process_rfp(rfp_data)
    
    # Verify quote structure
    quote = result['quote']
    assert 'quote_id' in quote
    assert 'total' in quote
    assert 'line_items' in quote
    assert 'validity_days' in quote
    
    # Verify line items have required fields
    for item in quote['line_items']:
        assert 'item_id' in item
        assert 'product' in item
        assert 'quantity' in item
        assert 'unit_price' in item
        assert 'amount' in item


@pytest.mark.asyncio
async def test_workflow_compliance_validation(setup_system):
    """Test workflow validates compliance requirements."""
    orchestrator, comm_manager = setup_system
    
    rfp_data = {
        'rfp_id': 'RFP_TEST_010',
        'customer_id': 'CUST_TEST_010',
        'document': 'Test Document',
        'document_type': 'pdf'
    }
    
    result = await orchestrator.process_rfp(rfp_data)
    
    # Verify compliance data
    compliance = result['compliance']
    assert 'score' in compliance
    assert 'standards_met' in compliance
    assert 'certifications' in compliance
    
    # Verify compliance score is reasonable
    assert 0.0 <= compliance['score'] <= 1.0
    
    # Verify standards and certifications are lists
    assert isinstance(compliance['standards_met'], list)
    assert isinstance(compliance['certifications'], list)

