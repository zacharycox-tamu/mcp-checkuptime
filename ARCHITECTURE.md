# UptimeCheck MCP Server - Architecture Flow

Complete diagram showing the flow from Docker container start to tool execution.

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DOCKER CONTAINER                                   │
│                                                                             │
│  Dockerfile CMD: python uptimecheck_modular.py                             │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │
                              ▼
╔═════════════════════════════════════════════════════════════════════════════╗
║  STEP 1: Entry Point - uptimecheck_modular.py                              ║
╠═════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║  def main():                                                                ║
║      1. Import configuration                                                ║
║      2. app = create_app()                                                  ║
║      3. setup_middleware(app)                                               ║
║      4. register_endpoints(app)                                             ║
║      5. uvicorn.run(app)                                                    ║
║                                                                             ║
╚═════════════════════════════════════════════════════════════════════════════╝
         │                    │                    │                    │
         │                    │                    │                    │
         ▼                    ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐
│  STEP 2:        │  │  STEP 3:        │  │  STEP 4:        │  │  STEP 5:     │
│  Configuration  │  │  Create App     │  │  Middleware     │  │  Endpoints   │
└─────────────────┘  └─────────────────┘  └─────────────────┘  └──────────────┘




╔═════════════════════════════════════════════════════════════════════════════╗
║  STEP 2: Configuration - src/config.py                                     ║
╠═════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║  ┌───────────────────────────────────────────────────────────┐            ║
║  │  Environment Variables                                     │            ║
║  │  • LOG_LEVEL = 'DEBUG'                                     │            ║
║  │  • MCP_HOST = '0.0.0.0'                                    │            ║
║  │  • MCP_PORT = 9000                                         │            ║
║  │  • BEARER_TOKEN = '' (optional)                            │            ║
║  └───────────────────────────────────────────────────────────┘            ║
║                           ↓                                                 ║
║  ┌───────────────────────────────────────────────────────────┐            ║
║  │  Setup Logging                                             │            ║
║  │  logger = logging.getLogger("UptimeCheck-server")          │            ║
║  │  Format: timestamp - name - level - [file:line] - func()  │            ║
║  └───────────────────────────────────────────────────────────┘            ║
║                           ↓                                                 ║
║  ┌───────────────────────────────────────────────────────────┐            ║
║  │  Authentication Config                                     │            ║
║  │  AUTH_ENABLED = bool(BEARER_TOKEN)                         │            ║
║  └───────────────────────────────────────────────────────────┘            ║
║                                                                             ║
║  Exports: logger, MCP_HOST, MCP_PORT, AUTH_ENABLED, BEARER_TOKEN          ║
╚═════════════════════════════════════════════════════════════════════════════╝
                              │
                              ▼




╔═════════════════════════════════════════════════════════════════════════════╗
║  STEP 3: Create FastAPI App - src/api/app.py                              ║
╠═════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║  def create_app() -> FastAPI:                                              ║
║      app = FastAPI(                                                         ║
║          title="UptimeCheck MCP Server",                                    ║
║          version="1.0.0",                                                   ║
║          description="MCP Server with Streamable HTTP"                      ║
║      )                                                                      ║
║      return app                                                             ║
║                                                                             ║
║  Returns: FastAPI application instance                                     ║
╚═════════════════════════════════════════════════════════════════════════════╝
                              │
                              ▼




╔═════════════════════════════════════════════════════════════════════════════╗
║  STEP 4: Setup Middleware - src/api/middleware.py                         ║
╠═════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║  def setup_middleware(app: FastAPI):                                       ║
║                                                                             ║
║      @app.middleware("http")                                               ║
║      async def add_security_headers(request, call_next):                   ║
║                                                                             ║
║          ┌─────────────────────────────────────────────────┐              ║
║          │  1. Log Request                                  │              ║
║          │     - Method, path, headers, params              │              ║
║          └──────────────────┬──────────────────────────────┘              ║
║                             ▼                                               ║
║          ┌─────────────────────────────────────────────────┐              ║
║          │  2. Handle CORS Preflight (OPTIONS)             │              ║
║          │     - Return 200 with CORS headers              │              ║
║          └──────────────────┬──────────────────────────────┘              ║
║                             ▼                                               ║
║          ┌─────────────────────────────────────────────────┐              ║
║          │  3. Check Authentication (if enabled)           │              ║
║          │     if AUTH_ENABLED:                            │              ║
║          │         - Check Authorization header            │              ║
║          │         - Validate Bearer token                 │              ║
║          │         - Return 401/403 if invalid             │              ║
║          └──────────────────┬──────────────────────────────┘              ║
║                             ▼                                               ║
║          ┌─────────────────────────────────────────────────┐              ║
║          │  4. Process Request                             │              ║
║          │     response = await call_next(request)         │              ║
║          └──────────────────┬──────────────────────────────┘              ║
║                             ▼                                               ║
║          ┌─────────────────────────────────────────────────┐              ║
║          │  5. Add Security Headers                        │              ║
║          │     - Access-Control-Allow-Origin: *            │              ║
║          │     - X-Accel-Buffering: no                     │              ║
║          │     - Cache-Control: no-cache                   │              ║
║          └──────────────────┬──────────────────────────────┘              ║
║                             ▼                                               ║
║                      return response                                        ║
║                                                                             ║
╚═════════════════════════════════════════════════════════════════════════════╝
                              │
                              ▼




╔═════════════════════════════════════════════════════════════════════════════╗
║  STEP 5: Register Endpoints - src/api/endpoints.py                        ║
╠═════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║  def register_endpoints(app: FastAPI):                                     ║
║                                                                             ║
║      ┌──────────────────────────────────────────────────────┐             ║
║      │  1. n8n_mcp_endpoints.register(app)                  │             ║
║      │     Registers: POST /                                │             ║
║      │     Purpose: N8N HTTP Streamable compatibility       │             ║
║      └────────────────────┬─────────────────────────────────┘             ║
║                           ▼                                                 ║
║      ┌──────────────────────────────────────────────────────┐             ║
║      │  2. mcp_endpoints.register(app)                      │             ║
║      │     Registers: POST /initialize, /mcp, /sse         │             ║
║      │     Purpose: Standard MCP protocol endpoints         │             ║
║      └────────────────────┬─────────────────────────────────┘             ║
║                           ▼                                                 ║
║      ┌──────────────────────────────────────────────────────┐             ║
║      │  3. legacy_endpoints.register(app)                   │             ║
║      │     Registers: /ping, /check-website, /health, etc. │             ║
║      │     Purpose: Direct tool access, backward compat    │             ║
║      └──────────────────────────────────────────────────────┘             ║
║                                                                             ║
╚═════════════════════════════════════════════════════════════════════════════╝
         │                           │                           │
         │                           │                           │
         ▼                           ▼                           ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  N8N Endpoints   │    │  MCP Endpoints   │    │ Legacy Endpoints │
└──────────────────┘    └──────────────────┘    └──────────────────┘




╔═════════════════════════════════════════════════════════════════════════════╗
║  STEP 6A: N8N MCP Endpoints - src/api/n8n_mcp_endpoints.py                ║
╠═════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║  ┌────────────────────────────────────────────────────────────────┐       ║
║  │  from ..mcp_server import handle_list_tools, handle_call_tool  │  ⚡   ║
║  │                                                                  │       ║
║  │  This is the connection to mcp_server.py!                       │       ║
║  └────────────────────────────────────────────────────────────────┘       ║
║                                                                             ║
║  def register(app: FastAPI):                                               ║
║                                                                             ║
║      @app.post("/")                                                        ║
║      async def root_mcp_endpoint(request: Request):                        ║
║          body = await request.json()                                       ║
║          method = body.get("method")                                       ║
║                                                                             ║
║          ┌─────────────────────────────────────────────────┐              ║
║          │  if method == "initialize":                      │              ║
║          │      • Get client protocol version               │              ║
║          │      • Support 2025-03-26 (N8N) or 2025-06-18   │              ║
║          │      • Return capabilities + serverInfo          │              ║
║          └─────────────────────────────────────────────────┘              ║
║                                                                             ║
║          ┌─────────────────────────────────────────────────┐              ║
║          │  elif method == "tools/list":                    │              ║
║          │      tools = await handle_list_tools() ────────┐│              ║
║          │      • Format as JSON-RPC response              ││              ║
║          │      • Return list of tools                     ││              ║
║          └─────────────────────────────────────────────────┘│              ║
║                                                              │              ║
║          ┌─────────────────────────────────────────────────┐│              ║
║          │  elif method == "tools/call":                    ││             ║
║          │      result = await handle_call_tool() ─────────┼┘             ║
║          │      • Format result as JSON-RPC response        │              ║
║          │      • Return tool execution result              │              ║
║          └──────────────────────────────────────────────────┘              ║
║                                                        │                    ║
╚════════════════════════════════════════════════════════│════════════════════╝
                                                         │
                                                         │
                    ┌────────────────────────────────────┘
                    │
                    ▼




╔═════════════════════════════════════════════════════════════════════════════╗
║  STEP 6B: MCP Core - src/mcp_server.py                                    ║
║                                                                             ║
║  ★★★ THE HEART OF THE MCP SERVER ★★★                                      ║
╠═════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║  ┌────────────────────────────────────────────────────────────┐           ║
║  │  from mcp.server import Server                              │           ║
║  │  from mcp.types import Tool, TextContent                    │           ║
║  │  from .mcp_tools import ping_host, check_website            │  ⚡       ║
║  └────────────────────────────────────────────────────────────┘           ║
║                                                                             ║
║  server = Server("uptimecheck")  # Create MCP server instance             ║
║                                                                             ║
║  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓               ║
║  ┃  @server.list_tools()                                   ┃               ║
║  ┃  async def handle_list_tools() -> list[Tool]:           ┃               ║
║  ┃                                                          ┃               ║
║  ┃      return [                                            ┃               ║
║  ┃          Tool(                                           ┃               ║
║  ┃              name="ping_host",                           ┃               ║
║  ┃              description="Ping a host to check uptime",  ┃               ║
║  ┃              inputSchema={                               ┃               ║
║  ┃                  "type": "object",                       ┃               ║
║  ┃                  "properties": {                         ┃               ║
║  ┃                      "host": {                           ┃               ║
║  ┃                          "type": "string",               ┃               ║
║  ┃                          "description": "Host to ping"   ┃               ║
║  ┃                      }                                   ┃               ║
║  ┃                  },                                      ┃               ║
║  ┃                  "required": ["host"]                    ┃               ║
║  ┃              }                                            ┃               ║
║  ┃          ),                                              ┃               ║
║  ┃          Tool(                                           ┃               ║
║  ┃              name="check_website",                       ┃               ║
║  ┃              description="Check if website is up",       ┃               ║
║  ┃              inputSchema={ ... }                         ┃               ║
║  ┃          )                                               ┃               ║
║  ┃      ]                                                   ┃               ║
║  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛               ║
║                           ▲                                                 ║
║                           │                                                 ║
║                           │  Called by n8n_mcp_endpoints.py                ║
║                           │  when method == "tools/list"                   ║
║                                                                             ║
║  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓               ║
║  ┃  @server.call_tool()                                    ┃               ║
║  ┃  async def handle_call_tool(                            ┃               ║
║  ┃      name: str,                                         ┃               ║
║  ┃      arguments: dict                                    ┃               ║
║  ┃  ) -> list[TextContent]:                                ┃               ║
║  ┃                                                          ┃               ║
║  ┃      if name == "ping_host":                            ┃               ║
║  ┃          host = arguments.get("host", "")               ┃               ║
║  ┃          return await ping_host(host)  ─────────┐       ┃               ║
║  ┃                                                  │       ┃               ║
║  ┃      elif name == "check_website":              │       ┃               ║
║  ┃          url = arguments.get("url", "")         │       ┃               ║
║  ┃          return await check_website(url)  ──────┼───┐   ┃               ║
║  ┃                                                  │   │   ┃               ║
║  ┃      else:                                       │   │   ┃               ║
║  ┃          return [TextContent(                    │   │   ┃               ║
║  ┃              type="text",                        │   │   ┃               ║
║  ┃              text="[ERROR] Unknown tool"         │   │   ┃               ║
║  ┃          )]                                      │   │   ┃               ║
║  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│━━━│━━━┛               ║
║                           ▲                          │   │                   ║
║                           │                          │   │                   ║
║                           │  Called by n8n_mcp_endpoints.py                 ║
║                           │  when method == "tools/call"                    ║
║                                                      │   │                   ║
╚══════════════════════════════════════════════════════│═══│═══════════════════╝
                                                       │   │
                                                       │   │
                    ┌──────────────────────────────────┘   │
                    │                                      │
                    ▼                                      ▼




╔═════════════════════════════════╗  ╔════════════════════════════════════╗
║  STEP 6C: Tool Implementations  ║  ║  STEP 6C: Tool Implementations     ║
║                                 ║  ║                                    ║
║  src/mcp_tools/ping_tool.py    ║  ║  src/mcp_tools/website_tool.py    ║
╠═════════════════════════════════╣  ╠════════════════════════════════════╣
║                                 ║  ║                                    ║
║  async def ping_host(           ║  ║  async def check_website(          ║
║      host: str                  ║  ║      url: str                      ║
║  ) -> list[TextContent]:        ║  ║  ) -> list[TextContent]:           ║
║                                 ║  ║                                    ║
║  1. Validate input              ║  ║  1. Validate input                 ║
║     • Check if host is empty    ║  ║     • Check if URL is empty        ║
║                                 ║  ║                                    ║
║  2. Detect OS                   ║  ║  2. Build curl command             ║
║     • platform.system()         ║  ║     • curl -I -s -w "..."          ║
║     • Linux: ping -c 3 -W 5     ║  ║     • Follow redirects             ║
║     • Windows: ping -n 3 -w 5000║  ║     • Timeout: 10s                 ║
║                                 ║  ║                                    ║
║  3. Execute ping                ║  ║  3. Execute curl                   ║
║     • subprocess.run()          ║  ║     • subprocess.run()             ║
║     • timeout=10s               ║  ║     • timeout=15s                  ║
║     • capture_output=True       ║  ║     • capture_output=True          ║
║                                 ║  ║                                    ║
║  4. Parse output                ║  ║  4. Parse HTTP status              ║
║     • Check returncode          ║  ║     • Extract status code          ║
║     • Parse ping statistics     ║  ║     • Check 2xx/3xx = success      ║
║     • Extract packet loss       ║  ║     • Parse content type           ║
║                                 ║  ║                                    ║
║  5. Format response             ║  ║  5. Format response                ║
║     • [SUCCESS] or [ERROR]      ║  ║     • [SUCCESS] or [ERROR]         ║
║     • Include full output       ║  ║     • Include status + details     ║
║     • Handle timeouts           ║  ║     • Handle timeouts              ║
║                                 ║  ║                                    ║
║  6. Return TextContent          ║  ║  6. Return TextContent             ║
║     • type: "text"              ║  ║     • type: "text"                 ║
║     • text: formatted result    ║  ║     • text: formatted result       ║
║                                 ║  ║                                    ║
╚═════════════════════════════════╝  ╚════════════════════════════════════╝
         │                                        │
         │                                        │
         └────────────┬───────────────────────────┘
                      │
                      ▼
          ┌────────────────────────────┐
          │  External System Calls     │
          │  • ping (ICMP)             │
          │  • curl (HTTP/HTTPS)       │
          └────────────────────────────┘
                      │
                      ▼
          ┌────────────────────────────┐
          │  Network/Internet          │
          │  • Remote hosts            │
          │  • Websites                │
          └────────────────────────────┘




╔═════════════════════════════════════════════════════════════════════════════╗
║                         REQUEST/RESPONSE FLOW                               ║
╠═════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║  Client (N8N) sends request:                                               ║
║  ┌──────────────────────────────────────────────────────────────┐         ║
║  │  POST http://mcp-server:8080/                                 │         ║
║  │  Content-Type: application/json                               │         ║
║  │                                                                │         ║
║  │  {                                                             │         ║
║  │    "jsonrpc": "2.0",                                           │         ║
║  │    "method": "tools/call",                                     │         ║
║  │    "id": 1,                                                    │         ║
║  │    "params": {                                                 │         ║
║  │      "name": "ping_host",                                      │         ║
║  │      "arguments": {"host": "google.com"}                       │         ║
║  │    }                                                            │         ║
║  │  }                                                             │         ║
║  └──────────────────────────────────────────────────────────────┘         ║
║                            ↓                                                ║
║  ┌──────────────────────────────────────────────────────────────┐         ║
║  │  1. Docker receives on port 9000                              │         ║
║  │  2. Uvicorn → FastAPI app                                     │         ║
║  │  3. Middleware checks auth, logs request                      │         ║
║  │  4. Routes to: n8n_mcp_endpoints.root_mcp_endpoint()          │         ║
║  │  5. Parses JSON-RPC, calls: handle_call_tool()                │         ║
║  │  6. Executes: ping_host("google.com")                         │         ║
║  │  7. Runs: subprocess ping command                             │         ║
║  │  8. Returns: TextContent with result                          │         ║
║  │  9. Formats as JSON-RPC response                              │         ║
║  │ 10. Middleware adds CORS headers                              │         ║
║  │ 11. Returns to client                                         │         ║
║  └──────────────────────────────────────────────────────────────┘         ║
║                            ↓                                                ║
║  Server responds:                                                           ║
║  ┌──────────────────────────────────────────────────────────────┐         ║
║  │  HTTP/1.1 200 OK                                              │         ║
║  │  Content-Type: application/json                               │         ║
║  │  Access-Control-Allow-Origin: *                               │         ║
║  │                                                                │         ║
║  │  {                                                             │         ║
║  │    "jsonrpc": "2.0",                                           │         ║
║  │    "id": 1,                                                    │         ║
║  │    "result": {                                                 │         ║
║  │      "content": [                                              │         ║
║  │        {                                                       │         ║
║  │          "type": "text",                                       │         ║
║  │          "text": "[SUCCESS] Host google.com is reachable!..."  │         ║
║  │        }                                                       │         ║
║  │      ]                                                         │         ║
║  │    }                                                            │         ║
║  │  }                                                             │         ║
║  └──────────────────────────────────────────────────────────────┘         ║
║                                                                             ║
╚═════════════════════════════════════════════════════════════════════════════╝




╔═════════════════════════════════════════════════════════════════════════════╗
║                          KEY DESIGN DECISIONS                               ║
╠═════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║  1. Modular Architecture                                                    ║
║     • Separation of concerns (config, app, middleware, endpoints, tools)   ║
║     • Easy to test individual components                                   ║
║     • Simple to add new tools                                              ║
║                                                                             ║
║  2. Entry Point Order                                                       ║
║     • Config first (logging setup before anything else)                    ║
║     • App creation (FastAPI instance)                                      ║
║     • Middleware (applies to all routes)                                   ║
║     • Endpoint registration (N8N first for root path)                      ║
║                                                                             ║
║  3. MCP Server as Library                                                  ║
║     • mcp_server.py doesn't run standalone                                 ║
║     • Provides handle_list_tools() and handle_call_tool()                  ║
║     • Imported by endpoint handlers                                        ║
║                                                                             ║
║  4. Multiple Endpoint Styles                                               ║
║     • N8N: POST / (JSON-RPC, protocol negotiation)                         ║
║     • Standard MCP: POST /mcp, GET /sse                                    ║
║     • Legacy: POST /ping, /check-website (direct tool access)              ║
║                                                                             ║
║  5. Tool Implementation Pattern                                            ║
║     • Each tool: separate file in mcp_tools/                               ║
║     • Async functions for I/O operations                                   ║
║     • Consistent error handling                                            ║
║     • Returns list[TextContent]                                            ║
║                                                                             ║
╚═════════════════════════════════════════════════════════════════════════════╝




╔═════════════════════════════════════════════════════════════════════════════╗
║                          FILE DEPENDENCY TREE                               ║
╠═════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║  uptimecheck_modular.py (entry point)                                      ║
║      │                                                                      ║
║      ├─── src/config.py                                                    ║
║      │       • Logging, environment variables, auth config                 ║
║      │                                                                      ║
║      ├─── src/api/app.py                                                   ║
║      │       • create_app() → FastAPI instance                             ║
║      │                                                                      ║
║      ├─── src/api/middleware.py                                            ║
║      │       • setup_middleware()                                          ║
║      │       • Auth, CORS, security headers                                ║
║      │                                                                      ║
║      └─── src/api/endpoints.py                                             ║
║              • register_endpoints()                                         ║
║              │                                                              ║
║              ├─── src/api/n8n_mcp_endpoints.py                             ║
║              │       • POST / (N8N JSON-RPC handler)                        ║
║              │       • Imports from src/mcp_server.py                       ║
║              │                                                              ║
║              ├─── src/api/mcp_endpoints.py                                 ║
║              │       • POST /initialize, /mcp                               ║
║              │       • GET /sse                                             ║
║              │       • Imports from src/mcp_server.py                       ║
║              │                                                              ║
║              └─── src/api/legacy_endpoints.py                              ║
║                      • POST /ping, /check-website                           ║
║                      • GET /health, /info                                   ║
║                      • Direct tool access                                   ║
║                                                                             ║
║  src/mcp_server.py (MCP protocol core)                                     ║
║      │                                                                      ║
║      ├─── mcp.server.Server (external library)                             ║
║      │                                                                      ║
║      └─── src/mcp_tools/                                                   ║
║              │                                                              ║
║              ├─── ping_tool.py                                              ║
║              │       • ping_host() function                                 ║
║              │                                                              ║
║              └─── website_tool.py                                           ║
║                      • check_website() function                             ║
║                                                                             ║
╚═════════════════════════════════════════════════════════════════════════════╝
```

## Summary

**The flow in 6 steps:**

1. **Entry** → `uptimecheck_modular.py` starts everything
2. **Config** → `src/config.py` loads settings and logging
3. **App** → `src/api/app.py` creates FastAPI instance
4. **Middleware** → `src/api/middleware.py` adds auth/CORS/security
5. **Endpoints** → `src/api/endpoints.py` registers all routes
6. **Execution** → Routes call `src/mcp_server.py` which calls `src/mcp_tools/*`

**The magic connection:** `n8n_mcp_endpoints.py` imports `handle_list_tools()` and `handle_call_tool()` from `mcp_server.py`, which routes to the actual tool implementations!
