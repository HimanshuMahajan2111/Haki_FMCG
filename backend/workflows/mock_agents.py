"""Mock agent implementations for RFP workflow demonstration.

These are simplified mock agents that simulate the behavior of real agents
for demonstration and testing purposes.
"""
import asyncio
import uuid
from typing import Dict, Any
import random
import structlog

logger = structlog.get_logger()


class MockRFPParserAgent:
    """Mock RFP parsing agent."""
    
    def __init__(self, comm_manager):
        self.comm_manager = comm_manager
        self.agent_id = "rfp_parser_agent"
    
    async def initialize(self):
        """Initialize agent."""
        await self.comm_manager.register_agent(
            self.agent_id,
            "parser",
            capabilities=["document_parsing", "text_extraction"]
        )
        
        async def handle_request(msg):
            await asyncio.sleep(0.5)  # Simulate processing
            
            # Mock parsing result
            response = {
                'status': 'success',
                'sections': [
                    {'type': 'executive_summary', 'content': '...'},
                    {'type': 'requirements', 'content': '...'},
                    {'type': 'specifications', 'content': '...'}
                ],
                'requirements': [
                    {'id': 'REQ001', 'description': '1100V Cables', 'quantity': 1000},
                    {'id': 'REQ002', 'description': '600V Wires', 'quantity': 500}
                ],
                'metadata': {
                    'pages': 25,
                    'sections': 8,
                    'tables': 3
                },
                'confidence_score': 0.92
            }
            
            await self.comm_manager.send_response(msg, response)
        
        await self.comm_manager.register_handler(self.agent_id, "request", handle_request)
        logger.info(f"{self.agent_id} initialized")


class MockSalesAgent:
    """Mock sales agent."""
    
    def __init__(self, comm_manager):
        self.comm_manager = comm_manager
        self.agent_id = "sales_agent"
    
    async def initialize(self):
        """Initialize agent."""
        await self.comm_manager.register_agent(
            self.agent_id,
            "sales",
            capabilities=["requirements_analysis", "customer_intelligence"]
        )
        
        async def handle_request(msg):
            await asyncio.sleep(0.7)  # Simulate processing
            
            requirements = msg.payload.get('requirements', [])
            
            response = {
                'status': 'success',
                'line_items': [
                    {
                        'item_id': 'ITEM001',
                        'product': 'High Voltage Cable 1100V',
                        'quantity': 1000,
                        'unit': 'meters',
                        'specifications': 'IS 694 compliant'
                    },
                    {
                        'item_id': 'ITEM002',
                        'product': 'Medium Voltage Wire 600V',
                        'quantity': 500,
                        'unit': 'meters',
                        'specifications': 'IS 1554 compliant'
                    }
                ],
                'customer_context': {
                    'tier': 'premium',
                    'history': 'long-term',
                    'payment_terms_preference': 'Net 30'
                },
                'opportunity_score': 0.85,
                'recommended_products': ['Cable Type A', 'Wire Type B'],
                'delivery_terms': {
                    'method': 'FOB',
                    'location': 'Mumbai Port'
                },
                'payment_terms': {
                    'type': 'Net 30',
                    'advance': 20
                }
            }
            
            await self.comm_manager.send_response(msg, response)
        
        await self.comm_manager.register_handler(self.agent_id, "request", handle_request)
        logger.info(f"{self.agent_id} initialized")


class MockTechnicalAgent:
    """Mock technical agent."""
    
    def __init__(self, comm_manager):
        self.comm_manager = comm_manager
        self.agent_id = "technical_agent"
    
    async def initialize(self):
        """Initialize agent."""
        await self.comm_manager.register_agent(
            self.agent_id,
            "technical",
            capabilities=["specifications_validation", "compliance_checking"]
        )
        
        async def handle_request(msg):
            await asyncio.sleep(0.8)  # Simulate processing
            
            line_items = msg.payload.get('line_items', [])
            
            response = {
                'status': 'success',
                'validated_products': [
                    {
                        'item_id': 'ITEM001',
                        'product': 'High Voltage Cable 1100V',
                        'validated': True,
                        'specifications_met': ['IS 694', 'IEC 60227'],
                        'test_reports': ['TR001', 'TR002']
                    },
                    {
                        'item_id': 'ITEM002',
                        'product': 'Medium Voltage Wire 600V',
                        'validated': True,
                        'specifications_met': ['IS 1554', 'IEC 60227'],
                        'test_reports': ['TR003']
                    }
                ],
                'compliance_report': {
                    'total_items': len(line_items),
                    'compliant_items': len(line_items),
                    'non_compliant_items': 0
                },
                'standards_met': ['IS 694', 'IS 1554', 'IEC 60227'],
                'certifications': ['ISI', 'BIS', 'CE'],
                'technical_notes': [
                    'All products meet required standards',
                    'Testing certificates available'
                ],
                'compliance_score': 0.96
            }
            
            await self.comm_manager.send_response(msg, response)
        
        await self.comm_manager.register_handler(self.agent_id, "request", handle_request)
        logger.info(f"{self.agent_id} initialized")


class MockPricingAgent:
    """Mock pricing agent."""
    
    def __init__(self, comm_manager):
        self.comm_manager = comm_manager
        self.agent_id = "pricing_agent"
    
    async def initialize(self):
        """Initialize agent."""
        await self.comm_manager.register_agent(
            self.agent_id,
            "pricing",
            capabilities=["price_calculation", "discount_application"]
        )
        
        async def handle_request(msg):
            await asyncio.sleep(0.6)  # Simulate processing
            
            line_items = msg.payload.get('line_items', [])
            
            # Calculate mock pricing
            line_item_prices = []
            subtotal = 0.0
            
            for item in line_items:
                unit_price = random.uniform(45.0, 75.0)
                quantity = item.get('quantity', 1)
                amount = unit_price * quantity
                subtotal += amount
                
                line_item_prices.append({
                    'item_id': item.get('item_id'),
                    'product': item.get('product'),
                    'quantity': quantity,
                    'unit_price': round(unit_price, 2),
                    'amount': round(amount, 2)
                })
            
            # Apply discount
            discount = subtotal * 0.05  # 5% discount
            subtotal_after_discount = subtotal - discount
            taxes = subtotal_after_discount * 0.18  # 18% GST
            total = subtotal_after_discount + taxes
            
            response = {
                'status': 'success',
                'quote_id': f'Q{uuid.uuid4().hex[:8].upper()}',
                'line_item_prices': line_item_prices,
                'subtotal': round(subtotal, 2),
                'taxes': round(taxes, 2),
                'total': round(total, 2),
                'discounts_applied': [
                    {'type': 'volume_discount', 'percentage': 5, 'amount': round(discount, 2)}
                ],
                'payment_terms': {
                    'type': 'Net 30',
                    'advance_required': 20,
                    'milestone_payments': []
                },
                'validity_period': 30
            }
            
            await self.comm_manager.send_response(msg, response)
        
        await self.comm_manager.register_handler(self.agent_id, "request", handle_request)
        logger.info(f"{self.agent_id} initialized")


class MockResponseGeneratorAgent:
    """Mock response generator agent."""
    
    def __init__(self, comm_manager):
        self.comm_manager = comm_manager
        self.agent_id = "response_generator_agent"
    
    async def initialize(self):
        """Initialize agent."""
        await self.comm_manager.register_agent(
            self.agent_id,
            "generator",
            capabilities=["document_generation", "formatting"]
        )
        
        async def handle_request(msg):
            await asyncio.sleep(0.5)  # Simulate processing
            
            response = {
                'status': 'success',
                'document': {
                    'format': 'pdf',
                    'pages': 15,
                    'sections': ['cover', 'executive_summary', 'technical', 'pricing', 'terms']
                },
                'executive_summary': 'We are pleased to submit our comprehensive proposal...',
                'technical_section': {
                    'products': 'Complete product specifications included',
                    'compliance': 'All standards and certifications provided'
                },
                'pricing_section': {
                    'quote_reference': msg.payload.get('pricing', {}).get('quote_id', 'N/A'),
                    'validity': '30 days'
                },
                'terms_conditions': {
                    'payment': 'Net 30 with 20% advance',
                    'delivery': 'FOB Mumbai Port',
                    'warranty': '12 months'
                },
                'format': 'pdf'
            }
            
            await self.comm_manager.send_response(msg, response)
        
        await self.comm_manager.register_handler(self.agent_id, "request", handle_request)
        logger.info(f"{self.agent_id} initialized")
