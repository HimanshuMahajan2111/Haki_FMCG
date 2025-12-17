"""Database and vector store setup script.

This script initializes the enhanced database schema and ChromaDB configuration.
Run this to set up or migrate to the new enhanced schema.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import structlog
from sqlalchemy import text

from config.settings import settings
from db.database import engine, AsyncSessionLocal
from db.migrations import (
    init_database,
    migrate_to_enhanced,
    create_indexes,
    validate_schema,
    backup_database
)
from data.vector_store_enhanced import EnhancedVectorStore
from services.data_service import DataService

logger = structlog.get_logger()


async def setup_database(use_enhanced: bool = True, backup_first: bool = True):
    """Set up database with enhanced schema.
    
    Args:
        use_enhanced: If True, use enhanced schema with relationships
        backup_first: If True, backup existing database before migration
    """
    logger.info("=" * 80)
    logger.info("DATABASE SETUP")
    logger.info("=" * 80)
    
    # Step 1: Backup existing database
    if backup_first:
        logger.info("Step 1: Creating backup")
        backup_path = Path("./backups") / f"db_backup_{asyncio.get_event_loop().time()}.db"
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            await backup_database(engine, backup_path)
            logger.info("Backup created", path=str(backup_path))
        except Exception as e:
            logger.warning("Backup failed (may be first run)", error=str(e))
    
    # Step 2: Initialize schema
    logger.info("Step 2: Initializing database schema", enhanced=use_enhanced)
    await init_database(engine, use_enhanced=use_enhanced)
    logger.info("Database schema initialized")
    
    # Step 3: Create performance indexes
    if use_enhanced:
        logger.info("Step 3: Creating performance indexes")
        await create_indexes(engine)
        logger.info("Indexes created")
    
    # Step 4: Validate schema
    logger.info("Step 4: Validating schema")
    is_valid = await validate_schema(engine)
    
    if is_valid:
        logger.info("✓ Database setup completed successfully")
    else:
        logger.error("✗ Database validation failed")
        return False
    
    return True


async def setup_vector_store(use_openai: bool = False, populate: bool = True):
    """Set up enhanced ChromaDB vector store.
    
    Args:
        use_openai: If True, use OpenAI embeddings
        populate: If True, populate with existing products
    """
    logger.info("=" * 80)
    logger.info("VECTOR STORE SETUP")
    logger.info("=" * 80)
    
    # Initialize enhanced vector store
    logger.info("Initializing ChromaDB", use_openai=use_openai)
    vector_store = EnhancedVectorStore()
    await vector_store.initialize(use_openai=use_openai)
    
    # Get stats
    stats = await vector_store.get_collection_stats()
    logger.info("Vector store initialized", stats=stats)
    
    # Populate if requested
    if populate:
        logger.info("Loading products from data service")
        data_service = DataService()
        await data_service.initialize()
        
        products = await data_service.get_products(limit=10000)
        logger.info("Products loaded", count=len(products))
        
        # Add to vector store
        logger.info("Adding products to vector store")
        added = await vector_store.add_products(
            products,
            batch_size=100,
            update_existing=True
        )
        
        logger.info("✓ Vector store populated", products_added=added)
        
        # Final stats
        final_stats = await vector_store.get_collection_stats()
        logger.info("Final statistics", stats=final_stats)
    
    return vector_store


async def migrate_existing_data():
    """Migrate data from basic to enhanced schema."""
    logger.info("=" * 80)
    logger.info("DATA MIGRATION")
    logger.info("=" * 80)
    
    logger.info("Migrating RFP matches and agent logs to enhanced schema")
    
    try:
        await migrate_to_enhanced(engine)
        logger.info("✓ Data migration completed")
        return True
    except Exception as e:
        logger.error("✗ Migration failed", error=str(e), exc_info=True)
        return False


async def populate_products_to_db():
    """Populate database with products from CSV files."""
    logger.info("=" * 80)
    logger.info("POPULATING DATABASE")
    logger.info("=" * 80)
    
    # Load products from data service
    data_service = DataService()
    await data_service.initialize()
    
    products = await data_service.get_products(limit=10000)
    logger.info("Loaded products", count=len(products))
    
    # Import models
    from db.models_enhanced import Product
    
    # Add to database
    async with AsyncSessionLocal() as session:
        added_count = 0
        batch_size = 100
        
        for i in range(0, len(products), batch_size):
            batch = products[i:i+batch_size]
            
            for product_data in batch:
                try:
                    # Normalize empty strings to None for unique constraint
                    product_code = product_data.get('product_code', '')
                    product_code = product_code if product_code and product_code.strip() else None
                    
                    # Create product instance
                    product = Product(
                        brand=product_data.get('brand', ''),
                        category=product_data.get('category', ''),
                        sub_category=product_data.get('sub_category'),
                        product_code=product_code,
                        product_name=product_data.get('product_name', ''),
                        model_name=product_data.get('model_name'),
                        specifications=product_data.get('specifications', {}),
                        mrp=product_data.get('mrp'),
                        selling_price=product_data.get('selling_price'),
                        dealer_price=product_data.get('dealer_price'),
                        certifications=product_data.get('certifications'),
                        bis_registration=product_data.get('bis_registration'),
                        standard=product_data.get('standard'),
                        hsn_code=product_data.get('hsn_code'),
                        warranty_years=product_data.get('warranty_years'),
                        country_of_origin=product_data.get('country_of_origin'),
                        embedding_id=product_data.get('product_code'),
                        is_active=True
                    )
                    
                    session.add(product)
                    added_count += 1
                    
                except Exception as e:
                    logger.warning("Product add failed", 
                                 product=product_data.get('product_code'), 
                                 error=str(e))
            
            # Commit batch
            try:
                await session.commit()
                logger.info("Batch committed", batch=i//batch_size + 1, count=len(batch))
            except Exception as e:
                logger.error("Batch commit failed", error=str(e))
                await session.rollback()
    
    logger.info("✓ Products populated", total=added_count)
    return added_count


async def verify_setup(skip_vector_store: bool = False):
    """Verify complete setup.
    
    Args:
        skip_vector_store: If True, skip vector store verification (faster)
    """
    import time
    logger.info("=" * 80)
    logger.info("SETUP VERIFICATION")
    logger.info("=" * 80)
    
    # Check database
    start_time = time.time()
    logger.info("Checking database...")
    is_valid = await validate_schema(engine)
    logger.info(f"Database check completed in {time.time() - start_time:.2f}s")
    
    if not is_valid:
        logger.error("✗ Database schema invalid")
        return False
    
    # Check product count
    start_time = time.time()
    async with AsyncSessionLocal() as session:
        from db.models_enhanced import Product, RFP, ProductMatch
        from sqlalchemy import select, func
        
        product_count = await session.execute(select(func.count(Product.id)))
        product_count = product_count.scalar()
        
        rfp_count = await session.execute(select(func.count(RFP.id)))
        rfp_count = rfp_count.scalar()
        
        match_count = await session.execute(select(func.count(ProductMatch.id)))
        match_count = match_count.scalar()
        
        logger.info("Database counts",
                   products=product_count,
                   rfps=rfp_count,
                   matches=match_count)
    logger.info(f"Database count check completed in {time.time() - start_time:.2f}s")
    
    # Check vector store (optional, can be slow)
    if not skip_vector_store:
        try:
            start_time = time.time()
            logger.info("Checking vector store (this may take 60-90s on first run)...")
            vector_store = EnhancedVectorStore()
            await vector_store.initialize()
            logger.info(f"Vector store initialization completed in {time.time() - start_time:.2f}s")
            
            start_time = time.time()
            stats = await vector_store.get_collection_stats()
            logger.info("Vector store stats", stats=stats)
            
            # Test search
            logger.info("Testing vector search...")
            results = await vector_store.search_products("LED lights", limit=3)
            logger.info(f"Vector search completed in {time.time() - start_time:.2f}s")
            logger.info("Search test", results_count=len(results))
            
            if len(results) > 0:
                logger.info("Sample result", result=results[0])
        except Exception as e:
            logger.warning(f"Vector store check skipped: {e}")
            logger.info("To fix: Install chromadb and sentence-transformers")
    else:
        logger.info("⏭️  Vector store check skipped (use --verify-full to enable)")
    
    logger.info("=" * 80)
    logger.info("✓ SETUP VERIFICATION COMPLETE")
    logger.info("=" * 80)
    
    return True


async def main():
    """Main setup flow."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup database and vector store")
    parser.add_argument('--skip-db', action='store_true', help="Skip database setup")
    parser.add_argument('--skip-vector', action='store_true', help="Skip vector store setup")
    parser.add_argument('--skip-populate', action='store_true', help="Skip data population")
    parser.add_argument('--migrate', action='store_true', help="Migrate existing data")
    parser.add_argument('--use-openai', action='store_true', help="Use OpenAI embeddings")
    parser.add_argument('--no-backup', action='store_true', help="Skip backup")
    parser.add_argument('--verify-only', action='store_true', help="Quick verification (skips vector store, ~5s)")
    parser.add_argument('--verify-full', action='store_true', help="Full verification with vector store (~60-90s)")
    
    args = parser.parse_args()
    
    try:
        # Verify only modes
        if args.verify_only:
            logger.info("Running quick verification (skips vector store)...")
            success = await verify_setup(skip_vector_store=True)
            return 0 if success else 1
        
        if args.verify_full:
            logger.info("Running full verification (includes vector store)...")
            success = await verify_setup(skip_vector_store=False)
            return 0 if success else 1
        
        # Database setup
        if not args.skip_db:
            success = await setup_database(
                use_enhanced=True,
                backup_first=not args.no_backup
            )
            if not success:
                logger.error("Database setup failed")
                return 1
            
            # Populate products
            if not args.skip_populate:
                await populate_products_to_db()
        
        # Migrate existing data
        if args.migrate:
            success = await migrate_existing_data()
            if not success:
                logger.error("Migration failed")
                return 1
        
        # Vector store setup
        if not args.skip_vector:
            await setup_vector_store(
                use_openai=args.use_openai,
                populate=not args.skip_populate
            )
        
        # Final verification
        logger.info("\nRunning final verification...")
        success = await verify_setup()
        
        if success:
            logger.info("\n✓ ALL SETUP COMPLETE!")
            logger.info("\nNext steps:")
            logger.info("1. Start the API server: python -m uvicorn main:app --reload")
            logger.info("2. Check API docs: http://localhost:8000/docs")
            return 0
        else:
            logger.error("\n✗ Setup verification failed")
            return 1
            
    except Exception as e:
        logger.error("Setup failed", error=str(e), exc_info=True)
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
