"""Vector database for semantic search."""
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any
import structlog

from config.settings import settings

logger = structlog.get_logger()


class VectorStore:
    """Vector database wrapper for product embeddings."""
    
    def __init__(self):
        """Initialize vector store."""
        self.persist_dir = settings.chroma_persist_dir
        self.client = None
        self.collection = None
        self.logger = logger.bind(component="VectorStore")
    
    async def initialize(self):
        """Initialize ChromaDB client and collection."""
        self.logger.info("Initializing vector store", persist_dir=self.persist_dir)
        
        # Create client
        self.client = chromadb.Client(ChromaSettings(
            persist_directory=self.persist_dir,
            anonymized_telemetry=False,
        ))
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="products",
            metadata={"description": "Product embeddings for semantic search"}
        )
        
        self.logger.info(
            "Vector store initialized",
            collection_count=self.collection.count()
        )
    
    async def add_products(self, products: List[Dict[str, Any]]):
        """Add products to vector store.
        
        Args:
            products: List of product dictionaries
        """
        self.logger.info("Adding products to vector store", count=len(products))
        
        if not self.collection:
            await self.initialize()
        
        # Prepare documents
        documents = []
        metadatas = []
        ids = []
        
        for product in products:
            # Create searchable text
            doc_text = self._create_document_text(product)
            documents.append(doc_text)
            
            # Metadata
            metadatas.append({
                "product_code": product.get("product_code", ""),
                "brand": product.get("brand", ""),
                "category": product.get("category", ""),
            })
            
            # ID
            ids.append(product.get("product_code", f"prod_{len(ids)}"))
        
        # Add to collection in batches
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i+batch_size]
            batch_meta = metadatas[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]
            
            self.collection.add(
                documents=batch_docs,
                metadatas=batch_meta,
                ids=batch_ids
            )
        
        self.logger.info("Products added to vector store", total=len(products))
    
    async def search(
        self,
        query: str,
        limit: int = 10,
        filter_dict: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Search for products using semantic search.
        
        Args:
            query: Search query
            limit: Maximum number of results
            filter_dict: Optional metadata filters
            
        Returns:
            List of search results
        """
        if not self.collection:
            await self.initialize()
        
        results = self.collection.query(
            query_texts=[query],
            n_results=limit,
            where=filter_dict if filter_dict else None
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                "product_code": results['metadatas'][0][i]['product_code'],
                "brand": results['metadatas'][0][i]['brand'],
                "category": results['metadatas'][0][i]['category'],
                "document": results['documents'][0][i],
                "distance": results['distances'][0][i] if 'distances' in results else None,
            })
        
        return formatted_results
    
    def _create_document_text(self, product: Dict[str, Any]) -> str:
        """Create searchable text from product.
        
        Args:
            product: Product dictionary
            
        Returns:
            Searchable text
        """
        parts = [
            f"Brand: {product.get('brand', '')}",
            f"Category: {product.get('category', '')}",
            f"Product: {product.get('product_name', '')}",
            f"Code: {product.get('product_code', '')}",
        ]
        
        # Add specifications
        specs = product.get('specifications', {})
        if specs:
            spec_text = " ".join([f"{k}: {v}" for k, v in specs.items() if v])
            parts.append(spec_text)
        
        # Add standards and certifications
        if product.get('standard'):
            parts.append(f"Standard: {product['standard']}")
        if product.get('certifications'):
            parts.append(f"Certifications: {product['certifications']}")
        
        return " | ".join(parts)
