# Kubernetes Deployment Guide

Complete Kubernetes manifests for deploying the UptimeCheck MCP Server.

## Quick Start

### 1. Create Namespace

```bash
kubectl create namespace mcp
```

### 2. Create Secret (Optional - for Authentication)

**Option A: Via kubectl (Recommended)**
```bash
# Generate a secure random token
TOKEN=$(openssl rand -base64 32)
echo "Your token: $TOKEN"

# Create the secret
kubectl create secret generic mcp-bearer-token \
  --from-literal=token=$TOKEN \
  -n mcp
```

**Option B: Via YAML**
```bash
# Edit mcp-secret.yaml and add your token
kubectl apply -f k8s/mcp-secret.yaml
```

**Option C: Skip Authentication**
```bash
# Don't create the secret - authentication will be disabled
# The deployment is configured with optional: true for the secret
```

### 3. Apply Traefik Middleware

```bash
kubectl apply -f k8s/traefik-mcp-middleware.yaml
```

### 4. Deploy MCP Server

```bash
# Update the image in mcp-deployment.yaml first
kubectl apply -f k8s/mcp-deployment.yaml
```

### 5. Apply Ingress

```bash
kubectl apply -f k8s/mcp-checkuptime-ingress.yaml
```

### 6. Verify Deployment

```bash
# Check pods
kubectl get pods -n mcp

# Check service
kubectl get svc -n mcp

# Check ingress
kubectl get ingress -n mcp

# Check logs
kubectl logs -f -n mcp deployment/mcp-checkuptime

# Test health endpoint
kubectl exec -it -n mcp deployment/mcp-checkuptime -- wget -O- http://localhost:9000/health
```

## Files Overview

| File | Purpose |
|------|---------|
| `mcp-secret.yaml` | Bearer token for authentication (optional) |
| `mcp-deployment.yaml` | Deployment + Service definitions |
| `traefik-mcp-middleware.yaml` | Traefik middlewares for SSE/streaming |
| `mcp-checkuptime-ingress.yaml` | Ingress with middleware configuration |

## Configuration

### Environment Variables

Set in `mcp-deployment.yaml` under `spec.template.spec.containers[0].env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_HOST` | `0.0.0.0` | Bind address |
| `MCP_PORT` | `9000` | Server port |
| `MCP_TRANSPORT` | `sse` | Transport mode |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `PYTHONUNBUFFERED` | `1` | Python output buffering |
| `BEARER_TOKEN` | _(from secret)_ | Authentication token (optional) |

### Resource Limits

Default resource allocation:

```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

Adjust based on your workload:

```bash
kubectl edit deployment mcp-checkuptime -n mcp
```

### Replicas

Default: 2 replicas for high availability

Scale up/down:
```bash
kubectl scale deployment mcp-checkuptime -n mcp --replicas=3
```

## Authentication Setup

### With Bearer Token

1. **Create Secret**:
   ```bash
   kubectl create secret generic mcp-bearer-token \
     --from-literal=token=your-secret-token-here \
     -n mcp
   ```

2. **Verify Secret**:
   ```bash
   kubectl get secret mcp-bearer-token -n mcp -o jsonpath='{.data.token}' | base64 -d
   ```

3. **Test with Token**:
   ```bash
   TOKEN=$(kubectl get secret mcp-bearer-token -n mcp -o jsonpath='{.data.token}' | base64 -d)
   
   curl -X POST https://mcp-checkuptime.your-domain.com \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","method":"initialize","id":1}'
   ```

### Without Authentication

1. **Don't create the secret** - the deployment will start without authentication
2. **Or delete existing secret**:
   ```bash
   kubectl delete secret mcp-bearer-token -n mcp
   kubectl rollout restart deployment/mcp-checkuptime -n mcp
   ```

## Ingress Configuration

The ingress is configured with:
- ✅ SSL/TLS termination
- ✅ Traefik middlewares for SSE support
- ✅ CORS headers
- ✅ No-buffer configuration

### Update Domain

Edit `k8s/mcp-checkuptime-ingress.yaml`:

```yaml
spec:
  rules:
    - host: mcp-checkuptime.your-domain.com  # Change this
```

### Using Different Ingress Controller

If not using Traefik, remove the middleware annotations:

```yaml
# Remove these annotations:
traefik.ingress.kubernetes.io/router.middlewares: ...
```

And configure buffering in your ingress controller (nginx example):

```yaml
annotations:
  nginx.ingress.kubernetes.io/proxy-buffering: "off"
  nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
```

## Troubleshooting

### Check Pod Status

```bash
# Get pod details
kubectl describe pod -n mcp -l app.kubernetes.io/name=mcp-uptimecheck

# Check logs
kubectl logs -f -n mcp deployment/mcp-checkuptime

# Get events
kubectl get events -n mcp --sort-by='.lastTimestamp'
```

### Secret Issues

```bash
# Verify secret exists
kubectl get secret mcp-bearer-token -n mcp

# Check if pod can access secret
kubectl exec -it -n mcp deployment/mcp-checkuptime -- env | grep BEARER_TOKEN
```

### Ingress Not Working

```bash
# Check ingress
kubectl describe ingress mcp-checkuptime -n mcp

# Check Traefik logs (if using Traefik)
kubectl logs -n traefik deployment/traefik | grep mcp

# Test internal service
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n mcp -- \
  curl http://mcp-checkuptime.mcp.svc.cluster.local:8080/health
```

### Health Check Failures

```bash
# Test health endpoint from inside pod
kubectl exec -it -n mcp deployment/mcp-checkuptime -- \
  wget -O- http://localhost:9000/health

# Check liveness/readiness probe status
kubectl describe pod -n mcp -l app.kubernetes.io/name=mcp-uptimecheck | grep -A5 "Liveness\|Readiness"
```

## Updating

### Update Image

```bash
# Edit deployment
kubectl edit deployment mcp-checkuptime -n mcp

# Or via kubectl set image
kubectl set image deployment/mcp-checkuptime \
  mcp-server=your-registry/mcp-checkuptime:2.1.0 \
  -n mcp

# Watch rollout
kubectl rollout status deployment/mcp-checkuptime -n mcp
```

### Update Configuration

```bash
# Edit environment variables
kubectl edit deployment mcp-checkuptime -n mcp

# Restart pods to pick up changes
kubectl rollout restart deployment/mcp-checkuptime -n mcp
```

### Update Secret

```bash
# Delete old secret
kubectl delete secret mcp-bearer-token -n mcp

# Create new secret
kubectl create secret generic mcp-bearer-token \
  --from-literal=token=new-token-here \
  -n mcp

# Restart deployment
kubectl rollout restart deployment/mcp-checkuptime -n mcp
```

## Rollback

```bash
# View rollout history
kubectl rollout history deployment/mcp-checkuptime -n mcp

# Rollback to previous version
kubectl rollout undo deployment/mcp-checkuptime -n mcp

# Rollback to specific revision
kubectl rollout undo deployment/mcp-checkuptime -n mcp --to-revision=2
```

## Complete Deployment Commands

```bash
# One-line complete deployment (with authentication)
kubectl create namespace mcp && \
kubectl create secret generic mcp-bearer-token --from-literal=token=$(openssl rand -base64 32) -n mcp && \
kubectl apply -f k8s/traefik-mcp-middleware.yaml && \
kubectl apply -f k8s/mcp-deployment.yaml && \
kubectl apply -f k8s/mcp-checkuptime-ingress.yaml && \
kubectl get pods -n mcp -w

# One-line complete deployment (without authentication)
kubectl create namespace mcp && \
kubectl apply -f k8s/traefik-mcp-middleware.yaml && \
kubectl apply -f k8s/mcp-deployment.yaml && \
kubectl apply -f k8s/mcp-checkuptime-ingress.yaml && \
kubectl get pods -n mcp -w
```

## Clean Up

```bash
# Delete everything
kubectl delete namespace mcp

# Or delete individually
kubectl delete -f k8s/mcp-checkuptime-ingress.yaml
kubectl delete -f k8s/mcp-deployment.yaml
kubectl delete -f k8s/traefik-mcp-middleware.yaml
kubectl delete secret mcp-bearer-token -n mcp
```

## Production Considerations

### High Availability

```yaml
# In mcp-deployment.yaml
spec:
  replicas: 3  # Increase replicas
  
  # Add pod anti-affinity
  affinity:
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
        - weight: 100
          podAffinityTerm:
            labelSelector:
              matchLabels:
                app.kubernetes.io/name: mcp-uptimecheck
            topologyKey: kubernetes.io/hostname
```

### Resource Tuning

Monitor and adjust based on actual usage:

```bash
# Monitor resource usage
kubectl top pod -n mcp -l app.kubernetes.io/name=mcp-uptimecheck

# Adjust if needed
kubectl set resources deployment mcp-checkuptime -n mcp \
  --requests=cpu=200m,memory=256Mi \
  --limits=cpu=1000m,memory=1Gi
```

### Monitoring

Add Prometheus annotations:

```yaml
# In deployment metadata
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "9000"
  prometheus.io/path: "/metrics"
```

### Backup

```bash
# Export current configuration
kubectl get deployment,service,ingress,secret -n mcp -o yaml > backup.yaml

# Restore from backup
kubectl apply -f backup.yaml
```

## N8N Integration

### Internal Service (Recommended)

In N8N MCP Client:
```
Endpoint: http://mcp-checkuptime.mcp.svc.cluster.local:8080
Server Transport: HTTP Streamable
Authentication: Bearer (if token configured)
Token: <from secret>
Tools to Include: All
```

### External URL

In N8N MCP Client:
```
Endpoint: https://mcp-checkuptime.your-domain.com
Server Transport: HTTP Streamable
Authentication: Bearer (if token configured)
Token: <your token>
Tools to Include: All
```

## Support

For issues and questions:
- **Logs**: `kubectl logs -f -n mcp deployment/mcp-checkuptime`
- **GitHub Issues**: https://github.com/your-repo/mcp-checkuptime/issues
- **Documentation**: [../README.md](../README.md)
