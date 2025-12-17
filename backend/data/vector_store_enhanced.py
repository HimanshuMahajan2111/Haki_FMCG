"""Enhanced ChromaDB configuration with production features."""
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional
import structlog
from pathlib import Path
import json
from datetime import datetime

from config.settings import settings

logger = structlog.get_logger()


class EnhancedVectorStore:
    """Production-ready vector database with advanced features."""
    
    def __init__(self):
        """Initialize enhanced vector store."""
        self.persist_dir = Path(settings.chroma_persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        self.client = None
        self.product_collection = None
        self.rfp_collection = None
        self.embedding_function = None
        
        self.logger = logger.bind(component="EnhancedVectorStore")
    
    async def initialize(self, use_openai: bool = False):
        """Initialize ChromaDB with production settings.
        
        Args:
            use_openai: If True, use OpenAI embeddings instead of default
        """
        self.logger.info(
            "Initializing enhanced vector store",
            persist_dir=str(self.persist_dir),
            use_openai=use_openai
        )
        
        # Configure embedding function
        if use_openai and settings.openai_api_key:
            self.logger.info("Using OpenAI embeddings", model=settings.embedding_model)
            self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                api_key=settings.openai_api_key,
                model_name=settings.embedding_model
            )
        else:
            self.logger.info("Using default sentence transformer embeddings")
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        
        # Create persistent client with production settings
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=False,  # Prevent accidental data loss
                is_persistent=True,
            )
        )
        
        # Initialize collections
        await self._initialize_collections()
        
        self.logger.info("Enhanced vector store initialized successfully")
    
    async def _initialize_collections(self):
        """Initialize all collections with proper metadata."""
        
        # Product collection with rich metadata
        self.product_collection = self.client.get_or_create_collection(
            name="products",
            metadata={
                "description": "Product catalog for semantic search",
                "created_at": datetime.utcnow().isoformat(),
                "schema_version": "2.0",
                "indexed_fields": "brand,category,sub_category,product_code"  # ChromaDB only accepts scalar metadata
            },
            embedding_function=self.embedding_function
        )
        
        # RFP collection for requirement matching
        self.rfp_collection = self.client.get_or_create_collection(
            name="rfp_requirements",
            metadata={
                "description": "RFP requirements for semantic matching",
                "created_at": datetime.utcnow().isoformat(),
                "schema_version": "2.0"
            },
            embedding_function=self.embedding_function
        )
        
        self.logger.info(
            "Collections initialized",
            product_count=self.product_collection.count(),
            rfp_count=self.rfp_collection.count()
        )
    
    async def add_products(
        self,
        products: List[Dict[str, Any]],
        batch_size: int = 100,
        update_existing: bool = False
    ):
        """Add products with enhanced indexing.
        
        Args:
            products: List of product dictionaries
            batch_size: Number of products per batch
            update_existing: If True, update existing products
        """
        self.logger.info("Adding products", count=len(products), update_existing=update_existing)
        
        if not self.product_collection:
            await self.initialize()
        
        documents = []
        metadatas = []
        ids = []
        
        for product in products:
            product_code = product.get("product_code", "")
            if not product_code:
                continue
            
            # Check if exists
            if not update_existing:
                try:
                    existing = self.product_collection.get(ids=[product_code])
                    if existing['ids']:
                        continue  # Skip existing
                except:
                    pass
            
            # Create rich searchable document
            doc_text = self._create_product_document(product)
            documents.append(doc_text)
            
            # Enhanced metadata with all searchable fields
            metadata = {
                "product_code": product_code,
                "brand": product.get("brand", ""),
                "category": product.get("category", ""),
                "sub_category": product.get("sub_category", ""),
                "product_name": product.get("product_name", ""),
                "standard": product.get("standard", ""),
                "hsn_code": product.get("hsn_code", ""),
                "price_range": self._get_price_range(product),
                "has_certifications": bool(product.get("certifications")),
                "is_active": product.get("is_active", True),
            }
            metadatas.append(metadata)
            ids.append(product_code)
        
        # Add in batches
        added_count = 0
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i+batch_size]
            batch_meta = metadatas[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]
            
            try:
                if update_existing:
                    self.product_collection.upsert(
                        documents=batch_docs,
                        metadatas=batch_meta,
                        ids=batch_ids
                    )
                else:
                    self.product_collection.add(
                        documents=batch_docs,
                        metadatas=batch_meta,
                        ids=batch_ids
                    )
                added_count += len(batch_ids)
            except Exception as e:
                self.logger.error("Batch add failed", batch=i, error=str(e))
        
        self.logger.info("Products added", total=added_count)
        return added_count
    
    async def search_products(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Advanced product search with filtering and scoring.
        
        Args:
            query: Search query
            limit: Maximum results
            filters: Metadata filters (brand, category, price_range, etc.)
            min_similarity: Minimum similarity threshold (0-1)
            
        Returns:
            List of search results with scores
        """
        if not self.product_collection:
            await self.initialize()
        
        # Build where clause
        where_clause = None
        if filters:
            where_clause = self._build_where_clause(filters)
        
        try:
            results = self.product_collection.query(
                query_texts=[query],
                n_results=limit * 2,  # Get more, then filter
                where=where_clause,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format and filter results
            formatted_results = []
            for i in range(len(results['ids'][0])):
                distance = results['distances'][0][i] if 'distances' in results else 0
                similarity = 1 - distance  # Convert distance to similarity
                
                if similarity < min_similarity:
                    continue
                
                formatted_results.append({
                    "product_code": results['metadatas'][0][i]['product_code'],
                    "brand": results['metadatas'][0][i]['brand'],
                    "category": results['metadatas'][0][i]['category'],
                    "product_name": results['metadatas'][0][i].get('product_name', ''),
                    "document": results['documents'][0][i],
                    "similarity_score": similarity,
                    "distance": distance,
                    "metadata": results['metadatas'][0][i]
                })
            
            # Sort by similarity and limit
            formatted_results.sort(key=lambda x: x['similarity_score'], reverse=True)
            formatted_results = formatted_results[:limit]
            
            self.logger.info("Search completed", query=query, results=len(formatted_results))
            return formatted_results
            
        except Exception as e:
            self.logger.error("Search failed", query=query, error=str(e))
            return []
    
    async def add_rfp_requirements(
        self,
        rfp_id: int,
        requirements: List[Dict[str, Any]]
    ):
        """Add RFP requirements for matching.
        
        Args:
            rfp_id: RFP identifier
            requirements: List of requirement items
        """
        if not self.rfp_collection:
            await self.initialize()
        
        documents = []
        metadatas = []
        ids = []
        
        for idx, req in enumerate(requirements):
            doc_text = self._create_requirement_document(req)
            documents.append(doc_text)
            
            metadatas.append({
                "rfp_id": str(rfp_id),
                "item_number": req.get("item_number", ""),
                "category": req.get("category", ""),
                "quantity": req.get("quantity", 0)
            })
            
            ids.append(f"rfp_{rfp_id}_req_{idx}")
        
        self.rfp_collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        self.logger.info("RFP requirements added", rfp_id=rfp_id, count=len(requirements))
    
    async def match_rfp_requirements(
        self,
        rfp_id: int,
        top_k: int = 5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Match RFP requirements to products.
        
        Args:
            rfp_id: RFP identifier
            top_k: Top matches per requirement
            
        Returns:
            Dictionary mapping requirement IDs to product matches
        """
        if not self.rfp_collection or not self.product_collection:
            await self.initialize()
        
        # Get all requirements for this RFP
        rfp_reqs = self.rfp_collection.get(
            where={"rfp_id": str(rfp_id)},
            include=["documents", "metadatas"]
        )
        
        matches = {}
        
        for idx, req_doc in enumerate(rfp_reqs['documents']):
            req_id = rfp_reqs['ids'][idx]
            
            # Search products for this requirement
            product_results = await self.search_products(
                query=req_doc,
                limit=top_k,
                min_similarity=0.5
            )
            
            matches[req_id] = product_results
        
        self.logger.info("RFP matching completed", rfp_id=rfp_id, requirements=len(matches))
        return matches
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        if not self.product_collection:
            await self.initialize()
        
        return {
            "products": {
                "count": self.product_collection.count(),
                "metadata": self.product_collection.metadata
            },
            "rfp_requirements": {
                "count": self.rfp_collection.count(),
                "metadata": self.rfp_collection.metadata
            },
            "persist_directory": str(self.persist_dir),
            "disk_usage_mb": self._get_disk_usage()
        }
    
    async def backup(self, backup_path: Path):
        """Create backup of vector store."""
        import shutil
        
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Copy entire persist directory
        shutil.copytree(
            self.persist_dir,
            backup_path / "chromadb_backup",
            dirs_exist_ok=True
        )
        
        # Save metadata
        stats = await self.get_collection_stats()
        with open(backup_path / "backup_metadata.json", "w") as f:
            json.dump({
                "timestamp": datetime.utcnow().isoformat(),
                "stats": stats
            }, f, indent=2)
        
        self.logger.info("Backup created", path=str(backup_path))
    
    async def reset_collection(self, collection_name: str):
        """Reset a specific collection (USE WITH CAUTION)."""
        self.logger.warning("Resetting collection", name=collection_name)
        
        if collection_name == "products":
            self.client.delete_collection("products")
            await self._initialize_collections()
        elif collection_name == "rfp_requirements":
            self.client.delete_collection("rfp_requirements")
            await self._initialize_collections()
        else:
            raise ValueError(f"Unknown collection: {collection_name}")
    
    def _create_product_document(self, product: Dict[str, Any]) -> str:
        """Create rich searchable document from product."""
        parts = [
            f"Brand: {product.get('brand', '')}",
            f"Category: {product.get('category', '')}",
            f"Product: {product.get('product_name', '')}",
            f"Code: {product.get('product_code', '')}",
        ]
        
        # Add sub-category
        if product.get('sub_category'):
            parts.append(f"Sub-category: {product['sub_category']}")
        
        # Add detailed specifications
        specs = product.get('specifications', {})
        if isinstance(specs, dict):
            for key, value in specs.items():
                if value and str(value).strip():
                    parts.append(f"{key}: {value}")
        
        # Add compliance info
        if product.get('standard'):
            parts.append(f"Standard: {product['standard']}")
        if product.get('certifications'):
            parts.append(f"Certifications: {product['certifications']}")
        if product.get('bis_registration'):
            parts.append(f"BIS: {product['bis_registration']}")
        
        # Add pricing context
        if product.get('mrp'):
            parts.append(f"MRP: {product['mrp']}")
        
        return " | ".join(parts)
    
    def _create_requirement_document(self, requirement: Dict[str, Any]) -> str:
        """Create searchable document from RFP requirement."""
        parts = [
            f"Item: {requirement.get('item_number', '')}",
            f"Description: {requirement.get('description', '')}",
        ]
        
        if requirement.get('quantity'):
            parts.append(f"Quantity: {requirement['quantity']} {requirement.get('unit', '')}")
        
        # Add required specifications
        req_specs = requirement.get('required_specifications', {})
        if isinstance(req_specs, dict):
            for key, value in req_specs.items():
                if value:
                    parts.append(f"{key}: {value}")
        
        # Add standards
        req_standards = requirement.get('required_standards', [])
        if req_standards:
            parts.append(f"Standards: {', '.join(req_standards)}")
        
        return " | ".join(parts)
    
    def _get_price_range(self, product: Dict[str, Any]) -> str:
        """Categorize product by price range."""
        price = product.get('selling_price') or product.get('mrp') or 0
        
        if price < 1000:
            return "budget"
        elif price < 5000:
            return "mid"
        elif price < 20000:
            return "premium"
        else:
            return "luxury"
    
    def _build_where_clause(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Build ChromaDB where clause from filters."""
        where = {}
        
        # Simple equality filters
        for field in ['brand', 'category', 'sub_category', 'standard', 'price_range']:
            if field in filters:
                where[field] = filters[field]
        
        # Boolean filters
        if 'is_active' in filters:
            where['is_active'] = filters['is_active']
        
        # Note: ChromaDB has limited filter syntax
        # For complex queries, filter in application code
        
        return where if where else None
    
    def _get_disk_usage(self) -> float:
        """Get disk usage of persist directory in MB."""
        total_size = 0
        for path in self.persist_dir.rglob('*'):
            if path.is_file():
                total_size += path.stat().st_size
        return round(total_size / (1024 * 1024), 2)
