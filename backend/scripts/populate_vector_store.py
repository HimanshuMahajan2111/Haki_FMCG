"""Script to populate vector store with products from data service."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services import get_vector_store_service


async def populate_vector_store(force: bool = False):
    """Populate vector store with products.
    
    Args:
        force: Force repopulation even if data exists
    """
    print("\n" + "="*60)
    print("VECTOR STORE POPULATION")
    print("="*60 + "\n")
    
    vector_service = get_vector_store_service()
    
    print("Initializing vector store service...")
    await vector_service.initialize()
    
    # Check current status
    stats = await vector_service.get_statistics()
    print(f"\nCurrent Status:")
    print(f"  - Products in vector store: {stats['total_products']}")
    print(f"  - Status: {stats['status']}")
    
    if stats['total_products'] > 0 and not force:
        print("\n⚠️  Vector store already contains products.")
        print("   Use --force flag to repopulate.")
        return
    
    print(f"\n{'Repopulating' if force else 'Populating'} vector store...")
    result = await vector_service.populate_from_data_service(force_repopulate=force)
    
    if result['status'] == 'success':
        print("\n✅ Population completed successfully!")
        print(f"\nResults:")
        print(f"  - Total products loaded: {result['total_products']}")
        print(f"  - Valid products: {result['valid_products']}")
        print(f"  - Vector store count: {result['vector_store_count']}")
        print(f"  - Action: {result['action']}")
    else:
        print(f"\n❌ Population failed: {result.get('message', 'Unknown error')}")
        return False
    
    # Verify with health check
    print("\nPerforming health check...")
    health = await vector_service.health_check()
    
    if health['status'] == 'healthy':
        print("✅ Vector store is healthy")
        print(f"   - Product count: {health['product_count']}")
        print(f"   - Search working: {health['search_working']}")
    else:
        print(f"❌ Health check failed: {health.get('error')}")
        return False
    
    # Test search
    print("\nTesting search functionality...")
    test_queries = [
        "copper wire",
        "ceiling fan",
        "circuit breaker"
    ]
    
    for query in test_queries:
        results = await vector_service.search_products(query, limit=3)
        print(f"\n   Query: '{query}' - Found {len(results)} results")
        if results:
            for i, r in enumerate(results[:2], 1):
                name = r.get("product_name") or r.get("name", "Unknown")
                print(f"      {i}. {name}")
    
    print("\n" + "="*60)
    print("✅ VECTOR STORE READY FOR USE")
    print("="*60 + "\n")
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Populate vector store with products")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force repopulation even if data exists"
    )
    
    args = parser.parse_args()
    
    success = asyncio.run(populate_vector_store(force=args.force))
    sys.exit(0 if success else 1)
