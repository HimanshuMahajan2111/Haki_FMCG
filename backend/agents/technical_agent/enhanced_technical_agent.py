"""
Enhanced Technical Agent - Complete integration of all features.
"""
from typing import Dict, Any, List, Optional
import structlog
import asyncio
from datetime import datetime
from pathlib import Path
import time

# Import all components
from technical_agent import (
    TechnicalAgent,
    RequirementExtractor,
    CatalogMatcher,
    ComparisonGenerator,
    ProductRequirement,
    ProductMatch,
    ComparisonTable
)
from llm_integration import LLMSpecificationParser, ComplianceChecker
from vector_search import VectorSearchEngine, HybridMatcher
from scope_analyzer import ScopeOfSupplyAnalyzer, MultiItemRFPHandler, GapAnalysisGenerator
from memory_system import TechnicalAgentMemory, ContextManager
from api_interface import TechnicalAgentAPI, WebhookManager
from monitoring import PerformanceTracker, QualityAssurance, MetricsCollector

logger = structlog.get_logger()


class EnhancedTechnicalAgent:
    """
    Enhanced Technical Agent with all 50+ features integrated.
    
    Features:
    1. ✅ RFP requirement parser
    2. ✅ LLM integration for understanding specs
    3. ✅ Product requirement extractor
    4. ✅ Scope of supply analyzer
    5. ✅ Multi-item RFP handler
    6. ✅ Product catalog querier
    7. ✅ Specification matching orchestrator
    8. ✅ Vector search integration
    9. ✅ Weighted matching (hybrid)
    10. ✅ Top-K selector (K=3)
    11. ✅ Match score calculator
    12. ✅ Confidence scoring
    13. ✅ Comparison table generator
    14. ✅ Gap analysis generator
    15. ✅ Specification explanation generator
    16. ✅ Technical risk assessor
    17. ✅ Compliance checker
    18. ✅ Standard verification
    19. ✅ Technical summary generator
    20. ✅ Product recommendation ranker
    21. ✅ Alternative suggestion logic
    22. ✅ Custom product flagging
    23. ✅ Technical report formatter
    24. ✅ Visualization data generator
    25. ✅ Detailed spec comparison
    26. ✅ Match justification writer
    27. ✅ Edge case handlers
    28. ✅ Technical validation
    29. ✅ Output to pricing agent
    30. ✅ Output to main agent
    31. ✅ Technical agent memory
    32. ✅ Context management
    33. ✅ Conversation history
    34. ✅ Technical agent logging
    35. ✅ Performance tracking
    36. ✅ Error recovery mechanisms
    37. ✅ Technical agent tests
    38. ✅ Mock RFP handlers
    39. ✅ Integration test cases
    40. ✅ Technical agent metrics
    41. ✅ Latency tracking
    42. ✅ Success rate monitoring
    43. ✅ Quality assurance checks
    44. ✅ Technical agent dashboard (API)
    45. ✅ Real-time status updates
    46. ✅ Technical agent documentation
    47. ✅ API interface
    48. ✅ Webhook support
    49. ✅ Batch processing mode
    50. ✅ Async operation support
    """
    
    def __init__(
        self,
        catalog_path: Optional[str] = None,
        llm_provider: str = "openai",
        llm_api_key: Optional[str] = None,
        enable_vector_search: bool = True,
        memory_dir: str = "./memory",
        enable_monitoring: bool = True
    ):
        """Initialize Enhanced Technical Agent.
        
        Args:
            catalog_path: Path to product catalog
            llm_provider: LLM provider (openai/anthropic)
            llm_api_key: LLM API key
            enable_vector_search: Enable vector search
            memory_dir: Memory directory
            enable_monitoring: Enable monitoring
        """
        self.logger = logger.bind(component="EnhancedTechnicalAgent")
        
        # Core components
        self.base_agent = TechnicalAgent(catalog_path)
        self.requirement_extractor = RequirementExtractor()
        self.catalog_matcher = CatalogMatcher(catalog_path)
        self.comparison_generator = ComparisonGenerator()
        
        # LLM integration
        try:
            self.llm_parser = LLMSpecificationParser(llm_provider, llm_api_key)
            self.compliance_checker = ComplianceChecker(self.llm_parser)
            self.llm_enabled = True
        except Exception as e:
            self.logger.warning(f"LLM integration disabled: {e}")
            self.llm_parser = None
            self.compliance_checker = None
            self.llm_enabled = False
        
        # Vector search
        if enable_vector_search:
            try:
                self.vector_engine = VectorSearchEngine()
                self.vector_engine.index_products(self.catalog_matcher.catalog)
                self.hybrid_matcher = HybridMatcher(self.vector_engine)
                self.vector_enabled = True
            except Exception as e:
                self.logger.warning(f"Vector search disabled: {e}")
                self.vector_engine = None
                self.hybrid_matcher = None
                self.vector_enabled = False
        else:
            self.vector_engine = None
            self.hybrid_matcher = None
            self.vector_enabled = False
        
        # Scope analysis
        self.scope_analyzer = ScopeOfSupplyAnalyzer()
        self.multi_item_handler = MultiItemRFPHandler()
        self.gap_analyzer = GapAnalysisGenerator()
        
        # Memory and context
        self.memory = TechnicalAgentMemory(memory_dir)
        self.context_manager = ContextManager()
        
        # Monitoring
        if enable_monitoring:
            self.performance_tracker = PerformanceTracker()
            self.qa_system = QualityAssurance()
            self.metrics_collector = MetricsCollector()
            self.monitoring_enabled = True
        else:
            self.performance_tracker = None
            self.qa_system = None
            self.metrics_collector = None
            self.monitoring_enabled = False
        
        # API and webhooks
        self.api = None
        self.webhook_manager = WebhookManager()
        
        self.logger.info(
            "Enhanced Technical Agent initialized",
            llm_enabled=self.llm_enabled,
            vector_enabled=self.vector_enabled,
            monitoring_enabled=self.monitoring_enabled
        )
    
    def process_rfp(
        self,
        rfp_summary: Dict[str, Any],
        use_llm: bool = True,
        use_vector_search: bool = True
    ) -> Dict[str, Any]:
        """Process RFP with all enhanced features.
        
        Args:
            rfp_summary: RFP summary
            use_llm: Use LLM for enhanced processing
            use_vector_search: Use vector search
            
        Returns:
            Comprehensive processing result
        """
        start_time = time.time()
        component_timings = {}
        
        rfp_id = rfp_summary.get('rfp_id', 'unknown')
        self.logger.info("Processing RFP with enhanced features", rfp_id=rfp_id)
        
        # Set context
        self.context_manager.push_context('rfp', rfp_summary)
        self.memory.store_conversation('system', f"Processing RFP: {rfp_id}")
        
        try:
            # Step 1: Scope analysis
            scope_start = time.time()
            rfp_text = f"{rfp_summary.get('title', '')} {rfp_summary.get('description', '')}"
            scope_analysis = self.scope_analyzer.analyze_scope(rfp_text, rfp_summary)
            component_timings['scope_analysis'] = time.time() - scope_start
            
            # Step 2: Extract requirements (with LLM if enabled)
            extract_start = time.time()
            if use_llm and self.llm_enabled:
                # Use LLM for enhanced extraction
                enhanced_summary = self._enhance_with_llm(rfp_summary)
                requirements = self.requirement_extractor.extract_requirements(enhanced_summary)
            else:
                requirements = self.requirement_extractor.extract_requirements(rfp_summary)
            component_timings['requirement_extraction'] = time.time() - extract_start
            
            if not requirements:
                return self._handle_no_requirements(rfp_summary)
            
            # Step 3: Handle multi-item RFP
            multi_item_start = time.time()
            items = [{'item_number': r.item_number, 'description': r.description, 'quantity': r.quantity}
                     for r in requirements]
            multi_item_plan = self.multi_item_handler.process_multi_item_rfp(rfp_summary, items)
            component_timings['multi_item_handling'] = time.time() - multi_item_start
            
            # Step 4: Match and compare for each requirement
            comparisons = []
            all_matches = []
            
            for requirement in requirements:
                self.context_manager.push_context('requirement', requirement.to_dict())
                
                # Match products (hybrid if vector search enabled)
                match_start = time.time()
                if use_vector_search and self.vector_enabled:
                    matches_with_scores = self.hybrid_matcher.match(
                        requirement.to_dict(),
                        self.catalog_matcher.catalog,
                        top_k=10
                    )
                    # Convert to ProductMatch objects
                    matches = self._convert_hybrid_matches(matches_with_scores, requirement)
                else:
                    matches = self.catalog_matcher.find_matches(requirement, top_k=10)
                component_timings[f'matching_{requirement.item_number}'] = time.time() - match_start
                
                if matches:
                    # Generate comparison
                    comp_start = time.time()
                    comparison = self.comparison_generator.generate_comparison(
                        requirement,
                        matches,
                        top_n=3
                    )
                    component_timings[f'comparison_{requirement.item_number}'] = time.time() - comp_start
                    
                    # Gap analysis
                    gap_start = time.time()
                    gap_analysis = self.gap_analyzer.generate_gap_analysis(
                        requirement.to_dict(),
                        [m.to_dict() for m in matches]
                    )
                    component_timings[f'gap_analysis_{requirement.item_number}'] = time.time() - gap_start
                    
                    # Add enhanced information
                    enhanced_comparison = self._enhance_comparison(
                        comparison,
                        gap_analysis,
                        use_llm and self.llm_enabled
                    )
                    
                    comparisons.append(enhanced_comparison)
                    all_matches.extend(matches)
                    
                    # Store in memory
                    for match in matches[:3]:
                        self.memory.store_product_match(
                            requirement.to_dict(),
                            match.to_dict(),
                            match.overall_score
                        )
                
                self.context_manager.pop_context()
            
            # Generate result
            processing_time = time.time() - start_time
            
            result = {
                'success': True,
                'rfp_id': rfp_id,
                'rfp_title': rfp_summary.get('title', 'Unknown'),
                'processed_at': datetime.now().isoformat(),
                'processing_time_seconds': round(processing_time, 2),
                'features_used': {
                    'llm_processing': use_llm and self.llm_enabled,
                    'vector_search': use_vector_search and self.vector_enabled,
                    'scope_analysis': True,
                    'gap_analysis': True,
                    'multi_item_handling': True
                },
                'scope_analysis': scope_analysis,
                'multi_item_plan': multi_item_plan,
                'summary': {
                    'total_requirements': len(requirements),
                    'requirements_matched': len(comparisons),
                    'match_rate': round(len(comparisons) / len(requirements) * 100, 1) if requirements else 0,
                    'average_confidence': sum(c['confidence_score'] for c in comparisons) / len(comparisons) if comparisons else 0,
                    'total_matches_found': len(all_matches)
                },
                'requirements': [req.to_dict() for req in requirements],
                'comparisons': comparisons,
                'component_timings': component_timings
            }
            
            # QA validation
            if self.monitoring_enabled:
                qa_report = self.qa_system.validate_result(result)
                result['qa_report'] = qa_report
                
                # Record metrics
                self.performance_tracker.record_request(
                    processing_time,
                    True,
                    component_timings
                )
                
                for component, timing in component_timings.items():
                    self.metrics_collector.record_metric(
                        f"component_timing_{component}",
                        timing,
                        {'rfp_id': rfp_id}
                    )
            
            # Store in memory
            self.memory.store_rfp_processing(rfp_id, rfp_summary, result)
            
            self.logger.info(
                "RFP processing completed",
                rfp_id=rfp_id,
                requirements=len(requirements),
                matches=len(comparisons),
                processing_time=processing_time
            )
            
            return result
        
        except Exception as e:
            self.logger.error(f"RFP processing failed: {e}", exc_info=True)
            
            if self.monitoring_enabled:
                self.performance_tracker.record_request(
                    time.time() - start_time,
                    False
                )
            
            return {
                'success': False,
                'rfp_id': rfp_id,
                'error': str(e),
                'processed_at': datetime.now().isoformat()
            }
        
        finally:
            self.context_manager.pop_context()
    
    async def process_rfp_async(self, rfp_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Process RFP asynchronously.
        
        Args:
            rfp_summary: RFP summary
            
        Returns:
            Processing result
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.process_rfp, rfp_summary)
    
    def process_batch(self, rfp_summaries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple RFPs in batch.
        
        Args:
            rfp_summaries: List of RFP summaries
            
        Returns:
            List of processing results
        """
        self.logger.info(f"Processing batch of {len(rfp_summaries)} RFPs")
        
        results = []
        for rfp_summary in rfp_summaries:
            result = self.process_rfp(rfp_summary)
            results.append(result)
        
        return results
    
    async def process_batch_async(self, rfp_summaries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple RFPs asynchronously.
        
        Args:
            rfp_summaries: List of RFP summaries
            
        Returns:
            List of processing results
        """
        tasks = [self.process_rfp_async(rfp) for rfp in rfp_summaries]
        return await asyncio.gather(*tasks)
    
    def _enhance_with_llm(self, rfp_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance RFP summary with LLM parsing.
        
        Args:
            rfp_summary: Original RFP summary
            
        Returns:
            Enhanced RFP summary
        """
        enhanced = rfp_summary.copy()
        
        # Parse technical requirements with LLM
        tech_reqs = rfp_summary.get('technical_requirements', [])
        enhanced_reqs = []
        
        for req_text in tech_reqs:
            parsed = self.llm_parser.parse_technical_specification(req_text)
            enhanced_reqs.append({
                'original': req_text,
                **parsed
            })
        
        enhanced['technical_requirements_enhanced'] = enhanced_reqs
        
        return enhanced
    
    def _convert_hybrid_matches(
        self,
        matches_with_scores: List[tuple],
        requirement: ProductRequirement
    ) -> List[ProductMatch]:
        """Convert hybrid matcher results to ProductMatch objects.
        
        Args:
            matches_with_scores: List of (product, score) tuples
            requirement: Product requirement
            
        Returns:
            List of ProductMatch objects
        """
        product_matches = []
        
        for product, vector_score in matches_with_scores:
            match = ProductMatch(
                product_id=product['product_id'],
                product_name=product['product_name'],
                manufacturer=product['manufacturer'],
                model_number=product['model_number'],
                category=product['category'],
                unit_price=product['unit_price'],
                moq=product['moq'],
                available_stock=product['available_stock'],
                specifications=product.get('specifications', {}),
                certifications=product.get('certifications', []),
                standards_compliance=product.get('standards_compliance', []),
                delivery_days=product.get('delivery_days', 30)
            )
            
            # Calculate scores
            self.catalog_matcher._calculate_scores(match, requirement)
            
            # Blend vector score with calculated score
            match.overall_score = (match.overall_score * 0.7 + vector_score * 0.3)
            
            product_matches.append(match)
        
        # Re-rank
        product_matches.sort(key=lambda x: x.overall_score, reverse=True)
        for rank, match in enumerate(product_matches, 1):
            match.rank = rank
        
        return product_matches
    
    def _enhance_comparison(
        self,
        comparison: ComparisonTable,
        gap_analysis: Dict[str, Any],
        use_llm: bool
    ) -> Dict[str, Any]:
        """Enhance comparison with additional information.
        
        Args:
            comparison: Basic comparison
            gap_analysis: Gap analysis
            use_llm: Whether to use LLM
            
        Returns:
            Enhanced comparison dict
        """
        comp_dict = comparison.to_dict()
        comp_dict['gap_analysis'] = gap_analysis
        
        # Add LLM-generated content if enabled
        if use_llm and self.llm_enabled and comparison.products:
            top_product = comparison.products[0]
            
            # Risk assessment
            risk_assessment = self.llm_parser.assess_technical_risk(
                comparison.requirement.to_dict(),
                top_product.to_dict()
            )
            comp_dict['risk_assessment'] = risk_assessment
            
            # Match justification
            justification = self.llm_parser.generate_match_justification(
                comparison.requirement.to_dict(),
                top_product.to_dict(),
                top_product.overall_score
            )
            comp_dict['technical_justification'] = justification
            
            # Specification explanations
            explanations = {}
            for spec_key in comparison.requirement.specifications.keys():
                explanation = self.llm_parser.explain_specification(
                    spec_key,
                    comparison.requirement.specifications[spec_key]
                )
                explanations[spec_key] = explanation
            comp_dict['specification_explanations'] = explanations
            
            # Compliance verification
            if self.compliance_checker:
                compliance = self.compliance_checker.verify_standard_compliance(
                    top_product.to_dict(),
                    comparison.requirement.required_standards
                )
                comp_dict['compliance_verification'] = compliance
        
        return comp_dict
    
    def _handle_no_requirements(self, rfp_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Handle case where no requirements could be extracted.
        
        Args:
            rfp_summary: RFP summary
            
        Returns:
            Error result
        """
        return {
            'success': False,
            'rfp_id': rfp_summary.get('rfp_id', 'unknown'),
            'error': 'No requirements extracted',
            'message': 'Unable to extract product requirements from RFP',
            'suggestions': [
                'Provide more detailed technical specifications',
                'Include item-wise breakdown',
                'Add explicit product categories'
            ]
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics.
        
        Returns:
            Metrics dictionary
        """
        metrics = {
            'agent_statistics': self.base_agent.get_statistics(),
            'memory_stats': {
                'rfp_history_count': len(self.memory.long_term['rfp_history']),
                'product_preferences': len(self.memory.long_term['product_preferences']),
                'conversation_messages': len(self.memory.conversation_history)
            }
        }
        
        if self.monitoring_enabled:
            metrics['performance'] = self.performance_tracker.get_metrics()
            metrics['qa_statistics'] = self.qa_system.get_qa_statistics()
        
        return metrics
    
    def start_api_server(self, host: str = "0.0.0.0", port: int = 8000):
        """Start API server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
        """
        if not self.api:
            self.api = TechnicalAgentAPI(self)
        
        self.logger.info(f"Starting API server on {host}:{port}")
        self.api.run(host, port)


# Example usage
if __name__ == '__main__':
    # Initialize enhanced agent
    agent = EnhancedTechnicalAgent(
        enable_vector_search=True,
        enable_monitoring=True
    )
    
    # Sample RFP
    rfp_summary = {
        'rfp_id': 'RFP-2024-ENHANCED-001',
        'title': 'Supply of Electrical Equipment',
        'organization': 'Indian Railways',
        'description': 'Complete electrical equipment supply including cables, switchgear, and lighting',
        'technical_requirements': [
            'PVC insulated 4-core cable, 2.5 sq.mm, 1.1kV, IS 694 compliant, BIS certified',
            '16A MCB, single pole, 10kA breaking capacity, IS 8828 compliant',
            'LED tube light, 20W, 6500K, IP65 rated'
        ],
        'estimated_value': 10000000.0
    }
    
    # Process RFP
    result = agent.process_rfp(rfp_summary, use_llm=False, use_vector_search=True)
    
    # Print results
    print("\n" + "="*80)
    print("ENHANCED TECHNICAL AGENT - COMPREHENSIVE RESULTS")
    print("="*80)
    
    print(f"\nRFP: {result['rfp_title']}")
    print(f"Processing Time: {result['processing_time_seconds']}s")
    print(f"\nFeatures Used:")
    for feature, enabled in result['features_used'].items():
        print(f"  - {feature}: {'✅' if enabled else '❌'}")
    
    print(f"\n📊 Summary:")
    for key, value in result['summary'].items():
        print(f"  {key}: {value}")
    
    if result.get('qa_report'):
        print(f"\n✅ QA Report:")
        print(f"  Quality: {result['qa_report']['quality']}")
        print(f"  Issues: {result['qa_report']['issue_count']}")
        print(f"  Warnings: {result['qa_report']['warning_count']}")
    
    # Get metrics
    metrics = agent.get_metrics()
    print(f"\n📈 Metrics:")
    print(f"  Total RFPs Processed: {metrics['agent_statistics']['total_rfps_processed']}")
    if 'performance' in metrics:
        print(f"  Average Processing Time: {metrics['performance']['avg_processing_time']:.2f}s")
        print(f"  Success Rate: {metrics['performance']['success_rate']}%")
