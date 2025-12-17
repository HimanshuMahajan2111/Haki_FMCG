"""
Match products from all RFPs against the 693-product database.
Extracts requirements from all RFPs and finds best matches.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from db.database import AsyncSessionLocal
from db.models import RFP
from agents.product_repository import ProductRepository
from agents.technical_agent_worker import TechnicalAgentWorker
import structlog
import json

logger = structlog.get_logger()


async def extract_product_requirements(rfp_data):
    """Extract product requirements from RFP structured data."""
    structured = rfp_data.structured_data
    
    if isinstance(structured, str):
        try:
            structured = json.loads(structured)
        except:
            structured = {}
    
    products = []
    
    # Extract from specifications
    specs = structured.get('specifications', [])
    if specs:
        # Group specs by product type if possible
        product_types = {}
        
        for spec in specs:
            param = spec.get('parameter', '')
            value = spec.get('value', '')
            
            # Try to identify product type from parameter
            if any(keyword in param.lower() for keyword in ['cable', 'wire', 'conductor']):
                product_type = 'Cable'
                if 'solar' in param.lower():
                    product_type = 'Solar Cable'
                elif 'power' in param.lower():
                    product_type = 'Power Cable'
                elif 'control' in param.lower():
                    product_type = 'Control Cable'
                
                if product_type not in product_types:
                    product_types[product_type] = {}
                
                product_types[product_type][param] = value
        
        # Create product requirements
        for prod_type, specifications in product_types.items():
            products.append({
                'name': prod_type,
                'specifications': specifications
            })
    
    return products


async def match_rfp_products(rfp_id: int, rfp_title: str, product_repo: ProductRepository):
    """Match products for a single RFP."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(RFP).where(RFP.id == rfp_id))
        rfp = result.scalar_one_or_none()
        
        if not rfp:
            return None
        
        # Extract requirements
        requirements = await extract_product_requirements(rfp)
        
        if not requirements:
            logger.info(f"No products found in RFP {rfp_id}: {rfp_title}")
            return None
        
        matches_summary = []
        
        for req in requirements:
            # Search for matches
            matches = await product_repo.search_products(
                category=req['name'],
                specifications=req['specifications'],
                limit=10
            )
            
            if matches:
                top_3 = matches[:3]
                matches_summary.append({
                    'rfp_id': rfp_id,
                    'rfp_title': rfp_title,
                    'product_type': req['name'],
                    'requirements': req['specifications'],
                    'matches_found': len(matches),
                    'top_matches': [
                        {
                            'manufacturer': m['manufacturer'],
                            'model': m['model_number'],
                            'match_score': m.get('_match_score', 0)
                        }
                        for m in top_3
                    ]
                })
        
        return matches_summary


async def main():
    """Match all RFPs against product database."""
    print("\n" + "="*60)
    print("  MATCHING ALL RFPS AGAINST 693 PRODUCTS")
    print("="*60 + "\n")
    
    # Initialize repository
    product_repo = ProductRepository(use_database=True)
    
    # Get product count
    total_products = await product_repo.get_product_count()
    print(f"✓ Product Database: {total_products} products\n")
    
    # Get all RFPs
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(RFP)
            .where(RFP.structured_data.isnot(None))
            .order_by(RFP.id)
        )
        rfps = result.scalars().all()
    
    print(f"✓ Found {len(rfps)} RFPs with structured data\n")
    print("="*60)
    
    all_matches = []
    rfps_with_matches = 0
    total_products_matched = 0
    
    for i, rfp in enumerate(rfps, 1):
        print(f"\n[{i}/{len(rfps)}] Processing RFP #{rfp.id}: {rfp.title}")
        
        matches = await match_rfp_products(rfp.id, rfp.title, product_repo)
        
        if matches:
            rfps_with_matches += 1
            for match in matches:
                all_matches.append(match)
                total_products_matched += len(match['top_matches'])
                
                print(f"  ✓ {match['product_type']}: {match['matches_found']} matches found")
                for m in match['top_matches']:
                    print(f"    - {m['manufacturer']} {m['model']} ({m['match_score']:.1f}%)")
        else:
            print(f"  ⚠ No products extracted or matched")
    
    # Summary
    print("\n" + "="*60)
    print("  MATCHING SUMMARY")
    print("="*60)
    print(f"✓ Total RFPs Processed: {len(rfps)}")
    print(f"✓ RFPs with Matches: {rfps_with_matches}")
    print(f"✓ Total Product Types Found: {len(all_matches)}")
    print(f"✓ Total Products Matched: {total_products_matched}")
    print(f"✓ Database Products Used: {total_products}")
    
    # Save results
    output_file = Path(__file__).parent.parent / 'outputs' / 'rfp_matching_results.json'
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump({
            'total_rfps': len(rfps),
            'rfps_with_matches': rfps_with_matches,
            'total_products_matched': total_products_matched,
            'database_products': total_products,
            'matches': all_matches
        }, f, indent=2)
    
    print(f"\n✓ Results saved to: {output_file}")
    print("\n" + "="*60 + "\n")


if __name__ == '__main__':
    asyncio.run(main())
