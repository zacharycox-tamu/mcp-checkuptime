"""MCP Server implementation with tool handlers."""
from mcp.server import Server
from mcp.types import Tool, TextContent, ToolAnnotations
from .config import logger
from .mcp_tools import ping_host, check_website

# Initialize MCP server
server = Server("uptimecheck")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools."""
    logger.debug("handle_list_tools called")
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
    """Handle tool calls with structured output."""
    logger.debug(f"handle_call_tool called with name='{name}', arguments={arguments}")
    
    if name == "ping_host":
        host = arguments.get("host", "")
        return await ping_host(host)
    
    elif name == "check_website":
        url = arguments.get("url", "")
        return await check_website(url)
    
    else:
        logger.warning(f"Unknown tool requested: {name}")
        return [TextContent(type="text", text=f"[ERROR] Unknown tool: {name}")]
