#!/usr/bin/env python3
"""
UptimeCheck MCP Server - Modular Implementation
Entry point for the refactored server with clean separation of concerns.
"""
import sys
import uvicorn
from src.config import logger, MCP_HOST, MCP_PORT, log_level
from src.api.app import create_app
from src.api.middleware import setup_middleware
from src.api.endpoints import register_endpoints


def main():
    """Main entry point for the server."""
    # Create FastAPI app
    app = create_app()
    
    # Setup middleware (auth, CORS, security)
    setup_middleware(app)
    
    # Register all endpoints (MCP + legacy)
    register_endpoints(app)
    
    # Log server configuration
    logger.info("=" * 80)
    logger.info(f"Starting UptimeCheck MCP server with Streamable HTTP Transport")
    logger.info(f"Host: {MCP_HOST}")
    logger.info(f"Port: {MCP_PORT}")
    logger.info(f"Transport: Streamable HTTP + SSE")
    logger.info(f"MCP Version: 2025-06-18")
    logger.info("=" * 80)
    logger.info("Available endpoints:")
    logger.info("  POST /initialize  - MCP handshake")
    logger.info("  POST /mcp         - MCP protocol (Streamable HTTP)")
    logger.info("  GET  /sse         - Server-Sent Events stream")
    logger.info("  POST /ping        - Direct ping tool")
    logger.info("  POST /check-website - Direct website check")
    logger.info("  GET  /health      - Health status")
    logger.info("  POST /tools/list  - List tools")
    logger.info("  POST /tools/call  - Call tool")
    logger.info("=" * 80)
    
    try:
        # Run with uvicorn
        logger.info(f"Launching uvicorn server...")
        uvicorn.run(
            app,
            host=MCP_HOST,
            port=MCP_PORT,
            log_level=log_level.lower(),
            access_log=True
        )
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
