"""
EMERGENCY FIX - Update status from 'reviewed' to 'REVIEWED'
"""
import sqlite3
import os

# Try multiple database locations
db_locations = [
    'd:\\Haki_FMCG\\backend\\fmcg_enhanced.db',
    'fmcg_enhanced.db',
    './fmcg_enhanced.db',
    '../fmcg_enhanced.db'
]

db_path = None
for path in db_locations:
    if os.path.exists(path):
        db_path = path
        break

if not db_path:
    print("❌ Database not found! Locations tried:")
    for loc in db_locations:
        print(f"   - {loc}")
    exit(1)

print(f"✓ Found database: {db_path}\n")

# Connect and fix
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check current status values
cursor.execute("SELECT status, COUNT(*) FROM rfps GROUP BY status")
print("Current status values:")
for status, count in cursor.fetchall():
    print(f"  - '{status}': {count} RFPs")

# Fix the lowercase status
cursor.execute("UPDATE rfps SET status = 'REVIEWED' WHERE LOWER(status) = 'reviewed'")
affected = cursor.rowcount
conn.commit()

print(f"\n✅ FIXED! Updated {affected} RFP record(s)")
print("✅ Backend should work now!")
print("🎉 Refresh your browser at http://localhost:3000/rfp/process/77")

conn.close()
