"""
Data Loader - Loads OEM product data from CSV files

Loads wires and cables data from:
- Havells
- Polycab
- KEI
- Finolex
- RR Kabel
"""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
import structlog

logger = structlog.get_logger()


class ProductDataLoader:
    """Load OEM product data from CSV files."""
    
    def __init__(self, base_path: str = ".."):
        """Initialize data loader.
        
        Args:
            base_path: Base path to data directories
        """
        self.base_path = Path(base_path)
        self.wires_cables_path = self.base_path / "wires_cables_data"
        self.fmeg_path = self.base_path / "FMEG_data"
        self.logger = logger.bind(component="ProductDataLoader")
    
    def load_all_products(self) -> List[Dict[str, Any]]:
        """Load all OEM products from CSV files.
        
        Returns:
            List of product dictionaries
        """
        all_products = []
        
        # Load from each manufacturer
        manufacturers = {
            'Havells': 'havells',
            'Polycab': 'polycab',
            'KEI': 'kei',
            'Finolex': 'finolex',
            'RR Kabel': 'rr_kabel'
        }
        
        for manufacturer_name, folder_name in manufacturers.items():
            products = self._load_manufacturer_data(manufacturer_name, folder_name)
            all_products.extend(products)
            self.logger.info(
                f"Loaded {len(products)} products from {manufacturer_name}",
                manufacturer=manufacturer_name,
                product_count=len(products)
            )
        
        self.logger.info(
            f"Total products loaded: {len(all_products)}",
            total_count=len(all_products)
        )
        
        return all_products
    
    def _load_manufacturer_data(
        self, 
        manufacturer: str, 
        folder: str
    ) -> List[Dict[str, Any]]:
        """Load data for a specific manufacturer.
        
        Args:
            manufacturer: Manufacturer name
            folder: Folder name
            
        Returns:
            List of products
        """
        manufacturer_path = self.wires_cables_path / folder
        
        if not manufacturer_path.exists():
            self.logger.warning(
                f"Manufacturer directory not found: {manufacturer_path}",
                manufacturer=manufacturer
            )
            return []
        
        # Look for complete products CSV
        csv_files = list(manufacturer_path.glob(f"{folder}_complete_products_*.csv"))
        
        if not csv_files:
            # Fallback to cables or wires CSV
            csv_files = list(manufacturer_path.glob(f"{folder}_cables_*.csv"))
        
        if not csv_files:
            csv_files = list(manufacturer_path.glob(f"{folder}_wires_*.csv"))
        
        if not csv_files:
            self.logger.warning(
                f"No product CSV files found for {manufacturer}",
                manufacturer=manufacturer,
                path=str(manufacturer_path)
            )
            return []
        
        # Use the most recent file
        csv_file = max(csv_files, key=lambda p: p.stat().st_mtime)
        
        try:
            return self._parse_csv_file(csv_file, manufacturer)
        except Exception as e:
            self.logger.error(
                f"Failed to load {manufacturer} data: {e}",
                manufacturer=manufacturer,
                error=str(e)
            )
            return []
    
    def _parse_csv_file(
        self, 
        csv_path: Path, 
        manufacturer: str
    ) -> List[Dict[str, Any]]:
        """Parse CSV file and extract products.
        
        Args:
            csv_path: Path to CSV file
            manufacturer: Manufacturer name
            
        Returns:
            List of products
        """
        try:
            df = pd.read_csv(csv_path, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(csv_path, encoding='latin-1')
        
        products = []
        
        for idx, row in df.iterrows():
            try:
                product = self._extract_product_from_row(row, manufacturer, idx)
                if product:
                    products.append(product)
            except Exception as e:
                self.logger.warning(
                    f"Failed to parse row {idx}: {e}",
                    row_index=idx,
                    error=str(e)
                )
                continue
        
        return products
    
    def _extract_product_from_row(
        self, 
        row: pd.Series, 
        manufacturer: str,
        idx: int
    ) -> Dict[str, Any]:
        """Extract product data from CSV row.
        
        Args:
            row: DataFrame row
            manufacturer: Manufacturer name
            idx: Row index
            
        Returns:
            Product dictionary
        """
        # Extract basic info and ensure unique product ID
        base_code = str(row.get('Product_Code', f'{idx:04d}'))
        # Add manufacturer prefix and row index to ensure complete uniqueness
        product_code = f"{manufacturer[:3].upper()}-{base_code}-{idx:04d}"
        
        product_name = str(row.get('Product_Name', 'Unknown Product'))
        
        # Clean product name - remove special characters and Unicode symbols
        product_name = product_name.encode('ascii', 'ignore').decode('ascii')
        product_name = ' '.join(product_name.split())  # Normalize whitespace
        # Truncate if too long
        if len(product_name) > 300:
            product_name = product_name[:297] + '...'
        
        category = str(row.get('Category', 'Unknown'))
        
        # Infer category type
        category_type = self._infer_category_type(category, product_name)
        
        # Extract specifications
        specifications = {}
        
        # Voltage rating
        if 'Voltage_Rating' in row and pd.notna(row['Voltage_Rating']):
            specifications['voltage_rating'] = str(row['Voltage_Rating'])
        
        # Conductor
        if 'Conductor_Material' in row and pd.notna(row['Conductor_Material']):
            specifications['conductor_material'] = str(row['Conductor_Material'])
        
        if 'Conductor_Size_sqmm' in row and pd.notna(row['Conductor_Size_sqmm']):
            specifications['conductor_size'] = str(row['Conductor_Size_sqmm']) + ' sq mm'
        
        if 'No_of_Cores' in row and pd.notna(row['No_of_Cores']):
            specifications['cores'] = str(row['No_of_Cores'])
        
        # Insulation
        if 'Insulation_Type' in row and pd.notna(row['Insulation_Type']):
            specifications['insulation'] = str(row['Insulation_Type'])
        
        # Temperature
        if 'Max_Conductor_Temp_C' in row and pd.notna(row['Max_Conductor_Temp_C']):
            specifications['temperature_rating'] = str(row['Max_Conductor_Temp_C']) + 'C'
        
        # Armour
        if 'Armour_Type' in row and pd.notna(row['Armour_Type']):
            armour = str(row['Armour_Type'])
            if armour.lower() != 'unarmoured':
                specifications['armour'] = armour
        
        # Standards
        standards = []
        if 'Standard' in row and pd.notna(row['Standard']):
            standards = [s.strip() for s in str(row['Standard']).split(',')]
        
        # Certifications
        certifications = []
        if 'BIS' in str(row.get('Standard', '')):
            certifications.append('BIS')
        if 'IEC' in str(row.get('Standard', '')):
            certifications.append('IEC')
        
        # Pricing
        unit_price = 0.0
        if 'Price_Per_Meter_INR' in row and pd.notna(row['Price_Per_Meter_INR']):
            try:
                unit_price = float(row['Price_Per_Meter_INR'])
            except:
                unit_price = 0.0
        
        # Current rating
        if 'Current_Rating_Amps' in row and pd.notna(row['Current_Rating_Amps']):
            try:
                specifications['current_rating'] = str(int(float(row['Current_Rating_Amps']))) + 'A'
            except:
                pass
        
        # Create product entry
        product = {
            'product_id': product_code,
            'manufacturer': manufacturer,
            'model_number': product_code,
            'product_name': product_name,
            'category': category_type,
            'specifications': specifications,
            'certifications': certifications,
            'standards': standards,
            'unit_price': unit_price,
            'stock': 1000,  # Default stock
            'delivery_days': 7  # Default delivery
        }
        
        return product
    
    def _infer_category_type(self, category: str, product_name: str) -> str:
        """Infer standardized category type.
        
        Args:
            category: Original category
            product_name: Product name
            
        Returns:
            Standardized category
        """
        text = (category + ' ' + product_name).lower()
        
        # Category mapping
        if 'solar' in text:
            return 'Solar Cables'
        elif 'power' in text and 'lt' in text:
            return 'Power Cables - LT'
        elif 'power' in text and 'ht' in text:
            return 'Power Cables - HT'
        elif 'control' in text:
            return 'Control Cables'
        elif 'signal' in text or 'railway' in text:
            return 'Signaling Cables'
        elif 'submersible' in text:
            return 'Submersible Cables'
        elif 'flexible' in text or 'flex' in text:
            return 'Flexible Cables'
        elif 'armoured' in text:
            return 'Armoured Cables'
        elif 'instrument' in text:
            return 'Instrumentation Cables'
        elif 'telecom' in text or 'telephone' in text:
            return 'Telecom Cables'
        else:
            return category
