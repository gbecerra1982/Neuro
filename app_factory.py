#!/usr/bin/env python3
"""
Avatar Factory - Main Application Runner
Run the Avatar Factory with specified instance or in management mode.

Usage:
    python app_factory.py                    # Run in management mode
    python app_factory.py --instance ypf_neuro  # Run specific instance
    python app_factory.py --create-instance my_avatar --template corporate
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from api.app import create_app, socketio
from factory.instance_manager import get_instance_manager
from factory.avatar_factory import AvatarFactory

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for Avatar Factory"""
    parser = argparse.ArgumentParser(
        description="Avatar Factory - Modular Avatar System"
    )
    
    parser.add_argument(
        '--instance',
        help='Name of the avatar instance to run'
    )
    
    parser.add_argument(
        '--host',
        default=os.environ.get('FLASK_HOST', '0.0.0.0'),
        help='Host to bind to (default: 0.0.0.0)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=int(os.environ.get('FLASK_PORT', 5000)),
        help='Port to bind to (default: 5000)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Run in debug mode'
    )
    
    parser.add_argument(
        '--list-instances',
        action='store_true',
        help='List all available instances'
    )
    
    parser.add_argument(
        '--list-templates',
        action='store_true',
        help='List all available templates'
    )
    
    parser.add_argument(
        '--validate',
        help='Validate an instance configuration'
    )
    
    parser.add_argument(
        '--create-instance',
        help='Create a new instance with specified name'
    )
    
    parser.add_argument(
        '--template',
        default='assistant',
        help='Template to use when creating instance (default: assistant)'
    )
    
    parser.add_argument(
        '--auto-start',
        action='store_true',
        help='Automatically start the instance on launch'
    )
    
    args = parser.parse_args()
    
    # Handle utility commands
    if args.list_instances:
        print("\n📦 Available Avatar Instances:")
        print("=" * 40)
        instances = AvatarFactory.list_instances()
        if instances:
            for instance in instances:
                status = "✓" if Path(f"instances/{instance}/config.yaml").exists() else "✗"
                print(f"  {status} {instance}")
        else:
            print("  No instances found")
        print("\nUse --instance <name> to run a specific instance")
        return
    
    if args.list_templates:
        print("\n📋 Available Templates:")
        print("=" * 40)
        templates = AvatarFactory.list_templates()
        if templates:
            for template in templates:
                print(f"  • {template}")
        else:
            print("  No templates found")
        print("\nUse --create-instance <name> --template <template> to create a new instance")
        return
    
    if args.validate:
        print(f"\n🔍 Validating instance: {args.validate}")
        print("=" * 40)
        errors = AvatarFactory.validate_instance(args.validate)
        if errors:
            print("❌ Validation failed:")
            for error in errors:
                print(f"  • {error}")
        else:
            print("✅ Instance is valid")
        return
    
    if args.create_instance:
        print(f"\n🏗️ Creating instance: {args.create_instance}")
        print("=" * 40)
        try:
            avatar = AvatarFactory.create_from_template(
                args.create_instance,
                args.template
            )
            print(f"✅ Instance '{args.create_instance}' created successfully")
            print(f"\nRun with: python {__file__} --instance {args.create_instance}")
        except Exception as e:
            print(f"❌ Failed to create instance: {e}")
            sys.exit(1)
        return
    
    # Print startup banner
    print("\n" + "=" * 60)
    print("🏭 AVATAR FACTORY - Modular Avatar System")
    print("=" * 60)
    
    # Create Flask app
    app = create_app(args.instance)
    
    # Get instance manager
    instance_manager = get_instance_manager()
    
    # Auto-start instance if specified
    if args.instance and args.auto_start:
        import asyncio
        print(f"\n🚀 Auto-starting instance: {args.instance}")
        try:
            result = asyncio.run(instance_manager.start_instance(args.instance))
            if result:
                print(f"✅ Instance '{args.instance}' started successfully")
            else:
                print(f"⚠️ Failed to start instance '{args.instance}'")
        except Exception as e:
            print(f"❌ Error starting instance: {e}")
    
    # Print running information
    if args.instance:
        print(f"\n📦 Instance: {args.instance}")
    else:
        print("\n🎛️ Running in Management Mode")
        print("   Available instances:")
        for instance in AvatarFactory.list_instances():
            print(f"     • {instance}")
    
    print(f"\n🌐 Server Configuration:")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Debug: {args.debug}")
    
    print(f"\n📡 API Endpoints:")
    print(f"   Main Interface: http://{args.host}:{args.port}/")
    print(f"   API Base: http://{args.host}:{args.port}/api/")
    print(f"   Health Check: http://{args.host}:{args.port}/api/health")
    print(f"   Instances: http://{args.host}:{args.port}/api/instances")
    
    print("\n" + "=" * 60)
    print("✨ Avatar Factory is starting...")
    print("Press CTRL+C to stop")
    print("=" * 60 + "\n")
    
    # Run the application
    try:
        socketio.run(
            app,
            host=args.host,
            port=args.port,
            debug=args.debug,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down Avatar Factory...")
        
        # Cleanup
        import asyncio
        asyncio.run(instance_manager.shutdown_all())
        
        print("✅ Shutdown complete")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
