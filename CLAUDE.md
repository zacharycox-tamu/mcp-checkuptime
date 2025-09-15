# UptimeCheck MCP Server Implementation Notes

- No @mcp.prompt() decorators used
- No prompt parameter in FastMCP()
- No complex type hints – only simple str parameters
- MCP tool docstrings are single-line only
- All parameters default to empty strings ("")
- All tools return formatted strings
- All tools check for empty strings with .strip()
- Error handling included in every tool
- Files clearly separated; only one version of each
- Docker container runs system ping/curl safely as non-root user
- No secrets required; no Docker secrets injected
