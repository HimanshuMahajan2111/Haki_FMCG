"""Historical RFP data loader with validation."""
import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import structlog

from config.settings import settings
from data.base_loader import BaseDataLoader

logger = structlog.get_logger()


class HistoricalRFPLoader(BaseDataLoader):
    """Load and validate historical RFP data."""
    
    def __init__(self):
        """Initialize historical RFP loader."""
        super().__init__("HistoricalRFPLoader")
        self.rfp_dir = Path(settings.rfp_input_dir)
        
        # Required fields for historical RFP records
        self.required_fields = {
            'rfp_id', 'client_name', 'rfp_date'
        }
        
        self.optional_fields = {
            'title', 'requirements', 'products_quoted', 'total_value',
            'status', 'win_loss', 'competitors', 'feedback',
            'delivery_timeline', 'payment_terms', 'technical_specs',
            'pricing_strategy', 'discount_offered', 'notes'
        }
    
    async def load(self) -> List[Dict[str, Any]]:
        """Load historical RFP data with validation.
        
        Returns:
            List of historical RFP records
        """
        self.logger.info("Loading historical RFP data with validation")
        
        historical_rfps = []
        
        # Try to load from various sources
        # 1. Look for historical RFP CSV/JSON files
        csv_file = self.rfp_dir.parent / "historical_rfps.csv"
        if csv_file.exists():
            csv_data = await self._load_from_csv(csv_file)
            historical_rfps.extend(csv_data)
        
        json_file = self.rfp_dir.parent / "historical_rfps.json"
        if json_file.exists():
            json_data = await self._load_from_json(json_file)
            historical_rfps.extend(json_data)
        
        # 2. If no historical data files exist, create sample structure
        if not historical_rfps:
            self.logger.warning("No historical RFP data files found")
            historical_rfps = self._create_sample_structure()
        
        # Validate the data
        if historical_rfps:
            validation_result = self.validate_data(historical_rfps)
            self.log_validation_summary(validation_result)
        
        self.logger.info(f"Loaded {len(historical_rfps)} historical RFP records")
        return historical_rfps
    
    async def _load_from_csv(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load historical RFPs from CSV.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            List of RFP records
        """
        try:
            df = pd.read_csv(file_path)
            rfps = []
            
            for _, row in df.iterrows():
                rfp = {
                    'rfp_id': str(row.get('RFP ID', row.get('rfp_id', ''))),
                    'client_name': str(row.get('Client Name', row.get('client', ''))),
                    'rfp_date': str(row.get('Date', row.get('rfp_date', ''))),
                    'title': str(row.get('Title', '')),
                    'requirements': self._parse_json_field(row.get('Requirements', '{}')),
                    'products_quoted': self._parse_json_field(row.get('Products', '[]')),
                    'total_value': self._parse_float(row.get('Total Value', 0)),
                    'status': str(row.get('Status', '')),
                    'win_loss': str(row.get('Win/Loss', '')),
                    'competitors': str(row.get('Competitors', '')),
                    'feedback': str(row.get('Feedback', '')),
                    'delivery_timeline': str(row.get('Delivery Timeline', '')),
                    'payment_terms': str(row.get('Payment Terms', '')),
                    'pricing_strategy': str(row.get('Pricing Strategy', '')),
                    'discount_offered': self._parse_float(row.get('Discount %', 0)),
                    'notes': str(row.get('Notes', '')),
                }
                rfps.append(rfp)
            
            self.logger.info(f"Loaded {len(rfps)} RFPs from CSV")
            return rfps
        except Exception as e:
            self.logger.error(f"Error loading CSV: {file_path}", error=str(e))
            return []
    
    async def _load_from_json(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load historical RFPs from JSON.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            List of RFP records
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                self.logger.info(f"Loaded {len(data)} RFPs from JSON")
                return data
            elif isinstance(data, dict) and 'rfps' in data:
                rfps = data['rfps']
                self.logger.info(f"Loaded {len(rfps)} RFPs from JSON")
                return rfps
            else:
                self.logger.warning("Unexpected JSON structure")
                return []
        except Exception as e:
            self.logger.error(f"Error loading JSON: {file_path}", error=str(e))
            return []
    
    def _create_sample_structure(self) -> List[Dict[str, Any]]:
        """Create sample structure for historical RFPs.
        
        Returns:
            List with sample RFP structure
        """
        sample = {
            'rfp_id': 'SAMPLE-001',
            'client_name': 'Sample Client',
            'rfp_date': datetime.now().strftime('%Y-%m-%d'),
            'title': 'Sample RFP - Please update with actual data',
            'requirements': [],
            'products_quoted': [],
            'total_value': 0.0,
            'status': 'Not Available',
            'win_loss': 'N/A',
            'competitors': '',
            'feedback': 'Historical data not yet populated',
            'delivery_timeline': '',
            'payment_terms': '',
            'pricing_strategy': '',
            'discount_offered': 0.0,
            'notes': 'Create historical_rfps.csv or historical_rfps.json to populate this data',
        }
        return [sample]
    
    def _parse_json_field(self, value: Any) -> Any:
        """Parse JSON field from string.
        
        Args:
            value: Value to parse
            
        Returns:
            Parsed JSON or original value
        """
        if pd.isna(value):
            return []
        
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value
    
    def _parse_float(self, value: Any) -> float:
        """Parse float value.
        
        Args:
            value: Value to parse
            
        Returns:
            Float value or 0.0
        """
        if pd.isna(value):
            return 0.0
        
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    async def save_rfp_history(self, rfp_data: Dict[str, Any], 
                              output_file: str = "historical_rfps.json"):
        """Save processed RFP to historical records.
        
        Args:
            rfp_data: RFP data to save
            output_file: Output filename
        """
        try:
            output_path = self.rfp_dir.parent / output_file
            
            # Load existing data
            existing_data = []
            if output_path.exists():
                with open(output_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            
            # Append new data
            existing_data.append(rfp_data)
            
            # Save updated data
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved RFP to history: {output_file}")
        except Exception as e:
            self.logger.error(f"Error saving RFP history", error=str(e))
