# Developer Guide: Adding Custom Tools to MCP Server

This guide shows you how to add your own custom tools to this MCP server using the existing codebase as an example.

## Table of Contents
- [Understanding the Architecture](#understanding-the-architecture)
- [Quick Start: Adding a Tool](#quick-start-adding-a-tool)
- [Step-by-Step Tutorial](#step-by-step-tutorial)
- [Tool Development Best Practices](#tool-development-best-practices)
- [Testing Your Tool](#testing-your-tool)
- [Advanced Topics](#advanced-topics)

## Understanding the Architecture

### Modular Structure

```
src/
├── config.py              # Configuration & logging setup
├── mcp_server.py         # Core MCP server - registers tools
├── mcp_tools/            # Tool implementations
│   ├── __init__.py       # Exports all tools
│   ├── ping_tool.py      # Example: Network ping tool
│   └── website_tool.py   # Example: Website check tool
└── api/                  # FastAPI endpoints
    ├── n8n_mcp_endpoints.py   # Handles MCP protocol
    └── legacy_endpoints.py     # Direct tool access
```

### How Tools Work

1. **Tool Definition** - Create a Python function in `src/mcp_tools/`
2. **Registration** - Register with MCP server in `src/mcp_server.py`
3. **Exposure** - Automatically available via all endpoints

## Quick Start: Adding a Tool

Let's add a simple "reverse_string" tool that reverses text.

### 1. Create Tool File

Create `src/mcp_tools/reverse_tool.py`:

```python
"""Reverse string tool for MCP server."""
from mcp.types import TextContent, Tool

# Tool definition
REVERSE_STRING_TOOL = Tool(
    name="reverse_string",
    description="Reverse a text string",
    inputSchema={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Text to reverse"
            }
        },
        "required": ["text"]
    }
)

async def reverse_string(text: str) -> list[TextContent]:
    """
    Reverse a text string.
    
    Args:
        text: The string to reverse
        
    Returns:
        List of TextContent with reversed string
    """
    try:
        reversed_text = text[::-1]
        
        return [
            TextContent(
                type="text",
                text=f"Original: {text}\nReversed: {reversed_text}"
            )
        ]
    except Exception as e:
        return [
            TextContent(
                type="text",
                text=f"[ERROR] Failed to reverse string: {str(e)}"
            )
        ]
```

### 2. Export Tool

Update `src/mcp_tools/__init__.py`:

```python
"""MCP Tools - Network and utility tools."""
from .ping_tool import PING_TOOL, ping_host
from .website_tool import WEBSITE_TOOL, check_website
from .reverse_tool import REVERSE_STRING_TOOL, reverse_string  # Add this

__all__ = [
    "PING_TOOL",
    "ping_host",
    "WEBSITE_TOOL", 
    "check_website",
    "REVERSE_STRING_TOOL",  # Add this
    "reverse_string",        # Add this
]
```

### 3. Register Tool

Update `src/mcp_server.py`:

```python
from mcp.server import Server
from mcp.types import TextContent
from .mcp_tools import (
    PING_TOOL, ping_host,
    WEBSITE_TOOL, check_website,
    REVERSE_STRING_TOOL, reverse_string,  # Add this
)

# ... existing code ...

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    return [
        PING_TOOL,
        WEBSITE_TOOL,
        REVERSE_STRING_TOOL,  # Add this
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict
) -> list[types.TextContent]:
    """Execute a tool."""
    if name == "ping_host":
        return await ping_host(arguments.get("host", ""))
    elif name == "check_website":
        return await check_website(arguments.get("url", ""))
    elif name == "reverse_string":  # Add this
        return await reverse_string(arguments.get("text", ""))
    else:
        raise ValueError(f"Unknown tool: {name}")
```

### 4. Test Your Tool

```bash
# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d

# Test via API
curl -X POST http://localhost:9000/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "reverse_string",
    "arguments": {"text": "Hello World"}
  }'
```

**That's it!** Your tool is now available in N8N, Open WebUI, Claude Desktop, and all MCP clients!

## Step-by-Step Tutorial

Let's create a more complex tool: **weather lookup** using a public API.

### Step 1: Plan Your Tool

**What it does**: Gets current weather for a city
**Inputs**: City name
**Outputs**: Temperature, conditions, humidity
**External API**: OpenWeatherMap (free tier)

### Step 2: Create the Tool File

Create `src/mcp_tools/weather_tool.py`:

```python
"""Weather lookup tool for MCP server."""
import httpx
from mcp.types import TextContent, Tool
from ..config import logger

# Tool definition
WEATHER_TOOL = Tool(
    name="get_weather",
    description="Get current weather for a city using OpenWeatherMap API",
    inputSchema={
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City name (e.g., 'London' or 'New York, US')"
            },
            "units": {
                "type": "string",
                "description": "Temperature units: 'metric' (Celsius) or 'imperial' (Fahrenheit)",
                "enum": ["metric", "imperial"],
                "default": "metric"
            }
        },
        "required": ["city"]
    }
)

async def get_weather(city: str, units: str = "metric") -> list[TextContent]:
    """
    Get current weather for a city.
    
    Args:
        city: City name (e.g., 'London' or 'New York, US')
        units: Temperature units ('metric' or 'imperial')
        
    Returns:
        List of TextContent with weather information
    """
    try:
        logger.info(f"Getting weather for: {city} (units: {units})")
        
        # Get API key from environment
        import os
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            return [
                TextContent(
                    type="text",
                    text="[ERROR] OPENWEATHER_API_KEY not configured. Set it in your environment."
                )
            ]
        
        # Call OpenWeatherMap API
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "q": city,
                    "appid": api_key,
                    "units": units
                }
            )
            
            if response.status_code != 200:
                return [
                    TextContent(
                        type="text",
                        text=f"[ERROR] Weather API returned {response.status_code}: {response.text}"
                    )
                ]
            
            data = response.json()
            
            # Extract weather data
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            description = data["weather"][0]["description"]
            wind_speed = data["wind"]["speed"]
            
            # Format units
            temp_unit = "°C" if units == "metric" else "°F"
            speed_unit = "m/s" if units == "metric" else "mph"
            
            # Build response
            result = f"""[SUCCESS] Weather for {city}:

Temperature: {temp}{temp_unit} (feels like {feels_like}{temp_unit})
Conditions: {description.capitalize()}
Humidity: {humidity}%
Wind Speed: {wind_speed} {speed_unit}
"""
            
            logger.info(f"Weather retrieved successfully for {city}")
            return [TextContent(type="text", text=result)]
            
    except httpx.TimeoutException:
        logger.error(f"Timeout getting weather for {city}")
        return [
            TextContent(
                type="text",
                text=f"[TIMEOUT] Weather API request timed out for {city}"
            )
        ]
    except KeyError as e:
        logger.error(f"Unexpected API response format: {e}")
        return [
            TextContent(
                type="text",
                text=f"[ERROR] Unexpected response format from weather API"
            )
        ]
    except Exception as e:
        logger.error(f"Error getting weather: {e}", exc_info=True)
        return [
            TextContent(
                type="text",
                text=f"[ERROR] Failed to get weather: {str(e)}"
            )
        ]
```

### Step 3: Add Configuration

Update `docker-compose.yml`:

```yaml
services:
  uptimecheck-server:
    # ... existing config ...
    environment:
      - MCP_HOST=0.0.0.0
      - MCP_PORT=9000
      - MCP_TRANSPORT=sse
      - LOG_LEVEL=DEBUG
      - PYTHONUNBUFFERED=1
      # Add your API key
      - OPENWEATHER_API_KEY=your_api_key_here
```

### Step 4: Export and Register

Update `src/mcp_tools/__init__.py`:

```python
from .ping_tool import PING_TOOL, ping_host
from .website_tool import WEBSITE_TOOL, check_website
from .weather_tool import WEATHER_TOOL, get_weather

__all__ = [
    "PING_TOOL", "ping_host",
    "WEBSITE_TOOL", "check_website",
    "WEATHER_TOOL", "get_weather",
]
```

Update `src/mcp_server.py`:

```python
from .mcp_tools import (
    PING_TOOL, ping_host,
    WEBSITE_TOOL, check_website,
    WEATHER_TOOL, get_weather,
)

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [PING_TOOL, WEBSITE_TOOL, WEATHER_TOOL]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "ping_host":
        return await ping_host(arguments.get("host", ""))
    elif name == "check_website":
        return await check_website(arguments.get("url", ""))
    elif name == "get_weather":
        return await get_weather(
            arguments.get("city", ""),
            arguments.get("units", "metric")
        )
    else:
        raise ValueError(f"Unknown tool: {name}")
```

### Step 5: Update Requirements

Add to `requirements.txt` if needed:

```
# Already included:
httpx
```

### Step 6: Test

```bash
# Rebuild
docker-compose build

# Start with API key
OPENWEATHER_API_KEY=your_key docker-compose up -d

# Test
curl -X POST http://localhost:9000/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_weather",
    "arguments": {
      "city": "London",
      "units": "metric"
    }
  }'
```

## Tool Development Best Practices

### 1. Input Validation

Always validate inputs:

```python
async def my_tool(param: str) -> list[TextContent]:
    # Validate
    if not param or not param.strip():
        return [TextContent(
            type="text",
            text="[ERROR] Parameter cannot be empty"
        )]
    
    # Sanitize
    param = param.strip()
    
    # Process...
```

### 2. Error Handling

Use comprehensive try-except blocks:

```python
async def my_tool(param: str) -> list[TextContent]:
    try:
        # Main logic
        result = await do_something(param)
        return [TextContent(type="text", text=f"[SUCCESS] {result}")]
        
    except TimeoutError:
        logger.error(f"Timeout in my_tool: {param}")
        return [TextContent(
            type="text",
            text="[TIMEOUT] Operation timed out"
        )]
        
    except ValueError as e:
        logger.warning(f"Invalid input: {e}")
        return [TextContent(
            type="text",
            text=f"[ERROR] Invalid input: {str(e)}"
        )]
        
    except Exception as e:
        logger.error(f"Unexpected error in my_tool: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"[ERROR] Unexpected error: {str(e)}"
        )]
```

### 3. Logging

Use the configured logger:

```python
from ..config import logger

async def my_tool(param: str) -> list[TextContent]:
    logger.info(f"Executing my_tool with param: {param}")
    
    try:
        result = await do_something(param)
        logger.info(f"my_tool completed successfully")
        return [TextContent(type="text", text=result)]
    except Exception as e:
        logger.error(f"my_tool failed: {e}", exc_info=True)
        return [TextContent(type="text", text=f"[ERROR] {e}")]
```

### 4. Async Operations

Use `async`/`await` for I/O operations:

```python
import httpx
import asyncio

async def fetch_data(url: str) -> str:
    """Good: Async HTTP request"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text

async def process_multiple(urls: list[str]) -> list[str]:
    """Good: Concurrent async operations"""
    tasks = [fetch_data(url) for url in urls]
    results = await asyncio.gather(*tasks)
    return results
```

### 5. Tool Schema Design

Make schemas clear and specific:

```python
GOOD_TOOL = Tool(
    name="calculate_distance",
    description="Calculate distance between two coordinates using Haversine formula",
    inputSchema={
        "type": "object",
        "properties": {
            "lat1": {
                "type": "number",
                "description": "Latitude of first point (decimal degrees, -90 to 90)",
                "minimum": -90,
                "maximum": 90
            },
            "lon1": {
                "type": "number",
                "description": "Longitude of first point (decimal degrees, -180 to 180)",
                "minimum": -180,
                "maximum": 180
            },
            "lat2": {
                "type": "number",
                "description": "Latitude of second point",
                "minimum": -90,
                "maximum": 90
            },
            "lon2": {
                "type": "number",
                "description": "Longitude of second point",
                "minimum": -180,
                "maximum": 180
            },
            "unit": {
                "type": "string",
                "description": "Unit for distance",
                "enum": ["km", "miles", "nautical_miles"],
                "default": "km"
            }
        },
        "required": ["lat1", "lon1", "lat2", "lon2"]
    }
)
```

### 6. Response Formatting

Use consistent, readable output:

```python
async def my_tool(param: str) -> list[TextContent]:
    result = await process(param)
    
    # Good: Clear, structured output
    output = f"""[SUCCESS] Operation completed

Input: {param}
Result: {result}
Timestamp: {datetime.now().isoformat()}

Details:
- Item 1: value1
- Item 2: value2
"""
    
    return [TextContent(type="text", text=output)]
```

## Testing Your Tool

### 1. Unit Testing

Create `tests/test_my_tool.py`:

```python
import pytest
from src.mcp_tools.my_tool import my_tool

@pytest.mark.asyncio
async def test_my_tool_success():
    """Test successful execution"""
    result = await my_tool("test_input")
    assert len(result) == 1
    assert "[SUCCESS]" in result[0].text

@pytest.mark.asyncio
async def test_my_tool_empty_input():
    """Test error handling for empty input"""
    result = await my_tool("")
    assert "[ERROR]" in result[0].text

@pytest.mark.asyncio
async def test_my_tool_invalid_input():
    """Test error handling for invalid input"""
    result = await my_tool("invalid@#$%")
    assert "[ERROR]" in result[0].text
```

Run tests:
```bash
pytest tests/
```

### 2. Integration Testing

Test via MCP protocol:

```python
# test_integration.py
import httpx
import pytest

@pytest.mark.asyncio
async def test_tool_via_mcp():
    async with httpx.AsyncClient() as client:
        # List tools
        response = await client.post(
            "http://localhost:9000/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 1
            }
        )
        assert response.status_code == 200
        data = response.json()
        tool_names = [t["name"] for t in data["result"]["tools"]]
        assert "my_tool" in tool_names
        
        # Call tool
        response = await client.post(
            "http://localhost:9000/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "id": 2,
                "params": {
                    "name": "my_tool",
                    "arguments": {"param": "test"}
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
```

### 3. Manual Testing

```bash
# Test tool list
curl -X POST http://localhost:9000/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 1
  }'

# Test tool execution
curl -X POST http://localhost:9000/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "id": 2,
    "params": {
      "name": "my_tool",
      "arguments": {"param": "test_value"}
    }
  }'

# Test via legacy endpoint
curl -X POST http://localhost:9000/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my_tool",
    "arguments": {"param": "test_value"}
  }'
```

### 4. N8N Testing

1. Add MCP Client node
2. Configure endpoint
3. Refresh tools list
4. Select your tool
5. Execute with test data

## Advanced Topics

### 1. Stateful Tools

Tools that maintain state across calls:

```python
# Use a global state manager
class ToolState:
    def __init__(self):
        self.cache = {}
    
    async def get_cached(self, key: str):
        return self.cache.get(key)
    
    async def set_cached(self, key: str, value: any):
        self.cache[key] = value

# Global instance
_state = ToolState()

async def my_stateful_tool(key: str) -> list[TextContent]:
    # Check cache
    cached = await _state.get_cached(key)
    if cached:
        return [TextContent(type="text", text=f"Cached: {cached}")]
    
    # Compute and cache
    result = await expensive_operation(key)
    await _state.set_cached(key, result)
    return [TextContent(type="text", text=f"Computed: {result}")]
```

### 2. Long-Running Operations

For operations that take time:

```python
import asyncio

async def long_running_tool(task_id: str) -> list[TextContent]:
    """Tool that might take a while"""
    try:
        # Start operation with timeout
        result = await asyncio.wait_for(
            perform_long_operation(task_id),
            timeout=30.0  # 30 second timeout
        )
        return [TextContent(type="text", text=f"[SUCCESS] {result}")]
        
    except asyncio.TimeoutError:
        return [TextContent(
            type="text",
            text="[TIMEOUT] Operation exceeded 30 seconds"
        )]
```

### 3. File Operations

Tools that work with files:

```python
import aiofiles
from pathlib import Path

async def read_file_tool(filename: str) -> list[TextContent]:
    """Read a file from the workspace"""
    try:
        # Validate path (security!)
        file_path = Path("/workspace") / filename
        if not file_path.is_relative_to("/workspace"):
            return [TextContent(
                type="text",
                text="[ERROR] Access denied: file outside workspace"
            )]
        
        # Read file asynchronously
        async with aiofiles.open(file_path, 'r') as f:
            content = await f.read()
        
        return [TextContent(
            type="text",
            text=f"File: {filename}\n\n{content}"
        )]
        
    except FileNotFoundError:
        return [TextContent(
            type="text",
            text=f"[ERROR] File not found: {filename}"
        )]
```

### 4. Subprocess Execution

For running external commands:

```python
import asyncio

async def run_command_tool(command: str) -> list[TextContent]:
    """Execute a shell command (use with caution!)"""
    try:
        # Whitelist commands for security
        allowed_commands = ["ls", "pwd", "echo", "date"]
        cmd_name = command.split()[0]
        
        if cmd_name not in allowed_commands:
            return [TextContent(
                type="text",
                text=f"[ERROR] Command not allowed: {cmd_name}"
            )]
        
        # Execute with timeout
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=10.0
        )
        
        if process.returncode == 0:
            return [TextContent(
                type="text",
                text=f"[SUCCESS]\n{stdout.decode()}"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"[ERROR] Exit code {process.returncode}\n{stderr.decode()}"
            )]
            
    except asyncio.TimeoutError:
        return [TextContent(
            type="text",
            text="[TIMEOUT] Command exceeded 10 seconds"
        )]
```

### 5. Multi-Tool Workflows

Tools that call other tools:

```python
from . import ping_host, check_website

async def diagnose_host(hostname: str) -> list[TextContent]:
    """Diagnose a host using multiple tools"""
    results = []
    
    # Ping the host
    ping_result = await ping_host(hostname)
    results.append(f"Ping Result:\n{ping_result[0].text}\n")
    
    # Check website
    website_result = await check_website(f"https://{hostname}")
    results.append(f"Website Check:\n{website_result[0].text}\n")
    
    # Combine results
    combined = "\n".join(results)
    return [TextContent(type="text", text=combined)]
```

## Checklist for New Tools

- [ ] Create tool file in `src/mcp_tools/`
- [ ] Define `Tool` schema with clear description
- [ ] Implement async function with proper error handling
- [ ] Add comprehensive logging
- [ ] Export from `src/mcp_tools/__init__.py`
- [ ] Register in `src/mcp_server.py` (list_tools and call_tool)
- [ ] Add any new dependencies to `requirements.txt`
- [ ] Add environment variables to `docker-compose.yml` if needed
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Test manually via curl
- [ ] Test in N8N
- [ ] Document in code comments
- [ ] Update README if tool is significant

## Common Patterns

### Pattern: API Client Tool

```python
"""Template for API client tool"""
import httpx
from mcp.types import TextContent, Tool
from ..config import logger

API_TOOL = Tool(
    name="api_tool",
    description="Call external API",
    inputSchema={
        "type": "object",
        "properties": {
            "param": {"type": "string", "description": "API parameter"}
        },
        "required": ["param"]
    }
)

async def api_tool(param: str) -> list[TextContent]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.example.com/endpoint",
                params={"q": param}
            )
            response.raise_for_status()
            data = response.json()
            return [TextContent(type="text", text=str(data))]
    except Exception as e:
        logger.error(f"API error: {e}")
        return [TextContent(type="text", text=f"[ERROR] {e}")]
```

### Pattern: Data Processing Tool

```python
"""Template for data processing tool"""
from mcp.types import TextContent, Tool

PROCESS_TOOL = Tool(
    name="process_data",
    description="Process and transform data",
    inputSchema={
        "type": "object",
        "properties": {
            "data": {"type": "string", "description": "Data to process"}
        },
        "required": ["data"]
    }
)

async def process_data(data: str) -> list[TextContent]:
    try:
        # Validate
        if not data:
            return [TextContent(type="text", text="[ERROR] No data provided")]
        
        # Process
        result = transform(data)
        
        # Format
        output = f"Processed: {result}"
        return [TextContent(type="text", text=output)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"[ERROR] {e}")]
```

## Getting Help

- **Examples**: See `src/mcp_tools/ping_tool.py` and `website_tool.py`
- **MCP Docs**: https://modelcontextprotocol.io/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Issues**: https://github.com/your-repo/mcp-checkuptime/issues

## Contributing Your Tools

Once you've built a useful tool:

1. Ensure it follows all best practices
2. Add comprehensive tests
3. Document it well
4. Submit a pull request!

Great additions are:
- Database query tools
- File system operations
- Cloud service integrations
- Data transformation utilities
- Monitoring and alerting tools

Happy coding! 🚀
