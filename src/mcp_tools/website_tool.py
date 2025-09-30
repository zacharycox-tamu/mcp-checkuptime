"""Website check tool implementation."""
import subprocess
from mcp.types import TextContent
from ..config import logger


async def check_website(url: str) -> list[TextContent]:
    """
    Check if a website is accessible using HTTP/HTTPS.
    
    Args:
        url: Website URL to check
        
    Returns:
        List of TextContent with website check results
    """
    logger.info(f"=== CHECK_WEBSITE TOOL CALLED ===")
    logger.info(f"Checking website: {url}")
    logger.debug(f"URL argument: {url}")
    
    if not url.strip():
        return [TextContent(
            type="text", 
            text="[ERROR] URL is required"
        )]
    
    try:
        # Use curl to check website (more reliable than requests for simple checks)
        cmd = f"curl -s -o /dev/null -w '%{{http_code}}' --max-time 8 {url}"
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            shell=True
        )
        
        # Strip quotes from curl output
        code = result.stdout.strip().strip("'\"")
        
        logger.info(f"Website check for {url} returned HTTP {code}")
        
        # 2xx and 3xx are considered successful
        if code and (code.startswith("2") or code.startswith("3")):
            return [TextContent(
                type="text", 
                text=f"[SUCCESS] Website {url} is up! HTTP status: {code}"
            )]
        else:
            return [TextContent(
                type="text", 
                text=f"[ERROR] Website {url} is down or unreachable. HTTP status: {code}"
            )]
    
    except subprocess.TimeoutExpired:
        logger.error(f"Website check timed out for {url}")
        return [TextContent(
            type="text", 
            text=f"[TIMEOUT] Website check timed out after 10 seconds for {url}"
        )]
    
    except Exception as e:
        logger.error(f"Error checking website {url}: {e}", exc_info=True)
        return [TextContent(
            type="text", 
            text=f"[ERROR] {str(e)}"
        )]
