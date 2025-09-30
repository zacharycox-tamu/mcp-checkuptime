# UptimeCheck MCP Server v2.0.0 - N8N Support Release

## 🎉 Major Achievement: Full N8N MCP Client Compatibility!

After extensive debugging and testing, the UptimeCheck MCP Server now **fully supports N8N's MCP Client Tool**!

### What's New

#### ✅ N8N Integration (The Main Event!)
- **Works with N8N v1.114.0+** and MCP Client Tool v1.2
- **Multi-protocol support**: Automatically negotiates between MCP `2025-03-26` (N8N) and `2025-06-18` (latest)
- **Both internal and external endpoints** supported:
  - Internal Kubernetes: `http://mcp-checkuptime.mcp.svc.cluster.local:8080`
  - External HTTPS: `https://your-domain.com`
- **HTTP Streamable transport** fully functional

#### 🏗️ Modular Architecture
Complete refactoring from monolithic to modular design:
```
src/
├── config.py           # Configuration & logging
├── mcp_server.py       # Core MCP logic
├── mcp_tools/         # Tool implementations
└── api/               # FastAPI endpoints
```

#### 🔐 Security & Auth
- Optional bearer token authentication
- Configurable via `BEARER_TOKEN` environment variable
- Authentication disabled by default for easy setup

#### ☸️ Kubernetes Native
- Traefik middleware for SSE/streaming support
- Proper ingress configuration with no-buffer settings
- Internal service discovery optimized
- CORS headers for cross-origin requests

### The Fix

The key issue was a **protocol version mismatch**:
- N8N MCP Client v1.2 uses MCP protocol `2025-03-26`
- Server was only responding with `2025-06-18`

**Solution**: Server now auto-negotiates protocol version based on client request.

### Verified Working

#### N8N Workflow
```
When chat message received
  ↓
AI Agent (GPT-4)
  ↓
MCP Client → UptimeCheck MCP Server
  ↓
Tools: ping_host, check_website
```

#### Configuration That Works
```
Endpoint: http://mcp-checkuptime.mcp.svc.cluster.local:8080
Server Transport: HTTP Streamable
Authentication: None
Tools to Include: All
```

### Installation & Upgrade

#### New Installation
```bash
git clone https://github.com/your-repo/mcp-checkuptime
cd mcp-checkuptime
docker-compose up -d
```

#### Upgrade from v1.x
```bash
git pull
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

#### Kubernetes Deployment
```bash
kubectl apply -f k8s/traefik-mcp-middleware.yaml
kubectl apply -f k8s/mcp-checkuptime-ingress.yaml
kubectl rollout restart deployment/mcp-checkuptime -n mcp
```

### Documentation

New comprehensive guides in `ai-docs/`:
- **[K8S_N8N_SETUP.md](./ai-docs/K8S_N8N_SETUP.md)** - Complete Kubernetes + N8N setup
- **[N8N_TROUBLESHOOTING_CONNECTION.md](./ai-docs/N8N_TROUBLESHOOTING_CONNECTION.md)** - Troubleshooting guide
- **[BEARER_TOKEN_AUTH.md](./ai-docs/BEARER_TOKEN_AUTH.md)** - Authentication setup
- **[CHANGELOG.md](./CHANGELOG.md)** - Full change log

### Compatibility Matrix

| Client | Version | Status | Transport |
|--------|---------|--------|-----------|
| N8N | 1.114.0+ | ✅ Working | HTTP Streamable |
| Open WebUI | Latest | ✅ Working | Direct API |
| Claude Desktop | Latest | ✅ Working | stdio |
| MCP Clients | 2025-03-26 | ✅ Working | HTTP/SSE |
| MCP Clients | 2025-06-18 | ✅ Working | HTTP/SSE |

### Breaking Changes

1. **Removed legacy files**:
   - `uptimecheck_server.py` (replaced by modular version)
   - `uptimecheck_fastmcp.py` (not needed)
   
2. **Endpoint changes**:
   - Root GET `/` moved to `/info`
   - Root POST `/` now handles MCP protocol (N8N compatible)

3. **Entry point**:
   - Use `uptimecheck_modular.py` instead of `uptimecheck_server.py`
   - Dockerfile CMD updated accordingly

### Migration Guide

If you're upgrading from v1.x:

1. **Update your imports/references**:
   - Old: `python uptimecheck_server.py`
   - New: `python uptimecheck_modular.py` (or just use Docker)

2. **Update Claude Desktop config** (if needed):
   ```json
   {
     "mcpServers": {
       "uptimecheck": {
         "command": "docker",
         "args": ["run", "--rm", "-i", "mcp-checkuptime", "python", "uptimecheck_modular.py"],
         "transport": "stdio"
       }
     }
   }
   ```

3. **No changes needed for**:
   - Docker Compose (handled automatically)
   - Kubernetes deployments (Dockerfile CMD updated)
   - Environment variables (all compatible)

### Performance & Reliability

- **Faster startup**: Modular architecture reduces initialization time
- **Better error handling**: Comprehensive logging at all levels
- **Connection stability**: Fixed SSE/streaming issues with Traefik
- **Resource usage**: Similar to v1.x (minimal overhead from refactoring)

### Known Issues & Limitations

None! All previous issues resolved:
- ✅ Protocol version mismatch - Fixed
- ✅ Traefik buffering - Fixed with middleware
- ✅ N8N connection errors - Fixed
- ✅ CORS issues - Fixed with proper headers

### Credits

This release was made possible through:
- Extensive N8N integration testing
- Community feedback and bug reports
- Protocol specification analysis
- Real-world Kubernetes deployment testing

### What's Next?

Future improvements planned:
- Additional network diagnostic tools
- Prometheus metrics endpoint
- WebSocket support for real-time monitoring
- More MCP client integrations

### Get Help

- **Issues**: https://github.com/your-repo/mcp-checkuptime/issues
- **Discussions**: https://github.com/your-repo/mcp-checkuptime/discussions
- **Documentation**: [./ai-docs/README.md](./ai-docs/README.md)

### Thank You!

Special thanks to everyone who tested and provided feedback during development!

---

**Download**: [v2.0.0 Release](https://github.com/your-repo/mcp-checkuptime/releases/tag/v2.0.0)

**Docker Image**: `your-registry/mcp-checkuptime:2.0.0`
