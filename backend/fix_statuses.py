"""
Quick script to fix old 'completed' status values to 'reviewed' in database
"""
import sqlite3
import os

# Path to database
db_path = os.path.join(os.path.dirname(__file__), 'fmcg_enhanced.db')

print(f"Connecting to database: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check current statuses
    cursor.execute("SELECT id, title, status FROM rfps WHERE status='completed'")
    old_records = cursor.fetchall()
    
    if old_records:
        print(f"\nFound {len(old_records)} RFPs with 'completed' status:")
        for rfp_id, title, status in old_records:
            print(f"  - RFP #{rfp_id}: {title} (status={status})")
        
        # Update to 'reviewed'
        cursor.execute("UPDATE rfps SET status='reviewed' WHERE status='completed'")
        count = cursor.rowcount
        conn.commit()
        
        print(f"\n✅ Successfully updated {count} RFP records from 'completed' to 'reviewed'")
    else:
        print("\n✅ No RFPs with 'completed' status found - database is already correct!")
    
    # Show current status distribution
    cursor.execute("SELECT status, COUNT(*) FROM rfps GROUP BY status")
    status_counts = cursor.fetchall()
    print("\n📊 Current status distribution:")
    for status, count in status_counts:
        print(f"  - {status}: {count} RFPs")
    
    conn.close()
    print("\n✨ Database fix complete!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
