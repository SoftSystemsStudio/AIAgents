"""
Usage Tracking Service - Monitor and enforce customer quotas.

Tracks email processing usage per customer and enforces plan limits.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID
from dataclasses import dataclass

from src.domain.customer import Customer, UsageStats, PlanQuota


class QuotaExceededError(Exception):
    """Raised when usage tracking detects quota exceeded"""
    pass


@dataclass
class UsageRecord:
    """A single usage record"""
    customer_id: UUID
    period: str  # YYYY-MM format
    emails_processed: int
    cleanups_executed: int
    created_at: datetime
    updated_at: datetime


class UsageTrackingService:
    """
    Service for tracking and enforcing usage quotas.
    
    In production, this would use a database. For now, uses in-memory storage.
    """
    
    def __init__(self):
        # In-memory storage: {(customer_id, period): usage_record}
        self._usage_db: Dict[tuple, UsageRecord] = {}
        # Daily cleanup counter: {(customer_id, date): count}
        self._daily_cleanups: Dict[tuple, int] = {}
    
    def record_emails_processed(
        self,
        customer_id: UUID,
        emails_count: int,
        period: Optional[str] = None,
    ) -> UsageRecord:
        """
        Record emails processed in a cleanup operation.
        
        Args:
            customer_id: Customer ID
            emails_count: Number of emails processed
            period: Period in YYYY-MM format (defaults to current month)
            
        Returns:
            Updated usage record
        """
        if period is None:
            period = datetime.utcnow().strftime("%Y-%m")
        
        key = (customer_id, period)
        
        if key in self._usage_db:
            record = self._usage_db[key]
            record.emails_processed += emails_count
            record.updated_at = datetime.utcnow()
        else:
            record = UsageRecord(
                customer_id=customer_id,
                period=period,
                emails_processed=emails_count,
                cleanups_executed=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self._usage_db[key] = record
        
        return record
    
    def record_cleanup_executed(
        self,
        customer_id: UUID,
        emails_count: int,
        period: Optional[str] = None,
    ) -> UsageRecord:
        """
        Record a cleanup execution (increments both cleanup count and emails processed).
        
        Args:
            customer_id: Customer ID
            emails_count: Number of emails processed in this cleanup
            period: Period in YYYY-MM format (defaults to current month)
            
        Returns:
            Updated usage record
        """
        if period is None:
            period = datetime.utcnow().strftime("%Y-%m")
        
        # Update monthly usage
        key = (customer_id, period)
        
        if key in self._usage_db:
            record = self._usage_db[key]
            record.cleanups_executed += 1
            record.emails_processed += emails_count
            record.updated_at = datetime.utcnow()
        else:
            record = UsageRecord(
                customer_id=customer_id,
                period=period,
                emails_processed=emails_count,
                cleanups_executed=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self._usage_db[key] = record
        
        # Update daily cleanup counter
        today = datetime.utcnow().strftime("%Y-%m-%d")
        daily_key = (customer_id, today)
        self._daily_cleanups[daily_key] = self._daily_cleanups.get(daily_key, 0) + 1
        
        return record
    
    def get_usage(
        self,
        customer_id: UUID,
        period: Optional[str] = None,
    ) -> UsageRecord:
        """
        Get usage for a customer in a specific period.
        
        Args:
            customer_id: Customer ID
            period: Period in YYYY-MM format (defaults to current month)
            
        Returns:
            Usage record (may be empty if no usage yet)
        """
        if period is None:
            period = datetime.utcnow().strftime("%Y-%m")
        
        key = (customer_id, period)
        
        if key in self._usage_db:
            return self._usage_db[key]
        
        # Return empty record if no usage yet
        return UsageRecord(
            customer_id=customer_id,
            period=period,
            emails_processed=0,
            cleanups_executed=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    
    def get_daily_cleanup_count(
        self,
        customer_id: UUID,
        date: Optional[str] = None,
    ) -> int:
        """
        Get number of cleanups executed today.
        
        Args:
            customer_id: Customer ID
            date: Date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Number of cleanups executed today
        """
        if date is None:
            date = datetime.utcnow().strftime("%Y-%m-%d")
        
        key = (customer_id, date)
        return self._daily_cleanups.get(key, 0)
    
    def get_usage_stats(
        self,
        customer: Customer,
        period: Optional[str] = None,
    ) -> UsageStats:
        """
        Get usage statistics for a customer.
        
        Args:
            customer: Customer object
            period: Period in YYYY-MM format (defaults to current month)
            
        Returns:
            UsageStats with quota information
        """
        if period is None:
            period = datetime.utcnow().strftime("%Y-%m")
        
        usage_record = self.get_usage(customer.id, period)
        quota = customer.get_quota()
        
        return UsageStats(
            customer_id=customer.id,
            period=period,
            emails_processed=usage_record.emails_processed,
            quota_limit=quota.emails_per_month,
            cleanups_executed=usage_record.cleanups_executed,
        )
    
    def check_can_execute_cleanup(
        self,
        customer: Customer,
    ) -> tuple[bool, Optional[str]]:
        """
        Check if customer can execute a cleanup right now.
        
        Checks both daily cleanup limit and monthly email quota.
        
        Args:
            customer: Customer object
            
        Returns:
            Tuple of (can_execute, error_message)
        """
        quota = customer.get_quota()
        
        # Check daily cleanup limit
        today_count = self.get_daily_cleanup_count(customer.id)
        if today_count >= quota.cleanups_per_day:
            return False, f"Daily cleanup limit reached ({quota.cleanups_per_day}). Try again tomorrow."
        
        # Check monthly email quota
        current_period = datetime.utcnow().strftime("%Y-%m")
        usage = self.get_usage(customer.id, current_period)
        
        if usage.emails_processed >= quota.emails_per_month:
            return False, f"Monthly email quota exceeded ({quota.emails_per_month}). Please upgrade your plan."
        
        return True, None
    
    def enforce_quota(
        self,
        customer: Customer,
        emails_to_process: int,
    ) -> None:
        """
        Enforce quota limits before processing.
        
        Raises QuotaExceededError if limits would be exceeded.
        
        Args:
            customer: Customer object
            emails_to_process: Number of emails about to be processed
            
        Raises:
            QuotaExceededError: If quota would be exceeded
        """
        can_execute, error_msg = self.check_can_execute_cleanup(customer)
        
        if not can_execute:
            raise QuotaExceededError(error_msg)
        
        # Check if processing these emails would exceed monthly quota
        quota = customer.get_quota()
        current_period = datetime.utcnow().strftime("%Y-%m")
        usage = self.get_usage(customer.id, current_period)
        
        if usage.emails_processed + emails_to_process > quota.emails_per_month:
            remaining = quota.emails_per_month - usage.emails_processed
            raise QuotaExceededError(
                f"Processing {emails_to_process} emails would exceed monthly quota. "
                f"Only {remaining} emails remaining in your plan."
            )
    
    def get_quota_status(
        self,
        customer: Customer,
    ) -> Dict[str, Any]:
        """
        Get comprehensive quota status for customer.
        
        Args:
            customer: Customer object
            
        Returns:
            Dictionary with all quota information
        """
        quota = customer.get_quota()
        current_period = datetime.utcnow().strftime("%Y-%m")
        usage = self.get_usage(customer.id, current_period)
        today_count = self.get_daily_cleanup_count(customer.id)
        
        emails_remaining = max(0, quota.emails_per_month - usage.emails_processed)
        emails_percent = (usage.emails_processed / quota.emails_per_month) * 100 if quota.emails_per_month > 0 else 0
        
        cleanups_remaining = max(0, quota.cleanups_per_day - today_count)
        
        return {
            "customer_id": str(customer.id),
            "plan_tier": customer.plan_tier.value,
            "period": current_period,
            "emails": {
                "limit": quota.emails_per_month,
                "used": usage.emails_processed,
                "remaining": emails_remaining,
                "percent_used": round(emails_percent, 1),
                "approaching_limit": emails_percent >= 80,
            },
            "cleanups": {
                "daily_limit": quota.cleanups_per_day,
                "today_count": today_count,
                "remaining_today": cleanups_remaining,
            },
            "api_calls": {
                "hourly_limit": quota.api_calls_per_hour,
            },
            "trial": {
                "is_on_trial": customer.is_on_trial(),
                "trial_ends_at": customer.trial_ends_at.isoformat() if customer.trial_ends_at else None,
            },
            "can_execute_cleanup": cleanups_remaining > 0 and emails_remaining > 0,
        }
    
    def reset_usage(
        self,
        customer_id: UUID,
        period: Optional[str] = None,
    ) -> None:
        """
        Reset usage for a customer (admin function).
        
        Args:
            customer_id: Customer ID
            period: Period to reset (defaults to current month)
        """
        if period is None:
            period = datetime.utcnow().strftime("%Y-%m")
        
        key = (customer_id, period)
        if key in self._usage_db:
            del self._usage_db[key]
        
        # Also reset daily cleanup counter for today
        today = datetime.utcnow().strftime("%Y-%m-%d")
        daily_key = (customer_id, today)
        if daily_key in self._daily_cleanups:
            del self._daily_cleanups[daily_key]
    
    def cleanup_old_records(
        self,
        months_to_keep: int = 12,
    ) -> int:
        """
        Clean up old usage records (maintenance function).
        
        Args:
            months_to_keep: Number of months of history to keep
            
        Returns:
            Number of records deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=months_to_keep * 30)
        cutoff_period = cutoff_date.strftime("%Y-%m")
        
        deleted = 0
        keys_to_delete = []
        
        for key, record in self._usage_db.items():
            if record.period < cutoff_period:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self._usage_db[key]
            deleted += 1
        
        return deleted


# Global instance (in production, inject via dependency injection)
usage_tracking = UsageTrackingService()
