"""FastAPI application entry point."""
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from api.routes import health, rfp, products, analytics, agents
from db.database import init_db, close_db
from utils.logger import setup_logging


# Setup logging
setup_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting RFP Response System", environment=settings.environment)
    
    # Initialize database
    await init_db()
    
    # Initialize vector database
    from data.vector_store import VectorStore
    vector_store = VectorStore()
    await vector_store.initialize()
    
    logger.info("Application started successfully")
    
    yield
    
    # Cleanup
    logger.info("Shutting down application")
    await close_db()


app = FastAPI(
    title=settings.app_name,
    description="AI-Powered Multi-Agent System for B2B RFP Response Automation",
    version="1.0.0",
    lifespan=lifespan,
    debug=settings.debug
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(rfp.router, prefix="/api/rfp", tags=["RFP"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "RFP Response System API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
