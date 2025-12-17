"""
Load Products to Database - Import CSV data into SQLite

This script loads all OEM product data from CSV files into the database.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from sqlalchemy import select
from db.database import AsyncSessionLocal, engine, Base
from db.product_models import OEMProduct, ProductInventory
from agents.data_loader import ProductDataLoader
import structlog
from datetime import datetime

logger = structlog.get_logger()


async def create_tables():
    """Create database tables."""
    logger.info("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


async def clear_existing_products():
    """Clear existing products from database."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(OEMProduct))
        existing = result.scalars().all()
        
        if existing:
            logger.info(f"Clearing {len(existing)} existing products")
            for product in existing:
                await db.delete(product)
            await db.commit()
            logger.info("Existing products cleared")
        else:
            logger.info("No existing products to clear")


async def load_products_from_csv():
    """Load products from CSV files into database."""
    
    logger.info("="*80)
    logger.info("LOADING OEM PRODUCTS FROM CSV FILES TO DATABASE")
    logger.info("="*80)
    
    # Step 1: Create tables
    await create_tables()
    
    # Step 2: Load CSV data
    logger.info("\nStep 1: Loading CSV data...")
    data_loader = ProductDataLoader(base_path="..")
    products = data_loader.load_all_products()
    logger.info(f"Loaded {len(products)} products from CSV files")
    
    # Step 3: Clear existing data (optional)
    logger.info("\nStep 2: Clearing existing database...")
    await clear_existing_products()
    
    # Step 4: Insert products into database
    logger.info("\nStep 3: Inserting products into database...")
    
    async with AsyncSessionLocal() as db:
        inserted_count = 0
        error_count = 0
        
        for idx, product_data in enumerate(products, 1):
            try:
                # Check for duplicate product_id and skip if exists
                product_id = product_data.get('product_id')
                result = await db.execute(
                    select(OEMProduct).where(OEMProduct.product_id == product_id)
                )
                if result.scalar_one_or_none():
                    # Skip duplicate
                    continue
                
                # Create OEMProduct instance
                product = OEMProduct(
                    product_id=product_id,
                    manufacturer=product_data.get('manufacturer'),
                    model_number=product_data.get('model_number'),
                    product_name=product_data.get('product_name'),
                    category=product_data.get('category'),
                    specifications=product_data.get('specifications', {}),
                    unit_price=product_data.get('unit_price', 0.0),
                    stock_quantity=product_data.get('stock', 1000),
                    available_stock=product_data.get('stock', 1000),
                    delivery_days=product_data.get('delivery_days', 7),
                    certifications=product_data.get('certifications', []),
                    standards=product_data.get('standards', []),
                    currency='INR',
                    is_active=True,
                    data_source='CSV Import',
                    extracted_date=datetime.now()
                )
                
                # Extract specific fields from specifications
                specs = product_data.get('specifications', {})
                product.voltage_rating = specs.get('voltage_rating')
                product.conductor_material = specs.get('conductor_material')
                product.conductor_size = specs.get('conductor_size')
                product.insulation_type = specs.get('insulation')
                product.max_temperature = specs.get('temperature_rating')
                product.current_rating = specs.get('current_rating')
                
                if 'cores' in specs:
                    try:
                        product.no_of_cores = int(specs['cores'])
                    except:
                        pass
                
                db.add(product)
                inserted_count += 1
                
                # Commit in batches of 100
                if idx % 100 == 0:
                    await db.commit()
                    logger.info(f"Inserted {inserted_count} products...")
                
            except Exception as e:
                error_count += 1
                logger.error(f"Failed to insert product {product_data.get('product_id')}: {e}")
                continue
        
        # Final commit
        await db.commit()
        
        logger.info("\n" + "="*80)
        logger.info(f"DATABASE LOADING COMPLETE")
        logger.info(f"Total Products Inserted: {inserted_count}")
        logger.info(f"Errors: {error_count}")
        logger.info("="*80)
    
    # Step 5: Verify insertion
    logger.info("\nStep 4: Verifying database...")
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(OEMProduct))
        all_products = result.scalars().all()
        logger.info(f"Database now contains {len(all_products)} products")
        
        # Show sample by manufacturer
        manufacturers = {}
        for product in all_products:
            manufacturers[product.manufacturer] = manufacturers.get(product.manufacturer, 0) + 1
        
        logger.info("\nProducts by Manufacturer:")
        for manufacturer, count in sorted(manufacturers.items()):
            logger.info(f"  {manufacturer}: {count} products")
        
        # Show sample by category
        categories = {}
        for product in all_products:
            categories[product.category] = categories.get(product.category, 0) + 1
        
        logger.info("\nProducts by Category:")
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]:
            logger.info(f"  {category}: {count} products")


if __name__ == "__main__":
    asyncio.run(load_products_from_csv())
