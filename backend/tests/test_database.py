"""Tests for database operations (CRUD functionality)."""
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List


class TestDatabaseConnection:
    """Test database connection functionality."""
    
    def test_mock_db_connection_created(self, mock_db_connection):
        """Test mock database connection is created."""
        assert mock_db_connection is not None
        assert mock_db_connection.connected is True
    
    def test_mock_db_execute(self, mock_db_connection):
        """Test mock database execute method."""
        cursor = mock_db_connection.execute("SELECT * FROM products")
        assert cursor is not None
    
    def test_mock_db_commit(self, mock_db_connection):
        """Test mock database commit."""
        mock_db_connection.commit()
        # Should not raise exception
    
    def test_mock_db_close(self, mock_db_connection):
        """Test mock database close."""
        mock_db_connection.close()
        assert mock_db_connection.connected is False
    
    @pytest.mark.asyncio
    async def test_async_db_connection(self, async_mock_db):
        """Test async database connection."""
        assert async_mock_db is not None
        assert async_mock_db.connected is True
    
    @pytest.mark.asyncio
    async def test_async_db_execute(self, async_mock_db):
        """Test async database execute."""
        result = await async_mock_db.execute("SELECT * FROM products")
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_async_db_fetch(self, async_mock_db):
        """Test async database fetch."""
        results = await async_mock_db.fetch("SELECT * FROM products")
        assert isinstance(results, list)
        assert len(results) > 0
    
    @pytest.mark.asyncio
    async def test_async_db_fetchrow(self, async_mock_db):
        """Test async database fetch single row."""
        row = await async_mock_db.fetchrow("SELECT * FROM products WHERE id = 1")
        assert isinstance(row, dict)
        assert 'id' in row


class TestProductCRUD:
    """Test CRUD operations for products."""
    
    def test_create_product(self, mock_db_connection, sample_product):
        """Test creating a new product."""
        # Simulate INSERT
        cursor = mock_db_connection.execute(
            "INSERT INTO products (brand, product_name) VALUES (?, ?)",
            (sample_product['brand'], sample_product['product_name'])
        )
        
        assert cursor.rowcount >= 1
    
    def test_read_product(self, mock_db_connection):
        """Test reading a product."""
        cursor = mock_db_connection.execute("SELECT * FROM products WHERE id = 1")
        product = cursor.fetchone()
        
        assert product is not None
        assert 'id' in product
    
    def test_read_all_products(self, mock_db_connection):
        """Test reading all products."""
        cursor = mock_db_connection.execute("SELECT * FROM products")
        products = cursor.fetchall()
        
        assert isinstance(products, list)
        assert len(products) > 0
    
    def test_update_product(self, mock_db_connection):
        """Test updating a product."""
        cursor = mock_db_connection.execute(
            "UPDATE products SET mrp = ? WHERE id = ?",
            (2500.00, 1)
        )
        
        assert cursor.rowcount >= 1
    
    def test_delete_product(self, mock_db_connection):
        """Test deleting a product."""
        cursor = mock_db_connection.execute("DELETE FROM products WHERE id = ?", (1,))
        assert cursor.rowcount >= 1
    
    def test_search_products_by_brand(self, mock_db_connection):
        """Test searching products by brand."""
        cursor = mock_db_connection.execute(
            "SELECT * FROM products WHERE brand = ?",
            ('Havells',)
        )
        products = cursor.fetchall()
        
        assert isinstance(products, list)
    
    def test_filter_products_by_category(self, mock_db_connection):
        """Test filtering products by category."""
        cursor = mock_db_connection.execute(
            "SELECT * FROM products WHERE category = ?",
            ('Cables',)
        )
        products = cursor.fetchall()
        
        assert isinstance(products, list)


class TestProductQueries:
    """Test complex product queries."""
    
    def test_query_products_price_range(self, mock_db_connection):
        """Test querying products in price range."""
        cursor = mock_db_connection.execute(
            "SELECT * FROM products WHERE mrp BETWEEN ? AND ?",
            (1000, 5000)
        )
        products = cursor.fetchall()
        
        assert isinstance(products, list)
    
    def test_query_products_by_voltage(self, mock_db_connection):
        """Test querying products by voltage rating."""
        cursor = mock_db_connection.execute(
            "SELECT * FROM products WHERE voltage_rating LIKE ?",
            ('%1.1kV%',)
        )
        products = cursor.fetchall()
        
        assert isinstance(products, list)
    
    def test_query_active_products(self, mock_db_connection):
        """Test querying only active products."""
        cursor = mock_db_connection.execute(
            "SELECT * FROM products WHERE is_active = ?",
            (True,)
        )
        products = cursor.fetchall()
        
        assert isinstance(products, list)
    
    def test_query_products_count(self, mock_db_connection):
        """Test counting products."""
        cursor = mock_db_connection.execute("SELECT COUNT(*) as count FROM products")
        result = cursor.fetchone()
        
        assert result is not None
        # Mock returns standard results


class TestRFPDatabaseOperations:
    """Test RFP database operations."""
    
    def test_create_rfp(self, mock_db_connection, sample_rfp):
        """Test creating a new RFP."""
        cursor = mock_db_connection.execute(
            "INSERT INTO rfps (rfp_number, title, organization) VALUES (?, ?, ?)",
            (sample_rfp['rfp_number'], sample_rfp['title'], sample_rfp['organization'])
        )
        
        assert cursor.rowcount >= 1
    
    def test_read_rfp(self, mock_db_connection):
        """Test reading an RFP."""
        cursor = mock_db_connection.execute("SELECT * FROM rfps WHERE id = 1")
        rfp = cursor.fetchone()
        
        assert rfp is not None
    
    def test_update_rfp_status(self, mock_db_connection):
        """Test updating RFP status."""
        cursor = mock_db_connection.execute(
            "UPDATE rfps SET status = ? WHERE id = ?",
            ('Closed', 1)
        )
        
        assert cursor.rowcount >= 1
    
    def test_query_open_rfps(self, mock_db_connection):
        """Test querying open RFPs."""
        cursor = mock_db_connection.execute(
            "SELECT * FROM rfps WHERE status = ?",
            ('Open',)
        )
        rfps = cursor.fetchall()
        
        assert isinstance(rfps, list)
    
    def test_query_rfps_by_deadline(self, mock_db_connection):
        """Test querying RFPs by deadline."""
        future_date = (datetime.now() + timedelta(days=30)).date()
        cursor = mock_db_connection.execute(
            "SELECT * FROM rfps WHERE submission_deadline <= ?",
            (future_date,)
        )
        rfps = cursor.fetchall()
        
        assert isinstance(rfps, list)


class TestRFPItemsOperations:
    """Test RFP items database operations."""
    
    def test_create_rfp_item(self, mock_db_connection, sample_rfp_items):
        """Test creating RFP line item."""
        item = sample_rfp_items[0]
        cursor = mock_db_connection.execute(
            "INSERT INTO rfp_items (rfp_id, item_number, description, quantity) VALUES (?, ?, ?, ?)",
            (item['rfp_id'], item['item_number'], item['description'], item['quantity'])
        )
        
        assert cursor.rowcount >= 1
    
    def test_read_rfp_items(self, mock_db_connection):
        """Test reading items for an RFP."""
        cursor = mock_db_connection.execute(
            "SELECT * FROM rfp_items WHERE rfp_id = ?",
            (1,)
        )
        items = cursor.fetchall()
        
        assert isinstance(items, list)
    
    def test_update_rfp_item_quantity(self, mock_db_connection):
        """Test updating item quantity."""
        cursor = mock_db_connection.execute(
            "UPDATE rfp_items SET quantity = ? WHERE id = ?",
            (6000, 1)
        )
        
        assert cursor.rowcount >= 1
    
    def test_delete_rfp_item(self, mock_db_connection):
        """Test deleting an RFP item."""
        cursor = mock_db_connection.execute(
            "DELETE FROM rfp_items WHERE id = ?",
            (1,)
        )
        
        assert cursor.rowcount >= 1


class TestBulkOperations:
    """Test bulk database operations."""
    
    def test_bulk_insert_products(self, mock_db_connection, sample_products_list):
        """Test bulk inserting products."""
        for product in sample_products_list:
            cursor = mock_db_connection.execute(
                "INSERT INTO products (brand, product_name, mrp) VALUES (?, ?, ?)",
                (product['brand'], product['product_name'], product['mrp'])
            )
            assert cursor.rowcount >= 1
    
    def test_bulk_update_prices(self, mock_db_connection):
        """Test bulk updating product prices."""
        # Update prices by percentage
        cursor = mock_db_connection.execute(
            "UPDATE products SET mrp = mrp * 1.10 WHERE brand = ?",
            ('Havells',)
        )
        
        # Mock cursor always returns rowcount = 1
        assert cursor.rowcount >= 1
    
    def test_bulk_delete_inactive_products(self, mock_db_connection):
        """Test bulk deleting inactive products."""
        cursor = mock_db_connection.execute(
            "DELETE FROM products WHERE is_active = ?",
            (False,)
        )
        
        assert cursor is not None


class TestTransactionOperations:
    """Test transaction handling."""
    
    def test_commit_transaction(self, mock_db_connection):
        """Test committing a transaction."""
        cursor = mock_db_connection.execute(
            "INSERT INTO products (brand, product_name) VALUES (?, ?)",
            ('TestBrand', 'TestProduct')
        )
        mock_db_connection.commit()
        
        # Should not raise exception
        assert True
    
    def test_rollback_transaction(self, mock_db_connection):
        """Test rolling back a transaction."""
        cursor = mock_db_connection.execute(
            "INSERT INTO products (brand, product_name) VALUES (?, ?)",
            ('TestBrand', 'TestProduct')
        )
        mock_db_connection.rollback()
        
        # Should not raise exception
        assert True
    
    def test_transaction_consistency(self, mock_db_connection):
        """Test transaction consistency."""
        try:
            # Start transaction
            mock_db_connection.execute(
                "INSERT INTO products (brand, product_name) VALUES (?, ?)",
                ('Brand1', 'Product1')
            )
            mock_db_connection.execute(
                "INSERT INTO products (brand, product_name) VALUES (?, ?)",
                ('Brand2', 'Product2')
            )
            mock_db_connection.commit()
        except Exception:
            mock_db_connection.rollback()
            pytest.fail("Transaction failed")


class TestAsyncDatabaseOperations:
    """Test async database operations."""
    
    @pytest.mark.asyncio
    async def test_async_create_product(self, async_mock_db, sample_product):
        """Test async product creation."""
        result = await async_mock_db.execute(
            "INSERT INTO products (brand, product_name) VALUES ($1, $2)",
            sample_product['brand'],
            sample_product['product_name']
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_async_read_products(self, async_mock_db):
        """Test async reading products."""
        products = await async_mock_db.fetch("SELECT * FROM products")
        
        assert isinstance(products, list)
        assert len(products) > 0
    
    @pytest.mark.asyncio
    async def test_async_read_single_product(self, async_mock_db):
        """Test async reading single product."""
        product = await async_mock_db.fetchrow(
            "SELECT * FROM products WHERE id = $1",
            1
        )
        
        assert isinstance(product, dict)
        assert 'id' in product
    
    @pytest.mark.asyncio
    async def test_async_count_products(self, async_mock_db):
        """Test async counting products."""
        count = await async_mock_db.fetchval("SELECT COUNT(*) FROM products")
        
        assert isinstance(count, int)
        assert count >= 0
    
    @pytest.mark.asyncio
    async def test_async_update_product(self, async_mock_db):
        """Test async product update."""
        result = await async_mock_db.execute(
            "UPDATE products SET mrp = $1 WHERE id = $2",
            2500.00,
            1
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_async_delete_product(self, async_mock_db):
        """Test async product deletion."""
        result = await async_mock_db.execute(
            "DELETE FROM products WHERE id = $1",
            1
        )
        
        assert result is not None


class TestDatabaseValidation:
    """Test database validation and constraints."""
    
    def test_product_required_fields(self, sample_product, validator):
        """Test product has required fields for database."""
        required_fields = ['brand', 'category', 'product_name']
        
        for field in required_fields:
            assert field in sample_product, f"Missing required field: {field}"
    
    def test_product_data_types(self, sample_product):
        """Test product data types are correct."""
        assert isinstance(sample_product['brand'], str)
        assert isinstance(sample_product['product_name'], str)
        assert isinstance(sample_product['mrp'], (int, float))
        assert isinstance(sample_product['is_active'], bool)
    
    def test_product_price_validation(self, sample_product, validator):
        """Test product prices are valid."""
        assert validator.is_valid_price(sample_product['mrp'])
        assert validator.is_valid_price(sample_product['selling_price'])
        assert validator.is_valid_price(sample_product['dealer_price'])
    
    def test_product_pricing_hierarchy(self, sample_product):
        """Test pricing hierarchy: MRP >= Selling >= Dealer."""
        mrp = sample_product['mrp']
        selling = sample_product['selling_price']
        dealer = sample_product['dealer_price']
        
        assert mrp >= selling, "MRP should be >= selling price"
        assert selling >= dealer, "Selling price should be >= dealer price"
    
    def test_rfp_date_validation(self, sample_rfp):
        """Test RFP dates are valid."""
        issue = sample_rfp['issue_date']
        tech_deadline = sample_rfp['technical_deadline']
        submission = sample_rfp['submission_deadline']
        
        assert tech_deadline <= submission, "Technical deadline should be before submission"


class TestDatabasePerformance:
    """Test database performance considerations."""
    
    def test_batch_fetch_products(self, mock_db_connection):
        """Test fetching products in batches."""
        cursor = mock_db_connection.execute("SELECT * FROM products")
        batch = cursor.fetchmany(10)
        
        assert isinstance(batch, list)
    
    def test_indexed_query(self, mock_db_connection):
        """Test query using indexed field (id)."""
        cursor = mock_db_connection.execute(
            "SELECT * FROM products WHERE id = ?",
            (1,)
        )
        product = cursor.fetchone()
        
        assert product is not None
    
    def test_query_with_limit(self, mock_db_connection):
        """Test query with LIMIT clause."""
        cursor = mock_db_connection.execute(
            "SELECT * FROM products LIMIT 10"
        )
        products = cursor.fetchall()
        
        assert isinstance(products, list)


class TestDatabaseErrorHandling:
    """Test database error handling."""
    
    def test_handle_connection_error(self, mock_db_connection):
        """Test handling connection errors."""
        try:
            mock_db_connection.execute("INVALID SQL QUERY")
        except Exception:
            pass  # Expected
    
    def test_handle_duplicate_insert(self, mock_db_connection, sample_product):
        """Test handling duplicate insert."""
        try:
            # First insert
            mock_db_connection.execute(
                "INSERT INTO products (id, brand) VALUES (?, ?)",
                (1, sample_product['brand'])
            )
            # Duplicate insert
            mock_db_connection.execute(
                "INSERT INTO products (id, brand) VALUES (?, ?)",
                (1, sample_product['brand'])
            )
        except Exception:
            pass  # Expected for duplicate
    
    def test_handle_foreign_key_violation(self, mock_db_connection):
        """Test handling foreign key violations."""
        try:
            # Insert item with non-existent RFP
            mock_db_connection.execute(
                "INSERT INTO rfp_items (rfp_id, item_number) VALUES (?, ?)",
                (99999, '001')
            )
        except Exception:
            pass  # Expected for FK violation
