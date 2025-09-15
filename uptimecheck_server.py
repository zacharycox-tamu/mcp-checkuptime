#!/usr/bin/env python3
"""Simple UptimeCheck MCP Server - Checks uptime (ping) and website (curl)."""
import os
import sys
import logging
import subprocess
from datetime import datetime, timezone
from mcp.server.fastmcp import FastMCP

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("UptimeCheck-server")

# Initialize MCP server
mcp = FastMCP("uptimecheck")

# === MCP TOOLS ===

@mcp.tool()
async def ping_host(host: str = "") -> str:
    """Ping a host to check network uptime (ICMP)."""
    logger.info(f"Pinging host: {host}")
    if not host.strip():
        return "❌ Error: Host is required"
    try:
        cmd = f"ping -c 3 -W 2 {host}"
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, shell=True)
        if result.returncode == 0:
            return f"✅ Host {host} is reachable!\n{result.stdout}"
        else:
            return f"❌ Cannot reach {host}.\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return "⏱️ Ping timed out"
    except Exception as e:
        logger.error(f"Error pinging {host}: {e}")
        return f"❌ Error: {str(e)}"

@mcp.tool()
async def check_website(url: str = "") -> str:
    """Check if a website is up using curl (HTTP/HTTPS)."""
    logger.info(f"Checking website: {url}")
    if not url.strip():
        return "❌ Error: URL is required"
    try:
        cmd = f"curl -s -o /dev/null -w '%{{http_code}}' --max-time 8 {url}"
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, shell=True)
        code = result.stdout.strip()
        if code and code.startswith("2") or code.startswith("3"):
            return f"✅ Website {url} is up! HTTP status: {code}"
        else:
            return f"❌ Website {url} is down or unreachable. HTTP status: {code}"
    except subprocess.TimeoutExpired:
        return "⏱️ Website check timed out"
    except Exception as e:
        logger.error(f"Error checking website {url}: {e}")
        return f"❌ Error: {str(e)}"

# === SERVER STARTUP ===

if __name__ == "__main__":
    logger.info("Starting UptimeCheck MCP server...")
    try:
        mcp.run(transport='stdio')
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
