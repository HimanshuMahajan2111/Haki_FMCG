"""Testing data loader with validation."""
import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Any
import structlog

from config.settings import settings
from data.base_loader import BaseDataLoader, ValidationResult

logger = structlog.get_logger()


class TestingDataLoader(BaseDataLoader):
    """Load and validate testing and certification data."""
    
    def __init__(self):
        """Initialize testing data loader."""
        super().__init__("TestingDataLoader")
        self.testing_dir = Path(settings.testing_data_dir)
        
        # Required fields for test records
        # CSV has: lab_name, test_name, estimated_cost, price_range, etc.
        self.required_fields = {
            'test_name'
        }
        
        self.optional_fields = {
            'standard', 'description', 'procedure', 'equipment',
            'parameters', 'acceptance_criteria', 'frequency',
            'laboratory', 'certification', 'cost'
        }
    
    async def load(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load all testing data with validation.
        
        Returns:
            Dictionary with different test types
        """
        self.logger.info("Loading testing data with validation")
        
        testing_data = {
            'type_tests': await self._load_type_tests(),
            'routine_tests': await self._load_routine_tests(),
            'special_tests': await self._load_special_tests(),
            'emi_emc_tests': await self._load_emi_emc_tests(),
            'certifications': await self._load_certifications(),
            'laboratories': await self._load_laboratories(),
            'standards': await self._load_standards(),
        }
        
        # Load comprehensive JSON data
        json_data = await self._load_json_testing_data()
        if json_data:
            testing_data['comprehensive'] = json_data
        
        # Validate each category
        for category, data in testing_data.items():
            if data and isinstance(data, list):
                self.logger.info(f"Validating {category}", count=len(data))
                validation_result = self.validate_data(data)
                self.log_validation_summary(validation_result)
        
        total_records = sum(len(v) if isinstance(v, list) else 0 
                          for v in testing_data.values())
        self.logger.info("Testing data loaded", total_records=total_records)
        
        return testing_data
    
    async def _load_type_tests(self) -> List[Dict[str, Any]]:
        """Load type test data."""
        file_path = self.testing_dir / "type_tests_20251213_161518.csv"
        return await self._load_csv_file(file_path, 'Type Test')
    
    async def _load_routine_tests(self) -> List[Dict[str, Any]]:
        """Load routine test data."""
        file_path = self.testing_dir / "routine_tests_20251213_161518.csv"
        return await self._load_csv_file(file_path, 'Routine Test')
    
    async def _load_special_tests(self) -> List[Dict[str, Any]]:
        """Load special test data."""
        file_path = self.testing_dir / "special_tests_20251213_161518.csv"
        return await self._load_csv_file(file_path, 'Special Test')
    
    async def _load_emi_emc_tests(self) -> List[Dict[str, Any]]:
        """Load EMI/EMC test data."""
        file_path = self.testing_dir / "emi_emc_tests_20251213_161518.csv"
        return await self._load_csv_file(file_path, 'EMI/EMC Test')
    
    async def _load_certifications(self) -> List[Dict[str, Any]]:
        """Load certification data."""
        file_path = self.testing_dir / "certification_20251213_161518.csv"
        
        if not self.check_file_exists(file_path):
            return []
        
        try:
            df = pd.read_csv(file_path)
            certifications = []
            
            for _, row in df.iterrows():
                name = str(row.get('certification', row.get('Certification', row.get('name', 'Unknown'))))
                if pd.isna(name) or name == 'nan':
                    name = 'Certification'
                
                cert = {
                    'test_name': name,
                    'test_type': 'Certification',
                    'issuing_body': str(row.get('issuing_body', row.get('Issuing Body', ''))),
                    'standard': str(row.get('standard', row.get('Standard', ''))),
                    'validity': str(row.get('validity', row.get('Validity', ''))),
                    'cost': str(row.get('cost', row.get('Cost', ''))),
                    'description': str(row.get('description', row.get('Description', ''))),
                }
                certifications.append(cert)
            
            self.logger.info(f"Loaded {len(certifications)} certifications")
            return certifications
        except Exception as e:
            self.logger.error(f"Error loading certifications", error=str(e))
            return []
    
    async def _load_laboratories(self) -> List[Dict[str, Any]]:
        """Load laboratory data."""
        file_path = self.testing_dir / "laboratories_20251213_161518.csv"
        
        if not self.check_file_exists(file_path):
            return []
        
        try:
            df = pd.read_csv(file_path)
            laboratories = []
            
            for _, row in df.iterrows():
                name = str(row.get('lab_name', row.get('Laboratory', row.get('name', 'Unknown Lab'))))
                if pd.isna(name) or name == 'nan':
                    name = 'Laboratory'
                
                lab = {
                    'test_name': name,
                    'test_type': 'Laboratory',
                    'location': str(row.get('location', row.get('Location', ''))),
                    'accreditation': str(row.get('accreditation', row.get('Accreditation', ''))),
                    'capabilities': str(row.get('capabilities', row.get('Capabilities', ''))),
                    'contact': str(row.get('contact', row.get('Contact', ''))),
                }
                laboratories.append(lab)
            
            self.logger.info(f"Loaded {len(laboratories)} laboratories")
            return laboratories
        except Exception as e:
            self.logger.error(f"Error loading laboratories", error=str(e))
            return []
    
    async def _load_standards(self) -> List[Dict[str, Any]]:
        """Load standards data."""
        file_path = self.testing_dir / "standards_20251213_161518.csv"
        
        if not self.check_file_exists(file_path):
            return []
        
        try:
            df = pd.read_csv(file_path)
            standards = []
            
            for _, row in df.iterrows():
                name = str(row.get('standard', row.get('Standard', row.get('name', 'Unknown Standard'))))
                if pd.isna(name) or name == 'nan':
                    name = 'Standard'
                
                standard = {
                    'test_name': name,
                    'test_type': 'Standard',
                    'description': str(row.get('description', row.get('Description', ''))),
                    'scope': str(row.get('scope', row.get('Scope', ''))),
                    'authority': str(row.get('authority', row.get('Authority', ''))),
                }
                standards.append(standard)
            
            self.logger.info(f"Loaded {len(standards)} standards")
            return standards
        except Exception as e:
            self.logger.error(f"Error loading standards", error=str(e))
            return []
    
    async def _load_json_testing_data(self) -> List[Dict[str, Any]]:
        """Load comprehensive testing data from JSON."""
        file_path = self.testing_dir / "cable_testing_data_20251213_161519.json"
        
        if not self.check_file_exists(file_path):
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Flatten JSON structure if needed
            if isinstance(data, dict):
                test_records = []
                for key, value in data.items():
                    if isinstance(value, list):
                        test_records.extend(value)
                    elif isinstance(value, dict):
                        test_records.append(value)
                self.logger.info(f"Loaded {len(test_records)} tests from JSON")
                return test_records
            elif isinstance(data, list):
                self.logger.info(f"Loaded {len(data)} tests from JSON")
                return data
            
            return []
        except Exception as e:
            self.logger.error(f"Error loading JSON testing data", error=str(e))
            return []
    
    async def _load_csv_file(self, file_path: Path, test_type: str) -> List[Dict[str, Any]]:
        """Load test data from CSV file.
        
        Args:
            file_path: Path to CSV file
            test_type: Type of test
            
        Returns:
            List of test records
        """
        if not self.check_file_exists(file_path):
            return []
        
        try:
            df = pd.read_csv(file_path)
            tests = []
            
            for _, row in df.iterrows():
                # CSV columns: lab_name, test_name, estimated_cost, price_range, location, source, note, category
                name = str(row.get('test_name', 'Unknown Test'))
                if pd.isna(name) or name == 'nan':
                    name = f"{test_type}"
                
                test = {
                    'test_name': name,
                    'test_type': test_type,
                    'lab_name': str(row.get('lab_name', '')),
                    'estimated_cost': str(row.get('estimated_cost', '')),
                    'price_range': str(row.get('price_range', '')),
                    'location': str(row.get('location', '')),
                    'standard': str(row.get('standard', '')),
                    'note': str(row.get('note', row.get('source', ''))),
                }
                tests.append(test)
            
            self.logger.info(f"Loaded {len(tests)} {test_type}s from {file_path.name}")
            return tests
        except Exception as e:
            self.logger.error(f"Error loading {file_path.name}", error=str(e))
            return []
