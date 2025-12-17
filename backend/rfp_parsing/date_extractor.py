"""
Date and Deadline Extractor - Extract dates, deadlines, and timelines from RFP documents.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, date
import re
import structlog

logger = structlog.get_logger()


@dataclass
class Deadline:
    """Deadline information."""
    deadline_type: str  # submission, clarification, pre_bid, etc.
    date: Optional[date] = None
    time: Optional[str] = None
    description: str = ""
    is_mandatory: bool = True
    source_text: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'deadline_type': self.deadline_type,
            'date': self.date.isoformat() if self.date else None,
            'time': self.time,
            'description': self.description,
            'is_mandatory': self.is_mandatory,
            'source_text': self.source_text
        }


class DateExtractor:
    """Extract dates and deadlines from text."""
    
    def __init__(self):
        """Initialize date extractor."""
        self.logger = logger.bind(component="DateExtractor")
        
        # Date patterns (DD/MM/YYYY, DD-MM-YYYY, etc.)
        self.date_patterns = [
            # DD/MM/YYYY or DD-MM-YYYY or DD.MM.YYYY
            r'(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})',
            # YYYY-MM-DD
            r'(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})',
            # DD Month YYYY (e.g., 15 December 2025)
            r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
            # Month DD, YYYY (e.g., December 15, 2025)
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})',
        ]
        
        # Time patterns
        self.time_patterns = [
            r'(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)',
            r'(\d{1,2}):(\d{2})\s*(?:hours|hrs)?',
        ]
        
        # Deadline keywords
        self.deadline_keywords = {
            'submission': [
                'submission deadline', 'last date for submission', 'submit by',
                'proposal due', 'bid submission', 'tender submission'
            ],
            'clarification': [
                'clarification deadline', 'queries by', 'last date for queries',
                'question deadline'
            ],
            'pre_bid': [
                'pre-bid meeting', 'pre bid conference', 'site visit'
            ],
            'opening': [
                'bid opening', 'tender opening', 'opening date'
            ],
            'validity': [
                'bid validity', 'proposal validity', 'valid until'
            ]
        }
    
    def extract_dates(self, text: str) -> List[date]:
        """Extract all dates from text.
        
        Args:
            text: Text content
            
        Returns:
            List of date objects
        """
        dates = []
        
        for pattern in self.date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                try:
                    parsed_date = self._parse_date_match(match)
                    if parsed_date:
                        dates.append(parsed_date)
                except Exception as e:
                    self.logger.debug("Failed to parse date", match=match.group(0), error=str(e))
        
        return dates
    
    def extract_deadlines(self, text: str) -> List[Deadline]:
        """Extract deadlines from text.
        
        Args:
            text: Text content
            
        Returns:
            List of Deadline objects
        """
        deadlines = []
        
        # Split text into lines for context
        lines = text.split('\n')
        
        for deadline_type, keywords in self.deadline_keywords.items():
            for keyword in keywords:
                # Find lines containing the keyword
                pattern = re.compile(rf'.*{re.escape(keyword)}.*', re.IGNORECASE)
                
                for line in lines:
                    if pattern.search(line):
                        # Extract date from this line
                        line_dates = self.extract_dates(line)
                        line_times = self._extract_times(line)
                        
                        deadline = Deadline(
                            deadline_type=deadline_type,
                            date=line_dates[0] if line_dates else None,
                            time=line_times[0] if line_times else None,
                            description=keyword,
                            source_text=line.strip()
                        )
                        
                        deadlines.append(deadline)
        
        return deadlines
    
    def _parse_date_match(self, match: re.Match) -> Optional[date]:
        """Parse date from regex match.
        
        Args:
            match: Regex match object
            
        Returns:
            date object or None
        """
        groups = match.groups()
        
        # Handle different date formats
        if len(groups) == 3:
            # Check if month names are used
            month_names = [
                'January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'
            ]
            
            # DD Month YYYY
            if groups[1] in month_names:
                day = int(groups[0])
                month = month_names.index(groups[1]) + 1
                year = int(groups[2])
                return date(year, month, day)
            
            # Month DD, YYYY
            elif groups[0] in month_names:
                month = month_names.index(groups[0]) + 1
                day = int(groups[1])
                year = int(groups[2])
                return date(year, month, day)
            
            # DD/MM/YYYY
            elif int(groups[0]) <= 31 and int(groups[1]) <= 12:
                day = int(groups[0])
                month = int(groups[1])
                year = int(groups[2])
                return date(year, month, day)
            
            # YYYY-MM-DD
            elif int(groups[0]) > 1900:
                year = int(groups[0])
                month = int(groups[1])
                day = int(groups[2])
                return date(year, month, day)
        
        return None
    
    def _extract_times(self, text: str) -> List[str]:
        """Extract time values from text.
        
        Args:
            text: Text content
            
        Returns:
            List of time strings
        """
        times = []
        
        for pattern in self.time_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                times.append(match.group(0))
        
        return times
    
    def find_submission_deadline(self, text: str) -> Optional[Deadline]:
        """Find the submission deadline (most important).
        
        Args:
            text: Text content
            
        Returns:
            Deadline object or None
        """
        deadlines = self.extract_deadlines(text)
        
        # Find submission deadlines
        submission_deadlines = [
            d for d in deadlines 
            if d.deadline_type == 'submission'
        ]
        
        return submission_deadlines[0] if submission_deadlines else None
    
    def get_timeline(self, text: str) -> Dict[str, List[Deadline]]:
        """Get complete timeline of all deadlines.
        
        Args:
            text: Text content
            
        Returns:
            Dictionary mapping deadline types to deadlines
        """
        deadlines = self.extract_deadlines(text)
        
        timeline = {}
        for deadline in deadlines:
            if deadline.deadline_type not in timeline:
                timeline[deadline.deadline_type] = []
            timeline[deadline.deadline_type].append(deadline)
        
        return timeline
