# 🐳 Portainer Deployment Guide

Complete guide to deploy **Real Debrid Media Manager v2.0** using Portainer.

## 📋 Prerequisites

1. **Portainer installed** and running
   - Portainer CE/EE on Docker or Docker Swarm
   - Access to Portainer web interface

2. **Docker host** with sufficient resources
   - Min: 1GB RAM, 2GB disk space
   - Recommended: 2GB RAM, 10GB disk space

## 🚀 Method 1: Deploy from GitHub (Recommended)

### Step 1: Access Portainer

1. Open **Portainer web interface**
2. Navigate to **"Stacks"** in the sidebar
3. Click **"Add stack"**

### Step 2: Configure Stack

**Stack Configuration:**
```
Name: realdebrid-media-manager
Build method: Repository
```

**Repository Settings:**
```
Repository URL: https://github.com/Optimism-Bliss/Real-debrid-Strm
Reference: refs/heads/main
Compose path: docker-compose.portainer.yml
```

### Step 3: Environment Variables

Add these environment variables in Portainer:

| Variable | Value | Required |
|----------|-------|----------|
| `REAL_DEBRID_API_KEY` | `your_api_key_here` | ✅ **Required** |
| `CYCLE_INTERVAL_MINUTES` | `20` | Optional |
| `FILE_EXPIRY_DAYS` | `14` | Optional |
| `LOG_LEVEL` | `INFO` | Optional |
| `TZ` | `America/New_York` | Optional |
| `RETRY_503_ATTEMPTS` | `2` | Optional |
| `RETRY_429_ATTEMPTS` | `3` | Optional |

### Step 4: Volume Mapping

⚠️ **Important**: Update volume paths for your system:

**For Linux/TrueNAS:**
```yaml
volumes:
  - /mnt/pool/realdebrid/media:/app/media
  - /mnt/pool/realdebrid/logs:/app/logs
  - /mnt/pool/realdebrid/output:/app/output
  - /mnt/pool/realdebrid/config:/app/config
```

**For Windows Docker Desktop:**
```yaml
volumes:
  - C:\Docker\realdebrid\media:/app/media
  - C:\Docker\realdebrid\logs:/app/logs
  - C:\Docker\realdebrid\output:/app/output
  - C:\Docker\realdebrid\config:/app/config
```

### Step 5: Deploy

1. Click **"Deploy the stack"**
2. Wait for build to complete (3-5 minutes)
3. Check **"Containers"** section for status

## 🛠️ Method 2: Manual Docker Compose

### Step 1: Create Stack with Custom Compose

In Portainer **"Stacks"** → **"Add stack"** → **"Web editor"**:

```yaml
version: '3.8'

services:
  realdebrid-media:
    image: ghcr.io/optimism-bliss/real-debrid-strm:latest
    container_name: realdebrid-media
    restart: unless-stopped
    
    environment:
      - REAL_DEBRID_API_KEY=${REAL_DEBRID_API_KEY}
      - CYCLE_INTERVAL_MINUTES=20
      - FILE_EXPIRY_DAYS=14
      - LOG_LEVEL=INFO
      - PYTHONUNBUFFERED=1
      - TZ=UTC
      - RETRY_503_ATTEMPTS=2
      - RETRY_429_ATTEMPTS=3
    
    volumes:
      # Update these paths for your system
      - /your/media/path:/app/media
      - /your/logs/path:/app/logs
      - /your/output/path:/app/output
      - /your/config/path:/app/config
    
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
    
    healthcheck:
      test: ["CMD", "python", "-c", "import sys, os; sys.exit(0 if os.path.exists('/app/logs') else 1)"]
      interval: 2m
      timeout: 30s
      retries: 3
      start_period: 60s
```

## 📊 Portainer-Specific Configuration

### Environment Variables in Portainer

Navigate to **"Stacks"** → **Your Stack** → **"Environment variables"**:

```bash
# Core Configuration
REAL_DEBRID_API_KEY=F7EPLKXNZXQSTQF4PF75ALGQGGNDUMZFWLUK7GDKY2CA4AOLEUGQ

# Optional Tuning
CYCLE_INTERVAL_MINUTES=30     # Every 30 minutes
FILE_EXPIRY_DAYS=7           # Refresh weekly
LOG_LEVEL=DEBUG              # Detailed logging
TZ=America/New_York          # Your timezone
```

### Volume Management

1. **Create volumes** in Portainer first:
   - Go to **"Volumes"** → **"Add volume"**
   - Create: `realdebrid-media`, `realdebrid-logs`, `realdebrid-output`

2. **Use in stack**:
   ```yaml
   volumes:
     - realdebrid-media:/app/media
     - realdebrid-logs:/app/logs
     - realdebrid-output:/app/output
   ```

### Network Configuration

**Default (recommended):**
```yaml
networks:
  default:
    name: realdebrid-network
```

**Custom network:**
1. Create network in Portainer: **"Networks"** → **"Add network"**
2. Name: `realdebrid-net`
3. Driver: `bridge`

## 🔍 Monitoring in Portainer

### Container Logs
1. **"Containers"** → **"realdebrid-media"** → **"Logs"**
2. Enable **"Auto-refresh"** to see real-time logs
3. Filter by **"Error"** or **"Warning"** for troubleshooting

### Resource Usage
1. **"Containers"** → **"realdebrid-media"** → **"Stats"**
2. Monitor CPU, Memory, Network usage
3. Set up alerts if needed

### Health Checks
- **Green**: Container healthy
- **Yellow**: Starting up (first 60s)
- **Red**: Health check failing

## 🚨 Common Portainer Issues

### ❌ "Failed to deploy stack"

**Check:**
1. Repository URL is correct
2. `docker-compose.portainer.yml` exists in repo
3. Environment variables are set
4. Volume paths are valid

### ❌ "Build failed"

**Solutions:**
1. Use pre-built image instead of building from source
2. Check Dockerfile syntax
3. Ensure sufficient disk space

### ❌ "Container not starting"

**Debug steps:**
1. Check container logs in Portainer
2. Verify environment variables
3. Check volume mount permissions
4. Ensure API key is valid

### ❌ "Volume mount failed"

**Fix:**
1. Create directories on host first:
   ```bash
   mkdir -p /your/path/{media,logs,output,config}
   chmod 755 /your/path/{media,logs,output,config}
   ```

2. Update paths in stack configuration

## 🎯 Production Tips

### Auto-Update Setup

1. **Enable auto-pull** in stack settings
2. Set **webhook** for GitHub pushes
3. Configure **notification** endpoints

### Backup Strategy

1. **Volume backup** in Portainer
2. Export stack configuration
3. Backup environment variables

### Scaling

For multiple Real Debrid accounts:
1. Duplicate stack with different name
2. Use different API keys
3. Separate volume mounts

## 📱 Portainer App Integration

**For TrueNAS Scale:**
1. Use **TrueNAS Portainer app**
2. Configure through TrueNAS UI
3. Automatic volume management

**For Synology:**
1. Install **Portainer package**
2. Use Synology folder structure
3. Configure through DSM + Portainer

## 🎉 Expected Result

After successful deployment:

```
🔄 Container Status: Running (Green)
📊 Health Check: Healthy
📋 Logs showing:
   🚀 Real Debrid Media Manager Starting
   🔧 CycleManager Configuration: 20 minutes, 14 days
   🔄 Starting cycle scheduler...
   📊 Cycle Status: 0 existing files, 0 expired, 0 retry queue
   📡 Fetching fresh data from Real Debrid API...
```

## 🆘 Support

**Portainer Issues:**
- Check Portainer documentation
- Verify Docker daemon is running
- Ensure sufficient resources

**Application Issues:**
- Check container logs in Portainer
- Verify Real Debrid API key
- Monitor cycle completion

---

**Ready for production deployment with Portainer!** 🚀 