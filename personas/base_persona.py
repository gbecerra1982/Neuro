"""
Base Persona - Base class for avatar personas
"""

import yaml
import json
from typing import Dict, List, Optional, Any
from pathlib import Path


class BasePersona:
    """
    Base class for avatar personas.
    Defines personality, voice, appearance, and behavior.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize persona.
        
        Args:
            config: Optional persona configuration
        """
        self.config = config or self._get_default_config()
        
        # Extract main attributes
        self.name = self.config.get('name', 'Default Avatar')
        self.role = self.config.get('role', 'Assistant')
        self.voice = self.config.get('voice', {})
        self.avatar = self.config.get('avatar', {})
        self.personality = self.config.get('personality', {})
        self.system_prompt = self.config.get('system_prompt', '')
        self.knowledge_domains = self.config.get('knowledge_domains', [])
        self.tools = self.config.get('tools', [])
        self.conversation_style = self.config.get('conversation_style', {})
        
    @classmethod
    def from_file(cls, file_path: str) -> 'BasePersona':
        """
        Load persona from configuration file.
        
        Args:
            file_path: Path to persona configuration file
            
        Returns:
            BasePersona instance
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Persona file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            if file_path.suffix in ['.yaml', '.yml']:
                config = yaml.safe_load(f)
            elif file_path.suffix == '.json':
                config = json.load(f)
            else:
                raise ValueError(f"Unsupported persona file format: {file_path.suffix}")
        
        return cls(config)
    
    @classmethod
    def from_template(cls, template_name: str) -> 'BasePersona':
        """
        Load persona from a template.
        
        Args:
            template_name: Name of the template
            
        Returns:
            BasePersona instance
        """
        template_path = Path(f"personas/templates/{template_name}.yaml")
        
        if not template_path.exists():
            # Try without .yaml extension
            template_path = Path(f"personas/templates/{template_name}")
            if not template_path.exists():
                raise ValueError(f"Template not found: {template_name}")
        
        return cls.from_file(str(template_path))
    
    def _get_default_config(self) -> Dict:
        """Get default persona configuration"""
        return {
            'name': 'Default Avatar',
            'role': 'AI Assistant',
            'voice': {
                'language': 'en-US',
                'model': 'en-US-JennyNeural',
                'pitch': '0Hz',
                'rate': 1.0,
                'volume': 1.0
            },
            'avatar': {
                'character': 'lisa',
                'style': 'casual-sitting',
                'background_color': '#FFFFFF',
                'video_quality': 'high'
            },
            'personality': {
                'traits': ['helpful', 'friendly', 'professional'],
                'tone': 'conversational',
                'formality': 'moderate'
            },
            'system_prompt': 'You are a helpful AI assistant.',
            'knowledge_domains': [],
            'tools': [],
            'conversation_style': {
                'greeting': 'Hello! How can I help you today?',
                'farewell': 'Thank you for chatting with me. Have a great day!',
                'acknowledgment': 'I understand.',
                'thinking': 'Let me think about that...',
                'error': 'I apologize, but I encountered an issue.'
            }
        }
    
    def get_system_prompt(self) -> str:
        """
        Get the complete system prompt for the persona.
        
        Returns:
            System prompt string
        """
        prompt_parts = [self.system_prompt]
        
        # Add role information
        if self.role:
            prompt_parts.append(f"Your role is: {self.role}")
        
        # Add personality traits
        if self.personality.get('traits'):
            traits = ', '.join(self.personality['traits'])
            prompt_parts.append(f"Your personality traits are: {traits}")
        
        # Add conversation style
        if self.conversation_style:
            style = self.personality.get('tone', 'conversational')
            prompt_parts.append(f"Maintain a {style} tone in your responses.")
        
        # Add knowledge domains
        if self.knowledge_domains:
            domains = ', '.join(self.knowledge_domains)
            prompt_parts.append(f"You have expertise in: {domains}")
        
        # Add available tools
        if self.tools:
            tools = ', '.join(self.tools)
            prompt_parts.append(f"You have access to these tools: {tools}")
        
        return '\n\n'.join(prompt_parts)
    
    def get_voice_config(self) -> Dict:
        """Get voice configuration"""
        return self.voice
    
    def get_avatar_config(self) -> Dict:
        """Get avatar visual configuration"""
        return self.avatar
    
    def get_greeting(self) -> str:
        """Get greeting message"""
        return self.conversation_style.get('greeting', 'Hello!')
    
    def get_farewell(self) -> str:
        """Get farewell message"""
        return self.conversation_style.get('farewell', 'Goodbye!')
    
    def update_config(self, updates: Dict):
        """
        Update persona configuration.
        
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
        
        # Update attributes
        self.name = self.config.get('name', self.name)
        self.role = self.config.get('role', self.role)
        self.voice = self.config.get('voice', self.voice)
        self.avatar = self.config.get('avatar', self.avatar)
        self.personality = self.config.get('personality', self.personality)
        self.system_prompt = self.config.get('system_prompt', self.system_prompt)
        self.knowledge_domains = self.config.get('knowledge_domains', self.knowledge_domains)
        self.tools = self.config.get('tools', self.tools)
        self.conversation_style = self.config.get('conversation_style', self.conversation_style)
    
    def to_dict(self) -> Dict:
        """Export persona as dictionary"""
        return self.config.copy()
    
    def to_yaml(self, file_path: Optional[str] = None) -> str:
        """
        Export persona as YAML.
        
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
        Export persona as JSON.
        
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
    
    def validate(self) -> List[str]:
        """
        Validate persona configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required fields
        if not self.name:
            errors.append("Persona name is required")
        
        if not self.system_prompt:
            errors.append("System prompt is required")
        
        # Validate voice configuration
        if self.voice:
            if not self.voice.get('language'):
                errors.append("Voice language is required")
            if not self.voice.get('model'):
                errors.append("Voice model is required")
        
        # Validate avatar configuration
        if self.avatar:
            if not self.avatar.get('character'):
                errors.append("Avatar character is required")
            if not self.avatar.get('style'):
                errors.append("Avatar style is required")
        
        return errors
    
    def get_metadata(self) -> Dict:
        """Get persona metadata"""
        return {
            'name': self.name,
            'role': self.role,
            'language': self.voice.get('language', 'en-US'),
            'avatar_character': self.avatar.get('character', 'lisa'),
            'knowledge_domains': len(self.knowledge_domains),
            'tools': len(self.tools),
            'personality_traits': self.personality.get('traits', [])
        }
