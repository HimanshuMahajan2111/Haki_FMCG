"""
Load OEM Product Data from CSV files into SQLite Database.

This script:
1. Creates database tables
2. Loads products from CSV using ProductDataLoader
3. Inserts products into database with duplicate handling
"""

import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import logging

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select
from db.database import engine, AsyncSessionLocal, Base
from db.product_models import OEMProduct, ProductInventory, PriceHistory
from agents.data_loader import ProductDataLoader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def create_tables():
    """Create all database tables."""
    async with engine.begin() as conn:
        # Drop existing tables (optional - for clean slate)
        # await conn.run_sync(Base.metadata.drop_all)
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database tables created successfully")


async def clear_existing_products():
    """Clear all existing products from database."""
    async with AsyncSessionLocal() as db:
        # Delete all products
        from sqlalchemy import delete
        await db.execute(delete(OEMProduct))
        await db.commit()
        logger.info("Cleared all existing products from database")


async def load_products_to_database():
    """Main function to load products into database."""
    
    logger.info("="*80)
    logger.info("DATABASE LOADING PROCESS STARTED")
    logger.info("="*80)
    
    # Step 1: Create tables
    logger.info("\nStep 1: Creating database schema...")
    await create_tables()
    
    # Step 2: Clear existing data
    logger.info("\nStep 2: Clearing existing database...")
    await clear_existing_products()
    
    # Step 3: Load products from CSV
    logger.info("\nStep 3: Loading products from CSV files...")
    data_loader = ProductDataLoader()
    products = data_loader.load_all_products()
    
    logger.info(f"\nLoaded {len(products)} products from CSV files")
    logger.info("Breakdown by manufacturer:")
    for manufacturer in ['Havells', 'Polycab', 'KEI', 'Finolex', 'RR Kabel']:
        count = sum(1 for p in products if p.get('manufacturer') == manufacturer)
        logger.info(f"  - {manufacturer}: {count} products")
    
    # Step 4: Insert products into database
    logger.info("\nStep 4: Inserting products into database...")
    
    inserted_count = 0
    error_count = 0
    batch_size = 50  # Smaller batches for better error handling
    
    async with AsyncSessionLocal() as db:
        for idx, product_data in enumerate(products, 1):
            try:
                # Create product instance
                product = OEMProduct(
                    product_id=product_data.get('product_id'),
                    manufacturer=product_data.get('manufacturer'),
                    model_number=product_data.get('model_number'),
                    product_name=product_data.get('product_name', ''),
                    category=product_data.get('category', 'General'),
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
                
                # Extract specific technical specifications
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
                
                # Commit in batches
                if idx % batch_size == 0:
                    try:
                        await db.commit()
                        logger.info(f"  Committed batch: {inserted_count}/{idx} products inserted")
                    except Exception as batch_error:
                        logger.error(f"  Batch commit failed: {batch_error}")
                        await db.rollback()
                        error_count += batch_size
                        inserted_count -= batch_size
                
            except Exception as e:
                error_count += 1
                product_id = product_data.get('product_id', 'UNKNOWN')
                manufacturer = product_data.get('manufacturer', 'UNKNOWN')
                logger.error(f"  Failed to process product {idx} - {manufacturer} - {product_id}: {str(e)[:200]}")
                import traceback
                logger.error(f"  Traceback: {traceback.format_exc()[:500]}")
                continue
        
        # Final commit for remaining products
        try:
            await db.commit()
            logger.info(f"  Final commit: All products processed")
        except Exception as final_error:
            logger.error(f"  Final commit failed: {final_error}")
            await db.rollback()
    
    # Step 5: Verify insertion
    logger.info("\nStep 5: Verifying database insertion...")
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(OEMProduct))
        db_products = result.scalars().all()
        
        logger.info("\n" + "="*80)
        logger.info("DATABASE LOADING COMPLETE")
        logger.info("="*80)
        logger.info(f"Total Products in Database: {len(db_products)}")
        logger.info(f"Successfully Inserted: {inserted_count}")
        logger.info(f"Errors: {error_count}")
        
        # Count by manufacturer
        logger.info("\nProducts by manufacturer in database:")
        for manufacturer in ['Havells', 'Polycab', 'KEI', 'Finolex', 'RR Kabel']:
            count = sum(1 for p in db_products if p.manufacturer == manufacturer)
            logger.info(f"  - {manufacturer}: {count}")
        
        logger.info("="*80)


if __name__ == "__main__":
    asyncio.run(load_products_to_database())
