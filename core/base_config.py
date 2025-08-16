"""
Base Configuration - Configuration management for avatar instances
"""

import os
import yaml
import json
from typing import Dict, Any, Optional, List
from pathlib import Path


class BaseConfig:
    """
    Base configuration class for avatar instances.
    Handles configuration loading, validation, and environment variable resolution.
    """
    
    def __init__(self, config_data: Optional[Dict] = None):
        """
        Initialize configuration.
        
        Args:
            config_data: Optional configuration dictionary
        """
        self.config = config_data or {}
        self._env_cache = {}
        
    @classmethod
    def from_file(cls, config_path: str) -> 'BaseConfig':
        """
        Load configuration from a file.
        
        Args:
            config_path: Path to configuration file (YAML or JSON)
            
        Returns:
            BaseConfig instance
        """
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            if config_path.suffix in ['.yaml', '.yml']:
                config_data = yaml.safe_load(f)
            elif config_path.suffix == '.json':
                config_data = json.load(f)
            else:
                raise ValueError(f"Unsupported config file format: {config_path.suffix}")
        
        instance = cls(config_data)
        instance.resolve_environment_variables()
        return instance
    
    def resolve_environment_variables(self):
        """Resolve environment variable placeholders in configuration"""
        self.config = self._resolve_env_recursive(self.config)
    
    def _resolve_env_recursive(self, obj: Any) -> Any:
        """
        Recursively resolve environment variables in configuration object.
        
        Args:
            obj: Configuration object (dict, list, or value)
            
        Returns:
            Object with resolved environment variables
        """
        if isinstance(obj, dict):
            return {k: self._resolve_env_recursive(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._resolve_env_recursive(item) for item in obj]
        elif isinstance(obj, str):
            # Check for environment variable pattern ${VAR_NAME}
            if obj.startswith('${') and obj.endswith('}'):
                var_name = obj[2:-1]
                
                # Check cache first
                if var_name in self._env_cache:
                    return self._env_cache[var_name]
                
                # Get from environment with optional default
                if ':' in var_name:
                    var_name, default = var_name.split(':', 1)
                    value = os.environ.get(var_name, default)
                else:
                    value = os.environ.get(var_name, obj)
                
                self._env_cache[var_name] = value
                return value
            # Check for partial environment variables in string
            elif '${' in obj:
                import re
                pattern = r'\$\{([^}]+)\}'
                
                def replacer(match):
                    var_name = match.group(1)
                    if ':' in var_name:
                        var_name, default = var_name.split(':', 1)
                        return os.environ.get(var_name, default)
                    return os.environ.get(var_name, match.group(0))
                
                return re.sub(pattern, replacer, obj)
        
        return obj
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key (supports nested keys with dot notation).
        
        Args:
            key: Configuration key (e.g., 'azure.openai.endpoint')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        Set configuration value by key (supports nested keys with dot notation).
        
        Args:
            key: Configuration key (e.g., 'azure.openai.endpoint')
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def update(self, updates: Dict):
        """
        Update configuration with new values.
        
        Args:
            updates: Dictionary of updates to apply
        """
        def deep_update(base: dict, updates: dict):
            for key, value in updates.items():
                if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                    deep_update(base[key], value)
                else:
                    base[key] = value
        
        deep_update(self.config, updates)
    
    def validate(self, schema: Optional[Dict] = None) -> List[str]:
        """
        Validate configuration against a schema.
        
        Args:
            schema: Optional validation schema
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Basic validation - check required fields
        required_fields = [
            'instance.name',
            'azure.openai.endpoint',
            'azure.openai.api_key'
        ]
        
        for field in required_fields:
            if not self.get(field):
                errors.append(f"Required field missing: {field}")
        
        # Validate Azure configuration
        if self.get('azure'):
            errors.extend(self._validate_azure_config())
        
        # Validate plugins
        if self.get('plugins'):
            errors.extend(self._validate_plugins_config())
        
        return errors
    
    def _validate_azure_config(self) -> List[str]:
        """Validate Azure-specific configuration"""
        errors = []
        
        # Check OpenAI configuration
        openai_config = self.get('azure.openai', {})
        if openai_config:
            if not openai_config.get('endpoint'):
                errors.append("Azure OpenAI endpoint is required")
            elif not openai_config['endpoint'].startswith('http'):
                errors.append("Azure OpenAI endpoint must be a valid URL")
        
        # Check Speech configuration
        speech_config = self.get('azure.speech', {})
        if speech_config:
            if not speech_config.get('key'):
                errors.append("Azure Speech key is required when speech is configured")
            if not speech_config.get('region'):
                errors.append("Azure Speech region is required when speech is configured")
        
        return errors
    
    def _validate_plugins_config(self) -> List[str]:
        """Validate plugins configuration"""
        errors = []
        
        plugins = self.get('plugins', [])
        for i, plugin in enumerate(plugins):
            if isinstance(plugin, dict):
                if not plugin.get('name'):
                    errors.append(f"Plugin {i} missing required 'name' field")
            elif not isinstance(plugin, str):
                errors.append(f"Plugin {i} must be a string or dictionary")
        
        return errors
    
    def to_dict(self) -> Dict:
        """
        Export configuration as dictionary.
        
        Returns:
            Configuration dictionary
        """
        return self.config.copy()
    
    def to_yaml(self, file_path: Optional[str] = None) -> str:
        """
        Export configuration as YAML.
        
        Args:
            file_path: Optional file path to save YAML
            
        Returns:
            YAML string
        """
        yaml_str = yaml.dump(self.config, default_flow_style=False, sort_keys=False)
        
        if file_path:
            with open(file_path, 'w') as f:
                f.write(yaml_str)
        
        return yaml_str
    
    def to_json(self, file_path: Optional[str] = None) -> str:
        """
        Export configuration as JSON.
        
        Args:
            file_path: Optional file path to save JSON
            
        Returns:
            JSON string
        """
        json_str = json.dumps(self.config, indent=2)
        
        if file_path:
            with open(file_path, 'w') as f:
                f.write(json_str)
        
        return json_str
    
    def merge(self, other: 'BaseConfig'):
        """
        Merge another configuration into this one.
        
        Args:
            other: Another BaseConfig instance to merge
        """
        self.update(other.to_dict())
    
    def get_azure_config(self) -> Dict:
        """Get Azure-specific configuration"""
        return self.get('azure', {})
    
    def get_plugin_config(self, plugin_name: str) -> Optional[Dict]:
        """
        Get configuration for a specific plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Plugin configuration or None
        """
        plugins = self.get('plugins', [])
        
        for plugin in plugins:
            if isinstance(plugin, dict) and plugin.get('name') == plugin_name:
                return plugin.get('config', {})
            elif isinstance(plugin, str) and plugin == plugin_name:
                return {}
        
        return None
    
    def get_ui_config(self) -> Dict:
        """Get UI configuration"""
        return self.get('ui', {
            'template': 'base/avatar_interface.html',
            'theme': 'default'
        })
