"""Data-related API endpoints for pricing, testing, and standards."""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from services import get_data_service

router = APIRouter()


# ========== Pricing Endpoints ==========

@router.get("/pricing")
async def get_pricing(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    product_code: Optional[str] = None,
    brand: Optional[str] = None
):
    """Get pricing records with pagination and filtering.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        product_code: Filter by product code
        brand: Filter by brand
        
    Returns:
        List of pricing records
    """
    data_service = get_data_service()
    
    pricing = await data_service.get_pricing(
        skip=skip,
        limit=limit,
        product_code=product_code,
        brand=brand
    )
    
    # Get total count
    all_pricing = await data_service.get_pricing(
        product_code=product_code,
        brand=brand,
        limit=100000
    )
    total = len(all_pricing)
    
    return {
        "data": {
            "pricing": pricing,
            "total": total,
            "skip": skip,
            "limit": limit,
        }
    }


@router.get("/pricing/{product_code}")
async def get_pricing_for_product(product_code: str):
    """Get pricing for a specific product.
    
    Args:
        product_code: Product code
        
    Returns:
        Pricing details
    """
    data_service = get_data_service()
    pricing = await data_service.get_pricing_for_product(product_code)
    
    if not pricing:
        raise HTTPException(status_code=404, detail="Pricing not found for product")
    
    return {
        "data": pricing
    }


# ========== Testing Endpoints ==========

@router.get("/testing")
async def get_testing_data():
    """Get all testing data.
    
    Returns:
        Testing data organized by category
    """
    data_service = get_data_service()
    testing = await data_service.get_testing_data()
    
    # Calculate statistics
    total_tests = sum(
        len(v) if isinstance(v, list) else 0
        for v in testing.values()
    )
    
    return {
        "data": {
            "testing": testing,
            "categories": list(testing.keys()),
            "total_tests": total_tests
        }
    }


@router.get("/testing/{category}")
async def get_tests_by_category(category: str):
    """Get tests in a specific category.
    
    Args:
        category: Test category
        
    Returns:
        List of tests
    """
    data_service = get_data_service()
    tests = await data_service.get_tests_by_category(category)
    
    if not tests:
        raise HTTPException(status_code=404, detail=f"No tests found in category: {category}")
    
    return {
        "data": {
            "category": category,
            "tests": tests,
            "count": len(tests)
        }
    }


@router.get("/testing/test/{test_name}")
async def get_test_by_name(test_name: str):
    """Find a test by name.
    
    Args:
        test_name: Test name to search for
        
    Returns:
        Test details
    """
    data_service = get_data_service()
    test = await data_service.get_test_by_name(test_name)
    
    if not test:
        raise HTTPException(status_code=404, detail=f"Test not found: {test_name}")
    
    return {
        "data": test
    }


# ========== Standards Endpoints ==========

@router.get("/standards")
async def get_standards_data():
    """Get all standards data.
    
    Returns:
        Standards data organized by category
    """
    data_service = get_data_service()
    standards = await data_service.get_standards_data()
    
    # Calculate statistics
    total_standards = sum(
        len(v) if isinstance(v, list) else 0
        for v in standards.values()
    )
    
    return {
        "data": {
            "standards": standards,
            "categories": list(standards.keys()),
            "total_standards": total_standards
        }
    }


@router.get("/standards/indian")
async def get_indian_standards():
    """Get all Indian standards.
    
    Returns:
        List of Indian standards
    """
    data_service = get_data_service()
    standards = await data_service.get_indian_standards()
    
    return {
        "data": {
            "standards": standards,
            "count": len(standards)
        }
    }


@router.get("/standards/international")
async def get_international_standards():
    """Get all international standards.
    
    Returns:
        List of international standards
    """
    data_service = get_data_service()
    standards = await data_service.get_international_standards()
    
    return {
        "data": {
            "standards": standards,
            "count": len(standards)
        }
    }


@router.get("/standards/{standard_code}")
async def get_standard_by_code(standard_code: str):
    """Find a standard by code.
    
    Args:
        standard_code: Standard code to search for
        
    Returns:
        Standard details
    """
    data_service = get_data_service()
    standard = await data_service.get_standard_by_code(standard_code)
    
    if not standard:
        raise HTTPException(status_code=404, detail=f"Standard not found: {standard_code}")
    
    return {
        "data": standard
    }


# ========== Historical RFP Endpoints ==========

@router.get("/historical-rfps")
async def get_historical_rfps(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """Get historical RFPs.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of historical RFPs
    """
    data_service = get_data_service()
    
    rfps = await data_service.get_historical_rfps(
        skip=skip,
        limit=limit
    )
    
    # Get total count
    all_rfps = await data_service.get_historical_rfps(limit=10000)
    total = len(all_rfps)
    
    return {
        "data": {
            "rfps": rfps,
            "total": total,
            "skip": skip,
            "limit": limit,
        }
    }


# ========== Vector Store Endpoints ==========

@router.post("/vector-store/populate")
async def populate_vector_store(force_repopulate: bool = False):
    """Populate vector store with products.
    
    Args:
        force_repopulate: Force repopulate even if data exists
        
    Returns:
        Population status
    """
    from services import get_vector_store_service
    
    vector_service = get_vector_store_service()
    result = await vector_service.populate_from_data_service(force_repopulate)
    
    return {
        "data": result
    }


@router.get("/vector-store/status")
async def get_vector_store_status():
    """Get vector store status.
    
    Returns:
        Vector store statistics
    """
    from services import get_vector_store_service
    
    vector_service = get_vector_store_service()
    stats = await vector_service.get_statistics()
    
    return {
        "data": stats
    }


@router.get("/vector-store/health")
async def check_vector_store_health():
    """Check vector store health.
    
    Returns:
        Health status
    """
    from services import get_vector_store_service
    
    vector_service = get_vector_store_service()
    health = await vector_service.health_check()
    
    return {
        "data": health
    }
