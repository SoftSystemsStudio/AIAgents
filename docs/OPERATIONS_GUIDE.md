# Gmail Cleanup Agent - Production Operations Guide

**Version**: 1.0  
**Date**: November 21, 2025  
**Status**: Production Ready (100%)

## Overview

This guide provides complete instructions for deploying, configuring, and operating the Gmail Cleanup Agent in production environments.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [OAuth Configuration](#oauth-configuration)
4. [Deployment](#deployment)
5. [Configuration](#configuration)
6. [Monitoring](#monitoring)
7. [Troubleshooting](#troubleshooting)
8. [Security](#security)
9. [Maintenance](#maintenance)

---

## Prerequisites

### System Requirements

- **Python**: 3.11 or higher
- **OS**: Linux, macOS, or Windows
- **Memory**: Minimum 512MB RAM
- **Storage**: 100MB for application + logs

### Required Accounts

- **Google Cloud Project** with Gmail API enabled
- **OAuth 2.0 Credentials** (Desktop app type)
- **Gmail Account** for testing and operations

### Dependencies

```bash
# Core dependencies
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
pip install pydantic structlog tenacity

# Optional: Database support
pip install sqlalchemy asyncpg alembic

# Optional: Observability
pip install prometheus-client opentelemetry-api
```

---

## Initial Setup

### 1. Clone Repository

```bash
git clone https://github.com/SoftSystemsStudio/AIAgents
cd AIAgents
```

### 2. Install Dependencies

```bash
# Using pip
pip install -e ".[gmail,database,observability]"

# Or using pyproject.toml
pip install -e .
```

### 3. Verify Installation

```bash
# Run tests
pytest tests/test_domain_gmail_cleanup.py -v

# Expected: 18/18 passing
```

---

## OAuth Configuration

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Note the **Project ID**

### Step 2: Enable Gmail API

1. Navigate to **APIs & Services** > **Library**
2. Search for "Gmail API"
3. Click **Enable**

### Step 3: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. Application type: **Desktop app**
4. Name: "Gmail Cleanup Agent"
5. Click **Create**

### Step 4: Download Credentials

1. Click the download button (⬇) next to your OAuth client
2. Save as `credentials.json` in project root
3. **IMPORTANT**: Never commit this file to git

```json
# credentials.json structure (DO NOT share actual values)
{
  "installed": {
    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "YOUR_CLIENT_SECRET",
    "redirect_uris": ["http://localhost"]
  }
}
```

### Step 5: First Authentication

```bash
# Run initial authentication
python -c "from src.infrastructure.gmail_client import GmailClient; client = GmailClient()"

# Follow the prompts:
# 1. Copy the URL
# 2. Open in browser
# 3. Sign in and grant permissions
# 4. Copy authorization code
# 5. Paste back in terminal

# Result: token.pickle created
```

### Step 6: Verify Authentication

```bash
# Test API access
pytest tests/test_gmail_api_integration.py::test_gmail_authentication -v

# Expected: PASSED
```

---

## Deployment

### Development Environment

```bash
# Set environment variables
export GMAIL_CREDENTIALS_PATH=credentials.json
export GMAIL_TOKEN_PATH=token.pickle
export LOG_LEVEL=DEBUG

# Run application
python -m src.examples.gmail_cleanup_agent
```

### Production Environment

#### Using Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install -e ".[gmail,database,observability]"

# Copy application
COPY src/ src/
COPY credentials.json .
COPY token.pickle .

# Run application
CMD ["python", "-m", "src.examples.gmail_cleanup_agent"]
```

```bash
# Build and run
docker build -t gmail-cleanup:latest .
docker run -v $(pwd)/data:/app/data gmail-cleanup:latest
```

#### Using Kubernetes

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gmail-cleanup
spec:
  replicas: 1
  selector:
    matchLabels:
      app: gmail-cleanup
  template:
    metadata:
      labels:
        app: gmail-cleanup
    spec:
      containers:
      - name: gmail-cleanup
        image: gmail-cleanup:latest
        env:
        - name: LOG_LEVEL
          value: "INFO"
        volumeMounts:
        - name: credentials
          mountPath: /app/credentials
          readOnly: true
      volumes:
      - name: credentials
        secret:
          secretName: gmail-credentials
```

---

## Configuration

### Environment Variables

```bash
# Gmail API
export GMAIL_CREDENTIALS_PATH=credentials.json
export GMAIL_TOKEN_PATH=token.pickle
export GMAIL_MAX_THREADS=100

# Rate Limiting
export RATE_LIMIT_REQUESTS_PER_MINUTE=250
export RATE_LIMIT_REQUESTS_PER_HOUR=10000
export RATE_LIMIT_REQUESTS_PER_DAY=100000

# Database (Optional)
export DATABASE_URL=postgresql://user:pass@localhost/gmail_cleanup
export DATABASE_POOL_SIZE=5

# Observability
export PROMETHEUS_PORT=9090
export LOG_LEVEL=INFO
export LOG_FORMAT=json

# Safety
export DRY_RUN_BY_DEFAULT=true
export REQUIRE_CONFIRMATION=true
```

### Configuration File

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Gmail API
    gmail_credentials_path: str = "credentials.json"
    gmail_token_path: str = "token.pickle"
    gmail_max_threads: int = 100
    
    # Rate Limiting
    rate_limit_requests_per_minute: int = 250
    rate_limit_requests_per_hour: int = 10000
    
    # Safety
    dry_run_by_default: bool = True
    require_confirmation: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

## Monitoring

### Health Checks

```python
# health_check.py
from src.infrastructure.gmail_client import GmailClient

def health_check():
    """Verify system health."""
    try:
        client = GmailClient()
        threads = client.list_threads(max_results=1)
        return {"status": "healthy", "threads_accessible": len(threads) > 0}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

### Prometheus Metrics

```python
# Exposed metrics
gmail_cleanup_runs_total{status="completed|failed|dry_run"}
gmail_cleanup_actions_total{type="archive|delete|mark_read"}
gmail_cleanup_duration_seconds{policy="policy_name"}
gmail_api_requests_total{endpoint="threads|messages"}
gmail_api_errors_total{error_type="quota|auth|network"}
```

### Logging

```python
# Configure structured logging
import structlog

logger = structlog.get_logger()

# Log levels
logger.debug("Thread fetched", thread_id="123", message_count=5)
logger.info("Cleanup completed", run_id="run_123", actions=42)
logger.warning("Rate limit approached", requests=240, limit=250)
logger.error("Action failed", message_id="msg_123", error="Quota exceeded")
```

### Alerting

```yaml
# Prometheus alert rules
groups:
- name: gmail_cleanup
  rules:
  - alert: HighErrorRate
    expr: rate(gmail_cleanup_actions_total{status="failed"}[5m]) > 0.1
    for: 5m
    annotations:
      summary: "High error rate in Gmail cleanup"
      
  - alert: QuotaApproaching
    expr: gmail_api_requests_total / 10000 > 0.8
    annotations:
      summary: "Gmail API quota approaching limit"
```

---

## Troubleshooting

### Common Issues

#### 1. Authentication Failed

**Symptom**: "Failed to authenticate with Gmail API"

**Solutions**:
```bash
# Delete old token and re-authenticate
rm token.pickle
python -c "from src.infrastructure.gmail_client import GmailClient; client = GmailClient()"

# Verify credentials.json is valid
cat credentials.json | jq .

# Check OAuth consent screen configuration in Google Cloud Console
```

#### 2. Quota Exceeded

**Symptom**: "Quota exceeded for quota metric 'Queries' and limit 'Queries per minute per user'"

**Solutions**:
```python
# Increase delay between requests
time.sleep(0.1)  # 100ms delay

# Use batch operations
client.batch_archive_messages(message_ids)

# Request quota increase in Google Cloud Console
```

#### 3. Token Expired

**Symptom**: "Token has been expired or revoked"

**Solutions**:
```bash
# Refresh token automatically
# (GmailClient handles this automatically)

# If automatic refresh fails, re-authenticate
rm token.pickle
python -c "from src.infrastructure.gmail_client import GmailClient; client = GmailClient()"
```

#### 4. Network Errors

**Symptom**: "Connection timeout" or "Network unreachable"

**Solutions**:
```python
# Retry logic is built-in with exponential backoff
# Configure retry settings:
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=30)
)
def robust_operation():
    # Your operation here
    pass
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export GMAIL_DEBUG=true

# Run with verbose output
pytest tests/test_gmail_api_integration.py -v -s

# Check logs
tail -f logs/gmail_cleanup.log
```

### Support Checklist

When reporting issues, provide:
- [ ] Error message and stack trace
- [ ] Python version: `python --version`
- [ ] Package versions: `pip list | grep google`
- [ ] Configuration (redact sensitive values)
- [ ] Recent logs (last 100 lines)
- [ ] Steps to reproduce

---

## Security

### Credential Management

```bash
# NEVER commit credentials to git
echo "credentials.json" >> .gitignore
echo "token.pickle" >> .gitignore

# Use environment variables or secrets management
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Rotate credentials periodically
# 1. Create new OAuth client in Google Cloud Console
# 2. Download new credentials.json
# 3. Re-authenticate with new credentials
# 4. Delete old OAuth client
```

### OAuth Scopes

```python
# Use minimal required scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',  # Read and modify
    # NOT using gmail.readonly - we need write access
    # NOT using gmail.send - we don't send emails
]
```

### Data Privacy

```python
# Minimize data storage
- Store only necessary metadata (IDs, subjects, dates)
- Don't store email content or bodies
- Encrypt sensitive data at rest
- Use secure connections (HTTPS/TLS)

# Compliance
- GDPR: Users can request data deletion
- Audit logs: Track all cleanup operations
- Retention: Configure data retention policies
```

### Access Control

```python
# Production deployment
- Use service accounts for automation
- Implement role-based access control (RBAC)
- Audit user permissions regularly
- Monitor for suspicious activity
```

---

## Maintenance

### Regular Tasks

#### Daily
- [ ] Check error rates in monitoring dashboard
- [ ] Review failed cleanup actions
- [ ] Verify API quota usage

#### Weekly
- [ ] Review cleanup run history
- [ ] Analyze action patterns
- [ ] Update policies based on usage

#### Monthly
- [ ] Rotate OAuth credentials
- [ ] Review and update policies
- [ ] Analyze performance metrics
- [ ] Update dependencies

### Backup and Recovery

```bash
# Backup cleanup run history
pg_dump -t cleanup_runs > backup_$(date +%Y%m%d).sql

# Backup policies
python -c "
from src.infrastructure.gmail_persistence import GmailCleanupRepository
repo = GmailCleanupRepository()
policies = repo.get_policies('user_id')
import json
with open('policies_backup.json', 'w') as f:
    json.dump([p.dict() for p in policies], f, indent=2)
"

# Restore from backup
psql < backup_20251121.sql
```

### Updates and Upgrades

```bash
# Update dependencies
pip install --upgrade google-auth-oauthlib google-api-python-client

# Run tests after upgrade
pytest tests/ -v

# Deploy with zero downtime
# 1. Deploy new version to staging
# 2. Run smoke tests
# 3. Gradually roll out to production
# 4. Monitor for errors
# 5. Rollback if issues detected
```

### Performance Optimization

```python
# Use batch operations
message_ids = [msg.id for msg in messages]
results = client.batch_archive_messages(message_ids)

# Cache frequently accessed data
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_thread_cached(thread_id):
    return client.get_thread(thread_id)

# Paginate large result sets
for threads_batch in paginate_threads(max_results=100):
    process_batch(threads_batch)
```

---

## Production Checklist

### Pre-Deployment

- [ ] All tests passing (42/42)
- [ ] OAuth credentials configured
- [ ] Environment variables set
- [ ] Database migrated (if using)
- [ ] Monitoring configured
- [ ] Alerting set up
- [ ] Documentation reviewed

### Deployment

- [ ] Deploy to staging first
- [ ] Run smoke tests in staging
- [ ] Verify OAuth still works
- [ ] Check API quota usage
- [ ] Monitor error rates
- [ ] Verify logs are working

### Post-Deployment

- [ ] Run health check
- [ ] Verify first cleanup run
- [ ] Check monitoring dashboard
- [ ] Confirm alerts are firing
- [ ] Document deployment notes
- [ ] Update runbook if needed

---

## Quick Reference

### Common Commands

```bash
# Run dry-run cleanup
python -m src.examples.gmail_cleanup_agent --dry-run

# Execute real cleanup
python -m src.examples.gmail_cleanup_agent --execute

# Analyze inbox
python -m src.examples.gmail_cleanup_agent --analyze

# View cleanup history
python -m src.examples.gmail_cleanup_agent --history

# Health check
curl http://localhost:8080/health
```

### API Rate Limits

| Resource | Quota | Per User |
|----------|-------|----------|
| Queries | 250 | per second |
| Queries | 1,000,000,000 | per day |
| Send | 2,000 | per day |

### Support Contacts

- **Documentation**: https://github.com/SoftSystemsStudio/AIAgents/docs
- **Issues**: https://github.com/SoftSystemsStudio/AIAgents/issues
- **Email**: support@example.com

---

## Appendix

### A. Gmail API Reference

- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [OAuth 2.0 Setup](https://developers.google.com/gmail/api/quickstart/python)
- [API Quotas](https://developers.google.com/gmail/api/reference/quota)

### B. Architecture Diagrams

```
User → GmailCleanupAgent → GmailClient → Gmail API
                         ↓
                    CleanupPolicy
                         ↓
                    Domain Models
                         ↓
                    Repository (PostgreSQL)
                         ↓
                    Observability (Prometheus)
```

### C. Sample Policies

```python
# Conservative policy (archive only)
conservative = CleanupPolicy(
    id="conservative",
    name="Conservative Cleanup",
    cleanup_rules=[
        archive_old_promotions(days=90),
    ],
)

# Moderate policy (archive + some deletion)
moderate = CleanupPolicy(
    id="moderate",
    name="Moderate Cleanup",
    cleanup_rules=[
        archive_old_promotions(days=30),
        archive_old_social(days=14),
        delete_very_old(days=365),
    ],
)

# Aggressive policy (clean everything)
aggressive = CleanupPolicy(
    id="aggressive",
    name="Aggressive Cleanup",
    cleanup_rules=[
        archive_old_promotions(days=7),
        archive_old_social(days=7),
        delete_very_old(days=180),
        mark_newsletters_read(days=3),
    ],
)
```

---

**Last Updated**: November 21, 2025  
**Version**: 1.0  
**Status**: Production Ready ✅
