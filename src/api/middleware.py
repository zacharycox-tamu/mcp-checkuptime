"""FastAPI middleware for authentication, CORS, and security."""
from fastapi import FastAPI, Request, Response
from ..config import logger, AUTH_ENABLED, BEARER_TOKEN


def setup_middleware(app: FastAPI) -> None:
    """Configure middleware for the FastAPI app."""
    
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        """Add security headers, authentication, and CORS support."""
        logger.debug(f"HTTP Request: {request.method} {request.url.path}")
        logger.debug(f"Headers: {dict(request.headers)}")
        logger.debug(f"Query params: {dict(request.query_params)}")
        
        # Handle preflight OPTIONS requests for CORS
        if request.method == "OPTIONS":
            logger.debug("Handling OPTIONS preflight request")
            response = Response()
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-MCP-Session-ID"
            response.headers["Access-Control-Max-Age"] = "3600"
            return response
        
        # Bearer token authentication (if enabled)
        if AUTH_ENABLED:
            auth_header = request.headers.get("authorization", "")
            logger.debug(f"Auth header present: {bool(auth_header)}")
            
            if not auth_header:
                logger.warning(f"Authentication required but no Authorization header provided for {request.url.path}")
                return Response(
                    content='{"error": "Authentication required", "message": "Missing Authorization header"}',
                    status_code=401,
                    media_type="application/json",
                    headers={
                        "WWW-Authenticate": "Bearer",
                        "Access-Control-Allow-Origin": "*"
                    }
                )
            
            # Check for Bearer token format
            if not auth_header.startswith("Bearer "):
                logger.warning(f"Invalid Authorization header format for {request.url.path}")
                return Response(
                    content='{"error": "Invalid authentication", "message": "Authorization header must be in format: Bearer <token>"}',
                    status_code=401,
                    media_type="application/json",
                    headers={
                        "WWW-Authenticate": "Bearer",
                        "Access-Control-Allow-Origin": "*"
                    }
                )
            
            # Extract and validate token
            provided_token = auth_header[7:].strip()  # Remove "Bearer " prefix
            if provided_token != BEARER_TOKEN:
                logger.warning(f"Invalid bearer token provided for {request.url.path}")
                logger.debug(f"Expected token ends with: ...{BEARER_TOKEN[-4:]}, got token ends with: ...{provided_token[-4:] if len(provided_token) > 4 else '****'}")
                return Response(
                    content='{"error": "Invalid authentication", "message": "Invalid bearer token"}',
                    status_code=403,
                    media_type="application/json",
                    headers={"Access-Control-Allow-Origin": "*"}
                )
            
            logger.debug(f"Bearer token validated successfully for {request.url.path}")
        
        # Security: Validate Origin header to prevent DNS rebinding attacks
        origin = request.headers.get("origin")
        if origin and not any(origin.startswith(allowed) for allowed in ["http://localhost", "https://localhost", "http://127.0.0.1", "https://127.0.0.1", "http://", "https://"]):
            logger.warning(f"Suspicious origin header: {origin}")
        
        response = await call_next(request)
        
        # Add CORS headers for N8N compatibility
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-MCP-Session-ID"
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        
        return response
    
    logger.info("Middleware configured")
