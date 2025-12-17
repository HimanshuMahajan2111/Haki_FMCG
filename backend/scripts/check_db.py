"""Check database products"""
import sqlite3

conn = sqlite3.connect('db/fmcg_enhanced.db')
cursor = conn.cursor()

# Get all tables
tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables in database:")
for table in tables:
    print(f"  - {table[0]}")

# Check products table
try:
    count = cursor.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    print(f"\nProducts table count: {count}")
    
    if count > 0:
        # Get first 3 products
        products = cursor.execute("SELECT id, brand, product_name FROM products LIMIT 3").fetchall()
        print("\nFirst 3 products:")
        for p in products:
            print(f"  {p[0]}: {p[1]} - {p[2]}")
except Exception as e:
    print(f"\nError checking products: {e}")

conn.close()
