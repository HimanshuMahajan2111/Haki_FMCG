"""Standards data loader with validation."""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
import structlog

from config.settings import settings
from data.base_loader import BaseDataLoader

logger = structlog.get_logger()


class StandardsDataLoader(BaseDataLoader):
    """Load and validate standards data."""
    
    def __init__(self):
        """Initialize standards loader."""
        super().__init__("StandardsDataLoader")
        self.standards_dir = Path(settings.standards_dir)
        
        # Required fields for standards
        # CSV columns: standard_code, standard_type, description, issuing_body, etc.
        self.required_fields = {
            'standard_code'
        }
        
        self.optional_fields = {
            'description', 'scope', 'authority', 'category',
            'equivalent_standards', 'revision_date', 'status',
            'application', 'requirements', 'pricing_info'
        }
    
    async def load(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load all standards data with validation.
        
        Returns:
            Dictionary with different standards categories
        """
        self.logger.info("Loading standards data with validation")
        
        standards_data = {
            'indian_standards': await self._load_indian_standards(),
            'international_standards': await self._load_international_standards(),
            'comparisons': await self._load_comparisons(),
            'pricing': await self._load_pricing(),
            'tender_requirements': await self._load_tender_requirements(),
        }
        
        # Load complete summary if available
        complete_summary = await self._load_complete_summary()
        if complete_summary:
            standards_data['complete_summary'] = complete_summary
        
        # Validate each category
        for category, data in standards_data.items():
            if data and isinstance(data, list):
                self.logger.info(f"Validating {category}", count=len(data))
                validation_result = self.validate_data(data)
                self.log_validation_summary(validation_result)
        
        total_records = sum(len(v) if isinstance(v, list) else 0 
                          for v in standards_data.values())
        self.logger.info("Standards data loaded", total_records=total_records)
        
        return standards_data
    
    async def _load_indian_standards(self) -> List[Dict[str, Any]]:
        """Load Indian standards (IS codes)."""
        file_path = self.standards_dir / "wire_cable_standards_indian_standards_20251215_013650.csv"
        
        if not self.check_file_exists(file_path):
            return []
        
        try:
            df = pd.read_csv(file_path)
            standards = []
            
            for _, row in df.iterrows():
                # CSV columns: standard_code, standard_type, description, issuing_body, geographical_scope, etc.
                code = str(row.get('standard_code', 'UNKNOWN'))
                if pd.isna(code) or code == 'nan':
                    code = 'UNKNOWN'
                
                standard = {
                    'standard_code': code,
                    'standard_type': str(row.get('standard_type', 'Indian Standard (IS)')),
                    'description': str(row.get('description', '')),
                    'issuing_body': str(row.get('issuing_body', 'Bureau of Indian Standards (BIS)')),
                    'geographical_scope': str(row.get('geographical_scope', '')),
                    'mandatory_in_region': str(row.get('mandatory_in_region', '')),
                    'certification_required': str(row.get('certification_required', '')),
                }
                standards.append(standard)
            
            self.logger.info(f"Loaded {len(standards)} Indian standards")
            return standards
        except Exception as e:
            self.logger.error("Error loading Indian standards", error=str(e))
            return []
    
    async def _load_international_standards(self) -> List[Dict[str, Any]]:
        """Load international standards (IEC, BS, etc.)."""
        file_path = self.standards_dir / "wire_cable_standards_international_standards_20251215_013650.csv"
        
        if not self.check_file_exists(file_path):
            return []
        
        try:
            df = pd.read_csv(file_path)
            standards = []
            
            for _, row in df.iterrows():
                # CSV columns: standard_code, standard_type, description, issuing_body, geographical_scope, etc.
                code = str(row.get('standard_code', 'UNKNOWN'))
                if pd.isna(code) or code == 'nan':
                    code = 'UNKNOWN'
                
                standard = {
                    'standard_code': code,
                    'standard_type': str(row.get('standard_type', 'International Standard')),
                    'description': str(row.get('description', '')),
                    'issuing_body': str(row.get('issuing_body', 'IEC')),
                    'geographical_scope': str(row.get('geographical_scope', '')),
                    'mandatory_in_region': str(row.get('mandatory_in_region', '')),
                    'certification_required': str(row.get('certification_required', '')),
                }
                standards.append(standard)
            
            self.logger.info(f"Loaded {len(standards)} international standards")
            return standards
        except Exception as e:
            self.logger.error("Error loading international standards", error=str(e))
            return []
    
    async def _load_comparisons(self) -> List[Dict[str, Any]]:
        """Load standards comparison data."""
        file_path = self.standards_dir / "wire_cable_standards_comparisons_20251215_013650.csv"
        
        if not self.check_file_exists(file_path):
            return []
        
        try:
            df = pd.read_csv(file_path)
            comparisons = []
            
            for _, row in df.iterrows():
                code = str(row.get('indian_standard', row.get('IS Standard', 'UNKNOWN')))
                if pd.isna(code) or code == 'nan':
                    code = 'UNKNOWN'
                
                comparison = {
                    'standard_code': code,
                    'indian_standard': str(row.get('indian_standard', '')),
                    'international_equivalent': str(row.get('international_equivalent', row.get('IEC Standard', ''))),
                    'comparison_notes': str(row.get('comparison_notes', row.get('Differences', ''))),
                    'category': 'Standards Comparison',
                }
                comparisons.append(comparison)
            
            self.logger.info(f"Loaded {len(comparisons)} standards comparisons")
            return comparisons
        except Exception as e:
            self.logger.error("Error loading standards comparisons", error=str(e))
            return []
    
    async def _load_pricing(self) -> List[Dict[str, Any]]:
        """Load standards-related pricing data."""
        file_path = self.standards_dir / "wire_cable_standards_pricing_20251215_013650.csv"
        
        if not self.check_file_exists(file_path):
            return []
        
        try:
            df = pd.read_csv(file_path)
            pricing = []
            
            for _, row in df.iterrows():
                code = str(row.get('standard', row.get('Standard', row.get('standard_code', 'UNKNOWN'))))
                if pd.isna(code) or code == 'nan':
                    code = 'UNKNOWN'
                
                price_info = {
                    'standard_code': code,
                    'pricing_range': str(row.get('pricing_range', row.get('price_range', ''))),
                    'testing_cost_range': str(row.get('testing_cost_range', '')),
                    'certification_cost_range': str(row.get('certification_cost_range', '')),
                    'total_cost_estimate': str(row.get('total_cost_estimate', row.get('Total Cost', ''))),
                    'notes': str(row.get('notes', '')),
                    'category': 'Pricing Information',
                }
                pricing.append(price_info)
            
            self.logger.info(f"Loaded {len(pricing)} pricing records")
            return pricing
        except Exception as e:
            self.logger.error("Error loading pricing data", error=str(e))
            return []
    
    async def _load_tender_requirements(self) -> List[Dict[str, Any]]:
        """Load tender requirements related to standards."""
        file_path = self.standards_dir / "wire_cable_standards_tender_requirements_20251215_013650.csv"
        
        if not self.check_file_exists(file_path):
            return []
        
        try:
            df = pd.read_csv(file_path)
            requirements = []
            
            for _, row in df.iterrows():
                code = str(row.get('standard', row.get('Standard', row.get('required_standard', 'UNKNOWN'))))
                if pd.isna(code) or code == 'nan':
                    code = 'UNKNOWN'
                
                requirement = {
                    'standard_code': code,
                    'typical_clauses': str(row.get('typical_clauses', row.get('Requirements', ''))),
                    'mandatory_tests': str(row.get('mandatory_tests', row.get('Mandatory Tests', ''))),
                    'documentation_required': str(row.get('documentation_required', '')),
                    'inspection_requirements': str(row.get('inspection_requirements', '')),
                    'category': 'Tender Requirements',
                }
                requirements.append(requirement)
            
            self.logger.info(f"Loaded {len(requirements)} tender requirements")
            return requirements
        except Exception as e:
            self.logger.error("Error loading tender requirements", error=str(e))
            return []
    
    async def _load_complete_summary(self) -> List[Dict[str, Any]]:
        """Load complete summary of all standards."""
        file_path = self.standards_dir / "wire_cable_standards_complete_summary_20251215_013650.csv"
        
        if not self.check_file_exists(file_path):
            return []
        
        try:
            df = pd.read_csv(file_path)
            summary = []
            
            for _, row in df.iterrows():
                code = str(row.get('standard_code', row.get('Standard', 'UNKNOWN')))
                if pd.isna(code) or code == 'nan':
                    code = 'UNKNOWN'
                
                record = {
                    'standard_code': code,
                    'standard_type': str(row.get('standard_type', '')),
                    'description': str(row.get('description', row.get('Description', ''))),
                    'category': str(row.get('category', row.get('Category', ''))),
                    'issuing_body': str(row.get('issuing_body', '')),
                }
                summary.append(record)
            
            self.logger.info(f"Loaded {len(summary)} summary records")
            return summary
        except Exception as e:
            self.logger.error("Error loading complete summary", error=str(e))
            return []
