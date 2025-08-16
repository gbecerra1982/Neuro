"""
Avatar Engine - Core orchestrator for avatar instances
"""

import os
import json
import yaml
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from abc import ABC
import importlib.util

from .realtime_proxy import RealtimeProxy
from .speech_handler import SpeechHandler
from .base_config import BaseConfig

logger = logging.getLogger(__name__)


class AvatarEngine:
    """
    Main engine that orchestrates all avatar components.
    This is the core of the Avatar Factory system.
    """
    
    def __init__(self, instance_name: str, config_path: Optional[str] = None):
        """
        Initialize the Avatar Engine with an instance configuration.
        
        Args:
            instance_name: Name of the avatar instance
            config_path: Optional path to configuration file
        """
        self.instance_name = instance_name
        self.config_path = config_path or f"instances/{instance_name}/config.yaml"
        
        # Core components
        self.config: Optional[BaseConfig] = None
        self.realtime_proxy: Optional[RealtimeProxy] = None
        self.speech_handler: Optional[SpeechHandler] = None
        
        # Plugin system
        self.plugins: Dict[str, Any] = {}
        self.tools: Dict[str, Any] = {}
        
        # Persona and state
        self.persona: Optional[Dict] = None
        self.session_state: Dict = {
            'active': False,
            'session_id': None,
            'start_time': None,
            'messages': [],
            'metrics': {}
        }
        
        # Initialize
        self._initialized = False
        
    def load_config(self) -> BaseConfig:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Load environment variables for placeholders
            config_data = self._resolve_env_vars(config_data)
            
            self.config = BaseConfig(config_data)
            logger.info(f"Configuration loaded for instance: {self.instance_name}")
            return self.config
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _resolve_env_vars(self, config: Any) -> Any:
        """Recursively resolve environment variable placeholders in config"""
        if isinstance(config, dict):
            return {k: self._resolve_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._resolve_env_vars(item) for item in config]
        elif isinstance(config, str) and config.startswith('${') and config.endswith('}'):
            env_var = config[2:-1]
            return os.environ.get(env_var, config)
        return config
    
    def load_persona(self, persona_path: Optional[str] = None) -> Dict:
        """Load persona configuration"""
        if not persona_path:
            persona_path = f"instances/{self.instance_name}/persona.yaml"
        
        try:
            with open(persona_path, 'r') as f:
                self.persona = yaml.safe_load(f)
            
            logger.info(f"Persona loaded: {self.persona.get('name', 'Unknown')}")
            return self.persona
            
        except Exception as e:
            logger.error(f"Failed to load persona: {e}")
            # Use default persona if specific one fails
            self.persona = self._get_default_persona()
            return self.persona
    
    def _get_default_persona(self) -> Dict:
        """Return a default persona configuration"""
        return {
            'name': 'Default Assistant',
            'voice': {
                'language': 'en-US',
                'model': 'en-US-JennyNeural',
                'pitch': '0Hz',
                'rate': 1.0
            },
            'avatar': {
                'character': 'lisa',
                'style': 'casual-sitting',
                'background_color': '#FFFFFF'
            },
            'personality': {
                'role': 'Helpful Assistant',
                'traits': ['helpful', 'friendly', 'professional']
            },
            'system_prompt': 'You are a helpful AI assistant.'
        }
    
    def load_plugins(self, plugin_list: Optional[List[str]] = None):
        """
        Load plugins specified in configuration or provided list.
        
        Args:
            plugin_list: Optional list of plugin names to load
        """
        if not plugin_list and self.config:
            plugin_list = self.config.get('plugins', [])
        
        for plugin_config in plugin_list:
            plugin_name = plugin_config.get('name') if isinstance(plugin_config, dict) else plugin_config
            try:
                self._load_plugin(plugin_name, plugin_config)
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_name}: {e}")
    
    def _load_plugin(self, plugin_name: str, plugin_config: Any):
        """Load a single plugin"""
        # Try to load from plugins directory
        plugin_path = f"plugins/{plugin_name}.py"
        
        if not os.path.exists(plugin_path):
            # Try instance-specific plugins
            plugin_path = f"instances/{self.instance_name}/tools/{plugin_name}.py"
        
        if os.path.exists(plugin_path):
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Get the plugin class (assuming it follows naming convention)
            plugin_class_name = ''.join(word.capitalize() for word in plugin_name.split('_'))
            if hasattr(module, plugin_class_name):
                plugin_class = getattr(module, plugin_class_name)
                config = plugin_config.get('config', {}) if isinstance(plugin_config, dict) else {}
                self.plugins[plugin_name] = plugin_class()
                self.plugins[plugin_name].initialize(config)
                logger.info(f"Plugin loaded: {plugin_name}")
    
    def register_tool(self, tool_name: str, tool_function):
        """Register a tool function that can be called by the avatar"""
        self.tools[tool_name] = tool_function
        logger.info(f"Tool registered: {tool_name}")
    
    async def initialize(self):
        """Initialize all components of the avatar engine"""
        try:
            # Load configurations
            if not self.config:
                self.load_config()
            
            if not self.persona:
                self.load_persona()
            
            # Initialize core components
            if self.config.get('azure', {}).get('openai'):
                self.realtime_proxy = RealtimeProxy(self.config.get('azure'))
                await self.realtime_proxy.initialize()
            
            if self.config.get('azure', {}).get('speech'):
                self.speech_handler = SpeechHandler(self.config.get('azure'))
                await self.speech_handler.initialize()
            
            # Load plugins
            self.load_plugins()
            
            self._initialized = True
            logger.info(f"Avatar engine initialized for instance: {self.instance_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize avatar engine: {e}")
            raise
    
    async def start_session(self, session_id: str = None) -> Dict:
        """Start a new avatar session"""
        if not self._initialized:
            await self.initialize()
        
        session_id = session_id or datetime.now().isoformat()
        
        self.session_state = {
            'active': True,
            'session_id': session_id,
            'start_time': datetime.now(),
            'messages': [],
            'metrics': {
                'messages_sent': 0,
                'messages_received': 0,
                'tokens_used': 0
            }
        }
        
        # Start components
        if self.realtime_proxy:
            await self.realtime_proxy.connect()
        
        if self.speech_handler:
            await self.speech_handler.start_avatar(self.persona.get('avatar', {}))
        
        logger.info(f"Session started: {session_id}")
        return {'session_id': session_id, 'status': 'active'}
    
    async def process_message(self, message: Dict) -> Dict:
        """
        Process an incoming message through the avatar pipeline.
        
        Args:
            message: Message dictionary with type and content
            
        Returns:
            Response dictionary
        """
        if not self.session_state['active']:
            return {'error': 'No active session'}
        
        message_type = message.get('type', 'text')
        content = message.get('content', '')
        
        # Add to conversation history
        self.session_state['messages'].append({
            'role': 'user',
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        
        # Process through plugins
        response = await self._process_through_plugins(message)
        
        # Generate avatar response
        if response:
            self.session_state['messages'].append({
                'role': 'assistant',
                'content': response.get('content', ''),
                'timestamp': datetime.now().isoformat()
            })
            
            # Make avatar speak if speech handler is available
            if self.speech_handler and response.get('speak', True):
                await self.speech_handler.speak(response['content'])
        
        # Update metrics
        self.session_state['metrics']['messages_received'] += 1
        self.session_state['metrics']['messages_sent'] += 1
        
        return response
    
    async def _process_through_plugins(self, message: Dict) -> Dict:
        """Process message through registered plugins"""
        response = {'content': '', 'metadata': {}}
        
        # Process through each plugin in order
        for plugin_name, plugin in self.plugins.items():
            try:
                if hasattr(plugin, 'process'):
                    plugin_response = await plugin.process(message)
                    if plugin_response:
                        # Merge responses
                        if plugin_response.get('content'):
                            response['content'] = plugin_response['content']
                        if plugin_response.get('metadata'):
                            response['metadata'].update(plugin_response['metadata'])
                        
                        # If plugin marks as final, stop processing
                        if plugin_response.get('final', False):
                            break
                            
            except Exception as e:
                logger.error(f"Plugin {plugin_name} processing error: {e}")
        
        return response
    
    async def stop_session(self) -> Dict:
        """Stop the current avatar session"""
        if not self.session_state['active']:
            return {'error': 'No active session'}
        
        session_id = self.session_state['session_id']
        
        # Stop components
        if self.realtime_proxy:
            await self.realtime_proxy.disconnect()
        
        if self.speech_handler:
            await self.speech_handler.stop_avatar()
        
        # Clean up plugins
        for plugin_name, plugin in self.plugins.items():
            if hasattr(plugin, 'cleanup'):
                try:
                    await plugin.cleanup()
                except Exception as e:
                    logger.error(f"Plugin {plugin_name} cleanup error: {e}")
        
        # Calculate session duration
        duration = (datetime.now() - self.session_state['start_time']).total_seconds()
        
        # Final metrics
        final_metrics = {
            **self.session_state['metrics'],
            'session_duration': duration
        }
        
        self.session_state['active'] = False
        
        logger.info(f"Session stopped: {session_id}")
        return {
            'session_id': session_id,
            'status': 'stopped',
            'metrics': final_metrics
        }
    
    def get_status(self) -> Dict:
        """Get current status of the avatar engine"""
        return {
            'instance': self.instance_name,
            'initialized': self._initialized,
            'session': {
                'active': self.session_state['active'],
                'session_id': self.session_state.get('session_id'),
                'duration': (
                    (datetime.now() - self.session_state['start_time']).total_seconds()
                    if self.session_state.get('start_time') else 0
                )
            },
            'components': {
                'realtime_proxy': bool(self.realtime_proxy),
                'speech_handler': bool(self.speech_handler),
                'plugins': list(self.plugins.keys())
            },
            'metrics': self.session_state.get('metrics', {})
        }
    
    def get_conversation_history(self) -> List[Dict]:
        """Get the conversation history for the current session"""
        return self.session_state.get('messages', [])
    
    async def execute_tool(self, tool_name: str, parameters: Dict) -> Any:
        """Execute a registered tool"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found")
        
        tool_function = self.tools[tool_name]
        
        # Execute tool (support both sync and async)
        if asyncio.iscoroutinefunction(tool_function):
            return await tool_function(**parameters)
        else:
            return tool_function(**parameters)
