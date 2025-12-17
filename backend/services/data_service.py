"""Centralized data service for managing all loaded data."""
import asyncio
from typing import Dict, Any, List, Optional
import structlog
from functools import lru_cache

from data import (
    ValidatedProductLoader,
    PricingDataLoader,
    TestingDataLoader,
    StandardsDataLoader,
    HistoricalRFPLoader,
)

logger = structlog.get_logger()


class DataService:
    """Centralized service for accessing all loaded data."""
    
    def __init__(self):
        """Initialize data service with all loaders."""
        self.logger = logger.bind(component="DataService")
        
        # Initialize loaders
        self.product_loader = ValidatedProductLoader()
        self.pricing_loader = PricingDataLoader()
        self.testing_loader = TestingDataLoader()
        self.standards_loader = StandardsDataLoader()
        self.rfp_loader = HistoricalRFPLoader()
        
        # Cache for loaded data
        self._products_cache: Optional[List[Dict[str, Any]]] = None
        self._pricing_cache: Optional[List[Dict[str, Any]]] = None
        self._testing_cache: Optional[Dict[str, Any]] = None
        self._standards_cache: Optional[Dict[str, Any]] = None
        self._rfps_cache: Optional[List[Dict[str, Any]]] = None
        
        self._initialized = False
    
    async def initialize(self, force_reload: bool = False):
        """Load all data into memory.
        
        Args:
            force_reload: Force reload even if already initialized
        """
        if self._initialized and not force_reload:
            self.logger.info("Data service already initialized")
            return
        
        self.logger.info("Initializing data service - loading all data")
        
        # Load all data in parallel
        results = await asyncio.gather(
            self.product_loader.load(),
            self.pricing_loader.load(),
            self.testing_loader.load(),
            self.standards_loader.load(),
            self.rfp_loader.load(),
            return_exceptions=True
        )
        
        # Store results
        self._products_cache = results[0] if not isinstance(results[0], Exception) else []
        self._pricing_cache = results[1] if not isinstance(results[1], Exception) else []
        self._testing_cache = results[2] if not isinstance(results[2], Exception) else {}
        self._standards_cache = results[3] if not isinstance(results[3], Exception) else {}
        self._rfps_cache = results[4] if not isinstance(results[4], Exception) else []
        
        # Log any errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                loader_names = ["Products", "Pricing", "Testing", "Standards", "RFPs"]
                self.logger.error(
                    f"Failed to load {loader_names[i]} data",
                    error=str(result)
                )
        
        self._initialized = True
        
        self.logger.info(
            "Data service initialized",
            products=len(self._products_cache),
            pricing=len(self._pricing_cache),
            testing_categories=len(self._testing_cache),
            standards_categories=len(self._standards_cache),
            rfps=len(self._rfps_cache)
        )
    
    # ========== Product Methods ==========
    
    async def get_products(
        self,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get products with filtering and pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            category: Filter by category
            brand: Filter by brand
            search: Search in product name
            
        Returns:
            List of products
        """
        if not self._initialized:
            await self.initialize()
        
        products = self._products_cache or []
        
        # Apply filters
        if category:
            products = [p for p in products if p.get("category") == category]
        if brand:
            products = [p for p in products if p.get("brand") == brand]
        if search:
            search_lower = search.lower()
            products = [
                p for p in products
                if search_lower in p.get("name", "").lower()
                or search_lower in p.get("category", "").lower()
            ]
        
        # Apply pagination
        return products[skip:skip + limit]
    
    async def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific product by ID or product code.
        
        Args:
            product_id: Product ID or product code
            
        Returns:
            Product dict or None
        """
        if not self._initialized:
            await self.initialize()
        
        products = self._products_cache or []
        
        for product in products:
            if (product.get("product_code") == product_id or
                product.get("id") == product_id):
                return product
        
        return None
    
    async def get_products_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all products in a category.
        
        Args:
            category: Category name
            
        Returns:
            List of products
        """
        return await self.get_products(category=category, limit=10000)
    
    async def get_products_by_brand(self, brand: str) -> List[Dict[str, Any]]:
        """Get all products from a brand.
        
        Args:
            brand: Brand name
            
        Returns:
            List of products
        """
        return await self.get_products(brand=brand, limit=10000)
    
    async def get_product_categories(self) -> List[str]:
        """Get list of all product categories.
        
        Returns:
            List of unique categories
        """
        if not self._initialized:
            await self.initialize()
        
        products = self._products_cache or []
        categories = set(p.get("category") for p in products if p.get("category"))
        return sorted(list(categories))
    
    async def get_product_brands(self) -> List[str]:
        """Get list of all product brands.
        
        Returns:
            List of unique brands
        """
        if not self._initialized:
            await self.initialize()
        
        products = self._products_cache or []
        brands = set(p.get("brand") for p in products if p.get("brand"))
        return sorted(list(brands))
    
    # ========== Pricing Methods ==========
    
    async def get_pricing(
        self,
        skip: int = 0,
        limit: int = 100,
        product_code: Optional[str] = None,
        brand: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get pricing records with filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            product_code: Filter by product code
            brand: Filter by brand
            
        Returns:
            List of pricing records
        """
        if not self._initialized:
            await self.initialize()
        
        pricing = self._pricing_cache or []
        
        # Apply filters
        if product_code:
            pricing = [p for p in pricing if p.get("product_code") == product_code]
        if brand:
            pricing = [p for p in pricing if p.get("brand") == brand]
        
        # Apply pagination
        return pricing[skip:skip + limit]
    
    async def get_pricing_for_product(self, product_code: str) -> Optional[Dict[str, Any]]:
        """Get pricing for a specific product.
        
        Args:
            product_code: Product code
            
        Returns:
            Pricing dict or None
        """
        if not self._initialized:
            await self.initialize()
        
        pricing = self._pricing_cache or []
        
        for price in pricing:
            if price.get("product_code") == product_code:
                return price
        
        return None
    
    # ========== Testing Methods ==========
    
    async def get_testing_data(self) -> Dict[str, Any]:
        """Get all testing data.
        
        Returns:
            Dict with testing categories
        """
        if not self._initialized:
            await self.initialize()
        
        return self._testing_cache or {}
    
    async def get_test_by_name(self, test_name: str) -> Optional[Dict[str, Any]]:
        """Find a test by name across all categories.
        
        Args:
            test_name: Test name to search for
            
        Returns:
            Test dict or None
        """
        if not self._initialized:
            await self.initialize()
        
        testing = self._testing_cache or {}
        
        for category, tests in testing.items():
            if isinstance(tests, list):
                for test in tests:
                    if test.get("test_name") == test_name:
                        return {**test, "category": category}
        
        return None
    
    async def get_tests_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all tests in a category.
        
        Args:
            category: Test category
            
        Returns:
            List of tests
        """
        if not self._initialized:
            await self.initialize()
        
        testing = self._testing_cache or {}
        return testing.get(category, [])
    
    # ========== Standards Methods ==========
    
    async def get_standards_data(self) -> Dict[str, Any]:
        """Get all standards data.
        
        Returns:
            Dict with standards categories
        """
        if not self._initialized:
            await self.initialize()
        
        return self._standards_cache or {}
    
    async def get_standard_by_code(self, standard_code: str) -> Optional[Dict[str, Any]]:
        """Find a standard by code.
        
        Args:
            standard_code: Standard code to search for
            
        Returns:
            Standard dict or None
        """
        if not self._initialized:
            await self.initialize()
        
        standards = self._standards_cache or {}
        
        for category, standards_list in standards.items():
            if isinstance(standards_list, list):
                for standard in standards_list:
                    if standard.get("standard_code") == standard_code:
                        return {**standard, "category": category}
        
        return None
    
    async def get_indian_standards(self) -> List[Dict[str, Any]]:
        """Get all Indian standards.
        
        Returns:
            List of Indian standards
        """
        if not self._initialized:
            await self.initialize()
        
        standards = self._standards_cache or {}
        return standards.get("indian_standards", [])
    
    async def get_international_standards(self) -> List[Dict[str, Any]]:
        """Get all international standards.
        
        Returns:
            List of international standards
        """
        if not self._initialized:
            await self.initialize()
        
        standards = self._standards_cache or {}
        return standards.get("international_standards", [])
    
    # ========== Historical RFP Methods ==========
    
    async def get_historical_rfps(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get historical RFPs.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of RFPs
        """
        if not self._initialized:
            await self.initialize()
        
        rfps = self._rfps_cache or []
        return rfps[skip:skip + limit]
    
    async def add_historical_rfp(self, rfp_data: Dict[str, Any]):
        """Add a new historical RFP record.
        
        Args:
            rfp_data: RFP data to add
        """
        if not self._initialized:
            await self.initialize()
        
        # Add to cache
        if self._rfps_cache is None:
            self._rfps_cache = []
        
        self._rfps_cache.append(rfp_data)
        
        # Save to disk
        await self.rfp_loader.save_rfp_history(self._rfps_cache)
        
        self.logger.info("Added historical RFP", rfp_id=rfp_data.get("rfp_id"))
    
    # ========== Statistics Methods ==========
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get overall data statistics.
        
        Returns:
            Statistics dict
        """
        if not self._initialized:
            await self.initialize()
        
        testing = self._testing_cache or {}
        standards = self._standards_cache or {}
        
        total_tests = sum(
            len(v) if isinstance(v, list) else 0
            for v in testing.values()
        )
        
        total_standards = sum(
            len(v) if isinstance(v, list) else 0
            for v in standards.values()
        )
        
        return {
            "products": {
                "total": len(self._products_cache or []),
                "categories": len(await self.get_product_categories()),
                "brands": len(await self.get_product_brands()),
            },
            "pricing": {
                "total": len(self._pricing_cache or []),
            },
            "testing": {
                "total": total_tests,
                "categories": len(testing),
            },
            "standards": {
                "total": total_standards,
                "categories": len(standards),
            },
            "historical_rfps": {
                "total": len(self._rfps_cache or []),
            },
        }


# Global singleton instance
_data_service_instance: Optional[DataService] = None


def get_data_service() -> DataService:
    """Get or create the global DataService instance.
    
    Returns:
        DataService instance
    """
    global _data_service_instance
    
    if _data_service_instance is None:
        _data_service_instance = DataService()
    
    return _data_service_instance
