"""Base data loader with validation capabilities."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
import structlog
from dataclasses import dataclass

logger = structlog.get_logger()


@dataclass
class ValidationResult:
    """Result of data validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    records_validated: int
    records_failed: int
    
    def __str__(self):
        return (
            f"Validation: {'✓ PASSED' if self.is_valid else '✗ FAILED'}\n"
            f"Records: {self.records_validated} validated, {self.records_failed} failed\n"
            f"Errors: {len(self.errors)}, Warnings: {len(self.warnings)}"
        )


class BaseDataLoader(ABC):
    """Abstract base class for data loaders."""
    
    def __init__(self, name: str):
        """Initialize base loader.
        
        Args:
            name: Name of the loader for logging
        """
        self.name = name
        self.logger = logger.bind(component=name)
        self.required_fields: Set[str] = set()
        self.optional_fields: Set[str] = set()
    
    @abstractmethod
    async def load(self) -> List[Dict[str, Any]]:
        """Load data from source.
        
        Returns:
            List of data records
        """
        pass
    
    def validate_record(self, record: Dict[str, Any], index: int, check_warnings: bool = True) -> ValidationResult:
        """Validate a single data record.
        
        Args:
            record: Data record to validate
            index: Record index for error reporting
            check_warnings: Whether to check for unexpected fields (slow)
            
        Returns:
            ValidationResult with validation status
        """
        errors = []
        warnings = []
        
        # Check required fields
        for field in self.required_fields:
            if field not in record:
                errors.append(f"Record {index}: Missing required field '{field}'")
            elif record[field] is None or (isinstance(record[field], str) and not record[field].strip()):
                errors.append(f"Record {index}: Required field '{field}' is empty")
        
        # Check for unexpected fields only if requested (warning only)
        if check_warnings:
            expected_fields = self.required_fields | self.optional_fields
            if expected_fields:  # Only check if schema is defined
                for field in record.keys():
                    if field not in expected_fields:
                        warnings.append(f"Record {index}: Unexpected field '{field}'")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            records_validated=1,
            records_failed=1 if errors else 0
        )
    
    def validate_data(self, data: List[Dict[str, Any]]) -> ValidationResult:
        """Validate multiple data records.
        
        Args:
            data: List of data records
            
        Returns:
            Aggregated ValidationResult
        """
        all_errors = []
        all_warnings = []
        total_failed = 0
        
        self.logger.info(f"Validating {len(data)} records")
        
        # Only check for unexpected fields on first 10 records to save time
        for index, record in enumerate(data):
            check_warnings = index < 10  # Only validate field names for first 10 records
            result = self.validate_record(record, index, check_warnings=check_warnings)
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
            if not result.is_valid:
                total_failed += 1
        
        final_result = ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings,
            records_validated=len(data),
            records_failed=total_failed
        )
        
        # Log results
        if final_result.is_valid:
            self.logger.info("Validation passed", 
                           records=len(data),
                           warnings=len(all_warnings))
        else:
            self.logger.error("Validation failed",
                            records=len(data),
                            failed=total_failed,
                            errors=len(all_errors))
        
        return final_result
    
    def check_file_exists(self, file_path: Path) -> bool:
        """Check if file exists.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if file exists
        """
        if not file_path.exists():
            self.logger.error(f"File not found: {file_path}")
            return False
        return True
    
    def log_validation_summary(self, result: ValidationResult):
        """Log validation summary.
        
        Args:
            result: ValidationResult to log
        """
        self.logger.info(
            "Validation summary",
            status="PASSED" if result.is_valid else "FAILED",
            validated=result.records_validated,
            failed=result.records_failed,
            errors=len(result.errors),
            warnings=len(result.warnings)
        )
        
        # Log first 5 errors
        if result.errors:
            for error in result.errors[:5]:
                self.logger.error("Validation error", error=error)
            if len(result.errors) > 5:
                self.logger.warning(f"... and {len(result.errors) - 5} more errors")
        
        # Log first 3 warnings
        if result.warnings:
            for warning in result.warnings[:3]:
                self.logger.warning("Validation warning", warning=warning)
            if len(result.warnings) > 3:
                self.logger.info(f"... and {len(result.warnings) - 3} more warnings")
