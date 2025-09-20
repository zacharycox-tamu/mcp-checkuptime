# UptimeCheck MCP Server - Setup Guide
A Model Context Protocol (MCP) server that provides network uptime checking tools for Claude Desktop and Open WebUI. The server runs as both an MCP server and a standalone web API accessible on port 9000.

## Table of Contents
- [Prerequisites Installation](#prerequisites-installation)
  - [1. Install Docker Desktop](#1-install-docker-desktop)
    - [Windows](#windows)
    - [macOS](#macos)
    - [Linux](#linux)
  - [2. Install Docker MCP Plugin](#2-install-docker-mcp-plugin)
  - [3. Install Claude Desktop](#3-install-claude-desktop)
    - [Windows](#windows-1)
    - [macOS](#macos-1)
- [MCP Server Setup](#mcp-server-setup)
  - [1. Clone and Build](#1-clone-and-build)
  - [2. Configure Claude Desktop](#2-configure-claude-desktop)
  - [3. Test the Server](#3-test-the-server)
- [Web Server Mode](#web-server-mode)
  - [Running as Web API](#running-as-web-api)
  - [API Endpoints](#api-endpoints)
  - [Testing the Web API](#testing-the-web-api)
- [Open WebUI Integration](#open-webui-integration)
  - [Install Open WebUI](#install-open-webui)
  - [Configure MCP Server](#configure-mcp-server)
  - [Add to Open WebUI](#add-to-open-webui)
- [Available Tools](#available-tools)
  - [ping_host](#ping_host)
  - [check_website](#check_website)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

# Prerequisites Installation
## 1. Install Docker Desktop
### Windows
- Download Docker Desktop from docker.com/products/docker-desktop
- Run the installer and follow setup wizard
- Enable WSL 2 integration if prompted
- Restart your computer after installation

### macOS
- Download Docker Desktop for Mac from the official site
- Drag Docker.app to Applications folder
- Launch Docker Desktop and complete setup

### Linux
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Log out and back in
```
## 2. Install Docker MCP Plugin
```bash
# Install the Docker MCP plugin
docker plugin install docker/mcp-plugin:latest

# Verify installation
docker mcp version
```
## 3. Install Claude Desktop
### Windows
- Download from claude.ai/download
- Run installer and complete setup

### macOS
- Download Claude Desktop for macOS
- Move to Applications folder
- Launch and sign in


# MCP Server Setup
## 1. Clone and Build
```bash
# Clone this repository
git clone <your-repo-url>
cd uptimecheck-mcp-server

# Build the Docker image
docker build -t uptimecheck-mcp-server .
```
## 2. Set Up MCP Configuration Files
Create Directory Structure
### Windows
```powershell
# Create MCP directories
mkdir $env:USERPROFILE\.docker\mcp\catalogs -Force
```
### macOS/Linux:
```bash
# Create MCP directories
mkdir -p ~/.docker/mcp/catalogs
```
### Create custom.yaml
**File Location:**
- Windows: %USERPROFILE%\.docker\mcp\catalogs\custom.yaml
- macOS: ~/.docker/mcp/catalogs/custom.yaml
- Linux: ~/.docker/mcp/catalogs/custom.yaml

**Content:**

```yaml
version: 2
name: custom
displayName: Custom MCP Servers
registry:
  uptimecheck:
    description: "Checks server and website uptime (ping, curl)"
    title: "UptimeCheck"
    type: server
    dateAdded: "2025-09-15T13:31:00Z"
    image: uptimecheck-mcp-server:latest
    ref: ""
    readme: ""
    toolsUrl: ""
    source: ""
    upstream: ""
    icon: ""
    tools:
      - name: ping_host
      - name: check_website
    secrets: []
    metadata:
      category: monitoring
      tags:
        - uptime
        - ping
        - curl
        - monitoring
        - network
      license: MIT
      owner: local
```
### Create registry.yaml
**File Location:**
- Windows: 
    - %USERPROFILE%\.docker\mcp\registry.yaml
- macOS/Linux: 
    - ~/.docker/mcp/registry.yaml

**Content:**

```yaml
registry:
  uptimecheck:
    ref: ""
```
## 3. Configure Claude Desktop
Find Claude Config File
**File Locations:**
- Windows: %APPDATA%\Claude\claude_desktop_config.json
- macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
- Linux: ~/.config/Claude/claude_desktop_config.json

### Update Configuration
Replace your config file content with:

```json
{
  "mcpServers": {
    "mcp-toolkit-gateway": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v", "/var/run/docker.sock:/var/run/docker.sock",
        "-v", "C:/Users/YOUR_USERNAME/.docker/mcp:/mcp",
        "docker/mcp-gateway",
        "--catalog=/mcp/catalogs/docker-mcp.yaml",
        "--catalog=/mcp/catalogs/custom.yaml",
        "--config=/mcp/config.yaml",
        "--registry=/mcp/registry.yaml",
        "--tools-config=/mcp/tools.yaml",
        "--transport=stdio"
      ]
    }
  }
}
```
⚠️ **Important Path Replacements:**
---
- **Windows**: Replace C:/Users/YOUR_USERNAME with your actual user path (e.g., C:/Users/johnsmith)
- **macOS**: Replace with /Users/YOUR_USERNAME
- **Linux**: Replace with /home/YOUR_USERNAME

# Launch and Verify
## 1. Restart Services

 1. Close Claude Desktop completely
 2. Restart Docker Desktop
 3. Wait 30 seconds, then launch Claude Desktop
## 2. Verify MCP Server
```bash
# Check if server is recognized
docker mcp server list

# Should show: uptimecheck
3. Initialize MCP System (if needed)
bash
# If server doesn't appear, reset and reinitialize
docker mcp catalog reset
docker mcp catalog init
docker mcp catalog ls
```

# Web Server Mode
The UptimeCheck server can also run as a standalone web API accessible on port 9000, making it compatible with Open WebUI and other applications that can consume HTTP APIs.

## Running as Web API
The server automatically runs in web mode when started, providing both MCP protocol support and HTTP API endpoints.

### Start the Web Server
```bash
# Build the Docker image
docker build -t mcp_uptimecheck:latest .

# Run the container with port mapping
docker run -d -p 9000:9000 --name mcp-uptimecheck mcp_uptimecheck:latest

# Check if it's running
docker ps
docker logs mcp-uptimecheck
```

### Environment Variables
You can customize the server configuration using environment variables:

```bash
# Custom host and port
docker run -d -p 8080:8080 \
  -e MCP_HOST=0.0.0.0 \
  -e MCP_PORT=8080 \
  --name mcp-uptimecheck \
  mcp_uptimecheck:latest
```

## API Endpoints
The web server provides the following HTTP endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Server status and information |
| `GET` | `/health` | Health check with available tools |
| `GET` | `/ping` | Simple ping endpoint (no body required) |
| `GET` | `/check-website` | Simple website check endpoint (no body required) |
| `POST` | `/tools/list` | List all available MCP tools |
| `POST` | `/tools/call` | Execute MCP tools (flexible format) |
| `POST` | `/ping` | Simple ping endpoint (works without body) |
| `POST` | `/check-website` | Simple website check endpoint (works without body) |
| `POST` | `/debug` | Debug endpoint to inspect requests |

### API Examples

**Check server status:**
```bash
curl http://localhost:9000/
```

**Health check:**
```bash
curl http://localhost:9000/health
```

**List available tools:**
```bash
curl -X POST http://localhost:9000/tools/list
```

**Execute ping tool:**
```bash
curl -X POST http://localhost:9000/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "ping_host", "arguments": {"host": "google.com"}}'
```

**Execute website check tool:**
```bash
curl -X POST http://localhost:9000/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "check_website", "arguments": {"url": "https://google.com"}}'
```

**Simple ping endpoint (GET - no body required):**
```bash
curl http://localhost:9000/ping
curl "http://localhost:9000/ping?host=google.com"
```

**Simple ping endpoint (POST - works without body):**
```bash
curl -X POST http://localhost:9000/ping
curl -X POST http://localhost:9000/ping \
  -H "Content-Type: application/json" \
  -d '{"host": "google.com"}'
```

**Simple website check endpoint (GET - no body required):**
```bash
curl http://localhost:9000/check-website
curl "http://localhost:9000/check-website?url=https://google.com"
```

**Simple website check endpoint (POST - works without body):**
```bash
curl -X POST http://localhost:9000/check-website
curl -X POST http://localhost:9000/check-website \
  -H "Content-Type: application/json" \
  -d '{"url": "https://google.com"}'
```

**Debug endpoint (to see what Open WebUI sends):**
```bash
curl -X POST http://localhost:9000/debug \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

## Testing the Web API
You can test the web API using various methods:

### Using PowerShell (Windows)
```powershell
# Test basic endpoints
Invoke-RestMethod -Uri "http://localhost:9000/"
Invoke-RestMethod -Uri "http://localhost:9000/health"

# Test tool execution
$body = '{"name": "ping_host", "arguments": {"host": "google.com"}}'
Invoke-RestMethod -Uri "http://localhost:9000/tools/call" -Method POST -Body $body -ContentType "application/json"
```

### Using curl (Linux/macOS)
```bash
# Test basic endpoints
curl http://localhost:9000/
curl http://localhost:9000/health

# Test tool execution
curl -X POST http://localhost:9000/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "ping_host", "arguments": {"host": "google.com"}}'
```

# Open WebUI Integration
Open WebUI is an extensible, feature-rich, and user-friendly self-hosted WebUI designed to operate entirely offline. You can integrate the UptimeCheck MCP server with Open WebUI to provide uptime monitoring capabilities.

## Install Open WebUI
### Using Docker Compose (Recommended)
Create a `docker-compose.yml` file:

```yaml
version: '3.8'
services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    ports:
      - "3000:8080"
    volumes:
      - open-webui:/app/backend/data
    environment:
      - OPENAI_API_BASE_URL=http://localhost:9000
    depends_on:
      - uptimecheck-server

  uptimecheck-server:
    image: mcp_uptimecheck:latest
    container_name: uptimecheck-server
    ports:
      - "9000:9000"
    environment:
      - MCP_HOST=0.0.0.0
      - MCP_PORT=9000

volumes:
  open-webui:
```

Start the services:
```bash
docker-compose up -d
```

### Using Docker Run
```bash
# Start the UptimeCheck server
docker run -d -p 9000:9000 --name uptimecheck-server mcp_uptimecheck:latest

# Start Open WebUI
docker run -d -p 3000:8080 \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

## Configure MCP Server
The UptimeCheck server is already configured to work with Open WebUI through its HTTP API endpoints. No additional configuration is needed for the server itself.

## Add to Open WebUI
1. **Access Open WebUI**: Open your browser and navigate to `http://localhost:3000`
2. **Create an account** or sign in
3. **Add the MCP server**:
   - Go to Settings → Connected Services
   - Add a new MCP server with the following configuration:
     - **Name**: UptimeCheck
     - **URL**: `http://uptimecheck-server:9000` (if using docker-compose) or `http://localhost:9000`
     - **API Key**: (leave empty if no authentication is required)

### Alternative: Use as External Tool
If MCP integration isn't available, you can use the server as an external tool:

1. **Create a custom tool** in Open WebUI
2. **Configure the tool** to make HTTP requests to your UptimeCheck server
3. **Use the API endpoints** to execute ping and website checks

### Example Tool Configuration
```json
{
  "name": "ping_host",
  "description": "Ping a host to check network uptime",
  "url": "http://localhost:9000/tools/call",
  "method": "POST",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "name": "ping_host",
    "arguments": {
      "host": "{{host}}"
    }
  }
}
```
## 3. Usage Examples
Once set up, you can use these tools in Claude Desktop conversations:

### Ping Host Tool
```text
"Ping 8.8.8.8 to check if it's reachable"

"Check if my server at 192.168.1.100 is up"

"Ping google.com and tell me the results"
```
### Website Checker Tool
```text
"Check if https://google.com is up"

"Is my website https://example.com responding?"

"Test website availability for https://github.com"
```
# Troubleshooting
## "No tools available" in Claude Desktop
1. Check tool names match exactly (no backslashes in YAML)
2. Verify file paths in Claude config are correct for your OS
3. Restart both Docker Desktop and Claude Desktop after any config changes
4. Check Docker permissions - ensure Docker can access your user directory

## Server not appearing in docker mcp server list
1. Verify custom.yaml syntax with an online YAML validator
2. Check registry.yaml has uptimecheck entry under registry: key
3. Rebuild Docker image if you made code changes:
```bash
docker build -t uptimecheck-mcp-server .
```
## Docker MCP plugin issues
```bash
# Reinstall Docker MCP plugin
docker plugin rm docker/mcp-plugin:latest
docker plugin install docker/mcp-plugin:latest

# Verify installation
docker mcp version
```
## Permission errors (Linux/macOS)
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in

# Fix file permissions
chmod 644 ~/.docker/mcp/catalogs/custom.yaml
chmod 644 ~/.docker/mcp/registry.yaml
```

## Web server not accessible
1. **Check if container is running:**
   ```bash
   docker ps | grep mcp-uptimecheck
   ```

2. **Check container logs:**
   ```bash
   docker logs mcp-uptimecheck
   ```

3. **Verify port mapping:**
   ```bash
   # Should show 0.0.0.0:9000->9000/tcp
   docker port mcp-uptimecheck
   ```

4. **Test local connectivity:**
   ```bash
   # Test from inside the container
   docker exec mcp-uptimecheck curl http://localhost:9000/health
   
   # Test from host
   curl http://localhost:9000/health
   ```

5. **Check firewall settings** (if applicable):
   - Ensure port 9000 is not blocked
   - Check Windows Firewall or iptables rules

## Open WebUI integration issues
1. **Verify server is accessible** from Open WebUI container:
   ```bash
   # If using docker-compose
   docker exec open-webui curl http://uptimecheck-server:9000/health
   
   # If using separate containers
   docker exec open-webui curl http://host.docker.internal:9000/health
   ```

2. **Check network connectivity:**
   ```bash
   # Ensure containers can communicate
   docker network ls
   docker network inspect bridge
   ```

3. **Verify Open WebUI configuration:**
   - Check the MCP server URL is correct
   - Ensure the server is running before starting Open WebUI
   - Check Open WebUI logs for connection errors

## Open WebUI "Request body expected" Error
If you get the error "Request body expected for operation 'call_tool_tools_call_post' but none found":

### Solution 1: Use GET Endpoints (Recommended)
The easiest solution is to use GET endpoints that don't require a request body:

**For ping:**
- Use endpoint: `http://localhost:9000/ping` (GET)
- Optional: Add query parameter: `http://localhost:9000/ping?host=google.com`

**For website check:**
- Use endpoint: `http://localhost:9000/check-website` (GET)
- Optional: Add query parameter: `http://localhost:9000/check-website?url=https://google.com`

### Solution 2: Use POST Endpoints (No Body Required)
The POST endpoints now work even without a request body:

**For ping:**
- Use endpoint: `http://localhost:9000/ping` (POST)
- No body required - defaults to google.com
- Optional: Send `{"host": "google.com"}`

**For website check:**
- Use endpoint: `http://localhost:9000/check-website` (POST)
- No body required - defaults to https://google.com
- Optional: Send `{"url": "https://google.com"}`

### Solution 3: Debug the Request Format
1. **Check what Open WebUI is sending:**
   ```bash
   curl -X POST http://localhost:9000/debug \
     -H "Content-Type: application/json" \
     -d '{"test": "from_openwebui"}'
   ```

2. **Check server logs:**
   ```bash
   docker logs mcp-uptimecheck
   ```

### Solution 4: Configure Open WebUI Tool Correctly
When setting up the tool in Open WebUI, use this configuration:

**For Ping Tool:**
```json
{
  "name": "ping_host",
  "description": "Ping a host to check network uptime",
  "url": "http://localhost:9000/ping",
  "method": "POST",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "host": "{{host}}"
  }
}
```

**For Website Check Tool:**
```json
{
  "name": "check_website", 
  "description": "Check if a website is up",
  "url": "http://localhost:9000/check-website",
  "method": "POST",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "url": "{{url}}"
  }
}
```

# Architecture
```mermaid
flowchart TD
    A[Claude Desktop] -->|MCP Gateway| B[UptimeCheck MCP Server]
    E[Open WebUI] -->|HTTP API| B
    F[External Apps] -->|HTTP API| B
    B -->|Execute| C[ping/curl commands]
    D[Docker Desktop MCP System] -.->|Manages| B
    B -->|Port 9000| G[Web API Endpoints]
    
    subgraph "UptimeCheck Server"
        B
        G
        H[/tools/list]
        I[/tools/call]
        J[/health]
        K[/]
    end
    
    G --> H
    G --> I
    G --> J
    G --> K
```
# Development
## Local Testing
```bash
# Test the server directly
python uptimecheck_server.py

# Test MCP protocol
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python uptimecheck_server.py
```
## Adding New Tools
1. Add function to uptimecheck_server.py with @mcp.tool() decorator
2. Update custom.yaml tools list with new tool name
3. Rebuild Docker image: docker build -t uptimecheck-mcp-server .
4. Restart Claude Desktop

## Common File Paths Reference
| OS | Claude Config | MCP Config Directory |
| --- | --- | --- |
| Windows | %APPDATA%\Claude\claude_desktop_config.json | %USERPROFILE%\.docker\mcp\ |
| macOS | ~/Library/Application Support/Claude/claude_desktop_config.json | ~/.docker/mcp/ |
| Linux | ~/.config/Claude/claude_desktop_config.json | ~/.docker/mcp/ |

## Quick Reference

### Web Server Commands
```bash
# Build and run
docker build -t mcp_uptimecheck:latest .
docker run -d -p 9000:9000 --name mcp-uptimecheck mcp_uptimecheck:latest

# Check status
curl http://localhost:9000/health

# Test tools
curl -X POST http://localhost:9000/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "ping_host", "arguments": {"host": "google.com"}}'

# Stop and cleanup
docker stop mcp-uptimecheck && docker rm mcp-uptimecheck
```

### Docker Compose for Open WebUI
```yaml
version: '3.8'
services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    ports: ["3000:8080"]
    volumes: [open-webui:/app/backend/data]
    depends_on: [uptimecheck-server]

  uptimecheck-server:
    image: mcp_uptimecheck:latest
    ports: ["9000:9000"]

volumes:
  open-webui:
```

# Acknowledgements
This MCP server was based on the [work of NetworkChuck](https://github.com/theNetworkChuck/docker-mcp-tutorial)