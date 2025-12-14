"""Database initialization script."""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import init_db, get_db
from data.product_loader import ProductDataLoader
from data.vector_store import VectorStore
import structlog

logger = structlog.get_logger()


async def initialize_database():
    """Initialize database and load data."""
    logger.info("Starting database initialization")
    
    # Create tables
    await init_db()
    logger.info("Database tables created")
    
    # Load products
    loader = ProductDataLoader()
    products = loader.load_all_products()
    logger.info("Products loaded", count=len(products))
    
    # Initialize vector store
    vector_store = VectorStore()
    await vector_store.initialize()
    
    # Add products to vector store
    await vector_store.add_products(products)
    logger.info("Products added to vector store")
    
    # Store products in database
    async for db in get_db():
        from db.models import Product
        
        for product_data in products:
            product = Product(
                name=product_data["name"],
                category=product_data["category"],
                brand=product_data["brand"],
                specifications=product_data.get("specifications", {}),
                price=product_data.get("price"),
                description=product_data.get("description"),
            )
            db.add(product)
        
        await db.commit()
        logger.info("Products stored in database")
        break
    
    logger.info("Database initialization completed")


if __name__ == "__main__":
    asyncio.run(initialize_database())
