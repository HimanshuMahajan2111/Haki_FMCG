"""OEM Products API endpoints - Optimized for 693 database products."""
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import AsyncSessionLocal
from db.product_models import OEMProduct
from pydantic import BaseModel

router = APIRouter()


class ProductResponse(BaseModel):
    """Product response model."""
    product_id: str
    manufacturer: str
    model_number: str
    product_name: str
    category: str
    specifications: dict
    unit_price: float
    stock_quantity: int
    delivery_days: int
    certifications: list
    standards: list
    voltage_rating: Optional[str] = None
    conductor_material: Optional[str] = None
    conductor_size: Optional[str] = None
    
    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Product list response."""
    products: List[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class StatsResponse(BaseModel):
    """Statistics response."""
    total_products: int
    manufacturers: dict
    categories: dict


@router.get("/products", response_model=ProductListResponse)
async def get_oem_products(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    manufacturer: Optional[str] = Query(None, description="Filter by manufacturer"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in product name"),
    voltage: Optional[str] = Query(None, description="Filter by voltage rating"),
    conductor_material: Optional[str] = Query(None, description="Filter by conductor material"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
):
    """
    Get OEM products with pagination and advanced filtering.
    
    - **page**: Page number (starts at 1)
    - **page_size**: Number of items per page (max 100)
    - **manufacturer**: Filter by manufacturer (Havells, Polycab, KEI, Finolex, RR Kabel)
    - **category**: Filter by category
    - **search**: Search in product names
    - **voltage**: Filter by voltage rating
    - **conductor_material**: Filter by conductor material
    - **min_price**: Minimum unit price
    - **max_price**: Maximum unit price
    """
    async with AsyncSessionLocal() as db:
        # Build query
        query = select(OEMProduct).where(OEMProduct.is_active == True)
        
        # Apply filters
        if manufacturer:
            query = query.where(OEMProduct.manufacturer.ilike(f"%{manufacturer}%"))
        
        if category:
            query = query.where(OEMProduct.category.ilike(f"%{category}%"))
        
        if search:
            query = query.where(OEMProduct.product_name.ilike(f"%{search}%"))
        
        if voltage:
            query = query.where(OEMProduct.voltage_rating.ilike(f"%{voltage}%"))
        
        if conductor_material:
            query = query.where(OEMProduct.conductor_material.ilike(f"%{conductor_material}%"))
        
        if min_price is not None:
            query = query.where(OEMProduct.unit_price >= min_price)
        
        if max_price is not None:
            query = query.where(OEMProduct.unit_price <= max_price)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        result = await db.execute(query)
        products = result.scalars().all()
        
        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size
        
        return ProductListResponse(
            products=[ProductResponse.from_orm(p) for p in products],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product_by_id(product_id: str):
    """
    Get a specific OEM product by ID.
    
    - **product_id**: Unique product identifier
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(OEMProduct).where(OEMProduct.product_id == product_id)
        )
        product = result.scalar_one_or_none()
        
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        
        return ProductResponse.from_orm(product)


@router.get("/manufacturers")
async def get_manufacturers():
    """
    Get list of all manufacturers with product counts.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(
                OEMProduct.manufacturer,
                func.count(OEMProduct.id).label('count')
            )
            .where(OEMProduct.is_active == True)
            .group_by(OEMProduct.manufacturer)
            .order_by(func.count(OEMProduct.id).desc())
        )
        manufacturers = {row[0]: row[1] for row in result.all()}
        
        return {
            "manufacturers": manufacturers,
            "total": len(manufacturers)
        }


@router.get("/categories")
async def get_categories():
    """
    Get list of all product categories with counts.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(
                OEMProduct.category,
                func.count(OEMProduct.id).label('count')
            )
            .where(OEMProduct.is_active == True)
            .group_by(OEMProduct.category)
            .order_by(func.count(OEMProduct.id).desc())
        )
        categories = {row[0]: row[1] for row in result.all()}
        
        return {
            "categories": categories,
            "total": len(categories)
        }


@router.get("/statistics", response_model=StatsResponse)
async def get_statistics():
    """
    Get comprehensive product statistics.
    """
    async with AsyncSessionLocal() as db:
        # Total products
        total_result = await db.execute(
            select(func.count(OEMProduct.id)).where(OEMProduct.is_active == True)
        )
        total_products = total_result.scalar()
        
        # By manufacturer
        mfg_result = await db.execute(
            select(
                OEMProduct.manufacturer,
                func.count(OEMProduct.id).label('count')
            )
            .where(OEMProduct.is_active == True)
            .group_by(OEMProduct.manufacturer)
        )
        manufacturers = {row[0]: row[1] for row in mfg_result.all()}
        
        # By category
        cat_result = await db.execute(
            select(
                OEMProduct.category,
                func.count(OEMProduct.id).label('count')
            )
            .where(OEMProduct.is_active == True)
            .group_by(OEMProduct.category)
        )
        categories = {row[0]: row[1] for row in cat_result.all()}
        
        return StatsResponse(
            total_products=total_products,
            manufacturers=manufacturers,
            categories=categories
        )


@router.get("/search")
async def search_products(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results")
):
    """
    Search products by name, category, or specifications.
    
    - **q**: Search query (minimum 2 characters)
    - **limit**: Maximum number of results
    """
    async with AsyncSessionLocal() as db:
        # Search in multiple fields
        query = select(OEMProduct).where(
            OEMProduct.is_active == True,
            or_(
                OEMProduct.product_name.ilike(f"%{q}%"),
                OEMProduct.category.ilike(f"%{q}%"),
                OEMProduct.manufacturer.ilike(f"%{q}%"),
                OEMProduct.model_number.ilike(f"%{q}%")
            )
        ).limit(limit)
        
        result = await db.execute(query)
        products = result.scalars().all()
        
        return {
            "query": q,
            "results": [ProductResponse.from_orm(p) for p in products],
            "count": len(products)
        }


@router.get("/voltage-ratings")
async def get_voltage_ratings():
    """Get list of all voltage ratings."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(OEMProduct.voltage_rating, func.count(OEMProduct.id))
            .where(OEMProduct.is_active == True, OEMProduct.voltage_rating.isnot(None))
            .group_by(OEMProduct.voltage_rating)
            .order_by(func.count(OEMProduct.id).desc())
        )
        ratings = {row[0]: row[1] for row in result.all()}
        return {"voltage_ratings": ratings}


@router.get("/conductor-materials")
async def get_conductor_materials():
    """Get list of all conductor materials."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(OEMProduct.conductor_material, func.count(OEMProduct.id))
            .where(OEMProduct.is_active == True, OEMProduct.conductor_material.isnot(None))
            .group_by(OEMProduct.conductor_material)
            .order_by(func.count(OEMProduct.id).desc())
        )
        materials = {row[0]: row[1] for row in result.all()}
        return {"conductor_materials": materials}
