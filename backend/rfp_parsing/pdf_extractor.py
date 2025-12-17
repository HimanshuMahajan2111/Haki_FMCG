"""
PDF Extractor - Extract text, tables, and metadata from PDF documents using pdfplumber.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
import pdfplumber
import pandas as pd
import structlog
import re

logger = structlog.get_logger()


@dataclass
class PDFExtractionResult:
    """Result of PDF extraction."""
    file_path: str
    total_pages: int
    text: str = ""
    text_by_page: List[str] = field(default_factory=list)
    tables: List[pd.DataFrame] = field(default_factory=list)
    tables_by_page: Dict[int, List[pd.DataFrame]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'file_path': self.file_path,
            'total_pages': self.total_pages,
            'text': self.text,
            'text_by_page': self.text_by_page,
            'tables_count': len(self.tables),
            'metadata': self.metadata
        }


class PDFExtractor:
    """Extract text and tables from PDF documents using pdfplumber."""
    
    def __init__(self):
        """Initialize PDF extractor."""
        self.logger = logger.bind(component="PDFExtractor")
    
    def extract(
        self,
        pdf_path: str,
        extract_text: bool = True,
        extract_tables: bool = True,
        table_settings: Optional[Dict[str, Any]] = None
    ) -> PDFExtractionResult:
        """Extract content from PDF file.
        
        Args:
            pdf_path: Path to PDF file
            extract_text: Whether to extract text content
            extract_tables: Whether to extract tables
            table_settings: Optional pdfplumber table extraction settings
            
        Returns:
            PDFExtractionResult with extracted content
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        self.logger.info("Extracting PDF content", file=str(pdf_path))
        
        # Default table settings
        if table_settings is None:
            table_settings = {
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "intersection_tolerance": 3,
            }
        
        result = PDFExtractionResult(
            file_path=str(pdf_path),
            total_pages=0
        )
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                result.total_pages = len(pdf.pages)
                result.metadata = pdf.metadata or {}
                
                self.logger.info(
                    "Processing PDF",
                    pages=result.total_pages,
                    metadata_keys=list(result.metadata.keys())
                )
                
                all_text = []
                
                for page_num, page in enumerate(pdf.pages, 1):
                    # Extract text
                    if extract_text:
                        page_text = page.extract_text() or ""
                        result.text_by_page.append(page_text)
                        all_text.append(page_text)
                    
                    # Extract tables
                    if extract_tables:
                        tables = page.extract_tables(table_settings=table_settings)
                        
                        if tables:
                            page_dataframes = []
                            for table_data in tables:
                                if table_data and len(table_data) > 0:
                                    # Convert to DataFrame
                                    df = pd.DataFrame(table_data[1:], columns=table_data[0])
                                    # Clean column names
                                    df.columns = [str(col).strip() if col else f"Column_{i}" 
                                                 for i, col in enumerate(df.columns)]
                                    page_dataframes.append(df)
                                    result.tables.append(df)
                            
                            if page_dataframes:
                                result.tables_by_page[page_num] = page_dataframes
                
                # Combine all text
                result.text = "\n\n".join(all_text)
                
                self.logger.info(
                    "PDF extraction completed",
                    pages=result.total_pages,
                    text_length=len(result.text),
                    tables_found=len(result.tables)
                )
                
                return result
                
        except Exception as e:
            self.logger.error("PDF extraction failed", error=str(e), file=str(pdf_path))
            raise
    
    def extract_text_only(self, pdf_path: str) -> str:
        """Extract only text from PDF (faster).
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        result = self.extract(pdf_path, extract_text=True, extract_tables=False)
        return result.text
    
    def extract_tables_only(self, pdf_path: str) -> List[pd.DataFrame]:
        """Extract only tables from PDF.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of DataFrames containing tables
        """
        result = self.extract(pdf_path, extract_text=False, extract_tables=True)
        return result.tables
    
    def find_section(self, text: str, section_name: str) -> Optional[str]:
        """Find a specific section in the text.
        
        Args:
            text: Full text content
            section_name: Section name/heading to find
            
        Returns:
            Section text or None if not found
        """
        # Try to find section by heading patterns
        patterns = [
            rf"(?i)^{re.escape(section_name)}[\s:]*$",  # Exact match on line
            rf"(?i)\n{re.escape(section_name)}[\s:]*\n",  # With newlines
            rf"(?i)^\d+\.?\s*{re.escape(section_name)}",  # With numbering
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                # Extract text from this section to the next section
                start_pos = match.end()
                
                # Find next section (typically starts with number or uppercase heading)
                next_section = re.search(r'\n\d+\.?\s+[A-Z]', text[start_pos:])
                
                if next_section:
                    end_pos = start_pos + next_section.start()
                    return text[start_pos:end_pos].strip()
                else:
                    # Return rest of document
                    return text[start_pos:].strip()
        
        return None
    
    def extract_key_value_pairs(self, text: str) -> Dict[str, str]:
        """Extract key-value pairs from text (e.g., metadata, properties).
        
        Args:
            text: Text content
            
        Returns:
            Dictionary of key-value pairs
        """
        pairs = {}
        
        # Pattern: "Key: Value" or "Key - Value"
        pattern = r'([A-Za-z][A-Za-z\s]+?):\s*(.+?)(?:\n|$)'
        matches = re.findall(pattern, text)
        
        for key, value in matches:
            key = key.strip()
            value = value.strip()
            if key and value:
                pairs[key] = value
        
        return pairs
    
    def clean_text(self, text: str) -> str:
        """Clean extracted text (remove extra whitespace, special characters).
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        # Remove multiple spaces
        text = re.sub(r' +', ' ', text)
        
        # Remove multiple newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove special characters but keep common punctuation
        text = re.sub(r'[^\w\s.,;:()\-\'"/@%]+', '', text)
        
        return text.strip()
