#!/usr/bin/env python3
"""Simple UptimeCheck MCP Server - Checks uptime (ping) and website (curl)."""
import os
import sys
import logging
import subprocess
import uuid
import platform
from datetime import datetime, timezone
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.streamable_http import (
    StreamableHTTPServerTransport,
    EventStore,
    MCP_PROTOCOL_VERSION_HEADER,
    CONTENT_TYPE_JSON,
    CONTENT_TYPE_SSE
)
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import (
    Tool, 
    TextContent, 
    ResourceLink, 
    ToolAnnotations,
    ServerCapabilities,
    ToolsCapability
)
import asyncio
import json
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("UptimeCheck-server")

# Initialize MCP server with latest capabilities
server = Server("uptimecheck")

# Server capabilities are automatically determined from registered handlers

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
            },
            annotations=ToolAnnotations(
                description="Network connectivity test using ICMP ping protocol"
            )
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
            },
            annotations=ToolAnnotations(
                description="HTTP/HTTPS connectivity test using curl"
            )
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls with structured output and resource links."""
    if name == "ping_host":
        host = arguments.get("host", "")
        logger.info(f"Pinging host: {host}")
        if not host.strip():
            return [TextContent(
                type="text", 
                text="[ERROR] Host is required"
            )]
        try:
            # Detect OS and use appropriate ping syntax
            system = platform.system().lower()
            if system == "windows":
                # Windows: -n count, -w timeout_ms
                cmd = f"ping -n 3 -w 5000 {host}"
            else:
                # Linux/Unix: -c count, -W timeout_sec
                cmd = f"ping -c 3 -W 5 {host}"
            
            logger.info(f"Executing command on {system}: {cmd}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=20, shell=True)
            logger.info(f"Ping result - Return code: {result.returncode}, stdout length: {len(result.stdout)}, stderr length: {len(result.stderr)}")
            
            if result.returncode == 0:
                return [TextContent(
                    type="text", 
                    text=f"[SUCCESS] Host {host} is reachable!\n{result.stdout}"
                )]
            else:
                # Log the error for debugging
                logger.warning(f"Ping failed for {host}. Return code: {result.returncode}")
                logger.warning(f"Stderr: {result.stderr}")
                logger.warning(f"Stdout: {result.stdout}")
                return [TextContent(
                    type="text", 
                    text=f"[ERROR] Cannot reach {host}.\nReturn code: {result.returncode}\nStdout: {result.stdout}\nStderr: {result.stderr}"
                )]
        except subprocess.TimeoutExpired:
            logger.error(f"Ping command timed out for {host}")
            return [TextContent(
                type="text", 
                text=f"[TIMEOUT] Ping timed out after 20 seconds for {host}"
            )]
        except Exception as e:
            logger.error(f"Error pinging {host}: {e}", exc_info=True)
            return [TextContent(
                type="text", 
                text=f"[ERROR] {str(e)}"
            )]
    
    elif name == "check_website":
        url = arguments.get("url", "")
        logger.info(f"Checking website: {url}")
        if not url.strip():
            return [TextContent(
                type="text", 
                text="[ERROR] URL is required"
            )]
        try:
            cmd = f"curl -s -o /dev/null -w '%{{http_code}}' --max-time 8 {url}"
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, shell=True)
            code = result.stdout.strip().strip("'\"")
            if code and (code.startswith("2") or code.startswith("3")):
                return [TextContent(
                    type="text", 
                    text=f"[SUCCESS] Website {url} is up! HTTP status: {code}"
                )]
            else:
                return [TextContent(
                    type="text", 
                    text=f"[ERROR] Website {url} is down or unreachable. HTTP status: {code}"
                )]
        except subprocess.TimeoutExpired:
            return [TextContent(
                type="text", 
                text="[TIMEOUT] Website check timed out"
            )]
        except Exception as e:
            logger.error(f"Error checking website {url}: {e}")
            return [TextContent(
                type="text", 
                text=f"[ERROR] {str(e)}"
            )]
    
    else:
        return [TextContent(type="text", text=f"[ERROR] Unknown tool: {name}")]

# === STREAMABLE HTTP TRANSPORT ===

# Create event store for session management
class SimpleEventStore(EventStore):
    def __init__(self):
        self.events = []
    
    async def store_event(self, event_id: str, event_data: dict):
        """Store an event."""
        self.events.append((event_id, event_data))
        logger.debug(f"Stored event {event_id}: {event_data}")
    
    async def replay_events_after(self, event_id: str):
        """Replay events after a given event ID."""
        # Simple implementation - return all events after the given ID
        for stored_id, event_data in self.events:
            if stored_id > event_id:
                yield event_data

event_store = SimpleEventStore()

# Create security settings
security_settings = TransportSecuritySettings(
    allowed_origins=["http://localhost:*", "https://localhost:*", "http://127.0.0.1:*", "https://127.0.0.1:*"]
)

# Create FastAPI app for Streamable HTTP Transport
app = FastAPI(
    title="UptimeCheck MCP Server", 
    version="1.0.0",
    description="MCP Server with Streamable HTTP Transport (2025-06-18)"
)

# Store active sessions
active_sessions = {}

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers and validate origin."""
    # Security: Validate Origin header to prevent DNS rebinding attacks
    origin = request.headers.get("origin")
    if origin and not any(origin.startswith(allowed) for allowed in ["http://localhost", "https://localhost", "http://127.0.0.1", "https://127.0.0.1"]):
        logger.warning(f"Suspicious origin header: {origin}")
    
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response

@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """Main MCP endpoint using Streamable HTTP Transport."""
    # Get or create session ID
    session_id = request.query_params.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Check if we have an active session
    if session_id not in active_sessions:
        # Create new transport for this session
        transport = StreamableHTTPServerTransport(
            mcp_session_id=session_id,
            is_json_response_enabled=True,
            event_store=event_store,
            security_settings=security_settings
        )
        
        # Connect the transport to the MCP server
        from mcp.server.streaming_asgi_transport import MemoryObjectReceiveStream, MemoryObjectSendStream
        read_stream = MemoryObjectReceiveStream()
        write_stream = MemoryObjectSendStream()
        
        # Start the server in the background
        asyncio.create_task(server.run(
            read_stream=read_stream,
            write_stream=write_stream,
            initialization_options={}
        ))
        
        # Connect the transport
        await transport.connect(read_stream, write_stream)
        
        active_sessions[session_id] = {
            'transport': transport,
            'read_stream': read_stream,
            'write_stream': write_stream
        }
        logger.info(f"Created new MCP session: {session_id}")
    
    session_data = active_sessions[session_id]
    transport = session_data['transport']
    
    # Handle the request
    try:
        # Get request body
        body = await request.body()
        
        # Process through transport
        response_data = await transport.handle_request(body)
        
        # Return response with proper headers
        return Response(
            content=response_data,
            media_type=CONTENT_TYPE_JSON,
            headers={
                MCP_PROTOCOL_VERSION_HEADER: "2025-06-18",
                "X-MCP-Session-ID": session_id
            }
        )
        
    except Exception as e:
        logger.error(f"Error handling MCP request: {e}")
        return Response(
            content=f'{{"error": "Internal server error: {str(e)}"}}',
            media_type=CONTENT_TYPE_JSON,
            status_code=500,
            headers={MCP_PROTOCOL_VERSION_HEADER: "2025-06-18"}
        )

@app.get("/mcp/stream")
async def mcp_stream_endpoint(request: Request):
    """SSE stream endpoint for long-running operations."""
    session_id = request.query_params.get("session_id")
    if not session_id or session_id not in active_sessions:
        return Response(
            content='{"error": "Invalid or missing session_id"}',
            media_type=CONTENT_TYPE_JSON,
            status_code=400
        )
    
    session_data = active_sessions[session_id]
    transport = session_data['transport']
    
    async def event_generator():
        try:
            # This would be implemented to stream events
            # For now, we'll return a simple message
            yield f"data: {json.dumps({'type': 'connected', 'session_id': session_id})}\n\n"
            
            # Keep connection alive
            while True:
                await asyncio.sleep(1)
                yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now().isoformat()})}\n\n"
                
        except Exception as e:
            logger.error(f"Error in SSE stream: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type=CONTENT_TYPE_SSE,
        headers={
            MCP_PROTOCOL_VERSION_HEADER: "2025-06-18",
            "X-MCP-Session-ID": session_id,
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )

# === LEGACY API ENDPOINTS (for backward compatibility) ===

@app.get("/")
async def root():
    return {
        "message": "UptimeCheck MCP Server with Streamable HTTP Transport", 
        "status": "running",
        "mcp_version": "2025-06-18",
        "transport": "streamable_http"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy", 
        "tools": ["ping_host", "check_website"],
        "mcp_version": "2025-06-18",
        "transport": "streamable_http",
        "capabilities": {
            "tools": True,
            "structured_output": True,
            "resource_links": True,
            "sessions": len(active_sessions)
        }
    }

@app.post("/debug")
async def debug_request(request: dict):
    """Debug endpoint to see what Open WebUI is sending"""
    return {
        "received_request": request,
        "request_keys": list(request.keys()) if isinstance(request, dict) else "Not a dict",
        "request_type": type(request).__name__,
        "available_tools": ["ping_host", "check_website"],
        "transport": "streamable_http"
    }

# Legacy endpoints for backward compatibility
@app.get("/ping")
async def ping_get(host: str = "google.com"):
    """Simple ping endpoint with GET method"""
    logger.info(f"Ping GET endpoint called with host: {host}")
    try:
        result = await handle_call_tool("ping_host", {"host": host})
        # Convert MCP TextContent to simple response for Open WebUI
        if result and len(result) > 0:
            return {"result": result[0].text, "host": host}
        else:
            return {"error": "No result from ping tool", "host": host}
    except Exception as e:
        logger.error(f"Error in ping GET: {e}")
        return {"error": f"Ping failed: {str(e)}", "host": host}

@app.post("/ping")
async def ping_endpoint(request: Request = None):
    """Simple ping endpoint for easier integration"""
    try:
        # Handle both dict and Request objects
        if request is None:
            host = "google.com"
        elif hasattr(request, 'json'):  # FastAPI Request object
            try:
                body = await request.json()
                host = body.get("host", "google.com") if body else "google.com"
            except:
                host = "google.com"
        else:  # dict object
            host = request.get("host", "google.com") if request else "google.com"
        
        logger.info(f"Ping endpoint called with host: {host}")
        result = await handle_call_tool("ping_host", {"host": host})
        
        # Convert MCP TextContent to simple response for Open WebUI
        if result and len(result) > 0:
            return {"result": result[0].text, "host": host}
        else:
            return {"error": "No result from ping tool", "host": host}
    except Exception as e:
        logger.error(f"Error in ping POST: {e}")
        return {"error": f"Ping failed: {str(e)}", "host": host}

@app.get("/check-website")
async def check_website_get(url: str = "https://google.com"):
    """Simple website check endpoint with GET method"""
    logger.info(f"Check website GET endpoint called with URL: {url}")
    try:
        result = await handle_call_tool("check_website", {"url": url})
        # Convert MCP TextContent to simple response for Open WebUI
        if result and len(result) > 0:
            return {"result": result[0].text, "url": url}
        else:
            return {"error": "No result from website check tool", "url": url}
    except Exception as e:
        logger.error(f"Error in check-website GET: {e}")
        return {"error": f"Website check failed: {str(e)}", "url": url}

@app.post("/check-website")
async def check_website_endpoint(request: Request = None):
    """Simple website check endpoint for easier integration"""
    try:
        # Handle both dict and Request objects
        if request is None:
            url = "https://google.com"
        elif hasattr(request, 'json'):  # FastAPI Request object
            try:
                body = await request.json()
                url = body.get("url", "https://google.com") if body else "https://google.com"
            except:
                url = "https://google.com"
        else:  # dict object
            url = request.get("url", "https://google.com") if request else "https://google.com"
        
        logger.info(f"Check website endpoint called with URL: {url}")
        result = await handle_call_tool("check_website", {"url": url})
        
        # Convert MCP TextContent to simple response for Open WebUI
        if result and len(result) > 0:
            return {"result": result[0].text, "url": url}
        else:
            return {"error": "No result from website check tool", "url": url}
    except Exception as e:
        logger.error(f"Error in check-website POST: {e}")
        return {"error": f"Website check failed: {str(e)}", "url": url}

@app.post("/tools/list")
async def list_tools():
    tools = await handle_list_tools()
    # Convert to Open WebUI format
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
    """GET endpoint for tools list"""
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
        
        # Convert MCP TextContent to simple response for Open WebUI
        if result and len(result) > 0:
            return {"result": result[0].text, "tool": name, "arguments": arguments}
        else:
            return {"error": f"No result from tool {name}", "tool": name, "arguments": arguments}
        
    except Exception as e:
        logger.error(f"Error in call_tool: {e}")
        return {"error": f"Failed to call tool: {str(e)}", "received": request}

# === SERVER STARTUP ===

if __name__ == "__main__":
    # Get host and port from environment variables
    host = os.getenv('MCP_HOST', '0.0.0.0')
    port = int(os.getenv('MCP_PORT', '9000'))
    
    logger.info(f"Starting UptimeCheck MCP server with Streamable HTTP Transport on {host}:{port}...")
    try:
        # Run with uvicorn
        uvicorn.run(app, host=host, port=port)
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
