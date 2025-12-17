"""
Memory and Context Management for Technical Agent.
"""
from typing import Dict, Any, List, Optional
import structlog
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import deque
import pickle

logger = structlog.get_logger()


class TechnicalAgentMemory:
    """Memory system for Technical Agent with context persistence."""
    
    def __init__(self, memory_dir: str = "./memory"):
        """Initialize memory system.
        
        Args:
            memory_dir: Directory to store memory files
        """
        self.logger = logger.bind(component="TechnicalAgentMemory")
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # Short-term memory (current session)
        self.short_term = {
            'current_rfp': None,
            'recent_matches': deque(maxlen=100),
            'recent_queries': deque(maxlen=50),
            'session_stats': {}
        }
        
        # Long-term memory (persistent)
        self.long_term = {
            'rfp_history': [],
            'product_preferences': {},
            'common_patterns': {},
            'learning_data': {}
        }
        
        # Conversation history
        self.conversation_history = deque(maxlen=1000)
        
        # Load from disk
        self._load_memory()
        
        self.logger.info("Memory system initialized", memory_dir=memory_dir)
    
    def store_rfp_processing(self, rfp_id: str, rfp_data: Dict[str, Any], result: Dict[str, Any]):
        """Store RFP processing results.
        
        Args:
            rfp_id: RFP identifier
            rfp_data: RFP data
            result: Processing result
        """
        entry = {
            'rfp_id': rfp_id,
            'processed_at': datetime.now().isoformat(),
            'rfp_data': rfp_data,
            'result_summary': {
                'requirements_count': result.get('summary', {}).get('total_requirements', 0),
                'matches_found': result.get('summary', {}).get('requirements_matched', 0),
                'avg_confidence': result.get('summary', {}).get('average_confidence', 0),
            },
            'products_recommended': [
                {
                    'requirement': comp['requirement']['item_name'],
                    'top_product': comp['products'][0]['product_name'] if comp['products'] else None,
                    'score': comp['products'][0]['overall_score'] if comp['products'] else 0
                }
                for comp in result.get('comparisons', [])
            ]
        }
        
        # Store in short-term
        self.short_term['current_rfp'] = entry
        
        # Store in long-term
        self.long_term['rfp_history'].append(entry)
        
        # Update patterns
        self._update_patterns(rfp_data, result)
        
        # Persist
        self._save_memory()
        
        self.logger.info("RFP processing stored in memory", rfp_id=rfp_id)
    
    def store_product_match(self, requirement: Dict[str, Any], match: Dict[str, Any], score: float):
        """Store product match for learning.
        
        Args:
            requirement: Product requirement
            match: Matched product
            score: Match score
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'requirement': requirement,
            'match': match,
            'score': score
        }
        
        self.short_term['recent_matches'].append(entry)
        
        # Update product preferences
        product_id = match.get('product_id')
        category = requirement.get('item_name', 'unknown')
        
        if category not in self.long_term['product_preferences']:
            self.long_term['product_preferences'][category] = {}
        
        if product_id not in self.long_term['product_preferences'][category]:
            self.long_term['product_preferences'][category][product_id] = {
                'product_name': match.get('product_name'),
                'manufacturer': match.get('manufacturer'),
                'match_count': 0,
                'avg_score': 0.0,
                'total_score': 0.0
            }
        
        prefs = self.long_term['product_preferences'][category][product_id]
        prefs['match_count'] += 1
        prefs['total_score'] += score
        prefs['avg_score'] = prefs['total_score'] / prefs['match_count']
    
    def store_conversation(self, role: str, message: str, metadata: Optional[Dict[str, Any]] = None):
        """Store conversation message.
        
        Args:
            role: Message role (user/agent/system)
            message: Message content
            metadata: Additional metadata
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'role': role,
            'message': message,
            'metadata': metadata or {}
        }
        
        self.conversation_history.append(entry)
    
    def get_similar_rfps(self, current_rfp: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """Get similar RFPs from history.
        
        Args:
            current_rfp: Current RFP data
            limit: Maximum results
            
        Returns:
            List of similar RFPs
        """
        if not self.long_term['rfp_history']:
            return []
        
        # Simple similarity based on keywords
        current_text = f"{current_rfp.get('title', '')} {current_rfp.get('description', '')}".lower()
        current_keywords = set(current_text.split())
        
        scored_rfps = []
        
        for historical_rfp in self.long_term['rfp_history'][-100:]:  # Last 100 RFPs
            hist_text = f"{historical_rfp['rfp_data'].get('title', '')} {historical_rfp['rfp_data'].get('description', '')}".lower()
            hist_keywords = set(hist_text.split())
            
            # Jaccard similarity
            intersection = len(current_keywords & hist_keywords)
            union = len(current_keywords | hist_keywords)
            similarity = intersection / union if union > 0 else 0
            
            if similarity > 0.1:
                scored_rfps.append((historical_rfp, similarity))
        
        # Sort by similarity
        scored_rfps.sort(key=lambda x: x[1], reverse=True)
        
        return [rfp for rfp, _ in scored_rfps[:limit]]
    
    def get_preferred_products(self, category: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get preferred products for a category.
        
        Args:
            category: Product category
            limit: Maximum results
            
        Returns:
            List of preferred products
        """
        if category not in self.long_term['product_preferences']:
            return []
        
        prefs = self.long_term['product_preferences'][category]
        
        # Sort by average score and match count
        sorted_prefs = sorted(
            prefs.items(),
            key=lambda x: (x[1]['avg_score'], x[1]['match_count']),
            reverse=True
        )
        
        return [
            {
                'product_id': pid,
                **pdata
            }
            for pid, pdata in sorted_prefs[:limit]
        ]
    
    def get_conversation_context(self, last_n: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation context.
        
        Args:
            last_n: Number of recent messages
            
        Returns:
            List of conversation messages
        """
        return list(self.conversation_history)[-last_n:]
    
    def clear_short_term_memory(self):
        """Clear short-term memory."""
        self.short_term = {
            'current_rfp': None,
            'recent_matches': deque(maxlen=100),
            'recent_queries': deque(maxlen=50),
            'session_stats': {}
        }
        self.logger.info("Short-term memory cleared")
    
    def _update_patterns(self, rfp_data: Dict[str, Any], result: Dict[str, Any]):
        """Update common patterns from processing."""
        # Extract patterns from successful matches
        for comp in result.get('comparisons', []):
            if not comp.get('products'):
                continue
            
            req = comp['requirement']
            top_product = comp['products'][0]
            
            # Category pattern
            category = req.get('item_name', 'unknown')
            manufacturer = top_product.get('manufacturer')
            
            if category not in self.long_term['common_patterns']:
                self.long_term['common_patterns'][category] = {
                    'manufacturers': {},
                    'specifications': {},
                    'certifications': set()
                }
            
            # Track manufacturer success
            if manufacturer:
                if manufacturer not in self.long_term['common_patterns'][category]['manufacturers']:
                    self.long_term['common_patterns'][category]['manufacturers'][manufacturer] = 0
                self.long_term['common_patterns'][category]['manufacturers'][manufacturer] += 1
            
            # Track common specifications
            for spec_key in req.get('specifications', {}).keys():
                if spec_key not in self.long_term['common_patterns'][category]['specifications']:
                    self.long_term['common_patterns'][category]['specifications'][spec_key] = 0
                self.long_term['common_patterns'][category]['specifications'][spec_key] += 1
            
            # Track certifications
            for cert in top_product.get('certifications', []):
                self.long_term['common_patterns'][category]['certifications'].add(cert)
    
    def _save_memory(self):
        """Persist memory to disk."""
        try:
            # Save long-term memory
            with open(self.memory_dir / "long_term_memory.pkl", 'wb') as f:
                pickle.dump(self.long_term, f)
            
            # Save conversation history
            with open(self.memory_dir / "conversation_history.json", 'w') as f:
                json.dump(list(self.conversation_history), f, indent=2)
            
            self.logger.debug("Memory persisted to disk")
        except Exception as e:
            self.logger.error(f"Failed to save memory: {e}")
    
    def _load_memory(self):
        """Load memory from disk."""
        try:
            # Load long-term memory
            long_term_path = self.memory_dir / "long_term_memory.pkl"
            if long_term_path.exists():
                with open(long_term_path, 'rb') as f:
                    self.long_term = pickle.load(f)
            
            # Load conversation history
            conv_path = self.memory_dir / "conversation_history.json"
            if conv_path.exists():
                with open(conv_path, 'r') as f:
                    history = json.load(f)
                    self.conversation_history = deque(history, maxlen=1000)
            
            self.logger.info("Memory loaded from disk")
        except Exception as e:
            self.logger.error(f"Failed to load memory: {e}")


class ContextManager:
    """Manage contextual information during processing."""
    
    def __init__(self):
        """Initialize context manager."""
        self.logger = logger.bind(component="ContextManager")
        self.context_stack = []
        self.global_context = {}
    
    def push_context(self, context_type: str, data: Dict[str, Any]):
        """Push new context onto stack.
        
        Args:
            context_type: Type of context (rfp, requirement, product, etc.)
            data: Context data
        """
        context = {
            'type': context_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        self.context_stack.append(context)
        self.logger.debug(f"Context pushed: {context_type}", stack_size=len(self.context_stack))
    
    def pop_context(self) -> Optional[Dict[str, Any]]:
        """Pop context from stack.
        
        Returns:
            Popped context or None
        """
        if self.context_stack:
            context = self.context_stack.pop()
            self.logger.debug(f"Context popped: {context['type']}")
            return context
        return None
    
    def get_current_context(self, context_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get current context.
        
        Args:
            context_type: Optional type to filter
            
        Returns:
            Current context or None
        """
        if not self.context_stack:
            return None
        
        if context_type:
            # Find most recent context of type
            for context in reversed(self.context_stack):
                if context['type'] == context_type:
                    return context
            return None
        else:
            return self.context_stack[-1]
    
    def get_context_chain(self) -> List[Dict[str, Any]]:
        """Get full context chain.
        
        Returns:
            List of all contexts
        """
        return self.context_stack.copy()
    
    def set_global_context(self, key: str, value: Any):
        """Set global context value.
        
        Args:
            key: Context key
            value: Context value
        """
        self.global_context[key] = value
        self.logger.debug(f"Global context set: {key}")
    
    def get_global_context(self, key: str, default: Any = None) -> Any:
        """Get global context value.
        
        Args:
            key: Context key
            default: Default value
            
        Returns:
            Context value
        """
        return self.global_context.get(key, default)
    
    def clear_context(self):
        """Clear all context."""
        self.context_stack.clear()
        self.global_context.clear()
        self.logger.info("Context cleared")
