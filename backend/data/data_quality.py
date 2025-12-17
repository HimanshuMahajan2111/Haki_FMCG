"""Data quality analysis and reporting utilities."""
import pandas as pd
from typing import Dict, List, Any, Optional
from collections import defaultdict
from datetime import datetime
import structlog

logger = structlog.get_logger()


class DataQualityAnalyzer:
    """Analyze data quality and generate reports."""
    
    def __init__(self):
        """Initialize analyzer."""
        self.logger = structlog.get_logger("DataQualityAnalyzer")
    
    def generate_statistics(self, data: List[Dict[str, Any]], 
                          data_type: str = "Unknown") -> Dict[str, Any]:
        """Generate comprehensive statistics for dataset.
        
        Args:
            data: List of data records
            data_type: Type of data being analyzed
            
        Returns:
            Dictionary with statistics
        """
        if not data:
            return {
                'data_type': data_type,
                'total_records': 0,
                'error': 'No data provided'
            }
        
        stats = {
            'data_type': data_type,
            'total_records': len(data),
            'timestamp': datetime.now().isoformat(),
            'field_analysis': self._analyze_fields(data),
            'completeness': self._calculate_completeness(data),
            'data_types': self._analyze_data_types(data),
            'value_ranges': self._analyze_value_ranges(data),
            'duplicates': self._find_duplicates(data),
        }
        
        return stats
    
    def preview_data(self, data: List[Dict[str, Any]], 
                    num_records: int = 5) -> Dict[str, Any]:
        """Generate data preview with sample records.
        
        Args:
            data: List of data records
            num_records: Number of records to preview
            
        Returns:
            Dictionary with preview information
        """
        if not data:
            return {'error': 'No data to preview'}
        
        preview = {
            'total_records': len(data),
            'sample_size': min(num_records, len(data)),
            'sample_records': data[:num_records],
            'fields': list(data[0].keys()) if data else [],
            'field_count': len(data[0].keys()) if data else 0,
        }
        
        return preview
    
    def generate_quality_report(self, 
                               products: List[Dict[str, Any]],
                               testing: Dict[str, List[Dict[str, Any]]],
                               standards: Dict[str, List[Dict[str, Any]]],
                               rfps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive data quality report.
        
        Args:
            products: Product data
            testing: Testing data
            standards: Standards data
            rfps: Historical RFP data
            
        Returns:
            Comprehensive quality report
        """
        self.logger.info("Generating data quality report")
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'products': self._summarize_dataset(products, 'Products'),
                'testing': self._summarize_testing(testing),
                'standards': self._summarize_standards(standards),
                'historical_rfps': self._summarize_dataset(rfps, 'Historical RFPs'),
            },
            'quality_scores': {
                'products': self._calculate_quality_score(products),
                'testing': self._calculate_testing_quality(testing),
                'standards': self._calculate_standards_quality(standards),
                'rfps': self._calculate_quality_score(rfps),
            },
            'issues': self._identify_issues(products, testing, standards, rfps),
            'recommendations': self._generate_recommendations(products, testing, standards, rfps),
        }
        
        # Overall quality score
        scores = [v for v in report['quality_scores'].values() if v > 0]
        report['overall_quality_score'] = sum(scores) / len(scores) if scores else 0
        
        self.logger.info(
            "Quality report generated",
            overall_score=report['overall_quality_score']
        )
        
        return report
    
    def _analyze_fields(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze field presence and consistency."""
        if not data:
            return {}
        
        # Get all unique fields
        all_fields = set()
        for record in data:
            all_fields.update(record.keys())
        
        field_stats = {}
        for field in all_fields:
            present_count = sum(1 for record in data if field in record)
            non_empty_count = sum(
                1 for record in data 
                if field in record and record[field] and str(record[field]).strip()
            )
            
            field_stats[field] = {
                'present_in': present_count,
                'present_percentage': (present_count / len(data)) * 100,
                'non_empty': non_empty_count,
                'completeness': (non_empty_count / len(data)) * 100,
            }
        
        return field_stats
    
    def _calculate_completeness(self, data: List[Dict[str, Any]]) -> float:
        """Calculate overall data completeness percentage."""
        if not data:
            return 0.0
        
        total_fields = sum(len(record) for record in data)
        filled_fields = sum(
            1 for record in data 
            for value in record.values() 
            if value and str(value).strip() and str(value) != 'nan'
        )
        
        return (filled_fields / total_fields * 100) if total_fields > 0 else 0.0
    
    def _analyze_data_types(self, data: List[Dict[str, Any]]) -> Dict[str, str]:
        """Analyze data types of fields."""
        if not data:
            return {}
        
        type_analysis = {}
        fields = set()
        for record in data:
            fields.update(record.keys())
        
        for field in fields:
            types_seen = set()
            for record in data:
                if field in record and record[field]:
                    types_seen.add(type(record[field]).__name__)
            
            type_analysis[field] = ', '.join(types_seen) if types_seen else 'unknown'
        
        return type_analysis
    
    def _analyze_value_ranges(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze value ranges for numeric fields."""
        if not data:
            return {}
        
        ranges = {}
        numeric_fields = ['price', 'cost', 'quantity', 'discount', 'mrp', 
                         'selling_price', 'dealer_price']
        
        for field in numeric_fields:
            values = []
            for record in data:
                if field in record and record[field]:
                    try:
                        val = float(str(record[field]).replace('₹', '').replace(',', ''))
                        if val > 0:
                            values.append(val)
                    except (ValueError, AttributeError):
                        pass
            
            if values:
                ranges[field] = {
                    'min': min(values),
                    'max': max(values),
                    'average': sum(values) / len(values),
                    'count': len(values),
                }
        
        return ranges
    
    def _find_duplicates(self, data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Find duplicate records based on key fields."""
        if not data:
            return {}
        
        # Try to find duplicates based on common identifier fields
        identifier_fields = ['product_id', 'name', 'model', 'rfp_id', 
                           'standard_code', 'test_name']
        
        duplicates = {}
        for field in identifier_fields:
            values = [record.get(field) for record in data if field in record]
            if values:
                seen = set()
                dup_count = 0
                for val in values:
                    if val in seen:
                        dup_count += 1
                    seen.add(val)
                
                if dup_count > 0:
                    duplicates[field] = dup_count
        
        return duplicates
    
    def _summarize_dataset(self, data: List[Dict[str, Any]], 
                          name: str) -> Dict[str, Any]:
        """Create summary for a dataset."""
        if not data:
            return {
                'name': name,
                'count': 0,
                'status': 'empty'
            }
        
        return {
            'name': name,
            'count': len(data),
            'completeness': self._calculate_completeness(data),
            'field_count': len(data[0].keys()) if data else 0,
            'status': 'loaded'
        }
    
    def _summarize_testing(self, testing: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Summarize testing data."""
        if not testing:
            return {'count': 0, 'status': 'empty'}
        
        total_records = sum(len(v) if isinstance(v, list) else 0 
                           for v in testing.values())
        
        return {
            'name': 'Testing Data',
            'categories': len(testing),
            'total_records': total_records,
            'breakdown': {k: len(v) if isinstance(v, list) else 0 
                         for k, v in testing.items()},
            'status': 'loaded'
        }
    
    def _summarize_standards(self, standards: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Summarize standards data."""
        if not standards:
            return {'count': 0, 'status': 'empty'}
        
        total_records = sum(len(v) if isinstance(v, list) else 0 
                           for v in standards.values())
        
        return {
            'name': 'Standards Data',
            'categories': len(standards),
            'total_records': total_records,
            'breakdown': {k: len(v) if isinstance(v, list) else 0 
                         for k, v in standards.items()},
            'status': 'loaded'
        }
    
    def _calculate_quality_score(self, data: List[Dict[str, Any]]) -> float:
        """Calculate quality score (0-100) for dataset."""
        if not data:
            return 0.0
        
        # Factors: completeness (40%), consistency (30%), validity (30%)
        completeness = self._calculate_completeness(data)
        
        # Consistency: check for similar field structure
        field_counts = [len(record) for record in data]
        avg_fields = sum(field_counts) / len(field_counts)
        consistency = 100 - (sum(abs(c - avg_fields) for c in field_counts) / len(data))
        
        # Validity: check for non-empty required fields
        required_fields = ['name', 'product_id', 'rfp_id', 'test_name', 'standard_code']
        valid_count = 0
        for record in data:
            has_required = any(
                field in record and record[field] and str(record[field]).strip()
                for field in required_fields
            )
            if has_required:
                valid_count += 1
        validity = (valid_count / len(data)) * 100
        
        quality_score = (completeness * 0.4) + (consistency * 0.3) + (validity * 0.3)
        return round(quality_score, 2)
    
    def _calculate_testing_quality(self, testing: Dict[str, List[Dict[str, Any]]]) -> float:
        """Calculate quality score for testing data."""
        if not testing:
            return 0.0
        
        scores = []
        for category, data in testing.items():
            if isinstance(data, list) and data:
                scores.append(self._calculate_quality_score(data))
        
        return round(sum(scores) / len(scores), 2) if scores else 0.0
    
    def _calculate_standards_quality(self, standards: Dict[str, List[Dict[str, Any]]]) -> float:
        """Calculate quality score for standards data."""
        if not standards:
            return 0.0
        
        scores = []
        for category, data in standards.items():
            if isinstance(data, list) and data:
                scores.append(self._calculate_quality_score(data))
        
        return round(sum(scores) / len(scores), 2) if scores else 0.0
    
    def _identify_issues(self, products, testing, standards, rfps) -> List[Dict[str, str]]:
        """Identify data quality issues."""
        issues = []
        
        # Check products
        if products:
            completeness = self._calculate_completeness(products)
            if completeness < 50:
                issues.append({
                    'severity': 'high',
                    'dataset': 'products',
                    'issue': f'Low data completeness: {completeness:.1f}%'
                })
        
        # Check for missing datasets
        if not products:
            issues.append({'severity': 'critical', 'dataset': 'products', 
                          'issue': 'No product data loaded'})
        if not testing:
            issues.append({'severity': 'medium', 'dataset': 'testing', 
                          'issue': 'No testing data loaded'})
        if not standards:
            issues.append({'severity': 'medium', 'dataset': 'standards', 
                          'issue': 'No standards data loaded'})
        
        return issues
    
    def _generate_recommendations(self, products, testing, standards, rfps) -> List[str]:
        """Generate recommendations for improving data quality."""
        recommendations = []
        
        if products:
            completeness = self._calculate_completeness(products)
            if completeness < 80:
                recommendations.append(
                    f"Improve product data completeness from {completeness:.1f}% to at least 80%"
                )
        
        if not rfps or len(rfps) < 5:
            recommendations.append(
                "Add more historical RFP data for better analysis (minimum 5 recommended)"
            )
        
        if not testing:
            recommendations.append(
                "Add testing and certification data for compliance checking"
            )
        
        if not standards:
            recommendations.append(
                "Add standards data for better product matching and validation"
            )
        
        return recommendations
