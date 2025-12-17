"""
Document Parser Base Class - Abstract base for all document parsers.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
import structlog

logger = structlog.get_logger()


@dataclass
class ParseResult:
    """Base result class for all parsing operations."""
    file_path: str
    file_type: str
    success: bool = True
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    quality_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'file_path': self.file_path,
            'file_type': self.file_type,
            'success': self.success,
            'error_message': self.error_message,
            'warnings': self.warnings,
            'metadata': self.metadata,
            'quality_metrics': self.quality_metrics
        }


class DocumentParser(ABC):
    """Abstract base class for all document parsers."""
    
    def __init__(self):
        """Initialize document parser."""
        self.logger = logger.bind(component=self.__class__.__name__)
        self.supported_formats: List[str] = []
    
    @abstractmethod
    def parse(self, file_path: str, **kwargs) -> ParseResult:
        """Parse document and return structured data.
        
        Args:
            file_path: Path to document file
            **kwargs: Additional parsing options
            
        Returns:
            ParseResult with extracted data
        """
        pass
    
    @abstractmethod
    def validate(self, file_path: str) -> bool:
        """Validate if file can be parsed.
        
        Args:
            file_path: Path to document file
            
        Returns:
            True if file is valid for this parser
        """
        pass
    
    def supports_format(self, file_path: str) -> bool:
        """Check if file format is supported.
        
        Args:
            file_path: Path to document file
            
        Returns:
            True if format is supported
        """
        file_ext = Path(file_path).suffix.lower()
        return file_ext in self.supported_formats
    
    def calculate_quality_metrics(self, result: ParseResult) -> Dict[str, Any]:
        """Calculate quality metrics for parsing result.
        
        Args:
            result: Parse result
            
        Returns:
            Dictionary of quality metrics
        """
        return {
            'success': result.success,
            'has_errors': result.error_message is not None,
            'warning_count': len(result.warnings)
        }
    
    def handle_error(self, error: Exception, file_path: str) -> ParseResult:
        """Handle parsing errors.
        
        Args:
            error: Exception that occurred
            file_path: Path to file being parsed
            
        Returns:
            ParseResult with error information
        """
        self.logger.error(
            "Parsing error",
            file=file_path,
            error=str(error),
            error_type=type(error).__name__
        )
        
        return ParseResult(
            file_path=file_path,
            file_type=Path(file_path).suffix,
            success=False,
            error_message=f"{type(error).__name__}: {str(error)}"
        )


class MultiFormatParser(DocumentParser):
    """Parser that supports multiple document formats."""
    
    def __init__(self):
        """Initialize multi-format parser."""
        super().__init__()
        self.parsers: Dict[str, DocumentParser] = {}
    
    def register_parser(self, formats: List[str], parser: DocumentParser):
        """Register a parser for specific formats.
        
        Args:
            formats: List of file extensions (e.g., ['.pdf', '.docx'])
            parser: Parser instance
        """
        for fmt in formats:
            self.parsers[fmt.lower()] = parser
            if fmt not in self.supported_formats:
                self.supported_formats.append(fmt)
    
    def parse(self, file_path: str, **kwargs) -> ParseResult:
        """Parse document using appropriate parser.
        
        Args:
            file_path: Path to document
            **kwargs: Additional options
            
        Returns:
            ParseResult
        """
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext not in self.parsers:
            return ParseResult(
                file_path=file_path,
                file_type=file_ext,
                success=False,
                error_message=f"Unsupported format: {file_ext}"
            )
        
        parser = self.parsers[file_ext]
        
        try:
            return parser.parse(file_path, **kwargs)
        except Exception as e:
            return self.handle_error(e, file_path)
    
    def validate(self, file_path: str) -> bool:
        """Validate file.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if valid
        """
        if not Path(file_path).exists():
            return False
        
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in self.parsers:
            return False
        
        return self.parsers[file_ext].validate(file_path)
