"""Text processing utilities for common NLP tasks used across agents."""
from typing import List, Dict, Optional, Set, Any
import re
from collections import Counter
import structlog

logger = structlog.get_logger()


class TextProcessor:
    """Common text processing and NLP utilities."""
    
    def __init__(self):
        """Initialize text processor."""
        self.logger = logger.bind(component="TextProcessor")
        
        # Common stopwords for technical text
        self.stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'can', 'may', 'might', 'must', 'shall',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it',
            'we', 'they', 'them', 'their', 'what', 'which', 'who', 'when',
            'where', 'why', 'how'
        }
        
        # Technical abbreviations to preserve
        self.preserve_abbreviations = {
            'ac', 'dc', 'led', 'lcd', 'pvc', 'xlpe', 'bis', 'iec', 'iso',
            'ul', 'ce', 'rohs', 'ip', 'mcb', 'mccb', 'rccb', 'elcb',
            'ohm', 'rpm', 'cfm', 'btu', 'hsn', 'gst', 'rfp'
        }
    
    def clean_text(self, text: str, preserve_case: bool = False) -> str:
        """Clean and normalize text.
        
        Args:
            text: Input text
            preserve_case: Whether to preserve original case
            
        Returns:
            Cleaned text
        """
        if not text:
            return ''
        
        # Convert to string if not already
        text = str(text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep alphanumeric, spaces, and basic punctuation
        text = re.sub(r'[^\w\s.,;:()\-/°]', '', text)
        
        # Normalize case
        if not preserve_case:
            # Keep technical abbreviations uppercase
            words = text.split()
            normalized = []
            for word in words:
                if word.lower() in self.preserve_abbreviations:
                    normalized.append(word.upper())
                else:
                    normalized.append(word.lower())
            text = ' '.join(normalized)
        
        return text.strip()
    
    def extract_keywords(
        self,
        text: str,
        max_keywords: int = 10,
        min_length: int = 3
    ) -> List[str]:
        """Extract important keywords from text.
        
        Args:
            text: Input text
            max_keywords: Maximum number of keywords to return
            min_length: Minimum word length
            
        Returns:
            List of keywords sorted by frequency
        """
        if not text:
            return []
        
        # Clean and tokenize
        text = self.clean_text(text)
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter words
        filtered = [
            word for word in words
            if len(word) >= min_length
            and word not in self.stopwords
        ]
        
        # Count frequencies
        counter = Counter(filtered)
        
        # Get top keywords
        keywords = [word for word, count in counter.most_common(max_keywords)]
        
        return keywords
    
    def extract_technical_terms(self, text: str) -> List[str]:
        """Extract technical terms and specifications.
        
        Args:
            text: Input text
            
        Returns:
            List of technical terms
        """
        if not text:
            return []
        
        terms = []
        
        # Pattern for voltage
        voltage_pattern = r'\b\d+\.?\d*\s*[kKmM]?[vV]\b'
        terms.extend(re.findall(voltage_pattern, text))
        
        # Pattern for current
        current_pattern = r'\b\d+\.?\d*\s*[mM]?[aA](?:mp)?\b'
        terms.extend(re.findall(current_pattern, text))
        
        # Pattern for power
        power_pattern = r'\b\d+\.?\d*\s*[kKmM]?[wW](?:att)?\b'
        terms.extend(re.findall(power_pattern, text))
        
        # Pattern for frequency
        freq_pattern = r'\b\d+\.?\d*\s*[hH][zZ]\b'
        terms.extend(re.findall(freq_pattern, text))
        
        # Pattern for dimensions
        dim_pattern = r'\b\d+\.?\d*\s*(?:mm|cm|m|inch|ft)\b'
        terms.extend(re.findall(dim_pattern, text, re.IGNORECASE))
        
        # Pattern for IP ratings
        ip_pattern = r'\bIP\s*\d{2}\b'
        terms.extend(re.findall(ip_pattern, text, re.IGNORECASE))
        
        # Pattern for standards
        std_pattern = r'\b(?:IS|IEC|BS|EN)\s*\d+(?:-\d+)?\b'
        terms.extend(re.findall(std_pattern, text, re.IGNORECASE))
        
        return list(set(terms))  # Remove duplicates
    
    def extract_numbers(self, text: str) -> List[float]:
        """Extract all numeric values from text.
        
        Args:
            text: Input text
            
        Returns:
            List of numeric values
        """
        if not text:
            return []
        
        # Pattern for numbers with optional decimal and thousands separator
        pattern = r'\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b'
        matches = re.findall(pattern, str(text))
        
        numbers = []
        for match in matches:
            try:
                # Remove commas and convert
                num = float(match.replace(',', ''))
                numbers.append(num)
            except ValueError:
                continue
        
        return numbers
    
    def extract_ranges(self, text: str) -> List[Dict[str, float]]:
        """Extract numeric ranges from text.
        
        Args:
            text: Input text (e.g., "10-20 meters", "5 to 10 kg")
            
        Returns:
            List of range dictionaries with min and max
        """
        ranges = []
        
        # Pattern for range with dash
        pattern1 = r'(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)'
        for match in re.finditer(pattern1, text):
            ranges.append({
                'min': float(match.group(1)),
                'max': float(match.group(2))
            })
        
        # Pattern for range with 'to'
        pattern2 = r'(\d+\.?\d*)\s+to\s+(\d+\.?\d*)'
        for match in re.finditer(pattern2, text, re.IGNORECASE):
            ranges.append({
                'min': float(match.group(1)),
                'max': float(match.group(2))
            })
        
        return ranges
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts (Jaccard similarity).
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0 and 1
        """
        if not text1 or not text2:
            return 0.0
        
        # Clean and tokenize
        tokens1 = set(self.clean_text(text1).split())
        tokens2 = set(self.clean_text(text2).split())
        
        # Remove stopwords
        tokens1 = tokens1 - self.stopwords
        tokens2 = tokens2 - self.stopwords
        
        if not tokens1 or not tokens2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        
        return intersection / union if union > 0 else 0.0
    
    def find_matching_phrases(
        self,
        text: str,
        phrases: List[str],
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Find phrases that match within the text.
        
        Args:
            text: Text to search in
            phrases: List of phrases to find
            threshold: Similarity threshold (0-1)
            
        Returns:
            List of matches with similarity scores
        """
        if not text or not phrases:
            return []
        
        text_lower = text.lower()
        matches = []
        
        for phrase in phrases:
            phrase_lower = phrase.lower()
            
            # Exact match
            if phrase_lower in text_lower:
                matches.append({
                    'phrase': phrase,
                    'match_type': 'exact',
                    'similarity': 1.0
                })
                continue
            
            # Fuzzy match using similarity
            similarity = self.calculate_similarity(text, phrase)
            if similarity >= threshold:
                matches.append({
                    'phrase': phrase,
                    'match_type': 'fuzzy',
                    'similarity': similarity
                })
        
        # Sort by similarity
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        return matches
    
    def summarize_text(
        self,
        text: str,
        max_sentences: int = 3
    ) -> str:
        """Create a simple extractive summary.
        
        Args:
            text: Text to summarize
            max_sentences: Maximum sentences in summary
            
        Returns:
            Summary text
        """
        if not text:
            return ''
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= max_sentences:
            return text
        
        # Score sentences by keyword density
        keywords = self.extract_keywords(text, max_keywords=20)
        keyword_set = set(keywords)
        
        scored_sentences = []
        for sentence in sentences:
            words = set(self.clean_text(sentence).split())
            score = len(words & keyword_set)
            scored_sentences.append((score, sentence))
        
        # Sort by score and take top sentences
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        top_sentences = [s for _, s in scored_sentences[:max_sentences]]
        
        # Maintain original order
        summary_sentences = []
        for sentence in sentences:
            if sentence in top_sentences:
                summary_sentences.append(sentence)
                if len(summary_sentences) == max_sentences:
                    break
        
        return '. '.join(summary_sentences) + '.'
    
    def tokenize(self, text: str, remove_stopwords: bool = True) -> List[str]:
        """Tokenize text into words.
        
        Args:
            text: Input text
            remove_stopwords: Whether to remove stopwords
            
        Returns:
            List of tokens
        """
        if not text:
            return []
        
        # Clean text
        text = self.clean_text(text)
        
        # Extract words
        tokens = re.findall(r'\b\w+\b', text.lower())
        
        # Remove stopwords if requested
        if remove_stopwords:
            tokens = [t for t in tokens if t not in self.stopwords]
        
        return tokens
    
    def extract_abbreviations(self, text: str) -> Dict[str, str]:
        """Extract abbreviations and their expansions.
        
        Args:
            text: Input text
            
        Returns:
            Dictionary mapping abbreviations to expansions
        """
        abbreviations = {}
        
        # Pattern: Full term followed by abbreviation in parentheses
        pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\(([A-Z]{2,})\)'
        
        for match in re.finditer(pattern, text):
            expansion = match.group(1)
            abbrev = match.group(2)
            abbreviations[abbrev] = expansion
        
        return abbreviations
    
    def normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace in text.
        
        Args:
            text: Input text
            
        Returns:
            Text with normalized whitespace
        """
        if not text:
            return ''
        
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        
        # Replace multiple newlines with double newline
        text = re.sub(r'\n+', '\n\n', text)
        
        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split('\n')]
        
        return '\n'.join(lines).strip()
    
    def extract_bullet_points(self, text: str) -> List[str]:
        """Extract bullet points or list items from text.
        
        Args:
            text: Input text
            
        Returns:
            List of bullet points
        """
        if not text:
            return []
        
        bullet_points = []
        
        # Pattern for various bullet formats
        patterns = [
            r'^\s*[\-\*\•]\s+(.+)$',  # - * • bullets
            r'^\s*\d+[\.\)]\s+(.+)$',  # Numbered lists
            r'^\s*[a-z][\.\)]\s+(.+)$',  # Lettered lists
        ]
        
        for line in text.split('\n'):
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    bullet_points.append(match.group(1).strip())
                    break
        
        return bullet_points
    
    def format_price(
        self,
        amount: float,
        currency: str = 'INR',
        include_symbol: bool = True
    ) -> str:
        """Format price with proper currency notation.
        
        Args:
            amount: Numeric amount
            currency: Currency code
            include_symbol: Whether to include currency symbol
            
        Returns:
            Formatted price string
        """
        if currency == 'INR':
            # Indian numbering system (lakhs and crores)
            if amount >= 10000000:  # 1 crore
                formatted = f"{amount/10000000:.2f} Cr"
            elif amount >= 100000:  # 1 lakh
                formatted = f"{amount/100000:.2f} L"
            else:
                formatted = f"{amount:,.2f}"
            
            if include_symbol:
                return f"₹{formatted}"
            return formatted
        else:
            # International format
            if include_symbol:
                return f"${amount:,.2f}"
            return f"{amount:,.2f}"
    
    def extract_dates(self, text: str) -> List[str]:
        """Extract date strings from text.
        
        Args:
            text: Input text
            
        Returns:
            List of date strings found
        """
        dates = []
        
        # Pattern for various date formats
        patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # DD/MM/YYYY or MM-DD-YYYY
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',  # YYYY-MM-DD
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b',  # Month DD, YYYY
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        
        return dates


# Global instance
_processor_instance = None


def get_text_processor() -> TextProcessor:
    """Get global text processor instance.
    
    Returns:
        TextProcessor instance
    """
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = TextProcessor()
    return _processor_instance
