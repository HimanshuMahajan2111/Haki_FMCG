"""
Product CRUD API - Add, Edit, Delete Products

Endpoints:
- POST   /api/products/add        - Add new product
- PUT    /api/products/{id}       - Update product
- DELETE /api/products/{id}       - Delete product
- GET    /api/products/validate   - Validate product data
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import structlog

from db.database import get_db
from db.models import Product

router = APIRouter(prefix="/api/products", tags=["products-crud"])
logger = structlog.get_logger()


class ProductCreate(BaseModel):
    """Product creation schema."""
    manufacturer: str = Field(..., description="Manufacturer name")
    product_code: str = Field(..., description="Product code/SKU")
    product_name: str = Field(..., description="Product name")
    category: str = Field(..., description="Product category")
    subcategory: Optional[str] = Field(None, description="Product subcategory")
    
    # Technical specifications
    voltage_rating: Optional[str] = Field(None, description="Voltage rating (e.g., '1.1 kV')")
    conductor_material: Optional[str] = Field(None, description="Conductor material (Copper/Aluminum)")
    conductor_size: Optional[str] = Field(None, description="Conductor size (e.g., '2.5 sq mm')")
    insulation_type: Optional[str] = Field(None, description="Insulation type")
    core_count: Optional[int] = Field(None, description="Number of cores")
    armoring: Optional[str] = Field(None, description="Armoring type")
    sheath_material: Optional[str] = Field(None, description="Sheath material")
    
    # Standards & certifications
    is_standard: Optional[str] = Field(None, description="IS standard (e.g., 'IS 1554')")
    iec_standard: Optional[str] = Field(None, description="IEC standard")
    bsi_standard: Optional[str] = Field(None, description="BSI standard")
    
    # Pricing
    list_price: Optional[float] = Field(None, description="List price per unit")
    unit: Optional[str] = Field("meter", description="Unit of measurement")
    
    # Additional specs (JSON)
    specifications: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional specifications")
    
    # Metadata
    description: Optional[str] = Field(None, description="Product description")
    datasheet_url: Optional[str] = Field(None, description="Datasheet URL")


class ProductUpdate(BaseModel):
    """Product update schema (all fields optional)."""
    manufacturer: Optional[str] = None
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    voltage_rating: Optional[str] = None
    conductor_material: Optional[str] = None
    conductor_size: Optional[str] = None
    insulation_type: Optional[str] = None
    core_count: Optional[int] = None
    armoring: Optional[str] = None
    sheath_material: Optional[str] = None
    is_standard: Optional[str] = None
    iec_standard: Optional[str] = None
    bsi_standard: Optional[str] = None
    list_price: Optional[float] = None
    unit: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    datasheet_url: Optional[str] = None


def map_api_to_db(product_data: ProductCreate) -> dict:
    """Convert API schema to database schema."""
    specs = product_data.specifications or {}
    
    # Add technical fields to specifications JSON
    if product_data.voltage_rating:
        specs['voltage_rating'] = product_data.voltage_rating
    if product_data.conductor_material:
        specs['conductor_material'] = product_data.conductor_material
    if product_data.conductor_size:
        specs['conductor_size'] = product_data.conductor_size
    if product_data.insulation_type:
        specs['insulation_type'] = product_data.insulation_type
    if product_data.core_count:
        specs['core_count'] = product_data.core_count
    if product_data.armoring:
        specs['armoring'] = product_data.armoring
    if product_data.sheath_material:
        specs['sheath_material'] = product_data.sheath_material
    if product_data.unit:
        specs['unit'] = product_data.unit
    if product_data.description:
        specs['description'] = product_data.description
    
    return {
        'brand': product_data.manufacturer,
        'category': product_data.category,
        'sub_category': product_data.subcategory,
        'product_code': product_data.product_code,
        'product_name': product_data.product_name,
        'specifications': specs,
        'mrp': product_data.list_price,
        'selling_price': product_data.list_price * 0.85 if product_data.list_price else None,
        'standard': product_data.is_standard or product_data.iec_standard or product_data.bsi_standard,
        'datasheet_url': product_data.datasheet_url
    }


@router.post("/add")
async def add_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Add a new OEM product to the database.
    
    Args:
        product: Product data
        db: Database session
        
    Returns:
        Created product with ID
    """
    logger.info("Adding new product", manufacturer=product.manufacturer, code=product.product_code)
    
    try:
        # Check if product already exists
        result = await db.execute(
            select(Product).where(
                Product.product_code == product.product_code
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Product {product.manufacturer} {product.product_code} already exists"
            )
        
        # Map API schema to database schema
        db_data = map_api_to_db(product)
        
        # Create new product
        new_product = Product(**db_data)
        
        db.add(new_product)
        await db.commit()
        await db.refresh(new_product)
        
        logger.info("Product added successfully", product_id=new_product.id)
        
        return {
            "success": True,
            "message": "Product added successfully",
            "data": {
                "id": new_product.id,
                "manufacturer": new_product.brand,
                "product_code": new_product.product_code,
                "product_name": new_product.product_name,
                "category": new_product.category
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error adding product", error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add product: {str(e)}")


@router.put("/{product_id}")
async def update_product(
    product_id: str,
    product_update: ProductUpdate,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update an existing product.
    
    Args:
        product_id: Product ID
        product_update: Fields to update
        db: Database session
        
    Returns:
        Updated product data
    """
    logger.info("Updating product", product_id=product_id)
    
    try:
        # Get existing product
        result = await db.execute(
            select(Product).where(Product.id == product_id)
        )
        product = result.scalar_one_or_none()
        
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        
        # Update fields (only non-None values)
        update_data = product_update.model_dump(exclude_unset=True, exclude_none=True)
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Map API fields to database fields
        if 'manufacturer' in update_data:
            product.brand = update_data.pop('manufacturer')
        if 'list_price' in update_data:
            product.mrp = update_data.pop('list_price')
            product.selling_price = product.mrp * 0.85 if product.mrp else None
        if 'subcategory' in update_data:
            product.sub_category = update_data.pop('subcategory')
        
        # Handle technical specifications - merge into specifications JSON
        specs = product.specifications or {}
        spec_fields = ['voltage_rating', 'conductor_material', 'conductor_size', 
                      'insulation_type', 'core_count', 'armoring', 'sheath_material',
                      'unit', 'description']
        
        for field in spec_fields:
            if field in update_data:
                specs[field] = update_data.pop(field)
        
        if specs:
            product.specifications = specs
        
        # Update remaining direct fields
        for field, value in update_data.items():
            if hasattr(product, field):
                setattr(product, field, value)
        
        product.updated_at = datetime.now()
        
        await db.commit()
        await db.refresh(product)
        
        logger.info("Product updated successfully", product_id=product_id, fields=list(update_data.keys()))
        
        return {
            "success": True,
            "message": "Product updated successfully",
            "data": {
                "id": product.id,
                "manufacturer": product.brand,
                "product_code": product.product_code,
                "product_name": product.product_name,
                "updated_fields": list(update_data.keys())
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating product", error=str(e), product_id=product_id)
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update product: {str(e)}")


@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Delete a product from the database.
    
    Args:
        product_id: Product ID
        db: Database session
        
    Returns:
        Deletion confirmation
    """
    logger.info("Deleting product", product_id=product_id)
    
    try:
        # Get existing product
        result = await db.execute(
            select(Product).where(Product.id == product_id)
        )
        product = result.scalar_one_or_none()
        
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        
        # Store info for response
        manufacturer = product.brand
        product_code = product.product_code
        
        # Delete product
        await db.delete(product)
        await db.commit()
        
        logger.info("Product deleted successfully", product_id=product_id)
        
        return {
            "success": True,
            "message": "Product deleted successfully",
            "data": {
                "id": product_id,
                "manufacturer": manufacturer,
                "product_code": product_code
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting product", error=str(e), product_id=product_id)
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete product: {str(e)}")


@router.post("/validate")
async def validate_product_data(
    product: ProductCreate
) -> Dict[str, Any]:
    """
    Validate product data without saving.
    
    Args:
        product: Product data to validate
        
    Returns:
        Validation result
    """
    errors = []
    warnings = []
    
    # Required fields
    if not product.manufacturer or len(product.manufacturer) < 2:
        errors.append("Manufacturer name is required (min 2 characters)")
    
    if not product.product_code or len(product.product_code) < 2:
        errors.append("Product code is required (min 2 characters)")
    
    if not product.product_name or len(product.product_name) < 3:
        errors.append("Product name is required (min 3 characters)")
    
    if not product.category:
        errors.append("Category is required")
    
    # Warnings for optional but recommended fields
    if not product.voltage_rating:
        warnings.append("Voltage rating not specified")
    
    if not product.conductor_material:
        warnings.append("Conductor material not specified")
    
    if not product.list_price:
        warnings.append("List price not specified")
    
    if not product.is_standard and not product.iec_standard:
        warnings.append("No standards specified")
    
    is_valid = len(errors) == 0
    
    return {
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "message": "Validation passed" if is_valid else "Validation failed"
    }


@router.get("/fields")
async def get_product_fields() -> Dict[str, Any]:
    """
    Get all available product fields with descriptions.
    
    Returns:
        Field definitions for frontend form
    """
    return {
        "fields": {
            "manufacturer": {
                "type": "string",
                "required": True,
                "description": "Manufacturer name (e.g., Havells, Polycab, KEI)",
                "example": "Havells"
            },
            "product_code": {
                "type": "string",
                "required": True,
                "description": "Product SKU/Code",
                "example": "HRFR-1100-2C-2.5"
            },
            "product_name": {
                "type": "string",
                "required": True,
                "description": "Full product name",
                "example": "Havells Lifeline Plus HRFR Cable 1.1kV 2C x 2.5 sq mm"
            },
            "category": {
                "type": "string",
                "required": True,
                "options": ["Power Cables", "Control Cables", "Instrumentation Cables", "Flexible Cables", "Wires"],
                "description": "Product category"
            },
            "voltage_rating": {
                "type": "string",
                "required": False,
                "options": ["1.1 kV", "3.3 kV", "6.6 kV", "11 kV", "22 kV", "33 kV"],
                "description": "Voltage rating"
            },
            "conductor_material": {
                "type": "string",
                "required": False,
                "options": ["Copper", "Aluminum", "Tinned Copper"],
                "description": "Conductor material"
            },
            "conductor_size": {
                "type": "string",
                "required": False,
                "description": "Conductor cross-sectional area",
                "example": "2.5 sq mm"
            },
            "core_count": {
                "type": "integer",
                "required": False,
                "description": "Number of cores",
                "example": 2
            },
            "insulation_type": {
                "type": "string",
                "required": False,
                "options": ["XLPE", "PVC", "FR-XLPE", "LSZH"],
                "description": "Insulation material"
            },
            "armoring": {
                "type": "string",
                "required": False,
                "options": ["Armoured", "Unarmoured", "SWA", "STA"],
                "description": "Armoring type"
            },
            "is_standard": {
                "type": "string",
                "required": False,
                "description": "IS standard code",
                "example": "IS 1554"
            },
            "list_price": {
                "type": "number",
                "required": False,
                "description": "List price per unit (₹)",
                "example": 125.50
            },
            "unit": {
                "type": "string",
                "required": False,
                "default": "meter",
                "options": ["meter", "km", "piece", "coil"],
                "description": "Unit of measurement"
            }
        }
    }
