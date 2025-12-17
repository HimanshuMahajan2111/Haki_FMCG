"""
Quality Validation System
Validates quality, completeness, and consistency of agent outputs and final responses.
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import structlog
import re

logger = structlog.get_logger()


class ValidationSeverity(Enum):
    """Validation issue severity."""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationCategory(Enum):
    """Validation category."""
    COMPLETENESS = "completeness"
    CONSISTENCY = "consistency"
    ACCURACY = "accuracy"
    COMPLIANCE = "compliance"
    FORMAT = "format"
    BUSINESS_RULES = "business_rules"


@dataclass
class ValidationIssue:
    """Validation issue."""
    category: ValidationCategory
    severity: ValidationSeverity
    message: str
    field: Optional[str] = None
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Validation result."""
    is_valid: bool
    score: float  # 0-100
    issues: List[ValidationIssue] = field(default_factory=list)
    validated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def critical_issues(self) -> List[ValidationIssue]:
        """Get critical issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.CRITICAL]
    
    @property
    def errors(self) -> List[ValidationIssue]:
        """Get errors."""
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]
    
    @property
    def warnings(self) -> List[ValidationIssue]:
        """Get warnings."""
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]


class CompletenessChecker:
    """Checks completeness of data."""
    
    def __init__(self):
        self.logger = logger.bind(component="CompletenessChecker")
    
    def check_required_fields(
        self,
        data: Dict[str, Any],
        required_fields: List[str]
    ) -> List[ValidationIssue]:
        """Check if required fields are present and non-empty.
        
        Args:
            data: Data to check
            required_fields: List of required field names
            
        Returns:
            List of validation issues
        """
        issues = []
        
        for field in required_fields:
            # Check nested fields (e.g., "customer.name")
            if '.' in field:
                parts = field.split('.')
                current = data
                missing = False
                
                for part in parts:
                    if not isinstance(current, dict) or part not in current:
                        missing = True
                        break
                    current = current[part]
                
                if missing or not current:
                    issues.append(ValidationIssue(
                        category=ValidationCategory.COMPLETENESS,
                        severity=ValidationSeverity.ERROR,
                        message=f"Required field '{field}' is missing or empty",
                        field=field
                    ))
            else:
                if field not in data or not data[field]:
                    issues.append(ValidationIssue(
                        category=ValidationCategory.COMPLETENESS,
                        severity=ValidationSeverity.ERROR,
                        message=f"Required field '{field}' is missing or empty",
                        field=field
                    ))
        
        return issues
    
    def check_rfp_response_completeness(
        self,
        rfp_response: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Check RFP response completeness.
        
        Args:
            rfp_response: RFP response data
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Required sections
        required_sections = [
            'rfp_id',
            'response_id',
            'customer_name',
            'executive_summary',
            'technical_proposal',
            'commercial_proposal',
            'terms_and_conditions'
        ]
        
        issues.extend(self.check_required_fields(rfp_response, required_sections))
        
        # Check technical proposal details
        if 'technical_proposal' in rfp_response:
            tech = rfp_response['technical_proposal']
            if not tech.get('comparisons'):
                issues.append(ValidationIssue(
                    category=ValidationCategory.COMPLETENESS,
                    severity=ValidationSeverity.WARNING,
                    message="Technical proposal has no product comparisons",
                    field="technical_proposal.comparisons"
                ))
        
        # Check commercial proposal details
        if 'commercial_proposal' in rfp_response:
            comm = rfp_response['commercial_proposal']
            if not comm.get('bid_summary'):
                issues.append(ValidationIssue(
                    category=ValidationCategory.COMPLETENESS,
                    severity=ValidationSeverity.ERROR,
                    message="Commercial proposal missing bid summary",
                    field="commercial_proposal.bid_summary"
                ))
            elif not comm['bid_summary'].get('grand_total'):
                issues.append(ValidationIssue(
                    category=ValidationCategory.COMPLETENESS,
                    severity=ValidationSeverity.ERROR,
                    message="Commercial proposal missing grand total",
                    field="commercial_proposal.bid_summary.grand_total"
                ))
        
        return issues


class ConsistencyValidator:
    """Validates consistency across different parts of data."""
    
    def __init__(self):
        self.logger = logger.bind(component="ConsistencyValidator")
    
    def check_price_consistency(
        self,
        technical_data: Dict[str, Any],
        pricing_data: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Check consistency between technical and pricing data.
        
        Args:
            technical_data: Technical proposal data
            pricing_data: Pricing data
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Check if all technical products have pricing
        comparisons = technical_data.get('comparisons', [])
        pricings = pricing_data.get('product_pricings', [])
        
        if len(comparisons) != len(pricings):
            issues.append(ValidationIssue(
                category=ValidationCategory.CONSISTENCY,
                severity=ValidationSeverity.WARNING,
                message=f"Mismatch between products ({len(comparisons)}) and pricings ({len(pricings)})",
                expected=len(comparisons),
                actual=len(pricings)
            ))
        
        return issues
    
    def check_total_calculations(
        self,
        pricing_data: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Validate pricing calculations.
        
        Args:
            pricing_data: Pricing data
            
        Returns:
            List of validation issues
        """
        issues = []
        
        bid_summary = pricing_data.get('bid_summary', {})
        
        # Check if grand total makes sense
        grand_total = bid_summary.get('grand_total', 0)
        
        if grand_total <= 0:
            issues.append(ValidationIssue(
                category=ValidationCategory.CONSISTENCY,
                severity=ValidationSeverity.CRITICAL,
                message="Grand total must be greater than 0",
                field="bid_summary.grand_total",
                actual=grand_total
            ))
        
        # Check margin
        margin = bid_summary.get('margin_percent', 0)
        if margin < 0 or margin > 100:
            issues.append(ValidationIssue(
                category=ValidationCategory.CONSISTENCY,
                severity=ValidationSeverity.ERROR,
                message="Margin percent must be between 0 and 100",
                field="bid_summary.margin_percent",
                actual=margin
            ))
        
        return issues
    
    def check_customer_info_consistency(
        self,
        sales_data: Dict[str, Any],
        rfp_response: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Check customer information consistency.
        
        Args:
            sales_data: Sales analysis data
            rfp_response: Final RFP response
            
        Returns:
            List of validation issues
        """
        issues = []
        
        sales_customer = sales_data.get('rfp_analysis', {}).get('customer_name')
        response_customer = rfp_response.get('customer_name')
        
        if sales_customer and response_customer:
            if sales_customer.strip().lower() != response_customer.strip().lower():
                issues.append(ValidationIssue(
                    category=ValidationCategory.CONSISTENCY,
                    severity=ValidationSeverity.WARNING,
                    message="Customer name mismatch between sales analysis and response",
                    expected=sales_customer,
                    actual=response_customer
                ))
        
        return issues


class OutputFormatter:
    """Validates and formats output data."""
    
    def __init__(self):
        self.logger = logger.bind(component="OutputFormatter")
    
    def validate_format(
        self,
        data: Dict[str, Any],
        data_type: str
    ) -> List[ValidationIssue]:
        """Validate data format.
        
        Args:
            data: Data to validate
            data_type: Type of data (rfp_response, technical_proposal, etc.)
            
        Returns:
            List of validation issues
        """
        issues = []
        
        if data_type == "rfp_response":
            issues.extend(self._validate_rfp_response_format(data))
        elif data_type == "technical_proposal":
            issues.extend(self._validate_technical_format(data))
        elif data_type == "commercial_proposal":
            issues.extend(self._validate_commercial_format(data))
        
        return issues
    
    def _validate_rfp_response_format(
        self,
        data: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Validate RFP response format."""
        issues = []
        
        # Check IDs format
        rfp_id = data.get('rfp_id', '')
        if not rfp_id or not isinstance(rfp_id, str):
            issues.append(ValidationIssue(
                category=ValidationCategory.FORMAT,
                severity=ValidationSeverity.ERROR,
                message="RFP ID must be a non-empty string",
                field="rfp_id"
            ))
        
        response_id = data.get('response_id', '')
        if not response_id or not isinstance(response_id, str):
            issues.append(ValidationIssue(
                category=ValidationCategory.FORMAT,
                severity=ValidationSeverity.ERROR,
                message="Response ID must be a non-empty string",
                field="response_id"
            ))
        
        # Check dates
        generated_at = data.get('generated_at', '')
        if generated_at:
            try:
                datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
            except:
                issues.append(ValidationIssue(
                    category=ValidationCategory.FORMAT,
                    severity=ValidationSeverity.WARNING,
                    message="Invalid date format for generated_at",
                    field="generated_at"
                ))
        
        return issues
    
    def _validate_technical_format(
        self,
        data: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Validate technical proposal format."""
        issues = []
        
        comparisons = data.get('comparisons', [])
        if not isinstance(comparisons, list):
            issues.append(ValidationIssue(
                category=ValidationCategory.FORMAT,
                severity=ValidationSeverity.ERROR,
                message="Comparisons must be a list",
                field="comparisons"
            ))
        
        return issues
    
    def _validate_commercial_format(
        self,
        data: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Validate commercial proposal format."""
        issues = []
        
        bid_summary = data.get('bid_summary', {})
        
        # Check numeric fields
        numeric_fields = ['grand_total', 'margin_percent', 'validity_days']
        for field in numeric_fields:
            if field in bid_summary:
                value = bid_summary[field]
                if not isinstance(value, (int, float)):
                    issues.append(ValidationIssue(
                        category=ValidationCategory.FORMAT,
                        severity=ValidationSeverity.ERROR,
                        message=f"{field} must be numeric",
                        field=f"bid_summary.{field}"
                    ))
        
        return issues


class QualityValidationSystem:
    """
    Comprehensive Quality Validation System
    
    Features:
    - Completeness checking
    - Consistency validation
    - Format validation
    - Business rules validation
    - Quality scoring
    """
    
    def __init__(self):
        """Initialize validation system."""
        self.logger = logger.bind(component="QualityValidation")
        
        self.completeness_checker = CompletenessChecker()
        self.consistency_validator = ConsistencyValidator()
        self.output_formatter = OutputFormatter()
        
        # Validation thresholds
        self.min_quality_score = 80.0
        self.critical_issue_weight = 25.0
        self.error_weight = 10.0
        self.warning_weight = 2.0
        
        self.logger.info("Quality Validation System initialized")
    
    def validate_agent_output(
        self,
        agent_name: str,
        output_data: Dict[str, Any],
        output_type: str
    ) -> ValidationResult:
        """Validate agent output.
        
        Args:
            agent_name: Name of agent
            output_data: Output data to validate
            output_type: Type of output
            
        Returns:
            ValidationResult
        """
        issues = []
        
        # Format validation
        issues.extend(
            self.output_formatter.validate_format(output_data, output_type)
        )
        
        # Calculate score
        score = self._calculate_quality_score(issues)
        is_valid = score >= self.min_quality_score and not any(
            i.severity == ValidationSeverity.CRITICAL for i in issues
        )
        
        result = ValidationResult(
            is_valid=is_valid,
            score=score,
            issues=issues
        )
        
        self.logger.info(
            "Agent output validated",
            agent_name=agent_name,
            output_type=output_type,
            is_valid=is_valid,
            score=score,
            issue_count=len(issues)
        )
        
        return result
    
    def validate_rfp_response(
        self,
        rfp_response: Dict[str, Any],
        consolidated_data: Dict[str, Any]
    ) -> ValidationResult:
        """Validate complete RFP response.
        
        Args:
            rfp_response: Final RFP response
            consolidated_data: Consolidated agent data
            
        Returns:
            ValidationResult
        """
        issues = []
        
        # Completeness checks
        issues.extend(
            self.completeness_checker.check_rfp_response_completeness(rfp_response)
        )
        
        # Format validation
        issues.extend(
            self.output_formatter.validate_format(rfp_response, "rfp_response")
        )
        
        # Consistency checks
        sales_data = consolidated_data.get('sales_analysis', {})
        technical_data = consolidated_data.get('technical_proposal', {})
        pricing_data = consolidated_data.get('commercial_proposal', {})
        
        issues.extend(
            self.consistency_validator.check_customer_info_consistency(
                sales_data, rfp_response
            )
        )
        
        issues.extend(
            self.consistency_validator.check_price_consistency(
                technical_data, pricing_data
            )
        )
        
        issues.extend(
            self.consistency_validator.check_total_calculations(pricing_data)
        )
        
        # Calculate score
        score = self._calculate_quality_score(issues)
        is_valid = score >= self.min_quality_score and not any(
            i.severity == ValidationSeverity.CRITICAL for i in issues
        )
        
        result = ValidationResult(
            is_valid=is_valid,
            score=score,
            issues=issues
        )
        
        self.logger.info(
            "RFP response validated",
            is_valid=is_valid,
            score=score,
            critical_issues=len(result.critical_issues),
            errors=len(result.errors),
            warnings=len(result.warnings)
        )
        
        return result
    
    def _calculate_quality_score(self, issues: List[ValidationIssue]) -> float:
        """Calculate quality score from issues.
        
        Args:
            issues: List of validation issues
            
        Returns:
            Quality score (0-100)
        """
        if not issues:
            return 100.0
        
        # Calculate penalty
        penalty = 0.0
        
        for issue in issues:
            if issue.severity == ValidationSeverity.CRITICAL:
                penalty += self.critical_issue_weight
            elif issue.severity == ValidationSeverity.ERROR:
                penalty += self.error_weight
            elif issue.severity == ValidationSeverity.WARNING:
                penalty += self.warning_weight
        
        # Calculate score
        score = max(0.0, 100.0 - penalty)
        
        return score
    
    def generate_validation_report(
        self,
        validation_result: ValidationResult
    ) -> str:
        """Generate human-readable validation report.
        
        Args:
            validation_result: Validation result
            
        Returns:
            Formatted report string
        """
        report = f"""
QUALITY VALIDATION REPORT
========================

Status: {'VALID' if validation_result.is_valid else 'INVALID'}
Quality Score: {validation_result.score:.2f}/100
Validated At: {validation_result.validated_at}

ISSUES SUMMARY:
- Critical: {len(validation_result.critical_issues)}
- Errors: {len(validation_result.errors)}
- Warnings: {len(validation_result.warnings)}

"""
        
        if validation_result.critical_issues:
            report += "\nCRITICAL ISSUES:\n"
            for issue in validation_result.critical_issues:
                report += f"  - {issue.message}"
                if issue.field:
                    report += f" (field: {issue.field})"
                report += "\n"
        
        if validation_result.errors:
            report += "\nERRORS:\n"
            for issue in validation_result.errors:
                report += f"  - {issue.message}"
                if issue.field:
                    report += f" (field: {issue.field})"
                report += "\n"
        
        if validation_result.warnings:
            report += "\nWARNINGS:\n"
            for issue in validation_result.warnings:
                report += f"  - {issue.message}"
                if issue.field:
                    report += f" (field: {issue.field})"
                report += "\n"
        
        return report
