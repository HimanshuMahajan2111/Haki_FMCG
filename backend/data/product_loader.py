"""Product data loader from CSV files."""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
import structlog

from config.settings import settings

logger = structlog.get_logger()


class ProductDataLoader:
    """Load product data from CSV files."""
    
    def __init__(self):
        """Initialize data loader."""
        self.data_dir = settings.data_dir
        self.wires_cables_dir = settings.wires_cables_dir
        self.logger = logger.bind(component="ProductDataLoader")
    
    async def load_all_products(self) -> List[Dict[str, Any]]:
        """Load all product data from CSV files.
        
        Returns:
            List of product dictionaries
        """
        self.logger.info("Loading product data")
        
        products = []
        
        # Load FMEG products
        fmeg_products = await self.load_fmeg_products()
        products.extend(fmeg_products)
        
        # Load wires and cables
        cable_products = await self.load_wire_cable_products()
        products.extend(cable_products)
        
        self.logger.info(
            "Product data loaded",
            total_products=len(products)
        )
        
        return products
    
    async def load_fmeg_products(self) -> List[Dict[str, Any]]:
        """Load FMEG products from Havells and Polycab.
        
        Returns:
            List of FMEG products
        """
        products = []
        
        # Load Havells products
        havells_dir = self.data_dir / "Havells"
        if havells_dir.exists():
            for csv_file in havells_dir.glob("*.csv"):
                df = pd.read_csv(csv_file)
                products.extend(self._process_fmeg_dataframe(df, "Havells"))
        
        # Load Polycab products
        polycab_dir = self.data_dir / "Polycab"
        if polycab_dir.exists():
            for csv_file in polycab_dir.glob("*.csv"):
                df = pd.read_csv(csv_file)
                products.extend(self._process_fmeg_dataframe(df, "Polycab"))
        
        return products
    
    async def load_wire_cable_products(self) -> List[Dict[str, Any]]:
        """Load wire and cable products.
        
        Returns:
            List of wire/cable products
        """
        products = []
        
        manufacturers = ["havells", "polycab", "kei", "finolex", "rr_kabel"]
        
        for manufacturer in manufacturers:
            mfg_dir = self.wires_cables_dir / manufacturer
            complete_file = mfg_dir / f"{manufacturer}_complete_products_*.csv"
            
            # Find the latest file
            files = list(mfg_dir.glob(f"{manufacturer}_complete_products_*.csv"))
            if files:
                df = pd.read_csv(files[0])
                products.extend(self._process_cable_dataframe(df, manufacturer))
        
        return products
    
    def _process_fmeg_dataframe(
        self,
        df: pd.DataFrame,
        brand: str
    ) -> List[Dict[str, Any]]:
        """Process FMEG dataframe into product dictionaries.
        
        Args:
            df: Pandas dataframe
            brand: Brand name
            
        Returns:
            List of product dictionaries
        """
        products = []
        
        for _, row in df.iterrows():
            product = {
                "brand": brand,
                "category": row.get("Main_Category", ""),
                "sub_category": row.get("Sub_Category", ""),
                "product_code": row.get("SKU", ""),
                "product_name": row.get("Model_Name", ""),
                "model_name": row.get("Variant_Description", ""),
                "specifications": {
                    "color": row.get("Color_Variant", ""),
                    "size": row.get("Size", ""),
                    "warranty": row.get("Warranty", ""),
                },
                "mrp": self._safe_float(row.get("MRP")),
                "selling_price": self._safe_float(row.get("Selling_Price")),
                "dealer_price": self._safe_float(row.get("Dealer_Price")),
                "certifications": row.get("Certifications", ""),
                "bis_registration": row.get("BIS_Registration", ""),
                "country_of_origin": row.get("Country_of_Origin", ""),
                "hsn_code": row.get("HSN_Code", ""),
                "image_url": row.get("Image_URL", ""),
                "datasheet_url": row.get("Datasheet_URL", ""),
            }
            
            products.append(product)
        
        return products
    
    def _process_cable_dataframe(
        self,
        df: pd.DataFrame,
        brand: str
    ) -> List[Dict[str, Any]]:
        """Process wire/cable dataframe into product dictionaries.
        
        Args:
            df: Pandas dataframe
            brand: Brand name
            
        Returns:
            List of product dictionaries
        """
        products = []
        
        for _, row in df.iterrows():
            product = {
                "brand": brand.title(),
                "category": row.get("Category", "Wires & Cables"),
                "sub_category": row.get("Type", ""),
                "product_code": row.get("Product_Code", ""),
                "product_name": row.get("Product_Name", ""),
                "specifications": {
                    "voltage_rating": row.get("Voltage_Rating", ""),
                    "conductor_material": row.get("Conductor_Material", ""),
                    "conductor_size": row.get("Conductor_Size_sqmm", ""),
                    "no_of_cores": row.get("No_of_Cores", ""),
                    "conductor_class": row.get("Conductor_Class", ""),
                    "insulation_type": row.get("Insulation_Type", ""),
                    "armour_type": row.get("Armour_Type", ""),
                    "current_rating": row.get("Current_Rating_Amps", ""),
                },
                "mrp": self._safe_float(row.get("Price_Per_Meter_INR")),
                "standard": row.get("Standard", ""),
                "hsn_code": row.get("HSN_Code", ""),
                "warranty_years": self._safe_int(row.get("Warranty_Years")),
            }
            
            products.append(product)
        
        return products
    
    def _safe_float(self, value: Any) -> float:
        """Safely convert value to float.
        
        Args:
            value: Value to convert
            
        Returns:
            Float value or None
        """
        try:
            if pd.isna(value):
                return None
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _safe_int(self, value: Any) -> int:
        """Safely convert value to int.
        
        Args:
            value: Value to convert
            
        Returns:
            Int value or None
        """
        try:
            if pd.isna(value):
                return None
            return int(value)
        except (ValueError, TypeError):
            return None
