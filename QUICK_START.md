# 🚀 Quick Start Guide

**Deploy Real Debrid Media Manager in 5 minutes with pre-built image**

## ⚡ Super Quick Deploy

```bash
# 1. Create .env file with your API key
echo "REAL_DEBRID_API_KEY=your_api_key_here" > .env

# 2. Download pre-built compose file
curl -O https://raw.githubusercontent.com/Optimism-Bliss/Real-debrid-Strm/main/docker-compose.prebuilt.yml

# 3. Start container
docker-compose -f docker-compose.prebuilt.yml up -d

# 4. Monitor logs
docker-compose -f docker-compose.prebuilt.yml logs -f
```

## 📋 Step-by-Step

### 1. **Get Your Real Debrid API Key**
- Go to [Real Debrid API](https://real-debrid.com/apitoken)
- Generate new token
- Copy the key

### 2. **Setup Environment**
```bash
# Create directory
mkdir realdebrid-media && cd realdebrid-media

# Create environment file
cat > .env << 'EOF'
REAL_DEBRID_API_KEY=your_api_key_here
CYCLE_INTERVAL_MINUTES=20
FILE_EXPIRY_DAYS=14
LOG_LEVEL=INFO
EOF
```

### 3. **Create Docker Compose**
```yaml
# Save as docker-compose.yml
version: '3.8'
services:
  realdebrid-media:
    image: ghcr.io/optimism-bliss/real-debrid-strm:latest
    container_name: realdebrid-media
    restart: unless-stopped
    environment:
      - REAL_DEBRID_API_KEY=${REAL_DEBRID_API_KEY}
      - CYCLE_INTERVAL_MINUTES=${CYCLE_INTERVAL_MINUTES:-20}
      - FILE_EXPIRY_DAYS=${FILE_EXPIRY_DAYS:-14}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    volumes:
      - ./media:/app/media          # Jellyfin media folder
      - ./logs:/app/logs            # Application logs
      - ./output:/app/output        # STRM files and tracking
    user: "0:0"
    healthcheck:
      test: ["CMD", "python", "-c", "import os; exit(0 if os.path.exists('/app/logs') else 1)"]
      interval: 2m
      timeout: 30s
      retries: 3
```

### 4. **Deploy**
```bash
# Start container
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f realdebrid-media
```

## 📊 Expected Output

```
🔄 Starting new processing cycle
📊 Cycle Status:
   📁 Existing STRM files: 0
   📅 Expired files (>14 days): 0
   🔄 Retry queue: 0 items
📡 Fetching fresh data from Real Debrid API
🔍 Processing Results:
   📂 Total torrents found: 150
   ✅ Files processed: 120
   ⏭️  Skipped existing: 0
✅ Cycle completed in 45.2s
💤 Waiting 20 minutes for next cycle...
```

## 📁 Directory Structure

```
realdebrid-media/
├── .env                    # Your API key
├── docker-compose.yml      # Container config
├── media/                  # → Mount to Jellyfin
│   └── unorganized/        # All STRM files here
├── logs/                   # Application logs
└── output/                 # Tracking data
    ├── file_tracking.json  # File database
    └── retry_queue.json    # Error recovery
```

## 🎯 Jellyfin Integration

```bash
# Point Jellyfin library to:
/path/to/realdebrid-media/media/unorganized/

# Jellyfin will automatically:
✅ Detect movies and TV shows
✅ Play STRM files directly
✅ Fetch metadata and artwork
✅ Create collections and continue watching
```

## 🔧 Configuration

### Environment Variables
```bash
# .env file options
REAL_DEBRID_API_KEY=your_key_here      # Required
CYCLE_INTERVAL_MINUTES=20              # Default: 20
FILE_EXPIRY_DAYS=14                    # Default: 14
RETRY_503_ATTEMPTS=2                   # Default: 2
RETRY_429_ATTEMPTS=3                   # Default: 3
LOG_LEVEL=INFO                         # DEBUG/INFO/WARNING/ERROR
```

### Resource Tuning
```yaml
# For large libraries (>5000 torrents)
environment:
  - CYCLE_INTERVAL_MINUTES=60          # Less frequent
  - LOG_LEVEL=WARNING                  # Reduce logs
  
# For small libraries (<1000 torrents)  
environment:
  - CYCLE_INTERVAL_MINUTES=10          # More frequent
  - FILE_EXPIRY_DAYS=30                # Longer cache
```

## 🛠️ Troubleshooting

### Common Issues
```bash
# Check container status
docker-compose ps

# View detailed logs
docker-compose logs --tail=100 realdebrid-media

# Restart container
docker-compose restart

# Update to latest image
docker-compose pull && docker-compose up -d
```

### Container Not Starting?
- Check `.env` file has valid API key
- Ensure ports 8000 not in use
- Verify Docker is running

### No Files Generated?
- Check API key is valid
- Monitor logs for 503/429 errors
- Verify Real Debrid has torrents

### Files Not Refreshing?
- Check `FILE_EXPIRY_DAYS` setting
- Look at `file_tracking.json` timestamps
- Ensure sufficient disk space

## 🔄 Updates

```bash
# Get latest image
docker-compose pull

# Restart with new image
docker-compose up -d

# Check version
docker-compose exec realdebrid-media python --version
```

## 📞 Support

- 📖 **Full Documentation**: [README.md](README.md)
- 🐳 **Container Issues**: Check logs first
- 🔧 **Configuration Help**: [DOCUMENTATION.md](DOCUMENTATION.md)
- 🌐 **Portainer Deploy**: [PORTAINER_DEPLOY.md](PORTAINER_DEPLOY.md)

---

**Ready to deploy in 5 minutes!** 🎉 