"""
Comprehensive Test Suite for Enhanced Technical Agent.
"""
import pytest
import asyncio
from datetime import datetime
import json
from pathlib import Path

# Test fixtures and mocks


class MockRFPGenerator:
    """Generate mock RFPs for testing."""
    
    @staticmethod
    def generate_simple_rfp():
        """Generate simple single-item RFP."""
        return {
            'rfp_id': 'TEST-RFP-001',
            'title': 'Supply of Electrical Cable',
            'organization': 'Test Organization',
            'description': '4-core PVC insulated cable supply',
            'technical_requirements': [
                'PVC insulated 4-core cable, 2.5 sq.mm, 1.1kV, IS 694'
            ],
            'estimated_value': 100000.0
        }
    
    @staticmethod
    def generate_multi_item_rfp():
        """Generate multi-item RFP."""
        return {
            'rfp_id': 'TEST-RFP-002',
            'title': 'Complete Electrical Package',
            'organization': 'Test Organization',
            'description': 'Complete electrical equipment supply',
            'technical_requirements': [
                'PVC insulated 4-core cable, 2.5 sq.mm, 1.1kV',
                '16A MCB, single pole, 10kA breaking capacity',
                'LED tube light, 20W, 6500K'
            ],
            'estimated_value': 500000.0
        }
    
    @staticmethod
    def generate_complex_rfp():
        """Generate complex RFP with specifications."""
        return {
            'rfp_id': 'TEST-RFP-003',
            'title': 'Specialized Equipment Supply',
            'organization': 'Government Agency',
            'description': 'High-spec industrial equipment',
            'items': [
                {
                    'item_number': '001',
                    'name': 'Industrial Cable',
                    'description': 'Heavy duty cable for industrial use',
                    'quantity': 1000,
                    'unit': 'meters',
                    'specifications': {
                        'voltage': '11',
                        'current': '100',
                        'cores': '4',
                        'size_sqmm': '25'
                    },
                    'standards': ['IS 7098', 'IEC 60502'],
                    'certifications': ['BIS', 'ISO 9001'],
                    'max_price': 500.0
                }
            ],
            'estimated_value': 5000000.0
        }


class TestEnhancedTechnicalAgent:
    """Test suite for Enhanced Technical Agent."""
    
    @pytest.fixture
    def agent(self):
        """Create agent instance for testing."""
        from enhanced_technical_agent import EnhancedTechnicalAgent
        return EnhancedTechnicalAgent(
            enable_vector_search=False,  # Disable for faster tests
            enable_monitoring=True
        )
    
    @pytest.fixture
    def mock_rfp_generator(self):
        """Mock RFP generator."""
        return MockRFPGenerator()
    
    # Basic functionality tests
    
    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent is not None
        assert agent.base_agent is not None
        assert agent.requirement_extractor is not None
        assert agent.catalog_matcher is not None
    
    def test_process_simple_rfp(self, agent, mock_rfp_generator):
        """Test processing simple RFP."""
        rfp = mock_rfp_generator.generate_simple_rfp()
        result = agent.process_rfp(rfp, use_llm=False, use_vector_search=False)
        
        assert result['success'] == True
        assert result['rfp_id'] == 'TEST-RFP-001'
        assert 'summary' in result
        assert result['summary']['total_requirements'] > 0
    
    def test_process_multi_item_rfp(self, agent, mock_rfp_generator):
        """Test processing multi-item RFP."""
        rfp = mock_rfp_generator.generate_multi_item_rfp()
        result = agent.process_rfp(rfp, use_llm=False, use_vector_search=False)
        
        assert result['success'] == True
        assert result['summary']['total_requirements'] == 3
    
    def test_process_complex_rfp(self, agent, mock_rfp_generator):
        """Test processing complex RFP with structured items."""
        rfp = mock_rfp_generator.generate_complex_rfp()
        result = agent.process_rfp(rfp, use_llm=False, use_vector_search=False)
        
        assert result['success'] == True
        assert len(result['requirements']) > 0
    
    # Requirement extraction tests
    
    def test_requirement_extraction(self, agent, mock_rfp_generator):
        """Test requirement extraction."""
        rfp = mock_rfp_generator.generate_simple_rfp()
        requirements = agent.requirement_extractor.extract_requirements(rfp)
        
        assert len(requirements) > 0
        assert isinstance(requirements[0].item_number, str)
        assert isinstance(requirements[0].item_name, str)
    
    def test_specification_parsing(self, agent):
        """Test specification parsing from text."""
        text = "Supply 4-core cable, 2.5 sq.mm, 1.1kV, 50Hz, IP65 rated"
        specs = agent.requirement_extractor._parse_specifications(text)
        
        assert 'voltage' in specs or 'size_sqmm' in specs
    
    def test_standard_extraction(self, agent):
        """Test standard extraction."""
        text = "Product must comply with IS 694, IEC 60227, and IEEE 1234"
        standards = agent.requirement_extractor._extract_standards(text)
        
        assert len(standards) > 0
        assert any('IS' in s for s in standards)
    
    # Catalog matching tests
    
    def test_catalog_matcher(self, agent):
        """Test catalog matching."""
        from technical_agent import ProductRequirement
        
        req = ProductRequirement(
            item_number='001',
            item_name='Cable',
            description='Test cable',
            quantity=1,
            unit='nos',
            specifications={'voltage': '1.1', 'cores': '4'}
        )
        
        matches = agent.catalog_matcher.find_matches(req, top_k=3)
        assert isinstance(matches, list)
    
    def test_match_scoring(self, agent):
        """Test match scoring."""
        from technical_agent import ProductRequirement, ProductMatch
        
        req = ProductRequirement(
            item_number='001',
            item_name='Cable',
            description='Test',
            quantity=1,
            unit='nos',
            specifications={'voltage': '1.1'},
            required_certifications=['BIS']
        )
        
        match = ProductMatch(
            product_id='TEST-001',
            product_name='Test Product',
            manufacturer='Test',
            model_number='TEST',
            category='Cable',
            unit_price=100.0,
            moq=1,
            available_stock=100,
            specifications={'voltage': '1.1'},
            certifications=['BIS', 'ISI']
        )
        
        agent.catalog_matcher._calculate_scores(match, req)
        
        assert 0 <= match.overall_score <= 1
        assert match.specification_score >= 0
        assert match.certification_score >= 0
    
    # Comparison generation tests
    
    def test_comparison_generation(self, agent):
        """Test comparison table generation."""
        from technical_agent import ProductRequirement, ProductMatch
        
        req = ProductRequirement(
            item_number='001',
            item_name='Cable',
            description='Test',
            quantity=1,
            unit='nos'
        )
        
        matches = [
            ProductMatch(
                product_id=f'TEST-{i}',
                product_name=f'Product {i}',
                manufacturer='Test',
                model_number=f'M{i}',
                category='Cable',
                unit_price=100.0 + i,
                moq=1,
                available_stock=100,
                overall_score=0.9 - (i * 0.1),
                rank=i+1
            )
            for i in range(3)
        ]
        
        comparison = agent.comparison_generator.generate_comparison(req, matches, top_n=3)
        
        assert comparison is not None
        assert len(comparison.products) <= 3
        assert comparison.confidence_score > 0
    
    # Scope analysis tests
    
    def test_scope_analysis(self, agent, mock_rfp_generator):
        """Test scope of supply analysis."""
        rfp = mock_rfp_generator.generate_multi_item_rfp()
        rfp_text = f"{rfp['title']} {rfp['description']}"
        
        scope = agent.scope_analyzer.analyze_scope(rfp_text, rfp)
        
        assert 'total_items' in scope
        assert 'categories' in scope
        assert 'complexity_score' in scope
    
    def test_multi_item_handling(self, agent, mock_rfp_generator):
        """Test multi-item RFP handling."""
        rfp = mock_rfp_generator.generate_multi_item_rfp()
        items = [
            {'item_number': f'{i}', 'description': f'Item {i}', 'quantity': 10}
            for i in range(5)
        ]
        
        plan = agent.multi_item_handler.process_multi_item_rfp(rfp, items)
        
        assert 'total_items' in plan
        assert 'processing_plan' in plan
        assert 'batch_strategy' in plan
    
    # Gap analysis tests
    
    def test_gap_analysis(self, agent):
        """Test gap analysis generation."""
        requirement = {
            'item_name': 'Cable',
            'specifications': {'voltage': '1.1', 'cores': '4'},
            'required_certifications': ['BIS', 'CE']
        }
        
        matches = [{
            'product_id': 'TEST-001',
            'product_name': 'Test Cable',
            'specifications': {'voltage': '1.1'},
            'certifications': ['BIS'],
            'overall_score': 0.7
        }]
        
        gap_analysis = agent.gap_analyzer.generate_gap_analysis(requirement, matches)
        
        assert 'has_gaps' in gap_analysis
        assert 'gaps' in gap_analysis
        assert 'recommendations' in gap_analysis
    
    # Memory and context tests
    
    def test_memory_storage(self, agent, mock_rfp_generator):
        """Test memory storage."""
        rfp = mock_rfp_generator.generate_simple_rfp()
        result = agent.process_rfp(rfp, use_llm=False, use_vector_search=False)
        
        # Check memory stored
        assert len(agent.memory.long_term['rfp_history']) > 0
    
    def test_conversation_history(self, agent):
        """Test conversation history."""
        agent.memory.store_conversation('user', 'Test message')
        agent.memory.store_conversation('agent', 'Test response')
        
        history = agent.memory.get_conversation_context(last_n=2)
        assert len(history) == 2
    
    def test_context_management(self, agent):
        """Test context management."""
        agent.context_manager.push_context('test', {'key': 'value'})
        context = agent.context_manager.get_current_context()
        
        assert context is not None
        assert context['type'] == 'test'
        
        agent.context_manager.pop_context()
        assert agent.context_manager.get_current_context() is None
    
    # Monitoring and metrics tests
    
    def test_performance_tracking(self, agent, mock_rfp_generator):
        """Test performance tracking."""
        rfp = mock_rfp_generator.generate_simple_rfp()
        result = agent.process_rfp(rfp, use_llm=False, use_vector_search=False)
        
        metrics = agent.get_metrics()
        
        assert 'performance' in metrics
        assert metrics['performance']['total_requests'] > 0
    
    def test_qa_validation(self, agent, mock_rfp_generator):
        """Test QA validation."""
        rfp = mock_rfp_generator.generate_simple_rfp()
        result = agent.process_rfp(rfp, use_llm=False, use_vector_search=False)
        
        assert 'qa_report' in result
        assert 'quality' in result['qa_report']
        assert 'passed' in result['qa_report']
    
    def test_metrics_collection(self, agent, mock_rfp_generator):
        """Test metrics collection."""
        rfp = mock_rfp_generator.generate_simple_rfp()
        agent.process_rfp(rfp, use_llm=False, use_vector_search=False)
        
        metrics = agent.get_metrics()
        assert 'agent_statistics' in metrics
        assert 'memory_stats' in metrics
    
    # Batch processing tests
    
    def test_batch_processing(self, agent, mock_rfp_generator):
        """Test batch processing."""
        rfps = [
            mock_rfp_generator.generate_simple_rfp(),
            mock_rfp_generator.generate_multi_item_rfp()
        ]
        
        results = agent.process_batch(rfps)
        
        assert len(results) == 2
        assert all(r['success'] for r in results)
    
    @pytest.mark.asyncio
    async def test_async_processing(self, agent, mock_rfp_generator):
        """Test async processing."""
        rfp = mock_rfp_generator.generate_simple_rfp()
        result = await agent.process_rfp_async(rfp)
        
        assert result['success'] == True
    
    @pytest.mark.asyncio
    async def test_batch_async_processing(self, agent, mock_rfp_generator):
        """Test batch async processing."""
        rfps = [
            mock_rfp_generator.generate_simple_rfp(),
            mock_rfp_generator.generate_multi_item_rfp()
        ]
        
        results = await agent.process_batch_async(rfps)
        
        assert len(results) == 2
        assert all(r['success'] for r in results)
    
    # Edge case tests
    
    def test_empty_rfp(self, agent):
        """Test handling empty RFP."""
        rfp = {
            'rfp_id': 'EMPTY-001',
            'title': '',
            'description': '',
            'technical_requirements': []
        }
        
        result = agent.process_rfp(rfp, use_llm=False, use_vector_search=False)
        
        # Should handle gracefully
        assert 'success' in result
    
    def test_no_matches_found(self, agent):
        """Test handling when no matches found."""
        rfp = {
            'rfp_id': 'NOMATCH-001',
            'title': 'Impossible Product',
            'description': 'Non-existent product with impossible specs',
            'technical_requirements': [
                'Ultra-rare quantum cable with impossible specifications'
            ]
        }
        
        result = agent.process_rfp(rfp, use_llm=False, use_vector_search=False)
        
        # Should complete without errors
        assert 'success' in result
    
    def test_invalid_specifications(self, agent):
        """Test handling invalid specifications."""
        from technical_agent import ProductRequirement
        
        req = ProductRequirement(
            item_number='001',
            item_name='Invalid',
            description='Test',
            quantity=-1,  # Invalid
            unit='',
            specifications={'invalid_spec': 'bad_value'}
        )
        
        # Should not crash
        matches = agent.catalog_matcher.find_matches(req, top_k=3)
        assert isinstance(matches, list)
    
    # Integration tests
    
    def test_end_to_end_flow(self, agent, mock_rfp_generator):
        """Test complete end-to-end flow."""
        rfp = mock_rfp_generator.generate_complex_rfp()
        
        # Process
        result = agent.process_rfp(rfp, use_llm=False, use_vector_search=False)
        
        # Verify all components worked
        assert result['success'] == True
        assert 'scope_analysis' in result
        assert 'multi_item_plan' in result
        assert 'comparisons' in result
        assert 'qa_report' in result
        
        # Verify metrics updated
        metrics = agent.get_metrics()
        assert metrics['agent_statistics']['total_rfps_processed'] > 0
    
    def test_output_format(self, agent, mock_rfp_generator):
        """Test output format is correct."""
        rfp = mock_rfp_generator.generate_simple_rfp()
        result = agent.process_rfp(rfp, use_llm=False, use_vector_search=False)
        
        # Check required fields
        required_fields = [
            'success', 'rfp_id', 'rfp_title', 'processed_at',
            'processing_time_seconds', 'features_used', 'summary'
        ]
        
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"
    
    def test_export_comparison_tables(self, agent, mock_rfp_generator, tmp_path):
        """Test exporting comparison tables."""
        rfp = mock_rfp_generator.generate_simple_rfp()
        result = agent.process_rfp(rfp, use_llm=False, use_vector_search=False)
        
        # Export
        output_dir = str(tmp_path)
        excel_path = agent.base_agent.export_comparison_tables(result, output_dir)
        
        assert Path(excel_path).exists()


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
