"""Test script for data quality analysis."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data import (
    ValidatedProductLoader,
    TestingDataLoader,
    StandardsDataLoader,
    HistoricalRFPLoader,
    PricingDataLoader,
    DataQualityAnalyzer
)
import structlog
import json

logger = structlog.get_logger()


async def test_pricing_loader():
    """Test pricing data loader."""
    logger.info("=" * 60)
    logger.info("Testing Pricing Data Loader")
    logger.info("=" * 60)
    
    loader = PricingDataLoader()
    pricing_data = await loader.load()
    
    logger.info(f"✓ Loaded {len(pricing_data)} pricing records")
    
    # Show sample
    logger.info("\nSample Pricing Records:")
    for record in pricing_data[:3]:
        logger.info(f"  - {record.get('product_id')}: ₹{record.get('price', 0):.2f} ({record.get('brand')})")
    
    return pricing_data


async def test_data_statistics():
    """Test data statistics generation."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Data Statistics")
    logger.info("=" * 60)
    
    # Load sample data
    product_loader = ValidatedProductLoader()
    products = await product_loader.load()
    
    # Generate statistics
    analyzer = DataQualityAnalyzer()
    stats = analyzer.generate_statistics(products[:100], "Products Sample")
    
    logger.info(f"\n✓ Generated statistics for {stats['total_records']} records")
    logger.info(f"  - Data completeness: {stats['completeness']:.2f}%")
    logger.info(f"  - Field count: {len(stats['field_analysis'])}")
    logger.info(f"  - Duplicate issues: {len(stats['duplicates'])}")
    
    # Show field analysis
    logger.info("\nTop 5 Fields by Completeness:")
    sorted_fields = sorted(
        stats['field_analysis'].items(),
        key=lambda x: x[1]['completeness'],
        reverse=True
    )[:5]
    
    for field, info in sorted_fields:
        logger.info(f"  - {field}: {info['completeness']:.1f}% complete")
    
    return stats


async def test_data_preview():
    """Test data preview functionality."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Data Preview")
    logger.info("=" * 60)
    
    # Load sample data
    testing_loader = TestingDataLoader()
    testing_data = await testing_loader.load()
    
    analyzer = DataQualityAnalyzer()
    
    # Preview each category
    for category, data in testing_data.items():
        if isinstance(data, list) and data:
            preview = analyzer.preview_data(data, num_records=2)
            logger.info(f"\n✓ {category.upper()} Preview:")
            logger.info(f"  - Total records: {preview['total_records']}")
            logger.info(f"  - Fields: {preview['field_count']}")
            logger.info(f"  - Sample records: {preview['sample_size']}")


async def test_quality_report():
    """Test comprehensive quality report generation."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Quality Report Generation")
    logger.info("=" * 60)
    
    # Load all data
    logger.info("Loading all datasets...")
    product_loader = ValidatedProductLoader()
    testing_loader = TestingDataLoader()
    standards_loader = StandardsDataLoader()
    rfp_loader = HistoricalRFPLoader()
    
    products = await product_loader.load()
    testing = await testing_loader.load()
    standards = await standards_loader.load()
    rfps = await rfp_loader.load()
    
    # Generate report
    analyzer = DataQualityAnalyzer()
    report = analyzer.generate_quality_report(products, testing, standards, rfps)
    
    logger.info("\n✓ COMPREHENSIVE QUALITY REPORT")
    logger.info(f"  Generated at: {report['generated_at']}")
    logger.info(f"  Overall Quality Score: {report['overall_quality_score']:.2f}/100")
    
    logger.info("\n  Dataset Summaries:")
    for dataset, summary in report['summary'].items():
        if isinstance(summary, dict):
            status = summary.get('status', 'unknown')
            count = summary.get('count', summary.get('total_records', 0))
            logger.info(f"    - {summary.get('name', dataset)}: {count} records ({status})")
    
    logger.info("\n  Quality Scores:")
    for dataset, score in report['quality_scores'].items():
        logger.info(f"    - {dataset}: {score:.2f}/100")
    
    if report['issues']:
        logger.info("\n  Issues Found:")
        for issue in report['issues']:
            severity = issue['severity'].upper()
            logger.info(f"    - [{severity}] {issue['dataset']}: {issue['issue']}")
    
    if report['recommendations']:
        logger.info("\n  Recommendations:")
        for i, rec in enumerate(report['recommendations'], 1):
            logger.info(f"    {i}. {rec}")
    
    # Save report to file
    report_file = Path(__file__).parent.parent / "data_quality_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n✓ Report saved to: {report_file}")
    
    return report


async def main():
    """Run all data quality tests."""
    logger.info("\n🚀 " * 20)
    logger.info("DATA QUALITY TESTING SUITE")
    logger.info("🚀 " * 20)
    
    try:
        # Test 1: Pricing Loader
        await test_pricing_loader()
        
        # Test 2: Data Statistics
        await test_data_statistics()
        
        # Test 3: Data Preview
        await test_data_preview()
        
        # Test 4: Quality Report
        await test_quality_report()
        
        logger.info("\n" + "=" * 60)
        logger.info("SUMMARY")
        logger.info("=" * 60)
        logger.info("✓ PricingDataLoader: Working")
        logger.info("✓ Data Statistics: Working")
        logger.info("✓ Data Preview: Working")
        logger.info("✓ Quality Report: Working")
        logger.info("\n✅ All data quality tests completed successfully!")
        
    except Exception as e:
        logger.error("Test failed", error=str(e), exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
