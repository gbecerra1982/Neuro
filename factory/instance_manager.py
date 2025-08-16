"""
Instance Manager - Manage avatar instances lifecycle
"""

import os
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
import asyncio

from core.avatar_engine import AvatarEngine
from .avatar_factory import AvatarFactory

logger = logging.getLogger(__name__)


class InstanceManager:
    """
    Manager for avatar instances lifecycle and orchestration.
    """
    
    def __init__(self):
        """Initialize instance manager"""
        self.instances: Dict[str, AvatarEngine] = {}
        self.instance_metadata: Dict[str, Dict] = {}
        self.max_instances = 10
        
    async def start_instance(self, instance_name: str) -> bool:
        """
        Start an avatar instance.
        
        Args:
            instance_name: Name of instance to start
            
        Returns:
            True if started successfully
        """
        try:
            # Check if already running
            if instance_name in self.instances:
                logger.warning(f"Instance {instance_name} is already running")
                return True
            
            # Check instance limit
            if len(self.instances) >= self.max_instances:
                logger.error(f"Maximum instance limit reached ({self.max_instances})")
                return False
            
            # Create avatar instance
            avatar = AvatarFactory.create_avatar(instance_name)
            
            # Initialize avatar
            await avatar.initialize()
            
            # Store instance
            self.instances[instance_name] = avatar
            self.instance_metadata[instance_name] = {
                'started_at': datetime.now().isoformat(),
                'status': 'running',
                'sessions': 0
            }
            
            logger.info(f"Instance started: {instance_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start instance {instance_name}: {e}")
            return False
    
    async def stop_instance(self, instance_name: str) -> bool:
        """
        Stop an avatar instance.
        
        Args:
            instance_name: Name of instance to stop
            
        Returns:
            True if stopped successfully
        """
        try:
            if instance_name not in self.instances:
                logger.warning(f"Instance {instance_name} is not running")
                return False
            
            avatar = self.instances[instance_name]
            
            # Stop any active sessions
            if avatar.session_state['active']:
                await avatar.stop_session()
            
            # Clean up
            for plugin_name, plugin in avatar.plugins.items():
                if hasattr(plugin, 'cleanup'):
                    await plugin.cleanup()
            
            # Remove from instances
            del self.instances[instance_name]
            
            # Update metadata
            if instance_name in self.instance_metadata:
                self.instance_metadata[instance_name]['status'] = 'stopped'
                self.instance_metadata[instance_name]['stopped_at'] = datetime.now().isoformat()
            
            logger.info(f"Instance stopped: {instance_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop instance {instance_name}: {e}")
            return False
    
    async def restart_instance(self, instance_name: str) -> bool:
        """
        Restart an avatar instance.
        
        Args:
            instance_name: Name of instance to restart
            
        Returns:
            True if restarted successfully
        """
        # Stop if running
        if instance_name in self.instances:
            await self.stop_instance(instance_name)
        
        # Start again
        return await self.start_instance(instance_name)
    
    def get_instance(self, instance_name: str) -> Optional[AvatarEngine]:
        """
        Get an avatar instance.
        
        Args:
            instance_name: Name of instance
            
        Returns:
            AvatarEngine instance or None
        """
        return self.instances.get(instance_name)
    
    def list_running_instances(self) -> List[str]:
        """
        List all running instances.
        
        Returns:
            List of running instance names
        """
        return list(self.instances.keys())
    
    def get_instance_status(self, instance_name: str) -> Dict:
        """
        Get status of an instance.
        
        Args:
            instance_name: Name of instance
            
        Returns:
            Status dictionary
        """
        if instance_name in self.instances:
            avatar = self.instances[instance_name]
            metadata = self.instance_metadata.get(instance_name, {})
            
            return {
                'name': instance_name,
                'status': 'running',
                'started_at': metadata.get('started_at'),
                'sessions': metadata.get('sessions', 0),
                'current_session': avatar.session_state.get('session_id'),
                'session_active': avatar.session_state.get('active', False),
                'plugins': list(avatar.plugins.keys()),
                'metrics': avatar.session_state.get('metrics', {})
            }
        else:
            # Check if instance exists but not running
            instance_path = Path(f"instances/{instance_name}")
            if instance_path.exists():
                return {
                    'name': instance_name,
                    'status': 'stopped',
                    'exists': True
                }
            else:
                return {
                    'name': instance_name,
                    'status': 'not_found',
                    'exists': False
                }
    
    def get_all_status(self) -> Dict:
        """
        Get status of all instances.
        
        Returns:
            Dictionary with all instance statuses
        """
        status = {
            'running': [],
            'stopped': [],
            'total_sessions': 0
        }
        
        # Running instances
        for name in self.instances.keys():
            instance_status = self.get_instance_status(name)
            status['running'].append(instance_status)
            status['total_sessions'] += instance_status.get('sessions', 0)
        
        # Check for stopped instances
        instances_dir = Path("instances")
        if instances_dir.exists():
            for item in instances_dir.iterdir():
                if item.is_dir() and item.name not in self.instances:
                    status['stopped'].append({
                        'name': item.name,
                        'status': 'stopped'
                    })
        
        status['running_count'] = len(status['running'])
        status['stopped_count'] = len(status['stopped'])
        
        return status
    
    async def start_session(self, instance_name: str, session_id: Optional[str] = None) -> Dict:
        """
        Start a session for an instance.
        
        Args:
            instance_name: Name of instance
            session_id: Optional session ID
            
        Returns:
            Session information
        """
        avatar = self.get_instance(instance_name)
        
        if not avatar:
            # Try to start instance
            if await self.start_instance(instance_name):
                avatar = self.get_instance(instance_name)
            else:
                return {'error': f'Failed to start instance {instance_name}'}
        
        # Start session
        result = await avatar.start_session(session_id)
        
        # Update metadata
        if instance_name in self.instance_metadata:
            self.instance_metadata[instance_name]['sessions'] += 1
        
        return result
    
    async def stop_session(self, instance_name: str) -> Dict:
        """
        Stop a session for an instance.
        
        Args:
            instance_name: Name of instance
            
        Returns:
            Session closure information
        """
        avatar = self.get_instance(instance_name)
        
        if not avatar:
            return {'error': f'Instance {instance_name} not running'}
        
        return await avatar.stop_session()
    
    async def process_message(self, instance_name: str, message: Dict) -> Dict:
        """
        Process a message for an instance.
        
        Args:
            instance_name: Name of instance
            message: Message to process
            
        Returns:
            Response from instance
        """
        avatar = self.get_instance(instance_name)
        
        if not avatar:
            return {'error': f'Instance {instance_name} not running'}
        
        if not avatar.session_state.get('active'):
            return {'error': 'No active session'}
        
        return await avatar.process_message(message)
    
    async def shutdown_all(self):
        """Shutdown all running instances"""
        logger.info("Shutting down all instances...")
        
        tasks = []
        for instance_name in list(self.instances.keys()):
            tasks.append(self.stop_instance(instance_name))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info("All instances shut down")
    
    def save_state(self, file_path: Optional[str] = None):
        """
        Save current state to file.
        
        Args:
            file_path: Optional path to save state
        """
        if not file_path:
            file_path = "data/instance_manager_state.json"
        
        Path("data").mkdir(exist_ok=True)
        
        state = {
            'instances': list(self.instances.keys()),
            'metadata': self.instance_metadata,
            'saved_at': datetime.now().isoformat()
        }
        
        with open(file_path, 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info(f"State saved to {file_path}")
    
    def load_state(self, file_path: Optional[str] = None):
        """
        Load state from file.
        
        Args:
            file_path: Optional path to load state from
        """
        if not file_path:
            file_path = "data/instance_manager_state.json"
        
        if not os.path.exists(file_path):
            logger.warning(f"State file not found: {file_path}")
            return
        
        try:
            with open(file_path, 'r') as f:
                state = json.load(f)
            
            self.instance_metadata = state.get('metadata', {})
            
            logger.info(f"State loaded from {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
    
    def get_metrics(self) -> Dict:
        """Get metrics for all instances"""
        metrics = {
            'total_instances': len(AvatarFactory.list_instances()),
            'running_instances': len(self.instances),
            'total_sessions': sum(
                m.get('sessions', 0) for m in self.instance_metadata.values()
            ),
            'instances': {}
        }
        
        for name, avatar in self.instances.items():
            metrics['instances'][name] = {
                'sessions': self.instance_metadata.get(name, {}).get('sessions', 0),
                'current_session_active': avatar.session_state.get('active', False),
                'messages_processed': avatar.session_state.get('metrics', {}).get('messages_sent', 0),
                'plugins_loaded': len(avatar.plugins)
            }
        
        return metrics


# Global instance manager
_instance_manager = None


def get_instance_manager() -> InstanceManager:
    """Get the global instance manager"""
    global _instance_manager
    if _instance_manager is None:
        _instance_manager = InstanceManager()
    return _instance_manager
