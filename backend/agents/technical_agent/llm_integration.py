"""
LLM Integration for Technical Agent - Advanced specification understanding.
"""
from typing import Dict, Any, List, Optional, Tuple
import re
import json
import structlog
from openai import OpenAI
import anthropic

logger = structlog.get_logger()


class LLMSpecificationParser:
    """LLM-powered specification parser for complex RFP requirements."""
    
    def __init__(self, provider: str = "openai", api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize LLM parser.
        
        Args:
            provider: 'openai' or 'anthropic'
            api_key: API key for provider
            model: Model name (gpt-4, claude-3-sonnet, etc.)
        """
        self.logger = logger.bind(component="LLMSpecificationParser")
        self.provider = provider
        
        if provider == "openai":
            self.client = OpenAI(api_key=api_key) if api_key else None
            self.model = model or "gpt-4"
        elif provider == "anthropic":
            self.client = anthropic.Anthropic(api_key=api_key) if api_key else None
            self.model = model or "claude-3-sonnet-20240229"
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        self.logger.info(f"LLM parser initialized", provider=provider, model=self.model)
    
    def parse_technical_specification(self, text: str) -> Dict[str, Any]:
        """Parse technical specification using LLM.
        
        Args:
            text: Raw specification text
            
        Returns:
            Structured specification dictionary
        """
        if not self.client:
            self.logger.warning("LLM client not initialized, falling back to regex")
            return self._fallback_parse(text)
        
        try:
            prompt = self._create_parsing_prompt(text)
            
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert electrical engineer parsing technical specifications."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                result = json.loads(response.choices[0].message.content)
            
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2048,
                    temperature=0.1,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                result = json.loads(response.content[0].text)
            
            self.logger.info("LLM parsing completed", specs_found=len(result.get('specifications', {})))
            return result
        
        except Exception as e:
            self.logger.error(f"LLM parsing failed: {e}", exc_info=True)
            return self._fallback_parse(text)
    
    def _create_parsing_prompt(self, text: str) -> str:
        """Create prompt for LLM parsing."""
        return f"""
Parse the following technical specification and extract structured information.

TEXT:
{text}

Extract and return a JSON object with the following structure:
{{
    "specifications": {{
        "voltage": "value with unit",
        "current": "value with unit",
        "power": "value with unit",
        "frequency": "value with unit",
        "cores": "number",
        "size_sqmm": "value",
        "conductor_material": "material",
        "insulation_material": "material",
        "ip_rating": "IP code",
        "efficiency": "percentage or class",
        "temperature_range": "min to max",
        "any_other_specs": "values"
    }},
    "standards": ["IS 694", "IEC 60227", ...],
    "certifications": ["BIS", "ISI", "CE", ...],
    "product_category": "Cable|Switchgear|Lighting|Motor|etc",
    "application": "industrial|residential|commercial|etc",
    "special_requirements": ["requirement1", "requirement2"]
}}

Be thorough and extract all technical details. Use null for missing values.
"""
    
    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """Fallback regex-based parsing."""
        return {
            "specifications": {},
            "standards": [],
            "certifications": [],
            "product_category": "Unknown",
            "application": "general",
            "special_requirements": []
        }
    
    def explain_specification(self, spec_key: str, spec_value: Any) -> str:
        """Generate human-readable explanation of a specification.
        
        Args:
            spec_key: Specification key (e.g., 'voltage')
            spec_value: Specification value
            
        Returns:
            Human-readable explanation
        """
        if not self.client:
            return f"{spec_key}: {spec_value}"
        
        try:
            prompt = f"""
Explain what this electrical specification means in simple terms:
{spec_key}: {spec_value}

Provide a brief 1-2 sentence explanation that a non-technical person would understand.
Include why this specification matters for product selection.
"""
            
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert electrical engineer explaining technical concepts."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=150
                )
                explanation = response.choices[0].message.content
            
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=150,
                    temperature=0.3,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                explanation = response.content[0].text
            
            return explanation.strip()
        
        except Exception as e:
            self.logger.error(f"Explanation generation failed: {e}")
            return f"{spec_key}: {spec_value}"
    
    def assess_technical_risk(self, requirement: Dict[str, Any], match: Dict[str, Any]) -> Dict[str, Any]:
        """Assess technical risk of using a product for a requirement.
        
        Args:
            requirement: Product requirement
            match: Matched product
            
        Returns:
            Risk assessment with score and details
        """
        if not self.client:
            return {
                "risk_level": "medium",
                "risk_score": 0.5,
                "risks": [],
                "mitigations": []
            }
        
        try:
            prompt = f"""
Assess the technical risk of using this product for the requirement:

REQUIREMENT:
{json.dumps(requirement, indent=2)}

PRODUCT MATCH:
{json.dumps(match, indent=2)}

Analyze and return JSON:
{{
    "risk_level": "low|medium|high|critical",
    "risk_score": 0.0-1.0,
    "risks": [
        {{"category": "specification", "description": "risk description", "severity": "low|medium|high"}},
        ...
    ],
    "mitigations": [
        {{"risk": "risk description", "mitigation": "mitigation strategy"}},
        ...
    ],
    "overall_assessment": "brief summary"
}}
"""
            
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert in electrical engineering risk assessment."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    response_format={"type": "json_object"}
                )
                assessment = json.loads(response.choices[0].message.content)
            
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    temperature=0.2,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                assessment = json.loads(response.content[0].text)
            
            return assessment
        
        except Exception as e:
            self.logger.error(f"Risk assessment failed: {e}")
            return {
                "risk_level": "medium",
                "risk_score": 0.5,
                "risks": [{"category": "unknown", "description": "Unable to assess", "severity": "medium"}],
                "mitigations": [],
                "overall_assessment": "Unable to perform risk assessment"
            }
    
    def generate_match_justification(
        self,
        requirement: Dict[str, Any],
        match: Dict[str, Any],
        score: float
    ) -> str:
        """Generate detailed justification for a product match.
        
        Args:
            requirement: Product requirement
            match: Matched product
            score: Match score
            
        Returns:
            Detailed justification text
        """
        if not self.client:
            return f"Product matched with {score*100:.1f}% confidence."
        
        try:
            prompt = f"""
Generate a detailed technical justification for why this product matches the requirement.

REQUIREMENT:
{json.dumps(requirement, indent=2)}

MATCHED PRODUCT:
{json.dumps(match, indent=2)}

MATCH SCORE: {score*100:.1f}%

Write a 3-4 paragraph technical justification covering:
1. How the product meets key specifications
2. Certification and compliance alignment
3. Any gaps or considerations
4. Overall suitability assessment

Use professional technical language appropriate for an RFP response.
"""
            
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a technical writer preparing RFP responses."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.4,
                    max_tokens=500
                )
                justification = response.choices[0].message.content
            
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=500,
                    temperature=0.4,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                justification = response.content[0].text
            
            return justification.strip()
        
        except Exception as e:
            self.logger.error(f"Justification generation failed: {e}")
            return f"Product matched with {score*100:.1f}% confidence."


class ComplianceChecker:
    """Check compliance with standards and regulations using LLM."""
    
    def __init__(self, llm_parser: LLMSpecificationParser):
        """Initialize compliance checker."""
        self.logger = logger.bind(component="ComplianceChecker")
        self.llm_parser = llm_parser
    
    def verify_standard_compliance(
        self,
        product: Dict[str, Any],
        required_standards: List[str]
    ) -> Dict[str, Any]:
        """Verify product compliance with required standards.
        
        Args:
            product: Product details
            required_standards: List of required standards
            
        Returns:
            Compliance verification results
        """
        if not self.llm_parser.client:
            return self._basic_verification(product, required_standards)
        
        try:
            prompt = f"""
Verify if this product complies with the required standards:

PRODUCT:
{json.dumps(product, indent=2)}

REQUIRED STANDARDS:
{json.dumps(required_standards, indent=2)}

Return JSON:
{{
    "overall_compliant": true/false,
    "compliance_details": [
        {{
            "standard": "IS 694",
            "compliant": true/false,
            "evidence": "evidence from product data",
            "confidence": 0.0-1.0,
            "notes": "additional notes"
        }},
        ...
    ],
    "missing_standards": ["standard1", ...],
    "additional_certifications": ["cert1", ...],
    "recommendation": "comply|partial|non-compliant"
}}
"""
            
            if self.llm_parser.provider == "openai":
                response = self.llm_parser.client.chat.completions.create(
                    model=self.llm_parser.model,
                    messages=[
                        {"role": "system", "content": "You are an expert in electrical standards and compliance."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                result = json.loads(response.choices[0].message.content)
            
            elif self.llm_parser.provider == "anthropic":
                response = self.llm_parser.client.messages.create(
                    model=self.llm_parser.model,
                    max_tokens=1024,
                    temperature=0.1,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                result = json.loads(response.content[0].text)
            
            self.logger.info("Standard compliance verified", compliant=result.get('overall_compliant'))
            return result
        
        except Exception as e:
            self.logger.error(f"Compliance verification failed: {e}")
            return self._basic_verification(product, required_standards)
    
    def _basic_verification(
        self,
        product: Dict[str, Any],
        required_standards: List[str]
    ) -> Dict[str, Any]:
        """Basic compliance verification without LLM."""
        product_standards = set(
            str(s).upper() for s in 
            product.get('standards_compliance', []) + product.get('certifications', [])
        )
        required_standards_set = set(str(s).upper() for s in required_standards)
        
        matched = required_standards_set & product_standards
        missing = required_standards_set - product_standards
        
        return {
            "overall_compliant": len(missing) == 0,
            "compliance_details": [
                {
                    "standard": std,
                    "compliant": std.upper() in product_standards,
                    "evidence": "Product certifications" if std.upper() in product_standards else "Not found",
                    "confidence": 1.0 if std.upper() in product_standards else 0.0,
                    "notes": ""
                }
                for std in required_standards
            ],
            "missing_standards": list(missing),
            "additional_certifications": list(product_standards - required_standards_set),
            "recommendation": "comply" if len(missing) == 0 else "partial" if matched else "non-compliant"
        }
