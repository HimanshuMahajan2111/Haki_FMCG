"""Tests for advanced workflow features."""
import pytest
import asyncio
from datetime import datetime

from agents.communication import CommunicationManager
from workflows.rfp_workflow import RFPWorkflowOrchestrator
from workflows.mock_agents import (
    MockRFPParserAgent, MockSalesAgent, MockTechnicalAgent,
    MockPricingAgent, MockResponseGeneratorAgent
)
from workflows.workflow_extensions import (
    TimeEstimator, WorkflowVisualizer, ApprovalManager,
    WorkflowTemplateManager, ConditionalRouter, WorkflowTemplateType
)


@pytest.fixture
async def setup_system():
    """Setup communication system and agents."""
    comm_manager = CommunicationManager()
    
    # Initialize agents
    parser = MockRFPParserAgent(comm_manager)
    sales = MockSalesAgent(comm_manager)
    technical = MockTechnicalAgent(comm_manager)
    pricing = MockPricingAgent(comm_manager)
    response_gen = MockResponseGeneratorAgent(comm_manager)
    
    await parser.initialize()
    await sales.initialize()
    await technical.initialize()
    await pricing.initialize()
    await response_gen.initialize()
    
    # Initialize orchestrator
    orchestrator = RFPWorkflowOrchestrator(comm_manager, enable_visualization=False)
    await orchestrator.initialize()
    
    return orchestrator, comm_manager


@pytest.mark.asyncio
async def test_workflow_template_selection(setup_system):
    """Test automatic template selection based on RFP characteristics."""
    orchestrator, _ = setup_system
    
    # Test standard RFP
    rfp_standard = {
        'rfp_id': 'TEST001',
        'customer_id': 'CUST001',
        'priority': 'normal',
        'complexity': 'standard',
        'estimated_value': 100000
    }
    result = await orchestrator.process_rfp(rfp_standard)
    assert result['workflow_info']['template_id'] == 'standard_rfp'
    
    # Test fast track (urgent + simple)
    rfp_fast = {
        'rfp_id': 'TEST002',
        'customer_id': 'CUST002',
        'priority': 'urgent',
        'complexity': 'simple',
        'estimated_value': 30000
    }
    result = await orchestrator.process_rfp(rfp_fast)
    assert result['workflow_info']['template_id'] == 'fast_track_rfp'
    
    # Test complex (high value or complex)
    rfp_complex = {
        'rfp_id': 'TEST003',
        'customer_id': 'CUST003',
        'priority': 'high',
        'complexity': 'complex',
        'estimated_value': 1500000
    }
    result = await orchestrator.process_rfp(rfp_complex)
    assert result['workflow_info']['template_id'] == 'complex_rfp'
    
    # Test simple quote
    rfp_simple = {
        'rfp_id': 'TEST004',
        'customer_id': 'CUST004',
        'priority': 'normal',
        'complexity': 'simple',
        'estimated_value': 25000
    }
    result = await orchestrator.process_rfp(rfp_simple)
    assert result['workflow_info']['template_id'] == 'simple_quote'


@pytest.mark.asyncio
async def test_explicit_template_selection(setup_system):
    """Test using explicit template ID."""
    orchestrator, _ = setup_system
    
    rfp_data = {
        'rfp_id': 'TEST005',
        'customer_id': 'CUST005',
        'priority': 'normal'
    }
    
    # Force fast track template
    result = await orchestrator.process_rfp(rfp_data, template_id='fast_track_rfp')
    assert result['workflow_info']['template_id'] == 'fast_track_rfp'
    assert result['workflow_info']['template_name'] == 'Fast Track RFP'


@pytest.mark.asyncio
async def test_time_estimation():
    """Test time estimation with historical data."""
    estimator = TimeEstimator()
    
    # Record some stage times
    estimator.record_stage_time('parsing', 1.2)
    estimator.record_stage_time('parsing', 1.5)
    estimator.record_stage_time('parsing', 1.1)
    estimator.record_stage_time('parsing', 1.8)
    
    # Get estimate (should be 90th percentile)
    estimate = estimator.estimate_stage_time('parsing')
    assert 1.0 <= estimate <= 2.0
    
    # Check confidence level
    confidence = estimator.get_confidence_level('parsing')
    assert 0.0 <= confidence <= 1.0
    assert confidence > 0.0  # Should have some confidence with data
    
    # Unknown stage should return default
    unknown_estimate = estimator.estimate_stage_time('unknown_stage')
    assert unknown_estimate == 1.0


@pytest.mark.asyncio
async def test_time_estimation_integration(setup_system):
    """Test time estimation integration in workflow."""
    orchestrator, _ = setup_system
    
    # Process first workflow
    rfp1 = {'rfp_id': 'TEST006', 'customer_id': 'CUST006'}
    result1 = await orchestrator.process_rfp(rfp1)
    
    # Process second workflow
    rfp2 = {'rfp_id': 'TEST007', 'customer_id': 'CUST007'}
    result2 = await orchestrator.process_rfp(rfp2)
    
    # Get estimates (should have data from 2 runs)
    estimates = orchestrator.get_time_estimates()
    
    assert 'parsing' in estimates
    assert 'sales_analysis' in estimates
    assert 'total_workflow' in estimates
    
    # Check structure
    assert 'estimated_time' in estimates['parsing']
    assert 'confidence' in estimates['parsing']
    assert 'sample_count' in estimates['parsing']
    assert estimates['parsing']['sample_count'] >= 2


@pytest.mark.asyncio
async def test_workflow_visualization():
    """Test workflow visualization generation."""
    visualizer = WorkflowVisualizer()
    
    # Test ASCII flow
    stages = ['parsing', 'sales_analysis', 'pricing']
    ascii_viz = visualizer.generate_ascii_flow(stages)
    
    assert 'WORKFLOW EXECUTION FLOW' in ascii_viz
    assert 'parsing' in ascii_viz.lower()
    assert 'sales' in ascii_viz.lower()
    assert 'pricing' in ascii_viz.lower()
    
    # Test with current stage
    ascii_current = visualizer.generate_ascii_flow(
        stages,
        current_stage='sales_analysis',
        completed_stages=['parsing']
    )
    assert '✓' in ascii_current  # Completed marker
    assert '→' in ascii_current  # Current marker
    
    # Test Mermaid diagram
    mermaid = visualizer.generate_mermaid_diagram(
        stages,
        completed_stages=['parsing']
    )
    assert 'graph TD' in mermaid
    assert 'Start' in mermaid
    assert 'End' in mermaid
    
    # Test timeline
    stage_results = {
        'parsing': {'duration': 1.2},
        'sales_analysis': {'duration': 2.5},
        'pricing': {'duration': 1.8}
    }
    timeline = visualizer.generate_timeline(stage_results)
    assert 'EXECUTION TIMELINE' in timeline
    assert '1.20s' in timeline or '1.2s' in timeline


@pytest.mark.asyncio
async def test_visualization_integration(setup_system):
    """Test visualization integration in orchestrator."""
    orchestrator, _ = setup_system
    
    # Process workflow
    rfp = {'rfp_id': 'TEST008', 'customer_id': 'CUST008'}
    result = await orchestrator.process_rfp(rfp)
    
    workflows = orchestrator.get_all_active_workflows()
    workflow_id = workflows[0]['workflow_id']
    
    # Get ASCII visualization
    ascii_viz = orchestrator.visualize_workflow(workflow_id)
    assert 'WORKFLOW' in ascii_viz.upper()
    
    # Get Mermaid diagram
    mermaid = orchestrator.generate_mermaid_diagram(workflow_id)
    assert 'graph TD' in mermaid


@pytest.mark.asyncio
async def test_approval_manager():
    """Test approval manager functionality."""
    manager = ApprovalManager()
    
    # Request approval
    workflow_id = "test_workflow_001"
    
    # Create approval request task
    approval_task = asyncio.create_task(
        manager.request_approval(
            workflow_id=workflow_id,
            stage_name="sales_analysis",
            required_roles=["sales_manager"],
            context_data={'rfp_id': 'TEST009'},
            timeout=5.0
        )
    )
    
    # Wait a moment then approve
    await asyncio.sleep(0.1)
    
    # Get pending approvals
    pending = manager.get_pending_approvals()
    assert len(pending) == 1
    assert pending[0].workflow_id == workflow_id
    assert pending[0].stage_name == "sales_analysis"
    
    # Approve
    approval_id = pending[0].approval_id
    success = manager.approve(approval_id, "manager_john")
    assert success
    
    # Wait for approval task to complete
    approved = await approval_task
    assert approved


@pytest.mark.asyncio
async def test_approval_rejection():
    """Test approval rejection."""
    manager = ApprovalManager()
    
    # Request approval
    approval_task = asyncio.create_task(
        manager.request_approval(
            workflow_id="test_workflow_002",
            stage_name="pricing",
            required_roles=["pricing_manager"],
            context_data={},
            timeout=5.0
        )
    )
    
    await asyncio.sleep(0.1)
    
    # Get and reject
    pending = manager.get_pending_approvals()
    approval_id = pending[0].approval_id
    
    success = manager.reject(
        approval_id,
        "manager_jane",
        "Quote too low, needs revision"
    )
    assert success
    
    # Wait for approval task
    approved = await approval_task
    assert not approved


@pytest.mark.asyncio
async def test_approval_timeout():
    """Test approval timeout."""
    manager = ApprovalManager()
    
    # Request approval with short timeout
    approved = await manager.request_approval(
        workflow_id="test_workflow_003",
        stage_name="technical",
        required_roles=["technical_lead"],
        context_data={},
        timeout=0.5
    )
    
    # Should timeout
    assert not approved


@pytest.mark.asyncio
async def test_template_manager():
    """Test template manager functionality."""
    manager = WorkflowTemplateManager()
    
    # List templates
    templates = manager.list_templates()
    assert len(templates) >= 4  # At least 4 default templates
    
    template_ids = [t.template_id for t in templates]
    assert 'standard_rfp' in template_ids
    assert 'fast_track_rfp' in template_ids
    assert 'complex_rfp' in template_ids
    assert 'simple_quote' in template_ids
    
    # Get specific template
    template = manager.get_template('standard_rfp')
    assert template is not None
    assert template.name == "Standard RFP Processing"
    assert len(template.stages) > 0
    
    # Test auto-selection
    rfp_data = {'priority': 'urgent', 'complexity': 'simple'}
    selected = manager.select_template(rfp_data)
    assert selected == 'fast_track_rfp'


@pytest.mark.asyncio
async def test_conditional_router():
    """Test conditional routing logic."""
    from workflows.workflow_extensions import StageConfig, BranchCondition
    
    # Create stage configs
    stages = [
        StageConfig('parsing', 'parser', 60.0),
        StageConfig('technical_validation', 'technical', 120.0,
                   skip_conditions=[BranchCondition.SKIP_IF_STANDARD_PRODUCT]),
        StageConfig('pricing', 'pricing', 60.0)
    ]
    
    # Test with standard product (should skip technical)
    context_standard = {'is_standard_product': True}
    should_skip = ConditionalRouter.should_skip_stage(stages[1], context_standard)
    assert should_skip
    
    # Test with custom product (should not skip)
    context_custom = {'is_standard_product': False}
    should_skip = ConditionalRouter.should_skip_stage(stages[1], context_custom)
    assert not should_skip
    
    # Test low value condition
    stage_low_value = StageConfig('review', 'reviewer', 30.0,
                                  skip_conditions=[BranchCondition.SKIP_IF_LOW_VALUE])
    context_low = {'estimated_value': 5000}
    should_skip = ConditionalRouter.should_skip_stage(stage_low_value, context_low)
    assert should_skip
    
    context_high = {'estimated_value': 50000}
    should_skip = ConditionalRouter.should_skip_stage(stage_low_value, context_high)
    assert not should_skip


@pytest.mark.asyncio
async def test_get_available_templates(setup_system):
    """Test getting available templates through orchestrator."""
    orchestrator, _ = setup_system
    
    templates = orchestrator.get_available_templates()
    
    assert len(templates) >= 4
    assert all('template_id' in t for t in templates)
    assert all('name' in t for t in templates)
    assert all('description' in t for t in templates)
    assert all('stages' in t for t in templates)
    assert all('estimated_duration' in t for t in templates)


@pytest.mark.asyncio
async def test_workflow_with_metadata(setup_system):
    """Test workflow stores template metadata."""
    orchestrator, _ = setup_system
    
    rfp = {
        'rfp_id': 'TEST010',
        'customer_id': 'CUST010',
        'priority': 'high'
    }
    
    result = await orchestrator.process_rfp(rfp, template_id='standard_rfp')
    
    # Check metadata
    assert 'workflow_info' in result
    assert 'template_id' in result['workflow_info']
    assert 'template_name' in result['workflow_info']
    assert result['workflow_info']['template_id'] == 'standard_rfp'


@pytest.mark.asyncio
async def test_multiple_templates_concurrent(setup_system):
    """Test running multiple templates concurrently."""
    orchestrator, _ = setup_system
    
    rfp1 = {'rfp_id': 'TEST011', 'customer_id': 'CUST011'}
    rfp2 = {'rfp_id': 'TEST012', 'customer_id': 'CUST012'}
    rfp3 = {'rfp_id': 'TEST013', 'customer_id': 'CUST013'}
    
    # Run with different templates
    results = await asyncio.gather(
        orchestrator.process_rfp(rfp1, template_id='standard_rfp'),
        orchestrator.process_rfp(rfp2, template_id='fast_track_rfp'),
        orchestrator.process_rfp(rfp3, template_id='simple_quote')
    )
    
    assert len(results) == 3
    assert results[0]['workflow_info']['template_id'] == 'standard_rfp'
    assert results[1]['workflow_info']['template_id'] == 'fast_track_rfp'
    assert results[2]['workflow_info']['template_id'] == 'simple_quote'
