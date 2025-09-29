# Docker Network Fix for Ping Issues

## The Problem

Your MCP server is running in a Docker container with:
1. **Wrong ping syntax**: Using Windows ping syntax (`-n`, `-w`) in a Linux container
2. **Network isolation**: Docker container can't reach your internal network hosts (10.84.0.3, 127.0.0.1)

## The Solution

### Fix 1: Correct Ping Syntax ✅
The code now automatically detects the OS and uses:
- **Windows**: `ping -n 3 -w 5000 host`
- **Linux**: `ping -c 3 -W 5 host`

### Fix 2: Docker Network Access

You have three options:

#### Option A: Use Host Network Mode (Recommended for Internal Network Access)

**Using docker-compose (easiest):**
```bash
# Stop current container
docker-compose down

# Rebuild with new code
docker-compose build

# Start with host network
docker-compose up -d

# View logs
docker-compose logs -f
```

**Or using docker run:**
```bash
# Stop and remove old container
docker stop mcp-uptimecheck
docker rm mcp-uptimecheck

# Rebuild image
docker build -t uptimecheck-mcp-server .

# Run with host network
docker run -d \
  --name uptimecheck-mcp-server \
  --network host \
  uptimecheck-mcp-server:latest
```

**What host network mode does:**
- Container uses the host's network stack directly
- Can access all networks the host can access
- No port mapping needed (direct access to host ports)

#### Option B: Bridge Network with IP Routing

If you need container isolation but want network access:

```bash
docker run -d \
  --name uptimecheck-mcp-server \
  -p 9000:9000 \
  --add-host=host.docker.internal:host-gateway \
  uptimecheck-mcp-server:latest
```

Then ping hosts using their routable addresses.

#### Option C: Run Natively (No Docker)

If you're developing locally and don't need Docker:

```bash
# Install dependencies
pip install -r requirements.txt

# Run directly
python uptimecheck_server.py
```

This will use your native Windows environment and work with your network directly.

## Testing After Fix

### 1. Rebuild and Restart
```bash
docker-compose down
docker-compose build
docker-compose up -d
```

### 2. Check Logs
```bash
docker-compose logs -f
```

You should see:
```
Executing command on linux: ping -c 3 -W 5 10.84.0.3
```

### 3. Test from Open WebUI

Try pinging:
- `10.84.0.3` (your internal host)
- `127.0.0.1` (localhost within container)
- `8.8.8.8` (external IP)

### 4. Check Server Logs for Details

The logs will now show:
- What OS is detected
- Exact ping command used
- Return code and output
- Whether it succeeded or failed

## Troubleshooting

### If Still Getting Timeouts

1. **Check container network:**
   ```bash
   docker exec uptimecheck-mcp-server ping -c 3 10.84.0.3
   ```

2. **Check if curl works:**
   ```bash
   docker exec uptimecheck-mcp-server curl -I http://10.84.0.3
   ```

3. **Verify host network mode:**
   ```bash
   docker inspect uptimecheck-mcp-server | grep NetworkMode
   ```
   Should show: `"NetworkMode": "host"`

4. **Check from within container:**
   ```bash
   docker exec -it uptimecheck-mcp-server /bin/bash
   ping -c 3 10.84.0.3
   exit
   ```

### If Website Check Works But Ping Doesn't

This suggests:
- ICMP is blocked but TCP/HTTP works
- Use the website check endpoint instead
- Some hosts don't respond to ping but are online

## Alternative: Use Website Check for Internal Hosts

If your internal hosts have web servers:
```bash
# Instead of pinging 10.84.0.3
# Check HTTP connectivity
curl http://localhost:9000/check-website?url=http://10.84.0.3
```

This is often more reliable than ping!

## Current Status

✅ **Ping syntax fixed** - Now works on both Windows and Linux
✅ **Docker compose config added** - Easy deployment with host network
✅ **Better logging added** - See exactly what's happening
✅ **OS detection added** - Automatic platform detection

## Next Steps

1. Run `docker-compose down && docker-compose build && docker-compose up -d`
2. Check logs: `docker-compose logs -f`
3. Try ping from Open WebUI
4. Check server logs for detailed output
