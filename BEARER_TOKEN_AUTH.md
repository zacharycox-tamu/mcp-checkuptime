# Bearer Token Authentication 🔐

## Overview

Bearer token authentication has been added to secure your MCP server. It's **optional** and can be enabled/disabled via environment variable.

## How It Works

### Authentication Disabled (Default)
If `BEARER_TOKEN` is **not set** or **empty**, all requests are allowed without authentication.

```yaml
environment:
  # No BEARER_TOKEN = No authentication required
  - MCP_HOST=0.0.0.0
  - MCP_PORT=9000
```

**Logs will show:**
```
Authentication: DISABLED
⚠️  No BEARER_TOKEN set - authentication is DISABLED
```

### Authentication Enabled
If `BEARER_TOKEN` is **set to any non-empty value**, all HTTP requests must include a valid Bearer token.

```yaml
environment:
  - BEARER_TOKEN=my-secret-token-12345
```

**Logs will show:**
```
Authentication: ENABLED
Bearer token: ********...2345
```

## Configuration

### Method 1: docker-compose.yml (Recommended)

```yaml
services:
  uptimecheck-server:
    build: .
    environment:
      - BEARER_TOKEN=your-secret-token-here
```

### Method 2: .env File (More Secure)

Create `.env` file:
```bash
BEARER_TOKEN=your-secret-token-here
```

Update `docker-compose.yml`:
```yaml
services:
  uptimecheck-server:
    build: .
    env_file:
      - .env
```

**Don't forget to add `.env` to `.gitignore`!**

### Method 3: Docker Run Command

```bash
docker run -d \
  -e BEARER_TOKEN=your-secret-token-here \
  -p 9000:9000 \
  uptimecheck-mcp
```

### Method 4: Docker Secrets (Production)

```yaml
services:
  uptimecheck-server:
    build: .
    environment:
      - BEARER_TOKEN_FILE=/run/secrets/bearer_token
    secrets:
      - bearer_token

secrets:
  bearer_token:
    file: ./bearer_token.txt
```

## Generating a Secure Token

### Option 1: OpenSSL
```bash
openssl rand -hex 32
# Output: a1b2c3d4e5f6...
```

### Option 2: Python
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Output: xyz123abc456...
```

### Option 3: uuidgen
```bash
uuidgen
# Output: 550e8400-e29b-41d4-a716-446655440000
```

## Using Bearer Token Authentication

### cURL Example

```bash
# Without auth (if BEARER_TOKEN not set)
curl http://localhost:9000/health

# With auth (if BEARER_TOKEN is set)
curl http://localhost:9000/health \
  -H "Authorization: Bearer your-secret-token-here"
```

### Python Example

```python
import requests

token = "your-secret-token-here"
headers = {"Authorization": f"Bearer {token}"}

response = requests.post(
    "http://localhost:9000/ping",
    headers=headers,
    json={"host": "8.8.8.8"}
)
print(response.json())
```

### JavaScript/Node.js Example

```javascript
const token = "your-secret-token-here";

fetch("http://localhost:9000/ping", {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({ host: "8.8.8.8" })
})
  .then(res => res.json())
  .then(data => console.log(data));
```

### N8N HTTP Request Node

```json
{
  "url": "http://localhost:9000/ping",
  "method": "POST",
  "headers": {
    "Authorization": "Bearer your-secret-token-here"
  },
  "body": {
    "host": "8.8.8.8"
  }
}
```

## Error Responses

### Missing Authorization Header (401)

**Request:**
```bash
curl http://localhost:9000/health
```

**Response:**
```json
{
  "error": "Authentication required",
  "message": "Missing Authorization header"
}
```

**HTTP Status:** `401 Unauthorized`  
**Headers:** `WWW-Authenticate: Bearer`

### Invalid Format (401)

**Request:**
```bash
curl http://localhost:9000/health \
  -H "Authorization: wrong-format"
```

**Response:**
```json
{
  "error": "Invalid authentication",
  "message": "Authorization header must be in format: Bearer <token>"
}
```

**HTTP Status:** `401 Unauthorized`

### Invalid Token (403)

**Request:**
```bash
curl http://localhost:9000/health \
  -H "Authorization: Bearer wrong-token"
```

**Response:**
```json
{
  "error": "Invalid authentication",
  "message": "Invalid bearer token"
}
```

**HTTP Status:** `403 Forbidden`

## CORS Support

Bearer token authentication works with CORS:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Headers: Content-Type, Authorization, X-MCP-Session-ID
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
```

Preflight OPTIONS requests are always allowed (no auth required).

## Logging

### Successful Authentication

```
DEBUG - Auth header present: True
DEBUG - Bearer token validated successfully for /health
```

### Failed Authentication

```
WARNING - Authentication required but no Authorization header provided for /health
WARNING - Invalid bearer token provided for /health
DEBUG - Expected token ends with: ...2345, got token ends with: ...9999
```

### Token Masking in Logs

The bearer token is **never logged in full**. Only the last 4 characters are shown:

```
INFO - Bearer token: ********...2345
```

## Security Best Practices

### ✅ DO:

1. **Use strong random tokens** (at least 32 characters)
2. **Store tokens in environment variables or secrets**
3. **Use HTTPS in production** (not HTTP)
4. **Rotate tokens regularly**
5. **Use different tokens for dev/staging/prod**
6. **Never commit tokens to git**
7. **Add `.env` to `.gitignore`**

### ❌ DON'T:

1. **Don't use simple/guessable tokens** (e.g., "password123")
2. **Don't hardcode tokens in Dockerfile**
3. **Don't expose tokens in logs**
4. **Don't share tokens publicly**
5. **Don't use the same token across environments**

## Testing

### Test Without Authentication

```bash
# Remove or comment out BEARER_TOKEN
docker-compose down
docker-compose up -d

# Should work without auth
curl http://localhost:9000/health
```

### Test With Authentication

```bash
# Set BEARER_TOKEN in docker-compose.yml
environment:
  - BEARER_TOKEN=test-token-12345

docker-compose down
docker-compose up -d

# Should fail without token
curl http://localhost:9000/health
# Response: 401 Unauthorized

# Should work with correct token
curl http://localhost:9000/health \
  -H "Authorization: Bearer test-token-12345"
# Response: 200 OK
```

## Deployment Scenarios

### Development (No Auth)

```yaml
# docker-compose.dev.yml
environment:
  # No BEARER_TOKEN - easy testing
  - LOG_LEVEL=DEBUG
```

### Staging (With Auth)

```yaml
# docker-compose.staging.yml
environment:
  - BEARER_TOKEN=staging-token-abc123
  - LOG_LEVEL=INFO
```

### Production (With Auth + HTTPS)

```yaml
# docker-compose.prod.yml
environment:
  - BEARER_TOKEN=${BEARER_TOKEN}  # From .env or secrets
  - LOG_LEVEL=WARNING
```

Plus use a reverse proxy (nginx/traefik) with HTTPS:

```nginx
server {
    listen 443 ssl;
    server_name mcp-checkuptime.example.com;
    
    ssl_certificate /etc/ssl/cert.pem;
    ssl_certificate_key /etc/ssl/key.pem;
    
    location / {
        proxy_pass http://localhost:9000;
        proxy_set_header Authorization $http_authorization;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Health Check Endpoint

The `/health` endpoint also requires authentication when enabled:

```bash
# Without auth (BEARER_TOKEN not set)
curl http://localhost:9000/health

# With auth (BEARER_TOKEN set)
curl http://localhost:9000/health \
  -H "Authorization: Bearer your-token"
```

For monitoring tools, consider:
1. Creating a separate health check token
2. Using an internal health endpoint (without auth)
3. Checking from within the Docker network

## Multiple Tokens (Future Enhancement)

Currently supports single token. For multiple users/services, consider:

1. **API Gateway**: Use Kong/Traefik for multi-token auth
2. **JWT Tokens**: Upgrade to JWT with user claims
3. **API Keys**: Use database-backed API key system

## Troubleshooting

### Issue: "Authentication required" but token is set

**Check:**
```bash
docker-compose logs | grep "Authentication:"
```

**Should show:**
```
Authentication: ENABLED
```

**If shows `DISABLED`:**
- Check `BEARER_TOKEN` in docker-compose.yml
- Rebuild: `docker-compose build --no-cache`
- Restart: `docker-compose up -d`

### Issue: Token works in curl but not in browser/app

**Cause:** CORS preflight request

**Solution:** Browser sends OPTIONS first, then actual request. Make sure your app includes Authorization header in the main request, not just OPTIONS.

### Issue: 403 Forbidden with correct token

**Check logs:**
```bash
docker-compose logs | grep "Expected token ends with"
```

**Common causes:**
- Extra spaces in token
- Token copied incorrectly
- Token changed but client not updated
- Using different tokens in env vs client

## Summary

| Setting | Auth Status | Use Case |
|---------|-------------|----------|
| No `BEARER_TOKEN` | ❌ Disabled | Development, testing |
| `BEARER_TOKEN=""` | ❌ Disabled | Same as not set |
| `BEARER_TOKEN=xyz` | ✅ Enabled | Production, secure deployments |

**Simple rule:** Set `BEARER_TOKEN` to any non-empty string = authentication enabled!

## Quick Start

### Enable Auth Right Now:

1. Edit `docker-compose.yml`:
   ```yaml
   - BEARER_TOKEN=my-secret-token-12345
   ```

2. Restart:
   ```bash
   docker-compose down
   docker-compose build
   docker-compose up -d
   ```

3. Test:
   ```bash
   # This will fail (401)
   curl http://localhost:9000/health
   
   # This will work (200)
   curl http://localhost:9000/health \
     -H "Authorization: Bearer my-secret-token-12345"
   ```

Done! 🎉
