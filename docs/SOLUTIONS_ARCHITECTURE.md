# Solutions Architecture

## Overview

The AIAgents platform uses a **layered architecture** where business solutions (like Gmail cleanup) are built on top of a generic agent framework. This document describes the architecture pattern for creating new solution modules.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│  • CLI Entrypoints (run_gmail_agent.sh)                    │
│  • API Routes (future: src/api/gmail_cleanup.py)           │
│  • Examples (examples/gmail_cleanup_agent.py)              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                          │
│  • Use Cases (src/application/gmail_cleanup_use_cases.py)  │
│    - AnalyzeInboxUseCase                                    │
│    - DryRunCleanupUseCase                                   │
│    - ExecuteCleanupUseCase                                  │
│  • Orchestration Logic                                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     Domain Layer                             │
│  • Entities (src/domain/email_thread.py)                   │
│    - EmailMessage, EmailThread, MailboxSnapshot            │
│  • Value Objects (src/domain/cleanup_policy.py)            │
│    - CleanupPolicy, CleanupRule, CleanupAction             │
│  • Domain Services                                          │
│  • Interfaces (src/domain/gmail_interfaces.py)             │
│    - IGmailClient, IGmailCleanupRepository                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                        │
│  • API Adapters (src/infrastructure/gmail_client.py)       │
│  • Persistence (src/infrastructure/gmail_persistence.py)   │
│  • Observability (src/infrastructure/gmail_observability.py)│
│  • Rate Limiting, Batch Operations                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   External Services                          │
│  • Gmail API                                                 │
│  • PostgreSQL                                                │
│  • Prometheus/Grafana                                        │
└─────────────────────────────────────────────────────────────┘
```

## Solution Pattern: Gmail Cleanup

The Gmail cleanup solution demonstrates the complete pattern for building agency services:

### 1. Domain Layer (`src/domain/`)

**Purpose**: Core business logic, independent of external systems

**Files**:
- `email_thread.py` - Domain entities (EmailMessage, EmailThread, MailboxSnapshot)
- `cleanup_policy.py` - Business rules (CleanupPolicy, CleanupRule, CleanupAction)
- `cleanup_rule_builder.py` - Fluent API for creating policies
- `gmail_interfaces.py` - Abstract contracts (IGmailClient, IGmailObservability)
- `metrics.py` - Domain metrics (CleanupRun, MailboxStats)

**Key Principles**:
- No external dependencies (except standard library)
- Pure business logic
- Rich domain models with behavior
- Safety guardrails at domain level

**Example**:
```python
from src.domain.cleanup_policy import CleanupPolicy
from src.domain.cleanup_rule_builder import CleanupRuleBuilder

# Domain logic with fluent builder
policy = (
    CleanupRuleBuilder()
    .archive_if_category("promotions")
    .archive_if_older_than_days(30)
    .never_touch_starred()
    .build()
)
```

### 2. Application Layer (`src/application/`)

**Purpose**: Use case orchestration, workflow coordination

**Files**:
- `gmail_cleanup_use_cases.py` - Use case implementations:
  - `AnalyzeInboxUseCase` - Inbox analysis without modifications
  - `DryRunCleanupUseCase` - Preview cleanup actions
  - `ExecuteCleanupUseCase` - Execute cleanup with rate limiting

**Key Principles**:
- Orchestrates domain entities and infrastructure services
- Transaction boundaries
- Error handling and retry logic
- Emits observability signals

**Example**:
```python
from src.application.gmail_cleanup_use_cases import ExecuteCleanupUseCase

# Use case coordinates domain + infrastructure
use_case = ExecuteCleanupUseCase(
    gmail_client=gmail_client,
    repository=repository,
    observability=observability,
    rate_limiter=rate_limiter,
)

result = use_case.execute(
    user_id="user@example.com",
    policy=policy,
    dry_run=False,
)
```

### 3. Infrastructure Layer (`src/infrastructure/`)

**Purpose**: External system adapters, implements domain interfaces

**Files**:
- `gmail_client.py` - Gmail API adapter (implements IGmailClient)
- `gmail_persistence.py` - PostgreSQL repository
- `gmail_observability.py` - Metrics and logging (implements IGmailObservability)

**Key Principles**:
- Implements domain interfaces
- Handles external API specifics
- Rate limiting and batching
- Emits Prometheus metrics

**Example**:
```python
from src.infrastructure.gmail_client import GmailClient
from src.domain.gmail_interfaces import IGmailClient

# Infrastructure implements domain interface
class GmailClient(IGmailClient):
    def list_threads(self, query: str, ...) -> List[EmailThread]:
        # Gmail API specifics
        ...
```

### 4. Presentation Layer

**Purpose**: User-facing interfaces (CLI, API, examples)

**Files**:
- `run_gmail_agent.sh` - CLI entrypoint (calls use cases)
- `examples/gmail_cleanup_agent.py` - Reference implementation
- Future: `src/api/gmail_cleanup.py` - HTTP API routes

**Key Principles**:
- Thin layer, no business logic
- Instantiates use cases with dependencies
- Handles user input/output formatting

**Example**:
```python
# examples/gmail_cleanup_agent.py - Reference implementation only
from src.application.gmail_cleanup_use_cases import ExecuteCleanupUseCase
from src.infrastructure.gmail_client import GmailClient

# Wire up dependencies and demonstrate usage
client = GmailClient()
use_case = ExecuteCleanupUseCase(gmail_client=client)

# Show how to use, don't define business logic
result = use_case.execute(user_id="demo", policy=demo_policy)
print(result)
```

## Observability & Metrics

### Solution-Specific Metrics

Each solution defines its own metrics namespace:

**Gmail Cleanup Metrics**:
```python
# Counter metrics
gmail_cleanup_runs_total{user_id, policy_id, status}
gmail_cleanup_errors_total{user_id, error_type}
gmail_emails_processed_total{user_id, action_type}
gmail_emails_deleted_total{user_id, policy_id}
gmail_emails_archived_total{user_id, policy_id}

# Histogram metrics
gmail_cleanup_duration_seconds{user_id, policy_id}
gmail_api_duration_seconds{method}

# Gauge metrics
gmail_mailbox_health_score{user_id}
gmail_mailbox_threads{user_id}
```

### Business Value Metrics

Metrics directly map to client value propositions:

- **Time Saved**: `gmail_emails_processed_total * 0.5s` (avg time per email)
- **Storage Freed**: `gmail_storage_freed_bytes` 
- **Inbox Health**: `gmail_mailbox_health_score` (0-100)
- **Reliability**: `gmail_cleanup_runs_total{status="completed"}` / `gmail_cleanup_runs_total`

## Creating a New Solution

To add a new solution (e.g., "Meeting Notes Agent"):

### 1. Domain Layer

```
src/domain/meeting_models.py
src/domain/meeting_policy.py
src/domain/meeting_interfaces.py
```

Define:
- Entities: Meeting, Transcript, ActionItem
- Value Objects: MeetingSummary, SummaryPolicy
- Interfaces: IMeetingProvider, ITranscriptionService

### 2. Application Layer

```
src/application/meeting_notes_use_cases.py
```

Implement:
- `TranscribeMeetingUseCase`
- `GenerateSummaryUseCase`
- `ExtractActionItemsUseCase`

### 3. Infrastructure Layer

```
src/infrastructure/zoom_client.py
src/infrastructure/meeting_persistence.py
src/infrastructure/meeting_observability.py
```

Implement interfaces:
- `ZoomClient(IMeetingProvider)`
- `MeetingRepository`
- `MeetingObservability`

### 4. Presentation Layer

```
run_meeting_notes.sh
examples/meeting_notes_demo.py
```

Wire dependencies and demonstrate usage.

### 5. Observability

Define solution-specific metrics:
```python
meeting_transcriptions_total{user_id, provider}
meeting_summary_duration_seconds{user_id}
meeting_action_items_extracted{user_id}
```

## Benefits of This Architecture

### 1. **Separation of Concerns**
- Domain logic isolated from infrastructure
- Easy to test (mock interfaces)
- Clear dependency direction (always inward)

### 2. **Scalability**
- Multiple solutions share platform core
- Each solution is independent
- Solutions can evolve separately

### 3. **Testability**
- Domain layer: Pure unit tests
- Application layer: Mock infrastructure
- Infrastructure layer: Integration tests
- Presentation layer: E2E tests

### 4. **Maintainability**
- Clear file organization
- Consistent patterns across solutions
- Easy onboarding for new developers

### 5. **Observability**
- Solution-specific metrics
- Unified observability platform
- Business value tracking
- Client-facing SLAs

## File Organization

```
src/
├── domain/                          # Business logic
│   ├── models.py                   # Core platform entities
│   ├── interfaces.py               # Platform interfaces
│   │
│   ├── email_thread.py             # Gmail: Domain entities
│   ├── cleanup_policy.py           # Gmail: Business rules
│   ├── cleanup_rule_builder.py     # Gmail: Fluent API
│   ├── gmail_interfaces.py         # Gmail: Solution interfaces
│   └── metrics.py                  # Gmail: Domain metrics
│
├── application/                     # Use cases
│   ├── orchestrator.py             # Platform orchestrator
│   ├── gmail_cleanup_use_cases.py  # Gmail: Use cases
│   └── use_cases/                  # Legacy location
│
├── infrastructure/                  # External adapters
│   ├── llm_providers.py            # Platform: LLM adapters
│   ├── observability.py            # Platform: Base observability
│   │
│   ├── gmail_client.py             # Gmail: API adapter
│   ├── gmail_persistence.py        # Gmail: Database
│   └── gmail_observability.py      # Gmail: Metrics
│
└── api/                             # HTTP routes (future)
    └── gmail_cleanup.py            # Gmail: REST endpoints

examples/                            # Reference implementations
├── gmail_cleanup_agent.py          # How to use Gmail solution
├── simple_agent.py                 # Platform examples
└── ...

scripts/                             # CLI entrypoints
run_gmail_agent.sh                  # Gmail solution CLI
```

## Testing Strategy

### Domain Tests (18 tests)
```bash
pytest tests/test_domain_gmail_cleanup.py
```
- Pure unit tests
- No external dependencies
- Fast (<1 second)
- 69-98% coverage

### Smoke Tests (10 tests)
```bash
pytest tests/test_smoke_gmail_cleanup.py
```
- Production scenarios
- Mocked infrastructure
- Fast (3 seconds)

### Workflow Tests (4 tests)
```bash
pytest tests/test_e2e_gmail_workflow.py
```
- End-to-end workflows
- Builder pattern demos
- Fast (<3 seconds)

### Integration Tests (10 tests)
```bash
pytest tests/test_gmail_api_integration.py
```
- Real Gmail API
- Requires credentials
- Slower (25 seconds)
- Validates real-world behavior

## Dependencies

### Domain Layer
- **Zero external dependencies** (only Python stdlib)
- Ensures portability and testability

### Application Layer
- Domain layer
- `tenacity` (retry logic)
- Platform infrastructure interfaces

### Infrastructure Layer
- `google-auth-oauthlib` (Gmail OAuth)
- `google-api-python-client` (Gmail API)
- `sqlalchemy` (persistence)
- `prometheus_client` (metrics)

## Migration Guide

### From Examples to Solutions

**Before** (Gmail as example):
```python
# examples/gmail_cleanup_agent.py
# Contains business logic, API calls, etc.
```

**After** (Gmail as solution):
```python
# src/domain/gmail_interfaces.py - Contracts
# src/application/gmail_cleanup_use_cases.py - Orchestration
# src/infrastructure/gmail_client.py - API adapter
# examples/gmail_cleanup_agent.py - Demo only
```

### Updating Imports

**Old**:
```python
from src.application.use_cases.gmail_cleanup import ExecuteCleanupUseCase
```

**New**:
```python
from src.application.gmail_cleanup_use_cases import ExecuteCleanupUseCase
```

## Future Solutions

Planned solutions following this pattern:

1. **RAG Analyst Agent**
   - Domain: `src/domain/rag_models.py`
   - Use Cases: `src/application/rag_analysis_use_cases.py`
   - Infrastructure: `src/infrastructure/vector_store_client.py`

2. **Meeting Notes Agent**
   - Domain: `src/domain/meeting_models.py`
   - Use Cases: `src/application/meeting_notes_use_cases.py`
   - Infrastructure: `src/infrastructure/zoom_client.py`

3. **Document Processing Agent**
   - Domain: `src/domain/document_models.py`
   - Use Cases: `src/application/document_processing_use_cases.py`
   - Infrastructure: `src/infrastructure/pdf_processor.py`

## References

- **Domain-Driven Design**: Eric Evans
- **Clean Architecture**: Robert C. Martin
- **Hexagonal Architecture**: Alistair Cockburn
- **SOLID Principles**: Dependency Inversion, Interface Segregation

## Summary

The solutions architecture provides:

✅ **Clear separation** of platform vs. solutions  
✅ **Reusable patterns** for new revenue streams  
✅ **Testable design** with interface-based dependency injection  
✅ **Observable systems** with solution-specific metrics  
✅ **Scalable structure** that grows with the business  

Gmail cleanup demonstrates the complete pattern at 100% production readiness.
