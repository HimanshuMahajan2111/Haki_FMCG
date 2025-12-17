"""
Configuration Hot Reload - Monitor and reload configuration without restart.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Any, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent
import structlog
from threading import Lock

logger = structlog.get_logger()


class ConfigFileHandler(FileSystemEventHandler):
    """File system event handler for config changes."""
    
    def __init__(self, config_path: Path, callback: Callable[[dict[str, Any]], None]):
        """Initialize handler.
        
        Args:
            config_path: Path to configuration file
            callback: Function to call with new config
        """
        self.config_path = config_path
        self.callback = callback
        self.logger = logger.bind(component="ConfigFileHandler")
    
    def on_modified(self, event):
        """Handle file modification event."""
        if event.is_directory:
            return
        
        if Path(event.src_path).resolve() == self.config_path.resolve():
            self.logger.info("Config file modified", path=event.src_path)
            try:
                # Load and validate new config
                with open(self.config_path, 'r') as f:
                    new_config = json.load(f)
                
                # Call callback with new config
                self.callback(new_config)
                self.logger.info("Config reloaded successfully")
                
            except json.JSONDecodeError as e:
                self.logger.error("Invalid JSON in config file", error=str(e))
            except Exception as e:
                self.logger.error("Error reloading config", error=str(e))


class ConfigReloader:
    """Monitor configuration file and reload on changes."""
    
    def __init__(self, config_path: str, validation_callback: Optional[Callable[[dict[str, Any]], bool]] = None):
        """Initialize config reloader.
        
        Args:
            config_path: Path to configuration file
            validation_callback: Optional function to validate config before applying
        """
        self.config_path = Path(config_path)
        self.validation_callback = validation_callback
        self.logger = logger.bind(component="ConfigReloader")
        
        self.current_config: dict[str, Any] = {}
        self.observers: list[Observer] = []
        self.callbacks: list[Callable[[dict[str, Any]], None]] = []
        self.lock = Lock()
        
        # Load initial config
        self._load_config()
        
        self.logger.info("Config reloader initialized", config_path=str(self.config_path))
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            with open(self.config_path, 'r') as f:
                self.current_config = json.load(f)
            self.logger.info("Config loaded", entries=len(self.current_config))
        except FileNotFoundError:
            self.logger.warning("Config file not found, using defaults", path=str(self.config_path))
            self.current_config = self._get_default_config()
        except json.JSONDecodeError as e:
            self.logger.error("Invalid JSON in config file", error=str(e))
            self.current_config = self._get_default_config()
    
    def _get_default_config(self) -> dict[str, Any]:
        """Get default configuration."""
        return {
            'monitoring': {
                'enabled': True,
                'interval': 3600,
                'max_workers': 5
            },
            'scraping': {
                'timeout': 30,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'retry_attempts': 3,
                'retry_delay': 5
            },
            'filtering': {
                'min_relevance_score': 0.5,
                'keyword_boost': 1.5,
                'category_boost': 1.2
            },
            'alerting': {
                'email_enabled': False,
                'slack_enabled': False,
                'min_alert_score': 0.7
            },
            'selenium': {
                'enabled': False,
                'headless': True,
                'timeout': 30
            },
            'proxy': {
                'enabled': False,
                'rotation': True,
                'proxies': []
            }
        }
    
    def start_watching(self):
        """Start watching configuration file for changes."""
        if not self.config_path.exists():
            self.logger.warning("Config file does not exist, creating with defaults")
            self._save_config(self.current_config)
        
        # Create observer
        observer = Observer()
        handler = ConfigFileHandler(self.config_path, self._on_config_changed)
        
        # Watch the directory containing the config file
        observer.schedule(handler, str(self.config_path.parent), recursive=False)
        observer.start()
        
        self.observers.append(observer)
        self.logger.info("Started watching config file")
    
    def stop_watching(self):
        """Stop watching configuration file."""
        for observer in self.observers:
            observer.stop()
            observer.join()
        
        self.observers.clear()
        self.logger.info("Stopped watching config file")
    
    def _on_config_changed(self, new_config: dict[str, Any]):
        """Handle configuration change.
        
        Args:
            new_config: New configuration dictionary
        """
        with self.lock:
            # Validate if callback provided
            if self.validation_callback:
                if not self.validation_callback(new_config):
                    self.logger.error("Config validation failed, keeping current config")
                    return
            
            # Store old config for rollback
            old_config = self.current_config.copy()
            
            try:
                # Update current config
                self.current_config = new_config
                
                # Notify all callbacks
                for callback in self.callbacks:
                    try:
                        callback(new_config)
                    except Exception as e:
                        self.logger.error("Error in config callback", error=str(e))
                        # Rollback on error
                        self.current_config = old_config
                        raise
                
                self.logger.info("Config applied successfully", 
                               entries=len(new_config))
                
            except Exception as e:
                self.logger.error("Error applying config", error=str(e))
                self.current_config = old_config
    
    def register_callback(self, callback: Callable[[dict[str, Any]], None]):
        """Register callback for config changes.
        
        Args:
            callback: Function to call when config changes
        """
        self.callbacks.append(callback)
        self.logger.info("Callback registered", total_callbacks=len(self.callbacks))
    
    def get_config(self) -> dict[str, Any]:
        """Get current configuration.
        
        Returns:
            Current configuration dictionary
        """
        with self.lock:
            return self.current_config.copy()
    
    def get_value(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated path.
        
        Args:
            key_path: Dot-separated path (e.g., 'monitoring.interval')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        with self.lock:
            keys = key_path.split('.')
            value = self.current_config
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            
            return value
    
    def update_value(self, key_path: str, value: Any):
        """Update configuration value by dot-separated path.
        
        Args:
            key_path: Dot-separated path (e.g., 'monitoring.interval')
            value: New value
        """
        with self.lock:
            keys = key_path.split('.')
            config = self.current_config
            
            # Navigate to parent
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]
            
            # Set value
            config[keys[-1]] = value
            
            # Save to file
            self._save_config(self.current_config)
            
            self.logger.info("Config value updated", key=key_path, value=value)
    
    def _save_config(self, config: dict[str, Any]):
        """Save configuration to file.
        
        Args:
            config: Configuration dictionary
        """
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            self.logger.error("Error saving config", error=str(e))
    
    def reload_now(self):
        """Force reload configuration immediately."""
        self.logger.info("Forcing config reload")
        self._load_config()
        
        # Notify callbacks
        for callback in self.callbacks:
            try:
                callback(self.current_config)
            except Exception as e:
                self.logger.error("Error in config callback", error=str(e))
    
    def validate_config_schema(self, config: dict[str, Any]) -> bool:
        """Validate configuration schema.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            True if valid, False otherwise
        """
        required_sections = ['monitoring', 'scraping', 'filtering', 'alerting']
        
        # Check required sections
        for section in required_sections:
            if section not in config:
                self.logger.error("Missing required section", section=section)
                return False
        
        # Validate monitoring section
        if 'interval' in config['monitoring']:
            if not isinstance(config['monitoring']['interval'], int) or config['monitoring']['interval'] < 60:
                self.logger.error("Invalid monitoring interval")
                return False
        
        # Validate scraping section
        if 'timeout' in config['scraping']:
            if not isinstance(config['scraping']['timeout'], int) or config['scraping']['timeout'] < 1:
                self.logger.error("Invalid scraping timeout")
                return False
        
        # Validate filtering section
        if 'min_relevance_score' in config['filtering']:
            score = config['filtering']['min_relevance_score']
            if not isinstance(score, (int, float)) or score < 0 or score > 1:
                self.logger.error("Invalid min_relevance_score")
                return False
        
        return True
    
    def __enter__(self):
        """Context manager entry."""
        self.start_watching()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_watching()
