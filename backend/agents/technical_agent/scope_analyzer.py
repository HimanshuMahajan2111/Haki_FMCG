"""
Scope Analyzer and Multi-Item RFP Handler.
"""
from typing import List, Dict, Any, Optional, Tuple
import structlog
import re
from collections import defaultdict
from datetime import datetime

logger = structlog.get_logger()


class ScopeOfSupplyAnalyzer:
    """Analyze scope of supply from RFP."""
    
    def __init__(self):
        """Initialize scope analyzer."""
        self.logger = logger.bind(component="ScopeOfSupplyAnalyzer")
    
    def analyze_scope(self, rfp_text: str, rfp_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze complete scope of supply.
        
        Args:
            rfp_text: RFP text content
            rfp_metadata: RFP metadata
            
        Returns:
            Comprehensive scope analysis
        """
        self.logger.info("Analyzing scope of supply")
        
        # Extract items
        items = self._extract_items(rfp_text)
        
        # Categorize by product type
        categories = self._categorize_items(items)
        
        # Analyze dependencies
        dependencies = self._analyze_dependencies(items)
        
        # Estimate project scope
        project_scope = self._estimate_project_scope(items, rfp_metadata)
        
        # Identify special requirements
        special_reqs = self._identify_special_requirements(rfp_text)
        
        scope_analysis = {
            'total_items': len(items),
            'items': items,
            'categories': categories,
            'dependencies': dependencies,
            'project_scope': project_scope,
            'special_requirements': special_reqs,
            'complexity_score': self._calculate_complexity(items, special_reqs),
            'estimated_duration_days': self._estimate_duration(items, special_reqs)
        }
        
        self.logger.info(
            "Scope analysis completed",
            items=len(items),
            categories=len(categories),
            complexity=scope_analysis['complexity_score']
        )
        
        return scope_analysis
    
    def _extract_items(self, text: str) -> List[Dict[str, Any]]:
        """Extract individual items from RFP text."""
        items = []
        
        # Pattern: Item number, description, quantity
        patterns = [
            r'(?:Item|Sr\.?\s*No\.?)\s*[:\-]?\s*(\d+)[:\.\)]\s*([^\n]+)\s*Qty[:\-]?\s*(\d+)',
            r'(\d+)\.\s*([^\n]+)\s*[-–]\s*(\d+)\s*(?:Nos|Units|Pcs)',
            r'Item\s+(\d+)[:\.\)]\s*([^\n]+)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                item_num = match.group(1)
                description = match.group(2).strip()
                quantity = int(match.group(3)) if len(match.groups()) >= 3 else 1
                
                items.append({
                    'item_number': item_num,
                    'description': description,
                    'quantity': quantity,
                    'unit': 'nos'
                })
        
        # If no items found, create generic items
        if not items:
            items = [{
                'item_number': '1',
                'description': 'General Supply as per RFP',
                'quantity': 1,
                'unit': 'lot'
            }]
        
        return items
    
    def _categorize_items(self, items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize items by product type."""
        categories = defaultdict(list)
        
        category_keywords = {
            'Cable': ['cable', 'wire', 'conductor'],
            'Switchgear': ['switch', 'breaker', 'mcb', 'mccb', 'isolator'],
            'Lighting': ['light', 'led', 'lamp', 'luminaire'],
            'Panel': ['panel', 'distribution board', 'mcc', 'pcc'],
            'Motor': ['motor', 'induction motor'],
            'Transformer': ['transformer', 'distribution transformer'],
            'Pump': ['pump', 'water pump'],
            'Fan': ['fan', 'exhaust fan'],
            'HVAC': ['ac', 'air conditioner', 'hvac'],
            'Other': []
        }
        
        for item in items:
            desc_lower = item['description'].lower()
            categorized = False
            
            for category, keywords in category_keywords.items():
                if category == 'Other':
                    continue
                if any(kw in desc_lower for kw in keywords):
                    categories[category].append(item)
                    categorized = True
                    break
            
            if not categorized:
                categories['Other'].append(item)
        
        return dict(categories)
    
    def _analyze_dependencies(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze dependencies between items."""
        dependencies = []
        
        # Common dependency patterns
        dependency_patterns = [
            (['cable', 'wire'], ['switchgear', 'breaker'], 'electrical_connection'),
            (['motor', 'pump'], ['starter', 'panel'], 'control_system'),
            (['light', 'led'], ['driver', 'ballast'], 'power_supply'),
        ]
        
        for item1 in items:
            desc1 = item1['description'].lower()
            
            for item2 in items:
                if item1 == item2:
                    continue
                
                desc2 = item2['description'].lower()
                
                for keywords1, keywords2, dep_type in dependency_patterns:
                    if (any(kw in desc1 for kw in keywords1) and 
                        any(kw in desc2 for kw in keywords2)):
                        dependencies.append({
                            'item1': item1['item_number'],
                            'item2': item2['item_number'],
                            'type': dep_type,
                            'description': f"{item1['description']} requires {item2['description']}"
                        })
        
        return dependencies
    
    def _estimate_project_scope(
        self,
        items: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Estimate overall project scope."""
        total_qty = sum(item.get('quantity', 1) for item in items)
        
        # Estimate value per item
        avg_value_per_item = metadata.get('estimated_value', 0) / len(items) if items else 0
        
        return {
            'total_line_items': len(items),
            'total_quantity': total_qty,
            'estimated_value': metadata.get('estimated_value', 0),
            'avg_value_per_item': avg_value_per_item,
            'project_type': self._classify_project_type(items),
            'delivery_locations': metadata.get('delivery_locations', ['Single location']),
            'installation_required': self._check_installation_required(items)
        }
    
    def _classify_project_type(self, items: List[Dict[str, Any]]) -> str:
        """Classify project type based on items."""
        total_items = len(items)
        
        if total_items == 1:
            return 'single_item'
        elif total_items <= 5:
            return 'small_supply'
        elif total_items <= 20:
            return 'medium_supply'
        else:
            return 'large_supply'
    
    def _check_installation_required(self, items: List[Dict[str, Any]]) -> bool:
        """Check if installation is required."""
        installation_keywords = ['install', 'commission', 'setup', 'erection']
        
        for item in items:
            desc = item['description'].lower()
            if any(kw in desc for kw in installation_keywords):
                return True
        
        return False
    
    def _identify_special_requirements(self, text: str) -> List[str]:
        """Identify special requirements from RFP."""
        special_reqs = []
        
        # Common special requirements
        req_patterns = {
            'testing': r'(?:type|routine|acceptance)\s+test',
            'certification': r'(?:BIS|ISI|CE|UL)\s+cert',
            'warranty': r'warranty\s+(?:of\s+)?(\d+)\s+(?:year|month)',
            'installation': r'installation\s+(?:and|&)\s+commissioning',
            'documentation': r'(?:test|inspection)\s+certificate',
            'training': r'(?:training|operator\s+manual)',
            'AMC': r'(?:AMC|annual\s+maintenance)',
            'buyback': r'(?:buyback|old\s+equipment)',
        }
        
        for req_type, pattern in req_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                special_reqs.append(req_type)
        
        return special_reqs
    
    def _calculate_complexity(
        self,
        items: List[Dict[str, Any]],
        special_reqs: List[str]
    ) -> float:
        """Calculate project complexity score (0-1)."""
        score = 0.0
        
        # Item count contributes to complexity
        item_score = min(len(items) / 50, 0.3)
        score += item_score
        
        # Number of categories
        categories = len(self._categorize_items(items))
        category_score = min(categories / 10, 0.2)
        score += category_score
        
        # Special requirements
        special_score = min(len(special_reqs) / 5, 0.3)
        score += special_score
        
        # Dependencies
        dependencies = self._analyze_dependencies(items)
        dep_score = min(len(dependencies) / 10, 0.2)
        score += dep_score
        
        return min(score, 1.0)
    
    def _estimate_duration(
        self,
        items: List[Dict[str, Any]],
        special_reqs: List[str]
    ) -> int:
        """Estimate project duration in days."""
        # Base duration
        base_days = 30
        
        # Add time for item count
        item_days = len(items) * 2
        
        # Add time for special requirements
        special_days = len(special_reqs) * 5
        
        # Add time for testing
        if 'testing' in special_reqs:
            special_days += 15
        
        # Add time for installation
        if 'installation' in special_reqs:
            special_days += 20
        
        total_days = base_days + item_days + special_days
        
        return min(total_days, 180)  # Cap at 6 months


class MultiItemRFPHandler:
    """Handle RFPs with multiple items efficiently."""
    
    def __init__(self):
        """Initialize multi-item handler."""
        self.logger = logger.bind(component="MultiItemRFPHandler")
    
    def process_multi_item_rfp(
        self,
        rfp: Dict[str, Any],
        items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process RFP with multiple items.
        
        Args:
            rfp: RFP metadata
            items: List of items extracted from RFP
            
        Returns:
            Processed multi-item RFP structure
        """
        self.logger.info(f"Processing multi-item RFP with {len(items)} items")
        
        # Group similar items
        grouped_items = self._group_similar_items(items)
        
        # Prioritize items
        prioritized = self._prioritize_items(items, rfp)
        
        # Create processing plan
        plan = self._create_processing_plan(grouped_items, prioritized)
        
        result = {
            'rfp_id': rfp.get('rfp_id'),
            'total_items': len(items),
            'grouped_items': grouped_items,
            'prioritized_items': prioritized,
            'processing_plan': plan,
            'estimated_processing_time_minutes': self._estimate_processing_time(items),
            'batch_strategy': self._determine_batch_strategy(items)
        }
        
        self.logger.info(
            "Multi-item RFP processed",
            items=len(items),
            groups=len(grouped_items),
            strategy=result['batch_strategy']
        )
        
        return result
    
    def _group_similar_items(self, items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group similar items together."""
        groups = defaultdict(list)
        
        for item in items:
            # Extract category from description
            desc = item.get('description', '').lower()
            
            # Simple keyword-based grouping
            if 'cable' in desc or 'wire' in desc:
                groups['cables'].append(item)
            elif 'switch' in desc or 'breaker' in desc:
                groups['switchgear'].append(item)
            elif 'light' in desc or 'led' in desc:
                groups['lighting'].append(item)
            elif 'motor' in desc:
                groups['motors'].append(item)
            else:
                groups['other'].append(item)
        
        return dict(groups)
    
    def _prioritize_items(
        self,
        items: List[Dict[str, Any]],
        rfp: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Prioritize items based on value, complexity, etc."""
        scored_items = []
        
        total_value = rfp.get('estimated_value', 0)
        value_per_item = total_value / len(items) if items else 0
        
        for item in items:
            priority_score = 0.0
            
            # Higher quantity = higher priority
            qty = item.get('quantity', 1)
            if qty > 100:
                priority_score += 3
            elif qty > 10:
                priority_score += 2
            else:
                priority_score += 1
            
            # Complex items get higher priority
            desc = item.get('description', '').lower()
            if any(word in desc for word in ['custom', 'special', 'design']):
                priority_score += 2
            
            # Critical items
            if any(word in desc for word in ['critical', 'urgent', 'immediate']):
                priority_score += 3
            
            scored_items.append({
                **item,
                'priority_score': priority_score,
                'priority_level': 'high' if priority_score >= 5 else 'medium' if priority_score >= 3 else 'low'
            })
        
        # Sort by priority
        scored_items.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return scored_items
    
    def _create_processing_plan(
        self,
        grouped_items: Dict[str, List[Dict[str, Any]]],
        prioritized: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create optimal processing plan."""
        plan = {
            'batches': [],
            'parallel_processing': [],
            'sequential_processing': [],
            'estimated_duration_minutes': 0
        }
        
        # Create batches by group
        for group_name, group_items in grouped_items.items():
            if len(group_items) > 1:
                plan['batches'].append({
                    'batch_id': f"batch_{group_name}",
                    'group': group_name,
                    'items': [item['item_number'] for item in group_items],
                    'can_process_parallel': True
                })
            else:
                plan['sequential_processing'].extend([item['item_number'] for item in group_items])
        
        # High priority items processed first
        high_priority = [item for item in prioritized if item['priority_level'] == 'high']
        if high_priority:
            plan['sequential_processing'] = (
                [item['item_number'] for item in high_priority] +
                [x for x in plan['sequential_processing'] 
                 if x not in [item['item_number'] for item in high_priority]]
            )
        
        return plan
    
    def _estimate_processing_time(self, items: List[Dict[str, Any]]) -> int:
        """Estimate processing time in minutes."""
        # Base time per item
        base_time = 2  # minutes
        
        # Additional time for complex items
        complex_keywords = ['custom', 'special', 'design', 'fabricated']
        
        total_time = 0
        for item in items:
            desc = item.get('description', '').lower()
            item_time = base_time
            
            if any(kw in desc for kw in complex_keywords):
                item_time *= 2
            
            total_time += item_time
        
        return total_time
    
    def _determine_batch_strategy(self, items: List[Dict[str, Any]]) -> str:
        """Determine optimal batch processing strategy."""
        if len(items) <= 5:
            return 'sequential'
        elif len(items) <= 20:
            return 'small_batch'
        elif len(items) <= 50:
            return 'medium_batch'
        else:
            return 'large_batch'


class GapAnalysisGenerator:
    """Generate gap analysis between requirements and offerings."""
    
    def __init__(self):
        """Initialize gap analysis generator."""
        self.logger = logger.bind(component="GapAnalysisGenerator")
    
    def generate_gap_analysis(
        self,
        requirement: Dict[str, Any],
        matched_products: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate comprehensive gap analysis.
        
        Args:
            requirement: Product requirement
            matched_products: List of matched products
            
        Returns:
            Gap analysis report
        """
        self.logger.info("Generating gap analysis")
        
        if not matched_products:
            return {
                'has_gaps': True,
                'severity': 'critical',
                'gaps': [{'type': 'no_match', 'description': 'No matching products found'}],
                'recommendations': ['Review requirements', 'Consider alternative specifications']
            }
        
        # Analyze best match
        best_match = matched_products[0]
        
        gaps = []
        
        # Specification gaps
        spec_gaps = self._analyze_specification_gaps(
            requirement.get('specifications', {}),
            best_match.get('specifications', {})
        )
        gaps.extend(spec_gaps)
        
        # Certification gaps
        cert_gaps = self._analyze_certification_gaps(
            requirement.get('required_certifications', []) + requirement.get('required_standards', []),
            best_match.get('certifications', []) + best_match.get('standards_compliance', [])
        )
        gaps.extend(cert_gaps)
        
        # Price gaps
        price_gap = self._analyze_price_gap(
            requirement.get('max_unit_price'),
            best_match.get('unit_price')
        )
        if price_gap:
            gaps.append(price_gap)
        
        # Delivery gaps
        delivery_gap = self._analyze_delivery_gap(
            requirement.get('delivery_days_required'),
            best_match.get('delivery_days')
        )
        if delivery_gap:
            gaps.append(delivery_gap)
        
        # Determine severity
        severity = self._calculate_gap_severity(gaps)
        
        # Generate recommendations
        recommendations = self._generate_gap_recommendations(gaps, best_match)
        
        return {
            'has_gaps': len(gaps) > 0,
            'gap_count': len(gaps),
            'severity': severity,
            'gaps': gaps,
            'recommendations': recommendations,
            'mitigation_strategies': self._generate_mitigation_strategies(gaps),
            'alternative_approach': self._suggest_alternative_approach(gaps, requirement)
        }
    
    def _analyze_specification_gaps(
        self,
        required: Dict[str, Any],
        available: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Analyze specification gaps."""
        gaps = []
        
        for key, req_value in required.items():
            if key not in available:
                gaps.append({
                    'type': 'specification',
                    'category': key,
                    'required': req_value,
                    'available': None,
                    'severity': 'high',
                    'description': f"Required {key}: {req_value} not available"
                })
            else:
                avail_value = available[key]
                if str(req_value).lower() != str(avail_value).lower():
                    gaps.append({
                        'type': 'specification',
                        'category': key,
                        'required': req_value,
                        'available': avail_value,
                        'severity': 'medium',
                        'description': f"{key} mismatch: required {req_value}, got {avail_value}"
                    })
        
        return gaps
    
    def _analyze_certification_gaps(
        self,
        required: List[str],
        available: List[str]
    ) -> List[Dict[str, Any]]:
        """Analyze certification gaps."""
        gaps = []
        
        required_set = set(s.upper() for s in required)
        available_set = set(s.upper() for s in available)
        
        missing = required_set - available_set
        
        for cert in missing:
            gaps.append({
                'type': 'certification',
                'category': cert,
                'required': cert,
                'available': None,
                'severity': 'high',
                'description': f"Required certification {cert} missing"
            })
        
        return gaps
    
    def _analyze_price_gap(
        self,
        max_price: Optional[float],
        actual_price: Optional[float]
    ) -> Optional[Dict[str, Any]]:
        """Analyze price gap."""
        if max_price is None or actual_price is None:
            return None
        
        if actual_price > max_price:
            over_budget = ((actual_price - max_price) / max_price) * 100
            return {
                'type': 'price',
                'category': 'budget',
                'required': f"≤ ₹{max_price:,.2f}",
                'available': f"₹{actual_price:,.2f}",
                'severity': 'high' if over_budget > 20 else 'medium',
                'description': f"Price {over_budget:.1f}% over budget"
            }
        
        return None
    
    def _analyze_delivery_gap(
        self,
        required_days: Optional[int],
        actual_days: Optional[int]
    ) -> Optional[Dict[str, Any]]:
        """Analyze delivery gap."""
        if required_days is None or actual_days is None:
            return None
        
        if actual_days > required_days:
            delay = actual_days - required_days
            return {
                'type': 'delivery',
                'category': 'timeline',
                'required': f"{required_days} days",
                'available': f"{actual_days} days",
                'severity': 'high' if delay > 30 else 'low',
                'description': f"Delivery delayed by {delay} days"
            }
        
        return None
    
    def _calculate_gap_severity(self, gaps: List[Dict[str, Any]]) -> str:
        """Calculate overall gap severity."""
        if not gaps:
            return 'none'
        
        high_count = sum(1 for g in gaps if g['severity'] == 'high')
        
        if high_count >= 3:
            return 'critical'
        elif high_count >= 1:
            return 'high'
        elif len(gaps) >= 3:
            return 'medium'
        else:
            return 'low'
    
    def _generate_gap_recommendations(
        self,
        gaps: List[Dict[str, Any]],
        product: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations to address gaps."""
        recommendations = []
        
        spec_gaps = [g for g in gaps if g['type'] == 'specification']
        if spec_gaps:
            recommendations.append("Consider specification relaxation or custom manufacturing")
        
        cert_gaps = [g for g in gaps if g['type'] == 'certification']
        if cert_gaps:
            recommendations.append("Request manufacturer to obtain missing certifications")
        
        price_gaps = [g for g in gaps if g['type'] == 'price']
        if price_gaps:
            recommendations.append("Negotiate pricing or increase budget allocation")
        
        delivery_gaps = [g for g in gaps if g['type'] == 'delivery']
        if delivery_gaps:
            recommendations.append("Adjust project timeline or request expedited delivery")
        
        if not recommendations:
            recommendations.append("Product meets all requirements - proceed with purchase")
        
        return recommendations
    
    def _generate_mitigation_strategies(self, gaps: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Generate mitigation strategies for gaps."""
        strategies = []
        
        for gap in gaps:
            if gap['type'] == 'specification':
                strategies.append({
                    'gap': gap['description'],
                    'strategy': 'Request custom modification or accept nearest available specification',
                    'effort': 'medium',
                    'cost_impact': 'low-medium'
                })
            elif gap['type'] == 'certification':
                strategies.append({
                    'gap': gap['description'],
                    'strategy': 'Work with manufacturer to obtain certification or accept equivalent',
                    'effort': 'high',
                    'cost_impact': 'medium'
                })
            elif gap['type'] == 'price':
                strategies.append({
                    'gap': gap['description'],
                    'strategy': 'Negotiate volume discount or consider alternative product',
                    'effort': 'low',
                    'cost_impact': 'high'
                })
        
        return strategies
    
    def _suggest_alternative_approach(
        self,
        gaps: List[Dict[str, Any]],
        requirement: Dict[str, Any]
    ) -> Optional[str]:
        """Suggest alternative approach if gaps are significant."""
        high_severity_gaps = [g for g in gaps if g['severity'] in ['high', 'critical']]
        
        if len(high_severity_gaps) >= 3:
            return "Consider revising requirements or splitting into multiple items"
        elif len(high_severity_gaps) >= 2:
            return "Explore alternative product categories or manufacturers"
        elif gaps:
            return "Minor adjustments should resolve all gaps"
        else:
            return None
