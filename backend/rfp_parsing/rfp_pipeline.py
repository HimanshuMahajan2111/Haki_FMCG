"""
RFP Pipeline - Main pipeline for processing RFP documents.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
import pandas as pd
import structlog

from rfp_parsing.pdf_extractor import PDFExtractor, PDFExtractionResult
from rfp_parsing.boq_extractor import BOQExtractor, BOQItem
from rfp_parsing.spec_parser import SpecificationParser, Specification
from rfp_parsing.date_extractor import DateExtractor, Deadline
from rfp_parsing.testing_extractor import TestingRequirementExtractor, TestingRequirement
from rfp_parsing.ocr_handler import OCRHandler
from rfp_parsing.quality_metrics import QualityMetrics, PreviewGenerator

logger = structlog.get_logger()


@dataclass
class RFPDocument:
    """Complete RFP document with extracted data."""
    file_path: str
    total_pages: int
    
    # Extracted content
    full_text: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # BOQ data
    boq_items: List[BOQItem] = field(default_factory=list)
    boq_df: Optional[pd.DataFrame] = None
    
    # Specifications
    specifications: List[Specification] = field(default_factory=list)
    specs_by_category: Dict[str, List[Specification]] = field(default_factory=dict)
    
    # Sections
    sections: Dict[str, str] = field(default_factory=dict)
    
    # Dates and deadlines
    deadlines: List[Any] = field(default_factory=list)  # List[Deadline]
    submission_deadline: Optional[Any] = None  # Optional[Deadline]
    
    # Testing requirements
    testing_requirements: List[Any] = field(default_factory=list)  # List[TestingRequirement]
    standards: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    
    # Quality metrics
    quality_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Statistics
    stats: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'file_path': self.file_path,
            'total_pages': self.total_pages,
            'metadata': self.metadata,
            'boq_items_count': len(self.boq_items),
            'specifications_count': len(self.specifications),
            'sections': list(self.sections.keys()),
            'deadlines_count': len(self.deadlines),
            'submission_deadline': self.submission_deadline.to_dict() if self.submission_deadline else None,
            'testing_requirements_count': len(self.testing_requirements),
            'standards_count': len(self.standards),
            'certifications_count': len(self.certifications),
            'quality_metrics': self.quality_metrics,
            'stats': self.stats
        }
    
    def get_mandatory_specs(self) -> List[Specification]:
        """Get mandatory specifications."""
        return [spec for spec in self.specifications if spec.requirement_type == "mandatory"]
    
    def get_boq_summary(self) -> Dict[str, Any]:
        """Get BOQ summary statistics."""
        if not self.boq_items:
            return {}
        
        total_quantity = sum(item.quantity for item in self.boq_items)
        total_amount = sum(item.amount for item in self.boq_items if item.amount)
        
        categories = {}
        for item in self.boq_items:
            cat = item.category or "Uncategorized"
            if cat not in categories:
                categories[cat] = 0
            categories[cat] += 1
        
        return {
            'total_items': len(self.boq_items),
            'total_quantity': total_quantity,
            'total_amount': total_amount,
            'categories': categories
        }


class RFPPipeline:
    """Complete pipeline for processing RFP documents."""
    
    def __init__(
        self,
        extract_boq: bool = True,
        extract_specs: bool = True,
        extract_dates: bool = True,
        extract_testing: bool = True,
        use_ocr_fallback: bool = False,
        section_headings: Optional[List[str]] = None
    ):
        """Initialize RFP pipeline.
        
        Args:
            extract_boq: Whether to extract BOQ
            extract_specs: Whether to extract specifications
            extract_dates: Whether to extract dates and deadlines
            extract_testing: Whether to extract testing requirements
            use_ocr_fallback: Whether to use OCR for scanned PDFs
            section_headings: List of section headings to extract
        """
        self.pdf_extractor = PDFExtractor()
        self.boq_extractor = BOQExtractor()
        self.spec_parser = SpecificationParser()
        self.date_extractor = DateExtractor()
        self.testing_extractor = TestingRequirementExtractor()
        self.ocr_handler = OCRHandler()
        self.quality_calculator = QualityMetrics()
        self.preview_generator = PreviewGenerator()
        
        self.extract_boq = extract_boq
        self.extract_specs = extract_specs
        self.extract_dates = extract_dates
        self.extract_testing = extract_testing
        self.use_ocr_fallback = use_ocr_fallback
        self.section_headings = section_headings or [
            "Technical Specifications",
            "Scope of Work",
            "Bill of Quantities",
            "Terms and Conditions",
            "Submission Requirements"
        ]
        
        self.logger = logger.bind(component="RFPPipeline")
    
    def process(self, pdf_path: str) -> RFPDocument:
        """Process RFP PDF document.
        
        Args:
            pdf_path: Path to RFP PDF file
            
        Returns:
            RFPDocument with all extracted data
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"RFP PDF not found: {pdf_path}")
        
        self.logger.info("Processing RFP document", file=str(pdf_path))
        
        # Initialize RFP document
        rfp_doc = RFPDocument(
            file_path=str(pdf_path),
            total_pages=0
        )
        
        try:
            # Step 1: Extract PDF content
            self.logger.info("Step 1: Extracting PDF content")
            pdf_result = self.pdf_extractor.extract(
                pdf_path,
                extract_text=True,
                extract_tables=True
            )
            
            rfp_doc.full_text = pdf_result.text
            rfp_doc.total_pages = pdf_result.total_pages
            rfp_doc.metadata = pdf_result.metadata
            
            # Step 2: Extract sections
            self.logger.info("Step 2: Extracting sections")
            rfp_doc.sections = self._extract_sections(pdf_result.text)
            
            # Step 3: Extract BOQ
            if self.extract_boq and pdf_result.tables:
                self.logger.info("Step 3: Extracting BOQ", tables=len(pdf_result.tables))
                rfp_doc.boq_items = self.boq_extractor.extract_from_multiple_tables(
                    pdf_result.tables
                )
                
                if rfp_doc.boq_items:
                    rfp_doc.boq_df = self.boq_extractor.to_dataframe(rfp_doc.boq_items)
            
            # Step 4: Extract specifications
            if self.extract_specs:
                self.logger.info("Step 4: Extracting specifications")
                rfp_doc.specifications = self._extract_all_specs(rfp_doc)
                rfp_doc.specs_by_category = self.spec_parser.group_by_category(
                    rfp_doc.specifications
                )
            
            # Step 5: Extract dates and deadlines
            if self.extract_dates:
                self.logger.info("Step 5: Extracting dates and deadlines")
                rfp_doc.deadlines = self.date_extractor.extract_deadlines(rfp_doc.full_text)
                rfp_doc.submission_deadline = self.date_extractor.find_submission_deadline(rfp_doc.full_text)
            
            # Step 6: Extract testing requirements
            if self.extract_testing:
                self.logger.info("Step 6: Extracting testing requirements")
                rfp_doc.testing_requirements = self.testing_extractor.extract_testing_requirements(rfp_doc.full_text)
                rfp_doc.standards = self.testing_extractor.extract_standards(rfp_doc.full_text)
                rfp_doc.certifications = self.testing_extractor.extract_certifications(rfp_doc.full_text)
            
            # Step 7: Calculate quality metrics
            self.logger.info("Step 7: Calculating quality metrics")
            text_quality = self.quality_calculator.calculate_text_quality(rfp_doc.full_text)
            table_quality = self.quality_calculator.calculate_table_quality(pdf_result.tables)
            rfp_doc.quality_metrics = self.quality_calculator.calculate_overall_quality(
                text_quality,
                table_quality,
                len(rfp_doc.boq_items),
                len(rfp_doc.specifications)
            )
            
            # Step 8: Calculate statistics
            rfp_doc.stats = self._calculate_stats(rfp_doc)
            
            self.logger.info(
                "RFP processing completed",
                boq_items=len(rfp_doc.boq_items),
                specifications=len(rfp_doc.specifications),
                deadlines=len(rfp_doc.deadlines),
                testing_requirements=len(rfp_doc.testing_requirements),
                quality_score=rfp_doc.quality_metrics.get('overall_score', 0),
                sections=len(rfp_doc.sections)
            )
            
            return rfp_doc
            
        except Exception as e:
            self.logger.error("RFP processing failed", error=str(e), file=str(pdf_path))
            
            # Try OCR fallback if enabled and text extraction failed
            if self.use_ocr_fallback and self.ocr_handler.is_available():
                self.logger.info("Attempting OCR fallback")
                try:
                    ocr_text = self.ocr_handler.extract_text_from_pdf(str(pdf_path))
                    if ocr_text:
                        rfp_doc.full_text = ocr_text
                        rfp_doc.metadata['ocr_used'] = True
                        self.logger.info("OCR fallback successful", text_length=len(ocr_text))
                        return rfp_doc
                except Exception as ocr_error:
                    self.logger.error("OCR fallback failed", error=str(ocr_error))
            
            raise
    
    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Extract predefined sections from text.
        
        Args:
            text: Full RFP text
            
        Returns:
            Dictionary of section names to content
        """
        sections = {}
        
        for heading in self.section_headings:
            section_text = self.pdf_extractor.find_section(text, heading)
            if section_text:
                sections[heading] = section_text
                self.logger.debug(
                    "Section extracted",
                    section=heading,
                    length=len(section_text)
                )
        
        return sections
    
    def _extract_all_specs(self, rfp_doc: RFPDocument) -> List[Specification]:
        """Extract specifications from all sources.
        
        Args:
            rfp_doc: RFP document
            
        Returns:
            List of all specifications
        """
        all_specs = []
        
        # Extract from full text
        general_specs = self.spec_parser.parse(rfp_doc.full_text, category="general")
        all_specs.extend(general_specs)
        
        # Extract from each section
        for section_name, section_text in rfp_doc.sections.items():
            section_specs = self.spec_parser.parse(section_text, category=section_name)
            all_specs.extend(section_specs)
        
        # Remove duplicates (same parameter and value)
        unique_specs = self._deduplicate_specs(all_specs)
        
        return unique_specs
    
    def _deduplicate_specs(
        self,
        specifications: List[Specification]
    ) -> List[Specification]:
        """Remove duplicate specifications.
        
        Args:
            specifications: List of specifications
            
        Returns:
            Deduplicated list
        """
        seen = set()
        unique = []
        
        for spec in specifications:
            key = (spec.category, spec.parameter, spec.value)
            if key not in seen:
                seen.add(key)
                unique.append(spec)
        
        return unique
    
    def _calculate_stats(self, rfp_doc: RFPDocument) -> Dict[str, Any]:
        """Calculate document statistics.
        
        Args:
            rfp_doc: RFP document
            
        Returns:
            Statistics dictionary
        """
        stats = {
            'total_pages': rfp_doc.total_pages,
            'text_length': len(rfp_doc.full_text),
            'sections_count': len(rfp_doc.sections),
            'boq_items_count': len(rfp_doc.boq_items),
            'specifications_count': len(rfp_doc.specifications),
        }
        
        # BOQ statistics
        if rfp_doc.boq_items:
            stats['boq_summary'] = rfp_doc.get_boq_summary()
        
        # Specification statistics
        if rfp_doc.specifications:
            stats['mandatory_specs'] = len(rfp_doc.get_mandatory_specs())
            stats['specs_by_category'] = {
                cat: len(specs) 
                for cat, specs in rfp_doc.specs_by_category.items()
            }
        
        return stats
    
    def process_batch(self, pdf_paths: List[str]) -> List[RFPDocument]:
        """Process multiple RFP documents.
        
        Args:
            pdf_paths: List of PDF file paths
            
        Returns:
            List of RFPDocument objects
        """
        self.logger.info("Processing batch of RFP documents", count=len(pdf_paths))
        
        results = []
        
        for pdf_path in pdf_paths:
            try:
                rfp_doc = self.process(pdf_path)
                results.append(rfp_doc)
            except Exception as e:
                self.logger.error(
                    "Failed to process RFP",
                    file=pdf_path,
                    error=str(e)
                )
        
        self.logger.info(
            "Batch processing completed",
            total=len(pdf_paths),
            successful=len(results)
        )
        
        return results
    
    def export_boq_to_csv(self, rfp_doc: RFPDocument, output_path: str):
        """Export BOQ to CSV file.
        
        Args:
            rfp_doc: RFP document
            output_path: Output CSV file path
        """
        if rfp_doc.boq_df is not None and not rfp_doc.boq_df.empty:
            rfp_doc.boq_df.to_csv(output_path, index=False)
            self.logger.info("BOQ exported to CSV", file=output_path)
        else:
            self.logger.warning("No BOQ data to export")
    
    def export_specs_to_csv(self, rfp_doc: RFPDocument, output_path: str):
        """Export specifications to CSV file.
        
        Args:
            rfp_doc: RFP document
            output_path: Output CSV file path
        """
        if rfp_doc.specifications:
            specs_data = self.spec_parser.to_dict_list(rfp_doc.specifications)
            df = pd.DataFrame(specs_data)
            df.to_csv(output_path, index=False)
            self.logger.info("Specifications exported to CSV", file=output_path)
        else:
            self.logger.warning("No specifications to export")
