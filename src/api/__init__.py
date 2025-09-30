"""FastAPI application and endpoints."""
from .app import create_app
from .middleware import setup_middleware
from .endpoints import register_endpoints

__all__ = ['create_app', 'setup_middleware', 'register_endpoints']
