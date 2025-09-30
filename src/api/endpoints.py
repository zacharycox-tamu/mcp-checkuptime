"""Register all API endpoints."""
from fastapi import FastAPI
from . import mcp_endpoints, legacy_endpoints, n8n_mcp_endpoints
from ..config import logger


def register_endpoints(app: FastAPI) -> None:
    """Register all API endpoints on the FastAPI app."""
    logger.info("Registering endpoints...")
    
    # Register N8N-compatible MCP endpoints (must be first for root path)
    n8n_mcp_endpoints.register(app)
    
    # Register MCP protocol endpoints
    mcp_endpoints.register(app)
    
    # Register legacy/compatibility endpoints
    legacy_endpoints.register(app)
    
    logger.info("All endpoints registered")
