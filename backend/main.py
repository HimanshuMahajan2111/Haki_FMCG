"""FastAPI application entry point."""
import structlog
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config.settings import settings
from api.routes import health, rfp, products, analytics, agents, data, challenge, workflow, oem_products, website_scanner
from api.routes import products_crud, agent_logs, file_upload, rfp_analysis, rfp_workflow
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
    
    # Initialize data service (loads all CSV/JSON data)
    from services import get_data_service, get_vector_store_service
    data_service = get_data_service()
    await data_service.initialize()
    logger.info("Data service initialized")
    
    # Initialize vector store service
    vector_service = get_vector_store_service()
    await vector_service.initialize()
    logger.info("Vector store initialized")
    
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
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(rfp.router, prefix="/api/rfp", tags=["RFP"])
app.include_router(rfp_analysis.router, prefix="/api/rfp", tags=["RFP Analysis"])
app.include_router(rfp_workflow.router, prefix="/api/rfp-workflow", tags=["RFP Workflow"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(oem_products.router, prefix="/api/oem", tags=["OEM Products"])
app.include_router(products_crud.router, tags=["Product Management"])
app.include_router(website_scanner.router, prefix="/api/scanner", tags=["Website Scanner"])
app.include_router(agent_logs.router, tags=["Agent Logs"])
app.include_router(file_upload.router, tags=["File Upload"])
app.include_router(data.router, prefix="/api/data", tags=["Data"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])
app.include_router(workflow.router, tags=["Workflow"])
app.include_router(challenge.router)


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
