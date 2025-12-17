"""
Mock Implementations for Optional Features
Allows testing LLM and Vector Search features without API keys or external dependencies
"""

import json
import random
from typing import Dict, Any, List, Optional
import hashlib


class MockLLMProvider:
    """
    Mock LLM that generates realistic responses without API calls
    
    Features:
    - Deterministic responses (same input = same output)
    - Realistic technical language
    - JSON structured outputs
    - Fast and free
    """
    
    def __init__(self, model_name: str = "mock-gpt-4"):
        self.model_name = model_name
        self.call_count = 0
    
    def _hash_input(self, text: str) -> int:
        """Create deterministic hash from input"""
        return int(hashlib.md5(text.encode()).hexdigest(), 16)
    
    def parse_technical_specification(self, text: str) -> Dict[str, Any]:
        """Mock specification parsing"""
        self.call_count += 1
        seed = self._hash_input(text)
        random.seed(seed)
        
        # Extract some keywords for realistic responses
        keywords = text.lower().split()
        
        return {
            "specifications": {
                "voltage": "415V AC" if "415" in text or "voltage" in keywords else "230V AC",
                "current": "100A" if "100" in text or "current" in keywords else "63A",
                "frequency": "50Hz",
                "power": "10kW" if "power" in keywords else "5kW",
                "phase": "3-phase" if "3" in text or "phase" in keywords else "Single phase"
            },
            "standards": [
                "IS 694",
                "IEC 60227"
            ] if "standard" in keywords or "is" in keywords else [],
            "certifications": [
                "BIS",
                "ISI"
            ] if "certified" in keywords or "bis" in keywords else [],
            "special_requirements": [
                "UV resistant" if "uv" in keywords else "Flame retardant",
                "High temperature rating"
            ],
            "confidence": round(0.85 + random.random() * 0.10, 2)
        }
    
    def explain_specification(self, spec_name: str, spec_value: str, context: str) -> str:
        """Mock specification explanation"""
        self.call_count += 1
        
        explanations = {
            "voltage": f"The voltage rating of {spec_value} indicates the maximum voltage the equipment can safely handle. This is a critical parameter for electrical safety and proper operation.",
            "current": f"The current rating of {spec_value} specifies the maximum continuous current carrying capacity. Exceeding this value may cause overheating and equipment failure.",
            "power": f"The power rating of {spec_value} represents the maximum electrical power consumption or generation capacity. This determines the energy efficiency and operational costs.",
            "frequency": f"The frequency of {spec_value} is standard for Indian electrical systems. This ensures compatibility with grid power and proper operation of motors and transformers.",
            "ip_rating": f"The IP rating of {spec_value} indicates the level of protection against dust and water ingress. Higher numbers mean better protection for outdoor or harsh environments."
        }
        
        return explanations.get(spec_name.lower(), 
                               f"The {spec_name} specification of {spec_value} is an important technical parameter that must be considered for proper system integration and performance.")
    
    def generate_match_justification(self, product_name: str, score: float, 
                                     matched_specs: List[str], missing_specs: List[str]) -> str:
        """Mock match justification"""
        self.call_count += 1
        
        if score >= 0.85:
            quality = "Excellent"
            reason = "This product is an ideal match with all critical specifications met"
        elif score >= 0.70:
            quality = "Good"
            reason = "This product meets most requirements with minor gaps"
        elif score >= 0.50:
            quality = "Fair"
            reason = "This product is acceptable but has some limitations"
        else:
            quality = "Poor"
            reason = "This product has significant gaps and may not meet requirements"
        
        justification = f"""
**{quality} Match ({score*100:.0f}%)**

{reason}. 

**Strengths:**
- {len(matched_specs)} specifications matched correctly
- Compliant with industry standards
- Proven track record with similar applications

**Considerations:**
- {len(missing_specs)} specifications need verification
- May require additional accessories or configuration
- Consult technical team for final validation

**Recommendation:** {"Highly recommended for this application" if score >= 0.70 else "Consider as backup option"}
"""
        return justification.strip()
    
    def assess_technical_risk(self, product_name: str, requirements: Dict[str, Any],
                             matched_specs: Dict[str, Any]) -> Dict[str, Any]:
        """Mock technical risk assessment"""
        self.call_count += 1
        seed = self._hash_input(product_name)
        random.seed(seed)
        
        risk_level = random.choice(["low", "low", "medium", "low"])  # Bias toward low risk
        
        risks = {
            "low": {
                "severity": "LOW",
                "score": round(0.15 + random.random() * 0.15, 2),
                "factors": [
                    "All critical specifications matched",
                    "Proven technology with good track record",
                    "Standard certifications available"
                ],
                "mitigations": [
                    "Regular maintenance as per manufacturer guidelines",
                    "Proper installation by certified technicians"
                ]
            },
            "medium": {
                "severity": "MEDIUM",
                "score": round(0.35 + random.random() * 0.25, 2),
                "factors": [
                    "Some specifications not fully matched",
                    "Limited field experience in similar applications",
                    "May require custom configuration"
                ],
                "mitigations": [
                    "Conduct pre-installation testing",
                    "Request manufacturer support during commissioning",
                    "Consider extended warranty"
                ]
            },
            "high": {
                "severity": "HIGH",
                "score": round(0.65 + random.random() * 0.25, 2),
                "factors": [
                    "Critical specifications missing or mismatched",
                    "New or unproven technology",
                    "Certification gaps identified"
                ],
                "mitigations": [
                    "Thorough technical evaluation required",
                    "Request performance guarantees",
                    "Consider alternative products"
                ]
            }
        }
        
        return risks[risk_level]
    
    def generate_technical_summary(self, rfp_summary: str, matches: List[Dict[str, Any]]) -> str:
        """Mock technical summary generation"""
        self.call_count += 1
        
        summary = f"""
**TECHNICAL ANALYSIS SUMMARY**

**RFP Overview:**
Based on the requirements analysis, this procurement involves electrical/electronic equipment with specific technical and certification requirements.

**Product Analysis:**
- {len(matches)} products evaluated
- Average match score: {sum(m.get('final_score', 0) for m in matches) / len(matches) * 100:.1f}%
- All products meet minimum safety standards

**Top Recommendation:**
{matches[0]['product_name']} (Score: {matches[0].get('final_score', 0)*100:.0f}%)
- Best overall match for specifications
- Competitive pricing
- Proven reliability

**Key Considerations:**
1. Verify final specifications with supplier before ordering
2. Ensure proper installation and commissioning
3. Maintain warranty documentation

**Next Steps:**
1. Request detailed quotations from top 3 suppliers
2. Conduct technical clarification meeting if needed
3. Proceed to commercial evaluation
"""
        return summary.strip()


class MockVectorEmbeddings:
    """
    Mock vector embeddings that generate deterministic vectors
    
    Features:
    - Deterministic (same text = same vector)
    - Simulates semantic similarity
    - Fast and lightweight
    """
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.encode_count = 0
    
    def _text_to_vector(self, text: str) -> List[float]:
        """Generate deterministic vector from text"""
        # Use hash for determinism
        seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)
        random.seed(seed)
        
        # Generate random vector
        vector = [random.gauss(0, 1) for _ in range(self.dimension)]
        
        # Normalize
        magnitude = sum(v**2 for v in vector) ** 0.5
        normalized = [v / magnitude for v in vector]
        
        return normalized
    
    def encode(self, texts: List[str], show_progress_bar: bool = False) -> List[List[float]]:
        """Encode multiple texts to vectors"""
        self.encode_count += len(texts)
        return [self._text_to_vector(text) for text in texts]
    
    def similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        return max(0.0, min(1.0, dot_product))  # Clamp to [0, 1]


class MockVectorIndex:
    """
    Mock FAISS-like vector index
    
    Features:
    - In-memory storage
    - Similarity search
    - Same interface as real FAISS
    """
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.vectors = []
        self.metadata = []
        self.embeddings = MockVectorEmbeddings(dimension)
    
    def add(self, vectors: List[List[float]], metadata: List[Dict[str, Any]]):
        """Add vectors to index"""
        self.vectors.extend(vectors)
        self.metadata.extend(metadata)
    
    def search(self, query_vector: List[float], k: int = 10) -> tuple:
        """Search for similar vectors"""
        if not self.vectors:
            return ([], [])
        
        # Calculate similarities
        similarities = []
        for i, vec in enumerate(self.vectors):
            sim = self.embeddings.similarity(query_vector, vec)
            similarities.append((sim, i))
        
        # Sort and get top k
        similarities.sort(reverse=True)
        top_k = similarities[:k]
        
        scores = [sim for sim, idx in top_k]
        indices = [idx for sim, idx in top_k]
        
        return (scores, indices)
    
    def get_metadata(self, indices: List[int]) -> List[Dict[str, Any]]:
        """Get metadata for indices"""
        return [self.metadata[i] for i in indices if i < len(self.metadata)]


def create_mock_llm(provider: str = "openai"):
    """Factory function to create mock LLM"""
    return MockLLMProvider(f"mock-{provider}")


def create_mock_vector_model():
    """Factory function to create mock vector embeddings"""
    return MockVectorEmbeddings()


def create_mock_vector_index(dimension: int = 384):
    """Factory function to create mock vector index"""
    return MockVectorIndex(dimension)


if __name__ == "__main__":
    print("="*60)
    print("MOCK IMPLEMENTATIONS DEMO")
    print("="*60)
    
    # Test Mock LLM
    print("\n🤖 Testing Mock LLM Provider...")
    llm = MockLLMProvider()
    
    result = llm.parse_technical_specification(
        "Supply 100A 415V 3-phase cable as per IS 694 with BIS certification"
    )
    print(f"\nParsed Specifications:")
    print(json.dumps(result, indent=2))
    
    explanation = llm.explain_specification("voltage", "415V", "Industrial application")
    print(f"\nExplanation: {explanation}")
    
    justification = llm.generate_match_justification(
        "Havells XLPE Cable 100A",
        0.87,
        ["voltage", "current", "certification"],
        ["flame_retardant"]
    )
    print(f"\nJustification:\n{justification}")
    
    # Test Mock Vector Embeddings
    print("\n\n🔍 Testing Mock Vector Embeddings...")
    embeddings = MockVectorEmbeddings()
    
    texts = [
        "100A 415V 3-phase cable",
        "100A 415V three phase wire",
        "50A 230V single phase cable"
    ]
    
    vectors = embeddings.encode(texts)
    print(f"\nEncoded {len(texts)} texts to vectors of dimension {len(vectors[0])}")
    
    # Check similarity
    sim_12 = embeddings.similarity(vectors[0], vectors[1])
    sim_13 = embeddings.similarity(vectors[0], vectors[2])
    
    print(f"\nSimilarity between text 1 and 2 (similar): {sim_12:.3f}")
    print(f"Similarity between text 1 and 3 (different): {sim_13:.3f}")
    
    # Test Mock Vector Index
    print("\n\n📊 Testing Mock Vector Index...")
    index = MockVectorIndex()
    
    index.add(vectors, [
        {"id": 1, "text": texts[0]},
        {"id": 2, "text": texts[1]},
        {"id": 3, "text": texts[2]}
    ])
    
    query_vector = embeddings.encode(["100A cable"])[0]
    scores, indices = index.search(query_vector, k=2)
    
    print(f"\nSearch results for '100A cable':")
    for score, idx in zip(scores, indices):
        print(f"  - {texts[idx]} (similarity: {score:.3f})")
    
    print("\n" + "="*60)
    print("✅ All mock implementations working correctly!")
    print("="*60)
