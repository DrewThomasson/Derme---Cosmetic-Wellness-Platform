# Docker Deployment Guide for Derme

This guide explains how to run the Derme application using Docker and Docker Compose.

## Prerequisites

- Docker installed (version 20.10 or higher)
- Docker Compose v2 (included with Docker Desktop)
- (Optional) Google Gemini API key for AI features

## Quick Start

### 1. Using Docker Compose (Recommended)

**Basic setup (without AI features):**

```bash
# Build and start the container
docker compose up -d

# View logs
docker compose logs -f

# Access the application
# Open browser: http://localhost:7860
```

**With AI features enabled:**

```bash
# Create .env file with your Gemini API key
echo "GEMINI_API_KEY=your-api-key-here" > .env

# Build and start
docker compose up -d

# Access the application
# Open browser: http://localhost:7860
```

### 2. Using Docker directly

**Build the image:**
```bash
docker build -t derme-app .
```

**Run without AI:**
```bash
docker run -d \
  --name derme \
  -p 7860:7860 \
  -v $(pwd)/instance:/app/instance \
  -v $(pwd)/static/uploads:/app/static/uploads \
  derme-app
```

**Run with AI features:**
```bash
docker run -d \
  --name derme \
  -p 7860:7860 \
  -e GEMINI_API_KEY=your-api-key-here \
  -v $(pwd)/instance:/app/instance \
  -v $(pwd)/static/uploads:/app/static/uploads \
  derme-app
```

## Configuration

### Environment Variables

Configure the application by setting environment variables in a `.env` file:

```bash
# Copy the example file
cp .env.example .env

# Edit with your settings
nano .env
```

**Available variables:**

```bash
# Required for production
SECRET_KEY=your-secret-key-here

# Google Gemini API (optional)
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-1.5-flash

# Feature flags
USE_GEMINI_FOR_OCR=true
USE_GEMINI_FOR_ALLERGEN_INFO=true
FALLBACK_TO_TESSERACT=true

# Analysis settings
CONFIDENCE_THRESHOLD=0.6
MAX_ALLERGEN_SYNONYMS=10
```

### Persistent Data

The Docker setup uses volumes to persist data locally:

- **Database**: `./instance/derme.db` - User data, allergens, products
- **Uploads**: `./static/uploads/` - Uploaded product images

These directories are created automatically and mounted from your local filesystem.

## Common Operations

### View Logs
```bash
# All logs
docker compose logs -f

# Last 100 lines
docker compose logs --tail=100
```

### Stop the Application
```bash
docker compose down
```

### Restart the Application
```bash
docker compose restart
```

### Rebuild After Code Changes
```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Access Container Shell
```bash
docker compose exec derme-app /bin/bash
```

### Remove Everything (including volumes)
```bash
docker compose down -v
```

## Port Configuration

By default, the application runs on port **7860**. To use a different port:

**Edit docker-compose.yml:**
```yaml
ports:
  - "8080:7860"  # Access on port 8080
```

## Troubleshooting

### Container won't start

**Check logs:**
```bash
docker compose logs derme-app
```

**Common issues:**
- Port 7860 already in use → Change port mapping
- Permission issues → Check volume mount permissions
- Missing dependencies → Rebuild: `docker compose build --no-cache`

### Database errors

**Reset database:**
```bash
docker compose down
rm -f instance/derme.db
docker compose up -d
```

### Out of memory

**Increase Docker memory:**
- Docker Desktop → Settings → Resources → Memory
- Allocate at least 2GB RAM

### Tesseract OCR not working

**Verify installation:**
```bash
docker compose exec derme-app tesseract --version
```

### Gemini API not working

**Check API key:**
```bash
docker compose exec derme-app printenv GEMINI_API_KEY
```

**Verify connectivity:**
```bash
docker compose exec derme-app curl -I https://generativelanguage.googleapis.com
```

## Production Deployment

For production environments:

### 1. Security

```bash
# Generate secure secret key
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')

# Add to .env file
echo "SECRET_KEY=$SECRET_KEY" >> .env
```

### 2. Disable Debug Mode

**Modify app.py** before building:
```python
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=7860, debug=False)  # Set debug=False
```

### 3. Use Production Server

**Replace CMD in Dockerfile:**
```dockerfile
# Install gunicorn
RUN pip install gunicorn

# Use gunicorn instead of Flask dev server
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:7860", "app:app"]
```

### 4. Enable HTTPS

Use a reverse proxy like Nginx or Traefik for SSL/TLS termination.

### 5. Resource Limits

**Add to docker-compose.yml:**
```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 512M
```

## Health Checks

The container includes a health check that verifies the application is responding:

```bash
# Check health status
docker compose ps

# Manual health check
curl http://localhost:7860
```

## Backup and Restore

### Backup
```bash
# Backup database
cp instance/derme.db instance/derme.db.backup

# Or create tarball
tar -czf derme-backup-$(date +%Y%m%d).tar.gz instance/ static/uploads/
```

### Restore
```bash
# Stop application
docker compose down

# Restore database
cp instance/derme.db.backup instance/derme.db

# Or extract tarball
tar -xzf derme-backup-20250101.tar.gz

# Restart
docker compose up -d
```

## Multi-Platform Support

Build for multiple architectures:

```bash
# Enable BuildKit
export DOCKER_BUILDKIT=1

# Build for multiple platforms
docker buildx build --platform linux/amd64,linux/arm64 -t derme-app .
```

## Docker Hub Deployment

Push to Docker Hub:

```bash
# Tag image
docker tag derme-app yourusername/derme-app:latest

# Push to Docker Hub
docker push yourusername/derme-app:latest

# Pull and run on any machine
docker pull yourusername/derme-app:latest
docker run -d -p 7860:7860 yourusername/derme-app:latest
```

## Support

For issues specific to Docker deployment:
1. Check logs: `docker compose logs -f`
2. Verify configuration: `docker compose config`
3. Test locally first before deploying to production
4. Review [Docker documentation](https://docs.docker.com/)

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Main Application README](README.md)
- [Configuration Guide](CONFIG_README.md)
- [Quick Start Guide](QUICKSTART.md)
