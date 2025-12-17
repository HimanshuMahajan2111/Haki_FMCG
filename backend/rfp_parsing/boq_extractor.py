"""
BOQ Extractor - Extract Bill of Quantities from RFP documents.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import pandas as pd
import re
import structlog

logger = structlog.get_logger()


@dataclass
class BOQItem:
    """Bill of Quantities item."""
    item_no: str
    description: str
    quantity: float
    unit: str
    specifications: Dict[str, Any] = None
    rate: Optional[float] = None
    amount: Optional[float] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    make: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'item_no': self.item_no,
            'description': self.description,
            'quantity': self.quantity,
            'unit': self.unit,
            'specifications': self.specifications or {},
            'rate': self.rate,
            'amount': self.amount,
            'category': self.category,
            'brand': self.brand,
            'make': self.make
        }


class BOQExtractor:
    """Extract Bill of Quantities from tables."""
    
    def __init__(self):
        """Initialize BOQ extractor."""
        self.logger = logger.bind(component="BOQExtractor")
        
        # Common BOQ column patterns
        self.column_patterns = {
            'item_no': [r'item\s*no', r'sl\s*no', r'sr\s*no', r'#', r's\.n'],
            'description': [r'description', r'item\s*description', r'particulars', r'work\s*description'],
            'quantity': [r'quantity', r'qty', r'nos', r'no\.'],
            'unit': [r'unit', r'uom', r'u\.o\.m'],
            'rate': [r'rate', r'unit\s*rate', r'price'],
            'amount': [r'amount', r'total', r'value'],
            'specifications': [r'spec', r'specification', r'technical\s*spec'],
            'brand': [r'brand', r'make', r'manufacturer'],
        }
    
    def is_boq_table(self, df: pd.DataFrame) -> bool:
        """Check if DataFrame is likely a BOQ table.
        
        Args:
            df: DataFrame to check
            
        Returns:
            True if likely a BOQ table
        """
        if df is None or df.empty:
            return False
        
        # Check if table has typical BOQ columns
        columns = [str(col).lower() for col in df.columns]
        
        # Must have item/description and quantity
        has_item = any(
            any(re.search(pattern, col, re.IGNORECASE) for pattern in self.column_patterns['item_no'])
            for col in columns
        )
        
        has_description = any(
            any(re.search(pattern, col, re.IGNORECASE) for pattern in self.column_patterns['description'])
            for col in columns
        )
        
        has_quantity = any(
            any(re.search(pattern, col, re.IGNORECASE) for pattern in self.column_patterns['quantity'])
            for col in columns
        )
        
        # BOQ should have at least item number/description and quantity
        return (has_item or has_description) and has_quantity
    
    def extract_from_table(self, df: pd.DataFrame) -> List[BOQItem]:
        """Extract BOQ items from a DataFrame.
        
        Args:
            df: DataFrame containing BOQ data
            
        Returns:
            List of BOQItem objects
        """
        if not self.is_boq_table(df):
            self.logger.debug("Table is not a BOQ table")
            return []
        
        self.logger.info("Extracting BOQ from table", rows=len(df))
        
        # Map columns to BOQ fields
        column_mapping = self._map_columns(df)
        
        boq_items = []
        
        for idx, row in df.iterrows():
            try:
                item = self._extract_item(row, column_mapping, idx)
                if item:
                    boq_items.append(item)
            except Exception as e:
                self.logger.warning(
                    "Failed to extract BOQ item",
                    row_index=idx,
                    error=str(e)
                )
        
        self.logger.info("BOQ extraction completed", items_extracted=len(boq_items))
        
        return boq_items
    
    def _map_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """Map DataFrame columns to BOQ fields.
        
        Args:
            df: DataFrame
            
        Returns:
            Mapping of field names to column names
        """
        mapping = {}
        columns = {col: str(col).lower() for col in df.columns}
        
        for field, patterns in self.column_patterns.items():
            for col, col_lower in columns.items():
                if any(re.search(pattern, col_lower, re.IGNORECASE) for pattern in patterns):
                    mapping[field] = col
                    break
        
        return mapping
    
    def _extract_item(
        self,
        row: pd.Series,
        column_mapping: Dict[str, str],
        row_idx: int
    ) -> Optional[BOQItem]:
        """Extract a single BOQ item from a row.
        
        Args:
            row: DataFrame row
            column_mapping: Column to field mapping
            row_idx: Row index
            
        Returns:
            BOQItem or None if invalid
        """
        # Get item number
        item_no = self._get_value(row, column_mapping, 'item_no')
        if not item_no:
            item_no = f"ITEM_{row_idx + 1}"
        
        # Get description (required)
        description = self._get_value(row, column_mapping, 'description')
        if not description:
            return None
        
        # Get quantity (required)
        quantity_str = self._get_value(row, column_mapping, 'quantity')
        quantity = self._parse_number(quantity_str)
        if quantity is None or quantity <= 0:
            return None
        
        # Get unit
        unit = self._get_value(row, column_mapping, 'unit') or 'unit'
        
        # Get optional fields
        rate_str = self._get_value(row, column_mapping, 'rate')
        rate = self._parse_number(rate_str)
        
        amount_str = self._get_value(row, column_mapping, 'amount')
        amount = self._parse_number(amount_str)
        
        brand = self._get_value(row, column_mapping, 'brand')
        
        specifications = self._extract_specifications(description)
        
        return BOQItem(
            item_no=str(item_no).strip(),
            description=description.strip(),
            quantity=quantity,
            unit=unit.strip(),
            specifications=specifications,
            rate=rate,
            amount=amount,
            brand=brand
        )
    
    def _get_value(
        self,
        row: pd.Series,
        column_mapping: Dict[str, str],
        field: str
    ) -> Optional[str]:
        """Get value from row using column mapping.
        
        Args:
            row: DataFrame row
            column_mapping: Column mapping
            field: Field name
            
        Returns:
            Value as string or None
        """
        if field in column_mapping:
            col = column_mapping[field]
            value = row.get(col)
            if pd.notna(value):
                return str(value).strip()
        return None
    
    def _parse_number(self, value: Optional[str]) -> Optional[float]:
        """Parse numeric value from string.
        
        Args:
            value: String value
            
        Returns:
            Float value or None
        """
        if not value:
            return None
        
        try:
            # Remove common formatting
            cleaned = re.sub(r'[^\d.,\-]', '', str(value))
            cleaned = cleaned.replace(',', '')
            
            if cleaned:
                return float(cleaned)
        except (ValueError, AttributeError):
            pass
        
        return None
    
    def _extract_specifications(self, description: str) -> Dict[str, Any]:
        """Extract specifications from description text.
        
        Args:
            description: Item description
            
        Returns:
            Dictionary of specifications
        """
        specs = {}
        
        # Common specification patterns
        patterns = {
            'size': r'(\d+\.?\d*)\s*(mm|cm|m|inch|")',
            'voltage': r'(\d+)\s*V',
            'power': r'(\d+\.?\d*)\s*(W|KW|HP)',
            'capacity': r'(\d+\.?\d*)\s*(L|litre|liter|ton)',
            'rating': r'(\d+)\s*star',
        }
        
        for spec_name, pattern in patterns.items():
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                specs[spec_name] = match.group(0)
        
        return specs
    
    def extract_from_multiple_tables(
        self,
        tables: List[pd.DataFrame]
    ) -> List[BOQItem]:
        """Extract BOQ items from multiple tables.
        
        Args:
            tables: List of DataFrames
            
        Returns:
            Combined list of BOQItem objects
        """
        all_items = []
        
        for table_idx, table in enumerate(tables):
            self.logger.debug(
                "Processing table for BOQ",
                table_index=table_idx,
                rows=len(table)
            )
            
            items = self.extract_from_table(table)
            all_items.extend(items)
        
        return all_items
    
    def to_dataframe(self, boq_items: List[BOQItem]) -> pd.DataFrame:
        """Convert BOQ items to DataFrame.
        
        Args:
            boq_items: List of BOQItem objects
            
        Returns:
            DataFrame with BOQ data
        """
        if not boq_items:
            return pd.DataFrame()
        
        data = [item.to_dict() for item in boq_items]
        return pd.DataFrame(data)
