"""
Gmail Cleanup Observability - Metrics and logging integration.

Integrates with existing observability infrastructure to track
cleanup operations, performance, and outcomes.
"""

from typing import Dict, Any, Optional
from datetime import datetime

from src.infrastructure.observability import ObservabilityProvider
from src.domain.metrics import CleanupRun, CleanupStatus


class GmailCleanupObservability:
    """
    Observability wrapper for Gmail cleanup operations.
    
    Integrates with existing observability provider to emit
    metrics and structured logs.
    """
    
    def __init__(self, observability: ObservabilityProvider):
        """
        Initialize observability wrapper.
        
        Args:
            observability: Existing observability provider
        """
        self.observability = observability
    
    def log_cleanup_started(
        self,
        user_id: str,
        policy_id: str,
        policy_name: str,
        dry_run: bool = False,
    ) -> None:
        """Log cleanup operation start."""
        self.observability.log(
            "info",
            "gmail_cleanup_started",
            {
                "user_id": user_id,
                "policy_id": policy_id,
                "policy_name": policy_name,
                "dry_run": dry_run,
            }
        )
        
        self.observability.record_metric(
            "gmail_cleanup_starts_total",
            1.0,
            {
                "user_id": user_id,
                "policy_id": policy_id,
                "dry_run": str(dry_run).lower(),
            }
        )
    
    def log_cleanup_completed(self, run: CleanupRun) -> None:
        """Log cleanup operation completion."""
        summary = run.get_summary()
        
        self.observability.log(
            "info",
            "gmail_cleanup_completed",
            {
                "run_id": run.id,
                "user_id": run.user_id,
                "policy_id": run.policy_id,
                "status": run.status.value,
                "duration_seconds": run.duration_seconds,
                "actions_total": len(run.actions),
                "actions_successful": run.actions_successful,
                "actions_failed": run.actions_failed,
                "emails_deleted": run.emails_deleted,
                "emails_archived": run.emails_archived,
            }
        )
        
        # Record metrics
        self.observability.record_metric(
            "gmail_cleanup_runs_total",
            1.0,
            {
                "user_id": run.user_id,
                "policy_id": run.policy_id,
                "status": run.status.value,
            }
        )
        
        if run.duration_seconds:
            self.observability.record_metric(
                "gmail_cleanup_duration_seconds",
                run.duration_seconds,
                {
                    "user_id": run.user_id,
                    "policy_id": run.policy_id,
                }
            )
        
        self.observability.record_metric(
            "gmail_emails_processed_total",
            float(len(run.actions)),
            {
                "user_id": run.user_id,
                "policy_id": run.policy_id,
            }
        )
        
        self.observability.record_metric(
            "gmail_emails_deleted_total",
            float(run.emails_deleted),
            {
                "user_id": run.user_id,
                "policy_id": run.policy_id,
            }
        )
        
        self.observability.record_metric(
            "gmail_emails_archived_total",
            float(run.emails_archived),
            {
                "user_id": run.user_id,
                "policy_id": run.policy_id,
            }
        )
        
        if run.storage_freed_mb:
            self.observability.record_metric(
                "gmail_storage_freed_bytes",
                run.storage_freed_mb * 1024 * 1024,
                {
                    "user_id": run.user_id,
                    "policy_id": run.policy_id,
                }
            )
    
    def log_cleanup_failed(
        self,
        user_id: str,
        policy_id: str,
        error: str,
        duration_seconds: Optional[float] = None,
    ) -> None:
        """Log cleanup operation failure."""
        self.observability.log(
            "error",
            "gmail_cleanup_failed",
            {
                "user_id": user_id,
                "policy_id": policy_id,
                "error": error,
                "duration_seconds": duration_seconds,
            }
        )
        
        self.observability.record_metric(
            "gmail_cleanup_errors_total",
            1.0,
            {
                "user_id": user_id,
                "policy_id": policy_id,
            }
        )
    
    def log_action_executed(
        self,
        user_id: str,
        action_type: str,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """Log individual action execution."""
        level = "info" if success else "warning"
        
        self.observability.log(
            level,
            "gmail_action_executed",
            {
                "user_id": user_id,
                "action_type": action_type,
                "success": success,
                "error": error,
            }
        )
        
        self.observability.record_metric(
            "gmail_actions_total",
            1.0,
            {
                "user_id": user_id,
                "action_type": action_type,
                "success": str(success).lower(),
            }
        )
    
    def log_analysis_completed(
        self,
        user_id: str,
        total_threads: int,
        total_actions: int,
        health_score: float,
    ) -> None:
        """Log inbox analysis completion."""
        self.observability.log(
            "info",
            "gmail_analysis_completed",
            {
                "user_id": user_id,
                "total_threads": total_threads,
                "total_actions": total_actions,
                "health_score": health_score,
            }
        )
        
        self.observability.record_metric(
            "gmail_mailbox_health_score",
            health_score,
            {"user_id": user_id}
        )
        
        self.observability.record_metric(
            "gmail_mailbox_threads",
            float(total_threads),
            {"user_id": user_id}
        )
    
    def log_gmail_api_call(
        self,
        method: str,
        duration_seconds: float,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """Log Gmail API call."""
        level = "debug" if success else "warning"
        
        self.observability.log(
            level,
            "gmail_api_call",
            {
                "method": method,
                "duration_seconds": duration_seconds,
                "success": success,
                "error": error,
            }
        )
        
        self.observability.record_metric(
            "gmail_api_calls_total",
            1.0,
            {
                "method": method,
                "success": str(success).lower(),
            }
        )
        
        self.observability.record_metric(
            "gmail_api_duration_seconds",
            duration_seconds,
            {"method": method}
        )
    
    def log_rate_limit_hit(self, method: str) -> None:
        """Log when Gmail API rate limit is hit."""
        self.observability.log(
            "warning",
            "gmail_rate_limit_hit",
            {"method": method}
        )
        
        self.observability.record_metric(
            "gmail_rate_limit_hits_total",
            1.0,
            {"method": method}
        )


# Prometheus metric descriptions for documentation
GMAIL_CLEANUP_METRICS = {
    "gmail_cleanup_starts_total": {
        "type": "counter",
        "description": "Total number of cleanup operations started",
        "labels": ["user_id", "policy_id", "dry_run"],
    },
    "gmail_cleanup_runs_total": {
        "type": "counter",
        "description": "Total number of cleanup operations completed",
        "labels": ["user_id", "policy_id", "status"],
    },
    "gmail_cleanup_errors_total": {
        "type": "counter",
        "description": "Total number of cleanup operation failures",
        "labels": ["user_id", "policy_id"],
    },
    "gmail_cleanup_duration_seconds": {
        "type": "histogram",
        "description": "Cleanup operation duration in seconds",
        "labels": ["user_id", "policy_id"],
        "buckets": [1, 5, 10, 30, 60, 120, 300],
    },
    "gmail_emails_processed_total": {
        "type": "counter",
        "description": "Total number of emails processed",
        "labels": ["user_id", "policy_id"],
    },
    "gmail_emails_deleted_total": {
        "type": "counter",
        "description": "Total number of emails deleted",
        "labels": ["user_id", "policy_id"],
    },
    "gmail_emails_archived_total": {
        "type": "counter",
        "description": "Total number of emails archived",
        "labels": ["user_id", "policy_id"],
    },
    "gmail_storage_freed_bytes": {
        "type": "counter",
        "description": "Total storage freed in bytes",
        "labels": ["user_id", "policy_id"],
    },
    "gmail_actions_total": {
        "type": "counter",
        "description": "Total number of actions executed",
        "labels": ["user_id", "action_type", "success"],
    },
    "gmail_mailbox_health_score": {
        "type": "gauge",
        "description": "Mailbox health score (0-100)",
        "labels": ["user_id"],
    },
    "gmail_mailbox_threads": {
        "type": "gauge",
        "description": "Total threads in mailbox",
        "labels": ["user_id"],
    },
    "gmail_api_calls_total": {
        "type": "counter",
        "description": "Total Gmail API calls",
        "labels": ["method", "success"],
    },
    "gmail_api_duration_seconds": {
        "type": "histogram",
        "description": "Gmail API call duration",
        "labels": ["method"],
        "buckets": [0.1, 0.5, 1, 2, 5, 10],
    },
    "gmail_rate_limit_hits_total": {
        "type": "counter",
        "description": "Total rate limit hits",
        "labels": ["method"],
    },
}


# Alert rules for Prometheus (example configuration)
GMAIL_CLEANUP_ALERTS = """
groups:
  - name: gmail_cleanup
    interval: 1m
    rules:
      # High failure rate
      - alert: GmailCleanupHighFailureRate
        expr: |
          rate(gmail_cleanup_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High Gmail cleanup failure rate"
          description: "Gmail cleanup is failing at {{ $value }} errors/sec for user {{ $labels.user_id }}"
      
      # Slow cleanup operations
      - alert: GmailCleanupSlow
        expr: |
          histogram_quantile(0.95, rate(gmail_cleanup_duration_seconds_bucket[5m])) > 120
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Gmail cleanup operations are slow"
          description: "95th percentile cleanup duration is {{ $value }}s"
      
      # Rate limit issues
      - alert: GmailRateLimitHit
        expr: |
          rate(gmail_rate_limit_hits_total[5m]) > 0.01
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Gmail API rate limit being hit"
          description: "Rate limit hits detected for {{ $labels.method }}"
      
      # Low mailbox health
      - alert: GmailLowMailboxHealth
        expr: |
          gmail_mailbox_health_score < 50
        for: 1h
        labels:
          severity: info
        annotations:
          summary: "Low mailbox health score"
          description: "Mailbox health for {{ $labels.user_id }} is {{ $value }}/100"
"""


# Grafana dashboard configuration (example JSON)
GRAFANA_DASHBOARD_CONFIG = """
{
  "dashboard": {
    "title": "Gmail Cleanup Monitoring",
    "panels": [
      {
        "title": "Cleanup Operations",
        "targets": [
          {"expr": "rate(gmail_cleanup_runs_total[5m])"}
        ]
      },
      {
        "title": "Success Rate",
        "targets": [
          {"expr": "rate(gmail_cleanup_runs_total{status='completed'}[5m]) / rate(gmail_cleanup_runs_total[5m])"}
        ]
      },
      {
        "title": "Emails Processed",
        "targets": [
          {"expr": "rate(gmail_emails_processed_total[5m])"},
          {"expr": "rate(gmail_emails_deleted_total[5m])"},
          {"expr": "rate(gmail_emails_archived_total[5m])"}
        ]
      },
      {
        "title": "Cleanup Duration (p95)",
        "targets": [
          {"expr": "histogram_quantile(0.95, rate(gmail_cleanup_duration_seconds_bucket[5m]))"}
        ]
      },
      {
        "title": "Storage Freed",
        "targets": [
          {"expr": "rate(gmail_storage_freed_bytes[5m]) / 1024 / 1024"}
        ]
      },
      {
        "title": "Mailbox Health Score",
        "targets": [
          {"expr": "gmail_mailbox_health_score"}
        ]
      }
    ]
  }
}
"""
