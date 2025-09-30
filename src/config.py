"""Configuration and environment variables."""
import os
import sys
import logging

# Configure logging to stderr
log_level = os.getenv('LOG_LEVEL', 'DEBUG').upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s',
    stream=sys.stderr,
    force=True
)

# Get logger
logger = logging.getLogger("UptimeCheck-server")
logger.setLevel(getattr(logging, log_level))

# Server configuration
MCP_HOST = os.getenv('MCP_HOST', '0.0.0.0')
MCP_PORT = int(os.getenv('MCP_PORT', '9000'))
MCP_TRANSPORT = os.getenv('MCP_TRANSPORT', 'sse')

# Authentication configuration
BEARER_TOKEN = os.getenv('BEARER_TOKEN', '').strip()
AUTH_ENABLED = bool(BEARER_TOKEN)

# Log startup information
logger.info("=" * 80)
logger.info("UptimeCheck MCP Server Starting")
logger.info("=" * 80)
logger.info(f"Python version: {sys.version}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info(f"Log level: {log_level}")
logger.info(f"Authentication: {'ENABLED' if AUTH_ENABLED else 'DISABLED'}")
if AUTH_ENABLED:
    logger.info(f"Bearer token: {'*' * 8}...{BEARER_TOKEN[-4:] if len(BEARER_TOKEN) > 4 else '****'}")
else:
    logger.warning("⚠️  No BEARER_TOKEN set - authentication is DISABLED")
logger.info(f"Environment variables:")
for key, value in os.environ.items():
    if key.startswith('MCP_') or key in ['LOG_LEVEL', 'PYTHONUNBUFFERED', 'BEARER_TOKEN']:
        if key == 'BEARER_TOKEN' and value:
            logger.info(f"  {key}={'*' * 8}...{value[-4:] if len(value) > 4 else '****'}")
        else:
            logger.info(f"  {key}={value}")
logger.info("=" * 80)
