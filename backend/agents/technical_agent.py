"""Technical Agent - Handles product matching and technical compliance."""
from typing import Any, Dict, List
import structlog

from agents.base_agent import BaseAgent
from data.product_matcher import ProductMatcher
from utils.standards_checker import StandardsChecker

logger = structlog.get_logger()


class TechnicalAgent(BaseAgent):
    """Agent responsible for technical product matching and compliance checking."""
    
    def __init__(self, model: str = None):
        """Initialize Technical Agent."""
        super().__init__(
            agent_name="TechnicalAgent",
            agent_type="technical",
            model=model
        )
        self.product_matcher = ProductMatcher()
        self.standards_checker = StandardsChecker()
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process RFP requirements and match products.
        
        Args:
            input_data: Dictionary containing:
                - rfp_requirements: List of technical requirements
                - rfp_text: Raw RFP text
                - compliance_standards: Required standards
                
        Returns:
            Dictionary containing matched products and compliance info
        """
        self.logger.info("Starting technical processing")
        
        rfp_requirements = input_data.get("rfp_requirements", [])
        compliance_standards = input_data.get("compliance_standards", [])
        
        # Match products for each requirement
        matched_products = []
        
        for requirement in rfp_requirements:
            self.logger.info(
                "Processing requirement",
                requirement=requirement.get("item_name")
            )
            
            # Find matching products
            matches = await self.product_matcher.find_matches(
                requirement=requirement,
                top_k=5
            )
            
            # Check compliance for each match
            compliance_results = []
            for match in matches:
                compliance = await self.standards_checker.check_compliance(
                    product=match,
                    required_standards=compliance_standards
                )
                
                match["compliance"] = compliance
                compliance_results.append(compliance)
            
            # Select best match
            best_match = self._select_best_match(matches, compliance_results)
            
            matched_products.append({
                "requirement": requirement,
                "matched_product": best_match,
                "all_matches": matches[:3],  # Top 3 alternatives
                "match_confidence": best_match.get("similarity_score", 0),
            })
        
        # Calculate overall technical compliance score
        avg_confidence = sum(
            m["match_confidence"] for m in matched_products
        ) / len(matched_products) if matched_products else 0
        
        result = {
            "matched_products": matched_products,
            "total_requirements": len(rfp_requirements),
            "matched_count": len(matched_products),
            "average_confidence": round(avg_confidence, 2),
            "compliance_summary": self._generate_compliance_summary(matched_products),
        }
        
        self.logger.info(
            "Technical processing completed",
            matched_count=len(matched_products),
            avg_confidence=avg_confidence
        )
        
        return result
    
    def _select_best_match(
        self,
        matches: List[Dict[str, Any]],
        compliance_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Select the best product match based on similarity and compliance.
        
        Args:
            matches: List of product matches
            compliance_results: Compliance check results
            
        Returns:
            Best matching product
        """
        if not matches:
            return {}
        
        # Score each match
        scored_matches = []
        for match, compliance in zip(matches, compliance_results):
            similarity_score = match.get("similarity_score", 0)
            compliance_score = compliance.get("overall_score", 0)
            
            # Combined score (70% similarity, 30% compliance)
            combined_score = (similarity_score * 0.7) + (compliance_score * 0.3)
            
            scored_matches.append({
                **match,
                "combined_score": combined_score
            })
        
        # Return highest scoring match
        best = max(scored_matches, key=lambda x: x["combined_score"])
        return best
    
    def _generate_compliance_summary(
        self,
        matched_products: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate summary of compliance across all matched products.
        
        Args:
            matched_products: List of matched products with compliance data
            
        Returns:
            Compliance summary
        """
        total_checks = 0
        passed_checks = 0
        
        for match in matched_products:
            product = match.get("matched_product", {})
            compliance = product.get("compliance", {})
            
            checks = compliance.get("checks", [])
            total_checks += len(checks)
            passed_checks += sum(1 for c in checks if c.get("passed", False))
        
        return {
            "total_compliance_checks": total_checks,
            "passed_checks": passed_checks,
            "compliance_rate": round(
                (passed_checks / total_checks * 100) if total_checks > 0 else 0,
                2
            ),
        }
