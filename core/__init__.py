"""
Avatar Factory Core Components
This module contains the core engine and base classes for the Avatar Factory system.
"""

from .avatar_engine import AvatarEngine
from .realtime_proxy import RealtimeProxy
from .speech_handler import SpeechHandler
from .base_config import BaseConfig

__all__ = [
    'AvatarEngine',
    'RealtimeProxy',
    'SpeechHandler',
    'BaseConfig'
]

__version__ = '1.0.0'
