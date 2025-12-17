"""
Technical Agent - Advanced RFP analysis, product matching, and recommendations.

This agent:
1. Receives RFP summaries
2. Extracts product requirements
3. Matches against catalog
4. Calculates match scores
5. Generates comparison tables
6. Recommends top 3 products per item
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
import json
import re
import structlog
from collections import defaultdict
import pandas as pd

logger = structlog.get_logger()


@dataclass
class ProductRequirement:
    """Extracted product requirement from RFP."""
    item_number: str
    item_name: str
    description: str
    quantity: int
    unit: str
    
    # Technical specifications
    specifications: Dict[str, Any] = field(default_factory=dict)
    
    # Required standards/certifications
    required_standards: List[str] = field(default_factory=list)
    required_certifications: List[str] = field(default_factory=list)
    
    # Optional preferences
    preferred_brands: List[str] = field(default_factory=list)
    excluded_brands: List[str] = field(default_factory=list)
    
    # Budget constraints
    max_unit_price: Optional[float] = None
    budget_total: Optional[float] = None
    
    # Delivery requirements
    delivery_days_required: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ProductMatch:
    """Product catalog match for a requirement."""
    product_id: str
    product_name: str
    manufacturer: str
    model_number: str
    category: str
    
    # Pricing
    unit_price: float
    moq: int  # Minimum order quantity
    available_stock: int
    
    # Technical specs
    specifications: Dict[str, Any] = field(default_factory=dict)
    
    # Certifications
    certifications: List[str] = field(default_factory=list)
    standards_compliance: List[str] = field(default_factory=list)
    
    # Delivery
    delivery_days: int = 30
    
    # Documentation
    datasheet_url: Optional[str] = None
    catalog_url: Optional[str] = None
    
    # Match scores
    specification_score: float = 0.0
    certification_score: float = 0.0
    price_score: float = 0.0
    delivery_score: float = 0.0
    overall_score: float = 0.0
    
    # Match details
    matched_specs: List[str] = field(default_factory=list)
    missing_specs: List[str] = field(default_factory=list)
    matched_certifications: List[str] = field(default_factory=list)
    missing_certifications: List[str] = field(default_factory=list)
    
    rank: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ComparisonTable:
    """Comparison table for top products."""
    requirement: ProductRequirement
    products: List[ProductMatch]
    comparison_matrix: pd.DataFrame
    recommendation: str
    confidence_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'requirement': self.requirement.to_dict(),
            'products': [p.to_dict() for p in self.products],
            'comparison_matrix': self.comparison_matrix.to_dict() if isinstance(self.comparison_matrix, pd.DataFrame) else {},
            'recommendation': self.recommendation,
            'confidence_score': self.confidence_score
        }


class RequirementExtractor:
    """Extract product requirements from RFP summaries."""
    
    def __init__(self):
        """Initialize requirement extractor."""
        self.logger = logger.bind(component="RequirementExtractor")
    
    def extract_requirements(self, rfp_summary: Dict[str, Any]) -> List[ProductRequirement]:
        """Extract product requirements from RFP summary.
        
        Args:
            rfp_summary: RFP summary with technical details
            
        Returns:
            List of ProductRequirement objects
        """
        self.logger.info("Extracting requirements from RFP summary")
        
        requirements = []
        
        # Extract from technical_requirements field
        tech_reqs = rfp_summary.get('technical_requirements', [])
        
        # Parse structured requirements if available
        if 'items' in rfp_summary:
            for item in rfp_summary['items']:
                req = self._parse_item(item)
                requirements.append(req)
        else:
            # Parse from unstructured text
            requirements = self._parse_unstructured(rfp_summary, tech_reqs)
        
        self.logger.info(f"Extracted {len(requirements)} requirements")
        return requirements
    
    def _parse_item(self, item: Dict[str, Any]) -> ProductRequirement:
        """Parse structured item into ProductRequirement."""
        return ProductRequirement(
            item_number=item.get('item_number', 'ITEM-001'),
            item_name=item.get('name', 'Unknown Item'),
            description=item.get('description', ''),
            quantity=item.get('quantity', 1),
            unit=item.get('unit', 'nos'),
            specifications=item.get('specifications', {}),
            required_standards=item.get('standards', []),
            required_certifications=item.get('certifications', []),
            max_unit_price=item.get('max_price', None),
            delivery_days_required=item.get('delivery_days', None)
        )
    
    def _parse_unstructured(self, rfp_summary: Dict[str, Any], tech_reqs: List[str]) -> List[ProductRequirement]:
        """Parse unstructured RFP text into requirements."""
        requirements = []
        
        description = rfp_summary.get('description', '')
        title = rfp_summary.get('title', '')
        
        # Extract categories from title/description
        categories = self._extract_categories(title + ' ' + description)
        
        # Create requirements from technical requirements
        for idx, req_text in enumerate(tech_reqs, 1):
            specs = self._parse_specifications(req_text)
            
            req = ProductRequirement(
                item_number=f"ITEM-{idx:03d}",
                item_name=categories[0] if categories else f"Item {idx}",
                description=req_text,
                quantity=1,
                unit='nos',
                specifications=specs,
                required_standards=self._extract_standards(req_text),
                required_certifications=self._extract_certifications(req_text)
            )
            requirements.append(req)
        
        # If no technical requirements, create from categories
        if not requirements and categories:
            for idx, category in enumerate(categories, 1):
                req = ProductRequirement(
                    item_number=f"ITEM-{idx:03d}",
                    item_name=category,
                    description=f"{category} as per RFP specifications",
                    quantity=1,
                    unit='nos',
                    specifications={},
                    required_standards=[],
                    required_certifications=[]
                )
                requirements.append(req)
        
        return requirements
    
    def _extract_categories(self, text: str) -> List[str]:
        """Extract product categories from text."""
        categories = []
        
        # Common FMCG electrical categories
        category_keywords = {
            'Cable': ['cable', 'wire', 'conductor'],
            'Switchgear': ['switchgear', 'switch', 'circuit breaker', 'mcb', 'mccb'],
            'Lighting': ['light', 'led', 'lamp', 'luminaire', 'fixture'],
            'Fan': ['fan', 'ceiling fan', 'exhaust fan'],
            'Air Conditioner': ['ac', 'air conditioner', 'cooling'],
            'Water Heater': ['water heater', 'geyser'],
            'Pump': ['pump', 'water pump'],
            'Motor': ['motor', 'induction motor'],
            'Transformer': ['transformer', 'distribution transformer']
        }
        
        text_lower = text.lower()
        for category, keywords in category_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                categories.append(category)
        
        return categories or ['General Electrical']
    
    def _parse_specifications(self, text: str) -> Dict[str, Any]:
        """Parse technical specifications from text."""
        specs = {}
        
        # Voltage pattern
        voltage_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:kV|V|volt)', text, re.IGNORECASE)
        if voltage_match:
            specs['voltage'] = voltage_match.group(1)
        
        # Current pattern
        current_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:A|amp|ampere)', text, re.IGNORECASE)
        if current_match:
            specs['current'] = current_match.group(1)
        
        # Power pattern
        power_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:W|watt|kW|kilowatt|HP|hp)', text, re.IGNORECASE)
        if power_match:
            specs['power'] = power_match.group(1)
        
        # Frequency pattern
        freq_match = re.search(r'(\d+)\s*(?:Hz|hertz)', text, re.IGNORECASE)
        if freq_match:
            specs['frequency'] = freq_match.group(1)
        
        # Core/conductor pattern
        core_match = re.search(r'(\d+)\s*core', text, re.IGNORECASE)
        if core_match:
            specs['cores'] = core_match.group(1)
        
        # Size/area pattern
        size_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:sq\.?\s*mm|mm2|sqmm)', text, re.IGNORECASE)
        if size_match:
            specs['size_sqmm'] = size_match.group(1)
        
        # IP rating
        ip_match = re.search(r'IP\s*(\d{2})', text, re.IGNORECASE)
        if ip_match:
            specs['ip_rating'] = f"IP{ip_match.group(1)}"
        
        return specs
    
    def _extract_standards(self, text: str) -> List[str]:
        """Extract required standards from text."""
        standards = []
        
        # Indian standards
        is_matches = re.findall(r'IS\s*[:\-]?\s*(\d+(?:[:\-]\d+)?)', text, re.IGNORECASE)
        standards.extend([f"IS {match}" for match in is_matches])
        
        # International standards
        iec_matches = re.findall(r'IEC\s*[:\-]?\s*(\d+(?:[:\-]\d+)?)', text, re.IGNORECASE)
        standards.extend([f"IEC {match}" for match in iec_matches])
        
        # IEEE standards
        ieee_matches = re.findall(r'IEEE\s*[:\-]?\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)
        standards.extend([f"IEEE {match}" for match in ieee_matches])
        
        return list(set(standards))
    
    def _extract_certifications(self, text: str) -> List[str]:
        """Extract required certifications from text."""
        certifications = []
        
        cert_keywords = ['BIS', 'ISI', 'CE', 'UL', 'ISO', 'BEE', 'CPRI']
        
        text_upper = text.upper()
        for cert in cert_keywords:
            if cert in text_upper:
                certifications.append(cert)
        
        return certifications


class CatalogMatcher:
    """Match requirements against product catalog."""
    
    def __init__(self, catalog_path: Optional[str] = None):
        """Initialize catalog matcher.
        
        Args:
            catalog_path: Path to product catalog JSON/CSV
        """
        self.logger = logger.bind(component="CatalogMatcher")
        self.catalog = []
        
        if catalog_path:
            self.load_catalog(catalog_path)
        else:
            # Initialize with sample catalog
            self._init_sample_catalog()
    
    def load_catalog(self, catalog_path: str):
        """Load product catalog from file."""
        path = Path(catalog_path)
        
        if path.suffix == '.json':
            with open(path, 'r') as f:
                self.catalog = json.load(f)
        elif path.suffix == '.csv':
            df = pd.read_csv(path)
            self.catalog = df.to_dict('records')
        
        self.logger.info(f"Loaded {len(self.catalog)} products from catalog")
    
    def _init_sample_catalog(self):
        """Initialize with sample catalog for testing."""
        self.catalog = [
            {
                'product_id': 'HAV-CAB-001',
                'product_name': 'Havells PVC Insulated Cable',
                'manufacturer': 'Havells',
                'model_number': 'HRFR-90',
                'category': 'Cable',
                'unit_price': 45.50,
                'moq': 100,
                'available_stock': 50000,
                'specifications': {
                    'voltage': '1.1',
                    'cores': '4',
                    'size_sqmm': '2.5',
                    'conductor': 'Copper',
                    'insulation': 'PVC'
                },
                'certifications': ['BIS', 'ISI', 'ISO 9001'],
                'standards_compliance': ['IS 694', 'IS 1554'],
                'delivery_days': 15,
                'datasheet_url': 'https://havells.com/cables/hrfr90.pdf'
            },
            {
                'product_id': 'POL-CAB-002',
                'product_name': 'Polycab FR PVC Cable',
                'manufacturer': 'Polycab',
                'model_number': 'FR-PVC-4C',
                'category': 'Cable',
                'unit_price': 42.00,
                'moq': 100,
                'available_stock': 75000,
                'specifications': {
                    'voltage': '1.1',
                    'cores': '4',
                    'size_sqmm': '2.5',
                    'conductor': 'Copper',
                    'insulation': 'FR-PVC'
                },
                'certifications': ['BIS', 'ISI', 'ISO 9001', 'CE'],
                'standards_compliance': ['IS 694', 'IS 1554', 'IEC 60227'],
                'delivery_days': 10,
                'datasheet_url': 'https://polycab.com/cables/fr-pvc.pdf'
            },
            {
                'product_id': 'HAV-SW-003',
                'product_name': 'Havells Crabtree Athena Switchgear',
                'manufacturer': 'Havells',
                'model_number': 'ATHENA-MCB-16A',
                'category': 'Switchgear',
                'unit_price': 185.00,
                'moq': 50,
                'available_stock': 10000,
                'specifications': {
                    'current': '16',
                    'voltage': '240',
                    'poles': '1',
                    'breaking_capacity': '10kA'
                },
                'certifications': ['BIS', 'ISI', 'ISO 9001'],
                'standards_compliance': ['IS 8828', 'IEC 60898'],
                'delivery_days': 7,
                'datasheet_url': 'https://havells.com/switchgear/athena.pdf'
            }
        ]
        
        self.logger.info(f"Initialized with {len(self.catalog)} sample products")
    
    def find_matches(self, requirement: ProductRequirement, top_k: int = 10) -> List[ProductMatch]:
        """Find matching products for requirement.
        
        Args:
            requirement: Product requirement to match
            top_k: Number of top matches to return
            
        Returns:
            List of ProductMatch objects sorted by score
        """
        self.logger.info(f"Finding matches for: {requirement.item_name}")
        
        matches = []
        
        for product in self.catalog:
            # Check category match
            if not self._category_matches(requirement.item_name, product.get('category', '')):
                continue
            
            # Create ProductMatch
            match = ProductMatch(
                product_id=product['product_id'],
                product_name=product['product_name'],
                manufacturer=product['manufacturer'],
                model_number=product['model_number'],
                category=product['category'],
                unit_price=product['unit_price'],
                moq=product['moq'],
                available_stock=product['available_stock'],
                specifications=product.get('specifications', {}),
                certifications=product.get('certifications', []),
                standards_compliance=product.get('standards_compliance', []),
                delivery_days=product.get('delivery_days', 30),
                datasheet_url=product.get('datasheet_url'),
                catalog_url=product.get('catalog_url')
            )
            
            # Calculate scores
            self._calculate_scores(match, requirement)
            
            matches.append(match)
        
        # Sort by overall score
        matches.sort(key=lambda x: x.overall_score, reverse=True)
        
        # Assign ranks
        for rank, match in enumerate(matches[:top_k], 1):
            match.rank = rank
        
        self.logger.info(f"Found {len(matches)} matches, returning top {min(top_k, len(matches))}")
        
        return matches[:top_k]
    
    def _category_matches(self, requirement_name: str, product_category: str) -> bool:
        """Check if product category matches requirement."""
        req_lower = requirement_name.lower()
        cat_lower = product_category.lower()
        
        # Direct match
        if cat_lower in req_lower or req_lower in cat_lower:
            return True
        
        # Keyword matching
        req_keywords = set(req_lower.split())
        cat_keywords = set(cat_lower.split())
        
        return bool(req_keywords & cat_keywords)
    
    def _calculate_scores(self, match: ProductMatch, requirement: ProductRequirement):
        """Calculate match scores for product.
        
        Args:
            match: ProductMatch object to score
            requirement: ProductRequirement to match against
        """
        # 1. Specification Score (40%)
        spec_score, matched_specs, missing_specs = self._calculate_specification_score(
            match.specifications,
            requirement.specifications
        )
        match.specification_score = spec_score
        match.matched_specs = matched_specs
        match.missing_specs = missing_specs
        
        # 2. Certification Score (30%)
        cert_score, matched_certs, missing_certs = self._calculate_certification_score(
            match.certifications + match.standards_compliance,
            requirement.required_certifications + requirement.required_standards
        )
        match.certification_score = cert_score
        match.matched_certifications = matched_certs
        match.missing_certifications = missing_certs
        
        # 3. Price Score (20%)
        match.price_score = self._calculate_price_score(
            match.unit_price,
            requirement.max_unit_price
        )
        
        # 4. Delivery Score (10%)
        match.delivery_score = self._calculate_delivery_score(
            match.delivery_days,
            requirement.delivery_days_required
        )
        
        # Overall Score (weighted average)
        match.overall_score = (
            match.specification_score * 0.40 +
            match.certification_score * 0.30 +
            match.price_score * 0.20 +
            match.delivery_score * 0.10
        )
        
        match.overall_score = round(match.overall_score, 2)
    
    def _calculate_specification_score(
        self,
        product_specs: Dict[str, Any],
        required_specs: Dict[str, Any]
    ) -> Tuple[float, List[str], List[str]]:
        """Calculate specification match score."""
        if not required_specs:
            return 1.0, [], []
        
        matched = []
        missing = []
        
        for key, req_value in required_specs.items():
            if key in product_specs:
                prod_value = str(product_specs[key])
                req_value_str = str(req_value)
                
                # Exact or fuzzy match
                if prod_value.lower() == req_value_str.lower():
                    matched.append(f"{key}: {req_value}")
                elif req_value_str.lower() in prod_value.lower():
                    matched.append(f"{key}: {req_value} (≈ {prod_value})")
                else:
                    missing.append(f"{key}: {req_value} (got {prod_value})")
            else:
                missing.append(f"{key}: {req_value}")
        
        score = len(matched) / len(required_specs) if required_specs else 1.0
        return score, matched, missing
    
    def _calculate_certification_score(
        self,
        product_certs: List[str],
        required_certs: List[str]
    ) -> Tuple[float, List[str], List[str]]:
        """Calculate certification match score."""
        if not required_certs:
            return 1.0, [], []
        
        product_certs_upper = [c.upper() for c in product_certs]
        required_certs_upper = [c.upper() for c in required_certs]
        
        matched = [c for c in required_certs if c.upper() in product_certs_upper]
        missing = [c for c in required_certs if c.upper() not in product_certs_upper]
        
        score = len(matched) / len(required_certs) if required_certs else 1.0
        return score, matched, missing
    
    def _calculate_price_score(
        self,
        product_price: float,
        max_price: Optional[float]
    ) -> float:
        """Calculate price score (lower is better)."""
        if max_price is None or max_price == 0:
            return 1.0
        
        if product_price <= max_price:
            # Perfect score if under budget
            return 1.0
        else:
            # Penalize for over budget
            over_budget_ratio = (product_price - max_price) / max_price
            return max(0.0, 1.0 - over_budget_ratio)
    
    def _calculate_delivery_score(
        self,
        product_delivery_days: int,
        required_delivery_days: Optional[int]
    ) -> float:
        """Calculate delivery score (faster is better)."""
        if required_delivery_days is None:
            return 1.0
        
        if product_delivery_days <= required_delivery_days:
            return 1.0
        else:
            # Penalize for slower delivery
            delay_ratio = (product_delivery_days - required_delivery_days) / required_delivery_days
            return max(0.0, 1.0 - delay_ratio * 0.5)


class ComparisonGenerator:
    """Generate comparison tables and recommendations."""
    
    def __init__(self):
        """Initialize comparison generator."""
        self.logger = logger.bind(component="ComparisonGenerator")
    
    def generate_comparison(
        self,
        requirement: ProductRequirement,
        matches: List[ProductMatch],
        top_n: int = 3
    ) -> ComparisonTable:
        """Generate comparison table for top N products.
        
        Args:
            requirement: Product requirement
            matches: List of product matches
            top_n: Number of top products to compare
            
        Returns:
            ComparisonTable object
        """
        self.logger.info(f"Generating comparison for {requirement.item_name}")
        
        # Select top N products
        top_products = matches[:top_n]
        
        # Generate comparison matrix
        matrix = self._create_comparison_matrix(top_products)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(requirement, top_products)
        
        # Calculate confidence
        confidence = self._calculate_confidence(top_products)
        
        return ComparisonTable(
            requirement=requirement,
            products=top_products,
            comparison_matrix=matrix,
            recommendation=recommendation,
            confidence_score=confidence
        )
    
    def _create_comparison_matrix(self, products: List[ProductMatch]) -> pd.DataFrame:
        """Create comparison matrix DataFrame."""
        if not products:
            return pd.DataFrame()
        
        data = []
        for product in products:
            row = {
                'Rank': product.rank,
                'Product': product.product_name,
                'Manufacturer': product.manufacturer,
                'Model': product.model_number,
                'Price (₹)': f"₹{product.unit_price:,.2f}",
                'MOQ': product.moq,
                'Stock': product.available_stock,
                'Delivery': f"{product.delivery_days} days",
                'Spec Score': f"{product.specification_score*100:.1f}%",
                'Cert Score': f"{product.certification_score*100:.1f}%",
                'Price Score': f"{product.price_score*100:.1f}%",
                'Overall Score': f"{product.overall_score*100:.1f}%",
                'Certifications': ', '.join(product.certifications[:3]),
            }
            data.append(row)
        
        return pd.DataFrame(data)
    
    def _generate_recommendation(
        self,
        requirement: ProductRequirement,
        products: List[ProductMatch]
    ) -> str:
        """Generate recommendation text."""
        if not products:
            return "No suitable products found in catalog."
        
        top_product = products[0]
        
        recommendation = f"""
RECOMMENDED PRODUCT:

Product: {top_product.product_name} ({top_product.manufacturer})
Model: {top_product.model_number}
Overall Score: {top_product.overall_score*100:.1f}%

STRENGTHS:
"""
        
        # Add matched specs
        if top_product.matched_specs:
            recommendation += "✓ Specifications: " + ", ".join(top_product.matched_specs[:3]) + "\n"
        
        # Add matched certifications
        if top_product.matched_certifications:
            recommendation += "✓ Certifications: " + ", ".join(top_product.matched_certifications) + "\n"
        
        # Add price advantage
        if top_product.price_score >= 0.9:
            recommendation += f"✓ Competitive Price: ₹{top_product.unit_price:,.2f}/unit\n"
        
        # Add delivery advantage
        if top_product.delivery_score >= 0.9:
            recommendation += f"✓ Quick Delivery: {top_product.delivery_days} days\n"
        
        # Add concerns
        if top_product.missing_specs or top_product.missing_certifications:
            recommendation += "\nCONSIDERATIONS:\n"
            
            if top_product.missing_specs:
                recommendation += "⚠ Missing Specs: " + ", ".join(top_product.missing_specs[:2]) + "\n"
            
            if top_product.missing_certifications:
                recommendation += "⚠ Missing Certs: " + ", ".join(top_product.missing_certifications) + "\n"
        
        # Add alternatives
        if len(products) > 1:
            recommendation += f"\nALTERNATIVES:\n"
            for i, alt in enumerate(products[1:3], 2):
                recommendation += f"{i}. {alt.product_name} ({alt.manufacturer}) - Score: {alt.overall_score*100:.1f}%\n"
        
        return recommendation.strip()
    
    def _calculate_confidence(self, products: List[ProductMatch]) -> float:
        """Calculate confidence in recommendation."""
        if not products:
            return 0.0
        
        top_score = products[0].overall_score
        
        # High confidence if top product has high score
        if top_score >= 0.9:
            confidence = 0.95
        elif top_score >= 0.8:
            confidence = 0.85
        elif top_score >= 0.7:
            confidence = 0.75
        else:
            confidence = 0.60
        
        # Adjust for gap between #1 and #2
        if len(products) > 1:
            second_score = products[1].overall_score
            gap = top_score - second_score
            
            if gap >= 0.2:
                confidence = min(1.0, confidence + 0.05)  # Clear winner
            elif gap < 0.05:
                confidence = max(0.5, confidence - 0.10)  # Close race
        
        return round(confidence, 2)


class TechnicalAgent:
    """
    Technical Agent for RFP analysis and product matching.
    
    Capabilities:
    1. Receives RFP summaries
    2. Extracts product requirements
    3. Matches against catalog
    4. Calculates match scores
    5. Generates comparison tables
    6. Recommends top 3 products per item
    """
    
    def __init__(self, catalog_path: Optional[str] = None):
        """Initialize Technical Agent.
        
        Args:
            catalog_path: Optional path to product catalog
        """
        self.logger = logger.bind(component="TechnicalAgent")
        
        # Initialize components
        self.requirement_extractor = RequirementExtractor()
        self.catalog_matcher = CatalogMatcher(catalog_path)
        self.comparison_generator = ComparisonGenerator()
        
        # Statistics
        self.statistics = {
            'total_rfps_processed': 0,
            'total_requirements_extracted': 0,
            'total_matches_found': 0,
            'average_confidence': 0.0
        }
        
        self.logger.info("Technical Agent initialized")
    
    def process_rfp(self, rfp_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Process RFP summary and generate product recommendations.
        
        Args:
            rfp_summary: RFP summary from Sales Agent
            
        Returns:
            Dictionary with requirements, matches, and comparisons
        """
        self.logger.info("Processing RFP", rfp_id=rfp_summary.get('rfp_id', 'unknown'))
        
        # Step 1: Extract requirements
        requirements = self.requirement_extractor.extract_requirements(rfp_summary)
        
        if not requirements:
            self.logger.warning("No requirements extracted from RFP")
            return {
                'success': False,
                'error': 'No requirements extracted',
                'requirements': [],
                'comparisons': []
            }
        
        # Step 2: Match and compare for each requirement
        comparisons = []
        all_matches = []
        
        for requirement in requirements:
            # Find matches
            matches = self.catalog_matcher.find_matches(requirement, top_k=10)
            
            if matches:
                # Generate comparison for top 3
                comparison = self.comparison_generator.generate_comparison(
                    requirement,
                    matches,
                    top_n=3
                )
                comparisons.append(comparison)
                all_matches.extend(matches)
            else:
                self.logger.warning(f"No matches found for: {requirement.item_name}")
        
        # Update statistics
        self.statistics['total_rfps_processed'] += 1
        self.statistics['total_requirements_extracted'] += len(requirements)
        self.statistics['total_matches_found'] += len(all_matches)
        
        if comparisons:
            avg_conf = sum(c.confidence_score for c in comparisons) / len(comparisons)
            self.statistics['average_confidence'] = round(avg_conf, 2)
        
        # Generate summary
        result = {
            'success': True,
            'rfp_id': rfp_summary.get('rfp_id', 'unknown'),
            'rfp_title': rfp_summary.get('title', 'Unknown'),
            'processed_at': datetime.now().isoformat(),
            'summary': {
                'total_requirements': len(requirements),
                'requirements_matched': len(comparisons),
                'match_rate': round(len(comparisons) / len(requirements) * 100, 1) if requirements else 0,
                'average_confidence': self.statistics['average_confidence']
            },
            'requirements': [req.to_dict() for req in requirements],
            'comparisons': [comp.to_dict() for comp in comparisons],
            'statistics': self.statistics.copy()
        }
        
        self.logger.info(
            "RFP processing completed",
            requirements=len(requirements),
            matches=len(comparisons),
            avg_confidence=self.statistics['average_confidence']
        )
        
        return result
    
    def export_comparison_tables(self, result: Dict[str, Any], output_dir: str = './outputs') -> str:
        """Export comparison tables to Excel file.
        
        Args:
            result: Result from process_rfp
            output_dir: Output directory for files
            
        Returns:
            Path to exported file
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        rfp_id = result['rfp_id']
        
        # Create Excel writer
        excel_path = output_path / f"comparison_{rfp_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = {
                'Metric': ['RFP ID', 'RFP Title', 'Total Requirements', 'Requirements Matched', 'Match Rate', 'Avg Confidence'],
                'Value': [
                    result['rfp_id'],
                    result['rfp_title'],
                    result['summary']['total_requirements'],
                    result['summary']['requirements_matched'],
                    f"{result['summary']['match_rate']}%",
                    f"{result['summary']['average_confidence']*100:.1f}%"
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            
            # Comparison tables for each requirement
            for idx, comparison in enumerate(result['comparisons'], 1):
                req = ProductRequirement(**comparison['requirement'])
                
                # Reconstruct DataFrame from dict
                if comparison['comparison_matrix']:
                    df = pd.DataFrame(comparison['comparison_matrix'])
                    sheet_name = f"Item_{idx}_{req.item_name[:20]}"
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # Add recommendation as note
                    worksheet = writer.sheets[sheet_name]
                    recommendation = comparison['recommendation']
                    
                    # Add recommendation in separate rows
                    start_row = len(df) + 3
                    worksheet.cell(row=start_row, column=1, value="RECOMMENDATION:")
                    
                    for i, line in enumerate(recommendation.split('\n'), 1):
                        worksheet.cell(row=start_row + i, column=1, value=line)
        
        self.logger.info(f"Comparison tables exported to: {excel_path}")
        
        return str(excel_path)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get agent statistics."""
        return self.statistics.copy()
    
    def load_catalog(self, catalog_path: str):
        """Load product catalog from file.
        
        Args:
            catalog_path: Path to catalog JSON/CSV
        """
        self.catalog_matcher.load_catalog(catalog_path)
        self.logger.info(f"Catalog loaded: {len(self.catalog_matcher.catalog)} products")


# Example usage
if __name__ == '__main__':
    # Initialize agent
    agent = TechnicalAgent()
    
    # Sample RFP summary from Sales Agent
    rfp_summary = {
        'rfp_id': 'RFP-2024-001',
        'title': 'Supply of Electrical Cables and Wires',
        'organization': 'Indian Railways',
        'description': 'Tender for supply of 4-core PVC insulated cables',
        'technical_requirements': [
            'PVC insulated 4-core cable, 2.5 sq.mm, 1.1kV, IS 694 compliant',
            'Minimum length 100 meters per coil',
            'BIS certification mandatory'
        ],
        'estimated_value': 5000000.0
    }
    
    # Process RFP
    result = agent.process_rfp(rfp_summary)
    
    # Print results
    print("\n" + "="*80)
    print("TECHNICAL AGENT - RFP ANALYSIS RESULTS")
    print("="*80)
    
    print(f"\nRFP: {result['rfp_title']}")
    print(f"Requirements Extracted: {result['summary']['total_requirements']}")
    print(f"Requirements Matched: {result['summary']['requirements_matched']}")
    print(f"Match Rate: {result['summary']['match_rate']}%")
    print(f"Average Confidence: {result['summary']['average_confidence']*100:.1f}%")
    
    print("\n" + "-"*80)
    print("PRODUCT COMPARISONS:")
    print("-"*80)
    
    for comparison in result['comparisons']:
        req = ProductRequirement(**comparison['requirement'])
        print(f"\n📦 {req.item_name}")
        print(f"   Quantity: {req.quantity} {req.unit}")
        
        if comparison['products']:
            print(f"\n   Top 3 Products:")
            for product_dict in comparison['products']:
                product = ProductMatch(**product_dict)
                print(f"   {product.rank}. {product.product_name}")
                print(f"      Manufacturer: {product.manufacturer}")
                print(f"      Price: ₹{product.unit_price:,.2f}")
                print(f"      Overall Score: {product.overall_score*100:.1f}%")
        
        print(f"\n   {comparison['recommendation']}")
        print(f"\n   Confidence: {comparison['confidence_score']*100:.1f}%")
    
    # Export to Excel
    excel_path = agent.export_comparison_tables(result)
    print(f"\n✅ Comparison tables exported to: {excel_path}")
