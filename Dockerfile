# Use Python slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set Python unbuffered mode
ENV PYTHONUNBUFFERED=1

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install system dependencies for ping and curl
RUN apt-get update && apt-get install -y iputils-ping curl && rm -rf /var/lib/apt/lists/*

# Copy the server code
COPY uptimecheck_fastmcp.py .
COPY uptimecheck_server.py .
COPY uptimecheck_modular.py .
COPY src/ ./src/

# Set environment variables for HTTP server
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=9000
ENV MCP_TRANSPORT=sse

# Authentication (optional - if not set, auth is disabled)
# Set this via docker-compose.yml or docker run -e BEARER_TOKEN=your-secret-token
# ENV BEARER_TOKEN=

# Expose the port
EXPOSE 9000

# Create non-root user
RUN useradd -m -u 1000 mcpuser && chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Run the server with Streamable HTTP and SSE
# Use modular version (recommended) or legacy monolithic version
CMD ["python", "uptimecheck_modular.py"]
# Alternative: CMD ["python", "uptimecheck_server.py"]
