"""
Quality Metrics and Preview Generator.
"""
from typing import Dict, Any, List, Optional
import structlog
from pathlib import Path

logger = structlog.get_logger()


class QualityMetrics:
    """Calculate parsing quality metrics."""
    
    def __init__(self):
        """Initialize quality metrics calculator."""
        self.logger = logger.bind(component="QualityMetrics")
    
    def calculate_text_quality(self, text: str) -> Dict[str, Any]:
        """Calculate text extraction quality metrics.
        
        Args:
            text: Extracted text
            
        Returns:
            Quality metrics dictionary
        """
        if not text:
            return {
                'text_length': 0,
                'has_content': False,
                'quality_score': 0.0
            }
        
        metrics = {
            'text_length': len(text),
            'word_count': len(text.split()),
            'line_count': len(text.split('\n')),
            'has_content': len(text.strip()) > 0,
            'avg_line_length': len(text) / max(len(text.split('\n')), 1),
            'alphanumeric_ratio': self._calculate_alphanumeric_ratio(text)
        }
        
        # Calculate quality score (0-100)
        score = 0.0
        
        if metrics['has_content']:
            score += 20
        
        if metrics['word_count'] > 50:
            score += 30
        
        if metrics['alphanumeric_ratio'] > 0.7:
            score += 30
        
        if metrics['avg_line_length'] > 20:
            score += 20
        
        metrics['quality_score'] = min(score, 100.0)
        
        return metrics
    
    def calculate_table_quality(self, tables: List[Any]) -> Dict[str, Any]:
        """Calculate table extraction quality.
        
        Args:
            tables: List of tables/DataFrames
            
        Returns:
            Quality metrics
        """
        if not tables:
            return {
                'table_count': 0,
                'has_tables': False,
                'quality_score': 0.0
            }
        
        import pandas as pd
        
        total_rows = 0
        total_cols = 0
        empty_tables = 0
        
        for table in tables:
            if isinstance(table, pd.DataFrame):
                rows, cols = table.shape
                total_rows += rows
                total_cols += cols
                
                if rows == 0 or cols == 0:
                    empty_tables += 1
        
        metrics = {
            'table_count': len(tables),
            'has_tables': len(tables) > 0,
            'total_rows': total_rows,
            'total_columns': total_cols,
            'avg_rows_per_table': total_rows / len(tables) if tables else 0,
            'avg_cols_per_table': total_cols / len(tables) if tables else 0,
            'empty_tables': empty_tables
        }
        
        # Quality score
        score = 0.0
        
        if metrics['has_tables']:
            score += 30
        
        if metrics['avg_rows_per_table'] >= 3:
            score += 30
        
        if metrics['avg_cols_per_table'] >= 3:
            score += 20
        
        if metrics['empty_tables'] == 0:
            score += 20
        
        metrics['quality_score'] = min(score, 100.0)
        
        return metrics
    
    def calculate_overall_quality(
        self,
        text_metrics: Dict[str, Any],
        table_metrics: Dict[str, Any],
        boq_count: int = 0,
        spec_count: int = 0
    ) -> Dict[str, Any]:
        """Calculate overall parsing quality.
        
        Args:
            text_metrics: Text quality metrics
            table_metrics: Table quality metrics
            boq_count: Number of BOQ items found
            spec_count: Number of specifications found
            
        Returns:
            Overall quality metrics
        """
        text_score = text_metrics.get('quality_score', 0)
        table_score = table_metrics.get('quality_score', 0)
        
        # Weighted average
        overall_score = (
            text_score * 0.4 +
            table_score * 0.3 +
            (min(boq_count, 10) * 10) * 0.15 +
            (min(spec_count, 10) * 10) * 0.15
        )
        
        return {
            'overall_score': min(overall_score, 100.0),
            'text_quality': text_score,
            'table_quality': table_score,
            'boq_items': boq_count,
            'specifications': spec_count,
            'completeness': self._assess_completeness(
                text_metrics,
                table_metrics,
                boq_count,
                spec_count
            )
        }
    
    def _calculate_alphanumeric_ratio(self, text: str) -> float:
        """Calculate ratio of alphanumeric characters."""
        if not text:
            return 0.0
        
        alphanumeric = sum(c.isalnum() or c.isspace() for c in text)
        return alphanumeric / len(text)
    
    def _assess_completeness(
        self,
        text_metrics: Dict[str, Any],
        table_metrics: Dict[str, Any],
        boq_count: int,
        spec_count: int
    ) -> str:
        """Assess parsing completeness.
        
        Returns:
            Completeness level: excellent, good, fair, poor
        """
        has_text = text_metrics.get('has_content', False)
        has_tables = table_metrics.get('has_tables', False)
        has_boq = boq_count > 0
        has_specs = spec_count > 0
        
        complete_count = sum([has_text, has_tables, has_boq, has_specs])
        
        if complete_count == 4:
            return 'excellent'
        elif complete_count == 3:
            return 'good'
        elif complete_count >= 2:
            return 'fair'
        else:
            return 'poor'


class PreviewGenerator:
    """Generate previews and summaries of parsed documents."""
    
    def __init__(self):
        """Initialize preview generator."""
        self.logger = logger.bind(component="PreviewGenerator")
    
    def generate_text_preview(
        self,
        text: str,
        max_length: int = 500
    ) -> str:
        """Generate text preview.
        
        Args:
            text: Full text
            max_length: Maximum preview length
            
        Returns:
            Preview text
        """
        if not text:
            return ""
        
        if len(text) <= max_length:
            return text
        
        # Take first max_length chars and end at word boundary
        preview = text[:max_length]
        last_space = preview.rfind(' ')
        
        if last_space > 0:
            preview = preview[:last_space]
        
        return preview + "..."
    
    def generate_table_preview(
        self,
        tables: List[Any],
        max_rows: int = 5
    ) -> List[Dict[str, Any]]:
        """Generate table previews.
        
        Args:
            tables: List of tables
            max_rows: Maximum rows to preview
            
        Returns:
            List of table preview dictionaries
        """
        import pandas as pd
        
        previews = []
        
        for idx, table in enumerate(tables):
            if isinstance(table, pd.DataFrame):
                preview = {
                    'table_index': idx,
                    'shape': table.shape,
                    'columns': list(table.columns),
                    'preview_data': table.head(max_rows).to_dict('records')
                }
                previews.append(preview)
        
        return previews
    
    def generate_summary(
        self,
        file_path: str,
        text: str,
        tables: List[Any],
        boq_count: int,
        spec_count: int,
        quality_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate document summary.
        
        Args:
            file_path: Document file path
            text: Extracted text
            tables: Extracted tables
            boq_count: BOQ item count
            spec_count: Specification count
            quality_metrics: Quality metrics
            
        Returns:
            Summary dictionary
        """
        return {
            'file_name': Path(file_path).name,
            'file_path': file_path,
            'text_preview': self.generate_text_preview(text, 300),
            'statistics': {
                'text_length': len(text),
                'word_count': len(text.split()),
                'table_count': len(tables),
                'boq_items': boq_count,
                'specifications': spec_count
            },
            'quality': quality_metrics,
            'table_previews': self.generate_table_preview(tables, 3)
        }
