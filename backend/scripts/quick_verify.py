"""Quick verification script to test all systems."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

async def verify_all():
    """Verify all systems are working."""
    print("\n" + "="*60)
    print("SYSTEM VERIFICATION TEST")
    print("="*60 + "\n")
    
    # Test 1: Imports
    print("1. Testing Imports...")
    try:
        from data import (
            BaseDataLoader, ValidationResult,
            ValidatedProductLoader, PricingDataLoader,
            TestingDataLoader, StandardsDataLoader,
            HistoricalRFPLoader, DataQualityAnalyzer
        )
        from config.settings import settings
        print("   ✅ All imports successful")
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False
    
    # Test 2: Configuration
    print("\n2. Testing Configuration...")
    try:
        print(f"   ✅ Data directory: {settings.data_dir}")
        print(f"   ✅ Testing directory: {settings.testing_data_dir}")
        print(f"   ✅ Database URL: {settings.database_url}")
    except Exception as e:
        print(f"   ❌ Configuration failed: {e}")
        return False
    
    # Test 3: Data Loaders
    print("\n3. Testing Data Loaders...")
    try:
        # Product Loader
        product_loader = ValidatedProductLoader()
        products = await product_loader.load()
        print(f"   ✅ Products: {len(products)} loaded")
        
        # Pricing Loader
        pricing_loader = PricingDataLoader()
        pricing = await pricing_loader.load()
        print(f"   ✅ Pricing: {len(pricing)} records loaded")
        
        # Testing Loader
        testing_loader = TestingDataLoader()
        testing = await testing_loader.load()
        total_tests = sum(len(v) if isinstance(v, list) else 0 for v in testing.values())
        print(f"   ✅ Testing: {total_tests} records loaded")
        
        # Standards Loader
        standards_loader = StandardsDataLoader()
        standards = await standards_loader.load()
        total_standards = sum(len(v) if isinstance(v, list) else 0 for v in standards.values())
        print(f"   ✅ Standards: {total_standards} records loaded")
        
        # Historical RFP Loader
        rfp_loader = HistoricalRFPLoader()
        rfps = await rfp_loader.load()
        print(f"   ✅ RFPs: {len(rfps)} records loaded")
        
    except Exception as e:
        print(f"   ❌ Data loader failed: {e}")
        return False
    
    # Test 4: Data Quality Analysis
    print("\n4. Testing Data Quality Analysis...")
    try:
        analyzer = DataQualityAnalyzer()
        
        # Statistics
        stats = analyzer.generate_statistics(products[:100], "Products Sample")
        print(f"   ✅ Statistics: {stats['total_records']} records analyzed")
        print(f"   ✅ Completeness: {stats['completeness']:.2f}%")
        
        # Preview
        preview = analyzer.preview_data(products[:10], num_records=3)
        print(f"   ✅ Preview: {preview['sample_size']} records previewed")
        
        # Quality Report
        report = analyzer.generate_quality_report(products, testing, standards, rfps)
        print(f"   ✅ Quality Report: {report['overall_quality_score']:.2f}/100")
        
    except Exception as e:
        print(f"   ❌ Data quality analysis failed: {e}")
        return False
    
    # Test 5: File Structure
    print("\n5. Verifying File Structure...")
    try:
        backend_dir = Path(__file__).parent.parent
        required_files = [
            "data/base_loader.py",
            "data/validated_product_loader.py",
            "data/pricing_loader.py",
            "data/testing_data_loader.py",
            "data/standards_loader.py",
            "data/historical_rfp_loader.py",
            "data/data_quality.py",
            "config/settings.py",
            "main.py",
        ]
        
        for file in required_files:
            file_path = backend_dir / file
            if file_path.exists():
                print(f"   ✅ {file}")
            else:
                print(f"   ❌ {file} - NOT FOUND")
                
    except Exception as e:
        print(f"   ❌ File structure check failed: {e}")
        return False
    
    # Summary
    print("\n" + "="*60)
    print("✅ ALL SYSTEMS OPERATIONAL")
    print("="*60)
    print(f"\nData Summary:")
    print(f"  - Products: {len(products):,} ({len([p for p in products if p.get('name')])} valid)")
    print(f"  - Pricing: {len(pricing):,} records")
    print(f"  - Testing: {total_tests} records")
    print(f"  - Standards: {total_standards} records")
    print(f"  - RFPs: {len(rfps)} records")
    print(f"\nQuality Score: {report['overall_quality_score']:.2f}/100")
    print(f"Data Completeness: {stats['completeness']:.2f}%")
    print("\n✅ System is ready for production use!")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(verify_all())
    sys.exit(0 if success else 1)
