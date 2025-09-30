# Bearer Token Auth - Quick Start 🔐

## TL;DR

**No `BEARER_TOKEN` set = No authentication required** (default)  
**Set `BEARER_TOKEN` = All requests need Bearer token**

## Enable Authentication (3 Steps)

### 1. Generate a Token

```bash
openssl rand -hex 32
# Or
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Set in docker-compose.yml

```yaml
environment:
  - BEARER_TOKEN=your-generated-token-here
```

### 3. Restart

```bash
docker-compose down
docker-compose build
docker-compose up -d
```

## Usage

### Without Auth (Default)

```bash
curl http://localhost:9000/health
```

### With Auth (When BEARER_TOKEN is set)

```bash
curl http://localhost:9000/health \
  -H "Authorization: Bearer your-token-here"
```

## Examples

### Python

```python
import requests

headers = {"Authorization": "Bearer your-token-here"}
response = requests.post(
    "http://localhost:9000/ping",
    headers=headers,
    json={"host": "8.8.8.8"}
)
```

### N8N

```
HTTP Request Node:
  URL: http://localhost:9000/ping
  Headers:
    Authorization: Bearer your-token-here
  Body:
    {"host": "8.8.8.8"}
```

## Logs

### Auth Disabled:
```
Authentication: DISABLED
⚠️  No BEARER_TOKEN set - authentication is DISABLED
```

### Auth Enabled:
```
Authentication: ENABLED
Bearer token: ********...2345
```

## Errors

| Error | Cause | Fix |
|-------|-------|-----|
| 401 Unauthorized | No Authorization header | Add `-H "Authorization: Bearer token"` |
| 401 Unauthorized | Wrong format | Use `Bearer token` not just `token` |
| 403 Forbidden | Invalid token | Check token matches `BEARER_TOKEN` |

## Security Tips

✅ Use strong random tokens (32+ chars)  
✅ Store in `.env` file (add to `.gitignore`)  
✅ Use HTTPS in production  
✅ Rotate tokens regularly  

❌ Never commit tokens to git  
❌ Don't use simple tokens like "password123"  
❌ Don't share tokens publicly  

## Full Documentation

See [`BEARER_TOKEN_AUTH.md`](./BEARER_TOKEN_AUTH.md) for complete details.
