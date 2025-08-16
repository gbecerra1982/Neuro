#!/usr/bin/env python3
"""
Create Avatar Instance Script
Creates a new avatar instance from a template with proper configuration.

Usage:
    python create_instance.py --name my_avatar --template corporate
    python create_instance.py --name tech_support --template technical --language es-ES
"""

import argparse
import os
import sys
import shutil
import yaml
from pathlib import Path
from datetime import datetime


def create_avatar_instance(
    name: str,
    template: str = "assistant",
    language: str = "en-US",
    voice: str = None,
    description: str = None
):
    """
    Create a new avatar instance from a template.
    
    Args:
        name: Name of the new instance
        template: Template to use (corporate, technical, assistant)
        language: Language code (e.g., en-US, es-AR)
        voice: Voice model name
        description: Description of the avatar
    """
    print(f"🏭 Avatar Factory - Creating new instance: {name}")
    print(f"📋 Template: {template}")
    print(f"🌍 Language: {language}")
    
    # Validate name
    if not name or not name.replace('_', '').replace('-', '').isalnum():
        print("❌ Error: Instance name must be alphanumeric (underscores and hyphens allowed)")
        return False
    
    # Check if instance already exists
    instance_path = Path(f"instances/{name}")
    if instance_path.exists():
        print(f"❌ Error: Instance '{name}' already exists")
        return False
    
    # Check if template exists
    template_path = Path(f"personas/templates/{template}.yaml")
    if not template_path.exists():
        print(f"❌ Error: Template '{template}' not found")
        print(f"Available templates: {', '.join(list_templates())}")
        return False
    
    try:
        # Create instance directory structure
        print(f"📁 Creating directory structure...")
        instance_path.mkdir(parents=True, exist_ok=True)
        (instance_path / "tools").mkdir(exist_ok=True)
        (instance_path / "knowledge_base").mkdir(exist_ok=True)
        
        # Copy and customize persona template
        print(f"👤 Setting up persona...")
        with open(template_path, 'r') as f:
            persona_config = yaml.safe_load(f)
        
        # Customize persona
        persona_config['name'] = f"{name.replace('_', ' ').title()} Assistant"
        if description:
            persona_config['role'] = description
        
        # Set language and voice
        persona_config['voice']['language'] = language
        if voice:
            persona_config['voice']['model'] = voice
        else:
            # Auto-select voice based on language
            persona_config['voice']['model'] = get_default_voice(language)
        
        # Save persona configuration
        persona_file = instance_path / "persona.yaml"
        with open(persona_file, 'w') as f:
            yaml.dump(persona_config, f, default_flow_style=False, sort_keys=False)
        
        # Create instance configuration
        print(f"⚙️ Creating configuration...")
        config = create_default_config(name, template)
        
        config_file = instance_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        # Copy .env template
        print(f"🔐 Setting up environment template...")
        env_template = Path(".env-template")
        if env_template.exists():
            shutil.copy(env_template, instance_path / ".env")
        
        # Create README for the instance
        print(f"📝 Creating documentation...")
        create_instance_readme(instance_path, name, template, language)
        
        # Create example tool
        print(f"🔧 Adding example tool...")
        create_example_tool(instance_path / "tools")
        
        # Create example knowledge base file
        print(f"📚 Adding example knowledge base...")
        create_example_knowledge(instance_path / "knowledge_base")
        
        print(f"\n✅ Avatar instance '{name}' created successfully!")
        print(f"\n📍 Location: {instance_path}")
        print(f"\n🚀 Next steps:")
        print(f"   1. Edit {instance_path}/config.yaml to configure Azure services")
        print(f"   2. Set environment variables in {instance_path}/.env")
        print(f"   3. Add documents to {instance_path}/knowledge_base/")
        print(f"   4. Add custom tools to {instance_path}/tools/")
        print(f"   5. Run: python app.py --instance {name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating instance: {e}")
        # Clean up on failure
        if instance_path.exists():
            shutil.rmtree(instance_path)
        return False


def create_default_config(name: str, template: str) -> dict:
    """Create default configuration for instance"""
    return {
        'instance': {
            'name': name,
            'template': template,
            'version': '1.0.0',
            'created': datetime.now().isoformat(),
            'environment': 'development'
        },
        'azure': {
            'openai': {
                'endpoint': '${AZURE_OPENAI_ENDPOINT}',
                'api_key': '${AZURE_OPENAI_API_KEY}',
                'deployment': '${AZURE_OPENAI_DEPLOYMENT:gpt-4o-realtime-preview}',
                'api_version': '${AZURE_OPENAI_API_VERSION:2025-04-01-preview}'
            },
            'speech': {
                'key': '${SPEECH_KEY}',
                'region': '${SPEECH_REGION}',
                'endpoint': '${SPEECH_ENDPOINT}'
            }
        },
        'plugins': get_template_plugins(template),
        'ui': {
            'template': 'base/avatar_interface.html',
            'theme': get_template_theme(template)
        },
        'features': {
            'avatar': True,
            'voice': True,
            'chat': True,
            'rag': template in ['corporate', 'technical'],
            'sql': template in ['corporate', 'technical'],
            'tools': True
        }
    }


def get_template_plugins(template: str) -> list:
    """Get default plugins for template"""
    plugins = {
        'assistant': [
            {'name': 'tools_plugin', 'config': {'enabled_tools': ['weather', 'calculator']}}
        ],
        'corporate': [
            {'name': 'rag_plugin', 'config': {'vector_store_type': 'in_memory'}},
            {'name': 'sql_plugin', 'config': {'database': 'sqlite', 'read_only': True}},
            {'name': 'tools_plugin', 'config': {'enabled_tools': ['calendar', 'email']}}
        ],
        'technical': [
            {'name': 'rag_plugin', 'config': {'vector_store_type': 'in_memory'}},
            {'name': 'sql_plugin', 'config': {'database': 'sqlite', 'read_only': False}},
            {'name': 'tools_plugin', 'config': {'enabled_tools': ['diagnostics', 'logs']}}
        ]
    }
    return plugins.get(template, plugins['assistant'])


def get_template_theme(template: str) -> str:
    """Get default theme for template"""
    themes = {
        'assistant': 'friendly',
        'corporate': 'professional',
        'technical': 'dark'
    }
    return themes.get(template, 'default')


def get_default_voice(language: str) -> str:
    """Get default voice for language"""
    voices = {
        'en-US': 'en-US-JennyNeural',
        'en-GB': 'en-GB-SoniaNeural',
        'es-ES': 'es-ES-ElviraNeural',
        'es-AR': 'es-AR-ElenaNeural',
        'es-MX': 'es-MX-DaliaNeural',
        'fr-FR': 'fr-FR-DeniseNeural',
        'de-DE': 'de-DE-KatjaNeural',
        'it-IT': 'it-IT-ElsaNeural',
        'pt-BR': 'pt-BR-FranciscaNeural',
        'ja-JP': 'ja-JP-NanamiNeural',
        'zh-CN': 'zh-CN-XiaoxiaoNeural'
    }
    return voices.get(language, 'en-US-JennyNeural')


def create_instance_readme(path: Path, name: str, template: str, language: str):
    """Create README for instance"""
    readme_content = f"""# {name.replace('_', ' ').title()} Avatar Instance

## Overview
This avatar instance was created from the '{template}' template.

- **Language**: {language}
- **Template**: {template}
- **Created**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Configuration

### Azure Services
Edit `config.yaml` to configure your Azure services:
- Azure OpenAI endpoint and API key
- Azure Speech Services key and region
- Azure Cognitive Search (if using RAG)

### Environment Variables
Copy `.env.example` to `.env` and set your credentials.

### Persona
Edit `persona.yaml` to customize:
- Voice and language settings
- Avatar appearance
- Personality traits
- System prompt
- Conversation style

## Knowledge Base
Add documents to the `knowledge_base/` directory:
- Supported formats: .txt, .md, .pdf, .json
- Documents will be indexed for RAG (if enabled)

## Custom Tools
Add Python files to the `tools/` directory:
- Each file should contain tool functions
- Use `register_tools(avatar)` function to register

## Running the Instance

```bash
python app.py --instance {name}
```

Or using the API:
```python
from factory import AvatarFactory

avatar = AvatarFactory.create_avatar("{name}")
await avatar.initialize()
await avatar.start_session()
```

## Testing

```bash
python test_instance.py --name {name}
```
"""
    
    with open(path / "README.md", 'w') as f:
        f.write(readme_content)


def create_example_tool(tools_path: Path):
    """Create an example tool file"""
    tool_content = '''"""
Example Custom Tool for Avatar Instance
"""

def register_tools(avatar):
    """Register custom tools with the avatar engine"""
    
    # Register a simple greeting tool
    avatar.register_tool("custom_greeting", custom_greeting)
    
    # Register a data lookup tool
    avatar.register_tool("lookup_data", lookup_data)


async def custom_greeting(name: str = "User") -> str:
    """
    Custom greeting tool.
    
    Args:
        name: Name to greet
        
    Returns:
        Greeting message
    """
    return f"Hello {name}! This is a custom tool response."


async def lookup_data(query: str) -> dict:
    """
    Example data lookup tool.
    
    Args:
        query: Search query
        
    Returns:
        Mock data results
    """
    # In a real implementation, this would query a database or API
    return {
        "query": query,
        "results": [
            {"id": 1, "value": "Example result 1"},
            {"id": 2, "value": "Example result 2"}
        ],
        "count": 2
    }
'''
    
    with open(tools_path / "example_tool.py", 'w') as f:
        f.write(tool_content)


def create_example_knowledge(kb_path: Path):
    """Create example knowledge base file"""
    kb_content = """# Example Knowledge Base Document

This is an example document in your avatar's knowledge base.

## Key Information

- Your avatar can access and search through all documents in the knowledge_base directory
- Supported formats include: .txt, .md, .pdf, .json
- Documents are automatically indexed when the RAG plugin is enabled

## Adding Knowledge

1. Add documents to this directory
2. The RAG plugin will index them automatically
3. Your avatar can then answer questions based on this knowledge

## Best Practices

- Organize documents by topic
- Use clear, descriptive filenames
- Include metadata in document headers when possible
- Keep documents focused on specific topics

## Example Q&A

**Q: What is in the knowledge base?**
A: The knowledge base contains documents that provide context and information for the avatar to reference when answering questions.

**Q: How does the avatar use this information?**
A: When RAG (Retrieval Augmented Generation) is enabled, the avatar searches through these documents to find relevant information to include in its responses.
"""
    
    with open(kb_path / "example_knowledge.md", 'w') as f:
        f.write(kb_content)


def list_templates() -> list:
    """List available templates"""
    templates_dir = Path("personas/templates")
    if not templates_dir.exists():
        return []
    
    return [f.stem for f in templates_dir.glob("*.yaml")]


def main():
    parser = argparse.ArgumentParser(
        description="Create a new avatar instance from a template"
    )
    
    parser.add_argument(
        "--name",
        required=True,
        help="Name for the new avatar instance"
    )
    
    parser.add_argument(
        "--template",
        default="assistant",
        choices=["assistant", "corporate", "technical"],
        help="Template to use (default: assistant)"
    )
    
    parser.add_argument(
        "--language",
        default="en-US",
        help="Language code (e.g., en-US, es-AR, fr-FR)"
    )
    
    parser.add_argument(
        "--voice",
        help="Voice model name (optional, auto-selected based on language)"
    )
    
    parser.add_argument(
        "--description",
        help="Description or role for the avatar"
    )
    
    parser.add_argument(
        "--list-templates",
        action="store_true",
        help="List available templates"
    )
    
    args = parser.parse_args()
    
    if args.list_templates:
        templates = list_templates()
        print("Available templates:")
        for t in templates:
            print(f"  - {t}")
        return
    
    success = create_avatar_instance(
        name=args.name,
        template=args.template,
        language=args.language,
        voice=args.voice,
        description=args.description
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
