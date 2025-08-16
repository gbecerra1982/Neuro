"""
Base Plugin - Abstract base class for all avatar plugins
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class BasePlugin(ABC):
    """
    Abstract base class for all avatar plugins.
    Plugins extend avatar functionality with custom processing capabilities.
    """
    
    def __init__(self):
        """Initialize base plugin"""
        self.name = self.__class__.__name__
        self.config = {}
        self.enabled = True
        self.priority = 50  # Default priority (0-100, higher = earlier execution)
        self.metadata = {
            'version': '1.0.0',
            'author': 'Unknown',
            'description': 'Base plugin'
        }
    
    @abstractmethod
    def initialize(self, config: Dict) -> bool:
        """
        Initialize the plugin with configuration.
        
        Args:
            config: Plugin configuration dictionary
            
        Returns:
            True if initialization successful
        """
        pass
    
    @abstractmethod
    async def process(self, input_data: Dict) -> Optional[Dict]:
        """
        Process input data and return response.
        
        Args:
            input_data: Input data dictionary with 'type' and 'content'
            
        Returns:
            Response dictionary or None if plugin doesn't handle this input
        """
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Clean up plugin resources"""
        pass
    
    def validate_config(self, config: Dict) -> List[str]:
        """
        Validate plugin configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Default validation - override in subclasses
        required_fields = self.get_required_config_fields()
        for field in required_fields:
            if field not in config:
                errors.append(f"Required field '{field}' missing in {self.name} configuration")
        
        return errors
    
    def get_required_config_fields(self) -> List[str]:
        """
        Get list of required configuration fields.
        Override in subclasses to specify requirements.
        
        Returns:
            List of required field names
        """
        return []
    
    def set_enabled(self, enabled: bool):
        """
        Enable or disable the plugin.
        
        Args:
            enabled: True to enable, False to disable
        """
        self.enabled = enabled
        logger.info(f"Plugin {self.name} {'enabled' if enabled else 'disabled'}")
    
    def get_status(self) -> Dict:
        """
        Get plugin status.
        
        Returns:
            Status dictionary
        """
        return {
            'name': self.name,
            'enabled': self.enabled,
            'priority': self.priority,
            'metadata': self.metadata,
            'config': self._get_safe_config()
        }
    
    def _get_safe_config(self) -> Dict:
        """Get configuration with sensitive values masked"""
        safe_config = {}
        sensitive_keys = ['api_key', 'key', 'password', 'secret', 'token']
        
        for key, value in self.config.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                safe_config[key] = '***MASKED***'
            elif isinstance(value, dict):
                safe_config[key] = self._mask_sensitive_dict(value)
            else:
                safe_config[key] = value
        
        return safe_config
    
    def _mask_sensitive_dict(self, d: Dict) -> Dict:
        """Recursively mask sensitive values in dictionary"""
        masked = {}
        sensitive_keys = ['api_key', 'key', 'password', 'secret', 'token']
        
        for key, value in d.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                masked[key] = '***MASKED***'
            elif isinstance(value, dict):
                masked[key] = self._mask_sensitive_dict(value)
            else:
                masked[key] = value
        
        return masked
    
    def handle_error(self, error: Exception, context: str = "") -> Dict:
        """
        Handle plugin errors consistently.
        
        Args:
            error: Exception that occurred
            context: Additional context about the error
            
        Returns:
            Error response dictionary
        """
        error_msg = f"Plugin {self.name} error"
        if context:
            error_msg += f" ({context})"
        error_msg += f": {str(error)}"
        
        logger.error(error_msg)
        
        return {
            'error': True,
            'error_message': str(error),
            'plugin': self.name,
            'context': context
        }
    
    async def pre_process(self, input_data: Dict) -> Dict:
        """
        Pre-process input before main processing.
        Override in subclasses for custom pre-processing.
        
        Args:
            input_data: Input data
            
        Returns:
            Pre-processed input data
        """
        return input_data
    
    async def post_process(self, response: Dict) -> Dict:
        """
        Post-process response after main processing.
        Override in subclasses for custom post-processing.
        
        Args:
            response: Response data
            
        Returns:
            Post-processed response
        """
        return response
    
    def supports_streaming(self) -> bool:
        """
        Check if plugin supports streaming responses.
        
        Returns:
            True if streaming is supported
        """
        return False
    
    async def process_stream(self, input_data: Dict):
        """
        Process input with streaming response.
        Override in subclasses that support streaming.
        
        Args:
            input_data: Input data
            
        Yields:
            Response chunks
        """
        yield {
            'error': True,
            'error_message': f"Plugin {self.name} does not support streaming"
        }
