#!/usr/bin/env python3
"""
Avatar Factory - Main Application Entry Point

This is the main entry point for the Avatar Factory system.
It provides a unified interface for running the application with various options.

Usage:
    python main.py                    # Run with default settings
    python main.py --instance ypf_neuro  # Run with specific instance
    python main.py --create my_avatar    # Create new instance
    python main.py --list              # List all instances
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from api.app import create_app, socketio
from factory import AvatarFactory, get_instance_manager
from scripts.create_instance import create_avatar_instance

# Configure logging
logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_banner():
    """Print application banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║     🏭  AVATAR FACTORY - AI Avatar Management System  🏭     ║
    ║                                                              ║
    ║     Powered by Azure OpenAI Realtime API & Speech Services  ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def run_server(args):
    """Run the Avatar Factory server"""
    print_banner()
    
    # Create Flask app
    app = create_app(instance_name=args.instance)
    
    # Print configuration
    print(f"\n📡 Server Configuration:")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Debug: {args.debug}")
    
    if args.instance:
        print(f"   Default Instance: {args.instance}")
    
    # List available instances
    instances = AvatarFactory.list_instances()
    if instances:
        print(f"\n📦 Available Instances:")
        for instance in instances:
            errors = AvatarFactory.validate_instance(instance)
            status = "✅" if not errors else "⚠️"
            print(f"   {status} {instance}")
            if errors and args.debug:
                for error in errors[:3]:  # Show first 3 errors
                    print(f"      - {error}")
    else:
        print(f"\n📦 No instances found. Create one with: python main.py --create <name>")
    
    print(f"\n🌐 Endpoints:")
    print(f"   Web Interface: http://{args.host}:{args.port}/")
    print(f"   API: http://{args.host}:{args.port}/api/")
    print(f"   Health Check: http://{args.host}:{args.port}/api/health")
    print(f"   Metrics: http://{args.host}:{args.port}/api/metrics")
    
    if args.instance:
        print(f"   Instance URL: http://{args.host}:{args.port}/instance/{args.instance}")
    
    print("\n✨ Server starting...\n")
    print("=" * 70)
    
    # Run the server
    try:
        socketio.run(
            app,
            host=args.host,
            port=args.port,
            debug=args.debug,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


def create_instance(args):
    """Create a new avatar instance"""
    print_banner()
    print(f"\n🎭 Creating new avatar instance: {args.create}")
    
    success = create_avatar_instance(
        name=args.create,
        template=args.template,
        language=args.language,
        voice=args.voice,
        description=args.description
    )
    
    if success:
        print(f"\n✅ Instance created successfully!")
        print(f"\nTo run this instance:")
        print(f"   python main.py --instance {args.create}")
    else:
        print(f"\n❌ Failed to create instance")
        sys.exit(1)


def list_instances(args):
    """List all avatar instances"""
    print_banner()
    print(f"\n📦 Avatar Instances:\n")
    
    instances = AvatarFactory.list_instances()
    templates = AvatarFactory.list_templates()
    
    if instances:
        print("Instances:")
        for instance in instances:
            errors = AvatarFactory.validate_instance(instance)
            if not errors:
                print(f"  ✅ {instance}")
            else:
                print(f"  ⚠️  {instance} ({len(errors)} issues)")
                if args.verbose:
                    for error in errors:
                        print(f"     - {error}")
    else:
        print("  No instances found")
    
    print(f"\nTemplates:")
    for template in templates:
        print(f"  📋 {template}")
    
    print(f"\nCommands:")
    print(f"  Create instance: python main.py --create <name> --template <template>")
    print(f"  Run instance: python main.py --instance <name>")
    print(f"  Delete instance: python main.py --delete <name>")


def delete_instance(args):
    """Delete an avatar instance"""
    print_banner()
    print(f"\n🗑️  Deleting instance: {args.delete}")
    
    # Confirm deletion
    if not args.force:
        response = input(f"Are you sure you want to delete '{args.delete}'? (y/N): ")
        if response.lower() != 'y':
            print("Deletion cancelled")
            return
    
    success = AvatarFactory.delete_instance(args.delete)
    if success:
        print(f"✅ Instance '{args.delete}' deleted successfully")
    else:
        print(f"❌ Failed to delete instance '{args.delete}'")
        sys.exit(1)


def validate_instance(args):
    """Validate an avatar instance"""
    print_banner()
    print(f"\n🔍 Validating instance: {args.validate}\n")
    
    errors = AvatarFactory.validate_instance(args.validate)
    
    if not errors:
        print(f"✅ Instance '{args.validate}' is valid and ready to run")
    else:
        print(f"⚠️  Instance '{args.validate}' has {len(errors)} issue(s):\n")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
        sys.exit(1)


def export_instance(args):
    """Export an avatar instance"""
    print_banner()
    print(f"\n📤 Exporting instance: {args.export_instance}")
    
    try:
        package_path = AvatarFactory.export_instance(args.export_instance)
        print(f"✅ Instance exported to: {package_path}")
    except Exception as e:
        print(f"❌ Export failed: {e}")
        sys.exit(1)


def import_instance(args):
    """Import an avatar instance"""
    print_banner()
    print(f"\n📥 Importing from: {args.import_instance}")
    
    try:
        instance_name = AvatarFactory.import_instance(
            args.import_instance,
            args.import_name
        )
        print(f"✅ Instance imported as: {instance_name}")
        print(f"\nTo run: python main.py --instance {instance_name}")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        sys.exit(1)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Avatar Factory - AI Avatar Management System',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Server options
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Host to bind to (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to bind to (default: 5000)'
    )
    parser.add_argument(
        '--instance',
        help='Default instance to load'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Run in debug mode'
    )
    
    # Instance management
    parser.add_argument(
        '--create',
        metavar='NAME',
        help='Create a new avatar instance'
    )
    parser.add_argument(
        '--template',
        default='assistant',
        choices=['assistant', 'corporate', 'technical'],
        help='Template for new instance (default: assistant)'
    )
    parser.add_argument(
        '--language',
        default='en-US',
        help='Language for new instance (default: en-US)'
    )
    parser.add_argument(
        '--voice',
        help='Voice model for new instance'
    )
    parser.add_argument(
        '--description',
        help='Description for new instance'
    )
    
    # Other operations
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all instances and templates'
    )
    parser.add_argument(
        '--delete',
        metavar='NAME',
        help='Delete an avatar instance'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force deletion without confirmation'
    )
    parser.add_argument(
        '--validate',
        metavar='NAME',
        help='Validate an instance configuration'
    )
    parser.add_argument(
        '--export-instance',
        metavar='NAME',
        help='Export an instance as a package'
    )
    parser.add_argument(
        '--import-instance',
        metavar='PATH',
        help='Import an instance from a package'
    )
    parser.add_argument(
        '--import-name',
        help='Name for imported instance'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    # Handle different operations
    try:
        if args.create:
            create_instance(args)
        elif args.list:
            list_instances(args)
        elif args.delete:
            delete_instance(args)
        elif args.validate:
            validate_instance(args)
        elif args.export_instance:
            export_instance(args)
        elif args.import_instance:
            import_instance(args)
        else:
            # Default: run server
            run_server(args)
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
