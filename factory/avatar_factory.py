"""
Avatar Factory - Main factory for creating avatar instances
"""

import os
import logging
from typing import Optional, Dict, List
from pathlib import Path

from core.avatar_engine import AvatarEngine
from core.base_config import BaseConfig
from personas.base_persona import BasePersona
from .config_loader import ConfigLoader
from .instance_manager import InstanceManager

logger = logging.getLogger(__name__)


class AvatarFactory:
    """
    Factory class for creating and managing avatar instances.
    """
    
    @staticmethod
    def create_avatar(instance_name: str, config_path: Optional[str] = None) -> AvatarEngine:
        """
        Create an avatar instance from configuration.
        
        Args:
            instance_name: Name of the avatar instance
            config_path: Optional path to configuration file
            
        Returns:
            Configured AvatarEngine instance
        """
        try:
            # Determine configuration path
            if not config_path:
                config_path = f"instances/{instance_name}/config.yaml"
            
            # Check if instance exists
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Instance configuration not found: {config_path}")
            
            logger.info(f"Creating avatar instance: {instance_name}")
            
            # Create avatar engine
            avatar = AvatarEngine(instance_name, config_path)
            
            # Load configuration
            avatar.load_config()
            
            # Load persona
            persona_path = f"instances/{instance_name}/persona.yaml"
            if os.path.exists(persona_path):
                avatar.load_persona(persona_path)
            else:
                logger.warning(f"No persona found for {instance_name}, using default")
                avatar.load_persona()
            
            # Load plugins from configuration
            avatar.load_plugins()
            
            # Load instance-specific tools
            AvatarFactory._load_instance_tools(avatar, instance_name)
            
            # Load knowledge base if exists
            kb_path = f"instances/{instance_name}/knowledge_base"
            if os.path.exists(kb_path):
                AvatarFactory._load_knowledge_base(avatar, kb_path)
            
            logger.info(f"Avatar instance created successfully: {instance_name}")
            return avatar
            
        except Exception as e:
            logger.error(f"Failed to create avatar instance {instance_name}: {e}")
            raise
    
    @staticmethod
    def create_from_template(
        instance_name: str,
        template_name: str,
        config_overrides: Optional[Dict] = None
    ) -> AvatarEngine:
        """
        Create an avatar instance from a template.
        
        Args:
            instance_name: Name for the new instance
            template_name: Name of the template to use
            config_overrides: Optional configuration overrides
            
        Returns:
            Configured AvatarEngine instance
        """
        try:
            logger.info(f"Creating avatar {instance_name} from template {template_name}")
            
            # Create instance directory
            instance_path = Path(f"instances/{instance_name}")
            instance_path.mkdir(parents=True, exist_ok=True)
            
            # Load template configuration
            template_config = ConfigLoader.load_template(template_name)
            
            # Apply overrides
            if config_overrides:
                template_config.update(config_overrides)
            
            # Set instance name
            template_config['instance'] = {
                'name': instance_name,
                'template': template_name,
                'version': '1.0.0'
            }
            
            # Save configuration
            config_path = instance_path / "config.yaml"
            BaseConfig(template_config).to_yaml(str(config_path))
            
            # Copy persona template
            persona_template = Path(f"personas/templates/{template_name}.yaml")
            if persona_template.exists():
                import shutil
                shutil.copy(persona_template, instance_path / "persona.yaml")
            
            # Create required directories
            (instance_path / "tools").mkdir(exist_ok=True)
            (instance_path / "knowledge_base").mkdir(exist_ok=True)
            
            # Create avatar
            return AvatarFactory.create_avatar(instance_name, str(config_path))
            
        except Exception as e:
            logger.error(f"Failed to create avatar from template: {e}")
            raise
    
    @staticmethod
    def list_instances() -> List[str]:
        """
        List all available avatar instances.
        
        Returns:
            List of instance names
        """
        instances_dir = Path("instances")
        if not instances_dir.exists():
            return []
        
        instances = []
        for item in instances_dir.iterdir():
            if item.is_dir() and (item / "config.yaml").exists():
                instances.append(item.name)
        
        return instances
    
    @staticmethod
    def list_templates() -> List[str]:
        """
        List all available templates.
        
        Returns:
            List of template names
        """
        templates_dir = Path("personas/templates")
        if not templates_dir.exists():
            return []
        
        templates = []
        for item in templates_dir.iterdir():
            if item.suffix in ['.yaml', '.yml']:
                templates.append(item.stem)
        
        return templates
    
    @staticmethod
    def delete_instance(instance_name: str) -> bool:
        """
        Delete an avatar instance.
        
        Args:
            instance_name: Name of instance to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            instance_path = Path(f"instances/{instance_name}")
            
            if not instance_path.exists():
                logger.warning(f"Instance not found: {instance_name}")
                return False
            
            # Remove directory and all contents
            import shutil
            shutil.rmtree(instance_path)
            
            logger.info(f"Instance deleted: {instance_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete instance {instance_name}: {e}")
            return False
    
    @staticmethod
    def validate_instance(instance_name: str) -> List[str]:
        """
        Validate an avatar instance configuration.
        
        Args:
            instance_name: Name of instance to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        try:
            # Check instance exists
            instance_path = Path(f"instances/{instance_name}")
            if not instance_path.exists():
                errors.append(f"Instance directory not found: {instance_name}")
                return errors
            
            # Check config exists
            config_path = instance_path / "config.yaml"
            if not config_path.exists():
                errors.append("Configuration file not found")
                return errors
            
            # Load and validate configuration
            try:
                config = BaseConfig.from_file(str(config_path))
                config_errors = config.validate()
                errors.extend(config_errors)
            except Exception as e:
                errors.append(f"Configuration error: {e}")
            
            # Check persona
            persona_path = instance_path / "persona.yaml"
            if persona_path.exists():
                try:
                    persona = BasePersona.from_file(str(persona_path))
                    persona_errors = persona.validate()
                    errors.extend(persona_errors)
                except Exception as e:
                    errors.append(f"Persona error: {e}")
            
            # Check directories
            if not (instance_path / "tools").exists():
                errors.append("Tools directory not found")
            
            if not (instance_path / "knowledge_base").exists():
                errors.append("Knowledge base directory not found")
            
        except Exception as e:
            errors.append(f"Validation error: {e}")
        
        return errors
    
    @staticmethod
    def _load_instance_tools(avatar: AvatarEngine, instance_name: str):
        """Load instance-specific tools"""
        tools_path = Path(f"instances/{instance_name}/tools")
        
        if not tools_path.exists():
            return
        
        # Look for Python tool files
        for tool_file in tools_path.glob("*.py"):
            try:
                # Import tool module
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    tool_file.stem,
                    tool_file
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Register tools from module
                if hasattr(module, 'register_tools'):
                    module.register_tools(avatar)
                    logger.info(f"Loaded tools from {tool_file.name}")
                
            except Exception as e:
                logger.error(f"Failed to load tool {tool_file.name}: {e}")
    
    @staticmethod
    def _load_knowledge_base(avatar: AvatarEngine, kb_path: str):
        """Load knowledge base into avatar"""
        kb_path = Path(kb_path)
        
        if not kb_path.exists():
            return
        
        # Check if avatar has RAG plugin
        rag_plugin = avatar.plugins.get('rag_plugin')
        if not rag_plugin:
            logger.warning("RAG plugin not found, skipping knowledge base loading")
            return
        
        # Load documents
        doc_count = 0
        for file_path in kb_path.iterdir():
            if file_path.is_file() and file_path.suffix in ['.txt', '.md', '.pdf', '.json']:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Add document to RAG plugin
                    rag_plugin.add_document({
                        'id': file_path.name,
                        'content': content,
                        'metadata': {
                            'source': str(file_path),
                            'type': file_path.suffix
                        }
                    })
                    doc_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to load document {file_path.name}: {e}")
        
        logger.info(f"Loaded {doc_count} documents into knowledge base")
    
    @staticmethod
    def export_instance(instance_name: str, output_path: Optional[str] = None) -> str:
        """
        Export an avatar instance as a package.
        
        Args:
            instance_name: Name of instance to export
            output_path: Optional output path for package
            
        Returns:
            Path to exported package
        """
        try:
            import shutil
            import tempfile
            from datetime import datetime
            
            # Validate instance exists
            instance_path = Path(f"instances/{instance_name}")
            if not instance_path.exists():
                raise ValueError(f"Instance not found: {instance_name}")
            
            # Create output filename
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"exports/{instance_name}_{timestamp}.zip"
            
            # Ensure exports directory exists
            Path("exports").mkdir(exist_ok=True)
            
            # Create archive
            base_name = output_path.replace('.zip', '')
            shutil.make_archive(base_name, 'zip', instance_path)
            
            logger.info(f"Instance exported: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to export instance {instance_name}: {e}")
            raise
    
    @staticmethod
    def import_instance(package_path: str, instance_name: Optional[str] = None) -> str:
        """
        Import an avatar instance from a package.
        
        Args:
            package_path: Path to package file
            instance_name: Optional name for imported instance
            
        Returns:
            Name of imported instance
        """
        try:
            import shutil
            import zipfile
            from datetime import datetime
            
            # Validate package exists
            if not os.path.exists(package_path):
                raise FileNotFoundError(f"Package not found: {package_path}")
            
            # Generate instance name if not provided
            if not instance_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                instance_name = f"imported_{timestamp}"
            
            # Extract to instances directory
            instance_path = Path(f"instances/{instance_name}")
            instance_path.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(package_path, 'r') as zip_ref:
                zip_ref.extractall(instance_path)
            
            # Update instance name in config
            config_path = instance_path / "config.yaml"
            if config_path.exists():
                config = BaseConfig.from_file(str(config_path))
                config.set('instance.name', instance_name)
                config.to_yaml(str(config_path))
            
            logger.info(f"Instance imported: {instance_name}")
            return instance_name
            
        except Exception as e:
            logger.error(f"Failed to import instance from {package_path}: {e}")
            raise
