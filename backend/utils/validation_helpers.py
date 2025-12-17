"""Validation helper utilities for data validation across the system."""
from typing import Any, Dict, List, Optional, Union, Callable
from decimal import Decimal, InvalidOperation
import re
from datetime import datetime
import structlog

logger = structlog.get_logger()


class ValidationHelpers:
    """Collection of validation helper functions."""
    
    def __init__(self):
        """Initialize validation helpers."""
        self.logger = logger.bind(component="ValidationHelpers")
    
    # ============= Type Validation =============
    
    def is_valid_email(self, email: str) -> bool:
        """Validate email address format.
        
        Args:
            email: Email address string
            
        Returns:
            True if valid email format
        """
        if not email:
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def is_valid_phone(self, phone: str, country: str = 'IN') -> bool:
        """Validate phone number format.
        
        Args:
            phone: Phone number string
            country: Country code (default: IN for India)
            
        Returns:
            True if valid phone format
        """
        if not phone:
            return False
        
        # Remove common separators
        phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        if country == 'IN':
            # Indian: 10 digits or +91 followed by 10 digits
            pattern = r'^(\+91)?[6-9]\d{9}$'
        else:
            # Generic: 7-15 digits with optional + prefix
            pattern = r'^\+?\d{7,15}$'
        
        return bool(re.match(pattern, phone))
    
    def is_valid_url(self, url: str) -> bool:
        """Validate URL format.
        
        Args:
            url: URL string
            
        Returns:
            True if valid URL format
        """
        if not url:
            return False
        
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, url, re.IGNORECASE))
    
    def is_valid_gstin(self, gstin: str) -> bool:
        """Validate Indian GSTIN format.
        
        Args:
            gstin: GSTIN string
            
        Returns:
            True if valid GSTIN format
        """
        if not gstin:
            return False
        
        # Format: 22AAAAA0000A1Z5
        pattern = r'^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}$'
        return bool(re.match(pattern, gstin.upper()))
    
    def is_valid_pan(self, pan: str) -> bool:
        """Validate Indian PAN format.
        
        Args:
            pan: PAN string
            
        Returns:
            True if valid PAN format
        """
        if not pan:
            return False
        
        # Format: AAAAA9999A
        pattern = r'^[A-Z]{5}\d{4}[A-Z]{1}$'
        return bool(re.match(pattern, pan.upper()))
    
    def is_valid_hsn_code(self, hsn: str) -> bool:
        """Validate HSN code format.
        
        Args:
            hsn: HSN code string
            
        Returns:
            True if valid HSN code (4, 6, or 8 digits)
        """
        if not hsn:
            return False
        
        hsn = str(hsn).strip()
        return bool(re.match(r'^\d{4}(?:\d{2}(?:\d{2})?)?$', hsn))
    
    # ============= Numeric Validation =============
    
    def is_positive_number(self, value: Any) -> bool:
        """Check if value is a positive number.
        
        Args:
            value: Value to check
            
        Returns:
            True if positive number
        """
        try:
            num = float(value)
            return num > 0
        except (ValueError, TypeError):
            return False
    
    def is_in_range(
        self,
        value: Any,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        inclusive: bool = True
    ) -> bool:
        """Check if value is within range.
        
        Args:
            value: Value to check
            min_val: Minimum value (None for no minimum)
            max_val: Maximum value (None for no maximum)
            inclusive: Whether range is inclusive
            
        Returns:
            True if in range
        """
        try:
            num = float(value)
            
            if min_val is not None:
                if inclusive and num < min_val:
                    return False
                if not inclusive and num <= min_val:
                    return False
            
            if max_val is not None:
                if inclusive and num > max_val:
                    return False
                if not inclusive and num >= max_val:
                    return False
            
            return True
        except (ValueError, TypeError):
            return False
    
    def is_valid_percentage(self, value: Any) -> bool:
        """Check if value is a valid percentage (0-100).
        
        Args:
            value: Value to check
            
        Returns:
            True if valid percentage
        """
        return self.is_in_range(value, 0, 100, inclusive=True)
    
    # ============= String Validation =============
    
    def is_not_empty(self, value: Any) -> bool:
        """Check if value is not empty.
        
        Args:
            value: Value to check
            
        Returns:
            True if not empty
        """
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        return bool(value)
    
    def has_min_length(self, value: str, min_length: int) -> bool:
        """Check if string has minimum length.
        
        Args:
            value: String to check
            min_length: Minimum length
            
        Returns:
            True if meets minimum length
        """
        if not isinstance(value, str):
            return False
        return len(value.strip()) >= min_length
    
    def has_max_length(self, value: str, max_length: int) -> bool:
        """Check if string has maximum length.
        
        Args:
            value: String to check
            max_length: Maximum length
            
        Returns:
            True if within maximum length
        """
        if not isinstance(value, str):
            return False
        return len(value.strip()) <= max_length
    
    def matches_pattern(self, value: str, pattern: str) -> bool:
        """Check if string matches regex pattern.
        
        Args:
            value: String to check
            pattern: Regex pattern
            
        Returns:
            True if matches pattern
        """
        if not isinstance(value, str):
            return False
        return bool(re.match(pattern, value))
    
    # ============= Date Validation =============
    
    def is_valid_date(
        self,
        date_str: str,
        format: str = '%Y-%m-%d'
    ) -> bool:
        """Check if string is a valid date.
        
        Args:
            date_str: Date string
            format: Expected date format
            
        Returns:
            True if valid date
        """
        try:
            datetime.strptime(date_str, format)
            return True
        except (ValueError, TypeError):
            return False
    
    def is_future_date(
        self,
        date_str: str,
        format: str = '%Y-%m-%d'
    ) -> bool:
        """Check if date is in the future.
        
        Args:
            date_str: Date string
            format: Date format
            
        Returns:
            True if future date
        """
        try:
            date = datetime.strptime(date_str, format)
            return date > datetime.now()
        except (ValueError, TypeError):
            return False
    
    def is_past_date(
        self,
        date_str: str,
        format: str = '%Y-%m-%d'
    ) -> bool:
        """Check if date is in the past.
        
        Args:
            date_str: Date string
            format: Date format
            
        Returns:
            True if past date
        """
        try:
            date = datetime.strptime(date_str, format)
            return date < datetime.now()
        except (ValueError, TypeError):
            return False
    
    # ============= Business Logic Validation =============
    
    def is_valid_price(self, price: Any) -> bool:
        """Check if price is valid (positive number with max 2 decimals).
        
        Args:
            price: Price value
            
        Returns:
            True if valid price
        """
        try:
            price_decimal = Decimal(str(price))
            if price_decimal <= 0:
                return False
            # Check max 2 decimal places
            return price_decimal.as_tuple().exponent >= -2
        except (InvalidOperation, ValueError, TypeError):
            return False
    
    def is_valid_quantity(self, quantity: Any) -> bool:
        """Check if quantity is valid (positive integer).
        
        Args:
            quantity: Quantity value
            
        Returns:
            True if valid quantity
        """
        try:
            qty = int(quantity)
            return qty > 0
        except (ValueError, TypeError):
            return False
    
    def is_valid_discount(self, discount: Any, max_discount: float = 100) -> bool:
        """Check if discount is valid.
        
        Args:
            discount: Discount percentage
            max_discount: Maximum allowed discount
            
        Returns:
            True if valid discount
        """
        return self.is_in_range(discount, 0, max_discount)
    
    # ============= Composite Validation =============
    
    def validate_required_fields(
        self,
        data: Dict[str, Any],
        required_fields: List[str]
    ) -> Dict[str, Any]:
        """Validate that required fields are present and not empty.
        
        Args:
            data: Data dictionary
            required_fields: List of required field names
            
        Returns:
            Validation result with errors
        """
        errors = []
        
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
            elif not self.is_not_empty(data[field]):
                errors.append(f"Required field is empty: {field}")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'missing_fields': [f for f in required_fields if f not in data]
        }
    
    def validate_field_types(
        self,
        data: Dict[str, Any],
        field_types: Dict[str, type]
    ) -> Dict[str, Any]:
        """Validate field types.
        
        Args:
            data: Data dictionary
            field_types: Dictionary mapping field names to expected types
            
        Returns:
            Validation result with errors
        """
        errors = []
        
        for field, expected_type in field_types.items():
            if field in data:
                value = data[field]
                if value is not None and not isinstance(value, expected_type):
                    errors.append(
                        f"Field '{field}' expected type {expected_type.__name__}, "
                        f"got {type(value).__name__}"
                    )
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }
    
    def validate_rfp_data(self, rfp: Dict[str, Any]) -> Dict[str, Any]:
        """Validate RFP data structure.
        
        Args:
            rfp: RFP data dictionary
            
        Returns:
            Validation result
        """
        errors = []
        warnings = []
        
        # Required fields
        required = ['rfp_number', 'title', 'organization', 'submission_deadline']
        req_result = self.validate_required_fields(rfp, required)
        errors.extend(req_result['errors'])
        
        # Date validation
        if 'submission_deadline' in rfp:
            if not self.is_future_date(str(rfp['submission_deadline']), '%Y-%m-%d'):
                warnings.append("Submission deadline is not in the future")
        
        # Validate quantities if present
        if 'quantity_requirements' in rfp:
            qty_req = rfp['quantity_requirements']
            if isinstance(qty_req, dict):
                for item, qty in qty_req.items():
                    if not self.is_valid_quantity(qty):
                        errors.append(f"Invalid quantity for {item}: {qty}")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def validate_product_data(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Validate product data structure.
        
        Args:
            product: Product data dictionary
            
        Returns:
            Validation result
        """
        errors = []
        warnings = []
        
        # Required fields
        required = ['brand', 'category', 'product_name']
        req_result = self.validate_required_fields(product, required)
        errors.extend(req_result['errors'])
        
        # Price validation
        price_fields = ['mrp', 'selling_price', 'dealer_price']
        for field in price_fields:
            if field in product and product[field] is not None:
                if not self.is_valid_price(product[field]):
                    errors.append(f"Invalid price for {field}: {product[field]}")
        
        # HSN code validation
        if 'hsn_code' in product and product['hsn_code']:
            if not self.is_valid_hsn_code(product['hsn_code']):
                warnings.append(f"Invalid HSN code format: {product['hsn_code']}")
        
        # Warranty validation
        if 'warranty_years' in product and product['warranty_years'] is not None:
            if not self.is_in_range(product['warranty_years'], 0, 50):
                errors.append(f"Invalid warranty years: {product['warranty_years']}")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def validate_pricing_data(self, pricing: Dict[str, Any]) -> Dict[str, Any]:
        """Validate pricing data structure.
        
        Args:
            pricing: Pricing data dictionary
            
        Returns:
            Validation result
        """
        errors = []
        
        # At least one price field required
        price_fields = ['mrp', 'selling_price', 'dealer_price']
        has_price = any(
            field in pricing and self.is_valid_price(pricing[field])
            for field in price_fields
        )
        
        if not has_price:
            errors.append("No valid price field found")
        
        # Validate discount if present
        if 'discount_percentage' in pricing:
            if not self.is_valid_discount(pricing['discount_percentage']):
                errors.append(
                    f"Invalid discount: {pricing['discount_percentage']}"
                )
        
        # Validate price hierarchy: MRP >= Selling Price >= Dealer Price
        if all(field in pricing for field in price_fields):
            try:
                mrp = float(pricing['mrp'])
                selling = float(pricing['selling_price'])
                dealer = float(pricing['dealer_price'])
                
                if not (mrp >= selling >= dealer):
                    errors.append(
                        "Price hierarchy violation: MRP >= Selling >= Dealer"
                    )
            except (ValueError, TypeError):
                pass
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }
    
    # ============= Utility Functions =============
    
    def sanitize_string(self, value: str, max_length: Optional[int] = None) -> str:
        """Sanitize string by removing dangerous characters.
        
        Args:
            value: String to sanitize
            max_length: Maximum length to truncate
            
        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            return str(value)
        
        # Remove control characters
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)
        
        # Trim whitespace
        sanitized = sanitized.strip()
        
        # Truncate if needed
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized
    
    def normalize_phone(self, phone: str) -> Optional[str]:
        """Normalize phone number to standard format.
        
        Args:
            phone: Phone number string
            
        Returns:
            Normalized phone number or None
        """
        if not phone:
            return None
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Indian number
        if len(digits) == 10:
            return f"+91{digits}"
        elif len(digits) == 12 and digits.startswith('91'):
            return f"+{digits}"
        
        return digits if len(digits) >= 7 else None
    
    def normalize_email(self, email: str) -> Optional[str]:
        """Normalize email address.
        
        Args:
            email: Email address
            
        Returns:
            Normalized email or None
        """
        if not email:
            return None
        
        email = email.strip().lower()
        
        if self.is_valid_email(email):
            return email
        
        return None


# Global instance
_validation_helpers = None


def get_validation_helpers() -> ValidationHelpers:
    """Get global validation helpers instance.
    
    Returns:
        ValidationHelpers instance
    """
    global _validation_helpers
    if _validation_helpers is None:
        _validation_helpers = ValidationHelpers()
    return _validation_helpers
