"""
Relevance Filter - Filters RFP opportunities based on relevance criteria.
"""
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
import structlog

from embeddings import ProductEmbedder, VectorStore

logger = structlog.get_logger()


@dataclass
class FilterCriteria:
    """Criteria for filtering RFP opportunities."""
    # Keywords
    required_keywords: List[str] = None
    preferred_keywords: List[str] = None
    exclude_keywords: List[str] = None
    
    # Categories
    target_categories: List[str] = None
    exclude_categories: List[str] = None
    
    # Value thresholds
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    
    # Geographic
    target_locations: List[str] = None
    exclude_locations: List[str] = None
    
    # Semantic similarity
    use_semantic_matching: bool = True
    min_semantic_score: float = 0.5
    reference_descriptions: List[str] = None
    
    def __post_init__(self):
        if self.required_keywords is None:
            self.required_keywords = []
        if self.preferred_keywords is None:
            self.preferred_keywords = []
        if self.exclude_keywords is None:
            self.exclude_keywords = []
        if self.target_categories is None:
            self.target_categories = []
        if self.exclude_categories is None:
            self.exclude_categories = []
        if self.target_locations is None:
            self.target_locations = []
        if self.exclude_locations is None:
            self.exclude_locations = []
        if self.reference_descriptions is None:
            self.reference_descriptions = []


class RelevanceFilter:
    """Filter RFP opportunities based on relevance."""
    
    def __init__(
        self,
        min_score: float = 0.6,
        embedder: Optional[ProductEmbedder] = None
    ):
        """Initialize relevance filter.
        
        Args:
            min_score: Minimum relevance score (0-1)
            embedder: ProductEmbedder for semantic matching
        """
        self.min_score = min_score
        self.embedder = embedder
        self.logger = logger.bind(component="RelevanceFilter")
        
        # Default criteria if none provided
        self.default_criteria = FilterCriteria(
            required_keywords=['electrical', 'electronics', 'lighting', 'cables', 'switchgear'],
            exclude_keywords=['medical', 'pharmaceutical', 'food', 'agriculture'],
            target_categories=['Electrical', 'Electronics', 'Lighting', 'Cables'],
            min_value=10000.0
        )
        
        self.logger.info("Relevance filter initialized", min_score=min_score)
    
    def filter_opportunity(
        self,
        title: str,
        description: str,
        categories: List[str] = None,
        estimated_value: Optional[float] = None,
        location: str = "",
        criteria: Optional[FilterCriteria] = None
    ) -> Tuple[bool, float, List[str]]:
        """Filter opportunity based on relevance.
        
        Args:
            title: RFP title
            description: RFP description
            categories: RFP categories
            estimated_value: Estimated contract value
            location: Location
            criteria: Filter criteria (uses default if None)
            
        Returns:
            Tuple of (is_relevant, score, reasons)
        """
        criteria = criteria or self.default_criteria
        categories = categories or []
        
        score = 0.0
        reasons = []
        max_score = 0.0
        
        # 1. Required keywords check (blocking)
        if criteria.required_keywords:
            max_score += 20
            has_required, required_score, required_reasons = self._check_required_keywords(
                title, description, criteria.required_keywords
            )
            if not has_required:
                return False, 0.0, ["Missing required keywords"]
            score += required_score
            reasons.extend(required_reasons)
        
        # 2. Exclude keywords check (blocking)
        if criteria.exclude_keywords:
            has_excluded, exclude_reasons = self._check_exclude_keywords(
                title, description, criteria.exclude_keywords
            )
            if has_excluded:
                return False, 0.0, exclude_reasons
        
        # 3. Preferred keywords (additive)
        if criteria.preferred_keywords:
            max_score += 15
            pref_score, pref_reasons = self._check_preferred_keywords(
                title, description, criteria.preferred_keywords
            )
            score += pref_score
            reasons.extend(pref_reasons)
        
        # 4. Category matching
        if criteria.target_categories:
            max_score += 20
            cat_score, cat_reasons = self._check_categories(
                categories, criteria.target_categories, criteria.exclude_categories
            )
            if cat_score == 0 and categories:  # Has categories but none match
                score += 0
            else:
                score += cat_score
                reasons.extend(cat_reasons)
        
        # 5. Value threshold
        if estimated_value is not None:
            max_score += 15
            value_score, value_reasons = self._check_value(
                estimated_value, criteria.min_value, criteria.max_value
            )
            score += value_score
            reasons.extend(value_reasons)
        
        # 6. Location matching
        if location and criteria.target_locations:
            max_score += 10
            loc_score, loc_reasons = self._check_location(
                location, criteria.target_locations, criteria.exclude_locations
            )
            score += loc_score
            reasons.extend(loc_reasons)
        
        # 7. Semantic similarity
        if criteria.use_semantic_matching and criteria.reference_descriptions and self.embedder:
            max_score += 20
            sem_score, sem_reasons = self._check_semantic_similarity(
                title, description, criteria.reference_descriptions, criteria.min_semantic_score
            )
            score += sem_score
            reasons.extend(sem_reasons)
        
        # Normalize score to 0-1
        if max_score > 0:
            normalized_score = score / max_score
        else:
            normalized_score = 0.5  # Default if no criteria
        
        is_relevant = normalized_score >= self.min_score
        
        self.logger.debug(
            "Opportunity filtered",
            title=title[:50],
            score=normalized_score,
            is_relevant=is_relevant,
            reasons=len(reasons)
        )
        
        return is_relevant, normalized_score, reasons
    
    def _check_required_keywords(
        self,
        title: str,
        description: str,
        keywords: List[str]
    ) -> Tuple[bool, float, List[str]]:
        """Check for required keywords."""
        text = f"{title} {description}".lower()
        found_keywords = []
        
        for keyword in keywords:
            if keyword.lower() in text:
                found_keywords.append(keyword)
        
        if not found_keywords:
            return False, 0.0, []
        
        # Score based on percentage of required keywords found
        score = (len(found_keywords) / len(keywords)) * 20
        reasons = [f"Matches required keywords: {', '.join(found_keywords)}"]
        
        return True, score, reasons
    
    def _check_exclude_keywords(
        self,
        title: str,
        description: str,
        keywords: List[str]
    ) -> Tuple[bool, List[str]]:
        """Check for excluded keywords."""
        text = f"{title} {description}".lower()
        found_excluded = []
        
        for keyword in keywords:
            if keyword.lower() in text:
                found_excluded.append(keyword)
        
        if found_excluded:
            return True, [f"Contains excluded keywords: {', '.join(found_excluded)}"]
        
        return False, []
    
    def _check_preferred_keywords(
        self,
        title: str,
        description: str,
        keywords: List[str]
    ) -> Tuple[float, List[str]]:
        """Check for preferred keywords."""
        text = f"{title} {description}".lower()
        found_keywords = []
        
        for keyword in keywords:
            if keyword.lower() in text:
                found_keywords.append(keyword)
        
        if not found_keywords:
            return 0.0, []
        
        # Score based on percentage of preferred keywords found
        score = (len(found_keywords) / len(keywords)) * 15
        reasons = [f"Matches preferred keywords: {', '.join(found_keywords)}"]
        
        return score, reasons
    
    def _check_categories(
        self,
        categories: List[str],
        target_categories: List[str],
        exclude_categories: List[str]
    ) -> Tuple[float, List[str]]:
        """Check category matching."""
        if not categories:
            return 10.0, ["No category information available"]
        
        categories_lower = [c.lower() for c in categories]
        
        # Check excluded categories
        for exclude_cat in exclude_categories:
            if exclude_cat.lower() in categories_lower:
                return 0.0, [f"Belongs to excluded category: {exclude_cat}"]
        
        # Check target categories
        matching_categories = []
        for target_cat in target_categories:
            if target_cat.lower() in categories_lower:
                matching_categories.append(target_cat)
        
        if matching_categories:
            score = (len(matching_categories) / len(target_categories)) * 20
            reasons = [f"Matches target categories: {', '.join(matching_categories)}"]
            return score, reasons
        
        return 0.0, []
    
    def _check_value(
        self,
        value: float,
        min_value: Optional[float],
        max_value: Optional[float]
    ) -> Tuple[float, List[str]]:
        """Check value thresholds."""
        reasons = []
        
        if min_value is not None and value < min_value:
            return 0.0, [f"Value INR {value:,.0f} below minimum threshold INR {min_value:,.0f}"]
        
        if max_value is not None and value > max_value:
            return 0.0, [f"Value INR {value:,.0f} exceeds maximum threshold INR {max_value:,.0f}"]
        
        # Value is within range
        score = 15.0
        if min_value:
            reasons.append(f"Value INR {value:,.0f} meets minimum threshold")
        else:
            reasons.append(f"Estimated value: INR {value:,.0f}")
        
        return score, reasons
    
    def _check_location(
        self,
        location: str,
        target_locations: List[str],
        exclude_locations: List[str]
    ) -> Tuple[float, List[str]]:
        """Check location matching."""
        location_lower = location.lower()
        
        # Check excluded locations
        for exclude_loc in exclude_locations:
            if exclude_loc.lower() in location_lower:
                return 0.0, [f"Location excluded: {location}"]
        
        # Check target locations
        for target_loc in target_locations:
            if target_loc.lower() in location_lower:
                return 10.0, [f"Matches target location: {target_loc}"]
        
        return 5.0, ["Location not in target areas"]
    
    def _check_semantic_similarity(
        self,
        title: str,
        description: str,
        reference_descriptions: List[str],
        min_score: float
    ) -> Tuple[float, List[str]]:
        """Check semantic similarity using embeddings."""
        if not self.embedder:
            return 0.0, []
        
        try:
            query_text = f"{title} {description}"
            
            # Create temporary documents from reference descriptions
            from embeddings.vector_store import SearchResult
            
            # Calculate similarity (simplified - in production would use vector store)
            # For now, use keyword overlap as proxy
            query_words = set(query_text.lower().split())
            max_similarity = 0.0
            
            for ref_desc in reference_descriptions:
                ref_words = set(ref_desc.lower().split())
                overlap = len(query_words & ref_words)
                total = len(query_words | ref_words)
                similarity = overlap / total if total > 0 else 0.0
                max_similarity = max(max_similarity, similarity)
            
            if max_similarity >= min_score:
                score = 20.0 * (max_similarity / 1.0)
                return score, [f"High semantic similarity: {max_similarity:.2f}"]
            else:
                return 0.0, [f"Low semantic similarity: {max_similarity:.2f}"]
                
        except Exception as e:
            self.logger.error("Semantic similarity check failed", error=str(e))
            return 0.0, []
