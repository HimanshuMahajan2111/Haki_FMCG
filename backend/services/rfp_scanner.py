"""RFP Scanner service - scans directory for new RFP PDFs."""
from pathlib import Path
from typing import List
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config.settings import settings
from db.models import RFP, RFPStatus

logger = structlog.get_logger()


class RFPScanner:
    """Scan directory for RFP documents."""
    
    def __init__(self, db: AsyncSession):
        """Initialize RFP scanner.
        
        Args:
            db: Database session
        """
        self.db = db
        self.rfp_dir = Path(settings.rfp_input_dir)
        self.logger = logger.bind(component="RFPScanner")
    
    async def scan_directory(self, force_rescan: bool = False):
        """Scan directory for new RFPs.
        
        Args:
            force_rescan: If True, re-process all files
        """
        self.logger.info("Starting RFP scan", directory=str(self.rfp_dir))
        
        if not self.rfp_dir.exists():
            self.logger.warning("RFP directory does not exist", path=str(self.rfp_dir))
            return
        
        # Get existing RFPs
        existing_files = await self._get_existing_files()
        
        # Scan for PDF files
        pdf_files = list(self.rfp_dir.glob("*.pdf"))
        
        new_count = 0
        for pdf_file in pdf_files:
            file_path = str(pdf_file)
            
            if force_rescan or file_path not in existing_files:
                await self._create_rfp_record(pdf_file)
                new_count += 1
        
        self.logger.info(
            "RFP scan completed",
            total_files=len(pdf_files),
            new_files=new_count
        )
    
    async def _get_existing_files(self) -> List[str]:
        """Get list of existing RFP file paths.
        
        Returns:
            List of file paths
        """
        query = select(RFP.file_path)
        result = await self.db.execute(query)
        return [row[0] for row in result.all()]
    
    async def _create_rfp_record(self, pdf_file: Path):
        """Create database record for RFP.
        
        Args:
            pdf_file: Path to PDF file
        """
        self.logger.info("Creating RFP record", file=pdf_file.name)
        
        rfp = RFP(
            title=self._extract_title(pdf_file),
            source="File System",
            file_path=str(pdf_file),
            status=RFPStatus.DISCOVERED,
        )
        
        self.db.add(rfp)
        await self.db.commit()
        
        self.logger.info("RFP record created", rfp_id=rfp.id)
    
    def _extract_title(self, pdf_file: Path) -> str:
        """Extract title from filename.
        
        Args:
            pdf_file: PDF file path
            
        Returns:
            Title string
        """
        # Remove .pdf extension and format
        title = pdf_file.stem
        title = title.replace("_", " ").replace("-", " ")
        return title.title()
