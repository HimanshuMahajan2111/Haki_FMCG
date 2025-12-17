"""Core specification matching engine with weighted parameter matching."""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import structlog

from utils.specification_normalizer import SpecificationNormalizer
from utils.unit_converter import UnitConverter
from utils.standard_mapper import StandardMapper
from utils.error_handlers import handle_errors, measure_time
from matching.weighted_scorer import WeightedScorer
from matching.parameter_extractor import ParameterExtractor
from matching.confidence_calculator import ConfidenceCalculator
from matching.score_aggregator import ScoreAggregator

logger = structlog.get_logger()


class ParameterType(Enum):
    """Types of parameters for matching."""
    CRITICAL = "critical"  # Must match exactly
    IMPORTANT = "important"  # High weight in scoring
    OPTIONAL = "optional"  # Low weight in scoring
    DERIVED = "derived"  # Calculated from other parameters


class MatchStatus(Enum):
    """Match status for products."""
    EXACT_MATCH = "exact_match"
    PARTIAL_MATCH = "partial_match"
    NO_MATCH = "no_match"
    NEEDS_REVIEW = "needs_review"


@dataclass
class ParameterMatch:
    """Result of matching a single parameter."""
    parameter_name: str
    rfp_value: Any
    product_value: Any
    normalized_rfp: Any = None
    normalized_product: Any = None
    match_score: float = 0.0
    is_match: bool = False
    parameter_type: ParameterType = ParameterType.OPTIONAL
    tolerance_applied: bool = False
    reason: str = ""
    unit_converted: bool = False


@dataclass
class SpecificationMatchResult:
    """Complete result of specification matching."""
    product_id: Optional[str] = None
    product_name: str = ""
    overall_score: float = 0.0
    technical_score: float = 0.0
    compliance_score: float = 0.0
    match_status: MatchStatus = MatchStatus.NO_MATCH
    
    # Parameter-level matches
    critical_matches: List[ParameterMatch] = field(default_factory=list)
    important_matches: List[ParameterMatch] = field(default_factory=list)
    optional_matches: List[ParameterMatch] = field(default_factory=list)
    
    # Detailed analysis
    matched_parameters: List[str] = field(default_factory=list)
    missing_parameters: List[str] = field(default_factory=list)
    exceeded_parameters: List[str] = field(default_factory=list)
    
    # Compliance
    standard_matches: Dict[str, bool] = field(default_factory=dict)
    compliance_issues: List[str] = field(default_factory=list)
    
    # Additional info
    match_reason: str = ""
    confidence_level: str = "low"
    recommended: bool = False
    
    # Internal fields for detailed analysis (not serialized by default)
    _aggregated_score: Optional[Any] = None
    _confidence_factors: Optional[Any] = None


class SpecificationMatcher:
    """Core specification matching engine with weighted parameter matching."""
    
    def __init__(
        self,
        default_tolerance: float = 0.05,  # 5% tolerance
        enable_unit_conversion: bool = True,
        strict_critical_match: bool = True
    ):
        """Initialize specification matcher.
        
        Args:
            default_tolerance: Default tolerance for numeric comparisons (0.05 = 5%)
            enable_unit_conversion: Whether to convert units before comparison
            strict_critical_match: If True, critical params must match exactly
        """
        self.default_tolerance = default_tolerance
        self.enable_unit_conversion = enable_unit_conversion
        self.strict_critical_match = strict_critical_match
        
        # Initialize utilities
        self.normalizer = SpecificationNormalizer()
        self.unit_converter = UnitConverter()
        self.standard_mapper = StandardMapper()
        self.scorer = WeightedScorer()
        self.extractor = ParameterExtractor()
        self.confidence_calculator = ConfidenceCalculator()
        self.score_aggregator = ScoreAggregator()
        
        self.logger = logger.bind(component="SpecificationMatcher")
        
        # Define critical parameters by category
        self.critical_parameters = {
            'cable': ['voltage_rating', 'current_rating', 'conductor_size', 'core_count'],
            'switchgear': ['rated_voltage', 'rated_current', 'breaking_capacity', 'frequency'],
            'motor': ['power_rating', 'voltage', 'frequency', 'rpm', 'phase'],
            'fan': ['sweep_size', 'power_consumption', 'voltage'],
            'lighting': ['wattage', 'voltage', 'lumens', 'color_temperature'],
            'default': ['voltage', 'current', 'power', 'frequency']
        }
        
        # Define parameter weights by type
        self.parameter_weights = {
            ParameterType.CRITICAL: 1.0,
            ParameterType.IMPORTANT: 0.7,
            ParameterType.OPTIONAL: 0.3,
            ParameterType.DERIVED: 0.5
        }
    
    @measure_time(log_result=True)
    def match_specifications(
        self,
        rfp_requirements: Dict[str, Any],
        product_specs: Dict[str, Any],
        category: str = "default",
        custom_weights: Optional[Dict[str, float]] = None
    ) -> SpecificationMatchResult:
        """Match RFP requirements against product specifications.
        
        Args:
            rfp_requirements: Dictionary of RFP technical requirements
            product_specs: Dictionary of product specifications
            category: Product category for specialized matching
            custom_weights: Optional custom parameter weights
            
        Returns:
            SpecificationMatchResult with detailed matching information
        """
        self.logger.info(
            "Starting specification matching",
            category=category,
            rfp_params=len(rfp_requirements),
            product_params=len(product_specs)
        )
        
        result = SpecificationMatchResult(
            product_id=product_specs.get('product_id'),
            product_name=product_specs.get('product_name', 'Unknown')
        )
        
        # Extract and normalize parameters
        rfp_params = self.extractor.extract_parameters(rfp_requirements, category)
        product_params = self.extractor.extract_parameters(product_specs, category)
        
        # Identify critical parameters for this category
        critical_param_names = self.critical_parameters.get(category, self.critical_parameters['default'])
        
        # Match each RFP parameter
        critical_fails = 0
        for param_name, rfp_value in rfp_params.items():
            if param_name not in product_params:
                result.missing_parameters.append(param_name)
                if param_name in critical_param_names:
                    critical_fails += 1
                continue
            
            product_value = product_params[param_name]
            
            # Determine parameter type
            param_type = self._classify_parameter(param_name, critical_param_names)
            
            # Match the parameter
            param_match = self._match_parameter(
                param_name,
                rfp_value,
                product_value,
                param_type,
                category
            )
            
            # Store match result by type
            if param_type == ParameterType.CRITICAL:
                result.critical_matches.append(param_match)
                if not param_match.is_match and self.strict_critical_match:
                    critical_fails += 1
            elif param_type == ParameterType.IMPORTANT:
                result.important_matches.append(param_match)
            else:
                result.optional_matches.append(param_match)
            
            if param_match.is_match:
                result.matched_parameters.append(param_name)
        
        # Check for exceeded parameters (product has more than required)
        for param_name, product_value in product_params.items():
            if param_name not in rfp_params:
                result.exceeded_parameters.append(param_name)
        
        # Match standards and compliance
        self._match_standards(rfp_requirements, product_specs, result)
        
        # Calculate scores
        result.technical_score = self._calculate_technical_score(result, custom_weights)
        result.compliance_score = self._calculate_compliance_score(result)
        
        # Use score aggregator for better scoring
        aggregated = self.score_aggregator.aggregate_match_scores(
            result.technical_score,
            result.compliance_score
        )
        result.overall_score = aggregated.overall_score
        
        # Calculate detailed confidence
        confidence_score, confidence_factors = self.confidence_calculator.calculate_confidence(
            result,
            rfp_requirements,
            product_specs
        )
        
        # Determine match status
        result.match_status = self._determine_match_status(result, critical_fails)
        result.confidence_level = self._calculate_confidence_level(result, confidence_score)
        result.recommended = self._is_recommended(result)
        result.match_reason = self._generate_match_reason(result)
        
        # Store aggregated scores and confidence for later explanation
        result._aggregated_score = aggregated
        result._confidence_factors = confidence_factors
        
        self.logger.info(
            "Specification matching completed",
            overall_score=round(result.overall_score, 2),
            match_status=result.match_status.value,
            critical_matches=len(result.critical_matches),
            matched=len(result.matched_parameters),
            missing=len(result.missing_parameters)
        )
        
        return result
    
    def _match_parameter(
        self,
        param_name: str,
        rfp_value: Any,
        product_value: Any,
        param_type: ParameterType,
        category: str
    ) -> ParameterMatch:
        """Match a single parameter with normalization and tolerance.
        
        Args:
            param_name: Name of the parameter
            rfp_value: Required value from RFP
            product_value: Product's value
            param_type: Type of parameter (critical/important/optional)
            category: Product category
            
        Returns:
            ParameterMatch with detailed matching results
        """
        match = ParameterMatch(
            parameter_name=param_name,
            rfp_value=rfp_value,
            product_value=product_value,
            parameter_type=param_type
        )
        
        # Normalize both values
        match.normalized_rfp = self._normalize_value(param_name, rfp_value, category)
        match.normalized_product = self._normalize_value(param_name, product_value, category)
        
        # Handle unit conversion if enabled
        if self.enable_unit_conversion:
            match = self._apply_unit_conversion(match, param_name)
        
        # Compare values based on type
        if isinstance(match.normalized_rfp, (int, float)) and isinstance(match.normalized_product, (int, float)):
            match = self._match_numeric_parameter(match, param_type)
        elif isinstance(match.normalized_rfp, str) and isinstance(match.normalized_product, str):
            # Check if this is a material parameter
            if any(keyword in param_name.lower() for keyword in ['material', 'conductor', 'insulation', 'sheath', 'armour']):
                match = self._match_material_parameter(match, param_type)
            else:
                match = self._match_string_parameter(match, param_type)
        elif isinstance(match.normalized_rfp, list) and isinstance(match.normalized_product, list):
            match = self._match_list_parameter(match, param_type)
        else:
            # Fallback to string comparison
            match.is_match = str(match.normalized_rfp).lower() == str(match.normalized_product).lower()
            match.match_score = 1.0 if match.is_match else 0.0
            match.reason = "Direct comparison"
        
        return match
    
    def _match_numeric_parameter(
        self,
        match: ParameterMatch,
        param_type: ParameterType
    ) -> ParameterMatch:
        """Match numeric parameters with tolerance.
        
        Args:
            match: ParameterMatch object
            param_type: Type of parameter
            
        Returns:
            Updated ParameterMatch
        """
        rfp_val = float(match.normalized_rfp)
        prod_val = float(match.normalized_product)
        
        # For critical parameters, product must meet or exceed requirement
        if param_type == ParameterType.CRITICAL:
            tolerance = 0.0 if self.strict_critical_match else self.default_tolerance
            
            # Check if product meets minimum requirement
            min_required = rfp_val * (1 - tolerance)
            max_allowed = rfp_val * (1 + tolerance)
            
            if prod_val >= min_required:
                match.is_match = True
                match.match_score = min(1.0, prod_val / rfp_val)
                if prod_val > max_allowed:
                    match.reason = f"Exceeds requirement by {((prod_val/rfp_val - 1) * 100):.1f}%"
                else:
                    match.reason = "Meets critical requirement"
            else:
                match.is_match = False
                match.match_score = prod_val / rfp_val if rfp_val > 0 else 0.0
                match.reason = f"Below requirement by {((1 - prod_val/rfp_val) * 100):.1f}%"
        else:
            # For non-critical, allow tolerance in both directions
            tolerance = self.default_tolerance * 2  # More lenient for optional
            
            lower_bound = rfp_val * (1 - tolerance)
            upper_bound = rfp_val * (1 + tolerance)
            
            if lower_bound <= prod_val <= upper_bound:
                match.is_match = True
                match.match_score = 1.0 - abs(prod_val - rfp_val) / rfp_val
                match.tolerance_applied = True
                match.reason = f"Within {tolerance*100:.0f}% tolerance"
            else:
                match.is_match = False
                deviation = abs(prod_val - rfp_val) / rfp_val
                match.match_score = max(0.0, 1.0 - deviation)
                match.reason = f"Outside tolerance (deviation: {deviation*100:.1f}%)"
        
        return match
    
    def _match_string_parameter(
        self,
        match: ParameterMatch,
        param_type: ParameterType
    ) -> ParameterMatch:
        """Match string parameters with fuzzy matching.
        
        Args:
            match: ParameterMatch object
            param_type: Type of parameter
            
        Returns:
            Updated ParameterMatch
        """
        rfp_str = str(match.normalized_rfp).lower().strip()
        prod_str = str(match.normalized_product).lower().strip()
        
        # Exact match
        if rfp_str == prod_str:
            match.is_match = True
            match.match_score = 1.0
            match.reason = "Exact match"
            return match
        
        # Contains match
        if rfp_str in prod_str or prod_str in rfp_str:
            match.is_match = True
            match.match_score = 0.8
            match.reason = "Partial string match"
            return match
        
        # Calculate similarity using simple character overlap
        similarity = self._calculate_string_similarity(rfp_str, prod_str)
        
        if param_type == ParameterType.CRITICAL:
            match.is_match = similarity >= 0.9
            match.match_score = similarity
            match.reason = f"String similarity: {similarity:.1%}"
        else:
            match.is_match = similarity >= 0.6
            match.match_score = similarity
            match.reason = f"Fuzzy match: {similarity:.1%}"
        
        return match
    
    def _match_material_parameter(
        self,
        match: ParameterMatch,
        param_type: ParameterType
    ) -> ParameterMatch:
        """Match material parameters with equivalence checking.
        
        Args:
            match: ParameterMatch object
            param_type: Type of parameter
            
        Returns:
            Updated ParameterMatch
        """
        rfp_material = str(match.normalized_rfp).lower().strip()
        prod_material = str(match.normalized_product).lower().strip()
        
        # Material equivalence mapping
        material_equivalents = {
            'copper': ['cu', 'copper', 'electrolytic copper', 'pure copper', 'oxygen-free copper'],
            'aluminium': ['al', 'aluminum', 'aluminium', 'alu'],
            'pvc': ['pvc', 'polyvinyl chloride', 'poly vinyl chloride'],
            'xlpe': ['xlpe', 'cross-linked polyethylene', 'crosslinked polyethylene', 'xlpe insulation'],
            'rubber': ['rubber', 'natural rubber', 'synthetic rubber', 'epr', 'ethylene propylene rubber'],
            'steel': ['steel', 'mild steel', 'ms', 'galvanized steel', 'gi'],
            'brass': ['brass', 'br'],
            'frls': ['frls', 'fr-lsh', 'flame retardant low smoke', 'fire resistant'],
            'hrfr': ['hrfr', 'hffr', 'halogen free flame retardant']
        }
        
        # Check exact match first
        if rfp_material == prod_material:
            match.is_match = True
            match.match_score = 1.0
            match.reason = "Exact material match"
            return match
        
        # Check equivalence
        for base_material, equivalents in material_equivalents.items():
            rfp_in_group = rfp_material in equivalents or any(eq in rfp_material for eq in equivalents)
            prod_in_group = prod_material in equivalents or any(eq in prod_material for eq in equivalents)
            
            if rfp_in_group and prod_in_group:
                match.is_match = True
                match.match_score = 0.95
                match.reason = f"Equivalent material ({base_material})"
                return match
        
        # Check for material grade upgrades (e.g., copper purity)
        if 'copper' in rfp_material and 'copper' in prod_material:
            match.is_match = True
            match.match_score = 0.9
            match.reason = "Material type match (grade may differ)"
            return match
        
        # Partial match
        if rfp_material in prod_material or prod_material in rfp_material:
            match.is_match = param_type != ParameterType.CRITICAL
            match.match_score = 0.7
            match.reason = "Partial material match"
            return match
        
        # No match
        match.is_match = False
        match.match_score = 0.0
        match.reason = "Material mismatch"
        return match
    
    def _match_list_parameter(
        self,
        match: ParameterMatch,
        param_type: ParameterType
    ) -> ParameterMatch:
        """Match list parameters (e.g., standards, features).
        
        Args:
            match: ParameterMatch object
            param_type: Type of parameter
            
        Returns:
            Updated ParameterMatch
        """
        rfp_list = [str(x).lower() for x in match.normalized_rfp]
        prod_list = [str(x).lower() for x in match.normalized_product]
        
        # Check how many required items are present
        matched_items = [item for item in rfp_list if item in prod_list]
        
        if len(rfp_list) == 0:
            match.is_match = True
            match.match_score = 1.0
            match.reason = "No requirements"
            return match
        
        coverage = len(matched_items) / len(rfp_list)
        
        if param_type == ParameterType.CRITICAL:
            match.is_match = coverage == 1.0  # All items must match
            match.match_score = coverage
            match.reason = f"Matched {len(matched_items)}/{len(rfp_list)} required items"
        else:
            match.is_match = coverage >= 0.5  # At least half
            match.match_score = coverage
            match.reason = f"Coverage: {coverage:.1%}"
        
        return match
    
    def _apply_unit_conversion(
        self,
        match: ParameterMatch,
        param_name: str
    ) -> ParameterMatch:
        """Apply unit conversion if needed.
        
        Args:
            match: ParameterMatch object
            param_name: Name of parameter
            
        Returns:
            Updated ParameterMatch with converted units
        """
        # Try to convert using standardize_to_base_unit
        try:
            if isinstance(match.normalized_rfp, (str, int, float)):
                rfp_str = str(match.normalized_rfp)
                result_rfp = self.unit_converter.standardize_to_base_unit(rfp_str)
                if result_rfp['success']:
                    match.normalized_rfp = result_rfp['value']
                    match.unit_converted = True
            
            if isinstance(match.normalized_product, (str, int, float)):
                prod_str = str(match.normalized_product)
                result_prod = self.unit_converter.standardize_to_base_unit(prod_str)
                if result_prod['success']:
                    match.normalized_product = result_prod['value']
                    match.unit_converted = True
        except Exception as e:
            # If conversion fails, continue with original values
            self.logger.debug(f"Unit conversion failed for {param_name}: {e}")
        
        return match
    
    def _normalize_value(self, param_name: str, value: Any, category: str) -> Any:
        """Normalize a parameter value.
        
        Args:
            param_name: Name of parameter
            value: Value to normalize
            category: Product category
            
        Returns:
            Normalized value
        """
        if value is None:
            return None
        
        # Handle numeric strings
        if isinstance(value, str):
            # Try to extract number
            import re
            number_match = re.search(r'[-+]?[0-9]*\.?[0-9]+', value)
            if number_match:
                try:
                    return float(number_match.group())
                except ValueError:
                    pass
        
        return value
    
    def _classify_parameter(
        self,
        param_name: str,
        critical_param_names: List[str]
    ) -> ParameterType:
        """Classify parameter as critical, important, or optional.
        
        Args:
            param_name: Name of parameter
            critical_param_names: List of critical parameter names
            
        Returns:
            ParameterType
        """
        if param_name in critical_param_names:
            return ParameterType.CRITICAL
        
        # Important parameters (not critical but significant)
        important_keywords = ['rating', 'capacity', 'size', 'standard', 'certification']
        if any(keyword in param_name.lower() for keyword in important_keywords):
            return ParameterType.IMPORTANT
        
        return ParameterType.OPTIONAL
    
    def _match_standards(
        self,
        rfp_requirements: Dict[str, Any],
        product_specs: Dict[str, Any],
        result: SpecificationMatchResult
    ) -> None:
        """Match standards and compliance requirements.
        
        Args:
            rfp_requirements: RFP requirements
            product_specs: Product specifications
            result: Result object to update
        """
        rfp_standards = rfp_requirements.get('standards', [])
        product_standards = product_specs.get('standards', [])
        
        if not rfp_standards:
            result.compliance_score = 1.0
            return
        
        if isinstance(rfp_standards, str):
            rfp_standards = [rfp_standards]
        if isinstance(product_standards, str):
            product_standards = [product_standards]
        
        for required_std in rfp_standards:
            matched = False
            for product_std in product_standards:
                # Check exact match or equivalence using check_standard_match
                match_result = self.standard_mapper.check_standard_match(required_std, product_std)
                if match_result.get('match', False) or match_result.get('equivalent', False):
                    matched = True
                    result.standard_matches[required_std] = True
                    break
            
            if not matched:
                result.standard_matches[required_std] = False
                result.compliance_issues.append(f"Missing standard: {required_std}")
    
    def _calculate_technical_score(
        self,
        result: SpecificationMatchResult,
        custom_weights: Optional[Dict[str, float]] = None
    ) -> float:
        """Calculate technical matching score.
        
        Args:
            result: Match result
            custom_weights: Optional custom weights
            
        Returns:
            Technical score (0.0 to 1.0)
        """
        weights = custom_weights or self.parameter_weights
        
        total_score = 0.0
        total_weight = 0.0
        
        # Score critical parameters
        for match in result.critical_matches:
            weight = weights.get(ParameterType.CRITICAL, 1.0)
            total_score += match.match_score * weight
            total_weight += weight
        
        # Score important parameters
        for match in result.important_matches:
            weight = weights.get(ParameterType.IMPORTANT, 0.7)
            total_score += match.match_score * weight
            total_weight += weight
        
        # Score optional parameters
        for match in result.optional_matches:
            weight = weights.get(ParameterType.OPTIONAL, 0.3)
            total_score += match.match_score * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def _calculate_compliance_score(self, result: SpecificationMatchResult) -> float:
        """Calculate compliance score based on standards matching.
        
        Args:
            result: Match result
            
        Returns:
            Compliance score (0.0 to 1.0)
        """
        if not result.standard_matches:
            return 1.0  # No standards required
        
        matched = sum(1 for match in result.standard_matches.values() if match)
        total = len(result.standard_matches)
        
        return matched / total if total > 0 else 1.0
    
    def _determine_match_status(
        self,
        result: SpecificationMatchResult,
        critical_fails: int
    ) -> MatchStatus:
        """Determine overall match status.
        
        Args:
            result: Match result
            critical_fails: Number of critical parameter failures
            
        Returns:
            MatchStatus
        """
        if critical_fails > 0:
            return MatchStatus.NO_MATCH
        
        if result.overall_score >= 0.9:
            return MatchStatus.EXACT_MATCH
        elif result.overall_score >= 0.8:
            return MatchStatus.PARTIAL_MATCH
        elif result.overall_score >= 0.6:
            return MatchStatus.NEEDS_REVIEW
        else:
            return MatchStatus.NO_MATCH
    
    def _calculate_confidence_level(
        self, 
        result: SpecificationMatchResult, 
        confidence_score: float = None
    ) -> str:
        """Calculate confidence level of the match.
        
        Args:
            result: Match result
            confidence_score: Optional pre-calculated confidence score
            
        Returns:
            Confidence level string
        """
        # Use provided confidence score if available
        score = confidence_score if confidence_score is not None else result.overall_score
        
        if score >= 0.85 and len(result.missing_parameters) == 0:
            return "high"
        elif score >= 0.75:
            return "medium"
        else:
            return "low"
    
    def _is_recommended(self, result: SpecificationMatchResult) -> bool:
        """Determine if product should be recommended.
        
        Args:
            result: Match result
            
        Returns:
            True if recommended
        """
        return (
            result.match_status in [MatchStatus.EXACT_MATCH, MatchStatus.PARTIAL_MATCH] and
            result.overall_score >= 0.8 and
            len(result.compliance_issues) == 0
        )
    
    def _generate_match_reason(self, result: SpecificationMatchResult) -> str:
        """Generate human-readable match reason.
        
        Args:
            result: Match result
            
        Returns:
            Match reason string
        """
        reasons = []
        
        if result.match_status == MatchStatus.EXACT_MATCH:
            reasons.append("Excellent match - all critical parameters met")
        elif result.match_status == MatchStatus.PARTIAL_MATCH:
            reasons.append("Good match - most requirements satisfied")
        elif result.match_status == MatchStatus.NEEDS_REVIEW:
            reasons.append("Requires review - some parameters need verification")
        else:
            reasons.append("Poor match - critical parameters not met")
        
        if result.missing_parameters:
            reasons.append(f"{len(result.missing_parameters)} parameters missing")
        
        if result.compliance_issues:
            reasons.append(f"{len(result.compliance_issues)} compliance issues")
        
        if result.exceeded_parameters:
            reasons.append(f"Exceeds requirements in {len(result.exceeded_parameters)} parameters")
        
        return "; ".join(reasons)
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings.
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not str1 or not str2:
            return 0.0
        
        # Simple character overlap
        set1 = set(str1.lower())
        set2 = set(str2.lower())
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def batch_match(
        self,
        rfp_requirements: Dict[str, Any],
        products: List[Dict[str, Any]],
        category: str = "default",
        top_k: int = 10
    ) -> List[SpecificationMatchResult]:
        """Match RFP requirements against multiple products.
        
        Args:
            rfp_requirements: RFP technical requirements
            products: List of product specifications
            category: Product category
            top_k: Number of top matches to return
            
        Returns:
            List of top matching results, sorted by score
        """
        self.logger.info(
            "Starting batch matching",
            num_products=len(products),
            category=category
        )
        
        results = []
        for product in products:
            result = self.match_specifications(
                rfp_requirements,
                product,
                category
            )
            results.append(result)
        
        # Sort by overall score
        results.sort(key=lambda x: x.overall_score, reverse=True)
        
        return results[:top_k]
    
    def generate_detailed_explanation(
        self,
        match_result: SpecificationMatchResult,
        rfp_requirements: Dict[str, Any],
        product_specs: Dict[str, Any]
    ):
        """Generate detailed explanation for a match result.
        
        Args:
            match_result: The match result to explain
            rfp_requirements: Original RFP requirements
            product_specs: Product specifications
            
        Returns:
            MatchExplanation with comprehensive analysis
        """
        # Get confidence factors from result or recalculate
        if hasattr(match_result, '_confidence_factors') and match_result._confidence_factors:
            confidence_factors = match_result._confidence_factors
        else:
            _, confidence_factors = self.confidence_calculator.calculate_confidence(
                match_result,
                rfp_requirements,
                product_specs
            )
        
        # Generate explanation
        explanation = self.confidence_calculator.generate_explanation(
            match_result,
            confidence_factors,
            rfp_requirements,
            product_specs
        )
        
        return explanation
    
    def rank_matches_with_explanations(
        self,
        match_results: List[SpecificationMatchResult],
        ranking_criteria: Optional[Dict[str, float]] = None
    ) -> List[Tuple[int, SpecificationMatchResult, float, str]]:
        """Rank matches with explanations and composite scores.
        
        Args:
            match_results: List of match results to rank
            ranking_criteria: Optional custom ranking criteria
            
        Returns:
            List of (rank, result, composite_score, explanation) tuples
        """
        # Use score aggregator to rank
        ranked = self.score_aggregator.rank_by_composite_score(
            match_results,
            ranking_criteria
        )
        
        # Add intelligent explanations based on scores and attributes
        result = []
        for rank, match, score in ranked:
            # Generate explanation based on overall score and specific attributes
            if match.overall_score >= 0.9 and len(match.exceeded_parameters) > 0:
                explanation = f"Excellent match - exceeds {len(match.exceeded_parameters)} requirements"
            elif match.overall_score >= 0.9:
                explanation = "Excellent match - meets all requirements"
            elif match.overall_score >= 0.75:
                if len(match.missing_parameters) > 0:
                    explanation = f"Good match - {len(match.missing_parameters)} params incomplete"
                else:
                    explanation = "Good match - meets key requirements"
            elif match.overall_score >= 0.6:
                if len(match.compliance_issues) > 0:
                    explanation = f"Fair match - {len(match.compliance_issues)} compliance issues"
                elif len(match.missing_parameters) > 0:
                    explanation = f"Fair match - missing {len(match.missing_parameters)} parameters"
                else:
                    explanation = "Fair match - review recommended"
            elif match.overall_score >= 0.4:
                explanation = f"Below requirements - {match.match_status.value.replace('_', ' ')}"
            else:
                explanation = "Does not meet requirements"
            
            # Add confidence indicator
            if hasattr(match, 'confidence_level'):
                conf_emoji = {'high': '●', 'medium': '◐', 'low': '○'}.get(match.confidence_level, '')
                explanation = f"{conf_emoji} {explanation}"
            
            result.append((rank, match, score, explanation))
        
        return result
