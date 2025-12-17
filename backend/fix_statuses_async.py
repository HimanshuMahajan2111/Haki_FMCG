"""
Async script to fix 'completed' status values to 'reviewed'
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import text
from db.database import get_db

async def fix_statuses():
    """Fix old 'completed' status to 'reviewed'"""
    print("Connecting to database...")
    
    async for session in get_db():
        try:
            # Check for completed statuses
            result = await session.execute(
                text("SELECT id, title FROM rfps WHERE status='completed'")
            )
            old_records = result.fetchall()
            
            if old_records:
                print(f"\nFound {len(old_records)} RFPs with 'completed' status:")
                for row in old_records:
                    print(f"  - RFP #{row[0]}: {row[1]}")
                
                # Update to 'reviewed'
                result = await session.execute(
                    text("UPDATE rfps SET status='reviewed' WHERE status='completed'")
                )
                await session.commit()
                
                print(f"\n✅ Successfully updated {result.rowcount} RFP records!")
            else:
                print("\n✅ No RFPs with 'completed' status found!")
            
            # Show status distribution
            result = await session.execute(
                text("SELECT status, COUNT(*) as count FROM rfps GROUP BY status")
            )
            status_counts = result.fetchall()
            print("\n📊 Current status distribution:")
            for row in status_counts:
                print(f"  - {row[0]}: {row[1]} RFPs")
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            break  # Exit after first session
    
    print("\n✨ Done!")

if __name__ == "__main__":
    asyncio.run(fix_statuses())
