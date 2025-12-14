"""Product matching logic for RFP requirements."""
from typing import Dict, Any, List
import structlog

from data.vector_store import VectorStore

logger = structlog.get_logger()


class ProductMatcher:
    """Match products to RFP requirements."""
    
    def __init__(self):
        """Initialize product matcher."""
        self.vector_store = VectorStore()
        self.logger = logger.bind(component="ProductMatcher")
    
    async def find_matches(
        self,
        requirement: Dict[str, Any],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Find products matching a requirement.
        
        Args:
            requirement: RFP requirement dict
            top_k: Number of matches to return
            
        Returns:
            List of matching products with similarity scores
        """
        # Build search query from requirement
        query = self._build_search_query(requirement)
        
        self.logger.info(
            "Searching for product matches",
            requirement=requirement.get("item_name"),
            query=query
        )
        
        # Search vector store
        results = await self.vector_store.search(
            query=query,
            limit=top_k
        )
        
        # Enhance results with similarity scores
        matches = []
        for result in results:
            match = {
                **result,
                "similarity_score": self._calculate_similarity_score(
                    requirement,
                    result
                ),
            }
            matches.append(match)
        
        # Sort by similarity score
        matches.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return matches
    
    def _build_search_query(self, requirement: Dict[str, Any]) -> str:
        """Build search query from requirement.
        
        Args:
            requirement: Requirement dictionary
            
        Returns:
            Search query string
        """
        parts = []
        
        # Add item name/description
        if "item_name" in requirement:
            parts.append(requirement["item_name"])
        if "description" in requirement:
            parts.append(requirement["description"])
        
        # Add technical specs
        specs = requirement.get("specifications", {})
        for key, value in specs.items():
            if value:
                parts.append(f"{key}: {value}")
        
        # Add standards
        if "standard" in requirement:
            parts.append(f"Standard: {requirement['standard']}")
        
        return " ".join(parts)
    
    def _calculate_similarity_score(
        self,
        requirement: Dict[str, Any],
        result: Dict[str, Any]
    ) -> float:
        """Calculate detailed similarity score.
        
        Args:
            requirement: RFP requirement
            result: Search result
            
        Returns:
            Similarity score (0-100)
        """
        # Start with vector similarity (distance)
        # Lower distance = higher similarity
        # Convert to 0-100 scale
        distance = result.get("distance", 1.0)
        base_score = max(0, (1.0 - distance) * 100)
        
        # TODO: Add more sophisticated scoring based on:
        # - Exact specification matches
        # - Standard compliance
        # - Certification matches
        # - Price competitiveness
        
        return min(100, base_score)
