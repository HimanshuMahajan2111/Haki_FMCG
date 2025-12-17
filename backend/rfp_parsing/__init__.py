"""
RFP Document Parsing Pipeline
Extracts text, tables, BOQ, and specifications from RFP PDF documents.
"""

from rfp_parsing.base_parser import DocumentParser, ParseResult, MultiFormatParser
from rfp_parsing.pdf_extractor import PDFExtractor, PDFExtractionResult
from rfp_parsing.boq_extractor import BOQExtractor, BOQItem
from rfp_parsing.spec_parser import SpecificationParser, Specification
from rfp_parsing.rfp_pipeline import RFPPipeline, RFPDocument
from rfp_parsing.date_extractor import DateExtractor, Deadline
from rfp_parsing.testing_extractor import TestingRequirementExtractor, TestingRequirement
from rfp_parsing.ocr_handler import OCRHandler
from rfp_parsing.multi_format import WordParser, ExcelParser, CSVParser
from rfp_parsing.quality_metrics import QualityMetrics, PreviewGenerator

__all__ = [
    # Base classes
    'DocumentParser',
    'ParseResult',
    'MultiFormatParser',
    # PDF extraction
    'PDFExtractor',
    'PDFExtractionResult',
    # BOQ extraction
    'BOQExtractor',
    'BOQItem',
    # Specification parsing
    'SpecificationParser',
    'Specification',
    # Pipeline
    'RFPPipeline',
    'RFPDocument',
    # Date extraction
    'DateExtractor',
    'Deadline',
    # Testing requirements
    'TestingRequirementExtractor',
    'TestingRequirement',
    # OCR support
    'OCRHandler',
    # Multi-format support
    'WordParser',
    'ExcelParser',
    'CSVParser',
    # Quality & Preview
    'QualityMetrics',
    'PreviewGenerator'
]
