"""Quick script to check RFP records in database."""
from db.database import engine
from db.models import RFP
from sqlalchemy.orm import Session
from sqlalchemy import select
import json

db = Session(engine)

# Get all RFPs
rfps = db.execute(select(RFP).limit(10)).scalars().all()

print(f"\n{'='*80}")
print(f"Found {len(rfps)} RFPs in database")
print(f"{'='*80}\n")

for rfp in rfps:
    print(f"RFP #{rfp.id}: {rfp.title[:60]}")
    print(f"  File Path: {rfp.file_path}")
    print(f"  Status: {rfp.status}")
    if rfp.structured_data:
        print(f"  Has Structured Data: Yes ({len(str(rfp.structured_data))} chars)")
        # Try to parse as JSON
        try:
            data = json.loads(rfp.structured_data) if isinstance(rfp.structured_data, str) else rfp.structured_data
            print(f"  Data Keys: {list(data.keys())[:5]}")
        except:
            print(f"  Data Preview: {str(rfp.structured_data)[:100]}")
    else:
        print(f"  Has Structured Data: No")
    print()

db.close()
