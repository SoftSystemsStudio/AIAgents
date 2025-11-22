"""
Gmail Cleanup Use Cases - Application layer business workflows.

Implements the core business logic for inbox cleanup operations,
orchestrating domain entities and infrastructure services.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import asdict
import uuid
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.domain.email_thread import MailboxSnapshot, EmailThread, EmailMessage
from src.domain.cleanup_policy import CleanupPolicy, CleanupAction
from src.domain.metrics import (
    CleanupRun,
    CleanupStatus,
    CleanupAction as CleanupActionRecord,
    ActionStatus,
    MailboxStats,
)
from src.infrastructure.gmail_client import GmailClient
from src.infrastructure.gmail_persistence import GmailCleanupRepository
from src.infrastructure.gmail_observability import GmailCleanupObservability
from src.rate_limiting import RateLimiter, RateLimitConfig, RateLimitError


class AnalyzeInboxUseCase:
    """
    Analyze user's inbox and generate recommendations.
    
    Creates a mailbox snapshot and applies cleanup policy to
    identify potential actions without executing them.
    """
    
    def __init__(
        self,
        gmail_client: GmailClient,
        observability: Optional[GmailCleanupObservability] = None,
    ):
        self.gmail = gmail_client
        self.observability = observability
    
    def execute(
        self,
        user_id: str,
        policy: CleanupPolicy,
        max_threads: int = 100,
        customer_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze inbox and return recommendations.
        
        Args:
            user_id: User identifier (Gmail user)
            policy: Cleanup policy to apply
            max_threads: Maximum threads to analyze
            customer_id: SaaS customer ID (for multi-tenancy)
            
        Returns:
            Analysis with recommendations
        """
        # Fetch threads from Gmail
        threads = self.gmail.list_threads(query='', max_results=max_threads)
        
        # Create mailbox snapshot
        snapshot = MailboxSnapshot.from_threads(user_id, threads)
        
        # Generate mailbox stats
        stats = MailboxStats.from_snapshot(snapshot)
        
        # Analyze each thread for potential actions
        recommendations = []
        total_actions = 0
        actions_by_type = {}
        
        for thread in threads:
            analysis = policy.analyze_thread(thread)
            if analysis['total_actions'] > 0:
                recommendations.append(analysis)
                total_actions += analysis['total_actions']
                
                # Count actions by type
                for msg in analysis['messages']:
                    for action_type, _ in msg['actions']:
                        actions_by_type[action_type] = actions_by_type.get(action_type, 0) + 1
        
        # Log analysis completion
        if self.observability:
            self.observability.log_analysis_completed(
                user_id=user_id,
                total_threads=len(threads),
                total_actions=total_actions,
                health_score=stats.get_health_score(),
                customer_id=customer_id,
            )
        
        return {
            "user_id": user_id,
            "customer_id": customer_id,
            "analyzed_at": datetime.utcnow().isoformat(),
            "snapshot": {
                "total_threads": len(threads),
                "total_messages": snapshot.message_count,
                "size_mb": snapshot.size_mb,
                "stats": stats.get_health_score(),
            },
            "policy": {
                "id": policy.id,
                "name": policy.name,
            },
            "recommendations": {
                "total_threads_affected": len(recommendations),
                "total_actions": total_actions,
                "actions_by_type": actions_by_type,
                "threads": recommendations[:10],  # Limit for display
            },
            "health_score": stats.get_health_score(),
        }


class DryRunCleanupUseCase:
    """
    Preview cleanup actions without executing them.
    
    Creates a detailed plan showing exactly what would happen
    if the cleanup were executed.
    """
    
    def __init__(
        self,
        gmail_client: GmailClient,
        observability: Optional[GmailCleanupObservability] = None,
    ):
        self.gmail = gmail_client
        self.observability = observability
    
    def execute(
        self,
        user_id: str,
        policy: CleanupPolicy,
        max_threads: int = 100,
        customer_id: Optional[str] = None,
    ) -> CleanupRun:
        """
        Generate dry run cleanup plan.
        
        Args:
            user_id: User identifier (Gmail user)
            policy: Cleanup policy to apply
            max_threads: Maximum threads to process
            customer_id: SaaS customer ID (for multi-tenancy)
            
        Returns:
            CleanupRun with status DRY_RUN
        """
        # Fetch threads and create snapshot
        threads = self.gmail.list_threads(query='', max_results=max_threads)
        before_snapshot = MailboxSnapshot.from_threads(user_id, threads)
        
        # Create cleanup run
        run = CleanupRun(
            id=f"dry_run_{user_id}_{int(datetime.utcnow().timestamp())}",
            user_id=user_id,
            policy_id=policy.id,
            policy_name=policy.name,
            status=CleanupStatus.DRY_RUN,
            before_snapshot=before_snapshot,
        )
        
        # Generate actions for each thread
        for thread in threads:
            for message in thread.messages:
                actions = policy.get_actions_for_message(message)
                for action_type, params in actions:
                    run.actions.append(CleanupActionRecord(
                        message_id=message.id,
                        action_type=action_type.value,
                        action_params=params,
                        status=ActionStatus.PENDING,
                        message_subject=message.subject,
                        message_from=str(message.from_address),
                        message_date=message.date,
                    ))
        
        return run


class ExecuteCleanupUseCase:
    """
    Execute cleanup actions and track results.
    
    Applies cleanup policy, executes actions, captures metrics,
    and creates audit trail.
    """
    
    def __init__(
        self,
        gmail_client: GmailClient,
        repository: Optional[GmailCleanupRepository] = None,
        observability: Optional[GmailCleanupObservability] = None,
        rate_limiter: Optional[RateLimiter] = None,
    ):
        self.gmail = gmail_client
        self.repository = repository
        self.observability = observability
        self.rate_limiter = rate_limiter or RateLimiter(RateLimitConfig(
            max_requests_per_minute=250,  # Gmail API quota
            max_requests_per_hour=10000,
            max_requests_per_day=100000,
        ))
    
    def execute(
        self,
        user_id: str,
        policy: CleanupPolicy,
        max_threads: int = 100,
        dry_run: bool = False,
        customer_id: Optional[str] = None,
    ) -> CleanupRun:
        """
        Execute cleanup run.
        
        Args:
            user_id: User identifier (Gmail user)
            policy: Cleanup policy to apply
            max_threads: Maximum threads to process
            dry_run: If True, don't actually execute actions
            customer_id: SaaS customer ID (for multi-tenancy)
            
        Returns:
            CleanupRun with complete results
        """
        # Fetch threads and create before snapshot
        threads = self.gmail.list_threads(query='', max_results=max_threads)
        before_snapshot = MailboxSnapshot.from_threads(user_id, threads)
        
        # Create cleanup run
        run = CleanupRun(
            id=f"run_{user_id}_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:6]}",
            user_id=user_id,
            policy_id=policy.id,
            policy_name=policy.name,
            status=CleanupStatus.DRY_RUN if dry_run else CleanupStatus.IN_PROGRESS,
            before_snapshot=before_snapshot,
            started_at=datetime.now(),
        )
        
        # Log cleanup start
        if self.observability:
            self.observability.log_cleanup_started(
                user_id=user_id,
                policy_id=policy.id,
                policy_name=policy.name,
                dry_run=dry_run,
                customer_id=customer_id,
            )
        
        try:
            # Process each thread
            for thread in threads:
                for message in thread.messages:
                    actions = policy.get_actions_for_message(message)
                    
                    for action_type, params in actions:
                        action_record = CleanupActionRecord(
                            message_id=message.id,
                            action_type=action_type.value,
                            action_params=params,
                            message_subject=message.subject,
                            message_from=str(message.from_address),
                            message_date=message.date,
                        )
                        
                        # Execute action if not dry run
                        if not dry_run:
                            try:
                                self._execute_action_with_retry(message.id, action_type, params, user_id)
                                action_record.status = ActionStatus.SUCCESS
                                action_record.executed_at = datetime.utcnow()
                                
                                # Log action
                                if self.observability:
                                    self.observability.log_action_executed(
                                        user_id=user_id,
                                        action_type=action_type.value,
                                        success=True,
                                    )
                            except Exception as e:
                                action_record.status = ActionStatus.FAILED
                                action_record.error_message = str(e)
                                
                                # Log action failure
                                if self.observability:
                                    self.observability.log_action_executed(
                                        user_id=user_id,
                                        action_type=action_type.value,
                                        success=False,
                                        error=str(e),
                                    )
                        else:
                            action_record.status = ActionStatus.SKIPPED
                        
                        run.actions.append(action_record)
            
            # Capture after snapshot if not dry run
            if not dry_run:
                threads_after = self.gmail.list_threads(query='', max_results=max_threads)
                run.after_snapshot = MailboxSnapshot.from_threads(user_id, threads_after)
            
            # Keep DRY_RUN status, otherwise mark as COMPLETED
            if not dry_run:
                run.status = CleanupStatus.COMPLETED
            
        except Exception as e:
            run.status = CleanupStatus.FAILED
            run.error_message = str(e)
            
            # Log failure
            if self.observability:
                duration = (datetime.utcnow() - run.started_at).total_seconds()
                self.observability.log_cleanup_failed(
                    user_id=user_id,
                    policy_id=policy.id,
                    error=str(e),
                    duration_seconds=duration,
                )
        finally:
            run.completed_at = datetime.utcnow()
            
            # Log completion
            if self.observability:
                self.observability.log_cleanup_completed(run)
            
            # Note: Repository save is async, must be called externally
            # if self.repository:
            #     await self.repository.save_run(run)
        
        return run
    
    def _execute_action_with_retry(
        self,
        message_id: str,
        action: CleanupAction,
        params: dict,
        user_id: str,
    ) -> None:
        """Execute action with rate limiting and retry logic."""
        # Small delay to respect Gmail API rate limits
        time.sleep(0.01)
        
        # Execute with exponential backoff retry
        return self._execute_action_with_backoff(message_id, action, params)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(Exception),
    )
    def _execute_action_with_backoff(
        self,
        message_id: str,
        action: CleanupAction,
        params: dict,
    ) -> None:
        """Execute action with exponential backoff retry."""
        return self._execute_action(message_id, action, params)
    
    def _execute_action(
        self,
        message_id: str,
        action: CleanupAction,
        params: dict,
    ) -> None:
        """Execute a single cleanup action."""
        if action == CleanupAction.DELETE:
            self.gmail.trash_message(message_id)
        elif action == CleanupAction.ARCHIVE:
            self.gmail.archive_message(message_id)
        elif action == CleanupAction.MARK_READ:
            self.gmail.mark_read(message_id)
        elif action == CleanupAction.MARK_UNREAD:
            self.gmail.mark_unread(message_id)
        elif action == CleanupAction.STAR:
            self.gmail.star_message(message_id)
        elif action == CleanupAction.UNSTAR:
            self.gmail.unstar_message(message_id)
        elif action == CleanupAction.APPLY_LABEL:
            label = params.get('label')
            if label:
                self.gmail.modify_labels(message_id, add_labels=[label])
        elif action == CleanupAction.REMOVE_LABEL:
            label = params.get('label')
            if label:
                self.gmail.modify_labels(message_id, remove_labels=[label])
        # SKIP action does nothing


class GenerateSummaryReportUseCase:
    """
    Generate human-readable summary report of cleanup run.
    
    Formats cleanup results for presentation to users.
    """
    
    def execute(self, cleanup_run: CleanupRun) -> str:
        """
        Generate summary report.
        
        Args:
            cleanup_run: CleanupRun to summarize
            
        Returns:
            Formatted text summary
        """
        summary = cleanup_run.get_summary()
        
        report = f"""
        📊 Gmail Cleanup Summary
        ========================
        
        Run ID: {summary['run_id']}
        Status: {summary['status']}
        Policy: {summary['policy']}
        Started: {summary['started_at']}
        Duration: {summary.get('duration_seconds', 0):.1f}s
        
        📧 Actions Taken:
        - Total: {summary['actions']['total']}
        - Successful: {summary['actions']['successful']}
        - Failed: {summary['actions']['failed']}
        - Skipped: {summary['actions']['skipped']}
        
        📈 Outcomes:
        - Emails Deleted: {summary['outcomes']['emails_deleted']}
        - Emails Archived: {summary['outcomes']['emails_archived']}
        - Emails Labeled: {summary['outcomes']['emails_labeled']}
        """
        
        if 'storage_freed_mb' in summary:
            report += f"\n💾 Storage Freed: {summary['storage_freed_mb']:.2f} MB\n"
        
        if summary.get('error'):
            report += f"\n⚠️ Error: {summary['error']}\n"
        
        return report.strip()
