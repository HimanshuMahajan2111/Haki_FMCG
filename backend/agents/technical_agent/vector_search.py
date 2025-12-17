"""
Vector Search Integration for Product Matching.
"""
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import structlog
from sentence_transformers import SentenceTransformer
import faiss
import json
from pathlib import Path

logger = structlog.get_logger()


class VectorSearchEngine:
    """Vector-based semantic search for product catalog."""
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        index_path: Optional[str] = None
    ):
        """Initialize vector search engine.
        
        Args:
            model_name: Sentence transformer model name
            index_path: Path to saved FAISS index
        """
        self.logger = logger.bind(component="VectorSearchEngine")
        
        # Load embedding model
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        
        # Initialize FAISS index
        self.index = None
        self.product_metadata = []
        
        if index_path and Path(index_path).exists():
            self.load_index(index_path)
        else:
            self.index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product for cosine similarity
        
        self.logger.info(
            "Vector search engine initialized",
            model=model_name,
            embedding_dim=self.embedding_dim
        )
    
    def index_products(self, products: List[Dict[str, Any]]):
        """Index products for vector search.
        
        Args:
            products: List of product dictionaries
        """
        self.logger.info(f"Indexing {len(products)} products")
        
        # Create text representations
        product_texts = []
        self.product_metadata = []
        
        for product in products:
            text = self._create_product_text(product)
            product_texts.append(text)
            self.product_metadata.append(product)
        
        # Generate embeddings
        embeddings = self.model.encode(
            product_texts,
            normalize_embeddings=True,  # For cosine similarity
            show_progress_bar=True
        )
        
        # Add to FAISS index
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        self.index.add(embeddings.astype('float32'))
        
        self.logger.info(f"Indexed {self.index.ntotal} products")
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Search for products using semantic similarity.
        
        Args:
            query: Search query (requirement description)
            top_k: Number of results to return
            filters: Optional filters (category, manufacturer, etc.)
            
        Returns:
            List of (product, similarity_score) tuples
        """
        if self.index is None or self.index.ntotal == 0:
            self.logger.warning("Index is empty")
            return []
        
        # Generate query embedding
        query_embedding = self.model.encode(
            [query],
            normalize_embeddings=True
        ).astype('float32')
        
        # Search index
        search_k = min(top_k * 3, self.index.ntotal)  # Over-fetch for filtering
        distances, indices = self.index.search(query_embedding, search_k)
        
        # Collect results
        results = []
        for idx, score in zip(indices[0], distances[0]):
            if idx < len(self.product_metadata):
                product = self.product_metadata[idx]
                
                # Apply filters
                if filters and not self._matches_filters(product, filters):
                    continue
                
                results.append((product, float(score)))
                
                if len(results) >= top_k:
                    break
        
        self.logger.info(f"Vector search found {len(results)} results", query=query[:50])
        return results
    
    def _create_product_text(self, product: Dict[str, Any]) -> str:
        """Create searchable text representation of product."""
        parts = [
            product.get('product_name', ''),
            product.get('manufacturer', ''),
            product.get('category', ''),
            product.get('model_number', ''),
        ]
        
        # Add specifications
        specs = product.get('specifications', {})
        if specs:
            spec_text = ' '.join(f"{k}:{v}" for k, v in specs.items())
            parts.append(spec_text)
        
        # Add certifications
        certs = product.get('certifications', [])
        if certs:
            parts.append(' '.join(certs))
        
        # Add standards
        standards = product.get('standards_compliance', [])
        if standards:
            parts.append(' '.join(standards))
        
        return ' '.join(str(p) for p in parts if p)
    
    def _matches_filters(self, product: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if product matches filters."""
        for key, value in filters.items():
            if key == 'category':
                if product.get('category', '').lower() != value.lower():
                    return False
            elif key == 'manufacturer':
                if product.get('manufacturer', '').lower() != value.lower():
                    return False
            elif key == 'max_price':
                if product.get('unit_price', float('inf')) > value:
                    return False
            elif key == 'min_stock':
                if product.get('available_stock', 0) < value:
                    return False
        
        return True
    
    def save_index(self, index_path: str):
        """Save FAISS index and metadata.
        
        Args:
            index_path: Path to save index
        """
        path = Path(index_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(path / "index.faiss"))
        
        # Save metadata
        with open(path / "metadata.json", 'w') as f:
            json.dump(self.product_metadata, f)
        
        self.logger.info(f"Index saved to {index_path}")
    
    def load_index(self, index_path: str):
        """Load FAISS index and metadata.
        
        Args:
            index_path: Path to load index from
        """
        path = Path(index_path)
        
        # Load FAISS index
        self.index = faiss.read_index(str(path / "index.faiss"))
        
        # Load metadata
        with open(path / "metadata.json", 'r') as f:
            self.product_metadata = json.load(f)
        
        self.logger.info(f"Index loaded from {index_path}", products=len(self.product_metadata))


class HybridMatcher:
    """Hybrid matcher combining vector search with rule-based matching."""
    
    def __init__(self, vector_engine: VectorSearchEngine):
        """Initialize hybrid matcher.
        
        Args:
            vector_engine: Vector search engine
        """
        self.logger = logger.bind(component="HybridMatcher")
        self.vector_engine = vector_engine
    
    def match(
        self,
        requirement: Dict[str, Any],
        catalog: List[Dict[str, Any]],
        top_k: int = 10,
        alpha: float = 0.7
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Hybrid matching with weighted combination.
        
        Args:
            requirement: Product requirement
            catalog: Product catalog
            top_k: Number of results
            alpha: Weight for vector search (1-alpha for rule-based)
            
        Returns:
            List of (product, combined_score) tuples
        """
        self.logger.info("Performing hybrid matching")
        
        # 1. Vector search
        query = self._create_requirement_query(requirement)
        vector_results = self.vector_engine.search(query, top_k=top_k*2)
        
        # 2. Rule-based matching
        rule_results = self._rule_based_match(requirement, catalog)
        
        # 3. Combine scores
        combined = self._combine_scores(vector_results, rule_results, alpha)
        
        # Sort and return top K
        combined.sort(key=lambda x: x[1], reverse=True)
        
        self.logger.info(f"Hybrid matching found {len(combined[:top_k])} results")
        return combined[:top_k]
    
    def _create_requirement_query(self, requirement: Dict[str, Any]) -> str:
        """Create search query from requirement."""
        parts = [
            requirement.get('item_name', ''),
            requirement.get('description', ''),
        ]
        
        # Add specifications
        specs = requirement.get('specifications', {})
        if specs:
            spec_text = ' '.join(f"{k}:{v}" for k, v in specs.items())
            parts.append(spec_text)
        
        # Add standards
        standards = requirement.get('required_standards', [])
        if standards:
            parts.append(' '.join(standards))
        
        return ' '.join(str(p) for p in parts if p)
    
    def _rule_based_match(
        self,
        requirement: Dict[str, Any],
        catalog: List[Dict[str, Any]]
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Rule-based matching for exact criteria."""
        results = []
        
        for product in catalog:
            score = 0.0
            count = 0
            
            # Category match
            req_category = requirement.get('item_name', '').lower()
            prod_category = product.get('category', '').lower()
            if req_category in prod_category or prod_category in req_category:
                score += 1.0
                count += 1
            else:
                count += 1
            
            # Specification match
            req_specs = requirement.get('specifications', {})
            prod_specs = product.get('specifications', {})
            if req_specs:
                matched_specs = sum(
                    1 for k, v in req_specs.items()
                    if k in prod_specs and str(v).lower() in str(prod_specs[k]).lower()
                )
                score += matched_specs / len(req_specs)
                count += 1
            
            # Standard match
            req_standards = set(s.upper() for s in requirement.get('required_standards', []))
            prod_standards = set(s.upper() for s in product.get('standards_compliance', []))
            if req_standards:
                matched_stds = len(req_standards & prod_standards)
                score += matched_stds / len(req_standards)
                count += 1
            
            # Average score
            final_score = score / count if count > 0 else 0.0
            results.append((product, final_score))
        
        return results
    
    def _combine_scores(
        self,
        vector_results: List[Tuple[Dict[str, Any], float]],
        rule_results: List[Tuple[Dict[str, Any], float]],
        alpha: float
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Combine vector and rule-based scores."""
        # Create lookup dictionaries
        vector_scores = {
            product['product_id']: score
            for product, score in vector_results
        }
        rule_scores = {
            product['product_id']: score
            for product, score in rule_results
        }
        
        # Combine
        all_product_ids = set(vector_scores.keys()) | set(rule_scores.keys())
        combined = []
        
        for pid in all_product_ids:
            v_score = vector_scores.get(pid, 0.0)
            r_score = rule_scores.get(pid, 0.0)
            
            # Weighted combination
            combined_score = alpha * v_score + (1 - alpha) * r_score
            
            # Find product
            product = None
            for p, _ in vector_results:
                if p['product_id'] == pid:
                    product = p
                    break
            if not product:
                for p, _ in rule_results:
                    if p['product_id'] == pid:
                        product = p
                        break
            
            if product:
                combined.append((product, combined_score))
        
        return combined
