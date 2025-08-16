"""
Avatar Factory API - Main application entry point
"""

from .app import create_app, socketio

__all__ = ['create_app', 'socketio']
