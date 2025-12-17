"""
Product Database Models - OEM Products and Inventory

Models for storing OEM product catalog with specifications, pricing, and inventory.
"""
from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, Text, Boolean
from sqlalchemy.sql import func
from db.database import Base


class OEMProduct(Base):
    """OEM Product catalog with specifications."""
    
    __tablename__ = "oem_products"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, unique=True, index=True, nullable=False)
    manufacturer = Column(String, index=True, nullable=False)
    model_number = Column(String, index=True)
    product_name = Column(String, nullable=False)
    category = Column(String, index=True)
    product_type = Column(String)  # Cable, Wire, etc.
    
    # Specifications (JSON)
    specifications = Column(JSON)
    
    # Pricing
    unit_price = Column(Float, default=0.0)
    currency = Column(String, default='INR')
    price_per_meter = Column(Float)
    price_per_100m = Column(Float)
    
    # Inventory
    stock_quantity = Column(Integer, default=0)
    available_stock = Column(Integer, default=0)
    delivery_days = Column(Integer, default=7)
    
    # Certifications and Standards
    certifications = Column(JSON)  # List of certifications
    standards = Column(JSON)  # List of standards
    
    # Test Costs
    routine_test_cost = Column(Float, default=0.0)
    type_test_cost = Column(Float, default=0.0)
    test_certificate_cost = Column(Float, default=0.0)
    
    # Product Details
    hsn_code = Column(String)
    warranty_years = Column(Integer)
    product_url = Column(Text)
    
    # Additional Technical Data
    voltage_rating = Column(String)
    conductor_material = Column(String)
    conductor_size = Column(String)
    no_of_cores = Column(Integer)
    insulation_type = Column(String)
    max_temperature = Column(String)
    current_rating = Column(String)
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    data_source = Column(String)  # CSV file name
    extracted_date = Column(DateTime)
    
    def __repr__(self):
        return f"<OEMProduct {self.manufacturer} {self.model_number}>"


class ProductInventory(Base):
    """Product inventory and availability tracking."""
    
    __tablename__ = "product_inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, index=True, nullable=False)
    
    stock_quantity = Column(Integer, default=0)
    reserved_quantity = Column(Integer, default=0)
    available_quantity = Column(Integer, default=0)
    
    warehouse_location = Column(String)
    reorder_level = Column(Integer, default=100)
    reorder_quantity = Column(Integer, default=1000)
    
    last_restocked_at = Column(DateTime)
    last_updated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Inventory {self.product_id}: {self.available_quantity} available>"


class PriceHistory(Base):
    """Historical pricing data for products."""
    
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, index=True, nullable=False)
    
    unit_price = Column(Float, nullable=False)
    currency = Column(String, default='INR')
    effective_date = Column(DateTime, nullable=False)
    
    price_change_reason = Column(String)  # Market change, supplier update, etc.
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<PriceHistory {self.product_id}: ₹{self.unit_price}>"
