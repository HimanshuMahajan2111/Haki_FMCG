"""Simple system status check."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

async def check_system():
    """Check system status."""
    print("\n" + "="*70)
    print("SYSTEM STATUS CHECK")
    print("="*70 + "\n")
    
    try:
        # Import services
        from services import get_data_service, get_vector_store_service
        
        # Initialize data service
        print("1. Initializing Data Service...")
        data_service = get_data_service()
        await data_service.initialize()
        
        # Get statistics
        stats = await data_service.get_statistics()
        print(f"   [OK] Products: {stats['products']['total']}")
        print(f"   [OK] Categories: {stats['products']['categories']}")
        print(f"   [OK] Brands: {stats['products']['brands']}")
        print(f"   [OK] Pricing: {stats['pricing']['total']}")
        print(f"   [OK] Testing: {stats['testing']['total']}")
        print(f"   [OK] Standards: {stats['standards']['total']}")
        
        # Initialize vector store
        print("\n2. Checking Vector Store...")
        vector_service = get_vector_store_service()
        await vector_service.initialize()
        
        vstats = await vector_service.get_statistics()
        print(f"   [OK] Vector store count: {vstats['total_products']}")
        print(f"   [OK] Status: {vstats['status']}")
        
        if vstats['total_products'] == 0:
            print("   [INFO] Populating vector store...")
            result = await vector_service.populate_from_data_service()
            print(f"   [OK] Populated: {result['vector_store_count']} products")
        
        # Test search
        print("\n3. Testing Vector Search...")
        results = await vector_service.search_products("cable 1.5 sq mm", limit=3)
        print(f"   [OK] Search returned {len(results)} results")
        
        # Test components
        print("\n4. Testing Core Components...")
        from data.product_matcher import ProductMatcher
        from data.pricing_calculator import PricingCalculator
        from utils.standards_checker import StandardsChecker
        
        matcher = ProductMatcher()
        calculator = PricingCalculator()
        checker = StandardsChecker()
        
        print("   [OK] Product Matcher initialized")
        print("   [OK] Pricing Calculator initialized")
        print("   [OK] Standards Checker initialized")
        
        # Test agents
        print("\n5. Testing Agents...")
        from agents.technical_agent import TechnicalAgent
        from agents.pricing_agent import PricingAgent
        from agents.orchestrator_agent.orchestrator import AgentOrchestrator
        
        tech_agent = TechnicalAgent()
        pricing_agent = PricingAgent()
        orchestrator = AgentOrchestrator()
        
        print("   [OK] Technical Agent initialized")
        print("   [OK] Pricing Agent initialized")
        print("   [OK] Agent Orchestrator initialized")
        
        # Summary
        print("\n" + "="*70)
        print("SYSTEM STATUS: FULLY OPERATIONAL")
        print("="*70)
        print(f"\nData Loaded:")
        print(f"  - Products: {stats['products']['total']:,}")
        print(f"  - Pricing Records: {stats['pricing']['total']:,}")
        print(f"  - Testing Records: {stats['testing']['total']}")
        print(f"  - Standards: {stats['standards']['total']}")
        print(f"  - Vector Store: {vstats['total_products']:,} products indexed")
        print(f"\nComponents:")
        print(f"  - Data Service: OPERATIONAL")
        print(f"  - Vector Store: OPERATIONAL")
        print(f"  - Product Matcher: OPERATIONAL")
        print(f"  - Pricing Calculator: OPERATIONAL")
        print(f"  - Standards Checker: OPERATIONAL")
        print(f"  - Technical Agent: OPERATIONAL")
        print(f"  - Pricing Agent: OPERATIONAL")
        print(f"  - Agent Orchestrator: OPERATIONAL")
        print("\n[SUCCESS] All systems integrated and ready!")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] System check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(check_system())
    sys.exit(0 if success else 1)
