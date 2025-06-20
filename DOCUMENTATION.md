# 📚 Real Debrid Media Manager - Complete Documentation

## 📖 Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Output Structure](#output-structure)
6. [Processing Workflow](#processing-workflow)
7. [Error Handling](#error-handling)
8. [Monitoring](#monitoring)
9. [TrueNAS Deployment](#truenas-deployment)
10. [Troubleshooting](#troubleshooting)

---

## 📋 Overview

Real Debrid Media Manager is a production-ready Docker container that automatically processes Real Debrid torrents and creates organized STRM files for media servers like Jellyfin and Plex.

### Key Improvements (v2.0)

- **Full Pagination Support** - No longer limited to first page of torrents
- **Intelligent File Filtering** - Automatically removes ads, trailers, and junk files
- **Improved Rate Limiting** - Respects API limits with exponential backoff
- **Unified Organization** - All content goes to `/media/unorganized/` for AI classification
- **Standard Permissions** - Files created with regular user permissions

## 📋 Features

### Core Functionality
- ✅ **Complete Torrent Processing** - Fetches ALL torrents via pagination
- ✅ **Smart Filtering** - Only processes video files ≥300MB + subtitle files
- ✅ **Torrent-Based Grouping** - Organizes files by original torrent structure
- ✅ **Extension Cleanup** - Removes extensions from folder names for single files
- ✅ **Rate Limit Protection** - 200 req/min with retry logic
- ✅ **Error Recovery** - Handles server issues and temporary failures

### File Support
- **Video Files**: `.mkv`, `.mp4`, `.avi`, `.mov`, `.wmv`, `.m4v`, `.webm`, `.flv`
- **Subtitle Files**: `.srt`, `.ass`, `.vtt`, `.sub`, `.idx`, `.ssa`, `.smi`
- **Size Filtering**: Videos must be ≥300MB (configurable)

### Output Organization
All content is placed in `/media/unorganized/` for subsequent AI-powered classification.

---

## 🚀 Installation

### Prerequisites
- Docker & Docker Compose
- Real Debrid Premium Account
- API Key from [Real Debrid API](https://real-debrid.com/apitoken)

### Setup Steps

1. **Clone Repository**:
   ```bash
   git clone <repository>
   cd RealDB-Media
   ```

2. **Configure Environment**:
   ```bash
   cp env-example.txt .env
   nano .env  # Add your REAL_DEBRID_API_KEY
   ```

3. **Deploy**:
   ```bash
   docker-compose up --build -d
   ```

---

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REAL_DEBRID_API_KEY` | ✅ | - | Your Real Debrid API token |
| `SYNC_INTERVAL` | ❌ | 3600 | Sync interval in seconds (1 hour) |
| `LOG_LEVEL` | ❌ | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |

### Advanced Configuration

The filtering behavior can be customized by modifying `app/real_debrid_processor.py`:

```python
# File size filtering
self.min_video_size_mb = 300  # Minimum video size in MB

# Additional extensions
self.allowed_video_extensions.add('.mkv')
self.allowed_subtitle_extensions.add('.srt')
```

---

## 📁 Output Structure

All media is organized under a single unorganized directory:

```
/media/unorganized/
├── Family.Guy.S05.1080p.DSNP.WEB-DL.AAC2.0.H.264-PHOENiX/
│   ├── Family.Guy.S05E01.Stewie.Loves.Lois.1080p.DSNP.WEB-DL.AAC2.0.H.264-PHOENiX.strm
│   ├── Family.Guy.S05E02.Mother.Tucker.1080p.DSNP.WEB-DL.AAC2.0.H.264-PHOENiX.strm
│   └── ... (all episodes)
├── Interstellar.2014.2160p.PROPER.IMAX.REMUX/
│   └── Interstellar.2014.2160p.PROPER.IMAX.REMUX.strm
├── Modern.Family.Season.1-11/
│   ├── Modern.Family.S01E01.Pilot.strm
│   └── ... (250+ episodes)
└── Misc/
    └── (unmatched single files)
```

### File Ownership
- **All folders**: `root:root` (0:0)
- **All STRM files**: `root:root` (0:0)
- **Permissions**: 755 for directories, 644 for files

---

## 🔄 Processing Workflow

### 1. Torrent Fetching (Pagination)
```
📡 GET /api/torrents?page=1&limit=100  ✅ Page 1 (100 torrents)
📡 GET /api/torrents?page=2&limit=100  ✅ Page 2 (100 torrents)
📡 GET /api/torrents?page=3&limit=100  ✅ Page 3 (80 torrents)
📡 GET /api/torrents?page=4&limit=100  ❌ Empty → Stop
```

### 2. Link Unrestricting (Batch Processing)
```
🔗 Batch 1: 3 links → Rate limit 0.3s delay
🔗 Batch 2: 3 links → Rate limit 0.3s delay
...
🔗 Batch N: Handle 429/503 errors with retry
```

### 3. File Filtering
```
📁 Total files: 3,000
✅ Video files ≥300MB: 1,800
✅ Subtitle files: 200
🚫 Small videos (<300MB): 950
🚫 Other file types: 50
```

### 4. STRM File Creation
```
📦 Create folder: /media/unorganized/{torrent_name}/
📄 Create STRM: {filename}.strm → {direct_url}
🔧 Set ownership: root:root
```

---

## 🎯 Error Handling

### Rate Limiting (429 Errors)
- **Detection**: HTTP 429 "too_many_requests"
- **Response**: Exponential backoff (2s → 4s → 8s)
- **Max Retries**: 3 attempts per request
- **Prevention**: 200 req/min limit (conservative)

### Server Issues (503 Errors)
- **Detection**: HTTP 503 "hoster_unavailable"
- **Response**: Log warning and skip
- **Cause**: Real Debrid server temporary issues
- **Resolution**: Usually resolves automatically

### Network Issues
- **Connection timeouts**: Automatic retry
- **DNS failures**: Container restart recommended
- **API key issues**: Check .env configuration

---

## 📊 Monitoring

### Real-time Logs
```bash
# View live logs
docker-compose logs -f realdebrid-media

# Filter by error level
docker-compose logs realdebrid-media | grep ERROR
```

### Expected Log Output
```
🔄 Fetching torrents with pagination...
📄 Page 1: 100 torrents (total: 100)
📄 Page 2: 100 torrents (total: 200)
...
🎉 Fetched 1,500 total torrents from 15 pages

🔍 Filtering Results:
   📂 Total files found: 3,000
   ✅ Files processed: 2,000
   🚫 Filtered out:
      📼 Small videos (<300MB): 950
      📄 Other file types: 50

✅ Processing Complete!
   📊 Pagination: 15 pages, 1,500 torrents
   🔗 Unrestrict: 2,847/3,000 successful
   ❌ Errors:
      ⏱️  Rate limits: 5
      🔧 Server issues: 148
      ❓ Other: 0
   📄 STRM files: 2,000 created, 0 skipped
   ⏱️  Total time: 890.5s
```

### Health Monitoring
- Container auto-restarts on failure
- Health check every 30 seconds
- Graceful shutdown handling

---

## 📋 TrueNAS Deployment

See [TrueNAS-DEPLOY.md](TrueNAS-DEPLOY.md) for complete TrueNAS Scale setup instructions.

### Quick TrueNAS Setup
```yaml
# docker-compose.override.yml for TrueNAS
services:
  realdebrid-media:
    user: "950:950"  # TrueNAS apps user
    volumes:
      - /mnt/pool/apps/realdebrid/media:/app/media
      - /mnt/pool/apps/realdebrid/logs:/app/logs
      - /mnt/pool/apps/realdebrid/output:/app/output
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. "No torrents found"
- **Cause**: Invalid API key or no downloaded torrents
- **Solution**: Verify API key in .env and check Real Debrid account

#### 2. High rate limit errors (429)
- **Cause**: API rate limiting
- **Solution**: Container automatically handles this with backoff
- **Check**: Should be <5% of total requests

#### 3. Many server errors (503)
- **Cause**: Real Debrid server issues
- **Solution**: These are temporary, container will retry later
- **Check**: Should resolve within 1-24 hours

#### 4. Permission denied errors
- **Cause**: Container user permissions
- **Solution**: Ensure proper user mapping in docker-compose.yml

### Debug Mode

Enable debug logging for detailed information:
```bash
# In .env
LOG_LEVEL=DEBUG

# Restart container
docker-compose restart
```

### Performance Tuning

For large libraries (>5000 torrents):
```python
# In app/real_debrid_api_client.py
self.rate_limit_per_minute = 150  # More conservative
self.concurrency_limit = 2        # Reduce concurrent requests
```

### File Recovery

If processing fails midway:
- Existing STRM files are preserved
- Re-running will skip existing files
- Check `/app/output/` for raw API data backup

### Contact & Support

- Check container logs first
- Real Debrid API issues are usually temporary
- Container is designed to handle most errors automatically
- For persistent issues, verify API key and network connectivity

---

*Optimized for TrueNAS deployment with user 950:950*

---

*Last updated: $(date)*
*For latest updates, check the GitHub repository.* 