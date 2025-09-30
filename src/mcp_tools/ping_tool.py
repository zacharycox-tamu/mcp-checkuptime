"""Ping tool implementation."""
import subprocess
import platform
from mcp.types import TextContent
from ..config import logger


async def ping_host(host: str) -> list[TextContent]:
    """
    Check if a host is reachable using ICMP ping.
    
    Args:
        host: Hostname or IP address to ping
        
    Returns:
        List of TextContent with ping results
    """
    logger.info(f"=== PING_HOST TOOL CALLED ===")
    logger.info(f"Pinging host: {host}")
    logger.debug(f"Host argument: {host}")
    
    if not host.strip():
        return [TextContent(
            type="text", 
            text="[ERROR] Host is required"
        )]
    
    try:
        # Detect OS and use appropriate ping syntax
        system = platform.system().lower()
        if system == "windows":
            # Windows: -n count, -w timeout_ms
            cmd = f"ping -n 3 -w 5000 {host}"
        else:
            # Linux/Unix: -c count, -W timeout_sec
            cmd = f"ping -c 3 -W 5 {host}"
        
        logger.info(f"Executing command on {system}: {cmd}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=20,
            shell=True
        )
        
        logger.info(f"Ping result - Return code: {result.returncode}")
        
        if result.returncode == 0:
            return [TextContent(
                type="text", 
                text=f"[SUCCESS] Host {host} is reachable!\n\n{result.stdout}"
            )]
        else:
            logger.warning(f"Ping failed for {host}. Return code: {result.returncode}")
            return [TextContent(
                type="text", 
                text=f"""[ERROR] Cannot reach {host}.

Return code: {result.returncode}
Stdout: {result.stdout}
Stderr: {result.stderr}"""
            )]
    
    except subprocess.TimeoutExpired:
        logger.error(f"Ping command timed out for {host}")
        return [TextContent(
            type="text", 
            text=f"[TIMEOUT] Ping timed out after 20 seconds for {host}"
        )]
    
    except Exception as e:
        logger.error(f"Error pinging {host}: {e}", exc_info=True)
        return [TextContent(
            type="text", 
            text=f"[ERROR] {str(e)}"
        )]
