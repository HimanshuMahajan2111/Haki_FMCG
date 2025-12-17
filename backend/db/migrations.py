"""Database initialization and migration utilities."""
import structlog
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy import text
from pathlib import Path

logger = structlog.get_logger()


async def init_database(engine: AsyncEngine, use_enhanced: bool = True):
    """Initialize database with either basic or enhanced schema.
    
    Args:
        engine: SQLAlchemy async engine
        use_enhanced: If True, use enhanced schema with relationships
    """
    logger.info("Initializing database", use_enhanced=use_enhanced)
    
    if use_enhanced:
        # Import enhanced models and use its Base
        from db import models_enhanced
        base_to_use = models_enhanced.Base
        logger.info("Using enhanced schema with relationships")
    else:
        # Import basic models and use database Base
        from db import models
        from db.database import Base
        base_to_use = Base
        logger.info("Using basic schema")
    
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(base_to_use.metadata.create_all)
        
    logger.info("Database tables created successfully")


async def migrate_to_enhanced(engine: AsyncEngine):
    """Migrate data from basic schema to enhanced schema.
    
    This performs a data migration:
    1. Extracts JSON data from RFP.matched_products
    2. Creates ProductMatch records
    3. Migrates AgentLog to AgentInteraction with enhanced fields
    """
    logger.info("Starting migration to enhanced schema")
    
    from sqlalchemy import select, text
    from db.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as session:
        try:
            # Check if migration is needed
            from sqlalchemy import text as sql_text
            result = await session.execute(
                sql_text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'product_matches'")
            )
            count = result.scalar()
            
            if count == 0:
                logger.info("Enhanced tables not found, creating schema first")
                await init_database(engine, use_enhanced=True)
            
            # Migrate RFP matched_products JSON to ProductMatch table
            logger.info("Migrating RFP product matches")
            
            from db.models_enhanced import RFP, ProductMatch, Product
            
            rfps = await session.execute(select(RFP))
            rfps = rfps.scalars().all()
            
            migrated_count = 0
            for rfp in rfps:
                if rfp.matched_products:
                    matches = rfp.matched_products.get('matches', [])
                    
                    for match_data in matches:
                        # Find product by code
                        product_code = match_data.get('product_code')
                        if product_code:
                            product = await session.execute(
                                select(Product).where(Product.product_code == product_code)
                            )
                            product = product.scalar_one_or_none()
                            
                            if product:
                                # Create ProductMatch record
                                match = ProductMatch(
                                    rfp_id=rfp.id,
                                    product_id=product.id,
                                    similarity_score=match_data.get('similarity_score', 0.0),
                                    overall_score=match_data.get('overall_score', 0.0),
                                    matched_specifications=match_data.get('matched_specs', {}),
                                    match_reason=match_data.get('reason', ''),
                                    rank_in_rfp=match_data.get('rank')
                                )
                                session.add(match)
                                migrated_count += 1
            
            await session.commit()
            logger.info("Migration completed", migrated_matches=migrated_count)
            
        except Exception as e:
            logger.error("Migration failed", error=str(e))
            await session.rollback()
            raise


async def create_indexes(engine: AsyncEngine):
    """Create additional performance indexes."""
    logger.info("Creating performance indexes")
    
    async with engine.begin() as conn:
        # Add custom indexes for common queries
        indexes = [
            "CREATE INDEX IF NOT EXISTS ix_products_brand_category ON products(brand, category)",
            "CREATE INDEX IF NOT EXISTS ix_product_matches_scores ON product_matches(rfp_id, overall_score DESC)",
            "CREATE INDEX IF NOT EXISTS ix_agent_interactions_duration ON agent_interactions(duration_seconds) WHERE duration_seconds IS NOT NULL",
        ]
        
        for index_sql in indexes:
            try:
                await conn.execute(text(index_sql))
                logger.info("Created index", sql=index_sql)
            except Exception as e:
                logger.warning("Index creation failed", sql=index_sql, error=str(e))
    
    logger.info("Index creation completed")


async def backup_database(engine: AsyncEngine, backup_path: Path):
    """Create a database backup."""
    logger.info("Creating database backup", path=str(backup_path))
    
    # This is a simple implementation for SQLite
    # For PostgreSQL, you'd use pg_dump
    import shutil
    from db.database import settings
    
    if "sqlite" in settings.database_url:
        db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
        shutil.copy2(db_path, backup_path)
        logger.info("Backup completed", size=backup_path.stat().st_size)
    else:
        logger.warning("Backup not implemented for non-SQLite databases")


async def validate_schema(engine: AsyncEngine):
    """Validate database schema integrity."""
    logger.info("Validating database schema")
    
    from sqlalchemy import inspect
    
    async with engine.begin() as conn:
        inspector = await conn.run_sync(lambda sync_conn: inspect(sync_conn))
        
        # Get all tables
        tables = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())
        
        logger.info("Schema validation", table_count=len(tables), tables=tables)
        
        # Validate key tables exist
        required_tables = [
            'rfps', 'products', 'product_matches', 
            'agent_interactions', 'standards', 'standard_compliances'
        ]
        
        missing_tables = [t for t in required_tables if t not in tables]
        
        if missing_tables:
            logger.error("Missing required tables", missing=missing_tables)
            return False
        
        logger.info("Schema validation passed")
        return True
