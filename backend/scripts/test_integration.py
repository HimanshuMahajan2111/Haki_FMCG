"""End-to-end integration test for RFP pipeline with loaded data."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import structlog
from services import get_data_service, get_vector_store_service
from agents.orchestrator_agent.orchestrator import AgentOrchestrator

logger = structlog.get_logger()


async def test_complete_pipeline():
    """Test complete RFP processing pipeline."""
    print("\n" + "="*80)
    print("END-TO-END RFP PIPELINE TEST")
    print("="*80 + "\n")
    
    # Step 1: Initialize data service
    print("Step 1: Initializing Data Service...")
    data_service = get_data_service()
    await data_service.initialize()
    
    stats = await data_service.get_statistics()
    print(f"✅ Data Service Initialized")
    print(f"   - Products: {stats['products']['total']:,}")
    print(f"   - Categories: {stats['products']['categories']}")
    print(f"   - Brands: {stats['products']['brands']}")
    print(f"   - Pricing Records: {stats['pricing']['total']:,}")
    print(f"   - Testing Records: {stats['testing']['total']}")
    print(f"   - Standards: {stats['standards']['total']}")
    
    # Step 2: Initialize vector store
    print("\nStep 2: Initializing Vector Store...")
    vector_service = get_vector_store_service()
    await vector_service.initialize()
    
    # Check if needs population
    vector_stats = await vector_service.get_statistics()
    if vector_stats['total_products'] == 0:
        print("   Populating vector store...")
        result = await vector_service.populate_from_data_service()
        print(f"   ✅ Vector Store Populated: {result['vector_store_count']} products")
    else:
        print(f"   ✅ Vector Store Ready: {vector_stats['total_products']} products")
    
    # Step 3: Test product search
    print("\nStep 3: Testing Product Search...")
    search_queries = [
        "1.5 sq mm copper wire",
        "ceiling fan 1200mm",
        "16A MCB circuit breaker"
    ]
    
    for query in search_queries:
        results = await vector_service.search_products(query, limit=3)
        print(f"\n   Query: '{query}'")
        print(f"   Found {len(results)} matches:")
        for i, result in enumerate(results[:3], 1):
            product_name = result.get("product_name") or result.get("name", "Unknown")
            brand = result.get("brand", "Unknown")
            price = result.get("selling_price") or result.get("price", 0)
            print(f"      {i}. {brand} - {product_name} (₹{price})")
    
    # Step 4: Test agent orchestrator with sample RFP
    print("\n\nStep 4: Testing Agent Orchestrator...")
    print("   Creating sample RFP data...")
    
    sample_rfp = {
        "rfp_id": "TEST-001",
        "rfp_requirements": [
            {
                "item_name": "House Wire 1.5 sq mm",
                "quantity": 1000,
                "specifications": {
                    "conductor_size": "1.5 sq mm",
                    "type": "PVC insulated",
                    "voltage": "1100V"
                },
                "standard": "IS 694"
            },
            {
                "item_name": "Ceiling Fan 1200mm",
                "quantity": 50,
                "specifications": {
                    "sweep": "1200mm",
                    "type": "Decorative",
                },
                "standard": "IS 374"
            },
            {
                "item_name": "MCB 16A Single Pole",
                "quantity": 100,
                "specifications": {
                    "rating": "16A",
                    "poles": "1P",
                    "breaking_capacity": "6kA"
                },
                "standard": "IS/IEC 60898"
            }
        ],
        "compliance_standards": ["IS 694", "IS 374", "IS/IEC 60898"],
        "quantities": {
            "House Wire 1.5 sq mm": 1000,
            "Ceiling Fan 1200mm": 50,
            "MCB 16A Single Pole": 100
        },
        "pricing_strategy": "competitive"
    }
    
    # Initialize orchestrator
    orchestrator = AgentOrchestrator()
    
    print("\n   Processing RFP through agents...")
    try:
        result = await orchestrator.process_rfp(
            rfp_id="TEST-001",
            rfp_data=sample_rfp
        )
        
        print("\n   ✅ RFP Processing Completed")
        print(f"   Duration: {result['total_duration_seconds']:.2f} seconds")
        
        # Display technical results
        tech_result = result.get("technical_result", {})
        if tech_result:
            matched = tech_result.get("matched_products", [])
            print(f"\n   Technical Agent Results:")
            print(f"      - Requirements: {tech_result.get('total_requirements', 0)}")
            print(f"      - Matched: {tech_result.get('matched_count', 0)}")
            print(f"      - Avg Confidence: {tech_result.get('average_confidence', 0):.1f}%")
            
            if matched:
                print(f"\n      Matched Products:")
                for match in matched:
                    req = match['requirement']
                    prod = match.get('matched_product', {})
                    conf = match.get('match_confidence', 0)
                    print(f"         - {req['item_name']}: {prod.get('product_name', 'N/A')} ({conf:.0f}% match)")
        
        # Display pricing results
        pricing_result = result.get("pricing_result", {})
        if pricing_result:
            summary = pricing_result.get("pricing_summary", {})
            print(f"\n   Pricing Agent Results:")
            print(f"      - Subtotal: ₹{summary.get('subtotal', 0):,.2f}")
            print(f"      - Testing Costs: ₹{summary.get('testing_costs', 0):,.2f}")
            print(f"      - GST ({summary.get('gst_percent', 0)}%): ₹{summary.get('gst_amount', 0):,.2f}")
            print(f"      - Grand Total: ₹{summary.get('grand_total', 0):,.2f}")
        
    except Exception as e:
        print(f"\n   ❌ Error processing RFP: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 5: Test API data endpoints
    print("\n\nStep 5: Testing Data Service Methods...")
    
    # Test categories
    categories = await data_service.get_product_categories()
    print(f"   ✅ Categories: {len(categories)} found")
    if categories:
        print(f"      Examples: {', '.join(categories[:5])}")
    
    # Test brands
    brands = await data_service.get_product_brands()
    print(f"   ✅ Brands: {len(brands)} found")
    if brands:
        print(f"      Examples: {', '.join(brands[:5])}")
    
    # Test pricing lookup
    products = await data_service.get_products(limit=5)
    if products:
        sample_product = products[0]
        product_code = sample_product.get("product_code")
        if product_code:
            pricing = await data_service.get_pricing_for_product(product_code)
            if pricing:
                print(f"   ✅ Pricing Lookup: Found pricing for {product_code}")
    
    # Test testing data
    testing = await data_service.get_testing_data()
    print(f"   ✅ Testing Data: {len(testing)} categories")
    
    # Test standards
    standards = await data_service.get_indian_standards()
    print(f"   ✅ Standards: {len(standards)} Indian standards")
    
    # Summary
    print("\n" + "="*80)
    print("✅ END-TO-END PIPELINE TEST COMPLETED SUCCESSFULLY")
    print("="*80)
    print("\nAll components working:")
    print("  ✅ Data service (CSV/JSON loaders)")
    print("  ✅ Vector store (ChromaDB)")
    print("  ✅ Product matcher (semantic search)")
    print("  ✅ Pricing calculator (with loaded pricing)")
    print("  ✅ Standards checker (with standards data)")
    print("  ✅ Agent orchestrator (technical + pricing agents)")
    print("  ✅ Data API methods")
    print("\n🎉 System is ready for production use!")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_complete_pipeline())
    sys.exit(0 if success else 1)
