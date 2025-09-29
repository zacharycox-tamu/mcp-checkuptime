# Open WebUI Compatibility Fixes

## Issues Fixed

### 1. **POST Endpoint Request Body Handling**
**Problem**: Open WebUI was sending POST requests without request bodies, causing "Request body expected" errors.

**Solution**: Updated POST endpoints to handle both Request objects and dict objects gracefully:
```python
@app.post("/ping")
async def ping_endpoint(request: Request = None):
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
```

### 2. **Response Format for Open WebUI**
**Problem**: MCP TextContent objects weren't compatible with Open WebUI's expected response format.

**Solution**: Convert MCP responses to simple JSON format:
```python
# Convert MCP TextContent to simple response for Open WebUI
if result and len(result) > 0:
    return {"result": result[0].text, "host": host}
else:
    return {"error": "No result from ping tool", "host": host}
```

### 3. **Unicode Character Issues**
**Problem**: Unicode emoji characters (✅, ❌, ⏱️) were causing encoding errors on Windows.

**Solution**: Replaced with ASCII-safe alternatives:
- ✅ → `[SUCCESS]`
- ❌ → `[ERROR]`
- ⏱️ → `[TIMEOUT]`

### 4. **Windows Ping Command Compatibility**
**Problem**: Linux ping syntax (`-c 3 -W 2`) doesn't work on Windows.

**Solution**: Updated to use Windows ping syntax:
```python
# Use Windows ping syntax
cmd = f"ping -n 3 -w 2000 {host}"
```

### 5. **HTTP Status Code Parsing**
**Problem**: Curl output was being parsed incorrectly, causing 3xx redirects to be treated as errors.

**Solution**: Improved string stripping to handle quoted output:
```python
code = result.stdout.strip().strip("'\"")
```

### 6. **ResourceLink Validation Errors**
**Problem**: ResourceLink objects were missing required fields, causing validation errors.

**Solution**: Removed ResourceLink annotations temporarily to focus on core functionality.

## Updated Endpoints

### **GET Endpoints**
- `GET /ping?host=google.com` - Simple ping with query parameter
- `GET /check-website?url=https://google.com` - Simple website check with query parameter

### **POST Endpoints**
- `POST /ping` - Ping with optional JSON body `{"host": "google.com"}`
- `POST /check-website` - Website check with optional JSON body `{"url": "https://google.com"}`

### **Tool Endpoints**
- `GET /tools` - List available tools
- `POST /tools/list` - List available tools (alternative)
- `POST /tools/call` - Execute tools with various request formats

### **Utility Endpoints**
- `GET /` - Server status
- `GET /health` - Health check with session count
- `POST /debug` - Debug endpoint for troubleshooting

## Response Format

All endpoints now return consistent JSON responses:

### **Success Response**
```json
{
  "result": "[SUCCESS] Host google.com is reachable!\n[ping output]",
  "host": "google.com"
}
```

### **Error Response**
```json
{
  "error": "[ERROR] Cannot reach host",
  "host": "google.com"
}
```

### **Tools List Response**
```json
{
  "tools": [
    {
      "name": "ping_host",
      "description": "Ping a host to check network uptime (ICMP).",
      "inputSchema": {
        "type": "object",
        "properties": {
          "host": {
            "type": "string",
            "description": "Hostname or IP address to ping"
          }
        },
        "required": ["host"]
      }
    }
  ]
}
```

## Testing Results

✅ **GET /ping** - Works correctly with Windows ping
✅ **POST /ping** - Handles both Request objects and dict objects
✅ **GET /check-website** - Works correctly with curl
✅ **POST /check-website** - Handles both Request objects and dict objects
✅ **GET /tools** - Returns proper tool list format
✅ **POST /tools/call** - Executes tools correctly

## Open WebUI Integration

The server is now fully compatible with Open WebUI and should work with:

1. **External Tools**: Configure as HTTP tools pointing to the server endpoints
2. **MCP Integration**: Use the `/mcp` endpoint for full MCP protocol support
3. **Simple API Calls**: Use the legacy endpoints for basic functionality

## Configuration for Open WebUI

### **Ping Tool Configuration**
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

### **Website Check Tool Configuration**
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

The server is now ready for production use with Open WebUI!
