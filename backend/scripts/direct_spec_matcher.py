"""
DIRECT SPECIFICATION MATCHER - NO BULLSHIT
Just compares specs with products and shows top 3 with percentages
"""
import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from db.database import AsyncSessionLocal
from db.models import RFP, Product


def normalize_key(key: str) -> str:
    """Normalize spec key for comparison."""
    return key.lower().replace(' ', '_').replace('-', '_')


def compare_values(rfp_val: str, product_val: str) -> bool:
    """Check if values match (with tolerance)."""
    if not rfp_val or not product_val:
        return False
    
    rfp_str = str(rfp_val).lower().strip()
    prod_str = str(product_val).lower().strip()
    
    # Exact match
    if rfp_str == prod_str:
        return True
    
    # Contains match
    if rfp_str in prod_str or prod_str in rfp_str:
        return True
    
    # Number extraction for voltage, size, etc.
    try:
        rfp_num = float(''.join(filter(str.isdigit, rfp_str.replace('.', ''))))
        prod_num = float(''.join(filter(str.isdigit, prod_str.replace('.', ''))))
        
        # 10% tolerance
        if abs(rfp_num - prod_num) / max(rfp_num, prod_num) <= 0.1:
            return True
    except:
        pass
    
    return False


def calculate_match_percentage(rfp_specs: list, product_specs: dict) -> tuple:
    """Calculate match percentage between RFP specs and product."""
    if not rfp_specs:
        return 0, []
    
    matched = []
    total = len(rfp_specs)
    
    # Normalize product specs
    norm_product = {normalize_key(k): v for k, v in product_specs.items()}
    
    for spec in rfp_specs:
        param = spec.get('parameter', '')
        value = spec.get('value', '')
        
        if not param:
            continue
        
        norm_param = normalize_key(param)
        
        # Check if product has this spec
        if norm_param in norm_product:
            if compare_values(value, norm_product[norm_param]):
                matched.append({
                    'parameter': param,
                    'rfp_value': value,
                    'product_value': norm_product[norm_param],
                    'match': True
                })
    
    match_pct = (len(matched) / total * 100) if total > 0 else 0
    return match_pct, matched


async def match_rfp_direct(rfp_id: int):
    """Direct matching for one RFP."""
    
    async with AsyncSessionLocal() as db:
        # Get RFP
        result = await db.execute(select(RFP).where(RFP.id == rfp_id))
        rfp = result.scalar_one_or_none()
        
        if not rfp:
            print(f"❌ RFP #{rfp_id} not found")
            return
        
        print(f"\n{'='*80}")
        print(f"RFP #{rfp.id}: {rfp.title}")
        print(f"{'='*80}")
        
        # Get specs
        structured_data = rfp.structured_data
        if isinstance(structured_data, str):
            structured_data = json.loads(structured_data)
        
        specifications = structured_data.get('specifications', [])
        print(f"\n📋 RFP has {len(specifications)} specifications")
        
        if not specifications:
            print("❌ No specifications found")
            return
        
        # Get ALL products
        result = await db.execute(select(Product))
        all_products = result.scalars().all()
        
        print(f"🔍 Comparing against {len(all_products)} products...")
        
        # Calculate match for each product
        matches = []
        for product in all_products:
            product_specs = product.specifications or {}
            if isinstance(product_specs, str):
                product_specs = json.loads(product_specs)
            
            match_pct, matched_specs = calculate_match_percentage(specifications, product_specs)
            
            if match_pct > 0:  # Only include products with some match
                matches.append({
                    'product_id': product.product_id,
                    'manufacturer': product.manufacturer,
                    'model_number': product.model_number,
                    'category': product.category,
                    'match_percentage': round(match_pct, 2),
                    'matched_specs': matched_specs,
                    'total_rfp_specs': len(specifications),
                    'matched_count': len(matched_specs),
                    'price': product.unit_price
                })
        
        # Sort by match percentage
        matches.sort(key=lambda x: x['match_percentage'], reverse=True)
        
        # Get top 3
        top_3 = matches[:3]
        
        print(f"\n✅ Found {len(matches)} products with matches")
        print(f"🏆 TOP 3 PRODUCTS:\n")
        
        for i, match in enumerate(top_3, 1):
            print(f"{i}. {match['manufacturer']} - {match['model_number']}")
            print(f"   Match: {match['match_percentage']}%")
            print(f"   Matched {match['matched_count']}/{match['total_rfp_specs']} specs")
            print(f"   Price: ₹{match['price']}")
            print()
        
        # Save to document
        output_dir = Path(__file__).parent.parent / 'outputs' / 'direct_matching'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"RFP_{rfp_id}_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        output_data = {
            'rfp_id': rfp.id,
            'rfp_title': rfp.title,
            'processed_at': datetime.now().isoformat(),
            'total_specifications': len(specifications),
            'total_products_checked': len(all_products),
            'products_with_matches': len(matches),
            'specifications': specifications,
            'top_3_matches': top_3,
            'all_matches': matches
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"💾 Output saved: {output_file.name}")
        
        # Update RFP in database
        rfp.matched_products = json.dumps(top_3)
        rfp.status = 'REVIEWED'
        await db.commit()
        
        print(f"✅ RFP #{rfp_id} updated in database")
        
        return top_3


async def match_all_rfps():
    """Match all RFPs."""
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(RFP).where(RFP.structured_data.isnot(None))
        )
        rfps = result.scalars().all()
    
    print(f"\n{'='*80}")
    print(f"PROCESSING {len(rfps)} RFPs")
    print(f"{'='*80}")
    
    for rfp in rfps:
        await match_rfp_direct(rfp.id)
        await asyncio.sleep(0.5)
    
    print(f"\n{'='*80}")
    print(f"✅ ALL {len(rfps)} RFPs PROCESSED")
    print(f"{'='*80}")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        rfp_id = int(sys.argv[1])
        asyncio.run(match_rfp_direct(rfp_id))
    else:
        asyncio.run(match_all_rfps())
