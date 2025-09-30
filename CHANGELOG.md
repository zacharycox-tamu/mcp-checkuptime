# Changelog

## v2.0.0 - N8N MCP Client Support (2025-09-30)

### 🎉 Major Features

- **Full N8N MCP Client compatibility** - Works with N8N v1.114.0+ and MCP Client Tool v1.2
- **Multi-protocol version support** - Supports both MCP protocol versions:
  - `2025-03-26` (N8N MCP Client)
  - `2025-06-18` (Latest MCP specification)
- **Kubernetes-native deployment** - Optimized for Kubernetes with Traefik ingress
- **Modular architecture** - Refactored into maintainable modules for better code organization

### ✅ N8N Integration

The server now fully supports N8N's MCP Client Tool node:

#### Internal Service (Recommended)
```
Endpoint: http://mcp-checkuptime.mcp.svc.cluster.local:8080
Server Transport: HTTP Streamable
Authentication: None (or Bearer if configured)
Tools to Include: All
```

#### External Access
```
Endpoint: https://mcp-checkuptime.your-domain.com
Server Transport: HTTP Streamable
Authentication: None (or Bearer if configured)
Tools to Include: All
```

### 🔧 Technical Improvements

#### MCP Protocol
- ✅ Root endpoint (`POST /`) for N8N HTTP Streamable transport
- ✅ Automatic protocol version negotiation
- ✅ Full MCP JSON-RPC 2.0 compliance
- ✅ Proper capability advertisement

#### Endpoints
- `POST /` - MCP protocol endpoint (N8N compatible)
- `POST /initialize` - MCP initialize (alternative)
- `POST /mcp` - MCP protocol (alternative)
- `GET /sse` - Server-Sent Events stream
- `POST /ping` - Direct ping tool (Open WebUI compatible)
- `POST /check-website` - Direct website check (Open WebUI compatible)
- `GET /health` - Health status
- `GET /info` - Server information
- `POST /tools/list` - List available tools
- `POST /tools/call` - Execute tools

#### Kubernetes Features
- ✅ Traefik middleware for SSE/streaming support
- ✅ Proper ingress configuration with no-buffer settings
- ✅ Internal service discovery
- ✅ CORS headers for cross-origin requests
- ✅ Optional bearer token authentication

#### Code Organization
```
src/
├── __init__.py
├── config.py                    # Logging & auth configuration
├── mcp_server.py               # Core MCP server logic
├── mcp_tools/
│   ├── __init__.py
│   ├── ping_tool.py           # Ping host tool
│   └── website_tool.py        # Website check tool
└── api/
    ├── __init__.py
    ├── app.py                  # FastAPI application
    ├── middleware.py           # CORS, security, auth
    ├── endpoints.py            # Endpoint registration
    ├── n8n_mcp_endpoints.py   # N8N-specific handlers
    ├── mcp_endpoints.py        # MCP protocol endpoints
    └── legacy_endpoints.py     # Backward compatibility
```

### 🐛 Bug Fixes

- Fixed protocol version mismatch with N8N MCP Client
- Fixed Docker port mapping for Windows compatibility
- Fixed Traefik buffering issues for SSE connections
- Fixed OS detection for ping commands (Linux vs Windows)
- Fixed Unicode encoding errors in ping output
- Fixed HTTP 405 errors on root endpoint

### 📚 Documentation

Added comprehensive documentation in `ai-docs/`:
- `K8S_N8N_SETUP.md` - Complete Kubernetes and N8N setup guide
- `N8N_TROUBLESHOOTING_CONNECTION.md` - Troubleshooting guide
- `BEARER_TOKEN_AUTH.md` - Authentication setup
- `AUTH_QUICK_START.md` - Quick authentication guide
- `MODULAR_REFACTOR.md` - Code refactoring documentation
- `SSE_STALLING_EXPLAINED.md` - SSE behavior explanation

### 🔐 Security

- Optional bearer token authentication
- CORS configuration
- Security headers middleware
- Non-root Docker user

### 🚀 Deployment

#### Docker Compose
```bash
docker-compose up -d
```

#### Kubernetes
```bash
# Deploy server
kubectl apply -f k8s/

# Apply Traefik middlewares
kubectl apply -f k8s/traefik-mcp-middleware.yaml

# Apply ingress
kubectl apply -f k8s/mcp-checkuptime-ingress.yaml
```

### ⚙️ Configuration

Environment variables:
- `MCP_HOST` - Server bind address (default: `0.0.0.0`)
- `MCP_PORT` - Server port (default: `9000`)
- `MCP_TRANSPORT` - Transport mode (default: `sse`)
- `LOG_LEVEL` - Logging level (default: `DEBUG`)
- `BEARER_TOKEN` - Optional authentication token
- `PYTHONUNBUFFERED` - Disable Python buffering (default: `1`)

### 🎯 Compatibility

#### Verified Working With:
- ✅ N8N v1.114.0+ (MCP Client Tool v1.2)
- ✅ Open WebUI (direct tool endpoints)
- ✅ Claude Desktop (stdio transport)
- ✅ Any MCP-compliant client

#### Protocol Versions:
- ✅ MCP 2025-03-26 (N8N)
- ✅ MCP 2025-06-18 (Latest)

### 📝 Breaking Changes

- Removed legacy monolithic server file (`uptimecheck_server.py`)
- Moved root GET endpoint from `/` to `/info`
- Restructured code into modular architecture

### 🙏 Acknowledgments

This release was made possible through extensive testing and debugging with:
- N8N MCP Client Tool
- Kubernetes + Traefik ingress
- Multiple MCP protocol versions

---

## v1.0.0 - Initial Release

Initial implementation with:
- Basic MCP server functionality
- Ping and website check tools
- Docker support
- MCP 2025-06-18 protocol support
