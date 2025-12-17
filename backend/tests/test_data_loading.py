"""Tests for data loading functionality from CSV and JSON files."""
import pytest
import json
import csv
from pathlib import Path
from typing import List, Dict, Any


class TestCSVDataLoading:
    """Test CSV data loading functionality."""
    
    def test_load_products_csv_file_exists(self, products_csv_path):
        """Test that products CSV file exists."""
        assert products_csv_path.exists(), f"CSV file not found: {products_csv_path}"
    
    def test_load_products_csv_structure(self, products_csv_path):
        """Test CSV file has correct structure."""
        with open(products_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            required_headers = ['brand', 'category', 'product_name', 'voltage_rating', 'mrp']
            for header in required_headers:
                assert header in headers, f"Missing required header: {header}"
    
    def test_load_products_csv_data(self, products_csv_path):
        """Test loading and parsing CSV data."""
        products = []
        with open(products_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            products = list(reader)
        
        assert len(products) > 0, "CSV file is empty"
        assert len(products) == 10, f"Expected 10 products, got {len(products)}"
    
    def test_csv_product_data_types(self, products_csv_path):
        """Test that CSV data can be parsed to correct types."""
        with open(products_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            first_product = next(reader)
            
            # Test string fields
            assert isinstance(first_product['brand'], str)
            assert isinstance(first_product['product_name'], str)
            
            # Test numeric fields can be converted
            mrp = float(first_product['mrp'])
            assert mrp > 0, "MRP should be positive"
            
            gst_rate = float(first_product['gst_rate'])
            assert 0 <= gst_rate <= 100, "GST rate should be between 0 and 100"
    
    def test_csv_brands(self, products_csv_path):
        """Test that CSV contains expected brands."""
        with open(products_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            brands = {row['brand'] for row in reader}
        
        expected_brands = {'Havells', 'Polycab', 'KEI', 'Finolex', 'RR Kabel'}
        assert expected_brands.issubset(brands), f"Missing brands. Found: {brands}"
    
    def test_csv_categories(self, products_csv_path):
        """Test that CSV contains valid categories."""
        with open(products_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            categories = {row['category'] for row in reader}
        
        valid_categories = {'Cables', 'Wires', 'Switchgear', 'Motors', 'Lighting', 'Fans'}
        assert categories.issubset(valid_categories), f"Invalid categories found: {categories - valid_categories}"


class TestJSONDataLoading:
    """Test JSON data loading functionality."""
    
    def test_load_products_json_file_exists(self, products_json_path):
        """Test that products JSON file exists."""
        assert products_json_path.exists(), f"JSON file not found: {products_json_path}"
    
    def test_load_products_json_valid(self, products_json_path):
        """Test JSON file is valid and can be parsed."""
        with open(products_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert isinstance(data, list), "JSON root should be a list"
        assert len(data) > 0, "JSON file is empty"
    
    def test_json_product_structure(self, products_json_path):
        """Test JSON product objects have correct structure."""
        with open(products_json_path, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        first_product = products[0]
        required_fields = ['id', 'brand', 'category', 'product_name', 'mrp', 'selling_price']
        
        for field in required_fields:
            assert field in first_product, f"Missing required field: {field}"
    
    def test_json_product_data_types(self, products_json_path):
        """Test JSON data types are correct."""
        with open(products_json_path, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        first_product = products[0]
        
        assert isinstance(first_product['id'], int)
        assert isinstance(first_product['brand'], str)
        assert isinstance(first_product['product_name'], str)
        assert isinstance(first_product['mrp'], (int, float))
        assert isinstance(first_product['is_active'], bool)
    
    def test_json_pricing_consistency(self, products_json_path):
        """Test pricing hierarchy: mrp >= selling_price >= dealer_price."""
        with open(products_json_path, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        for product in products:
            mrp = product['mrp']
            selling = product['selling_price']
            dealer = product['dealer_price']
            
            assert mrp >= selling, f"MRP < Selling Price for {product['product_name']}"
            assert selling >= dealer, f"Selling < Dealer Price for {product['product_name']}"
    
    def test_json_standards_field(self, products_json_path):
        """Test standards field is present and non-empty."""
        with open(products_json_path, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        for product in products:
            assert 'standards' in product, f"Missing standards for {product['product_name']}"
            assert len(product['standards']) > 0, f"Empty standards for {product['product_name']}"


class TestRFPDataLoading:
    """Test RFP data loading functionality."""
    
    def test_load_rfp_json_file_exists(self, sample_rfp_path):
        """Test that RFP JSON file exists."""
        assert sample_rfp_path.exists(), f"RFP file not found: {sample_rfp_path}"
    
    def test_load_rfp_json_valid(self, sample_rfp_path):
        """Test RFP JSON is valid."""
        with open(sample_rfp_path, 'r', encoding='utf-8') as f:
            rfp = json.load(f)
        
        assert isinstance(rfp, dict), "RFP should be a dictionary"
    
    def test_rfp_required_fields(self, sample_rfp_path):
        """Test RFP has all required fields."""
        with open(sample_rfp_path, 'r', encoding='utf-8') as f:
            rfp = json.load(f)
        
        required_fields = [
            'rfp_number', 'title', 'organization', 'issue_date',
            'submission_deadline', 'estimated_value', 'items'
        ]
        
        for field in required_fields:
            assert field in rfp, f"Missing required field: {field}"
    
    def test_rfp_items_structure(self, sample_rfp_path):
        """Test RFP items have correct structure."""
        with open(sample_rfp_path, 'r', encoding='utf-8') as f:
            rfp = json.load(f)
        
        assert 'items' in rfp
        assert len(rfp['items']) > 0, "RFP should have at least one item"
        
        first_item = rfp['items'][0]
        required_item_fields = ['item_number', 'description', 'quantity', 'specifications']
        
        for field in required_item_fields:
            assert field in first_item, f"Missing item field: {field}"
    
    def test_rfp_specifications_nested(self, sample_rfp_path):
        """Test RFP item specifications are nested correctly."""
        with open(sample_rfp_path, 'r', encoding='utf-8') as f:
            rfp = json.load(f)
        
        for item in rfp['items']:
            specs = item['specifications']
            assert isinstance(specs, dict), "Specifications should be a dictionary"
            assert len(specs) > 0, f"Empty specifications for item {item['item_number']}"


class TestSpecificationsLoading:
    """Test specifications data loading."""
    
    def test_load_specifications_json_exists(self, specifications_path):
        """Test specifications JSON file exists."""
        assert specifications_path.exists(), f"Specifications file not found: {specifications_path}"
    
    def test_load_specifications_json_valid(self, specifications_path):
        """Test specifications JSON is valid."""
        with open(specifications_path, 'r', encoding='utf-8') as f:
            specs = json.load(f)
        
        assert isinstance(specs, dict), "Specifications should be a dictionary"
    
    def test_specifications_categories(self, specifications_path):
        """Test specifications contain expected categories."""
        with open(specifications_path, 'r', encoding='utf-8') as f:
            specs = json.load(f)
        
        expected_categories = ['cable_specifications', 'switchgear_specifications']
        for category in expected_categories:
            assert category in specs, f"Missing category: {category}"
            assert isinstance(specs[category], list), f"{category} should be a list"
    
    def test_cable_specifications_structure(self, specifications_path):
        """Test cable specifications have correct structure."""
        with open(specifications_path, 'r', encoding='utf-8') as f:
            specs = json.load(f)
        
        cables = specs['cable_specifications']
        assert len(cables) > 0, "Should have at least one cable specification"
        
        first_cable = cables[0]
        required_fields = ['voltage', 'current', 'conductor_size', 'standards']
        
        for field in required_fields:
            assert field in first_cable, f"Missing field in cable specs: {field}"


class TestDataLoadingUtilities:
    """Test utility functions for data loading."""
    
    def test_load_json_helper(self, products_json_path):
        """Test helper function to load JSON files."""
        def load_json_file(filepath: Path) -> Any:
            """Load JSON file."""
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        data = load_json_file(products_json_path)
        assert data is not None
        assert isinstance(data, list)
    
    def test_load_csv_as_dict_helper(self, products_csv_path):
        """Test helper function to load CSV as list of dicts."""
        def load_csv_as_dicts(filepath: Path) -> List[Dict[str, str]]:
            """Load CSV file as list of dictionaries."""
            with open(filepath, 'r', encoding='utf-8') as f:
                return list(csv.DictReader(f))
        
        data = load_csv_as_dicts(products_csv_path)
        assert data is not None
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_validate_product_data(self, sample_product, validator):
        """Test product data validation using validator."""
        validation = validator.validate_product_data(sample_product)
        assert validation['is_valid'], f"Product validation failed: {validation.get('errors')}"
    
    def test_parse_csv_with_type_conversion(self, products_csv_path):
        """Test CSV loading with type conversion."""
        def parse_csv_typed(filepath: Path) -> List[Dict[str, Any]]:
            """Parse CSV with type conversion."""
            products = []
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    product = dict(row)
                    # Convert numeric fields
                    if product.get('mrp'):
                        product['mrp'] = float(product['mrp'])
                    if product.get('gst_rate'):
                        product['gst_rate'] = float(product['gst_rate'])
                    products.append(product)
            return products
        
        products = parse_csv_typed(products_csv_path)
        assert len(products) > 0
        assert isinstance(products[0]['mrp'], float)


class TestDataIntegrity:
    """Test data integrity and consistency."""
    
    def test_products_unique_ids_json(self, products_json_path):
        """Test that product IDs are unique in JSON."""
        with open(products_json_path, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        ids = [p['id'] for p in products]
        assert len(ids) == len(set(ids)), "Duplicate product IDs found"
    
    def test_products_non_empty_names(self, products_json_path):
        """Test that all products have non-empty names."""
        with open(products_json_path, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        for product in products:
            assert product['product_name'].strip(), f"Empty product name for ID {product['id']}"
    
    def test_valid_hsn_codes(self, products_json_path):
        """Test that HSN codes are valid (4 digits)."""
        with open(products_json_path, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        for product in products:
            hsn = product['hsn_code']
            assert hsn.isdigit(), f"Invalid HSN code: {hsn}"
            assert len(hsn) == 4, f"HSN code should be 4 digits: {hsn}"
    
    def test_gst_rates_valid(self, products_json_path):
        """Test that GST rates are valid percentages."""
        with open(products_json_path, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        valid_gst_rates = {0, 5, 12, 18, 28}
        for product in products:
            gst = product['gst_rate']
            assert gst in valid_gst_rates, f"Invalid GST rate {gst} for {product['product_name']}"
