"""Service for populating vector store with product data."""
import asyncio
from typing import List, Dict, Any
import structlog

from data.vector_store import VectorStore
from services.data_service import get_data_service

logger = structlog.get_logger()


class VectorStoreService:
    """Service for managing vector store population and updates."""
    
    def __init__(self):
        """Initialize vector store service."""
        self.logger = logger.bind(component="VectorStoreService")
        self.vector_store = VectorStore()
        self.data_service = get_data_service()
    
    async def initialize(self):
        """Initialize vector store."""
        await self.vector_store.initialize()
        self.logger.info("Vector store service initialized")
    
    async def populate_from_data_service(self, force_repopulate: bool = False):
        """Populate vector store with products from data service.
        
        Args:
            force_repopulate: Clear and repopulate even if data exists
        """
        self.logger.info("Starting vector store population")
        
        # Ensure vector store is initialized
        if not self.vector_store.collection:
            await self.initialize()
        
        # Check if already populated
        current_count = self.vector_store.collection.count()
        
        if current_count > 0 and not force_repopulate:
            self.logger.info(
                "Vector store already populated",
                count=current_count
            )
            return {
                "status": "already_populated",
                "count": current_count,
                "action": "skipped"
            }
        
        # Clear existing data if force repopulate
        if force_repopulate and current_count > 0:
            self.logger.info("Clearing existing vector store data")
            # Delete collection and recreate
            self.vector_store.client.delete_collection("products")
            self.vector_store.collection = self.vector_store.client.create_collection(
                name="products",
                metadata={"description": "Product embeddings for semantic search"}
            )
        
        # Load products from data service
        self.logger.info("Loading products from data service")
        await self.data_service.initialize()
        
        products = await self.data_service.get_products(limit=100000)
        
        if not products:
            self.logger.warning("No products found in data service")
            return {
                "status": "error",
                "message": "No products available",
                "count": 0
            }
        
        # Filter valid products (must have name)
        valid_products = [p for p in products if p.get("name")]
        
        self.logger.info(
            "Filtered products for vector store",
            total=len(products),
            valid=len(valid_products)
        )
        
        # Add products to vector store
        await self.vector_store.add_products(valid_products)
        
        final_count = self.vector_store.collection.count()
        
        self.logger.info(
            "Vector store population completed",
            count=final_count
        )
        
        return {
            "status": "success",
            "total_products": len(products),
            "valid_products": len(valid_products),
            "vector_store_count": final_count,
            "action": "repopulated" if force_repopulate else "populated"
        }
    
    async def add_single_product(self, product: Dict[str, Any]):
        """Add a single product to vector store.
        
        Args:
            product: Product dictionary
        """
        if not self.vector_store.collection:
            await self.initialize()
        
        if not product.get("name"):
            self.logger.warning(
                "Skipping product without name",
                product_code=product.get("product_code")
            )
            return
        
        await self.vector_store.add_products([product])
        
        self.logger.info(
            "Added product to vector store",
            product_code=product.get("product_code")
        )
    
    async def update_product(self, product_code: str, product: Dict[str, Any]):
        """Update a product in vector store.
        
        Args:
            product_code: Product code to update
            product: Updated product dictionary
        """
        if not self.vector_store.collection:
            await self.initialize()
        
        # Delete old entry
        try:
            self.vector_store.collection.delete(ids=[product_code])
        except Exception as e:
            self.logger.warning(
                "Failed to delete old product entry",
                product_code=product_code,
                error=str(e)
            )
        
        # Add updated entry
        await self.add_single_product(product)
        
        self.logger.info(
            "Updated product in vector store",
            product_code=product_code
        )
    
    async def remove_product(self, product_code: str):
        """Remove a product from vector store.
        
        Args:
            product_code: Product code to remove
        """
        if not self.vector_store.collection:
            await self.initialize()
        
        try:
            self.vector_store.collection.delete(ids=[product_code])
            self.logger.info(
                "Removed product from vector store",
                product_code=product_code
            )
        except Exception as e:
            self.logger.error(
                "Failed to remove product",
                product_code=product_code,
                error=str(e)
            )
            raise
    
    async def search_products(
        self,
        query: str,
        limit: int = 10,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Search products in vector store.
        
        Args:
            query: Search query
            limit: Maximum number of results
            filters: Optional filters (category, brand, etc.)
            
        Returns:
            List of matching products
        """
        if not self.vector_store.collection:
            await self.initialize()
        
        results = await self.vector_store.search(
            query=query,
            limit=limit,
            filter_dict=filters
        )
        
        self.logger.info(
            "Product search completed",
            query=query,
            results=len(results)
        )
        
        return results
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get vector store statistics.
        
        Returns:
            Statistics dict
        """
        if not self.vector_store.collection:
            await self.initialize()
        
        count = self.vector_store.collection.count()
        
        # Get sample to check metadata
        sample = None
        if count > 0:
            sample_result = self.vector_store.collection.peek(limit=1)
            if sample_result and sample_result.get("metadatas"):
                sample = sample_result["metadatas"][0]
        
        return {
            "total_products": count,
            "collection_name": "products",
            "sample_metadata": sample,
            "status": "operational" if count > 0 else "empty"
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on vector store.
        
        Returns:
            Health status dict
        """
        try:
            if not self.vector_store.collection:
                await self.initialize()
            
            count = self.vector_store.collection.count()
            
            # Try a simple search
            if count > 0:
                test_results = await self.vector_store.search(
                    query="test",
                    limit=1
                )
                search_working = len(test_results) > 0
            else:
                search_working = None
            
            return {
                "status": "healthy",
                "collection_exists": True,
                "product_count": count,
                "search_working": search_working
            }
        
        except Exception as e:
            self.logger.error("Vector store health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Global singleton instance
_vector_store_service_instance = None


def get_vector_store_service() -> VectorStoreService:
    """Get or create the global VectorStoreService instance.
    
    Returns:
        VectorStoreService instance
    """
    global _vector_store_service_instance
    
    if _vector_store_service_instance is None:
        _vector_store_service_instance = VectorStoreService()
    
    return _vector_store_service_instance
