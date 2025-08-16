"""
Config Loader - Configuration loading utilities
"""

import os
import yaml
import json
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigLoader:
    """
    Utility class for loading and managing configurations.
    """
    
    @staticmethod
    def load_config(file_path: str) -> Dict:
        """
        Load configuration from file.
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            if file_path.suffix in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            elif file_path.suffix == '.json':
                return json.load(f)
            else:
                raise ValueError(f"Unsupported configuration format: {file_path.suffix}")
    
    @staticmethod
    def save_config(config: Dict, file_path: str):
        """
        Save configuration to file.
        
        Args:
            config: Configuration dictionary
            file_path: Path to save configuration
        """
        file_path = Path(file_path)
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w') as f:
            if file_path.suffix in ['.yaml', '.yml']:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            elif file_path.suffix == '.json':
                json.dump(config, f, indent=2)
            else:
                raise ValueError(f"Unsupported configuration format: {file_path.suffix}")
    
    @staticmethod
    def load_template(template_name: str) -> Dict:
        """
        Load a configuration template.
        
        Args:
            template_name: Name of the template
            
        Returns:
            Template configuration dictionary
        """
        # Look for template in multiple locations
        template_paths = [
            f"templates/{template_name}.yaml",
            f"templates/{template_name}.yml",
            f"templates/{template_name}.json",
            f"config/templates/{template_name}.yaml",
            f"config/templates/{template_name}.yml",
            f"config/templates/{template_name}.json"
        ]
        
        for path in template_paths:
            if os.path.exists(path):
                return ConfigLoader.load_config(path)
        
        # If not found, create a basic template
        return ConfigLoader.get_default_template(template_name)
    
    @staticmethod
    def get_default_template(template_type: str = "basic") -> Dict:
        """
        Get a default configuration template.
        
        Args:
            template_type: Type of template
            
        Returns:
            Default template configuration
        """
        templates = {
            "basic": {
                "instance": {
                    "name": "new_avatar",
                    "version": "1.0.0",
                    "environment": "development"
                },
                "azure": {
                    "openai": {
                        "endpoint": "${AZURE_OPENAI_ENDPOINT}",
                        "api_key": "${AZURE_OPENAI_API_KEY}",
                        "deployment": "gpt-4o-realtime-preview",
                        "api_version": "2025-04-01-preview"
                    },
                    "speech": {
                        "key": "${SPEECH_KEY}",
                        "region": "${SPEECH_REGION}",
                        "endpoint": "${SPEECH_ENDPOINT}"
                    }
                },
                "plugins": [
                    {"name": "rag_plugin", "config": {"vector_store_type": "in_memory"}},
                    {"name": "tools_plugin", "config": {"enabled_tools": []}}
                ],
                "ui": {
                    "template": "base/avatar_interface.html",
                    "theme": "default"
                }
            },
            "corporate": {
                "instance": {
                    "name": "corporate_avatar",
                    "version": "1.0.0",
                    "environment": "production"
                },
                "azure": {
                    "openai": {
                        "endpoint": "${AZURE_OPENAI_ENDPOINT}",
                        "api_key": "${AZURE_OPENAI_API_KEY}",
                        "deployment": "gpt-4o-realtime-preview",
                        "api_version": "2025-04-01-preview"
                    },
                    "speech": {
                        "key": "${SPEECH_KEY}",
                        "region": "${SPEECH_REGION}",
                        "endpoint": "${SPEECH_ENDPOINT}"
                    },
                    "cognitive_search": {
                        "endpoint": "${COGNITIVE_SEARCH_ENDPOINT}",
                        "api_key": "${COGNITIVE_SEARCH_API_KEY}",
                        "index": "corporate-knowledge"
                    }
                },
                "plugins": [
                    {
                        "name": "rag_plugin",
                        "config": {
                            "vector_store_type": "azure_search",
                            "embedding_model": "text-embedding-3-large"
                        }
                    },
                    {
                        "name": "sql_plugin",
                        "config": {
                            "database": "postgresql",
                            "read_only": true
                        }
                    },
                    {
                        "name": "tools_plugin",
                        "config": {
                            "enabled_tools": ["calendar", "email", "documents"]
                        }
                    }
                ],
                "ui": {
                    "template": "corporate/avatar_interface.html",
                    "theme": "professional",
                    "branding": {
                        "logo": "static/images/company_logo.png",
                        "colors": {
                            "primary": "#1E40AF",
                            "secondary": "#3B82F6"
                        }
                    }
                }
            },
            "technical": {
                "instance": {
                    "name": "tech_support_avatar",
                    "version": "1.0.0",
                    "environment": "production"
                },
                "azure": {
                    "openai": {
                        "endpoint": "${AZURE_OPENAI_ENDPOINT}",
                        "api_key": "${AZURE_OPENAI_API_KEY}",
                        "deployment": "gpt-4o-realtime-preview",
                        "api_version": "2025-04-01-preview"
                    },
                    "speech": {
                        "key": "${SPEECH_KEY}",
                        "region": "${SPEECH_REGION}",
                        "endpoint": "${SPEECH_ENDPOINT}"
                    }
                },
                "plugins": [
                    {
                        "name": "rag_plugin",
                        "config": {
                            "vector_store_type": "in_memory",
                            "knowledge_base_path": "knowledge_base/technical"
                        }
                    },
                    {
                        "name": "sql_plugin",
                        "config": {
                            "database": "sqlite",
                            "database_path": "data/tickets.db",
                            "read_only": false
                        }
                    },
                    {
                        "name": "tools_plugin",
                        "config": {
                            "enabled_tools": [
                                "system_diagnostics",
                                "log_analyzer",
                                "ticket_system"
                            ]
                        }
                    }
                ],
                "ui": {
                    "template": "technical/support_interface.html",
                    "theme": "dark",
                    "features": {
                        "screen_sharing": true,
                        "file_upload": true,
                        "code_editor": true
                    }
                }
            }
        }
        
        return templates.get(template_type, templates["basic"])
    
    @staticmethod
    def merge_configs(*configs: Dict) -> Dict:
        """
        Merge multiple configuration dictionaries.
        
        Args:
            *configs: Configuration dictionaries to merge
            
        Returns:
            Merged configuration
        """
        result = {}
        
        for config in configs:
            ConfigLoader._deep_merge(result, config)
        
        return result
    
    @staticmethod
    def _deep_merge(base: Dict, update: Dict):
        """
        Deep merge two dictionaries.
        
        Args:
            base: Base dictionary (modified in place)
            update: Dictionary to merge into base
        """
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                ConfigLoader._deep_merge(base[key], value)
            else:
                base[key] = value
    
    @staticmethod
    def resolve_environment_variables(config: Dict) -> Dict:
        """
        Resolve environment variable placeholders in configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Configuration with resolved variables
        """
        import re
        
        def resolve_value(value):
            if isinstance(value, str):
                # Pattern for ${VAR_NAME} or ${VAR_NAME:default}
                pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'
                
                def replacer(match):
                    var_name = match.group(1)
                    default = match.group(2) if match.group(2) else match.group(0)
                    return os.environ.get(var_name, default)
                
                return re.sub(pattern, replacer, value)
            elif isinstance(value, dict):
                return {k: resolve_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [resolve_value(item) for item in value]
            return value
        
        return resolve_value(config)
    
    @staticmethod
    def validate_config(config: Dict, schema: Optional[Dict] = None) -> List[str]:
        """
        Validate configuration against a schema.
        
        Args:
            config: Configuration to validate
            schema: Optional validation schema
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Basic validation
        if not config.get('instance'):
            errors.append("Missing 'instance' section")
        elif not config['instance'].get('name'):
            errors.append("Missing instance name")
        
        if not config.get('azure'):
            errors.append("Missing 'azure' section")
        else:
            azure = config['azure']
            if not azure.get('openai'):
                errors.append("Missing Azure OpenAI configuration")
            elif not azure['openai'].get('endpoint') or not azure['openai'].get('api_key'):
                errors.append("Missing Azure OpenAI endpoint or API key")
        
        # Validate plugins
        if config.get('plugins'):
            for i, plugin in enumerate(config['plugins']):
                if isinstance(plugin, dict):
                    if not plugin.get('name'):
                        errors.append(f"Plugin {i} missing name")
                elif not isinstance(plugin, str):
                    errors.append(f"Plugin {i} must be string or dictionary")
        
        return errors
