"""
Avatar Factory API - Main Flask application
"""

import os
import sys
import logging
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from datetime import datetime
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from factory import AvatarFactory, InstanceManager, get_instance_manager
from core import AvatarEngine

# Configure logging
logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables
socketio = None
instance_manager = None


def create_app(instance_name: str = None):
    """
    Create Flask application for Avatar Factory.
    
    Args:
        instance_name: Optional default instance to load
        
    Returns:
        Flask application
    """
    app = Flask(
        __name__,
        template_folder='../templates',
        static_folder='../static'
    )
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'avatar-factory-secret-key')
    
    # CORS
    cors_origins = os.environ.get('CORS_ORIGINS', '*').split(',')
    CORS(app, origins=cors_origins)
    
    # Initialize SocketIO
    global socketio
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        ping_timeout=20,
        ping_interval=10,
        max_http_buffer_size=1000000,
        async_mode='threading',
        logger=False,
        engineio_logger=False
    )
    
    # Initialize instance manager
    global instance_manager
    instance_manager = get_instance_manager()
    
    # Load default instance if specified
    if instance_name:
        asyncio.run(load_default_instance(instance_name))
    
    # Register routes
    register_routes(app)
    
    # Register Socket.IO events
    register_socketio_events()
    
    return app


async def load_default_instance(instance_name: str):
    """Load default instance on startup"""
    try:
        await instance_manager.start_instance(instance_name)
        logger.info(f"Default instance loaded: {instance_name}")
    except Exception as e:
        logger.error(f"Failed to load default instance {instance_name}: {e}")


def register_routes(app):
    """Register Flask routes"""
    
    @app.route('/')
    def index():
        """Main interface"""
        instances = AvatarFactory.list_instances()
        return render_template('index.html', instances=instances)
    
    @app.route('/instance/<instance_name>')
    def instance_interface(instance_name):
        """Instance-specific interface"""
        # Check if instance exists
        if instance_name not in AvatarFactory.list_instances():
            return f"Instance {instance_name} not found", 404
        
        return render_template(
            'voice_live_interface.html',
            instance_name=instance_name,
            client_id=f"{instance_name}_{datetime.now().timestamp()}"
        )
    
    # API Routes
    @app.route('/api/instances', methods=['GET'])
    def list_instances():
        """List all available instances"""
        return jsonify({
            'instances': AvatarFactory.list_instances(),
            'running': instance_manager.list_running_instances()
        })
    
    @app.route('/api/instances/<instance_name>/start', methods=['POST'])
    async def start_instance(instance_name):
        """Start an instance"""
        success = await instance_manager.start_instance(instance_name)
        return jsonify({
            'success': success,
            'instance': instance_name,
            'status': 'running' if success else 'failed'
        })
    
    @app.route('/api/instances/<instance_name>/stop', methods=['POST'])
    async def stop_instance(instance_name):
        """Stop an instance"""
        success = await instance_manager.stop_instance(instance_name)
        return jsonify({
            'success': success,
            'instance': instance_name,
            'status': 'stopped' if success else 'failed'
        })
    
    @app.route('/api/instances/<instance_name>/status', methods=['GET'])
    def get_instance_status(instance_name):
        """Get instance status"""
        return jsonify(instance_manager.get_instance_status(instance_name))
    
    @app.route('/api/instances/<instance_name>/config', methods=['GET'])
    def get_instance_config(instance_name):
        """Get instance configuration"""
        try:
            from core.base_config import BaseConfig
            config_path = f"instances/{instance_name}/config.yaml"
            config = BaseConfig.from_file(config_path)
            
            # Remove sensitive information
            safe_config = config.to_dict()
            if 'azure' in safe_config:
                if 'openai' in safe_config['azure']:
                    safe_config['azure']['openai']['api_key'] = '***MASKED***'
                if 'speech' in safe_config['azure']:
                    safe_config['azure']['speech']['key'] = '***MASKED***'
                if 'cognitive_search' in safe_config['azure']:
                    safe_config['azure']['cognitive_search']['api_key'] = '***MASKED***'
            
            return jsonify(safe_config)
        except Exception as e:
            return jsonify({'error': str(e)}), 404
    
    @app.route('/api/instances/<instance_name>/session/start', methods=['POST'])
    async def start_session(instance_name):
        """Start a session for an instance"""
        data = request.get_json()
        session_id = data.get('session_id')
        
        result = await instance_manager.start_session(instance_name, session_id)
        return jsonify(result)
    
    @app.route('/api/instances/<instance_name>/session/stop', methods=['POST'])
    async def stop_session(instance_name):
        """Stop a session for an instance"""
        result = await instance_manager.stop_session(instance_name)
        return jsonify(result)
    
    @app.route('/api/instances/<instance_name>/message', methods=['POST'])
    async def process_message(instance_name):
        """Process a message for an instance"""
        data = request.get_json()
        result = await instance_manager.process_message(instance_name, data)
        return jsonify(result)
    
    @app.route('/api/instances/<instance_name>/validate', methods=['GET'])
    def validate_instance(instance_name):
        """Validate instance configuration"""
        errors = AvatarFactory.validate_instance(instance_name)
        return jsonify({
            'valid': len(errors) == 0,
            'errors': errors
        })
    
    @app.route('/api/instances/create', methods=['POST'])
    def create_instance():
        """Create a new instance"""
        data = request.get_json()
        
        try:
            avatar = AvatarFactory.create_from_template(
                instance_name=data['name'],
                template_name=data.get('template', 'assistant'),
                config_overrides=data.get('config', {})
            )
            
            return jsonify({
                'success': True,
                'instance': data['name'],
                'message': f"Instance {data['name']} created successfully"
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
    
    @app.route('/api/instances/<instance_name>/delete', methods=['DELETE'])
    def delete_instance(instance_name):
        """Delete an instance"""
        success = AvatarFactory.delete_instance(instance_name)
        return jsonify({
            'success': success,
            'instance': instance_name
        })
    
    @app.route('/api/instances/<instance_name>/export', methods=['POST'])
    def export_instance(instance_name):
        """Export instance as package"""
        try:
            package_path = AvatarFactory.export_instance(instance_name)
            return jsonify({
                'success': True,
                'package_path': package_path
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
    
    @app.route('/api/templates', methods=['GET'])
    def list_templates():
        """List available templates"""
        return jsonify({
            'templates': AvatarFactory.list_templates()
        })
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'instances': {
                'total': len(AvatarFactory.list_instances()),
                'running': len(instance_manager.list_running_instances())
            }
        })
    
    @app.route('/api/metrics', methods=['GET'])
    def get_metrics():
        """Get system metrics"""
        return jsonify(instance_manager.get_metrics())


def register_socketio_events():
    """Register Socket.IO event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        client_id = request.args.get('client_id', 'unknown')
        instance_name = request.args.get('instance', 'default')
        
        logger.info(f"Client connected: {client_id} for instance {instance_name}")
        
        emit('connected', {
            'client_id': client_id,
            'instance': instance_name,
            'timestamp': datetime.now().isoformat()
        })
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        logger.info(f"Client disconnected: {request.sid}")
    
    @socketio.on('start_instance')
    async def handle_start_instance(data):
        """Start an avatar instance"""
        instance_name = data.get('instance')
        success = await instance_manager.start_instance(instance_name)
        
        emit('instance_started', {
            'instance': instance_name,
            'success': success
        })
    
    @socketio.on('stop_instance')
    async def handle_stop_instance(data):
        """Stop an avatar instance"""
        instance_name = data.get('instance')
        success = await instance_manager.stop_instance(instance_name)
        
        emit('instance_stopped', {
            'instance': instance_name,
            'success': success
        })
    
    @socketio.on('start_session')
    async def handle_start_session(data):
        """Start a session"""
        instance_name = data.get('instance')
        session_id = data.get('session_id')
        
        result = await instance_manager.start_session(instance_name, session_id)
        emit('session_started', result)
    
    @socketio.on('stop_session')
    async def handle_stop_session(data):
        """Stop a session"""
        instance_name = data.get('instance')
        
        result = await instance_manager.stop_session(instance_name)
        emit('session_stopped', result)
    
    @socketio.on('message')
    async def handle_message(data):
        """Process a message"""
        instance_name = data.get('instance')
        message = data.get('message')
        
        result = await instance_manager.process_message(instance_name, message)
        emit('response', result)
    
    @socketio.on('realtime_connect')
    async def handle_realtime_connect(data):
        """Connect to realtime API"""
        instance_name = data.get('instance')
        client_id = data.get('client_id')
        
        avatar = instance_manager.get_instance(instance_name)
        if avatar and avatar.realtime_proxy:
            success = await avatar.realtime_proxy.connect()
            emit('realtime_connected', {
                'success': success,
                'client_id': client_id
            })
        else:
            emit('realtime_error', {
                'error': 'Instance not available or realtime not configured'
            })
    
    @socketio.on('realtime_message')
    def handle_realtime_message(data):
        """Forward message to realtime API"""
        instance_name = data.get('instance')
        message = data.get('message')
        
        avatar = instance_manager.get_instance(instance_name)
        if avatar and avatar.realtime_proxy:
            avatar.realtime_proxy.send(message)
        else:
            emit('realtime_error', {
                'error': 'Realtime connection not available'
            })
    
    @socketio.on('realtime_disconnect')
    async def handle_realtime_disconnect(data):
        """Disconnect from realtime API"""
        instance_name = data.get('instance')
        
        avatar = instance_manager.get_instance(instance_name)
        if avatar and avatar.realtime_proxy:
            await avatar.realtime_proxy.disconnect()
            emit('realtime_disconnected', {
                'instance': instance_name
            })


# Main entry point
def main():
    """Main entry point for Avatar Factory API"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Avatar Factory API Server')
    parser.add_argument(
        '--instance',
        help='Default instance to load on startup'
    )
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
        '--debug',
        action='store_true',
        help='Run in debug mode'
    )
    
    args = parser.parse_args()
    
    # Create application
    app = create_app(instance_name=args.instance)
    
    # Print startup information
    print("=" * 60)
    print("🏭 AVATAR FACTORY API SERVER")
    print("=" * 60)
    print(f"Host: {args.host}:{args.port}")
    print(f"Debug: {args.debug}")
    
    if args.instance:
        print(f"Default Instance: {args.instance}")
    
    print("\nAvailable Instances:")
    for instance in AvatarFactory.list_instances():
        print(f"  - {instance}")
    
    print("\nEndpoints:")
    print(f"  Main: http://{args.host}:{args.port}/")
    print(f"  API: http://{args.host}:{args.port}/api/")
    print(f"  Health: http://{args.host}:{args.port}/api/health")
    print("=" * 60)
    
    # Run application
    socketio.run(
        app,
        host=args.host,
        port=args.port,
        debug=args.debug,
        use_reloader=False
    )


if __name__ == '__main__':
    main()
