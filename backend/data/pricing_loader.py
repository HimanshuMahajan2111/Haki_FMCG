"""Pricing data loader with validation."""
import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import structlog

from config.settings import settings
from data.base_loader import BaseDataLoader, ValidationResult

logger = structlog.get_logger()


class PricingDataLoader(BaseDataLoader):
    """Load and validate pricing data from CSV files."""
    
    def __init__(self):
        """Initialize pricing loader."""
        super().__init__("PricingDataLoader")
        self.pricing_dir = Path(settings.data_dir)
        
        # Define required fields for pricing
        self.required_fields = {
            'product_id', 'price'
        }
        
        # Define optional fields
        self.optional_fields = {
            'brand', 'category', 'base_price', 'discount', 
            'mrp', 'selling_price', 'dealer_price', 'distributor_price',
            'margin_percentage', 'gst_rate', 'hsn_code', 'currency',
            'effective_date', 'valid_until', 'min_order_quantity',
            'volume_discount', 'seasonal_discount', 'competitor_price'
        }
    
    async def load(self) -> List[Dict[str, Any]]:
        """Load all pricing data with validation.
        
        Returns:
            List of validated pricing records
        """
        self.logger.info("Loading pricing data with validation")
        
        pricing_records = []
        
        # Load pricing from product CSV files (extract price columns)
        try:
            fmeg_pricing = await self._load_fmeg_pricing()
            pricing_records.extend(fmeg_pricing)
        except Exception as e:
            self.logger.error("Failed to load FMEG pricing", error=str(e))
        
        # Load pricing from wire/cable files
        try:
            cable_pricing = await self._load_cable_pricing()
            pricing_records.extend(cable_pricing)
        except Exception as e:
            self.logger.error("Failed to load cable pricing", error=str(e))
        
        # Load standards pricing if available
        try:
            standards_pricing = await self._load_standards_pricing()
            pricing_records.extend(standards_pricing)
        except Exception as e:
            self.logger.error("Failed to load standards pricing", error=str(e))
        
        # Validate all pricing records
        validation_result = self.validate_data(pricing_records)
        self.log_validation_summary(validation_result)
        
        self.logger.info(
            "Pricing data loaded",
            total_records=len(pricing_records),
            valid_records=len(pricing_records) - validation_result.records_failed
        )
        
        return pricing_records
    
    async def _load_fmeg_pricing(self) -> List[Dict[str, Any]]:
        """Load FMEG product pricing from Havells and Polycab.
        
        Returns:
            List of pricing records
        """
        pricing_records = []
        
        # Load Havells pricing
        havells_dir = self.pricing_dir / "Havells"
        if havells_dir.exists():
            for csv_file in havells_dir.glob("*.csv"):
                try:
                    df = pd.read_csv(csv_file)
                    category = self._extract_category_from_filename(csv_file.name)
                    
                    for idx, row in df.iterrows():
                        # Extract pricing information
                        product_id = f"H-{category}-{idx}"
                        model = str(row.get('Model_Name', row.get('SKU', '')))
                        
                        pricing = {
                            'product_id': product_id,
                            'brand': 'Havells',
                            'category': category,
                            'model': model,
                            'price': self._parse_price(row.get('Selling_Price', 0)),
                            'mrp': self._parse_price(row.get('MRP', 0)),
                            'selling_price': self._parse_price(row.get('Selling_Price', 0)),
                            'dealer_price': self._parse_price(row.get('Dealer_Price', 0)),
                            'discount': self._calculate_discount(
                                row.get('MRP'), 
                                row.get('Selling_Price')
                            ),
                            'currency': 'INR',
                            'hsn_code': str(row.get('HSN_Code', '')),
                        }
                        pricing_records.append(pricing)
                    
                    self.logger.info(f"Loaded {len(df)} pricing records from {csv_file.name}")
                except Exception as e:
                    self.logger.error(f"Error loading {csv_file.name}", error=str(e))
        
        # Load Polycab pricing
        polycab_dir = self.pricing_dir / "Polycab"
        if polycab_dir.exists():
            for csv_file in polycab_dir.glob("*.csv"):
                try:
                    df = pd.read_csv(csv_file)
                    category = self._extract_category_from_filename(csv_file.name)
                    
                    for idx, row in df.iterrows():
                        product_id = f"P-{category}-{idx}"
                        model = str(row.get('Model_Name', row.get('SKU', '')))
                        
                        pricing = {
                            'product_id': product_id,
                            'brand': 'Polycab',
                            'category': category,
                            'model': model,
                            'price': self._parse_price(row.get('Selling_Price', 0)),
                            'mrp': self._parse_price(row.get('MRP', 0)),
                            'selling_price': self._parse_price(row.get('Selling_Price', 0)),
                            'dealer_price': self._parse_price(row.get('Dealer_Price', 0)),
                            'discount': self._calculate_discount(
                                row.get('MRP'), 
                                row.get('Selling_Price')
                            ),
                            'currency': 'INR',
                            'hsn_code': str(row.get('HSN_Code', '')),
                        }
                        pricing_records.append(pricing)
                    
                    self.logger.info(f"Loaded {len(df)} pricing records from {csv_file.name}")
                except Exception as e:
                    self.logger.error(f"Error loading {csv_file.name}", error=str(e))
        
        return pricing_records
    
    async def _load_cable_pricing(self) -> List[Dict[str, Any]]:
        """Load wire and cable pricing.
        
        Returns:
            List of pricing records
        """
        pricing_records = []
        wires_cables_dir = Path(settings.wires_cables_dir)
        brands = ['havells', 'polycab', 'kei', 'finolex', 'rr_kabel']
        
        for brand in brands:
            brand_dir = wires_cables_dir / brand
            if not brand_dir.exists():
                continue
            
            for csv_file in brand_dir.glob("*.csv"):
                try:
                    df = pd.read_csv(csv_file)
                    
                    for idx, row in df.iterrows():
                        product_id = f"{brand.upper()}-CABLE-{idx}"
                        
                        pricing = {
                            'product_id': product_id,
                            'brand': brand.replace('_', ' ').title(),
                            'category': 'Wires & Cables',
                            'model': str(row.get('Product_Code', row.get('SKU', ''))),
                            'price': self._parse_price(row.get('Price', row.get('price', 0))),
                            'selling_price': self._parse_price(row.get('Selling_Price', 0)),
                            'currency': 'INR',
                        }
                        pricing_records.append(pricing)
                    
                    self.logger.info(f"Loaded {len(df)} cable pricing from {csv_file.name}")
                except Exception as e:
                    self.logger.error(f"Error loading {csv_file.name}", error=str(e))
        
        return pricing_records
    
    async def _load_standards_pricing(self) -> List[Dict[str, Any]]:
        """Load standards-related pricing data.
        
        Returns:
            List of pricing records
        """
        pricing_records = []
        standards_dir = Path(settings.standards_dir)
        file_path = standards_dir / "wire_cable_standards_pricing_20251215_013650.csv"
        
        if not self.check_file_exists(file_path):
            return []
        
        try:
            df = pd.read_csv(file_path)
            
            for idx, row in df.iterrows():
                pricing = {
                    'product_id': f"STD-{idx}",
                    'standard_code': str(row.get('standard', row.get('Standard', ''))),
                    'category': 'Standards & Certification',
                    'price': self._parse_price_range(row.get('pricing_range', '')),
                    'testing_cost': str(row.get('testing_cost_range', '')),
                    'certification_cost': str(row.get('certification_cost_range', '')),
                    'total_cost': str(row.get('total_cost_estimate', '')),
                    'currency': 'INR',
                }
                pricing_records.append(pricing)
            
            self.logger.info(f"Loaded {len(pricing_records)} standards pricing records")
        except Exception as e:
            self.logger.error("Error loading standards pricing", error=str(e))
        
        return pricing_records
    
    def _parse_price(self, price_value: Any) -> float:
        """Parse price from various formats.
        
        Args:
            price_value: Price value in any format
            
        Returns:
            Float price value
        """
        if pd.isna(price_value):
            return 0.0
        
        try:
            # Convert to string and remove currency symbols
            price_str = str(price_value).replace('₹', '').replace(',', '').strip()
            if price_str and price_str != 'nan' and price_str != 'N/A':
                return float(price_str)
        except (ValueError, AttributeError):
            pass
        
        return 0.0
    
    def _parse_price_range(self, price_range: str) -> float:
        """Parse price range and return average.
        
        Args:
            price_range: Price range string like "₹10,000 - ₹15,000"
            
        Returns:
            Average price
        """
        if pd.isna(price_range) or not price_range:
            return 0.0
        
        try:
            # Extract numbers from range
            import re
            numbers = re.findall(r'[\d,]+', str(price_range))
            if numbers:
                prices = [float(n.replace(',', '')) for n in numbers]
                return sum(prices) / len(prices)
        except (ValueError, AttributeError):
            pass
        
        return 0.0
    
    def _calculate_discount(self, mrp: Any, selling_price: Any) -> float:
        """Calculate discount percentage.
        
        Args:
            mrp: Maximum Retail Price
            selling_price: Actual Selling Price
            
        Returns:
            Discount percentage
        """
        mrp_val = self._parse_price(mrp)
        selling_val = self._parse_price(selling_price)
        
        if mrp_val > 0 and selling_val > 0 and mrp_val > selling_val:
            return round(((mrp_val - selling_val) / mrp_val) * 100, 2)
        
        return 0.0
    
    def _extract_category_from_filename(self, filename: str) -> str:
        """Extract category from filename.
        
        Args:
            filename: CSV filename
            
        Returns:
            Category name
        """
        # Remove brand prefix and file extension
        parts = filename.replace('Havells_', '').replace('Polycab_', '').replace('.csv', '')
        # Remove timestamp suffix
        parts = '_'.join(parts.split('_')[:-1]) if parts.split('_')[-1].isdigit() else parts
        return parts.replace('_', ' ')
