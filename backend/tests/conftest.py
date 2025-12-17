"""Pytest configuration and shared fixtures for all tests."""
import pytest
import asyncio
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Any
from datetime import datetime, timedelta
import json
import csv
import sys

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from db.database import Base
from utils import (
    get_normalizer,
    get_converter,
    get_standard_mapper,
    get_text_processor,
    get_validation_helpers,
    get_config_loader
)

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ============================================================================
# Event Loop Configuration
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestSessionLocal() as session:
        yield session
    
    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def mock_db_connection():
    """Mock database connection for testing."""
    class MockDBConnection:
        def __init__(self):
            self.connected = True
            self._data = {}
        
        def execute(self, query: str, params: tuple = None):
            """Mock execute method."""
            return MockCursor()
        
        def commit(self):
            """Mock commit."""
            pass
        
        def rollback(self):
            """Mock rollback."""
            pass
        
        def close(self):
            """Mock close."""
            self.connected = False
    
    class MockCursor:
        def __init__(self):
            self.rowcount = 1
            self._results = []
        
        def fetchone(self):
            return {'id': 1, 'name': 'Test Product'}
        
        def fetchall(self):
            return [
                {'id': 1, 'name': 'Product 1'},
                {'id': 2, 'name': 'Product 2'}
            ]
        
        def fetchmany(self, size: int):
            return self.fetchall()[:size]
    
    return MockDBConnection()


@pytest.fixture
async def async_mock_db():
    """Mock async database connection."""
    class AsyncMockDB:
        def __init__(self):
            self.connected = True
            self._storage = {}
        
        async def execute(self, query: str, *args):
            """Execute query."""
            return AsyncMockCursor()
        
        async def fetch(self, query: str, *args):
            """Fetch results."""
            return [
                {'id': 1, 'brand': 'Havells', 'category': 'Cables'},
                {'id': 2, 'brand': 'Polycab', 'category': 'Wires'}
            ]
        
        async def fetchrow(self, query: str, *args):
            """Fetch single row."""
            return {'id': 1, 'brand': 'Havells', 'category': 'Cables'}
        
        async def fetchval(self, query: str, *args):
            """Fetch single value."""
            return 1
        
        async def close(self):
            """Close connection."""
            self.connected = False
    
    class AsyncMockCursor:
        async def fetch(self):
            return [{'id': 1}]
    
    db = AsyncMockDB()
    yield db
    await db.close()


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture
def normalizer():
    """Get specification normalizer instance."""
    return get_normalizer()


@pytest.fixture
def converter():
    """Get unit converter instance."""
    return get_converter()


@pytest.fixture
def standard_mapper():
    """Get standard mapper instance."""
    return get_standard_mapper()


@pytest.fixture
def text_processor():
    """Get text processor instance."""
    return get_text_processor()


@pytest.fixture
def validator():
    """Get validation helpers instance."""
    return get_validation_helpers()


@pytest.fixture
def config_loader():
    """Get configuration loader instance."""
    return get_config_loader()


# ============================================================================
# Mock Data Path Fixtures
# ============================================================================

@pytest.fixture
def mock_data_dir():
    """Path to mock data directory."""
    return Path(__file__).parent / "mock_data"


@pytest.fixture
def products_json_path(mock_data_dir):
    """Path to products JSON file."""
    return mock_data_dir / "products.json"


@pytest.fixture
def products_csv_path(mock_data_dir):
    """Path to products CSV file."""
    return mock_data_dir / "products.csv"


@pytest.fixture
def sample_rfp_path(mock_data_dir):
    """Path to sample RFP JSON file."""
    return mock_data_dir / "sample_rfp.json"


@pytest.fixture
def specifications_path(mock_data_dir):
    """Path to specifications JSON file."""
    return mock_data_dir / "specifications.json"


# ============================================================================
# Mock Data Fixtures - Products
# ============================================================================

@pytest.fixture
def sample_product():
    """Sample product data."""
    return {
        'id': 1,
        'brand': 'Havells',
        'category': 'Cables',
        'product_name': 'PVC Insulated Cable',
        'voltage_rating': '1.1kV',
        'current_rating': '16A',
        'conductor_material': 'Copper',
        'insulation_type': 'PVC',
        'standards': 'IS 694, IEC 60227',
        'mrp': 1500.00,
        'selling_price': 1200.00,
        'dealer_price': 1000.00,
        'gst_rate': 18.0,
        'hsn_code': '8544',
        'is_active': True,
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }


@pytest.fixture
def sample_products_list():
    """List of sample products."""
    return [
        {
            'id': 1,
            'brand': 'Havells',
            'category': 'Cables',
            'product_name': 'HRFR Cable 1.5 sq mm',
            'voltage_rating': '1100V',
            'standards': 'IS 694',
            'mrp': 2500.00,
            'selling_price': 2000.00
        },
        {
            'id': 2,
            'brand': 'Polycab',
            'category': 'Wires',
            'product_name': 'FR Wire 2.5 sq mm',
            'voltage_rating': '1.1kV',
            'standards': 'IEC 60227',
            'mrp': 1800.00,
            'selling_price': 1500.00
        },
        {
            'id': 3,
            'brand': 'KEI',
            'category': 'Switchgear',
            'product_name': 'MCB 32A C-Curve',
            'current_rating': '32A',
            'standards': 'IS 8828',
            'mrp': 450.00,
            'selling_price': 380.00
        }
    ]


@pytest.fixture
def sample_specifications():
    """Sample specifications dictionary."""
    return {
        'voltage': '230V',
        'current': '16A',
        'power': '1500W',
        'frequency': '50Hz',
        'temperature': '70°C',
        'dimensions': '100mm x 50mm x 25mm',
        'weight': '2.5kg',
        'color': 'Red',
        'material': 'Copper',
        'insulation': 'PVC'
    }


# ============================================================================
# Mock Data Fixtures - RFPs
# ============================================================================

@pytest.fixture
def sample_rfp_data():
    """Sample RFP data for testing."""
    return {
        "rfp_number": "RFP/2025/001",
        "title": "Supply of Electrical Cables",
        "requirements": [
            {
                "item_name": "11 kV XLPE Cable",
                "specifications": {
                    "voltage": "11 kV",
                    "conductor": "Copper",
                    "insulation": "XLPE",
                    "cores": 3,
                },
                "quantity": 1000,
            }
        ],
        "standards": ["IS 7098"],
        "pricing_strategy": "competitive",
    }


@pytest.fixture
def sample_rfp():
    """Detailed sample RFP data."""
    return {
        'id': 1,
        'rfp_number': 'RFP/2025/001',
        'title': 'Supply of Electrical Cables and Accessories',
        'organization': 'ABC Corporation',
        'department': 'Procurement',
        'issue_date': datetime.now().date(),
        'submission_deadline': (datetime.now() + timedelta(days=30)).date(),
        'technical_deadline': (datetime.now() + timedelta(days=20)).date(),
        'estimated_value': 5000000.00,
        'currency': 'INR',
        'status': 'Open',
        'contact_person': 'Rajesh Kumar',
        'contact_email': 'rajesh.kumar@abc.com',
        'contact_phone': '+919876543210'
    }


@pytest.fixture
def sample_rfp_items():
    """Sample RFP line items."""
    return [
        {
            'id': 1,
            'rfp_id': 1,
            'item_number': '001',
            'description': 'HRFR Cable 1.5 sq mm, 1100V',
            'quantity': 5000,
            'unit': 'meters',
            'specifications': {
                'voltage': '1100V',
                'conductor_size': '1.5 sq mm',
                'insulation': 'HRFR',
                'standards': 'IS 694'
            },
            'delivery_location': 'Mumbai',
            'delivery_date': (datetime.now() + timedelta(days=45)).date()
        },
        {
            'id': 2,
            'rfp_id': 1,
            'item_number': '002',
            'description': 'MCB 32A, C-Curve',
            'quantity': 200,
            'unit': 'pieces',
            'specifications': {
                'current_rating': '32A',
                'curve_type': 'C',
                'poles': '4P',
                'standards': 'IS 8828'
            },
            'delivery_location': 'Delhi',
            'delivery_date': (datetime.now() + timedelta(days=40)).date()
        }
    ]


# ============================================================================
# Parametrized Test Data
# ============================================================================

@pytest.fixture
def voltage_test_cases():
    """Test cases for voltage normalization."""
    return [
        ('230V', 230.0, 'V'),
        ('1.1kV', 1.1, 'kV'),
        ('11000V', 11.0, 'kV'),
        ('415 V', 415.0, 'V'),
        ('0.4kV', 0.4, 'kV')
    ]


@pytest.fixture
def current_test_cases():
    """Test cases for current normalization."""
    return [
        ('16A', 16.0, 'A'),
        ('32 A', 32.0, 'A'),
        ('100mA', 0.1, 'A'),
        ('2.5A', 2.5, 'A')
    ]


@pytest.fixture
def standard_equivalence_cases():
    """Test cases for standard equivalence."""
    return [
        ('IS 694', 'IEC 60227', True),
        ('IS 1554', 'IEC 60502', True),
        ('IS 8828', 'IEC 60898', True),
        ('IS 694', 'IS 1554', False)
    ]
