"""
Speech Handler - Azure Speech Services wrapper for avatar and TTS
"""

import asyncio
import logging
from typing import Dict, Optional, Any
import requests
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class SpeechHandler:
    """
    Handler for Azure Speech Services including Avatar and TTS functionality.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize Speech Handler with configuration.
        
        Args:
            config: Configuration dictionary with speech service details
        """
        self.config = config.get('speech', {})
        
        # Azure Speech configuration
        self.speech_key = self.config.get('key', '')
        self.speech_region = self.config.get('region', 'westus2')
        self.speech_endpoint = self.config.get('endpoint', '')
        
        # Avatar configuration
        self.avatar_config = {
            'character': 'lisa',
            'style': 'casual-sitting',
            'background_color': '#FFFFFF',
            'video_codec': 'H264',
            'video_bitrate': 2000000,
            'video_framerate': 25
        }
        
        # TTS configuration
        self.voice_name = 'en-US-JennyNeural'
        self.voice_language = 'en-US'
        
        # State
        self.avatar_connected = False
        self.synthesizer = None
        self.avatar_connection = None
        
        # SDK availability flag
        self.sdk_available = False
    
    async def initialize(self):
        """Initialize the speech handler"""
        try:
            # Check if Speech SDK is available
            self._check_sdk_availability()
            
            if self.sdk_available:
                await self._initialize_sdk_components()
            else:
                logger.warning("Azure Speech SDK not available, using REST API fallback")
            
            logger.info("Speech handler initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize speech handler: {e}")
            return False
    
    def _check_sdk_availability(self):
        """Check if Azure Speech SDK is available"""
        try:
            import azure.cognitiveservices.speech as speechsdk
            self.sdk_available = True
            self.speechsdk = speechsdk
            logger.info("Azure Speech SDK is available")
        except ImportError:
            self.sdk_available = False
            logger.warning("Azure Speech SDK not installed")
    
    async def _initialize_sdk_components(self):
        """Initialize SDK-based components"""
        if not self.sdk_available:
            return
        
        try:
            # Create speech config
            speech_config = self.speechsdk.SpeechConfig(
                subscription=self.speech_key,
                region=self.speech_region
            )
            
            # Set voice
            speech_config.speech_synthesis_voice_name = self.voice_name
            speech_config.speech_synthesis_language = self.voice_language
            
            # Store config for later use
            self.speech_config = speech_config
            
        except Exception as e:
            logger.error(f"Failed to initialize SDK components: {e}")
    
    async def get_speech_token(self) -> Optional[str]:
        """
        Get a speech token for client-side SDK usage.
        
        Returns:
            Speech token string or None if failed
        """
        try:
            token_endpoint = f"https://{self.speech_region}.api.cognitive.microsoft.com/sts/v1.0/issuetoken"
            
            response = requests.post(
                token_endpoint,
                headers={
                    'Ocp-Apim-Subscription-Key': self.speech_key,
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return response.text
            else:
                logger.error(f"Failed to get speech token: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting speech token: {e}")
            return None
    
    async def start_avatar(self, avatar_config: Optional[Dict] = None) -> bool:
        """
        Start the avatar video stream.
        
        Args:
            avatar_config: Optional avatar configuration override
            
        Returns:
            True if avatar started successfully
        """
        if avatar_config:
            self.avatar_config.update(avatar_config)
        
        if not self.sdk_available:
            logger.warning("Cannot start avatar without SDK")
            return False
        
        try:
            # Get relay token for ICE servers
            relay_token = await self._get_relay_token()
            if not relay_token:
                return False
            
            # Create avatar configuration
            video_format = self.speechsdk.AvatarVideoFormat()
            video_format.width = 1920
            video_format.height = 1080
            video_format.bitrate = self.avatar_config['video_bitrate']
            video_format.frameRate = self.avatar_config['video_framerate']
            
            avatar_config_sdk = self.speechsdk.AvatarConfig(
                self.avatar_config['character'],
                self.avatar_config['style'],
                video_format
            )
            
            # Set background color if available
            if hasattr(avatar_config_sdk, 'backgroundColor'):
                avatar_config_sdk.backgroundColor = self.avatar_config['background_color']
            
            # Create avatar synthesizer
            self.synthesizer = self.speechsdk.AvatarSynthesizer(
                self.speech_config,
                avatar_config_sdk
            )
            
            # Start avatar connection
            # Note: Actual WebRTC connection would be established here
            # This is a simplified version
            self.avatar_connected = True
            
            logger.info("Avatar started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start avatar: {e}")
            return False
    
    async def _get_relay_token(self) -> Optional[Dict]:
        """Get relay token for WebRTC ICE servers"""
        try:
            relay_url = f"https://{self.speech_region}.tts.speech.microsoft.com/cognitiveservices/avatar/relay/token/v1"
            
            response = requests.get(
                relay_url,
                headers={
                    'Ocp-Apim-Subscription-Key': self.speech_key,
                    'Content-Type': 'application/json'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get relay token: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting relay token: {e}")
            return None
    
    async def stop_avatar(self) -> bool:
        """Stop the avatar video stream"""
        try:
            if self.synthesizer and self.avatar_connected:
                # Stop avatar synthesizer
                # Note: Actual SDK call would be here
                self.avatar_connected = False
                self.synthesizer = None
                
                logger.info("Avatar stopped")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to stop avatar: {e}")
            return False
    
    async def speak(self, text: str, voice: Optional[str] = None) -> bool:
        """
        Make the avatar speak the given text.
        
        Args:
            text: Text to speak
            voice: Optional voice override
            
        Returns:
            True if speech started successfully
        """
        if not text:
            return False
        
        voice = voice or self.voice_name
        
        # If SDK is available and avatar is connected
        if self.sdk_available and self.avatar_connected and self.synthesizer:
            return await self._speak_with_avatar(text)
        # Otherwise use REST API for TTS
        else:
            return await self._speak_with_rest(text, voice)
    
    async def _speak_with_avatar(self, text: str) -> bool:
        """Speak using avatar synthesizer"""
        try:
            # Use avatar synthesizer to speak
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self.synthesizer.speak_text_async(text).get
            )
            
            if result.reason == self.speechsdk.ResultReason.SynthesizingAudioCompleted:
                logger.info(f"Avatar speech completed: {text[:50]}...")
                return True
            else:
                logger.error(f"Avatar speech failed: {result.reason}")
                return False
                
        except Exception as e:
            logger.error(f"Error in avatar speech: {e}")
            return False
    
    async def _speak_with_rest(self, text: str, voice: str) -> bool:
        """Speak using REST API"""
        try:
            # Build SSML
            ssml = f"""
            <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='{self.voice_language}'>
                <voice name='{voice}'>
                    {text}
                </voice>
            </speak>
            """
            
            # TTS endpoint
            tts_url = f"https://{self.speech_region}.tts.speech.microsoft.com/cognitiveservices/v1"
            
            response = requests.post(
                tts_url,
                headers={
                    'Ocp-Apim-Subscription-Key': self.speech_key,
                    'Content-Type': 'application/ssml+xml',
                    'X-Microsoft-OutputFormat': 'audio-24khz-96kbitrate-mono-mp3'
                },
                data=ssml.encode('utf-8'),
                timeout=30
            )
            
            if response.status_code == 200:
                # Audio data is in response.content
                # This would be sent to the client or played
                logger.info(f"TTS completed: {text[:50]}...")
                return True
            else:
                logger.error(f"TTS failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error in REST TTS: {e}")
            return False
    
    def update_voice(self, voice_name: str, language: str = None):
        """
        Update the voice configuration.
        
        Args:
            voice_name: Name of the voice to use
            language: Optional language code
        """
        self.voice_name = voice_name
        if language:
            self.voice_language = language
        
        # Update SDK config if available
        if self.sdk_available and hasattr(self, 'speech_config'):
            self.speech_config.speech_synthesis_voice_name = voice_name
            if language:
                self.speech_config.speech_synthesis_language = language
        
        logger.info(f"Voice updated to: {voice_name}")
    
    def update_avatar_config(self, config: Dict):
        """
        Update avatar configuration.
        
        Args:
            config: Avatar configuration dictionary
        """
        self.avatar_config.update(config)
        logger.info(f"Avatar configuration updated")
    
    def get_available_voices(self, language: Optional[str] = None) -> list:
        """
        Get list of available voices.
        
        Args:
            language: Optional language filter
            
        Returns:
            List of available voice names
        """
        # This is a subset of available voices
        # In production, this would query the API for full list
        voices = {
            'en-US': [
                'en-US-JennyNeural',
                'en-US-GuyNeural',
                'en-US-AriaNeural',
                'en-US-DavisNeural'
            ],
            'es-AR': [
                'es-AR-ElenaNeural',
                'es-AR-TomasNeural'
            ],
            'es-ES': [
                'es-ES-AlvaroNeural',
                'es-ES-ElviraNeural'
            ]
        }
        
        if language:
            return voices.get(language, [])
        
        # Return all voices
        all_voices = []
        for lang_voices in voices.values():
            all_voices.extend(lang_voices)
        return all_voices
    
    def get_status(self) -> Dict:
        """Get current status of speech handler"""
        return {
            'sdk_available': self.sdk_available,
            'avatar_connected': self.avatar_connected,
            'current_voice': self.voice_name,
            'language': self.voice_language,
            'avatar_config': self.avatar_config
        }
