"""
Load additional 100+ products from latest wire/cable data files.
Scans wires_cables_data folder and adds new products to database.
"""
import asyncio
import sys
import json
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import AsyncSessionLocal
from db.product_models import OEMProduct
from sqlalchemy import select
import structlog

logger = structlog.get_logger()


def load_json_files(data_dir: Path) -> List[Dict[str, Any]]:
    """Load all JSON product files from directory."""
    products = []
    
    # Scan all manufacturer folders
    for manufacturer_dir in data_dir.iterdir():
        if not manufacturer_dir.is_dir():
            continue
        
        manufacturer_name = manufacturer_dir.name.title()
        
        # Look for JSON files
        for json_file in manufacturer_dir.glob('*.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Handle different JSON structures
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                item['_source_file'] = json_file.name
                                item['_manufacturer'] = manufacturer_name
                                products.append(item)
                    elif isinstance(data, dict):
                        # Check if it's a products list
                        if 'products' in data:
                            for item in data['products']:
                                item['_source_file'] = json_file.name
                                item['_manufacturer'] = manufacturer_name
                                products.append(item)
                        else:
                            data['_source_file'] = json_file.name
                            data['_manufacturer'] = manufacturer_name
                            products.append(data)
                            
                logger.info(f"Loaded {json_file.name}", manufacturer=manufacturer_name)
            except Exception as e:
                logger.error(f"Error loading {json_file}: {e}")
    
    return products


def normalize_product_data(product: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize product data to standard format."""
    manufacturer = product.get('_manufacturer', product.get('manufacturer', 'Unknown'))
    
    # Extract product ID
    product_id = (
        product.get('product_id') or
        product.get('sku') or
        product.get('part_number') or
        product.get('model_number') or
        f"AUTO-{hash(str(product))}"[:20]
    )
    
    # Extract product name
    product_name = (
        product.get('product_name') or
        product.get('name') or
        product.get('description') or
        'Unknown Product'
    )
    
    # Extract category
    category = (
        product.get('category') or
        product.get('type') or
        product.get('product_type') or
        'Cable'
    )
    
    # Extract specifications
    specs = product.get('specifications', {})
    if not specs:
        # Try to extract from root level
        spec_keys = ['voltage', 'conductor_size', 'insulation', 'conductor_material',
                    'cores', 'armour', 'sheath', 'voltage_rating', 'current_rating']
        specs = {k: v for k, v in product.items() if k in spec_keys}
    
    # Extract certifications
    certs = product.get('certifications', [])
    if isinstance(certs, str):
        certs = [c.strip() for c in certs.split(',')]
    
    # Extract standards
    standards = product.get('standards', [])
    if isinstance(standards, str):
        standards = [s.strip() for s in standards.split(',')]
    
    # Extract pricing
    unit_price = product.get('unit_price', product.get('price', 0))
    try:
        unit_price = float(unit_price)
    except:
        unit_price = 0.0
    
    return {
        'product_id': str(product_id)[:50],
        'manufacturer': manufacturer,
        'model_number': str(product.get('model_number', product_id))[:100],
        'product_name': str(product_name)[:200],
        'category': str(category)[:100],
        'specifications': specs,
        'certifications': certs,
        'standards': standards,
        'unit_price': unit_price,
        'stock_quantity': int(product.get('stock', product.get('stock_quantity', 1000))),
        'delivery_days': int(product.get('delivery_days', 7)),
        'is_active': True
    }


async def add_products_to_database(products: List[Dict[str, Any]]) -> int:
    """Add products to database, skipping duplicates."""
    added_count = 0
    skipped_count = 0
    
    async with AsyncSessionLocal() as db:
        for product_data in products:
            try:
                # Check if product already exists
                result = await db.execute(
                    select(OEMProduct).where(
                        OEMProduct.product_id == product_data['product_id']
                    )
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    skipped_count += 1
                    continue
                
                # Create new product
                product = OEMProduct(**product_data)
                db.add(product)
                added_count += 1
                
                # Commit in batches of 50
                if added_count % 50 == 0:
                    await db.commit()
                    logger.info(f"Committed batch: {added_count} products added")
            
            except Exception as e:
                logger.error(f"Error adding product {product_data.get('product_id')}: {e}")
        
        # Final commit
        await db.commit()
    
    return added_count, skipped_count


async def main():
    """Load additional 100+ products from data files."""
    print("\n" + "="*60)
    print("  LOADING ADDITIONAL PRODUCTS FROM DATA FILES")
    print("="*60 + "\n")
    
    # Find data directory
    data_dir = Path(__file__).parent.parent.parent / 'wires_cables_data'
    
    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        return
    
    print(f"✓ Scanning directory: {data_dir}\n")
    
    # Load products from JSON files
    raw_products = load_json_files(data_dir)
    print(f"✓ Found {len(raw_products)} products in JSON files\n")
    
    # Normalize data
    normalized_products = []
    for product in raw_products:
        try:
            normalized = normalize_product_data(product)
            normalized_products.append(normalized)
        except Exception as e:
            logger.error(f"Error normalizing product: {e}")
    
    print(f"✓ Normalized {len(normalized_products)} products\n")
    
    # Get current product count
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(OEMProduct))
        current_count = len(result.scalars().all())
    
    print(f"Current database: {current_count} products\n")
    print("="*60)
    print("Adding new products...\n")
    
    # Add to database
    added, skipped = await add_products_to_database(normalized_products)
    
    # Final count
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(OEMProduct))
        final_count = len(result.scalars().all())
    
    # Summary
    print("\n" + "="*60)
    print("  LOADING SUMMARY")
    print("="*60)
    print(f"✓ Products Found in Files: {len(raw_products)}")
    print(f"✓ Products Normalized: {len(normalized_products)}")
    print(f"✓ Products Added: {added}")
    print(f"✓ Products Skipped (duplicates): {skipped}")
    print(f"✓ Database Before: {current_count}")
    print(f"✓ Database After: {final_count}")
    print(f"✓ Net Increase: +{final_count - current_count}")
    print("\n" + "="*60 + "\n")
    
    if added > 0:
        print("✅ Successfully added new products!")
        print("⚠️  Restart backend to use updated database\n")


if __name__ == '__main__':
    asyncio.run(main())
