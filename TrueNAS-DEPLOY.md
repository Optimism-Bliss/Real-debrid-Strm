# TrueNAS Scale Deployment Guide

Complete guide for deploying Real Debrid Media Manager on TrueNAS Scale with proper permissions and directory structure.

## 🎯 Overview

This container organizes all media under `/media/unorganized/` for subsequent AI-powered classification, making it perfect for automated media management workflows.

## 📋 Prerequisites

- TrueNAS Scale 22.12 or later
- Real Debrid Premium account with API key
- Docker/Kubernetes experience (basic)

## 🚀 Quick Deploy

### Step 1: Prepare Directories

```bash
# SSH into TrueNAS
ssh root@truenas-ip

# Create app directories with proper ownership
mkdir -p /mnt/tank/apps/realdebrid/{media,logs,output,config}
chown -R 950:950 /mnt/tank/apps/realdebrid/
chmod -R 755 /mnt/tank/apps/realdebrid/
```

### Step 2: Create Docker Compose

Create `/mnt/tank/apps/realdebrid/docker-compose.yml`:

```yaml
version: '3.8'

services:
  realdebrid-media:
    build: .
    container_name: realdebrid-media
    restart: unless-stopped
    user: "950:950"  # TrueNAS apps user
    
    environment:
      - REAL_DEBRID_API_KEY=${REAL_DEBRID_API_KEY}
      - SYNC_INTERVAL=3600
      - LOG_LEVEL=INFO
    
    volumes:
      # Main output directory - organized under /unorganized/
      - /mnt/tank/apps/realdebrid/media:/app/media
      
      # Application logs
      - /mnt/tank/apps/realdebrid/logs:/app/logs
      
      # Raw API data backup
      - /mnt/tank/apps/realdebrid/output:/app/output
      
      # Configuration
      - /mnt/tank/apps/realdebrid/config:/app/config
    
    healthcheck:
      test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Step 3: Environment Configuration

Create `/mnt/tank/apps/realdebrid/.env`:

```bash
# Real Debrid API Configuration
REAL_DEBRID_API_KEY=your_real_debrid_api_key_here

# Processing Configuration
SYNC_INTERVAL=3600
LOG_LEVEL=INFO

# Container Configuration
PYTHONUNBUFFERED=1
TZ=America/New_York
```

### Step 4: Deploy

```bash
cd /mnt/tank/apps/realdebrid
docker-compose up -d --build
```

## 📁 Directory Structure

After deployment, your directory structure will look like:

```
/mnt/tank/apps/realdebrid/
├── docker-compose.yml
├── .env
├── media/unorganized/          # ← All STRM files organized here
│   ├── Family.Guy.S05.../
│   ├── Interstellar.2014.../
│   ├── Modern.Family.../
│   └── Misc/
├── logs/
│   └── realdebrid.log
├── output/                     # Raw API data
│   ├── realdebrid_torrents.json
│   ├── realdebrid_unrestricted.json
│   └── realdebrid_links.txt
└── config/
    └── settings.yaml
```

## 🔧 TrueNAS Integration

### Media Server Integration

Configure Jellyfin/Plex to scan the unorganized directory:

```yaml
# Jellyfin Library Path
/mnt/tank/apps/realdebrid/media/unorganized

# Plex Library Path
/mnt/tank/apps/realdebrid/media/unorganized
```

### Automated Classification

Set up AI-powered classification using the unorganized structure:

```bash
# Example: OpenAI-powered classification script
/mnt/tank/scripts/classify_media.py \
  --input /mnt/tank/apps/realdebrid/media/unorganized \
  --tv-output /mnt/tank/media/tv \
  --movie-output /mnt/tank/media/movies
```

## 🔍 Monitoring & Maintenance

### View Logs
```bash
# Real-time logs
docker-compose logs -f realdebrid-media

# Filter errors only
docker-compose logs realdebrid-media | grep ERROR
```

### Health Monitoring
```bash
# Check container status
docker-compose ps

# Container health
docker inspect realdebrid-media | grep -A5 Health
```

### Expected Output
```
🔄 Fetching torrents with pagination...
🎉 Fetched 1,500 total torrents from 15 pages
🔍 Filtering Results:
   📂 Total files found: 3,000
   ✅ Files processed: 2,000
✅ Processing Complete!
   📄 STRM files: 2,000 created in /media/unorganized/
```

## 🛠️ Advanced Configuration

### Custom File Filtering

Modify filtering in `app/real_debrid_processor.py`:

```python
# Adjust minimum video size
self.min_video_size_mb = 500  # Stricter filtering

# Add custom extensions
self.allowed_video_extensions.add('.ts')
self.allowed_subtitle_extensions.add('.vtt')
```

### Performance Tuning

For large libraries:

```yaml
# In docker-compose.yml
environment:
  - SYNC_INTERVAL=7200  # Every 2 hours
  - LOG_LEVEL=WARNING   # Reduce log volume
```

### Rate Limiting Adjustment

For premium accounts with higher limits:

```python
# In app/real_debrid_api_client.py
self.rate_limit_per_minute = 300  # Higher rate
self.concurrency_limit = 5        # More concurrent requests
```

## 🔒 Security Considerations

### API Key Protection
- Store API key in `.env` file with restricted permissions
- Never commit API key to version control
- Rotate API keys periodically

### Container Security
```bash
# Set proper ownership
chown -R 950:950 /mnt/tank/apps/realdebrid/

# Restrict permissions
chmod 600 /mnt/tank/apps/realdebrid/.env
chmod 755 /mnt/tank/apps/realdebrid/media
```

## 🚨 Troubleshooting

### Common TrueNAS Issues

#### 1. Permission Denied
```bash
# Fix ownership
chown -R 950:950 /mnt/tank/apps/realdebrid/
```

#### 2. Container Won't Start
```bash
# Check logs
docker-compose logs realdebrid-media

# Verify .env file
cat /mnt/tank/apps/realdebrid/.env
```

#### 3. No Files Created
- Verify API key is valid
- Check Real Debrid account has downloaded torrents
- Ensure proper volume mounting

### Performance Issues

#### High Memory Usage
```yaml
# Add memory limits
deploy:
  resources:
    limits:
      memory: 1G
    reservations:
      memory: 512M
```

#### Slow Processing
- Reduce `concurrency_limit` in API client
- Increase `SYNC_INTERVAL` to reduce frequency
- Check TrueNAS storage performance

## 📞 Support

### Log Analysis
Most issues can be diagnosed from container logs:

```bash
# Full logs
docker-compose logs realdebrid-media > debug.log

# Error analysis
grep -E "(ERROR|WARNING)" debug.log
```

### Common Log Patterns
- `503 errors`: Real Debrid server issues (temporary)
- `429 errors`: Rate limiting (should be <5% with proper config)
- `Permission denied`: TrueNAS ownership issues

### Contact Information
- Check container logs first
- Verify TrueNAS permissions (user 950:950)
- Ensure Real Debrid API key is valid

---

*Optimized for TrueNAS Scale with automated media classification workflows* 