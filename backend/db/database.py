"""Database connection and session management."""
import structlog
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator

from config.settings import settings

logger = structlog.get_logger()

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db(use_enhanced: bool = True):
    """Initialize database tables.
    
    Args:
        use_enhanced: If True, use enhanced schema with relationships (recommended)
    """
    logger.info("Initializing database", use_enhanced=use_enhanced)
    
    async with engine.begin() as conn:
        # Import models to ensure they're registered
        if use_enhanced:
            from db import models_enhanced  # noqa
            logger.info("Using enhanced schema")
        else:
            from db import models  # noqa
            logger.info("Using basic schema")
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database initialized successfully")


async def close_db():
    """Close database connections."""
    logger.info("Closing database connections")
    await engine.dispose()
