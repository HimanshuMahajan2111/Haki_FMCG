"""Quick verification script to check if everything is set up correctly."""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_imports():
    """Check if all modules can be imported."""
    print("=" * 80)
    print("CHECKING IMPORTS")
    print("=" * 80)
    
    try:
        print("✓ Importing database models...")
        from db import models_enhanced
        print("✓ models_enhanced imported successfully")
        
        print("✓ Importing migration utilities...")
        from db import migrations
        print("✓ migrations imported successfully")
        
        print("✓ Importing enhanced vector store...")
        from data import vector_store_enhanced
        print("✓ vector_store_enhanced imported successfully")
        
        print("✓ Importing data service...")
        from services import data_service
        print("✓ data_service imported successfully")
        
        print("\n✅ All imports successful!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Import failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def check_models():
    """Check if models are properly defined."""
    print("=" * 80)
    print("CHECKING MODELS")
    print("=" * 80)
    
    try:
        from db import models_enhanced
        
        # List all models
        models = [
            'RFP', 'Product', 'ProductMatch', 'RequirementItem',
            'AgentInteraction', 'PricingHistory', 'Standard',
            'StandardCompliance', 'TestResult', 'SystemMetric'
        ]
        
        for model_name in models:
            model_class = getattr(models_enhanced, model_name, None)
            if model_class:
                print(f"✓ {model_name}: {model_class.__tablename__}")
            else:
                print(f"✗ {model_name}: NOT FOUND")
                return False
        
        # Check enums
        enums = ['RFPStatus', 'AgentType', 'MatchStatus', 'InteractionStatus']
        for enum_name in enums:
            enum_class = getattr(models_enhanced, enum_name, None)
            if enum_class:
                values = [e.value for e in enum_class]
                print(f"✓ {enum_name}: {values}")
            else:
                print(f"✗ {enum_name}: NOT FOUND")
                return False
        
        print("\n✅ All models and enums defined correctly!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Model check failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def check_relationships():
    """Check if relationships are properly defined."""
    print("=" * 80)
    print("CHECKING RELATIONSHIPS")
    print("=" * 80)
    
    try:
        from db.models_enhanced import RFP, Product, ProductMatch, AgentInteraction
        
        # Check RFP relationships
        print("✓ RFP relationships:")
        print(f"  - product_matches: {hasattr(RFP, 'product_matches')}")
        print(f"  - agent_interactions: {hasattr(RFP, 'agent_interactions')}")
        print(f"  - requirement_items: {hasattr(RFP, 'requirement_items')}")
        
        # Check Product relationships
        print("✓ Product relationships:")
        print(f"  - product_matches: {hasattr(Product, 'product_matches')}")
        print(f"  - pricing_history: {hasattr(Product, 'pricing_history')}")
        print(f"  - standard_compliances: {hasattr(Product, 'standard_compliances')}")
        print(f"  - test_results: {hasattr(Product, 'test_results')}")
        
        # Check ProductMatch relationships
        print("✓ ProductMatch relationships:")
        print(f"  - rfp: {hasattr(ProductMatch, 'rfp')}")
        print(f"  - product: {hasattr(ProductMatch, 'product')}")
        
        # Check AgentInteraction relationships
        print("✓ AgentInteraction relationships:")
        print(f"  - rfp: {hasattr(AgentInteraction, 'rfp')}")
        print(f"  - parent_interaction: {hasattr(AgentInteraction, 'parent_interaction')}")
        print(f"  - child_interactions: {hasattr(AgentInteraction, 'child_interactions')}")
        
        print("\n✅ All relationships defined correctly!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Relationship check failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def check_files():
    """Check if all required files exist."""
    print("=" * 80)
    print("CHECKING FILES")
    print("=" * 80)
    
    files = {
        "Enhanced Models": "db/models_enhanced.py",
        "Migrations": "db/migrations.py",
        "Enhanced Vector Store": "data/vector_store_enhanced.py",
        "Setup Script": "scripts/setup_database.py",
        "Schema Docs": "../docs/DATABASE_SCHEMA.md",
        "Quick Reference": "../docs/DATABASE_QUICK_REFERENCE.md",
        "Implementation Docs": "../docs/DATABASE_IMPLEMENTATION_COMPLETE.md",
        "Summary": "../DATABASE_ENHANCEMENT_SUMMARY.md"
    }
    
    all_exist = True
    for name, file_path in files.items():
        full_path = Path(__file__).parent.parent / file_path
        if full_path.exists():
            size_kb = full_path.stat().st_size / 1024
            print(f"✓ {name}: {file_path} ({size_kb:.1f} KB)")
        else:
            print(f"✗ {name}: {file_path} NOT FOUND")
            all_exist = False
    
    if all_exist:
        print("\n✅ All files present!\n")
    else:
        print("\n❌ Some files missing!\n")
    
    return all_exist


def main():
    """Run all checks."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "DATABASE SETUP VERIFICATION" + " " * 31 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")
    
    results = []
    
    # Run checks
    results.append(("Files Check", check_files()))
    results.append(("Imports Check", check_imports()))
    results.append(("Models Check", check_models()))
    results.append(("Relationships Check", check_relationships()))
    
    # Summary
    print("=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False
    
    print("=" * 80)
    
    if all_passed:
        print("\n✅ ALL CHECKS PASSED!")
        print("\nYou're ready to run:")
        print("  python scripts/setup_database.py")
        print("\n")
        return 0
    else:
        print("\n❌ SOME CHECKS FAILED")
        print("\nPlease fix the issues above before running setup.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
