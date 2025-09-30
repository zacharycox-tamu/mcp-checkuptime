"""FastAPI application factory."""
from fastapi import FastAPI
from ..config import logger


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    logger.info("Creating FastAPI application...")
    
    app = FastAPI(
        title="UptimeCheck MCP Server",
        version="1.0.0",
        description="MCP Server with Streamable HTTP Transport (2025-06-18)"
    )
    
    logger.info("FastAPI application created")
    return app
