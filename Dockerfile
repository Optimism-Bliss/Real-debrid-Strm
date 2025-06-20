# Multi-stage build for optimized container size
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /build

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim AS production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python packages from builder
COPY --from=builder /root/.local /usr/local

# Create app user for security (but we'll run as root for chown operations)
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Create directories with proper permissions
RUN mkdir -p /app/{media,logs,output,config} && \
    chown -R app:app /app

# Copy application code
COPY app/ ./app/
COPY *.py ./
COPY *.md ./

# Set Python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check for cycle system
HEALTHCHECK --interval=2m --timeout=30s --start-period=60s --retries=3 \
    CMD python -c "import sys, os; sys.exit(0 if os.path.exists('/app/logs') else 1)"

# Labels for container metadata
LABEL maintainer="Real Debrid Media Manager" \
      version="2.0.0" \
      description="Cycle-based Real Debrid media processor with intelligent retry logic" \
      features="20min-cycles,14day-expiry,503-retry,intelligent-skip"

# Run as root for file operations and chown permissions
# USER app  # Commented out - need root for media file operations

# Expose potential monitoring port (if needed in future)
EXPOSE 8000

# Run the cycle manager
CMD ["python", "-m", "app.main"] 