#!/usr/bin/env python3
"""Simple UptimeCheck MCP Server - Checks uptime (ping) and website (curl)."""
import os
import sys
import logging
import subprocess
from datetime import datetime, timezone
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import asyncio

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("UptimeCheck-server")

# Initialize MCP server
server = Server("uptimecheck")

# === MCP TOOLS ===

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="ping_host",
            description="Ping a host to check network uptime (ICMP).",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {
                        "type": "string",
                        "description": "Hostname or IP address to ping"
                    }
                },
                "required": ["host"]
            }
        ),
        Tool(
            name="check_website",
            description="Check if a website is up using curl (HTTP/HTTPS).",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to check"
                    }
                },
                "required": ["url"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    if name == "ping_host":
        host = arguments.get("host", "")
        logger.info(f"Pinging host: {host}")
        if not host.strip():
            return [TextContent(type="text", text="❌ Error: Host is required")]
        try:
            cmd = f"ping -c 3 -W 2 {host}"
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, shell=True)
            if result.returncode == 0:
                return [TextContent(type="text", text=f"✅ Host {host} is reachable!\n{result.stdout}")]
            else:
                return [TextContent(type="text", text=f"❌ Cannot reach {host}.\n{result.stderr}")]
        except subprocess.TimeoutExpired:
            return [TextContent(type="text", text="⏱️ Ping timed out")]
        except Exception as e:
            logger.error(f"Error pinging {host}: {e}")
            return [TextContent(type="text", text=f"❌ Error: {str(e)}")]
    
    elif name == "check_website":
        url = arguments.get("url", "")
        logger.info(f"Checking website: {url}")
        if not url.strip():
            return [TextContent(type="text", text="❌ Error: URL is required")]
        try:
            cmd = f"curl -s -o /dev/null -w '%{{http_code}}' --max-time 8 {url}"
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, shell=True)
            code = result.stdout.strip()
            if code and (code.startswith("2") or code.startswith("3")):
                return [TextContent(type="text", text=f"✅ Website {url} is up! HTTP status: {code}")]
            else:
                return [TextContent(type="text", text=f"❌ Website {url} is down or unreachable. HTTP status: {code}")]
        except subprocess.TimeoutExpired:
            return [TextContent(type="text", text="⏱️ Website check timed out")]
        except Exception as e:
            logger.error(f"Error checking website {url}: {e}")
            return [TextContent(type="text", text=f"❌ Error: {str(e)}")]
    
    else:
        return [TextContent(type="text", text=f"❌ Unknown tool: {name}")]

# === SERVER STARTUP ===

if __name__ == "__main__":
    # Get host and port from environment variables
    host = os.getenv('MCP_HOST', '0.0.0.0')
    port = int(os.getenv('MCP_PORT', '9000'))
    
    logger.info(f"Starting UptimeCheck MCP server on {host}:{port}...")
    try:
        # Use uvicorn with a simple HTTP server
        import uvicorn
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        
        # Create FastAPI app
        app = FastAPI(title="UptimeCheck MCP Server", version="1.0.0")
        
        @app.get("/")
        async def root():
            return {"message": "UptimeCheck MCP Server", "status": "running"}
        
        @app.get("/health")
        async def health():
            return {"status": "healthy", "tools": ["ping_host", "check_website"]}
        
        @app.post("/debug")
        async def debug_request(request: dict):
            """Debug endpoint to see what Open WebUI is sending"""
            return {
                "received_request": request,
                "request_keys": list(request.keys()) if isinstance(request, dict) else "Not a dict",
                "request_type": type(request).__name__,
                "available_tools": ["ping_host", "check_website"]
            }
        
        @app.get("/ping")
        async def ping_get(host: str = "google.com"):
            """Simple ping endpoint with GET method"""
            logger.info(f"Ping GET endpoint called with host: {host}")
            return await handle_call_tool("ping_host", {"host": host})
        
        @app.post("/ping")
        async def ping_endpoint(request: dict = None):
            """Simple ping endpoint for easier integration"""
            # Handle case where no request body is sent
            if request is None:
                request = {}
            
            host = request.get("host", "google.com")
            logger.info(f"Ping endpoint called with host: {host} (request: {request})")
            return await handle_call_tool("ping_host", {"host": host})
        
        @app.get("/check-website")
        async def check_website_get(url: str = "https://google.com"):
            """Simple website check endpoint with GET method"""
            logger.info(f"Check website GET endpoint called with URL: {url}")
            return await handle_call_tool("check_website", {"url": url})
        
        @app.post("/check-website")
        async def check_website_endpoint(request: dict = None):
            """Simple website check endpoint for easier integration"""
            # Handle case where no request body is sent
            if request is None:
                request = {}
                
            url = request.get("url", "https://google.com")
            logger.info(f"Check website endpoint called with URL: {url} (request: {request})")
            return await handle_call_tool("check_website", {"url": url})
        
        @app.post("/tools/list")
        async def list_tools():
            return await handle_list_tools()
        
        @app.post("/tools/call")
        async def call_tool(request: dict):
            try:
                # Handle different request formats
                if "name" in request and "arguments" in request:
                    # Standard MCP format
                    name = request.get("name")
                    arguments = request.get("arguments", {})
                elif "tool_name" in request:
                    # Alternative format
                    name = request.get("tool_name")
                    arguments = request.get("params", {})
                elif "function" in request:
                    # Another possible format
                    name = request.get("function")
                    arguments = request.get("parameters", {})
                else:
                    # Try to extract from the request directly
                    name = request.get("name")
                    if not name:
                        # Look for common tool names in the request
                        if "ping" in str(request).lower():
                            name = "ping_host"
                            arguments = {"host": request.get("host", "google.com")}
                        elif "website" in str(request).lower() or "url" in str(request).lower():
                            name = "check_website"
                            arguments = {"url": request.get("url", "https://google.com")}
                        else:
                            return {"error": "No tool name found in request", "received": request}
                    else:
                        arguments = request.get("arguments", request.get("params", request.get("parameters", {})))
                
                if not name:
                    return {"error": "Tool name is required", "received": request}
                
                logger.info(f"Calling tool: {name} with arguments: {arguments}")
                return await handle_call_tool(name, arguments)
                
            except Exception as e:
                logger.error(f"Error in call_tool: {e}")
                return {"error": f"Failed to call tool: {str(e)}", "received": request}
        
        # Run with uvicorn
        uvicorn.run(app, host=host, port=port)
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
