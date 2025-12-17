"""Configuration loader utilities for loading and managing app configuration."""
from typing import Any, Dict, Optional, List
from pathlib import Path
import json
import yaml
from dotenv import load_dotenv
import os
import structlog

logger = structlog.get_logger()


class ConfigLoader:
    """Load and manage application configuration from multiple sources."""
    
    def __init__(self, base_path: Optional[Path] = None):
        """Initialize configuration loader.
        
        Args:
            base_path: Base path for configuration files (defaults to current dir)
        """
        self.base_path = base_path or Path.cwd()
        self.logger = logger.bind(component="ConfigLoader")
        self._config_cache: Dict[str, Any] = {}
    
    def load_env_file(self, env_file: str = '.env') -> Dict[str, str]:
        """Load environment variables from .env file.
        
        Args:
            env_file: Name of .env file
            
        Returns:
            Dictionary of environment variables
        """
        env_path = self.base_path / env_file
        
        if env_path.exists():
            load_dotenv(env_path)
            self.logger.info(f"Loaded environment from {env_file}")
        else:
            self.logger.warning(f"Environment file not found: {env_file}")
        
        # Return all environment variables
        return dict(os.environ)
    
    def load_json(self, file_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file.
        
        Args:
            file_path: Path to JSON file (relative to base_path)
            
        Returns:
            Configuration dictionary
        """
        full_path = self.base_path / file_path
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.logger.info(f"Loaded JSON config from {file_path}")
            return config
        except FileNotFoundError:
            self.logger.error(f"JSON config file not found: {file_path}")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in {file_path}: {e}")
            return {}
    
    def load_yaml(self, file_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file.
        
        Args:
            file_path: Path to YAML file (relative to base_path)
            
        Returns:
            Configuration dictionary
        """
        full_path = self.base_path / file_path
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            self.logger.info(f"Loaded YAML config from {file_path}")
            return config or {}
        except FileNotFoundError:
            self.logger.error(f"YAML config file not found: {file_path}")
            return {}
        except yaml.YAMLError as e:
            self.logger.error(f"Invalid YAML in {file_path}: {e}")
            return {}
    
    def save_json(self, file_path: str, config: Dict[str, Any], indent: int = 2):
        """Save configuration to JSON file.
        
        Args:
            file_path: Path to JSON file (relative to base_path)
            config: Configuration dictionary
            indent: JSON indentation
        """
        full_path = self.base_path / file_path
        
        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=indent, ensure_ascii=False)
            
            self.logger.info(f"Saved JSON config to {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to save JSON config: {e}")
    
    def save_yaml(self, file_path: str, config: Dict[str, Any]):
        """Save configuration to YAML file.
        
        Args:
            file_path: Path to YAML file (relative to base_path)
            config: Configuration dictionary
        """
        full_path = self.base_path / file_path
        
        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            self.logger.info(f"Saved YAML config to {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to save YAML config: {e}")
    
    def get_env(
        self,
        key: str,
        default: Any = None,
        required: bool = False,
        cast_type: Optional[type] = None
    ) -> Any:
        """Get environment variable with type casting.
        
        Args:
            key: Environment variable name
            default: Default value if not found
            required: Whether variable is required
            cast_type: Type to cast value to (int, float, bool, etc.)
            
        Returns:
            Environment variable value
            
        Raises:
            ValueError: If required variable is not found
        """
        value = os.getenv(key, default)
        
        if required and value is None:
            raise ValueError(f"Required environment variable not found: {key}")
        
        if value is None:
            return default
        
        # Type casting
        if cast_type:
            try:
                if cast_type == bool:
                    # Special handling for boolean
                    return str(value).lower() in ('true', '1', 'yes', 'on')
                else:
                    return cast_type(value)
            except (ValueError, TypeError) as e:
                self.logger.warning(
                    f"Failed to cast {key} to {cast_type.__name__}: {e}"
                )
                return default
        
        return value
    
    def merge_configs(self, *configs: Dict[str, Any]) -> Dict[str, Any]:
        """Merge multiple configuration dictionaries.
        
        Args:
            *configs: Configuration dictionaries to merge (later ones override earlier)
            
        Returns:
            Merged configuration
        """
        merged = {}
        
        for config in configs:
            self._deep_merge(merged, config)
        
        return merged
    
    def _deep_merge(self, base: Dict, update: Dict) -> Dict:
        """Deep merge update dict into base dict.
        
        Args:
            base: Base dictionary (modified in place)
            update: Update dictionary
            
        Returns:
            Merged dictionary
        """
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
        
        return base
    
    def load_config_hierarchy(
        self,
        default_config: Optional[str] = None,
        env_config: Optional[str] = None,
        local_config: Optional[str] = None
    ) -> Dict[str, Any]:
        """Load configuration from multiple files in hierarchy.
        
        Hierarchy (later overrides earlier):
        1. Default config
        2. Environment-specific config
        3. Local config (e.g., config.local.yaml)
        
        Args:
            default_config: Default config file path
            env_config: Environment-specific config file path
            local_config: Local override config file path
            
        Returns:
            Merged configuration
        """
        configs = []
        
        # Load default config
        if default_config:
            configs.append(self.load_yaml(default_config))
        
        # Load environment-specific config
        if env_config:
            configs.append(self.load_yaml(env_config))
        
        # Load local config
        if local_config:
            local_path = self.base_path / local_config
            if local_path.exists():
                configs.append(self.load_yaml(local_config))
        
        return self.merge_configs(*configs)
    
    def get_nested(
        self,
        config: Dict[str, Any],
        path: str,
        default: Any = None,
        separator: str = '.'
    ) -> Any:
        """Get nested configuration value using dot notation.
        
        Args:
            config: Configuration dictionary
            path: Dot-separated path (e.g., 'database.pool.size')
            default: Default value if path not found
            separator: Path separator character
            
        Returns:
            Configuration value or default
        """
        keys = path.split(separator)
        value = config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set_nested(
        self,
        config: Dict[str, Any],
        path: str,
        value: Any,
        separator: str = '.'
    ):
        """Set nested configuration value using dot notation.
        
        Args:
            config: Configuration dictionary
            path: Dot-separated path (e.g., 'database.pool.size')
            value: Value to set
            separator: Path separator character
        """
        keys = path.split(separator)
        current = config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def validate_config(
        self,
        config: Dict[str, Any],
        required_keys: List[str]
    ) -> Dict[str, Any]:
        """Validate configuration has required keys.
        
        Args:
            config: Configuration dictionary
            required_keys: List of required key paths (dot notation)
            
        Returns:
            Validation result
        """
        missing = []
        
        for key_path in required_keys:
            value = self.get_nested(config, key_path)
            if value is None:
                missing.append(key_path)
        
        return {
            'is_valid': len(missing) == 0,
            'missing_keys': missing
        }
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration from environment.
        
        Returns:
            Database configuration dictionary
        """
        return {
            'url': self.get_env('DATABASE_URL', 'sqlite:///./app.db'),
            'pool_size': self.get_env('DATABASE_POOL_SIZE', 10, cast_type=int),
            'max_overflow': self.get_env('DATABASE_MAX_OVERFLOW', 20, cast_type=int),
            'echo': self.get_env('DATABASE_ECHO', False, cast_type=bool),
        }
    
    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration from environment.
        
        Returns:
            Redis configuration dictionary
        """
        return {
            'url': self.get_env('REDIS_URL', 'redis://localhost:6379/0'),
            'max_connections': self.get_env('REDIS_MAX_CONNECTIONS', 10, cast_type=int),
            'decode_responses': True,
        }
    
    def get_ai_config(self) -> Dict[str, Any]:
        """Get AI/LLM configuration from environment.
        
        Returns:
            AI configuration dictionary
        """
        return {
            'openai_api_key': self.get_env('OPENAI_API_KEY'),
            'anthropic_api_key': self.get_env('ANTHROPIC_API_KEY'),
            'default_model': self.get_env('DEFAULT_LLM_MODEL', 'gpt-4-turbo-preview'),
            'embedding_model': self.get_env('EMBEDDING_MODEL', 'text-embedding-3-small'),
            'max_tokens': self.get_env('MAX_TOKENS', 4000, cast_type=int),
            'temperature': self.get_env('TEMPERATURE', 0.7, cast_type=float),
        }
    
    def get_app_config(self) -> Dict[str, Any]:
        """Get application configuration from environment.
        
        Returns:
            Application configuration dictionary
        """
        return {
            'name': self.get_env('APP_NAME', 'RFP Response System'),
            'environment': self.get_env('ENVIRONMENT', 'development'),
            'debug': self.get_env('DEBUG', True, cast_type=bool),
            'host': self.get_env('API_HOST', '0.0.0.0'),
            'port': self.get_env('API_PORT', 8000, cast_type=int),
            'log_level': self.get_env('LOG_LEVEL', 'INFO'),
            'log_format': self.get_env('LOG_FORMAT', 'json'),
        }
    
    def export_config(self, config: Dict[str, Any], format: str = 'json') -> str:
        """Export configuration to string.
        
        Args:
            config: Configuration dictionary
            format: Output format ('json' or 'yaml')
            
        Returns:
            Configuration as string
        """
        if format == 'json':
            return json.dumps(config, indent=2, ensure_ascii=False)
        elif format == 'yaml':
            return yaml.dump(config, default_flow_style=False, allow_unicode=True)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def load_secrets(self, secrets_file: str = 'secrets.json') -> Dict[str, str]:
        """Load secrets from encrypted file (placeholder).
        
        Args:
            secrets_file: Path to secrets file
            
        Returns:
            Dictionary of secrets
        """
        # This is a placeholder - implement actual encryption/decryption
        secrets_path = self.base_path / secrets_file
        
        if secrets_path.exists():
            return self.load_json(secrets_file)
        
        self.logger.warning(f"Secrets file not found: {secrets_file}")
        return {}


# Global instance
_config_loader = None


def get_config_loader(base_path: Optional[Path] = None) -> ConfigLoader:
    """Get global config loader instance.
    
    Args:
        base_path: Base path for configuration files
        
    Returns:
        ConfigLoader instance
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader(base_path)
    return _config_loader


# Convenience functions
def load_env(env_file: str = '.env') -> Dict[str, str]:
    """Load environment variables from file.
    
    Args:
        env_file: Environment file name
        
    Returns:
        Environment variables dictionary
    """
    return get_config_loader().load_env_file(env_file)


def get_env(key: str, default: Any = None, cast_type: Optional[type] = None) -> Any:
    """Get environment variable.
    
    Args:
        key: Variable name
        default: Default value
        cast_type: Type to cast to
        
    Returns:
        Environment variable value
    """
    return get_config_loader().get_env(key, default, cast_type=cast_type)
