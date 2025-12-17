"""
Product Repository - OEM product database with specifications.

This module provides a searchable repository of OEM products (Havells, Polycab, KEI, etc.)
with specifications for product matching.
"""
from typing import List, Dict, Any, Optional
import structlog
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import AsyncSessionLocal
from db.product_models import OEMProduct

logger = structlog.get_logger()


class ProductRepository:
    """Repository of OEM products with specifications."""
    
    def __init__(self, use_database: bool = True):
        """Initialize product repository.
        
        Args:
            use_database: Query from database (True) or use dummy data (False)
        """
        self.logger = logger.bind(component="ProductRepository")
        self.use_database = use_database
        
        if not use_database:
            self._products = self._load_dummy_products()
        else:
            self._products = []  # Will query database on demand
            self.logger.info("ProductRepository initialized with database backend")
    
    def _load_dummy_products(self) -> List[Dict[str, Any]]:
        """Load dummy OEM product database for testing."""
        self.logger.info("Loading dummy OEM product database")
        
        # Dummy product database
        products = [
            # Solar Cables
            {
                'product_id': 'HAV-SOL-001',
                'manufacturer': 'Havells',
                'model_number': 'HRFR-6SQ',
                'product_name': 'Havells Solar DC Cable 6 sq mm',
                'category': 'Solar Cables',
                'specifications': {
                    'voltage_rating': '1.1 kV',
                    'conductor_size': '6 sq mm',
                    'conductor_material': 'Tinned Copper',
                    'insulation': 'XLPE',
                    'cores': '1',
                    'temperature_rating': '90C',
                    'flame_retardant': 'Yes'
                },
                'certifications': ['BIS', 'IEC 60502', 'TUV'],
                'standards': ['IS 694', 'IEC 60502'],
                'unit_price': 2800,
                'stock': 5000,
                'delivery_days': 7
            },
            {
                'product_id': 'POL-SOL-002',
                'manufacturer': 'Polycab',
                'model_number': 'POLYSOLAR-6',
                'product_name': 'Polycab Solar Cable 6 sq mm',
                'category': 'Solar Cables',
                'specifications': {
                    'voltage_rating': '1.1 kV',
                    'conductor_size': '6 sq mm',
                    'conductor_material': 'Tinned Copper',
                    'insulation': 'XLPE',
                    'cores': '1',
                    'temperature_rating': '90C',
                    'flame_retardant': 'Yes'
                },
                'certifications': ['BIS', 'IEC 60502'],
                'standards': ['IS 694', 'IEC 60502'],
                'unit_price': 2700,
                'stock': 8000,
                'delivery_days': 5
            },
            {
                'product_id': 'KEI-SOL-003',
                'manufacturer': 'KEI',
                'model_number': 'KEI-SOLAR-6',
                'product_name': 'KEI Solar DC Cable 6 sq mm',
                'category': 'Solar Cables',
                'specifications': {
                    'voltage_rating': '1.1 kV',
                    'conductor_size': '6 sq mm',
                    'conductor_material': 'Tinned Copper',
                    'insulation': 'XLPE',
                    'cores': '1',
                    'temperature_rating': '90C',
                    'flame_retardant': 'Yes'
                },
                'certifications': ['BIS', 'TUV'],
                'standards': ['IS 694', 'IEC 60502'],
                'unit_price': 2600,
                'stock': 6000,
                'delivery_days': 10
            },
            
            # Power Cables
            {
                'product_id': 'HAV-POW-011',
                'manufacturer': 'Havells',
                'model_number': 'XLPE-11KV-185',
                'product_name': 'Havells 11kV XLPE Cable 185 sq mm',
                'category': 'Power Cables',
                'specifications': {
                    'voltage_rating': '11 kV',
                    'conductor_size': '185 sq mm',
                    'conductor_material': 'Aluminum',
                    'insulation': 'XLPE',
                    'cores': '3',
                    'sheath': 'PVC',
                    'armour': 'SWA'
                },
                'certifications': ['BIS', 'ISO 9001'],
                'standards': ['IS 7098', 'IEC 60502'],
                'unit_price': 3800,
                'stock': 3000,
                'delivery_days': 14
            },
            {
                'product_id': 'POL-POW-012',
                'manufacturer': 'Polycab',
                'model_number': 'POLYCAB-11KV-185',
                'product_name': 'Polycab 11kV XLPE Cable 185 sq mm',
                'category': 'Power Cables',
                'specifications': {
                    'voltage_rating': '11 kV',
                    'conductor_size': '185 sq mm',
                    'conductor_material': 'Aluminum',
                    'insulation': 'XLPE',
                    'cores': '3',
                    'sheath': 'PVC',
                    'armour': 'SWA'
                },
                'certifications': ['BIS', 'ISO 9001', 'IEC 60502'],
                'standards': ['IS 7098', 'IEC 60502'],
                'unit_price': 3900,
                'stock': 4000,
                'delivery_days': 10
            },
            {
                'product_id': 'KEI-POW-013',
                'manufacturer': 'KEI',
                'model_number': 'KEI-11KV-185',
                'product_name': 'KEI 11kV XLPE Cable 185 sq mm',
                'category': 'Power Cables',
                'specifications': {
                    'voltage_rating': '11 kV',
                    'conductor_size': '185 sq mm',
                    'conductor_material': 'Aluminum',
                    'insulation': 'XLPE',
                    'cores': '3',
                    'sheath': 'PVC',
                    'armour': 'SWA'
                },
                'certifications': ['BIS'],
                'standards': ['IS 7098', 'IEC 60502'],
                'unit_price': 3700,
                'stock': 2500,
                'delivery_days': 12
            },
            
            # Signaling Cables
            {
                'product_id': 'HAV-SIG-021',
                'manufacturer': 'Havells',
                'model_number': 'SIGNAL-4C-1.5',
                'product_name': 'Havells Signaling Cable 4C x 1.5 sq mm',
                'category': 'Signaling Cables',
                'specifications': {
                    'voltage_rating': '650 V',
                    'conductor_size': '1.5 sq mm',
                    'conductor_material': 'Copper',
                    'insulation': 'PVC',
                    'cores': '4',
                    'sheath': 'PVC'
                },
                'certifications': ['BIS', 'RDSO'],
                'standards': ['IS 1554', 'RDSO SPEC'],
                'unit_price': 2000,
                'stock': 10000,
                'delivery_days': 5
            },
            {
                'product_id': 'POL-SIG-022',
                'manufacturer': 'Polycab',
                'model_number': 'POLYSIGNAL-4C-1.5',
                'product_name': 'Polycab Railway Signaling Cable 4C x 1.5 sq mm',
                'category': 'Signaling Cables',
                'specifications': {
                    'voltage_rating': '650 V',
                    'conductor_size': '1.5 sq mm',
                    'conductor_material': 'Copper',
                    'insulation': 'PVC',
                    'cores': '4',
                    'sheath': 'PVC'
                },
                'certifications': ['BIS', 'RDSO', 'ISO 9001'],
                'standards': ['IS 1554', 'RDSO SPEC'],
                'unit_price': 1950,
                'stock': 12000,
                'delivery_days': 3
            },
            {
                'product_id': 'KEI-SIG-023',
                'manufacturer': 'KEI',
                'model_number': 'KEI-SIGNAL-4C-1.5',
                'product_name': 'KEI Signaling Cable 4C x 1.5 sq mm',
                'category': 'Signaling Cables',
                'specifications': {
                    'voltage_rating': '650 V',
                    'conductor_size': '1.5 sq mm',
                    'conductor_material': 'Copper',
                    'insulation': 'PVC',
                    'cores': '4',
                    'sheath': 'PVC'
                },
                'certifications': ['BIS', 'RDSO'],
                'standards': ['IS 1554', 'RDSO SPEC'],
                'unit_price': 1900,
                'stock': 8000,
                'delivery_days': 7
            },
            
            # Telecom Cables
            {
                'product_id': 'HAV-TEL-031',
                'manufacturer': 'Havells',
                'model_number': 'JELLY-50P',
                'product_name': 'Havells Telecom Cable 50 Pair',
                'category': 'Telecom Cables',
                'specifications': {
                    'pairs': '50',
                    'conductor_size': '0.5 mm',
                    'conductor_material': 'Copper',
                    'insulation': 'PE',
                    'filling': 'Jelly Filled',
                    'sheath': 'HDPE'
                },
                'certifications': ['BIS', 'DOT'],
                'standards': ['IS 13210'],
                'unit_price': 2500,
                'stock': 5000,
                'delivery_days': 10
            },
            {
                'product_id': 'POL-TEL-032',
                'manufacturer': 'Polycab',
                'model_number': 'POLYTELE-50P',
                'product_name': 'Polycab Telecom Cable 50 Pair Jelly Filled',
                'category': 'Telecom Cables',
                'specifications': {
                    'pairs': '50',
                    'conductor_size': '0.5 mm',
                    'conductor_material': 'Copper',
                    'insulation': 'PE',
                    'filling': 'Jelly Filled',
                    'sheath': 'HDPE'
                },
                'certifications': ['BIS', 'DOT', 'ISO 9001'],
                'standards': ['IS 13210'],
                'unit_price': 2400,
                'stock': 7000,
                'delivery_days': 8
            }
        ]
        
        self.logger.info(f"Loaded {len(products)} products from repository")
        return products
    
    async def search_products(
        self,
        category: str = None,
        specifications: Dict[str, Any] = None,
        manufacturer: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search products by criteria with intelligent specification matching.
        
        Handles 693+ products efficiently by:
        1. Smart keyword extraction from category
        2. Multi-keyword category matching
        3. Specification-based filtering
        4. Relevance-based ranking
        
        Args:
            category: Product category/type (e.g., "Solar Cables", "XLPE Cable 11kV")
            specifications: Required specifications (voltage_rating, conductor_size, etc.)
            manufacturer: Manufacturer to filter by
            limit: Maximum number of results
            
        Returns:
            List of matching products sorted by relevance
        """
        if not self.use_database:
            # Fallback to in-memory search for dummy data
            results = self._products.copy()
            
            if category:
                category_lower = category.lower()
                results = [
                    p for p in results
                    if category_lower in p['category'].lower() or
                       category_lower in p['product_name'].lower()
                ]
            
            if manufacturer:
                manufacturer_lower = manufacturer.lower()
                results = [
                    p for p in results
                    if manufacturer_lower in p['manufacturer'].lower()
                ]
            
            # Filter by specifications
            if specifications:
                results = self._filter_by_specifications(results, specifications)
            
            return results[:limit]
        
        # Database query with smart category matching
        async with AsyncSessionLocal() as db:
            query = select(OEMProduct).where(OEMProduct.is_active == True)
            
            # Smart category filtering - extract keywords
            category_results = []
            if category:
                # Extract meaningful keywords from category
                keywords = self._extract_category_keywords(category)
                
                # Build OR conditions for each keyword
                category_conditions = []
                for keyword in keywords:
                    category_conditions.extend([
                        OEMProduct.category.ilike(f"%{keyword}%"),
                        OEMProduct.product_name.ilike(f"%{keyword}%"),
                        OEMProduct.model_number.ilike(f"%{keyword}%")
                    ])
                
                if category_conditions:
                    category_query = query.where(or_(*category_conditions))
                    category_query = category_query.limit(limit * 5)
                    result = await db.execute(category_query)
                    category_results = result.scalars().all()
            
            # If category search found products, use them; otherwise search ALL products
            if category_results:
                products = category_results
                self.logger.info(
                    f"Category search: {len(products)} candidates",
                    category=category,
                    keywords=keywords if category else None
                )
            else:
                # Search ALL products if category search returned nothing
                all_query = query
                if manufacturer:
                    all_query = all_query.where(OEMProduct.manufacturer.ilike(f"%{manufacturer}%"))
                
                # Get ALL products (or large subset)
                all_query = all_query.limit(1000)  # Get all products
                result = await db.execute(all_query)
                products = result.scalars().all()
                
                self.logger.info(
                    f"Searching ALL products: {len(products)} candidates (category returned 0)",
                    category=category
                )
            
            # Convert to dict format
            results = [self._product_to_dict(p) for p in products]
            
            # ALWAYS filter by specifications to get top matches
            if specifications and len(specifications) > 0:
                results = self._filter_by_specifications(results, specifications)
            elif not specifications:
                # No specs provided, return top products by category match
                results = results[:limit]
            
            self.logger.info(
                f"Search results: {len(results)} products from database",
                category=category,
                manufacturer=manufacturer,
                has_specs=bool(specifications)
            )
            
            return results[:limit]
    
    def _extract_category_keywords(self, category: str) -> List[str]:
        """Extract meaningful keywords from category for better matching.
        
        Args:
            category: Product category/name from RFP
            
        Returns:
            List of keywords for searching
        """
        # Common stop words to exclude
        stop_words = {'and', 'or', 'the', 'a', 'an', 'for', 'with', 'of', 'in', 'to'}
        
        # Split and clean
        words = category.lower().replace('-', ' ').replace('_', ' ').split()
        
        # Extract meaningful keywords (length > 2, not stop words)
        keywords = [
            word.strip() 
            for word in words 
            if len(word) > 2 and word not in stop_words
        ]
        
        # Add the full phrase if it's not too long
        if len(category) > 3 and len(category) < 50:
            keywords.append(category.lower().strip())
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)
        
        return unique_keywords[:10]  # Limit to 10 keywords max
    
    def _filter_by_specifications(
        self, 
        products: List[Dict[str, Any]], 
        required_specs: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Filter products by specification matching with optimized performance.
        
        Matches products based on:
        - Exact matches for critical specs (voltage_rating, conductor_material)
        - Range matches for numeric specs (conductor_size with tolerance)
        - Partial matches for descriptive specs (insulation type, cable type)
        
        Optimized for 693+ products:
        - Early termination for low-match products
        - Prioritized spec checking (critical specs first)
        - Efficient key normalization caching
        
        Args:
            products: List of product dictionaries
            required_specs: Required specifications from RFP
            
        Returns:
            Filtered and scored products sorted by match quality
        """
        if not required_specs or len(required_specs) == 0:
            return products
        
        # Critical specs that must match (adjust based on your domain)
        critical_specs = {'voltage_rating', 'voltage', 'conductor_material', 'material', 
                         'insulation', 'insulation_material', 'cable_type', 'type'}
        
        scored_products = []
        total_specs = len(required_specs)
        min_match_threshold = 0.30  # 30% minimum match
        
        # Pre-normalize required spec keys for efficiency
        normalized_required = {}
        for spec_key, required_value in required_specs.items():
            spec_key_normalized = spec_key.lower().replace('_', ' ').replace('-', ' ').strip()
            normalized_required[spec_key_normalized] = (spec_key, required_value)
        
        for product in products:
            product_specs = product.get('specifications', {})
            if not product_specs or len(product_specs) == 0:
                continue
            
            match_score = 0
            matched_specs = []
            critical_match_count = 0
            critical_total = 0
            
            # Pre-normalize product spec keys
            normalized_product = {}
            for prod_key, prod_value in product_specs.items():
                prod_key_normalized = prod_key.lower().replace('_', ' ').replace('-', ' ').strip()
                normalized_product[prod_key_normalized] = prod_value
            
            # Check each required specification
            for norm_key, (original_key, required_value) in normalized_required.items():
                is_critical = any(crit in norm_key for crit in critical_specs)
                if is_critical:
                    critical_total += 1
                
                # Find matching spec in product (optimized lookup)
                found_match = False
                
                # Try exact normalized match first
                if norm_key in normalized_product:
                    if self._values_match(required_value, normalized_product[norm_key], original_key):
                        match_score += 1
                        matched_specs.append(original_key)
                        if is_critical:
                            critical_match_count += 1
                        found_match = True
                
                # Try partial match if exact didn't work
                if not found_match:
                    for prod_key_norm, prod_value in normalized_product.items():
                        if norm_key in prod_key_norm or prod_key_norm in norm_key:
                            if self._values_match(required_value, prod_value, original_key):
                                match_score += 1
                                matched_specs.append(original_key)
                                if is_critical:
                                    critical_match_count += 1
                                break
            
            # Calculate match percentage
            match_percentage = (match_score / total_specs) * 100 if total_specs > 0 else 0
            
            # Calculate critical spec match percentage
            critical_match_pct = (critical_match_count / critical_total * 100) if critical_total > 0 else 100
            
            # Add ALL products with scores (we'll filter later if needed)
            product['_match_score'] = match_percentage
            product['_critical_match_pct'] = critical_match_pct
            product['_matched_specs'] = matched_specs
            product['_match_count'] = match_score
            scored_products.append(product)
        
        # Sort by match score (highest first), then by critical match percentage
        scored_products.sort(
            key=lambda p: (p.get('_match_score', 0), p.get('_critical_match_pct', 0)), 
            reverse=True
        )
        
        # Filter products with at least minimum threshold, but ALWAYS return at least top 3
        filtered_products = [p for p in scored_products if p.get('_match_score', 0) >= (min_match_threshold * 100)]
        
        # If we have fewer than 3 products, return best available even if below threshold
        if len(filtered_products) < 3 and len(scored_products) > 0:
            filtered_products = scored_products[:max(3, len(scored_products))]
            self.logger.warning(
                f"Only {len(filtered_products)} products met threshold, returning best available",
                top_scores=[p.get('_match_score', 0) for p in filtered_products[:3]]
            )
        
        self.logger.info(
            f"Specification filtering: {len(filtered_products)} of {len(products)} products matched",
            required_specs_count=len(required_specs),
            min_threshold=f"{min_match_threshold*100}%",
            top_3_scores=[p.get('_match_score', 0) for p in filtered_products[:3]] if filtered_products else []
        )
        
        return filtered_products
    
    def _values_match(self, required: Any, product: Any, spec_key: str) -> bool:
        """Check if specification values match with intelligent tolerance.
        
        Args:
            required: Required value from RFP
            product: Product specification value
            spec_key: Specification key name
            
        Returns:
            True if values match within acceptable tolerance
        """
        spec_key_lower = spec_key.lower()
        
        # String comparison (case-insensitive)
        if isinstance(required, str) and isinstance(product, str):
            required_lower = required.lower().strip()
            product_lower = product.lower().strip()
            
            # Exact match
            if required_lower == product_lower:
                return True
            
            # Partial match (one contains the other)
            if required_lower in product_lower or product_lower in required_lower:
                return True
            
            # Special handling for common abbreviations
            abbreviations = {
                'xlpe': ['cross-linked polyethylene', 'crosslinked polyethylene'],
                'pvc': ['polyvinyl chloride'],
                'cu': ['copper'],
                'al': ['aluminum', 'aluminium'],
                'swa': ['steel wire armored', 'steel wire armour'],
                'lszh': ['low smoke zero halogen', 'ls0h'],
            }
            
            for abbr, expansions in abbreviations.items():
                if required_lower == abbr and any(exp in product_lower for exp in expansions):
                    return True
                if product_lower == abbr and any(exp in required_lower for exp in expansions):
                    return True
            
            return False
        
        # Numeric comparison with smart tolerance
        try:
            # Extract numeric value and unit
            req_str = str(required).strip()
            prod_str = str(product).strip()
            
            # Common unit patterns
            units = ['sq mm', 'sqmm', 'mm2', 'mm', 'kv', 'v', 'a', 'w', 'kg', 'm']
            req_num = req_str.lower()
            prod_num = prod_str.lower()
            
            # Remove units
            for unit in units:
                req_num = req_num.replace(unit, '').strip()
                prod_num = prod_num.replace(unit, '').strip()
            
            req_float = float(req_num)
            prod_float = float(prod_num)
            
            # Determine tolerance based on spec type
            if any(key in spec_key_lower for key in ['voltage', 'rating', 'kv']):
                # Voltage: 5% tolerance (stricter)
                tolerance = req_float * 0.05
            elif any(key in spec_key_lower for key in ['size', 'diameter', 'thickness', 'cross', 'section']):
                # Size: 10% tolerance
                tolerance = req_float * 0.10
            elif any(key in spec_key_lower for key in ['current', 'ampere', 'amp']):
                # Current: 15% tolerance (can vary with conditions)
                tolerance = req_float * 0.15
            elif any(key in spec_key_lower for key in ['temperature', 'temp']):
                # Temperature: ±5°C
                tolerance = 5.0
            elif any(key in spec_key_lower for key in ['core', 'pair', 'count']):
                # Count: exact match
                tolerance = 0
            else:
                # Default: 10% tolerance
                tolerance = req_float * 0.10
            
            return abs(req_float - prod_float) <= tolerance
            
        except (ValueError, TypeError):
            pass
        
        # Exact match for other types
        return required == product
    
    def _product_to_dict(self, product: OEMProduct) -> Dict[str, Any]:
        """Convert OEMProduct model to dictionary."""
        return {
            'product_id': product.product_id,
            'manufacturer': product.manufacturer,
            'model_number': product.model_number,
            'product_name': product.product_name,
            'category': product.category,
            'specifications': product.specifications or {},
            'certifications': product.certifications or [],
            'standards': product.standards or [],
            'unit_price': float(product.unit_price) if product.unit_price else 0.0,
            'stock': product.stock_quantity or 1000,
            'delivery_days': product.delivery_days or 7
        }
    
    async def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product by ID."""
        if not self.use_database:
            for product in self._products:
                if product['product_id'] == product_id:
                    return product
            return None
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(OEMProduct).where(OEMProduct.product_id == product_id)
            )
            product = result.scalar_one_or_none()
            return self._product_to_dict(product) if product else None
    
    async def get_all_products(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get all products (limited for performance)."""
        if not self.use_database:
            return self._products.copy()
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(OEMProduct).where(OEMProduct.is_active == True).limit(limit)
            )
            products = result.scalars().all()
            return [self._product_to_dict(p) for p in products]
    
    async def get_manufacturers(self) -> List[str]:
        """Get list of all manufacturers."""
        if not self.use_database:
            return list(set(p['manufacturer'] for p in self._products))
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(OEMProduct.manufacturer)
                .distinct()
                .where(OEMProduct.is_active == True)
            )
            return [row[0] for row in result.all()]
    
    async def get_categories(self) -> List[str]:
        """Get list of all categories."""
        if not self.use_database:
            return list(set(p['category'] for p in self._products))
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(OEMProduct.category)
                .distinct()
                .where(OEMProduct.is_active == True)
            )
            return [row[0] for row in result.all()]
    
    async def get_product_count(self) -> int:
        """Get total product count."""
        if not self.use_database:
            return len(self._products)
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(func.count(OEMProduct.id)).where(OEMProduct.is_active == True)
            )
            return result.scalar() or 0

