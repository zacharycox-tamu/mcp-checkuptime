"""Legacy API endpoints for backward compatibility (N8N, Open WebUI)."""
from fastapi import FastAPI, Request
from ..config import logger
from ..mcp_server import handle_call_tool, handle_list_tools


def register(app: FastAPI) -> None:
    """Register legacy/compatibility endpoints."""
    
    @app.get("/info")
    async def server_info():
        """Server information endpoint (moved from root for N8N compatibility)."""
        return {
            "message": "UptimeCheck MCP Server with Streamable HTTP Transport",
            "status": "running",
            "mcp_version": "2025-06-18",
            "transport": "streamable_http",
            "documentation": "/docs",
            "openapi": "/openapi.json"
        }

    @app.get("/openapi.json")
    async def openapi_spec():
        """OpenAPI specification for N8N compatibility."""
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "UptimeCheck MCP Server",
                "version": "1.0.0",
                "description": "MCP Server for network uptime checks - ping and website monitoring"
            },
            "servers": [
                {"url": "http://localhost:9000", "description": "Local server"}
            ],
            "paths": {
                "/ping": {
                    "get": {
                        "summary": "Ping a host",
                        "parameters": [{
                            "name": "host",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string", "default": "google.com"}
                        }],
                        "responses": {"200": {"description": "Ping result"}}
                    },
                    "post": {
                        "summary": "Ping a host",
                        "requestBody": {
                            "content": {"application/json": {"schema": {"type": "object", "properties": {"host": {"type": "string"}}}}}
                        },
                        "responses": {"200": {"description": "Ping result"}}
                    }
                },
                "/check-website": {
                    "get": {"summary": "Check website availability", "responses": {"200": {"description": "Website check result"}}},
                    "post": {"summary": "Check website availability", "responses": {"200": {"description": "Website check result"}}}
                },
                "/mcp": {"post": {"summary": "MCP Protocol endpoint", "responses": {"200": {"description": "MCP response"}}}},
                "/sse": {"get": {"summary": "Server-Sent Events endpoint", "responses": {"200": {"description": "SSE stream"}}}}
            }
        }

    @app.get("/health")
    async def health():
        """Health check endpoint with server capabilities."""
        from ..api.mcp_endpoints import active_sessions
        return {
            "status": "healthy",
            "tools": ["ping_host", "check_website"],
            "mcp_version": "2025-06-18",
            "transport": "streamable_http",
            "compatibility": {
                "open_webui": True,
                "n8n": True,
                "claude_desktop": True
            },
            "endpoints": {
                "sse": "/sse",
                "mcp": "/mcp",
                "initialize": "/initialize",
                "tools_list": "/tools/list",
                "tools_call": "/tools/call"
            },
            "capabilities": {
                "tools": True,
                "structured_output": True,
                "resource_links": True,
                "sse_streaming": True,
                "cors_enabled": True,
                "sessions": len(active_sessions)
            }
        }

    @app.post("/debug")
    async def debug_request(request: dict):
        """Debug endpoint to see what Open WebUI is sending."""
        return {
            "received_request": request,
            "request_keys": list(request.keys()) if isinstance(request, dict) else "Not a dict",
            "request_type": type(request).__name__,
            "available_tools": ["ping_host", "check_website"],
            "transport": "streamable_http"
        }

    # === PING ENDPOINTS ===

    @app.get("/ping")
    async def ping_get(host: str = "google.com"):
        """Simple ping endpoint with GET method."""
        logger.info(f"Ping GET endpoint called with host: {host}")
        try:
            result = await handle_call_tool("ping_host", {"host": host})
            if result and len(result) > 0:
                return {"result": result[0].text, "host": host}
            else:
                return {"error": "No result from ping tool", "host": host}
        except Exception as e:
            logger.error(f"Error in ping GET: {e}")
            return {"error": f"Ping failed: {str(e)}", "host": host}

    @app.post("/ping")
    async def ping_endpoint(request: Request = None):
        """Simple ping endpoint for easier integration."""
        try:
            if request is None:
                host = "google.com"
            elif hasattr(request, 'json'):
                try:
                    body = await request.json()
                    host = body.get("host", "google.com") if body else "google.com"
                except:
                    host = "google.com"
            else:
                host = request.get("host", "google.com") if request else "google.com"
            
            logger.info(f"Ping endpoint called with host: {host}")
            result = await handle_call_tool("ping_host", {"host": host})
            
            if result and len(result) > 0:
                return {"result": result[0].text, "host": host}
            else:
                return {"error": "No result from ping tool", "host": host}
        except Exception as e:
            logger.error(f"Error in ping POST: {e}")
            return {"error": f"Ping failed: {str(e)}", "host": host}

    # === WEBSITE CHECK ENDPOINTS ===

    @app.get("/check-website")
    async def check_website_get(url: str = "https://google.com"):
        """Simple website check endpoint with GET method."""
        logger.info(f"Check website GET endpoint called with URL: {url}")
        try:
            result = await handle_call_tool("check_website", {"url": url})
            if result and len(result) > 0:
                return {"result": result[0].text, "url": url}
            else:
                return {"error": "No result from website check tool", "url": url}
        except Exception as e:
            logger.error(f"Error in check-website GET: {e}")
            return {"error": f"Website check failed: {str(e)}", "url": url}

    @app.post("/check-website")
    async def check_website_endpoint(request: Request = None):
        """Simple website check endpoint for easier integration."""
        try:
            if request is None:
                url = "https://google.com"
            elif hasattr(request, 'json'):
                try:
                    body = await request.json()
                    url = body.get("url", "https://google.com") if body else "https://google.com"
                except:
                    url = "https://google.com"
            else:
                url = request.get("url", "https://google.com") if request else "https://google.com"
            
            logger.info(f"Check website endpoint called with URL: {url}")
            result = await handle_call_tool("check_website", {"url": url})
            
            if result and len(result) > 0:
                return {"result": result[0].text, "url": url}
            else:
                return {"error": "No result from website check tool", "url": url}
        except Exception as e:
            logger.error(f"Error in check-website POST: {e}")
            return {"error": f"Website check failed: {str(e)}", "url": url}

    # === TOOLS ENDPOINTS ===

    @app.post("/tools/list")
    async def list_tools():
        """List all available MCP tools."""
        tools = await handle_list_tools()
        return {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                }
                for tool in tools
            ]
        }

    @app.get("/tools")
    async def get_tools():
        """GET endpoint for tools list."""
        tools = await handle_list_tools()
        return {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                }
                for tool in tools
            ]
        }

    @app.post("/tools/call")
    async def call_tool(request: dict):
        """Execute an MCP tool with flexible format support."""
        try:
            # Handle different request formats
            if "name" in request and "arguments" in request:
                name = request.get("name")
                arguments = request.get("arguments", {})
            elif "tool_name" in request:
                name = request.get("tool_name")
                arguments = request.get("params", {})
            elif "function" in request:
                name = request.get("function")
                arguments = request.get("parameters", {})
            else:
                name = request.get("name")
                if not name:
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
            result = await handle_call_tool(name, arguments)
            
            if result and len(result) > 0:
                return {"result": result[0].text, "tool": name, "arguments": arguments}
            else:
                return {"error": f"No result from tool {name}", "tool": name, "arguments": arguments}
            
        except Exception as e:
            logger.error(f"Error in call_tool: {e}")
            return {"error": f"Failed to call tool: {str(e)}", "received": request}
    
    logger.info("Legacy API endpoints registered")
