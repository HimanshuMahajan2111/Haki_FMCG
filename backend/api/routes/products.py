"""Product-related API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from db.database import get_db
from db.models import Product
from api.schemas import ProductSearchRequest
from services import get_data_service, get_vector_store_service

router = APIRouter()


@router.get("")
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    category: Optional[str] = None,
    brand: Optional[str] = None,
    search: Optional[str] = None
):
    """Get products with pagination and filtering.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        category: Filter by category
        brand: Filter by brand
        search: Search query
        
    Returns:
        List of products with pagination info
    """
    data_service = get_data_service()
    
    # Get products from data service
    products = await data_service.get_products(
        skip=skip,
        limit=limit,
        category=category,
        brand=brand,
        search=search
    )
    
    # Get total count (without pagination)
    all_products = await data_service.get_products(
        category=category,
        brand=brand,
        search=search,
        limit=100000
    )
    total = len(all_products)
    
    return {
        "data": {
            "products": products,
            "total": total,
            "skip": skip,
            "limit": limit,
        }
    }


@router.post("/search")
async def search_products(request: ProductSearchRequest):
    """Search products using semantic search.
    
    Args:
        request: Search request with query
        
    Returns:
        Matching products from vector store
    """
    vector_store_service = get_vector_store_service()
    
    # Perform semantic search
    results = await vector_store_service.search_products(
        query=request.query,
        limit=request.limit
    )
    
    return {
        "data": {
            "query": request.query,
            "results": results,
            "count": len(results)
        }
    }


@router.get("/categories")
async def get_categories():
    """Get list of all product categories.
    
    Returns:
        List of categories
    """
    data_service = get_data_service()
    categories = await data_service.get_product_categories()
    
    return {
        "data": {
            "categories": categories,
            "count": len(categories)
        }
    }


@router.get("/brands")
async def get_brands():
    """Get list of all product brands.
    
    Returns:
        List of brands
    """
    data_service = get_data_service()
    brands = await data_service.get_product_brands()
    
    return {
        "data": {
            "brands": brands,
            "count": len(brands)
        }
    }


@router.get("/statistics")
async def get_statistics():
    """Get product statistics.
    
    Returns:
        Statistics about products
    """
    data_service = get_data_service()
    stats = await data_service.get_statistics()
    
    return {
        "data": stats
    }


@router.get("/{product_id}")
async def get_product(product_id: str):
    """Get product details by ID or product code.
    
    Args:
        product_id: Product ID or product code
        
    Returns:
        Product details
    """
    data_service = get_data_service()
    product = await data_service.get_product_by_id(product_id)
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {
        "data": product
    }
