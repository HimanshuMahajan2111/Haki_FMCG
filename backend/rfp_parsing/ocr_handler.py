"""
OCR Handler - Fallback OCR for scanned PDFs using pytesseract.
"""
from typing import Optional, Dict, Any
from pathlib import Path
import structlog

logger = structlog.get_logger()

try:
    import pytesseract
    from PIL import Image
    import pdf2image
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    logger.warning("pytesseract or pdf2image not available. OCR functionality disabled.")


class OCRHandler:
    """Handle OCR for scanned PDFs."""
    
    def __init__(self, tesseract_cmd: Optional[str] = None):
        """Initialize OCR handler.
        
        Args:
            tesseract_cmd: Path to tesseract executable (optional)
        """
        self.logger = logger.bind(component="OCRHandler")
        self.available = PYTESSERACT_AVAILABLE
        
        if self.available and tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    
    def is_available(self) -> bool:
        """Check if OCR is available.
        
        Returns:
            True if OCR dependencies are installed
        """
        return self.available
    
    def extract_text_from_pdf(
        self,
        pdf_path: str,
        dpi: int = 300,
        language: str = 'eng'
    ) -> str:
        """Extract text from scanned PDF using OCR.
        
        Args:
            pdf_path: Path to PDF file
            dpi: DPI for image conversion
            language: OCR language (default: English)
            
        Returns:
            Extracted text
        """
        if not self.available:
            raise RuntimeError(
                "OCR not available. Install: pip install pytesseract pdf2image pillow"
            )
        
        self.logger.info("Starting OCR extraction", file=pdf_path, dpi=dpi)
        
        try:
            # Convert PDF pages to images
            images = pdf2image.convert_from_path(
                pdf_path,
                dpi=dpi
            )
            
            all_text = []
            
            for page_num, image in enumerate(images, 1):
                self.logger.debug("Processing page", page=page_num)
                
                # Perform OCR on image
                page_text = pytesseract.image_to_string(
                    image,
                    lang=language,
                    config='--psm 3'  # Automatic page segmentation
                )
                
                all_text.append(page_text)
            
            combined_text = '\n\n'.join(all_text)
            
            self.logger.info(
                "OCR extraction completed",
                pages=len(images),
                text_length=len(combined_text)
            )
            
            return combined_text
            
        except Exception as e:
            self.logger.error("OCR extraction failed", error=str(e))
            raise
    
    def extract_text_from_image(
        self,
        image_path: str,
        language: str = 'eng'
    ) -> str:
        """Extract text from image file.
        
        Args:
            image_path: Path to image file
            language: OCR language
            
        Returns:
            Extracted text
        """
        if not self.available:
            raise RuntimeError("OCR not available")
        
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang=language)
            return text
        except Exception as e:
            self.logger.error("Image OCR failed", error=str(e))
            raise
    
    def get_ocr_confidence(
        self,
        image_path: str,
        language: str = 'eng'
    ) -> Dict[str, Any]:
        """Get OCR confidence scores.
        
        Args:
            image_path: Path to image
            language: OCR language
            
        Returns:
            Dictionary with confidence metrics
        """
        if not self.available:
            return {'available': False}
        
        try:
            image = Image.open(image_path)
            data = pytesseract.image_to_data(
                image,
                lang=language,
                output_type=pytesseract.Output.DICT
            )
            
            # Calculate average confidence
            confidences = [int(c) for c in data['conf'] if c != '-1']
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return {
                'available': True,
                'average_confidence': avg_confidence,
                'total_words': len(confidences),
                'low_confidence_words': len([c for c in confidences if c < 60])
            }
            
        except Exception as e:
            self.logger.error("Confidence calculation failed", error=str(e))
            return {'available': True, 'error': str(e)}
