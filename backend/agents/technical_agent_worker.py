"""
Technical Agent Worker - Product matching and specification analysis.

Responsibilities:
1. Receives RFP summary and document from Main Agent
2. Summarizes products in scope of supply
3. Recommends top 3 OEM products per item with Spec Match % metric
4. Creates comparison table of RFP specs vs top 3 OEM products
5. Selects top OEM product based on spec match metric
6. Sends product table to Main Agent and Pricing Agent
"""
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
import structlog
import pandas as pd

logger = structlog.get_logger()


@dataclass
class ProductInScope:
    """Product identified in RFP scope of supply."""
    item_number: str
    item_name: str
    description: str
    quantity: int
    unit: str
    specifications: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OEMProductRecommendation:
    """OEM product recommendation with spec match."""
    rank: int  # 1, 2, or 3
    product_id: str
    manufacturer: str  # OEM brand
    model_number: str
    product_name: str
    
    # Spec match metric (%)
    spec_match_percentage: float
    
    # Pricing and availability
    unit_price: float
    available_stock: int
    delivery_days: int
    
    # Product specs (with defaults must come after fields without defaults)
    specifications: Dict[str, Any] = field(default_factory=dict)
    
    # Certifications
    certifications: List[str] = field(default_factory=list)
    standards_compliance: List[str] = field(default_factory=list)
    
    # Match details
    matched_specs: List[str] = field(default_factory=list)
    missing_specs: List[str] = field(default_factory=list)


@dataclass
class ComparisonTableRow:
    """Single row in comparison table."""
    spec_parameter: str
    rfp_requirement: str
    product_1_value: str
    product_2_value: str
    product_3_value: str
    product_1_match: bool
    product_2_match: bool
    product_3_match: bool


class TechnicalAgentWorker:
    """
    Technical Agent - Product matching and recommendations.
    
    Workflow:
    1. Receive RFP summary and document from Master Agent
    2. Extract and summarize products in scope of supply
    3. For each product, search OEM product repository
    4. Calculate Spec Match % for each OEM product (equal weightage for all specs)
    5. Recommend top 3 OEM products per item
    6. Create comparison table (RFP specs vs Top 3 products)
    7. Select best match (highest Spec Match %)
    8. Send product recommendations to Main Agent and Pricing Agent
    """
    
    def __init__(self, product_repository):
        """Initialize Technical Agent Worker.
        
        Args:
            product_repository: Repository of OEM product datasheets
        """
        self.logger = logger.bind(component="TechnicalAgentWorker")
        self.product_repo = product_repository
    
    async def process_rfp_requirements(
        self, 
        rfp_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process RFP and generate product recommendations.
        
        Args:
            rfp_input: RFP data from Master Agent containing:
                - rfp_id: RFP identifier
                - rfp_title: RFP title
                - organization: Buyer organization
                - scope_of_supply: List of products needed
                - technical_requirements: List of technical specs
                - required_standards: Required compliance standards
                - required_certifications: Required certifications
                - specifications: Detailed specifications
                - rfp_document: Path to RFP PDF
                - raw_text: Extracted RFP text
        
        Returns:
            Dictionary with recommendations for Master Agent and Pricing Agent
        """
        rfp_id = rfp_input['rfp_id']
        
        self.logger.info(
            " Step 1: Receiving RFP from Master Agent",
            rfp_id=rfp_id,
            rfp_title=rfp_input['rfp_title']
        )
        
        # Step 2: Summarize products in scope of supply
        products_in_scope = self._summarize_scope_of_supply(rfp_input)
        self.logger.info(
            f" Step 2: Identified {len(products_in_scope)} products in scope"
        )
        
        # Step 3-6: For each product, find top 3 matches and create comparison
        all_recommendations = []
        all_comparisons = []
        selected_products = []
        
        for product_item in products_in_scope:
            self.logger.info(
                f" Processing: {product_item.item_name}",
                item_number=product_item.item_number
            )
            
            # Step 3: Find top 3 OEM products with Spec Match %
            top_3_matches = await self._find_top_3_matches(product_item)
            
            self.logger.info(
                f" Step 3: Found top 3 matches for {product_item.item_name}",
                matches=[f"{m.manufacturer} {m.model_number} ({m.spec_match_percentage}%)" 
                         for m in top_3_matches]
            )
            
            # Step 4: Create comparison table
            comparison_table = self._create_comparison_table(
                product_item,
                top_3_matches
            )
            
            self.logger.info(
                f" Step 4: Created comparison table for {product_item.item_name}"
            )
            
            # Step 5: Select best match (highest Spec Match %)
            best_match = top_3_matches[0] if top_3_matches else None
            
            if best_match:
                self.logger.info(
                    f" Step 5: Selected top product - {best_match.manufacturer} "
                    f"{best_match.model_number} ({best_match.spec_match_percentage}%)"
                )
                
                selected_products.append({
                    'item_number': product_item.item_number,
                    'item_name': product_item.item_name,
                    'quantity': product_item.quantity,
                    'unit': product_item.unit,
                    'product_id': best_match.product_id,
                    'manufacturer': best_match.manufacturer,
                    'model_number': best_match.model_number,
                    'spec_match_score': best_match.spec_match_percentage,
                    'unit_price': best_match.unit_price,
                    'line_total': best_match.unit_price * product_item.quantity,
                    'certifications': best_match.certifications,
                    'standards_compliance': best_match.standards_compliance,
                    'delivery_days': best_match.delivery_days
                })
            
            all_recommendations.append({
                'product_item': product_item,
                'top_3_matches': top_3_matches,
                'selected_product': best_match
            })
            
            all_comparisons.append(comparison_table)
        
        # Step 6: Prepare final table for Main Agent and Pricing Agent
        response = {
            'rfp_id': rfp_id,
            'products_in_scope': [vars(p) for p in products_in_scope],
            'recommendations': all_recommendations,
            'comparison_tables': all_comparisons,
            'selected_products': selected_products,
            'match_summary': self._create_match_summary(selected_products),
            'compliance_summary': self._create_compliance_summary(selected_products),
            'confidence_score': self._calculate_confidence(selected_products),
            'processed_at': datetime.now().isoformat()
        }
        
        self.logger.info(
            " Technical Agent processing complete",
            total_products=len(products_in_scope),
            total_recommendations=len(selected_products)
        )
        
        return response
    
    def _summarize_scope_of_supply(
        self, 
        rfp_input: Dict[str, Any]
    ) -> List[ProductInScope]:
        """Summarize products in scope of supply from RFP.
        
        Args:
            rfp_input: RFP data
            
        Returns:
            List of ProductInScope objects
        """
        self.logger.info("Extracting products from scope of supply")
        
        products = []
        
        # Get scope from input
        scope_items = rfp_input.get('scope_of_supply', [])
        
        for item in scope_items:
            product = ProductInScope(
                item_number=item.get('item_number', 'ITEM-001'),
                item_name=item.get('item_name', 'Unknown Product'),
                description=item.get('description', ''),
                quantity=item.get('quantity', 1),
                unit=item.get('unit', 'nos'),
                specifications=item.get('specifications', {})
            )
            products.append(product)
        
        # If no structured scope, extract from specifications
        if not products:
            products = self._extract_products_from_specifications(rfp_input)
        
        # Still no products? Parse from title/text
        if not products:
            products = self._parse_scope_from_text(rfp_input)
        
        return products
    
    def _extract_products_from_specifications(self, rfp_input: Dict[str, Any]) -> List[ProductInScope]:
        """Extract product types from RFP specifications.
        
        When scope_of_supply is not available, infer products from specifications.
        """
        structured_data = rfp_input.get('structured_data', {})
        if isinstance(structured_data, str):
            import json
            try:
                structured_data = json.loads(structured_data)
            except:
                structured_data = {}
        
        specifications = structured_data.get('specifications', [])
        
        if not specifications:
            return []
        
        # Group specifications by product type
        product_groups = {}
        generic_specs = {}
        
        for spec in specifications:
            if isinstance(spec, dict):
                param = spec.get('parameter', '').lower()
                value = spec.get('value', '')
                
                # Identify product type from parameter
                product_type = None
                
                # Cable type indicators
                if any(kw in param for kw in ['solar cable', 'pv cable', 'photovoltaic cable']):
                    product_type = 'Solar Cable'
                elif any(kw in param for kw in ['power cable', 'lv cable', 'hv cable', '11kv', '33kv']):
                    product_type = 'Power Cable'
                elif any(kw in param for kw in ['control cable', 'instrumentation cable']):
                    product_type = 'Control Cable'
                elif any(kw in param for kw in ['building wire', 'house wire', 'fr wire']):
                    product_type = 'Building Wire'
                elif any(kw in param for kw in ['armored cable', 'armoured cable', 'swa cable']):
                    product_type = 'Armored Cable'
                elif any(kw in param for kw in ['flexible cable', 'flex cable']):
                    product_type = 'Flexible Cable'
                elif 'cable' in param or 'wire' in param or 'conductor' in param:
                    # Generic cable/wire
                    if not product_type:
                        # Try to infer from voltage
                        if 'voltage' in param or 'kv' in param:
                            if any(v in str(value).lower() for v in ['11', '33', '22', '6.6', '3.3']):
                                product_type = 'Power Cable'
                            elif any(v in str(value).lower() for v in ['1.1', '1.5', '650', '450']):
                                product_type = 'Control Cable'
                        # Try to infer from conductor size
                        elif 'conductor' in param or 'size' in param:
                            if any(s in str(value) for s in ['50', '70', '95', '120', '150', '185', '240', '300']):
                                product_type = 'Power Cable'
                            elif any(s in str(value) for s in ['1.5', '2.5', '4', '6', '10', '16', '25']):
                                product_type = 'Control Cable'
                        
                        if not product_type:
                            product_type = 'Cable'
                
                # Store specification
                if product_type:
                    if product_type not in product_groups:
                        product_groups[product_type] = {}
                    
                    # Clean parameter name
                    clean_param = param.replace('cable', '').replace('wire', '').strip()
                    product_groups[product_type][clean_param] = value
                else:
                    # Store as generic spec
                    generic_specs[param] = value
        
        # Create ProductInScope objects
        products = []
        
        for idx, (product_type, specs) in enumerate(product_groups.items(), 1):
            # Merge with generic specs
            all_specs = {**generic_specs, **specs}
            
            # Infer quantity if present
            quantity = 1
            for key in ['quantity', 'qty', 'no of items', 'units']:
                if key in all_specs:
                    try:
                        quantity = int(str(all_specs[key]).split()[0])
                        break
                    except:
                        pass
            
            product = ProductInScope(
                item_number=f'ITEM-{idx:03d}',
                item_name=product_type,
                description=f'{product_type} from RFP specifications',
                quantity=quantity,
                unit='nos',
                specifications=all_specs
            )
            products.append(product)
        
        self.logger.info(
            f"Extracted {len(products)} product types from {len(specifications)} specifications",
            product_types=[p.item_name for p in products]
        )
        
        return products
    
    async def _find_top_3_matches(
        self, 
        product_item: ProductInScope
    ) -> List[OEMProductRecommendation]:
        """Find top 3 OEM product matches with Spec Match %.
        
        Spec Match % Calculation:
        - Equal weightage for all required specifications
        - Score = (Number of matched specs / Total required specs) * 100
        
        Args:
            product_item: Product from RFP scope
            
        Returns:
            Top 3 OEM products ranked by Spec Match %
        """
        self.logger.info(f"Searching OEM products for: {product_item.item_name}")
        
        # Search product repository (now async)
        candidate_products = await self.product_repo.search_products(
            category=product_item.item_name,
            specifications=product_item.specifications,
            limit=50
        )
        
        # Calculate Spec Match % for each candidate
        matches_with_scores = []
        
        for candidate in candidate_products:
            spec_match_pct = self._calculate_spec_match_percentage(
                required_specs=product_item.specifications,
                product_specs=candidate.get('specifications', {})
            )
            
            matched_specs, missing_specs = self._compare_specs(
                required_specs=product_item.specifications,
                product_specs=candidate.get('specifications', {})
            )
            
            recommendation = OEMProductRecommendation(
                rank=0,  # Will be set after sorting
                product_id=candidate.get('product_id', ''),
                manufacturer=candidate.get('manufacturer', ''),
                model_number=candidate.get('model_number', ''),
                product_name=candidate.get('product_name', ''),
                spec_match_percentage=spec_match_pct,
                specifications=candidate.get('specifications', {}),
                unit_price=candidate.get('unit_price', 0.0),
                available_stock=candidate.get('stock', 0),
                delivery_days=candidate.get('delivery_days', 30),
                certifications=candidate.get('certifications', []),
                standards_compliance=candidate.get('standards', []),
                matched_specs=matched_specs,
                missing_specs=missing_specs
            )
            
            matches_with_scores.append(recommendation)
        
        # Sort by Spec Match % (descending)
        sorted_matches = sorted(
            matches_with_scores,
            key=lambda x: x.spec_match_percentage,
            reverse=True
        )
        
        # Take top 3 and assign ranks
        top_3 = sorted_matches[:3]
        for idx, match in enumerate(top_3, 1):
            match.rank = idx
        
        self.logger.info(
            f"Found {len(sorted_matches)} candidates, returning top 3",
            top_3_scores=[m.spec_match_percentage for m in top_3]
        )
        
        return top_3
    
    def _calculate_spec_match_percentage(
        self,
        required_specs: Dict[str, Any],
        product_specs: Dict[str, Any]
    ) -> float:
        """Calculate Spec Match % with equal weightage for all specs.
        
        Formula:
        Spec Match % = (Matched Specs Count / Total Required Specs) * 100
        
        Args:
            required_specs: Specifications from RFP
            product_specs: Specifications from OEM product
            
        Returns:
            Spec Match percentage (0-100)
        """
        if not required_specs:
            return 100.0  # No requirements = perfect match
        
        total_required = len(required_specs)
        matched_count = 0
        
        for req_key, req_value in required_specs.items():
            if req_key in product_specs:
                prod_value = product_specs[req_key]
                
                # Check if values match (with tolerance for numeric)
                if self._specs_match(req_value, prod_value):
                    matched_count += 1
        
        match_percentage = (matched_count / total_required) * 100
        return round(match_percentage, 2)
    
    def _specs_match(self, required_value: Any, product_value: Any) -> bool:
        """Check if specification values match."""
        # String comparison
        if isinstance(required_value, str) and isinstance(product_value, str):
            return required_value.lower().strip() == product_value.lower().strip()
        
        # Numeric comparison (with 5% tolerance)
        try:
            req_num = float(required_value)
            prod_num = float(product_value)
            tolerance = req_num * 0.05
            return abs(req_num - prod_num) <= tolerance
        except (ValueError, TypeError):
            pass
        
        # Exact match
        return required_value == product_value
    
    def _compare_specs(
        self,
        required_specs: Dict[str, Any],
        product_specs: Dict[str, Any]
    ) -> Tuple[List[str], List[str]]:
        """Compare specs and return matched and missing lists."""
        matched = []
        missing = []
        
        for req_key, req_value in required_specs.items():
            if req_key in product_specs:
                if self._specs_match(req_value, product_specs[req_key]):
                    matched.append(req_key)
                else:
                    missing.append(req_key)
            else:
                missing.append(req_key)
        
        return matched, missing
    
    def _create_comparison_table(
        self,
        product_item: ProductInScope,
        top_3_matches: List[OEMProductRecommendation]
    ) -> Dict[str, Any]:
        """Create comparison table of RFP specs vs top 3 OEM products.
        
        Args:
            product_item: Product from RFP
            top_3_matches: Top 3 OEM product recommendations
            
        Returns:
            Comparison table data
        """
        self.logger.info(f"Creating comparison table for {product_item.item_name}")
        
        # Ensure we have exactly 3 products (pad with None if needed)
        products = top_3_matches + [None] * (3 - len(top_3_matches))
        
        rows = []
        
        # Create row for each specification parameter
        for spec_param, rfp_value in product_item.specifications.items():
            row = ComparisonTableRow(
                spec_parameter=spec_param,
                rfp_requirement=str(rfp_value),
                product_1_value=str(products[0].specifications.get(spec_param, 'N/A')) if products[0] else 'N/A',
                product_2_value=str(products[1].specifications.get(spec_param, 'N/A')) if products[1] else 'N/A',
                product_3_value=str(products[2].specifications.get(spec_param, 'N/A')) if products[2] else 'N/A',
                product_1_match=spec_param in products[0].matched_specs if products[0] else False,
                product_2_match=spec_param in products[1].matched_specs if products[1] else False,
                product_3_match=spec_param in products[2].matched_specs if products[2] else False
            )
            rows.append(vars(row))
        
        # Create DataFrame for easy viewing
        df = pd.DataFrame(rows)
        
        return {
            'item_name': product_item.item_name,
            'item_number': product_item.item_number,
            'product_1': {
                'manufacturer': products[0].manufacturer if products[0] else 'N/A',
                'model': products[0].model_number if products[0] else 'N/A',
                'spec_match': products[0].spec_match_percentage if products[0] else 0.0
            },
            'product_2': {
                'manufacturer': products[1].manufacturer if products[1] else 'N/A',
                'model': products[1].model_number if products[1] else 'N/A',
                'spec_match': products[1].spec_match_percentage if products[1] else 0.0
            },
            'product_3': {
                'manufacturer': products[2].manufacturer if products[2] else 'N/A',
                'model': products[2].model_number if products[2] else 'N/A',
                'spec_match': products[2].spec_match_percentage if products[2] else 0.0
            },
            'comparison_rows': rows,
            'comparison_dataframe': df.to_dict('records') if not df.empty else []
        }
    
    def _parse_scope_from_text(self, rfp_input: Dict[str, Any]) -> List[ProductInScope]:
        """Parse scope of supply from RFP text (fallback)."""
        # Try to get category from structured_data first
        structured_data = rfp_input.get('structured_data', {})
        specifications = rfp_input.get('specifications', {})
        
        # Extract category with fallback chain
        category = (
            structured_data.get('category') or 
            specifications.get('category') or 
            self._infer_category_from_title(rfp_input.get('title', '')) or
            'Electrical Products'
        )
        
        # Extract quantity
        quantity_str = structured_data.get('quantity', '1')
        try:
            quantity = int(''.join(filter(str.isdigit, str(quantity_str))) or '1')
        except:
            quantity = 1
        
        return [
            ProductInScope(
                item_number='ITEM-001',
                item_name=category,
                description=rfp_input.get('title', rfp_input.get('rfp_title', '')),
                quantity=quantity,
                unit='nos',
                specifications=specifications or structured_data
            )
        ]
    
    def _infer_category_from_title(self, title: str) -> str:
        """Infer product category from RFP title."""
        title_lower = title.lower()
        
        # Map keywords to categories
        category_keywords = {
            'Solar Cables': ['solar cable', 'pv cable', 'photovoltaic'],
            'Power Cables': ['power cable', 'lv cable', 'hv cable', 'mv cable'],
            'Signaling Cables': ['signal cable', 'railway cable', 'telecom cable'],
            'Control Cables': ['control cable', 'instrumentation'],
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in title_lower for keyword in keywords):
                return category
        
        return None
    
    def _create_match_summary(self, selected_products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create match summary statistics."""
        if not selected_products:
            return {}
        
        avg_match = sum(p['spec_match_score'] for p in selected_products) / len(selected_products)
        
        return {
            'total_products': len(selected_products),
            'average_spec_match': round(avg_match, 2),
            'high_match_count': sum(1 for p in selected_products if p['spec_match_score'] >= 80),
            'medium_match_count': sum(1 for p in selected_products if 60 <= p['spec_match_score'] < 80),
            'low_match_count': sum(1 for p in selected_products if p['spec_match_score'] < 60)
        }
    
    def _create_compliance_summary(self, selected_products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create compliance summary."""
        all_certs = set()
        all_standards = set()
        
        for product in selected_products:
            all_certs.update(product.get('certifications', []))
            all_standards.update(product.get('standards_compliance', []))
        
        return {
            'certifications_covered': list(all_certs),
            'standards_covered': list(all_standards),
            'compliance_level': 'High' if len(all_certs) >= 3 else 'Medium'
        }
    
    def _calculate_confidence(self, selected_products: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence score."""
        if not selected_products:
            return 0.0
        
        avg_match = sum(p['spec_match_score'] for p in selected_products) / len(selected_products)
        return round(avg_match / 100, 2)

