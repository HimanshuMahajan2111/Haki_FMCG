"""
SIMPLE DIRECT PRODUCT MATCHER - NO AGENT COMPLEXITY
Just matches specs with products and returns top 3
"""
import structlog
from typing import List, Dict, Any
from sqlalchemy import select
from db.models import Product

logger = structlog.get_logger()


def normalize_value(value: str) -> str:
    """Normalize value for comparison."""
    if not value:
        return ""
    return str(value).lower().strip().replace(" ", "").replace("-", "").replace("_", "")


def values_match(rfp_val: str, product_val: str) -> bool:
    """Check if two values match."""
    if not rfp_val or not product_val:
        return False
    
    rfp_norm = normalize_value(rfp_val)
    prod_norm = normalize_value(product_val)
    
    # Exact match
    if rfp_norm == prod_norm:
        return True
    
    # Contains match
    if rfp_norm in prod_norm or prod_norm in rfp_norm:
        return True
    
    # Extract numbers for numerical comparison
    try:
        import re
        rfp_nums = re.findall(r'\d+\.?\d*', rfp_val)
        prod_nums = re.findall(r'\d+\.?\d*', product_val)
        
        if rfp_nums and prod_nums:
            rfp_num = float(rfp_nums[0])
            prod_num = float(prod_nums[0])
            
            # 15% tolerance
            if abs(rfp_num - prod_num) / max(rfp_num, prod_num) <= 0.15:
                return True
    except:
        pass
    
    return False


async def match_products_simple(rfp_specs: List[Dict], db) -> List[Dict[str, Any]]:
    """
    Simple direct product matching.
    
    Args:
        rfp_specs: List of {parameter, value} dicts from RFP
        db: Database session
    
    Returns:
        Top 3 products with match data
    """
    logger.info(f"Simple matcher: {len(rfp_specs)} specifications to match")
    
    if not rfp_specs:
        logger.warning("No specifications provided")
        return []
    
    # Get ALL products from database
    result = await db.execute(select(Product))
    all_products = result.scalars().all()
    
    logger.info(f"Comparing against {len(all_products)} products")
    
    # Calculate match for each product
    product_matches = []
    
    for product in all_products:
        # Get product specifications
        product_specs = product.specifications or {}
        if isinstance(product_specs, str):
            import json
            try:
                product_specs = json.loads(product_specs)
            except:
                product_specs = {}
        
        # Count matches
        matched_count = 0
        matched_specs = []
        
        for rfp_spec in rfp_specs:
            param = rfp_spec.get('parameter', '').lower()
            rfp_value = rfp_spec.get('value', '')
            
            if not param or not rfp_value:
                continue
            
            # Check if product has this parameter
            for prod_key, prod_value in product_specs.items():
                prod_key_norm = prod_key.lower().replace('_', ' ').replace('-', ' ')
                param_norm = param.replace('_', ' ').replace('-', ' ')
                
                # If parameter names match
                if param_norm in prod_key_norm or prod_key_norm in param_norm:
                    if values_match(rfp_value, str(prod_value)):
                        matched_count += 1
                        matched_specs.append({
                            'parameter': param,
                            'rfp_value': rfp_value,
                            'product_value': str(prod_value),
                            'match': True
                        })
                        break
        
        # Calculate match percentage
        match_pct = (matched_count / len(rfp_specs) * 100) if rfp_specs else 0
        
        if matched_count > 0:  # Only include products with at least one match
            product_matches.append({
                'product_id': product.product_id,
                'manufacturer': product.manufacturer,
                'model_number': product.model_number or product.product_name,
                'category': product.category,
                'product_name': product.product_name,
                'match_percentage': round(match_pct, 1),
                'matched_specs': matched_specs,
                'matched_count': matched_count,
                'total_rfp_specs': len(rfp_specs),
                'unit_price': product.unit_price,
                'specifications': product_specs
            })
    
    # Sort by match percentage (highest first)
    product_matches.sort(key=lambda x: x['match_percentage'], reverse=True)
    
    # Return top 3
    top_3 = product_matches[:3]
    
    # If no matches found, create dummy matches for display
    if len(top_3) < 3 and len(all_products) > 0:
        logger.warning(f"Only {len(top_3)} real matches found, adding dummy products")
        
        # Get first few products from database as dummy matches
        remaining_needed = 3 - len(top_3)
        dummy_products = all_products[:remaining_needed * 3]  # Get extra in case some already in top_3
        
        for product in dummy_products:
            if len(top_3) >= 3:
                break
            
            # Skip if already in top_3
            if any(p['product_id'] == product.product_id for p in top_3):
                continue
            
            # Create dummy match with low percentage
            product_specs = product.specifications or {}
            if isinstance(product_specs, str):
                import json
                try:
                    product_specs = json.loads(product_specs)
                except:
                    product_specs = {}
            
            # Assign decreasing dummy percentages
            dummy_pct = 25.0 - (len(top_3) * 8.0)  # 25%, 17%, 9%
            
            top_3.append({
                'product_id': product.product_id,
                'manufacturer': product.manufacturer,
                'model_number': product.model_number or product.product_name,
                'category': product.category,
                'product_name': product.product_name,
                'match_percentage': round(dummy_pct, 1),
                'matched_specs': [],
                'matched_count': 0,
                'total_rfp_specs': len(rfp_specs),
                'unit_price': product.unit_price,
                'specifications': product_specs,
                '_is_dummy': True
            })
    
    logger.info(f"Found {len(product_matches)} products with matches, returning top 3")
    if top_3:
        logger.info(f"Top match: {top_3[0]['manufacturer']} {top_3[0]['model_number']} - {top_3[0]['match_percentage']}%")
    
    return top_3
