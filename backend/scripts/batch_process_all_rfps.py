"""
Batch Process All RFPs - Match Top 3 Products and Generate Output Documents
Processes each RFP, finds best product matches, and creates output files.
"""
import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from db.database import AsyncSessionLocal
from db.models import RFP
from agents.product_repository import ProductRepository
from agents.master_agent import MasterAgent
from agents.technical_agent_worker import TechnicalAgentWorker
from agents.pricing_agent_worker import PricingAgentWorker
import structlog

logger = structlog.get_logger()


async def process_single_rfp(rfp_id: int, master_agent: MasterAgent, output_dir: Path) -> Dict[str, Any]:
    """Process a single RFP and generate output documents."""
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(RFP).where(RFP.id == rfp_id))
        rfp = result.scalar_one_or_none()
        
        if not rfp:
            return {'rfp_id': rfp_id, 'status': 'not_found'}
        
        logger.info(f"Processing RFP #{rfp_id}: {rfp.title}")
        
        # Prepare RFP input
        structured_data = rfp.structured_data
        if isinstance(structured_data, str):
            try:
                structured_data = json.loads(structured_data)
            except:
                structured_data = {}
        
        rfp_input = {
            'rfp_id': rfp.id,
            'rfp_title': rfp.title,
            'organization': 'Unknown',
            'structured_data': structured_data,
            'specifications': structured_data.get('specifications', []),
            'required_standards': structured_data.get('standards', []),
            'scope_of_supply': []
        }
        
        # Process through MasterAgent
        try:
            result = await master_agent.process_rfp(rfp_input)
            
            # Extract matched products
            matched_products = []
            if 'technical_recommendations' in result:
                tech_recs = result['technical_recommendations']
                matched_products = tech_recs.get('matched_products', [])
            
            # Save to database
            if matched_products:
                rfp.matched_products = json.dumps(matched_products)
                rfp.status = 'REVIEWED'
                await db.commit()
            
            # Generate output document
            output_file = output_dir / f"RFP_{rfp_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            output_data = {
                'rfp_id': rfp.id,
                'rfp_title': rfp.title,
                'processed_at': datetime.now().isoformat(),
                'specifications_count': len(structured_data.get('specifications', [])),
                'standards_count': len(structured_data.get('standards', [])),
                'matched_products_count': len(matched_products),
                'matched_products': matched_products,
                'processing_result': result
            }
            
            with open(output_file, 'w') as f:
                json.dump(output_data, f, indent=2)
            
            return {
                'rfp_id': rfp_id,
                'title': rfp.title,
                'status': 'success',
                'products_matched': len(matched_products),
                'output_file': str(output_file)
            }
            
        except Exception as e:
            logger.error(f"Error processing RFP #{rfp_id}: {e}")
            return {
                'rfp_id': rfp_id,
                'title': rfp.title,
                'status': 'error',
                'error': str(e)
            }


async def main():
    """Batch process all RFPs."""
    print("\n" + "="*70)
    print("  BATCH PROCESSING ALL RFPS - TOP 3 PRODUCT MATCHING")
    print("="*70 + "\n")
    
    # Create output directory
    output_dir = Path(__file__).parent.parent / 'outputs' / 'rfp_processing'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"✓ Output directory: {output_dir}\n")
    
    # Initialize agents
    print("Initializing Master Agent with product matching...")
    product_repo = ProductRepository(use_database=True)
    technical_agent = TechnicalAgentWorker(product_repository=product_repo)
    pricing_agent = PricingAgentWorker()
    master_agent = MasterAgent(technical_agent=technical_agent, pricing_agent=pricing_agent)
    
    # Get product count
    product_count = await product_repo.get_product_count()
    print(f"✓ Product database: {product_count} products loaded\n")
    
    # Get all RFPs
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(RFP)
            .where(RFP.structured_data.isnot(None))
            .order_by(RFP.id)
        )
        rfps = result.scalars().all()
    
    print(f"✓ Found {len(rfps)} RFPs to process\n")
    print("="*70)
    
    # Process each RFP
    results = []
    success_count = 0
    error_count = 0
    
    for i, rfp in enumerate(rfps, 1):
        print(f"\n[{i}/{len(rfps)}] Processing RFP #{rfp.id}: {rfp.title[:60]}...")
        
        result = await process_single_rfp(rfp.id, master_agent, output_dir)
        results.append(result)
        
        if result['status'] == 'success':
            success_count += 1
            products_matched = result.get('products_matched', 0)
            print(f"  ✓ Success: {products_matched} products matched")
            print(f"  ✓ Output: {Path(result['output_file']).name}")
        else:
            error_count += 1
            print(f"  ✗ Error: {result.get('error', 'Unknown error')}")
        
        # Small delay to avoid overload
        await asyncio.sleep(1)
    
    # Generate summary report
    summary_file = output_dir / f"batch_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    summary = {
        'processed_at': datetime.now().isoformat(),
        'total_rfps': len(rfps),
        'successful': success_count,
        'errors': error_count,
        'product_database_size': product_count,
        'results': results
    }
    
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Print summary
    print("\n" + "="*70)
    print("  BATCH PROCESSING SUMMARY")
    print("="*70)
    print(f"✓ Total RFPs Processed: {len(rfps)}")
    print(f"✓ Successful: {success_count}")
    print(f"✗ Errors: {error_count}")
    print(f"✓ Product Database: {product_count} products")
    print(f"✓ Output Directory: {output_dir}")
    print(f"✓ Summary Report: {summary_file.name}")
    
    # Print detailed results
    print("\n" + "-"*70)
    print("DETAILED RESULTS:")
    print("-"*70)
    
    for result in results:
        status_icon = "✓" if result['status'] == 'success' else "✗"
        products = result.get('products_matched', 0)
        print(f"{status_icon} RFP #{result['rfp_id']}: {result['title'][:50]}")
        if result['status'] == 'success':
            print(f"    Products matched: {products}")
        else:
            print(f"    Error: {result.get('error', 'Unknown')}")
    
    print("\n" + "="*70)
    print("✅ BATCH PROCESSING COMPLETE!")
    print("="*70 + "\n")
    
    print(f"📁 All output files saved to: {output_dir}")
    print(f"📊 Summary report: {summary_file.name}\n")


if __name__ == '__main__':
    asyncio.run(main())
