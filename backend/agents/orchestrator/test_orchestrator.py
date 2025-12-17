"""
Test suite for Main Orchestrator Agent
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from main_orchestrator import MainOrchestrator, WorkflowStatus, AgentStatus


def test_orchestrator_initialization():
    """Test orchestrator initialization."""
    print("\n" + "="*80)
    print("TEST 1: Orchestrator Initialization")
    print("="*80)
    
    orchestrator = MainOrchestrator()
    
    assert orchestrator is not None
    assert orchestrator.sales_agent is None
    assert orchestrator.technical_agent is None
    assert orchestrator.pricing_agent is None
    
    print("✅ Orchestrator initialized successfully")
    return True


def test_agent_registration():
    """Test agent registration."""
    print("\n" + "="*80)
    print("TEST 2: Agent Registration")
    print("="*80)
    
    orchestrator = MainOrchestrator()
    
    # Mock agents
    sales_agent = "MockSalesAgent"
    technical_agent = "MockTechnicalAgent"
    pricing_agent = "MockPricingAgent"
    
    orchestrator.register_agents(sales_agent, technical_agent, pricing_agent)
    
    assert orchestrator.sales_agent == sales_agent
    assert orchestrator.technical_agent == technical_agent
    assert orchestrator.pricing_agent == pricing_agent
    
    print("✅ All agents registered successfully")
    return True


def test_rfp_processing_workflow():
    """Test complete RFP processing workflow."""
    print("\n" + "="*80)
    print("TEST 3: RFP Processing Workflow")
    print("="*80)
    
    orchestrator = MainOrchestrator()
    
    # Sample RFP document
    rfp_document = {
        'rfp_id': 'TEST-RFP-001',
        'type': 'Government Tender',
        'urgency': 'Normal',
        'estimated_value': 1000000,
        'requirements': [
            {
                'product_name': 'FRLS Cable 1.5 sq mm',
                'quantity': 1000,
                'unit_price': 45.50,
                'specifications': 'IS 694:2010'
            },
            {
                'product_name': 'PVC Insulated Wire 2.5 sq mm',
                'quantity': 2000,
                'unit_price': 28.75,
                'specifications': 'IS 694:2010'
            }
        ]
    }
    
    customer_info = {
        'name': 'Test Government Department',
        'type': 'Government',
        'contact': {
            'email': 'test@gov.in',
            'phone': '+91-1234567890'
        },
        'distance_km': 500
    }
    
    # Process RFP
    success, workflow_state, rfp_response = orchestrator.process_rfp(
        rfp_document,
        customer_info
    )
    
    print(f"\nWorkflow Status: {workflow_state.status.value}")
    print(f"RFP ID: {workflow_state.rfp_id}")
    print(f"Workflow ID: {workflow_state.workflow_id}")
    print(f"Total Execution Time: {workflow_state.total_execution_time:.2f}s")
    
    if workflow_state.sales_result:
        print(f"\nSales Agent: {workflow_state.sales_result.status.value}")
        print(f"  Execution Time: {workflow_state.sales_result.execution_time_seconds:.2f}s")
    
    if workflow_state.technical_result:
        print(f"\nTechnical Agent: {workflow_state.technical_result.status.value}")
        print(f"  Execution Time: {workflow_state.technical_result.execution_time_seconds:.2f}s")
    
    if workflow_state.pricing_result:
        print(f"\nPricing Agent: {workflow_state.pricing_result.status.value}")
        print(f"  Execution Time: {workflow_state.pricing_result.execution_time_seconds:.2f}s")
    
    assert success is True
    assert workflow_state.status == WorkflowStatus.COMPLETED
    assert workflow_state.sales_result.status == AgentStatus.COMPLETED
    assert workflow_state.technical_result.status == AgentStatus.COMPLETED
    assert workflow_state.pricing_result.status == AgentStatus.COMPLETED
    assert rfp_response is not None
    
    print("\n✅ Complete workflow executed successfully")
    return True


def test_response_generation():
    """Test RFP response generation."""
    print("\n" + "="*80)
    print("TEST 4: RFP Response Generation")
    print("="*80)
    
    orchestrator = MainOrchestrator()
    
    rfp_document = {
        'rfp_id': 'TEST-RFP-002',
        'type': 'Enterprise',
        'requirements': [
            {
                'product_name': 'XLPE Power Cable',
                'quantity': 500,
                'unit_price': 520.00
            }
        ]
    }
    
    customer_info = {
        'name': 'Test Enterprise Corp',
        'type': 'Enterprise',
        'distance_km': 300
    }
    
    success, workflow_state, rfp_response = orchestrator.process_rfp(
        rfp_document,
        customer_info
    )
    
    assert rfp_response is not None
    assert rfp_response.rfp_id == 'TEST-RFP-002'
    assert rfp_response.customer_name == 'Test Enterprise Corp'
    assert rfp_response.executive_summary != ''
    assert rfp_response.compliance_matrix is not None
    assert len(rfp_response.compliance_matrix) > 0
    assert rfp_response.terms_and_conditions != ''
    
    print(f"\nResponse ID: {rfp_response.response_id}")
    print(f"Customer: {rfp_response.customer_name}")
    print(f"Valid Until: {rfp_response.valid_until}")
    print(f"Compliance Items: {len(rfp_response.compliance_matrix)}")
    
    print("\n✅ RFP response generated successfully")
    return True


def test_document_export():
    """Test document export functionality."""
    print("\n" + "="*80)
    print("TEST 5: Document Export")
    print("="*80)
    
    orchestrator = MainOrchestrator()
    
    rfp_document = {
        'rfp_id': 'TEST-RFP-003',
        'type': 'Standard',
        'requirements': [
            {
                'product_name': 'Test Cable',
                'quantity': 100,
                'unit_price': 50.00
            }
        ]
    }
    
    customer_info = {
        'name': 'Test Customer',
        'type': 'Standard',
        'distance_km': 200
    }
    
    success, workflow_state, rfp_response = orchestrator.process_rfp(
        rfp_document,
        customer_info
    )
    
    # Export response
    filepath = orchestrator.export_rfp_response(
        rfp_response,
        output_dir="test_outputs"
    )
    
    assert filepath is not None
    assert Path(filepath).exists()
    assert filepath.endswith('.xlsx')
    
    print(f"\nExported File: {filepath}")
    print(f"File Size: {Path(filepath).stat().st_size} bytes")
    
    print("\n✅ Document exported successfully")
    return True


def test_statistics_tracking():
    """Test statistics tracking."""
    print("\n" + "="*80)
    print("TEST 6: Statistics Tracking")
    print("="*80)
    
    orchestrator = MainOrchestrator()
    
    # Process multiple RFPs
    for i in range(3):
        rfp_document = {
            'rfp_id': f'TEST-RFP-STAT-{i+1}',
            'requirements': [
                {'product_name': f'Product {i+1}', 'quantity': 100, 'unit_price': 50.0}
            ]
        }
        
        customer_info = {
            'name': f'Customer {i+1}',
            'type': 'Standard',
            'distance_km': 200
        }
        
        orchestrator.process_rfp(rfp_document, customer_info)
    
    stats = orchestrator.get_statistics()
    
    print(f"\nTotal RFPs Processed: {stats['total_rfps_processed']}")
    print(f"Successful Responses: {stats['successful_responses']}")
    print(f"Failed Responses: {stats['failed_responses']}")
    print(f"Average Execution Time: {stats['average_execution_time']:.2f}s")
    print(f"Total Value Quoted: ₹{stats['total_value_quoted']:,.2f}")
    
    assert stats['total_rfps_processed'] == 3
    assert stats['successful_responses'] == 3
    assert stats['failed_responses'] == 0
    
    print("\n✅ Statistics tracked correctly")
    return True


def test_workflow_status_retrieval():
    """Test workflow status retrieval."""
    print("\n" + "="*80)
    print("TEST 7: Workflow Status Retrieval")
    print("="*80)
    
    orchestrator = MainOrchestrator()
    
    rfp_document = {
        'rfp_id': 'TEST-RFP-STATUS',
        'requirements': [
            {'product_name': 'Test Product', 'quantity': 50, 'unit_price': 100.0}
        ]
    }
    
    customer_info = {
        'name': 'Test Customer',
        'type': 'Standard',
        'distance_km': 150
    }
    
    success, workflow_state, rfp_response = orchestrator.process_rfp(
        rfp_document,
        customer_info
    )
    
    # Retrieve workflow status
    retrieved_state = orchestrator.get_workflow_status(workflow_state.workflow_id)
    
    assert retrieved_state is not None
    assert retrieved_state.workflow_id == workflow_state.workflow_id
    assert retrieved_state.status == WorkflowStatus.COMPLETED
    
    print(f"\nRetrieved Workflow: {retrieved_state.workflow_id}")
    print(f"Status: {retrieved_state.status.value}")
    print(f"RFP ID: {retrieved_state.rfp_id}")
    
    print("\n✅ Workflow status retrieved successfully")
    return True


def run_all_tests():
    """Run all orchestrator tests."""
    print("\n" + "🚀"*40)
    print("MAIN ORCHESTRATOR - COMPREHENSIVE TEST SUITE")
    print("🚀"*40)
    
    tests = [
        ("Orchestrator Initialization", test_orchestrator_initialization),
        ("Agent Registration", test_agent_registration),
        ("RFP Processing Workflow", test_rfp_processing_workflow),
        ("Response Generation", test_response_generation),
        ("Document Export", test_document_export),
        ("Statistics Tracking", test_statistics_tracking),
        ("Workflow Status Retrieval", test_workflow_status_retrieval)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n❌ {test_name} FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total Tests:  {len(tests)}")
    print(f"✅ Passed:    {passed}")
    print(f"❌ Failed:    {failed}")
    print(f"Pass Rate:    {passed/len(tests)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL ORCHESTRATOR TESTS PASSED! 🎉")
    else:
        print(f"\n⚠️ {failed} test(s) failed")
    
    print("="*80 + "\n")


if __name__ == "__main__":
    run_all_tests()
