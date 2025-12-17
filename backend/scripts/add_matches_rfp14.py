"""
Add 3 matched products with 50+ match score to RFP14
"""
import asyncio
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from db.database import AsyncSessionLocal
from db.models import RFP
from services.data_service import DataService


async def add_matches_to_rfp14():
    """Add 3 matched products to RFP14 (id=77)"""
    
    # Initialize data service to load products
    print("\n🔄 Loading products from CSV files...")
    data_service = DataService()
    await data_service.initialize()
    
    # Get products from memory
    all_products = await data_service.get_products()
    print(f"✅ Loaded {len(all_products)} products")
    
    if len(all_products) < 3:
        print("❌ Not enough products!")
        return
    
    async with AsyncSessionLocal() as db:
        # Get RFP with id=77
        result = await db.execute(select(RFP).where(RFP.id == 77))
        rfp = result.scalar_one_or_none()
        
        if not rfp:
            print("❌ RFP #77 not found!")
            return
        
        print(f"\n{'='*70}")
        print(f"Adding matched products to RFP #{rfp.id}: {rfp.title}")
        print(f"{'='*70}\n")
        
        # Create 3 matched products with realistic high match scores
        matched_products = []
        
        # Select products with good variety
        selected_indices = [0, 5, 10] if len(all_products) > 10 else [0, 1, 2]
        match_scores = [85.5, 72.3, 58.7]  # 50+ match scores
        
        for idx, product_idx in enumerate(selected_indices):
            if product_idx >= len(all_products):
                product_idx = idx
            
            product = all_products[product_idx]
            match_score = match_scores[idx]
            
            # Extract product details
            product_id = product.get('product_id', f'PROD-{idx+1}')
            product_name = product.get('name', 'Unknown Product')
            brand = product.get('brand', 'Unknown Brand')
            model = product.get('model', '')
            category = product.get('category', 'General')
            price = float(product.get('price') or 0)
            mrp = float(product.get('mrp') or (price * 1.2 if price > 0 else 1000))
            specs = product.get('specifications', {})
            image_url = product.get('image_url', '')
            
            matched_product = {
                "match_score": match_score / 100,  # Convert to 0-1 range
                "product": {
                    "id": product_id,
                    "product_code": product_id,
                    "name": product_name,
                    "brand": brand,
                    "model": model if model else product_name.split()[0],
                    "category": category,
                    "selling_price": price,
                    "mrp": mrp,
                    "image_url": image_url,
                    "specifications": specs
                },
                "matched_specs": [],
                "missing_specs": [],
                "spec_compliance": match_score
            }
            
            matched_products.append(matched_product)
            
            print(f"✓ Product {idx+1}:")
            print(f"  - Name: {product_name}")
            print(f"  - Brand: {brand}")
            print(f"  - Match Score: {match_score}%")
            print(f"  - Price: ₹{price}")
            print()
        
        # Update RFP with matched products
        rfp.matched_products = matched_products
        
        await db.commit()
        
        print(f"{'='*70}")
        print(f"✅ Successfully added {len(matched_products)} matched products to RFP #{rfp.id}")
        print(f"   Products are now available in the UI!")
        print(f"{'='*70}\n")
        print("🎉 Done! Refresh your browser to see the matched products.")


if __name__ == "__main__":
    asyncio.run(add_matches_to_rfp14())
