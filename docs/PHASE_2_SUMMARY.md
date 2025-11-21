# Phase 2 Complete: API & CLI

## Overview

Phase 2 successfully delivers HTTP API endpoints and command-line interface for the Gmail cleanup service, making it accessible via REST API, CLI, and scheduled automation.

## What Was Built

### 1. REST API Router (`src/api/routers/gmail_cleanup.py`)

FastAPI router with 7 endpoints:

#### Core Endpoints

**POST `/gmail/cleanup/analyze`**
- Analyze inbox without making changes
- Returns mailbox stats, health score, recommendations
- Request: `{"user_id": "user123", "max_threads": 100}`

**POST `/gmail/cleanup/preview`**
- Preview cleanup actions (dry run)
- Shows exactly what would happen
- Returns action counts and affected emails

**POST `/gmail/cleanup/execute`**
- Execute cleanup with full audit trail
- Supports `dry_run` parameter
- Returns before/after snapshots, storage freed

**POST `/gmail/cleanup/quick`**
- Quick cleanup with sensible defaults
- Archives old promotional/social emails
- Customizable thresholds

#### Management Endpoints

**GET `/gmail/cleanup/health/{user_id}`**
- Calculate mailbox health score (0-100)
- Factors: unread ratio, old emails, promotional clutter

**POST `/gmail/cleanup/policy`**
- Create/update cleanup policy
- TODO: Persistence to database

**GET `/gmail/cleanup/runs/{user_id}/{run_id}`**
- Retrieve cleanup run details
- TODO: Database integration

### 2. Command-Line Interface (`scripts/run_gmail_cleanup.py`)

Full-featured CLI with multiple operation modes:

#### Usage Examples

```bash
# Analyze inbox
python scripts/run_gmail_cleanup.py --user-id=user123 --analyze-only

# Preview cleanup (dry run)
python scripts/run_gmail_cleanup.py --user-id=user123 --dry-run

# Execute quick cleanup
python scripts/run_gmail_cleanup.py --user-id=user123 --quick

# Custom thresholds
python scripts/run_gmail_cleanup.py --user-id=user123 \
  --archive-promotions --archive-social --old-days=14

# JSON output for scripting
python scripts/run_gmail_cleanup.py --user-id=user123 --analyze-only --json
```

#### CLI Features

- ✅ Beautiful banner and formatted output
- ✅ Progress indicators and emojis
- ✅ Verbose mode for debugging
- ✅ JSON output for automation
- ✅ Comprehensive error handling
- ✅ Help text with examples

### 3. Makefile Integration

Easy commands for developers:

```bash
make gmail-analyze   # Analyze inbox
make gmail-preview   # Preview cleanup
make gmail-cleanup   # Execute cleanup
```

### 4. Docker-Compose Scheduler

Automated daily cleanup at 2 AM:

```yaml
gmail-cleanup-scheduler:
  image: alpine:latest
  volumes:
    - ./scripts:/scripts
    - ./credentials.json:/credentials.json:ro
  command: |
    apk add python3 py3-pip &&
    pip3 install google-auth-oauthlib google-api-python-client pydantic &&
    echo '0 2 * * * python3 /scripts/run_gmail_cleanup.py --user-id=default --quick' | crontab - &&
    crond -f
```

## API Usage Examples

### cURL

```bash
# Analyze inbox
curl -X POST http://localhost:8000/gmail/cleanup/analyze \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "max_threads": 100}'

# Preview cleanup
curl -X POST http://localhost:8000/gmail/cleanup/preview \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123"}'

# Execute cleanup
curl -X POST http://localhost:8000/gmail/cleanup/execute \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "dry_run": false}'

# Quick cleanup
curl -X POST http://localhost:8000/gmail/cleanup/quick \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "auto_archive_promotions": true,
    "auto_archive_social": true,
    "old_threshold_days": 30
  }'

# Get health score
curl http://localhost:8000/gmail/cleanup/health/user123
```

### Python Client

```python
import requests

# Analyze inbox
response = requests.post(
    "http://localhost:8000/gmail/cleanup/analyze",
    json={"user_id": "user123", "max_threads": 100}
)
analysis = response.json()

print(f"Health Score: {analysis['health_score']}")
print(f"Recommendations: {analysis['recommendations']['total_actions']}")

# Execute cleanup
response = requests.post(
    "http://localhost:8000/gmail/cleanup/execute",
    json={"user_id": "user123"}
)
result = response.json()

print(f"Deleted: {result['outcomes']['emails_deleted']}")
print(f"Archived: {result['outcomes']['emails_archived']}")
```

### JavaScript/TypeScript

```typescript
// Analyze inbox
const response = await fetch('http://localhost:8000/gmail/cleanup/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 'user123',
    max_threads: 100
  })
});

const analysis = await response.json();
console.log(`Health Score: ${analysis.health_score}`);
```

## CLI Output Examples

### Analyze Mode

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║              📧  Gmail Cleanup CLI  📧                       ║
║                                                              ║
║          Automated Inbox Hygiene for Busy Professionals     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

🔐 Initializing Gmail client (credentials: credentials.json)...
📊 Analyzing inbox for user123...

📊 Inbox Analysis for user123
======================================================================

📬 Mailbox Overview:
   Total Threads: 1,234
   Total Messages: 2,456
   Size: 125.45 MB

🟢 Health Score: 78.5/100

💡 Recommendations:
   Threads Affected: 234
   Total Actions: 456

   Actions Breakdown:
      • archive: 234
      • mark_read: 122
      • delete: 100

✨ Completed at 2024-11-21 14:30:00
```

### Execute Mode

```
🚀 Executing cleanup for user123...

✅ Cleanup Complete
======================================================================

📈 Execution Summary:
   Run ID: run_user123_1700586600
   Status: completed
   Duration: 12.5s

🎯 Actions:
   Total: 456
   Successful: 450
   Failed: 6
   Skipped: 0

   By Type:
      • archive: 234
      • mark_read: 122
      • delete: 94

📦 Outcomes:
   Emails Deleted: 94
   Emails Archived: 234
   Emails Labeled: 122
   Storage Freed: 15.67 MB

✨ Completed at 2024-11-21 14:35:00
```

## Cron Integration

### Daily Cleanup at 2 AM

```bash
# Edit crontab
crontab -e

# Add this line
0 2 * * * /usr/bin/python3 /path/to/scripts/run_gmail_cleanup.py --user-id=user123 --quick >> /var/log/gmail-cleanup.log 2>&1
```

### Weekly Analysis on Sundays

```bash
0 0 * * 0 /usr/bin/python3 /path/to/scripts/run_gmail_cleanup.py --user-id=user123 --analyze-only --json > /var/log/gmail-analysis.json
```

### Multiple Users

```bash
# User 1: Daily at 2 AM
0 2 * * * /usr/bin/python3 /path/to/scripts/run_gmail_cleanup.py --user-id=user1 --quick

# User 2: Daily at 3 AM
0 3 * * * /usr/bin/python3 /path/to/scripts/run_gmail_cleanup.py --user-id=user2 --quick

# User 3: Daily at 4 AM
0 4 * * * /usr/bin/python3 /path/to/scripts/run_gmail_cleanup.py --user-id=user3 --quick
```

## Integration with REST API

### Start API Server

```bash
# Development mode
python -m uvicorn src.api.rest:app --reload

# Production mode
python -m uvicorn src.api.rest:app --host 0.0.0.0 --port 8000 --workers 4
```

### API Documentation

FastAPI provides automatic interactive docs:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Deployment Options

### Option 1: API + Scheduler in Docker

```bash
docker-compose up -d
```

Services:
- REST API on port 8000
- Scheduler runs daily at 2 AM
- Postgres for persistence (Phase 3)
- Prometheus for metrics

### Option 2: Standalone CLI on Cron

```bash
# Install dependencies
pip install -e ".[gmail]"

# Setup cron
crontab -e
# Add: 0 2 * * * /path/to/scripts/run_gmail_cleanup.py --user-id=default --quick
```

### Option 3: API Only (No Scheduler)

```bash
# Start API
uvicorn src.api.rest:app --host 0.0.0.0 --port 8000

# Trigger cleanup via API (e.g., from external scheduler)
curl -X POST http://localhost:8000/gmail/cleanup/execute \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123"}'
```

### Option 4: Serverless (AWS Lambda)

```python
# lambda_handler.py
import json
from src.infrastructure.gmail_client import GmailClient
from src.application.services.inbox_hygiene_service import InboxHygieneService

def lambda_handler(event, context):
    user_id = event['user_id']
    
    gmail = GmailClient()
    service = InboxHygieneService(gmail)
    
    result = service.quick_cleanup(user_id=user_id)
    
    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }
```

Deploy with EventBridge schedule (daily at 2 AM).

## What's Ready Now

✅ **Full API**: 7 endpoints for all operations  
✅ **Production CLI**: Argparse, formatted output, error handling  
✅ **Makefile Commands**: Easy development workflow  
✅ **Docker Scheduler**: Automated daily runs  
✅ **Integration Ready**: REST API for web/mobile clients  
✅ **Automation Ready**: Cron, Lambda, Kubernetes CronJobs  

## What's Next (Phase 3)

Still needed for full production readiness:

1. **Persistence**
   - Store cleanup policies in Postgres
   - Store cleanup run history for audit
   - Store mailbox snapshots for trends

2. **Observability**
   - Wire Prometheus metrics
   - Structured logging integration
   - Alert rules for failures

3. **Testing**
   - Domain model tests
   - Use case tests with mocks
   - API integration tests

4. **Documentation**
   - Client-facing docs (non-technical)
   - Operations runbook
   - API client libraries

5. **Rate Limiting**
   - Integrate existing `src/rate_limiting.py`
   - Protect against Gmail API limits

## Architecture Benefits

### Clean Separation

```
REST API ──┐
           ├──> InboxHygieneService ──> Use Cases ──> Domain ──> Infrastructure
CLI ───────┘
```

**Same business logic powers both API and CLI** - no duplication!

### Dependency Injection

API router uses FastAPI's DI:

```python
def get_gmail_client() -> GmailClient:
    return GmailClient(credentials_path='credentials.json')

@router.post("/analyze")
async def analyze_inbox(
    request: AnalyzeRequest,
    service: InboxHygieneService = Depends(get_inbox_service),
):
    return service.analyze_inbox(...)
```

CLI instantiates directly:

```python
gmail = GmailClient(credentials_path=args.credentials)
service = InboxHygieneService(gmail)
result = service.analyze_inbox(...)
```

### Type Safety

Pydantic models ensure:
- Request validation
- Response serialization  
- OpenAPI schema generation
- Client code generation

### Testability

Mock `InboxHygieneService` in API tests:

```python
def test_analyze_endpoint(client):
    # Mock service
    mock_service = Mock(spec=InboxHygieneService)
    mock_service.analyze_inbox.return_value = {...}
    
    app.dependency_overrides[get_inbox_service] = lambda: mock_service
    
    response = client.post("/gmail/cleanup/analyze", json={"user_id": "test"})
    assert response.status_code == 200
```

## Summary

Phase 2 delivers a complete API and CLI interface for the Gmail cleanup service:

- **273 lines**: REST API router  
- **351 lines**: CLI script  
- **Total**: ~624 new lines of production code  

Combined with Phase 1 (~1,693 lines), the production Gmail cleanup service now totals **~2,317 lines** of clean, maintainable, testable code.

**Ready for**: Web apps, mobile apps, scheduled automation, serverless deployment.

**Next up**: Phase 3 - Persistence, observability, testing, and documentation.
