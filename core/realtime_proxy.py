"""
Realtime Proxy - Generic WebSocket proxy for realtime APIs
"""

import json
import logging
import threading
import asyncio
from typing import Dict, Optional, Any, Callable
import websocket
from datetime import datetime

logger = logging.getLogger(__name__)


class RealtimeProxy:
    """
    Generic WebSocket proxy for connecting to realtime APIs.
    Can be configured for different providers (Azure OpenAI, OpenAI, etc.)
    """
    
    def __init__(self, config: Dict):
        """
        Initialize the Realtime Proxy with configuration.
        
        Args:
            config: Configuration dictionary containing endpoint details
        """
        self.config = config
        self.ws = None
        self.ws_thread = None
        self.is_connected = False
        
        # Callbacks
        self.on_message_callback: Optional[Callable] = None
        self.on_error_callback: Optional[Callable] = None
        self.on_close_callback: Optional[Callable] = None
        
        # Connection details
        self.endpoint = None
        self.headers = {}
        self.connection_params = {}
        
        # Message queue
        self.message_queue = []
        self.message_handlers = {}
        
        self._setup_connection_params()
    
    def _setup_connection_params(self):
        """Setup connection parameters based on configuration"""
        provider = self.config.get('provider', 'azure_openai')
        
        if provider == 'azure_openai':
            self._setup_azure_openai()
        elif provider == 'openai':
            self._setup_openai()
        else:
            self._setup_custom()
    
    def _setup_azure_openai(self):
        """Setup for Azure OpenAI Realtime API"""
        azure_config = self.config.get('openai', {})
        
        base_endpoint = azure_config.get('endpoint', '').replace('https://', 'wss://').rstrip('/')
        deployment = azure_config.get('deployment', 'gpt-4o-realtime-preview')
        api_version = azure_config.get('api_version', '2025-04-01-preview')
        api_key = azure_config.get('api_key', '')
        
        self.endpoint = f"{base_endpoint}/openai/realtime"
        self.connection_params = {
            'api-version': api_version,
            'deployment': deployment
        }
        self.headers = {
            'api-key': api_key
        }
    
    def _setup_openai(self):
        """Setup for OpenAI Realtime API"""
        openai_config = self.config.get('openai', {})
        
        self.endpoint = openai_config.get('endpoint', 'wss://api.openai.com/v1/realtime')
        self.headers = {
            'Authorization': f"Bearer {openai_config.get('api_key', '')}",
            'OpenAI-Beta': 'realtime=v1'
        }
    
    def _setup_custom(self):
        """Setup for custom WebSocket endpoint"""
        custom_config = self.config.get('custom', {})
        
        self.endpoint = custom_config.get('endpoint', '')
        self.headers = custom_config.get('headers', {})
        self.connection_params = custom_config.get('params', {})
    
    async def initialize(self):
        """Initialize the proxy (async wrapper for compatibility)"""
        logger.info(f"Realtime proxy initialized for provider: {self.config.get('provider', 'unknown')}")
        return True
    
    async def connect(self) -> bool:
        """Establish WebSocket connection"""
        try:
            # Build WebSocket URL with parameters
            if self.connection_params:
                params = '&'.join([f"{k}={v}" for k, v in self.connection_params.items()])
                ws_url = f"{self.endpoint}?{params}"
            else:
                ws_url = self.endpoint
            
            # Add API key to URL if needed (Azure style)
            if 'api-key' in self.headers:
                ws_url += f"&api-key={self.headers['api-key']}"
                headers = {}
            else:
                headers = self.headers
            
            logger.info(f"Connecting to WebSocket: {self.endpoint}")
            
            # Create WebSocket connection
            self.ws = websocket.WebSocketApp(
                ws_url,
                header=headers,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )
            
            # Run WebSocket in separate thread
            self.ws_thread = threading.Thread(target=self.ws.run_forever)
            self.ws_thread.daemon = True
            self.ws_thread.start()
            
            # Wait for connection
            await asyncio.sleep(1)
            
            return self.is_connected
            
        except Exception as e:
            logger.error(f"Failed to connect to realtime API: {e}")
            return False
    
    def _on_open(self, ws):
        """Handle WebSocket connection opened"""
        logger.info("Realtime WebSocket connection established")
        self.is_connected = True
        
        # Send any queued messages
        for message in self.message_queue:
            self.send(message)
        self.message_queue.clear()
    
    def _on_message(self, ws, message):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message) if isinstance(message, str) else message
            
            # Log message type
            message_type = data.get('type', 'unknown')
            logger.debug(f"Received message type: {message_type}")
            
            # Call registered handler for this message type
            if message_type in self.message_handlers:
                self.message_handlers[message_type](data)
            
            # Call general callback
            if self.on_message_callback:
                self.on_message_callback(data)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _on_error(self, ws, error):
        """Handle WebSocket error"""
        logger.error(f"WebSocket error: {error}")
        
        if self.on_error_callback:
            self.on_error_callback(error)
    
    def _on_close(self, ws, close_status_code=None, close_msg=None):
        """Handle WebSocket connection closed"""
        logger.info(f"WebSocket closed (code: {close_status_code}, msg: {close_msg})")
        self.is_connected = False
        
        if self.on_close_callback:
            self.on_close_callback(close_status_code, close_msg)
    
    def send(self, message: Dict) -> bool:
        """
        Send message through WebSocket.
        
        Args:
            message: Message dictionary to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.is_connected:
            # Queue message if not connected
            self.message_queue.append(message)
            return False
        
        try:
            if isinstance(message, dict):
                message = json.dumps(message)
            
            self.ws.send(message)
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def register_handler(self, message_type: str, handler: Callable):
        """
        Register a handler for specific message types.
        
        Args:
            message_type: Type of message to handle
            handler: Callback function to handle the message
        """
        self.message_handlers[message_type] = handler
        logger.debug(f"Registered handler for message type: {message_type}")
    
    def configure_session(self, session_config: Dict):
        """
        Configure the realtime session.
        
        Args:
            session_config: Session configuration dictionary
        """
        # Build session configuration message
        config_message = {
            "type": "session.update",
            "session": session_config
        }
        
        return self.send(config_message)
    
    async def disconnect(self):
        """Disconnect WebSocket connection"""
        if self.ws:
            try:
                self.ws.close()
                self.is_connected = False
                
                # Wait for thread to finish
                if self.ws_thread and self.ws_thread.is_alive():
                    self.ws_thread.join(timeout=2)
                
                logger.info("Realtime WebSocket disconnected")
                
            except Exception as e:
                logger.error(f"Error disconnecting WebSocket: {e}")
    
    def get_connection_status(self) -> Dict:
        """Get current connection status"""
        return {
            'connected': self.is_connected,
            'endpoint': self.endpoint,
            'provider': self.config.get('provider', 'unknown'),
            'queued_messages': len(self.message_queue)
        }
    
    def send_audio(self, audio_data: bytes, format: str = 'pcm16'):
        """
        Send audio data through the realtime connection.
        
        Args:
            audio_data: Audio data bytes
            format: Audio format (default: pcm16)
        """
        import base64
        
        # Encode audio to base64
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        message = {
            'type': 'input_audio_buffer.append',
            'audio': audio_base64
        }
        
        return self.send(message)
    
    def send_text(self, text: str):
        """
        Send text message through the realtime connection.
        
        Args:
            text: Text message to send
        """
        message = {
            'type': 'conversation.item.create',
            'item': {
                'type': 'message',
                'role': 'user',
                'content': [
                    {
                        'type': 'text',
                        'text': text
                    }
                ]
            }
        }
        
        return self.send(message)
    
    def request_response(self):
        """Request a response from the model"""
        message = {
            'type': 'response.create'
        }
        
        return self.send(message)
