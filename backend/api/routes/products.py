"""Product-related API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from db.database import get_db
from db.models import Product
from api.schemas import ProductSearchRequest

router = APIRouter()


@router.get("")
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    category: Optional[str] = None,
    brand: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get products with pagination and filtering.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        category: Filter by category
        brand: Filter by brand
        db: Database session
        
    Returns:
        List of products
    """
    query = select(Product)
    
    if category:
        query = query.where(Product.category == category)
    if brand:
        query = query.where(Product.brand == brand)
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    products = result.scalars().all()
    
    # Get total count
    count_query = select(func.count(Product.id))
    if category:
        count_query = count_query.where(Product.category == category)
    if brand:
        count_query = count_query.where(Product.brand == brand)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    return {
        "data": {
            "products": [
                {
                    "id": p.id,
                    "brand": p.brand,
                    "category": p.category,
                    "product_code": p.product_code,
                    "product_name": p.product_name,
                    "specifications": p.specifications,
                    "mrp": p.mrp,
                    "selling_price": p.selling_price,
                    "certifications": p.certifications,
                    "standard": p.standard,
                }
                for p in products
            ],
            "total": total,
            "skip": skip,
            "limit": limit,
        }
    }


@router.post("/search")
async def search_products(
    request: ProductSearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """Search products using semantic search.
    
    Args:
        request: Search request with query
        db: Database session
        
    Returns:
        Matching products
    """
    from data.vector_store import VectorStore
    
    vector_store = VectorStore()
    
    # Perform semantic search
    results = await vector_store.search(
        query=request.query,
        limit=request.limit
    )
    
    return {
        "data": {
            "query": request.query,
            "results": results,
        }
    }


@router.get("/{product_id}")
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get product details by ID.
    
    Args:
        product_id: Product ID
        db: Database session
        
    Returns:
        Product details
    """
    query = select(Product).where(Product.id == product_id)
    result = await db.execute(query)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {
        "data": {
            "id": product.id,
            "brand": product.brand,
            "category": product.category,
            "sub_category": product.sub_category,
            "product_code": product.product_code,
            "product_name": product.product_name,
            "model_name": product.model_name,
            "specifications": product.specifications,
            "mrp": product.mrp,
            "selling_price": product.selling_price,
            "dealer_price": product.dealer_price,
            "certifications": product.certifications,
            "bis_registration": product.bis_registration,
            "standard": product.standard,
            "hsn_code": product.hsn_code,
            "warranty_years": product.warranty_years,
            "country_of_origin": product.country_of_origin,
            "image_url": product.image_url,
            "datasheet_url": product.datasheet_url,
        }
    }
