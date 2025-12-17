"""Script to test all data loaders with validation."""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.validated_product_loader import ValidatedProductLoader
from data.testing_data_loader import TestingDataLoader
from data.standards_loader import StandardsDataLoader
from data.historical_rfp_loader import HistoricalRFPLoader
import structlog

# Setup logging
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()


async def test_product_loader():
    """Test product data loader."""
    logger.info("=" * 60)
    logger.info("Testing Product Data Loader")
    logger.info("=" * 60)
    
    loader = ValidatedProductLoader()
    products = await loader.load()
    
    logger.info(f"✓ Loaded {len(products)} products")
    
    # Show sample products
    if products:
        logger.info("\nSample Products:")
        for product in products[:3]:
            logger.info(f"  - {product.get('name')} ({product.get('brand')}) - {product.get('category')}")
    
    return products


async def test_testing_data_loader():
    """Test testing data loader."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Data Loader")
    logger.info("=" * 60)
    
    loader = TestingDataLoader()
    testing_data = await loader.load()
    
    for category, data in testing_data.items():
        if isinstance(data, list):
            logger.info(f"✓ {category}: {len(data)} records")
    
    # Show sample tests
    if testing_data.get('type_tests'):
        logger.info("\nSample Type Tests:")
        for test in testing_data['type_tests'][:3]:
            logger.info(f"  - {test.get('test_name')} ({test.get('standard')})")
    
    return testing_data


async def test_standards_loader():
    """Test standards data loader."""
    logger.info("\n" + "=" * 60)
    logger.info("Standards Data Loader")
    logger.info("=" * 60)
    
    loader = StandardsDataLoader()
    standards_data = await loader.load()
    
    for category, data in standards_data.items():
        if isinstance(data, list):
            logger.info(f"✓ {category}: {len(data)} records")
    
    # Show sample standards
    if standards_data.get('indian_standards'):
        logger.info("\nSample Indian Standards:")
        for std in standards_data['indian_standards'][:3]:
            logger.info(f"  - {std.get('standard_code')}: {std.get('title')}")
    
    return standards_data


async def test_historical_rfp_loader():
    """Test historical RFP loader."""
    logger.info("\n" + "=" * 60)
    logger.info("Historical RFP Data Loader")
    logger.info("=" * 60)
    
    loader = HistoricalRFPLoader()
    rfp_data = await loader.load()
    
    logger.info(f"✓ Loaded {len(rfp_data)} historical RFP records")
    
    # Show sample RFPs
    if rfp_data:
        logger.info("\nSample RFPs:")
        for rfp in rfp_data[:3]:
            logger.info(f"  - {rfp.get('rfp_id')}: {rfp.get('client_name')} - {rfp.get('title')}")
    
    return rfp_data


async def main():
    """Run all loader tests."""
    logger.info("\n" + "🚀 " * 20)
    logger.info("DATA LOADER VALIDATION TEST SUITE")
    logger.info("🚀 " * 20 + "\n")
    
    try:
        # Test all loaders
        products = await test_product_loader()
        testing_data = await test_testing_data_loader()
        standards_data = await test_standards_loader()
        rfp_data = await test_historical_rfp_loader()
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("SUMMARY")
        logger.info("=" * 60)
        logger.info(f"✓ Products loaded: {len(products)}")
        
        total_tests = sum(len(v) if isinstance(v, list) else 0 
                         for v in testing_data.values())
        logger.info(f"✓ Testing records loaded: {total_tests}")
        
        total_standards = sum(len(v) if isinstance(v, list) else 0 
                             for v in standards_data.values())
        logger.info(f"✓ Standards records loaded: {total_standards}")
        
        logger.info(f"✓ Historical RFPs loaded: {len(rfp_data)}")
        
        logger.info("\n✅ All data loaders tested successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
