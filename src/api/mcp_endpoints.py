"""MCP protocol endpoints - Streamable HTTP and SSE."""
import uuid
import json
import asyncio
from datetime import datetime, timezone
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from mcp.server.streamable_http import (
    StreamableHTTPServerTransport,
    EventStore,
    MCP_PROTOCOL_VERSION_HEADER,
    CONTENT_TYPE_JSON,
    CONTENT_TYPE_SSE
)
from mcp.server.transport_security import TransportSecuritySettings
from ..config import logger
from ..mcp_server import server


# === EVENT STORE ===

class SimpleEventStore(EventStore):
    """Simple in-memory event store for session management."""
    
    def __init__(self):
        self.events = []
    
    async def store_event(self, event_id: str, event_data: dict):
        """Store an event."""
        self.events.append((event_id, event_data))
        logger.debug(f"Stored event {event_id}: {event_data}")
    
    async def replay_events_after(self, event_id: str):
        """Replay events after a given event ID."""
        for stored_id, event_data in self.events:
            if stored_id > event_id:
                yield event_data


# Create event store and security settings
event_store = SimpleEventStore()
security_settings = TransportSecuritySettings(
    allowed_origins=["http://localhost:*", "https://localhost:*", "http://127.0.0.1:*", "https://127.0.0.1:*"]
)

# Store active sessions
active_sessions = {}


def register(app: FastAPI) -> None:
    """Register MCP protocol endpoints."""
    
    @app.post("/initialize")
    async def initialize_endpoint(request: Request):
        """Initialize endpoint for N8N MCP Client handshake."""
        logger.info("=== /initialize endpoint called ===")
        try:
            body = await request.json()
            logger.info(f"Initialize request body: {body}")
            logger.debug(f"Request headers: {dict(request.headers)}")
            
            # Create session
            session_id = str(uuid.uuid4())
            logger.info(f"Created new session: {session_id}")
            
            # Return server capabilities
            response_data = {
                "jsonrpc": "2.0",
                "id": body.get("id", 1),
                "result": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {
                        "tools": {
                            "listChanged": True
                        }
                    },
                    "serverInfo": {
                        "name": "uptimecheck",
                        "version": "1.0.0"
                    },
                    "sessionId": session_id
                }
            }
            logger.info(f"Returning initialize response: {response_data}")
            return response_data
        except Exception as e:
            logger.error(f"Error in initialize: {e}", exc_info=True)
            return {
                "jsonrpc": "2.0",
                "id": 1,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }

    @app.post("/mcp")
    async def mcp_endpoint(request: Request):
        """Main MCP endpoint using Streamable HTTP Transport."""
        logger.info("=== /mcp endpoint called ===")
        logger.debug(f"Request headers: {dict(request.headers)}")
        logger.debug(f"Query params: {dict(request.query_params)}")
        
        # Get or create session ID
        session_id = request.query_params.get("session_id")
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.info(f"No session_id in query params, created new: {session_id}")
        else:
            logger.info(f"Using session_id from query params: {session_id}")
        
        # Check if we have an active session
        if session_id not in active_sessions:
            logger.info(f"Creating new transport for session: {session_id}")
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

    @app.get("/sse")
    async def sse_endpoint(request: Request):
        """SSE endpoint for N8N MCP Client Node compatibility."""
        logger.info("=== /sse endpoint called ===")
        logger.debug(f"Request headers: {dict(request.headers)}")
        logger.debug(f"Query params: {dict(request.query_params)}")
        
        # N8N expects SSE at /sse path
        session_id = request.query_params.get("session_id", str(uuid.uuid4()))
        
        logger.info(f"SSE connection requested for session: {session_id}")
        
        async def event_generator():
            try:
                # Send initial connection event
                yield f"data: {json.dumps({'type': 'connection', 'status': 'connected', 'session_id': session_id, 'mcp_version': '2025-06-18'})}\n\n"
                
                # Keep connection alive with heartbeats
                while True:
                    await asyncio.sleep(30)
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"
                    
            except asyncio.CancelledError:
                logger.info(f"SSE connection closed for session: {session_id}")
                raise
            except Exception as e:
                logger.error(f"Error in SSE stream: {e}")
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type=CONTENT_TYPE_SSE,
            headers={
                MCP_PROTOCOL_VERSION_HEADER: "2025-06-18",
                "X-MCP-Session-ID": session_id,
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            }
        )

    @app.get("/mcp/stream")
    async def mcp_stream_endpoint(request: Request):
        """SSE stream endpoint for long-running operations (legacy path)."""
        return await sse_endpoint(request)
    
    @app.get("/mcp/status")
    async def mcp_status():
        """MCP server status endpoint (non-streaming for connection testing)."""
        logger.info("=== /mcp/status endpoint called ===")
        return {
            "status": "ready",
            "protocol": "2025-06-18",
            "transport": "streamable_http",
            "sse_endpoint": "/sse",
            "capabilities": {
                "tools": {
                    "listChanged": True
                }
            },
            "serverInfo": {
                "name": "uptimecheck",
                "version": "1.0.0"
            },
            "tools": [
                {"name": "ping_host", "description": "Ping a host to check network uptime"},
                {"name": "check_website", "description": "Check if a website is up"}
            ]
        }
    
    logger.info("MCP protocol endpoints registered")
