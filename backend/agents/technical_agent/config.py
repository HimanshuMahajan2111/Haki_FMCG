"""
Configuration Management for Technical Agent
Handles API keys, feature flags, and optional component settings
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import json


class TechnicalAgentConfig:
    """
    Centralized configuration for the Technical Agent
    
    Features:
    - API key management (environment variables or config file)
    - Feature flags for optional components
    - Mock mode for testing without API keys
    - Default settings for all components
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration
        
        Args:
            config_file: Path to JSON config file (optional)
        """
        self.config_file = config_file
        self._load_config()
    
    def _load_config(self):
        """Load configuration from environment variables and config file"""
        # Default configuration
        self.config = {
            # LLM Settings
            'llm': {
                'enabled': True,
                'provider': 'openai',  # 'openai', 'anthropic', or 'mock'
                'openai_api_key': os.getenv('OPENAI_API_KEY'),
                'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
                'openai_model': 'gpt-4',
                'anthropic_model': 'claude-3-sonnet-20240229',
                'temperature': 0.1,
                'max_tokens': 2000,
                'use_mock': False  # Use mock LLM for testing
            },
            
            # Vector Search Settings
            'vector_search': {
                'enabled': True,
                'model_name': 'all-MiniLM-L6-v2',  # SentenceTransformer model
                'index_path': './vector_index',
                'similarity_threshold': 0.7,
                'top_k': 10,
                'use_mock': False  # Use mock embeddings for testing
            },
            
            # Hybrid Matching Settings
            'hybrid_matching': {
                'enabled': True,
                'vector_weight': 0.7,  # Alpha parameter
                'rule_weight': 0.3,
                'use_vector_fallback': True
            },
            
            # Memory Settings
            'memory': {
                'enabled': True,
                'storage_path': './memory',
                'short_term_size': 100,
                'long_term_persist': True,
                'conversation_history_size': 1000
            },
            
            # API Settings
            'api': {
                'enabled': False,
                'host': '0.0.0.0',
                'port': 8000,
                'webhook_enabled': True,
                'webhook_retry_attempts': 3
            },
            
            # Monitoring Settings
            'monitoring': {
                'enabled': True,
                'performance_tracking': True,
                'quality_assurance': True,
                'metrics_export_path': './metrics'
            },
            
            # Scoring Weights
            'scoring': {
                'specification_weight': 0.4,
                'certification_weight': 0.3,
                'price_weight': 0.2,
                'delivery_weight': 0.1
            },
            
            # QA Thresholds
            'quality_thresholds': {
                'min_confidence': 0.6,
                'min_match_score': 0.5,
                'max_missing_specs': 3
            }
        }
        
        # Load from config file if provided
        if self.config_file and Path(self.config_file).exists():
            with open(self.config_file, 'r') as f:
                user_config = json.load(f)
                self._merge_config(user_config)
    
    def _merge_config(self, user_config: Dict[str, Any]):
        """Merge user configuration with defaults"""
        for key, value in user_config.items():
            if key in self.config and isinstance(value, dict):
                self.config[key].update(value)
            else:
                self.config[key] = value
    
    def get(self, *keys, default=None):
        """
        Get configuration value using dot notation
        
        Example:
            config.get('llm', 'provider')  # Returns 'openai'
        """
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def set(self, *keys, value):
        """
        Set configuration value using dot notation
        
        Example:
            config.set('llm', 'provider', value='mock')
        """
        config = self.config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value
    
    def enable_mock_mode(self):
        """Enable mock mode for all optional features (for testing without API keys)"""
        self.set('llm', 'use_mock', value=True)
        self.set('llm', 'provider', value='mock')
        self.set('vector_search', 'use_mock', value=True)
        print("✅ Mock mode enabled - LLM and Vector features will use mock implementations")
    
    def disable_mock_mode(self):
        """Disable mock mode and use real implementations"""
        self.set('llm', 'use_mock', value=False)
        self.set('vector_search', 'use_mock', value=False)
        
        # Check if API keys are available
        has_openai = self.get('llm', 'openai_api_key') is not None
        has_anthropic = self.get('llm', 'anthropic_api_key') is not None
        
        if not has_openai and not has_anthropic:
            print("⚠️ Warning: No API keys found. LLM features may not work.")
            print("   Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable")
        else:
            print("✅ Real API mode enabled")
    
    def has_llm_api_key(self) -> bool:
        """Check if any LLM API key is configured"""
        return (self.get('llm', 'openai_api_key') is not None or 
                self.get('llm', 'anthropic_api_key') is not None)
    
    def can_use_llm(self) -> bool:
        """Check if LLM features can be used"""
        if self.get('llm', 'use_mock'):
            return True  # Mock mode always works
        return self.has_llm_api_key()
    
    def can_use_vector_search(self) -> bool:
        """Check if vector search can be used"""
        if self.get('vector_search', 'use_mock'):
            return True  # Mock mode always works
        
        try:
            import faiss
            import sentence_transformers
            return True
        except ImportError:
            return False
    
    def save_config(self, filepath: str):
        """Save current configuration to JSON file"""
        # Don't save API keys to file for security
        safe_config = self.config.copy()
        if 'llm' in safe_config:
            safe_config['llm'] = {k: v for k, v in safe_config['llm'].items() 
                                 if 'api_key' not in k}
        
        with open(filepath, 'w') as f:
            json.dump(safe_config, f, indent=2)
        
        print(f"✅ Configuration saved to {filepath}")
    
    def print_status(self):
        """Print current configuration status"""
        print("\n" + "="*60)
        print("TECHNICAL AGENT CONFIGURATION STATUS")
        print("="*60)
        
        # LLM Status
        print("\n🤖 LLM Integration:")
        if self.get('llm', 'use_mock'):
            print("  Status: ✅ ENABLED (Mock Mode)")
        elif self.has_llm_api_key():
            provider = self.get('llm', 'provider')
            model = self.get('llm', f'{provider}_model')
            print(f"  Status: ✅ ENABLED ({provider.upper()})")
            print(f"  Model: {model}")
        else:
            print("  Status: ⚠️ DISABLED (No API Key)")
        
        # Vector Search Status
        print("\n🔍 Vector Search:")
        if self.get('vector_search', 'use_mock'):
            print("  Status: ✅ ENABLED (Mock Mode)")
        elif self.can_use_vector_search():
            model = self.get('vector_search', 'model_name')
            print(f"  Status: ✅ ENABLED")
            print(f"  Model: {model}")
        else:
            print("  Status: ⚠️ DISABLED (Missing Dependencies)")
        
        # Hybrid Matching Status
        print("\n⚖️ Hybrid Matching:")
        if self.get('hybrid_matching', 'enabled'):
            alpha = self.get('hybrid_matching', 'vector_weight')
            print(f"  Status: ✅ ENABLED")
            print(f"  Weights: {alpha:.1f} vector + {1-alpha:.1f} rule-based")
        else:
            print("  Status: ⚠️ DISABLED")
        
        # Other Features
        print("\n📦 Other Features:")
        features = [
            ('Memory System', self.get('memory', 'enabled')),
            ('API Interface', self.get('api', 'enabled')),
            ('Monitoring', self.get('monitoring', 'enabled')),
        ]
        for name, enabled in features:
            status = "✅ ENABLED" if enabled else "⚠️ DISABLED"
            print(f"  {name}: {status}")
        
        print("\n" + "="*60 + "\n")


# Singleton instance
_config_instance = None

def get_config(config_file: Optional[str] = None) -> TechnicalAgentConfig:
    """Get or create configuration singleton"""
    global _config_instance
    if _config_instance is None:
        _config_instance = TechnicalAgentConfig(config_file)
    return _config_instance


def reset_config():
    """Reset configuration singleton (useful for testing)"""
    global _config_instance
    _config_instance = None


if __name__ == "__main__":
    # Demo configuration usage
    print("Technical Agent Configuration Demo\n")
    
    # Create configuration
    config = TechnicalAgentConfig()
    
    # Print status
    config.print_status()
    
    # Enable mock mode
    print("\nEnabling mock mode for testing...")
    config.enable_mock_mode()
    config.print_status()
    
    # Save configuration
    config.save_config('example_config.json')
    print("\n✅ Configuration demo complete!")
