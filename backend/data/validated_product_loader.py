"""Enhanced product data loader with validation."""
import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import structlog

from config.settings import settings
from data.base_loader import BaseDataLoader, ValidationResult

logger = structlog.get_logger()


class ValidatedProductLoader(BaseDataLoader):
    """Load and validate product data from CSV files."""
    
    def __init__(self):
        """Initialize product loader."""
        super().__init__("ValidatedProductLoader")
        self.data_dir = Path(settings.data_dir)
        self.wires_cables_dir = Path(settings.wires_cables_dir)
        
        # Define required fields for products
        self.required_fields = {
            'name', 'category', 'brand'
        }
        
        # Define optional fields
        self.optional_fields = {
            'price', 'specifications', 'description', 'model',
            'voltage', 'current', 'power', 'standard', 'material',
            'application', 'features', 'warranty', 'dimensions'
        }
    
    async def load(self) -> List[Dict[str, Any]]:
        """Load all product data with validation.
        
        Returns:
            List of validated products
        """
        self.logger.info("Loading product data with validation")
        
        products = []
        
        # Load FMEG products
        try:
            fmeg_products = await self._load_fmeg_products()
            products.extend(fmeg_products)
        except Exception as e:
            self.logger.error("Failed to load FMEG products", error=str(e))
        
        # Load wires and cables
        try:
            cable_products = await self._load_wire_cable_products()
            products.extend(cable_products)
        except Exception as e:
            self.logger.error("Failed to load cable products", error=str(e))
        
        # Validate all products
        validation_result = self.validate_data(products)
        self.log_validation_summary(validation_result)
        
        # Filter out invalid products
        if not validation_result.is_valid:
            self.logger.warning(
                "Filtering out invalid products",
                total=len(products),
                failed=validation_result.records_failed
            )
        
        self.logger.info(
            "Product data loaded",
            total_products=len(products),
            valid_products=len(products) - validation_result.records_failed
        )
        
        return products
    
    async def _load_fmeg_products(self) -> List[Dict[str, Any]]:
        """Load FMEG products from Havells and Polycab.
        
        Returns:
            List of FMEG products
        """
        products = []
        
        # Load Havells products
        havells_dir = self.data_dir / "Havells"
        if havells_dir.exists():
            for csv_file in havells_dir.glob("*.csv"):
                try:
                    df = pd.read_csv(csv_file)
                    category = self._extract_category_from_filename(csv_file.name)
                    
                    for _, row in df.iterrows():
                        # Extract product name from Model_Name or Variant_Description
                        name = str(row.get('Model_Name', row.get('Variant_Description', 'Unknown')))
                        if pd.isna(name) or name == 'nan' or not name.strip():
                            name = str(row.get('Variant_Description', f"{category} Product"))
                        
                        product = {
                            'name': name,
                            'category': category or str(row.get('Main_Category', row.get('Sub_Category', 'Uncategorized'))),
                            'brand': str(row.get('Brand', 'Havells')),
                            'model': str(row.get('SKU', row.get('Model_Name', ''))),
                            'price': self._parse_price(row.get('Selling_Price', row.get('MRP', row.get('Dealer_Price')))),
                            'specifications': self._extract_specifications(row),
                            'description': str(row.get('Product_Description', '')),
                        }
                        products.append(product)
                    
                    self.logger.info(f"Loaded {len(df)} products from {csv_file.name}")
                except Exception as e:
                    self.logger.error(f"Error loading {csv_file.name}", error=str(e))
        
        # Load Polycab products
        polycab_dir = self.data_dir / "Polycab"
        if polycab_dir.exists():
            for csv_file in polycab_dir.glob("*.csv"):
                try:
                    df = pd.read_csv(csv_file)
                    category = self._extract_category_from_filename(csv_file.name)
                    
                    for _, row in df.iterrows():
                        # Extract product name from Model_Name or Variant_Description
                        name = str(row.get('Model_Name', row.get('Variant_Description', 'Unknown')))
                        if pd.isna(name) or name == 'nan' or not name.strip():
                            name = str(row.get('Variant_Description', f"{category} Product"))
                        
                        product = {
                            'name': name,
                            'category': category or str(row.get('Main_Category', row.get('Sub_Category', 'Uncategorized'))),
                            'brand': str(row.get('Brand', 'Polycab')),
                            'model': str(row.get('SKU', row.get('Model_Name', ''))),
                            'price': self._parse_price(row.get('Selling_Price', row.get('MRP', row.get('Dealer_Price')))),
                            'specifications': self._extract_specifications(row),
                            'description': str(row.get('Product_Description', '')),
                        }
                        products.append(product)
                    
                    self.logger.info(f"Loaded {len(df)} products from {csv_file.name}")
                except Exception as e:
                    self.logger.error(f"Error loading {csv_file.name}", error=str(e))
        
        return products
    
    async def _load_wire_cable_products(self) -> List[Dict[str, Any]]:
        """Load wire and cable products from all brands.
        
        Returns:
            List of wire/cable products
        """
        products = []
        brands = ['havells', 'polycab', 'kei', 'finolex', 'rr_kabel']
        
        for brand in brands:
            brand_dir = self.wires_cables_dir / brand
            if not brand_dir.exists():
                self.logger.warning(f"Brand directory not found: {brand}")
                continue
            
            # Load main product files
            for csv_file in brand_dir.glob("*_complete_products_*.csv"):
                try:
                    df = pd.read_csv(csv_file)
                    
                    for _, row in df.iterrows():
                        product = {
                            'name': str(row.get('Product Name', row.get('name', ''))),
                            'category': 'Wires & Cables',
                            'brand': brand.replace('_', ' ').title(),
                            'specifications': self._extract_cable_specifications(row),
                            'standard': str(row.get('Standard', row.get('standard', ''))),
                            'voltage': str(row.get('Voltage', row.get('voltage', ''))),
                            'description': str(row.get('Description', '')),
                        }
                        products.append(product)
                    
                    self.logger.info(f"Loaded {len(df)} products from {csv_file.name}")
                except Exception as e:
                    self.logger.error(f"Error loading {csv_file.name}", error=str(e))
        
        return products
    
    def _extract_category_from_filename(self, filename: str) -> str:
        """Extract category from filename.
        
        Args:
            filename: CSV filename
            
        Returns:
            Category name
        """
        # Remove brand prefix and timestamp
        name = filename.replace('.csv', '')
        parts = name.split('_')
        
        # Remove brand and date parts
        category_parts = [p for p in parts if not p.isdigit()]
        if category_parts:
            return ' '.join(category_parts[1:]).title()
        return 'Unknown'
    
    def _parse_price(self, price_value: Any) -> Optional[float]:
        """Parse price value to float.
        
        Args:
            price_value: Price value (can be string or number)
            
        Returns:
            Parsed price or None
        """
        if pd.isna(price_value):
            return None
        
        try:
            # Remove currency symbols and commas
            if isinstance(price_value, str):
                price_str = price_value.replace('₹', '').replace(',', '').strip()
                return float(price_str)
            return float(price_value)
        except (ValueError, TypeError):
            return None
    
    def _extract_specifications(self, row: pd.Series) -> Dict[str, Any]:
        """Extract specifications from row.
        
        Args:
            row: Pandas Series row
            
        Returns:
            Dictionary of specifications
        """
        specs = {}
        spec_columns = ['Voltage', 'Current', 'Power', 'Capacity', 'RPM', 
                       'Frequency', 'Efficiency', 'Material', 'Color']
        
        for col in spec_columns:
            if col in row.index and not pd.isna(row[col]):
                specs[col.lower()] = str(row[col])
        
        return specs
    
    def _extract_cable_specifications(self, row: pd.Series) -> Dict[str, Any]:
        """Extract cable-specific specifications.
        
        Args:
            row: Pandas Series row
            
        Returns:
            Dictionary of specifications
        """
        specs = {}
        cable_columns = ['Conductor', 'Insulation', 'Cores', 'Size', 
                        'Current Rating', 'Cross Section', 'Armour']
        
        for col in cable_columns:
            if col in row.index and not pd.isna(row[col]):
                specs[col.lower().replace(' ', '_')] = str(row[col])
        
        return specs
