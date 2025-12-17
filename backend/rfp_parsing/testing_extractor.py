"""
Testing Requirement Extractor - Extract testing, certification, and compliance requirements.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re
import structlog

logger = structlog.get_logger()


@dataclass
class TestingRequirement:
    """Testing or certification requirement."""
    requirement_type: str  # test, certification, standard, inspection
    name: str
    description: str = ""
    is_mandatory: bool = True
    standard: Optional[str] = None
    parameters: Dict[str, Any] = None
    source_text: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'requirement_type': self.requirement_type,
            'name': self.name,
            'description': self.description,
            'is_mandatory': self.is_mandatory,
            'standard': self.standard,
            'parameters': self.parameters or {},
            'source_text': self.source_text
        }


class TestingRequirementExtractor:
    """Extract testing, certification, and compliance requirements."""
    
    def __init__(self):
        """Initialize testing requirement extractor."""
        self.logger = logger.bind(component="TestingRequirementExtractor")
        
        # Standard patterns
        self.standard_patterns = {
            'is': r'IS[\s:-]*(\d+(?:\.\d+)?)',  # Indian Standards
            'iec': r'IEC[\s:-]*(\d+(?:\.\d+)?)',  # International Electrotechnical Commission
            'ieee': r'IEEE[\s:-]*(\d+(?:\.\d+)?)',  # IEEE Standards
            'iso': r'ISO[\s:-]*(\d+(?:\.\d+)?)',  # ISO Standards
            'bis': r'BIS[\s:-]*(\d+(?:\.\d+)?)',  # Bureau of Indian Standards
            'astm': r'ASTM[\s:-]*([A-Z]?\d+)',  # ASTM Standards
            'en': r'EN[\s:-]*(\d+(?:\.\d+)?)',  # European Standards
        }
        
        # Certification patterns
        self.certification_patterns = [
            r'(?:CE|ce)\s*(?:marked|certification|certified)',
            r'(?:UL|ul)\s*(?:listed|certification|certified)',
            r'(?:RoHS|rohs)\s*(?:compliant|compliance)',
            r'(?:FCC|fcc)\s*(?:certified|certification)',
            r'(?:ISI|isi)\s*(?:mark|marked|certification)',
        ]
        
        # Testing keywords
        self.testing_keywords = {
            'type_test': ['type test', 'type testing', 'prototype test'],
            'routine_test': ['routine test', 'production test', 'acceptance test'],
            'sample_test': ['sample testing', 'sample test'],
            'field_test': ['field test', 'site test', 'installation test'],
            'performance_test': ['performance test', 'performance testing'],
            'quality_test': ['quality test', 'quality assurance test'],
        }
        
        # Inspection keywords
        self.inspection_keywords = [
            'inspection', 'factory acceptance test', 'FAT', 'SAT',
            'site acceptance test', 'witness test', 'third party inspection'
        ]
    
    def extract_standards(self, text: str) -> List[str]:
        """Extract all standards mentioned in text.
        
        Args:
            text: Text content
            
        Returns:
            List of standard identifiers
        """
        standards = []
        
        for std_type, pattern in self.standard_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                std_id = match.group(0).strip()
                if std_id not in standards:
                    standards.append(std_id)
        
        return standards
    
    def extract_certifications(self, text: str) -> List[str]:
        """Extract certification requirements.
        
        Args:
            text: Text content
            
        Returns:
            List of certifications
        """
        certifications = []
        
        for pattern in self.certification_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                cert = match.group(0).strip()
                if cert not in certifications:
                    certifications.append(cert)
        
        return certifications
    
    def extract_testing_requirements(self, text: str) -> List[TestingRequirement]:
        """Extract all testing requirements.
        
        Args:
            text: Text content
            
        Returns:
            List of TestingRequirement objects
        """
        requirements = []
        
        # Extract testing requirements
        for test_type, keywords in self.testing_keywords.items():
            for keyword in keywords:
                pattern = re.compile(rf'.*{re.escape(keyword)}.*', re.IGNORECASE)
                matches = pattern.finditer(text)
                
                for match in matches:
                    source = match.group(0).strip()
                    
                    # Check if mandatory
                    is_mandatory = self._is_mandatory(source)
                    
                    # Extract associated standards
                    standards = self.extract_standards(source)
                    
                    req = TestingRequirement(
                        requirement_type='test',
                        name=test_type.replace('_', ' ').title(),
                        description=keyword,
                        is_mandatory=is_mandatory,
                        standard=standards[0] if standards else None,
                        source_text=source
                    )
                    
                    requirements.append(req)
        
        # Extract certification requirements
        certifications = self.extract_certifications(text)
        for cert in certifications:
            req = TestingRequirement(
                requirement_type='certification',
                name=cert,
                description=f"{cert} certification required",
                is_mandatory=True,
                source_text=cert
            )
            requirements.append(req)
        
        # Extract standard requirements
        standards = self.extract_standards(text)
        for standard in standards:
            req = TestingRequirement(
                requirement_type='standard',
                name=standard,
                description=f"Compliance with {standard}",
                is_mandatory=True,
                source_text=standard
            )
            requirements.append(req)
        
        # Extract inspection requirements
        for keyword in self.inspection_keywords:
            pattern = re.compile(rf'.*{re.escape(keyword)}.*', re.IGNORECASE)
            matches = pattern.finditer(text)
            
            for match in matches:
                source = match.group(0).strip()
                
                req = TestingRequirement(
                    requirement_type='inspection',
                    name=keyword.title(),
                    description=keyword,
                    is_mandatory=self._is_mandatory(source),
                    source_text=source
                )
                
                requirements.append(req)
        
        return requirements
    
    def _is_mandatory(self, text: str) -> bool:
        """Check if requirement is mandatory.
        
        Args:
            text: Requirement text
            
        Returns:
            True if mandatory
        """
        mandatory_keywords = ['must', 'shall', 'required', 'mandatory', 'essential']
        optional_keywords = ['may', 'optional', 'if possible', 'preferred']
        
        text_lower = text.lower()
        
        # Check for optional keywords first
        if any(keyword in text_lower for keyword in optional_keywords):
            return False
        
        # Check for mandatory keywords or default to mandatory
        return any(keyword in text_lower for keyword in mandatory_keywords) or True
    
    def group_by_type(
        self,
        requirements: List[TestingRequirement]
    ) -> Dict[str, List[TestingRequirement]]:
        """Group requirements by type.
        
        Args:
            requirements: List of requirements
            
        Returns:
            Dictionary mapping types to requirements
        """
        grouped = {}
        
        for req in requirements:
            req_type = req.requirement_type
            if req_type not in grouped:
                grouped[req_type] = []
            grouped[req_type].append(req)
        
        return grouped
    
    def get_mandatory_requirements(
        self,
        requirements: List[TestingRequirement]
    ) -> List[TestingRequirement]:
        """Get only mandatory requirements.
        
        Args:
            requirements: List of requirements
            
        Returns:
            List of mandatory requirements
        """
        return [req for req in requirements if req.is_mandatory]
    
    def extract_quality_parameters(self, text: str) -> Dict[str, Any]:
        """Extract quality parameters and acceptance criteria.
        
        Args:
            text: Text content
            
        Returns:
            Dictionary of quality parameters
        """
        parameters = {}
        
        # Common quality parameters
        param_patterns = {
            'acceptance_criteria': r'acceptance\s+criteria[:\s]*(.+?)(?:\n|$)',
            'rejection_criteria': r'rejection\s+criteria[:\s]*(.+?)(?:\n|$)',
            'tolerance': r'tolerance[:\s]*([±\d.%]+)',
            'accuracy': r'accuracy[:\s]*([±\d.%]+)',
            'sampling': r'sampling[:\s]*(.+?)(?:\n|$)',
        }
        
        for param_name, pattern in param_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                parameters[param_name] = match.group(1).strip()
        
        return parameters
