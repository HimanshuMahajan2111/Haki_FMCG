import sqlite3

conn = sqlite3.connect('rfp_system.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(products)')
print('Products table schema:')
for row in cursor.fetchall():
    col_name = row[1]
    col_type = row[2]
    not_null = row[3]
    nullable = 'NO' if not_null == 1 else 'YES'
    print(f'  {col_name}: {col_type} (nullable={nullable})')
conn.close()
