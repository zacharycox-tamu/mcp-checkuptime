"""N8N-specific MCP endpoints for full compatibility."""
import json
from fastapi import FastAPI, Request, Response
from ..config import logger
from ..mcp_server import handle_list_tools, handle_call_tool


def register(app: FastAPI) -> None:
    """Register N8N-compatible MCP endpoints."""
    
    @app.post("/")
    async def root_mcp_endpoint(request: Request):
        """
        Root MCP endpoint for N8N HTTP Streamable transport.
        N8N sends MCP JSON-RPC requests to the base URL.
        """
        logger.info("=== Root MCP endpoint called (N8N HTTP Streamable) ===")
        
        try:
            body = await request.json()
            logger.info(f"MCP Request: {json.dumps(body)}")
            
            method = body.get("method", "")
            request_id = body.get("id", 1)
            params = body.get("params", {})
            
            # Handle initialize
            if method == "initialize":
                logger.info("Handling initialize request")
                
                # Get the protocol version requested by the client
                client_protocol = params.get("protocolVersion", "2025-06-18")
                logger.info(f"Client requested protocol version: {client_protocol}")
                
                # Support both N8N's older version and the latest
                # Respond with the client's requested version for compatibility
                supported_versions = ["2025-03-26", "2025-06-18"]
                protocol_version = client_protocol if client_protocol in supported_versions else "2025-06-18"
                
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": protocol_version,
                        "capabilities": {
                            "tools": {
                                "listChanged": True
                            }
                        },
                        "serverInfo": {
                            "name": "uptimecheck",
                            "version": "1.0.0"
                        }
                    }
                }
                logger.info(f"Initialize response: {json.dumps(response)}")
                return response
            
            # Handle tools/list
            elif method == "tools/list":
                logger.info("Handling tools/list request")
                tools = await handle_list_tools()
                tools_list = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema
                    }
                    for tool in tools
                ]
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": tools_list
                    }
                }
                logger.info(f"Tools list response: {len(tools_list)} tools")
                return response
            
            # Handle tools/call
            elif method == "tools/call":
                logger.info("Handling tools/call request")
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})
                
                logger.info(f"Calling tool: {tool_name} with args: {arguments}")
                result = await handle_call_tool(tool_name, arguments)
                
                # Convert TextContent to JSON-RPC format
                content = []
                for item in result:
                    content.append({
                        "type": "text",
                        "text": item.text
                    })
                
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": content
                    }
                }
                logger.info(f"Tool call response: {len(content)} content items")
                return response
            
            # Unknown method
            else:
                logger.warning(f"Unknown method: {method}")
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
        
        except Exception as e:
            logger.error(f"Error in root MCP endpoint: {e}", exc_info=True)
            return {
                "jsonrpc": "2.0",
                "id": 1,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    @app.options("/")
    async def root_options():
        """Handle CORS preflight for root endpoint."""
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            }
        )
    
    logger.info("N8N-compatible MCP endpoints registered")
