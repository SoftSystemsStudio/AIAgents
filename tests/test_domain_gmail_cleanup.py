"""
Tests for Gmail cleanup domain models.

Tests pure business logic without external dependencies.
"""

import pytest
from datetime import datetime, timedelta
from src.domain.email_thread import (
    EmailAddress,
    EmailMessage,
    EmailThread,
    MailboxSnapshot,
    EmailCategory,
    EmailImportance,
)
from src.domain.cleanup_policy import (
    CleanupRule,
    CleanupAction,
    RuleCondition,
    CleanupPolicy,
    RetentionPolicy,
    LabelingRule,
)
from src.domain.metrics import (
    CleanupRun,
    CleanupStatus,
    CleanupAction as CleanupActionRecord,
    ActionStatus,
    MailboxStats,
)


# ============================================================================
# EmailAddress Tests
# ============================================================================

def test_email_address_domain():
    """Test domain extraction from email address."""
    addr = EmailAddress(address="user@example.com", name="John Doe")
    assert addr.domain == "example.com"
    
    addr2 = EmailAddress(address="admin@subdomain.example.org", name="")
    assert addr2.domain == "subdomain.example.org"


def test_email_address_string():
    """Test string representation."""
    addr = EmailAddress(address="user@example.com", name="John Doe")
    assert str(addr) == "John Doe <user@example.com>"
    
    addr2 = EmailAddress(address="user@example.com", name="")
    assert str(addr2) == "user@example.com"


# ============================================================================
# EmailMessage Tests
# ============================================================================

def test_email_message_age_days():
    """Test age calculation."""
    now = datetime.utcnow()
    old_date = now - timedelta(days=45)
    
    msg = EmailMessage(
        id="msg1",
        thread_id="thread1",
        from_address=EmailAddress(address="sender@example.com", name="Sender"),
        to_addresses=[],
        cc_addresses=[],
        subject="Test",
        snippet="Test snippet",
        date=old_date,
        labels=["INBOX"],
        is_unread=False,
        is_starred=False,
        has_attachments=False,
        size_bytes=1024,
        category=EmailCategory.PRIMARY,
        importance=EmailImportance.MEDIUM,
    )
    
    assert msg.age_days == 45


def test_email_message_is_in_inbox():
    """Test inbox detection."""
    msg = EmailMessage(
        id="msg1",
        thread_id="thread1",
        from_address=EmailAddress(address="sender@example.com", name=""),
        to_addresses=[],
        cc_addresses=[],
        subject="Test",
        snippet="",
        date=datetime.utcnow(),
        labels=["INBOX", "UNREAD"],
        is_unread=True,
        is_starred=False,
        has_attachments=False,
        size_bytes=1024,
        category=EmailCategory.PRIMARY,
        importance=EmailImportance.MEDIUM,
    )
    
    assert msg.is_in_inbox is True
    
    msg.labels = ["ARCHIVE"]
    assert msg.is_in_inbox is False


def test_email_message_matches_sender():
    """Test sender matching."""
    msg = EmailMessage(
        id="msg1",
        thread_id="thread1",
        from_address=EmailAddress(address="notifications@linkedin.com", name="LinkedIn"),
        to_addresses=[],
        cc_addresses=[],
        subject="Test",
        snippet="",
        date=datetime.utcnow(),
        labels=["INBOX"],
        is_unread=False,
        is_starred=False,
        has_attachments=False,
        size_bytes=1024,
        category=EmailCategory.SOCIAL,
        importance=EmailImportance.LOW,
    )
    
    # Match by full email
    assert msg.matches_sender("notifications@linkedin.com") is True
    
    # Match by domain
    assert msg.matches_sender("@linkedin.com") is True
    assert msg.matches_sender("linkedin.com") is True
    
    # No match
    assert msg.matches_sender("@facebook.com") is False
    assert msg.matches_sender("other@linkedin.com") is False


# ============================================================================
# EmailThread Tests
# ============================================================================

def test_email_thread_properties():
    """Test thread aggregation properties."""
    now = datetime.utcnow()
    msg1 = EmailMessage(
        id="msg1",
        thread_id="thread1",
        from_address=EmailAddress(address="user1@example.com", name="User 1"),
        to_addresses=[],
        cc_addresses=[],
        subject="Test Thread",
        snippet="First message",
        date=now - timedelta(days=5),
        labels=["INBOX", "UNREAD"],
        is_unread=True,
        is_starred=False,
        has_attachments=True,
        size_bytes=2048,
        category=EmailCategory.PRIMARY,
        importance=EmailImportance.MEDIUM,
    )
    
    msg2 = EmailMessage(
        id="msg2",
        thread_id="thread1",
        from_address=EmailAddress(address="user2@example.com", name="User 2"),
        to_addresses=[],
        cc_addresses=[],
        subject="Re: Test Thread",
        snippet="Second message",
        date=now - timedelta(days=3),
        labels=["INBOX"],
        is_unread=False,
        is_starred=True,
        has_attachments=False,
        size_bytes=1024,
        category=EmailCategory.PRIMARY,
        importance=EmailImportance.HIGH,
    )
    
    thread = EmailThread(id="thread1", messages=[msg1, msg2])
    
    assert thread.subject == "Test Thread"
    assert thread.message_count == 2
    assert thread.latest_message == msg2
    assert thread.oldest_message == msg1
    assert thread.age_days == 5
    assert thread.total_size_bytes == 3072
    assert thread.is_unread is True
    assert thread.has_attachments is True
    assert len(thread.unique_senders) == 2


def test_email_thread_empty():
    """Test thread with no messages."""
    thread = EmailThread(id="thread1", messages=[])
    
    assert thread.message_count == 0
    assert thread.latest_message is None
    assert thread.oldest_message is None
    assert thread.total_size_bytes == 0
    assert thread.is_unread is False
    assert thread.has_attachments is False


# ============================================================================
# MailboxSnapshot Tests
# ============================================================================

def test_mailbox_snapshot_from_threads():
    """Test snapshot creation from threads."""
    now = datetime.utcnow()
    
    # Create test threads
    threads = []
    for i in range(5):
        msg = EmailMessage(
            id=f"msg{i}",
            thread_id=f"thread{i}",
            from_address=EmailAddress(address=f"sender{i}@example.com", name=""),
            to_addresses=[],
            cc_addresses=[],
            subject=f"Subject {i}",
            snippet="",
            date=now - timedelta(days=i),
            labels=["INBOX"] if i < 3 else ["ARCHIVE"],
            is_unread=i % 2 == 0,
            is_starred=False,
            has_attachments=i % 3 == 0,
            size_bytes=1024 * (i + 1),
            category=EmailCategory.PRIMARY if i < 2 else EmailCategory.PROMOTIONS,
            importance=EmailImportance.MEDIUM,
        )
        threads.append(EmailThread(id=f"thread{i}", messages=[msg]))
    
    snapshot = MailboxSnapshot.from_threads("user123", threads)
    
    assert snapshot.user_id == "user123"
    assert snapshot.thread_count == 5
    assert snapshot.message_count == 5
    assert snapshot.total_size_bytes == 1024 * (1 + 2 + 3 + 4 + 5)
    
    stats = snapshot.summary_stats()
    assert stats["total_threads"] == 5
    assert stats["unread_threads"] == 3  # 0, 2, 4
    assert stats["threads_with_attachments"] == 2  # 0, 3


def test_mailbox_snapshot_get_threads_by_sender():
    """Test filtering threads by sender."""
    msg1 = EmailMessage(
        id="msg1",
        thread_id="thread1",
        from_address=EmailAddress(address="user@linkedin.com", name=""),
        to_addresses=[],
        cc_addresses=[],
        subject="LinkedIn notification",
        snippet="",
        date=datetime.utcnow(),
        labels=["INBOX"],
        is_unread=True,
        is_starred=False,
        has_attachments=False,
        size_bytes=1024,
        category=EmailCategory.SOCIAL,
        importance=EmailImportance.LOW,
    )
    
    msg2 = EmailMessage(
        id="msg2",
        thread_id="thread2",
        from_address=EmailAddress(address="user@example.com", name=""),
        to_addresses=[],
        cc_addresses=[],
        subject="Work email",
        snippet="",
        date=datetime.utcnow(),
        labels=["INBOX"],
        is_unread=False,
        is_starred=False,
        has_attachments=False,
        size_bytes=1024,
        category=EmailCategory.PRIMARY,
        importance=EmailImportance.MEDIUM,
    )
    
    snapshot = MailboxSnapshot(
        user_id="user123",
        captured_at=datetime.utcnow(),
        threads=[
            EmailThread(id="thread1", messages=[msg1]),
            EmailThread(id="thread2", messages=[msg2]),
        ],
    )
    
    linkedin_threads = snapshot.get_threads_by_sender("@linkedin.com")
    assert len(linkedin_threads) == 1
    assert linkedin_threads[0].id == "thread1"


def test_mailbox_snapshot_get_old_threads():
    """Test filtering old threads."""
    now = datetime.utcnow()
    old_msg = EmailMessage(
        id="msg1",
        thread_id="thread1",
        from_address=EmailAddress(address="user@example.com", name=""),
        to_addresses=[],
        cc_addresses=[],
        subject="Old email",
        snippet="",
        date=now - timedelta(days=60),
        labels=["INBOX"],
        is_unread=False,
        is_starred=False,
        has_attachments=False,
        size_bytes=1024,
        category=EmailCategory.PRIMARY,
        importance=EmailImportance.MEDIUM,
    )
    
    new_msg = EmailMessage(
        id="msg2",
        thread_id="thread2",
        from_address=EmailAddress(address="user@example.com", name=""),
        to_addresses=[],
        cc_addresses=[],
        subject="Recent email",
        snippet="",
        date=now - timedelta(days=5),
        labels=["INBOX"],
        is_unread=True,
        is_starred=False,
        has_attachments=False,
        size_bytes=1024,
        category=EmailCategory.PRIMARY,
        importance=EmailImportance.MEDIUM,
    )
    
    snapshot = MailboxSnapshot(
        user_id="user123",
        captured_at=datetime.utcnow(),
        threads=[
            EmailThread(id="thread1", messages=[old_msg]),
            EmailThread(id="thread2", messages=[new_msg]),
        ],
    )
    
    old_threads = snapshot.get_old_threads(days=30)
    assert len(old_threads) == 1
    assert old_threads[0].id == "thread1"


# ============================================================================
# CleanupRule Tests
# ============================================================================

def test_cleanup_rule_sender_matches():
    """Test rule matching by sender."""
    rule = CleanupRule(
        id="rule1",
        name="Archive LinkedIn",
        description="Archive all LinkedIn emails",
        condition_type=RuleCondition.SENDER_MATCHES,
        condition_value="@linkedin.com",
        action=CleanupAction.ARCHIVE,
    )
    
    msg = EmailMessage(
        id="msg1",
        thread_id="thread1",
        from_address=EmailAddress(address="notifications@linkedin.com", name=""),
        to_addresses=[],
        cc_addresses=[],
        subject="Test",
        snippet="",
        date=datetime.utcnow(),
        labels=["INBOX"],
        is_unread=False,
        is_starred=False,
        has_attachments=False,
        size_bytes=1024,
        category=EmailCategory.SOCIAL,
        importance=EmailImportance.LOW,
    )
    
    assert rule.matches_message(msg) is True


def test_cleanup_rule_older_than():
    """Test rule matching by age."""
    rule = CleanupRule(
        id="rule1",
        name="Archive old emails",
        description="Archive emails older than 30 days",
        condition_type=RuleCondition.OLDER_THAN_DAYS,
        condition_value="30",
        action=CleanupAction.ARCHIVE,
    )
    
    old_msg = EmailMessage(
        id="msg1",
        thread_id="thread1",
        from_address=EmailAddress(address="user@example.com", name=""),
        to_addresses=[],
        cc_addresses=[],
        subject="Old email",
        snippet="",
        date=datetime.utcnow() - timedelta(days=45),
        labels=["INBOX"],
        is_unread=False,
        is_starred=False,
        has_attachments=False,
        size_bytes=1024,
        category=EmailCategory.PRIMARY,
        importance=EmailImportance.MEDIUM,
    )
    
    new_msg = EmailMessage(
        id="msg2",
        thread_id="thread2",
        from_address=EmailAddress(address="user@example.com", name=""),
        to_addresses=[],
        cc_addresses=[],
        subject="Recent email",
        snippet="",
        date=datetime.utcnow() - timedelta(days=5),
        labels=["INBOX"],
        is_unread=True,
        is_starred=False,
        has_attachments=False,
        size_bytes=1024,
        category=EmailCategory.PRIMARY,
        importance=EmailImportance.MEDIUM,
    )
    
    assert rule.matches_message(old_msg) is True
    assert rule.matches_message(new_msg) is False


def test_cleanup_rule_category():
    """Test rule matching by category."""
    rule = CleanupRule(
        id="rule1",
        name="Archive promotions",
        description="Archive promotional emails",
        condition_type=RuleCondition.CATEGORY_IS,
        condition_value="promotions",
        action=CleanupAction.ARCHIVE,
    )
    
    promo_msg = EmailMessage(
        id="msg1",
        thread_id="thread1",
        from_address=EmailAddress(address="deals@store.com", name=""),
        to_addresses=[],
        cc_addresses=[],
        subject="50% off sale!",
        snippet="",
        date=datetime.utcnow(),
        labels=["INBOX", "CATEGORY_PROMOTIONS"],
        is_unread=True,
        is_starred=False,
        has_attachments=False,
        size_bytes=1024,
        category=EmailCategory.PROMOTIONS,
        importance=EmailImportance.LOW,
    )
    
    primary_msg = EmailMessage(
        id="msg2",
        thread_id="thread2",
        from_address=EmailAddress(address="boss@company.com", name=""),
        to_addresses=[],
        cc_addresses=[],
        subject="Important meeting",
        snippet="",
        date=datetime.utcnow(),
        labels=["INBOX"],
        is_unread=True,
        is_starred=True,
        has_attachments=False,
        size_bytes=1024,
        category=EmailCategory.PRIMARY,
        importance=EmailImportance.HIGH,
    )
    
    assert rule.matches_message(promo_msg) is True
    assert rule.matches_message(primary_msg) is False


# ============================================================================
# CleanupPolicy Tests
# ============================================================================

def test_cleanup_policy_get_actions():
    """Test policy action determination."""
    policy = CleanupPolicy(
        id="policy1",
        user_id="user123",
        name="Test Policy",
        description="Test policy",
        cleanup_rules=[
            CleanupRule(
                id="rule1",
                name="Archive old promotions",
                description="",
                condition_type=RuleCondition.CATEGORY_IS,
                condition_value="promotions",
                action=CleanupAction.ARCHIVE,
                priority=10,
            )
        ],
        auto_archive_promotions=False,
        auto_archive_social=False,
    )
    
    promo_msg = EmailMessage(
        id="msg1",
        thread_id="thread1",
        from_address=EmailAddress(address="deals@store.com", name=""),
        to_addresses=[],
        cc_addresses=[],
        subject="Sale!",
        snippet="",
        date=datetime.utcnow(),
        labels=["INBOX"],
        is_unread=True,
        is_starred=False,
        has_attachments=False,
        size_bytes=1024,
        category=EmailCategory.PROMOTIONS,
        importance=EmailImportance.LOW,
    )
    
    actions = policy.get_actions_for_message(promo_msg)
    
    assert len(actions) == 1
    assert actions[0][0] == CleanupAction.ARCHIVE


def test_cleanup_policy_default():
    """Test default policy creation."""
    policy = CleanupPolicy.create_default_policy("user123")
    
    assert policy.user_id == "user123"
    assert policy.auto_archive_promotions is True
    assert policy.auto_archive_social is True
    assert policy.old_threshold_days == 30


# ============================================================================
# CleanupRun Tests
# ============================================================================

def test_cleanup_run_metrics():
    """Test cleanup run metric calculations."""
    run = CleanupRun(
        id="run1",
        user_id="user123",
        policy_id="policy1",
        policy_name="Test Policy",
        status=CleanupStatus.COMPLETED,
        started_at=datetime.utcnow(),
    )
    
    # Add actions
    run.actions = [
        CleanupActionRecord(
            message_id="msg1",
            action_type="delete",
            status=ActionStatus.SUCCESS,
        ),
        CleanupActionRecord(
            message_id="msg2",
            action_type="archive",
            status=ActionStatus.SUCCESS,
        ),
        CleanupActionRecord(
            message_id="msg3",
            action_type="delete",
            status=ActionStatus.FAILED,
            error_message="Permission denied",
        ),
    ]
    
    run.completed_at = run.started_at + timedelta(seconds=10)
    
    assert run.actions_successful == 2
    assert run.actions_failed == 1
    assert run.emails_deleted == 1
    assert run.emails_archived == 1
    assert run.duration_seconds == 10.0
    
    actions_by_type = run.actions_by_type
    assert actions_by_type["delete"] == 2
    assert actions_by_type["archive"] == 1


def test_mailbox_stats_health_score():
    """Test mailbox health score calculation."""
    stats = MailboxStats(
        user_id="user123",
        total_messages=1000,
        unread_messages=100,  # 10% unread
        messages_older_than_90_days=200,  # 20% old
        promotions_messages=300,  # 30% promotions
    )
    
    score = stats.get_health_score()
    
    # Score should be reduced for high unread ratio, old emails, and promotions
    assert 0 <= score <= 100
    assert score < 81  # Should be penalized significantly


def test_mailbox_stats_from_snapshot():
    """Test stats creation from snapshot."""
    now = datetime.utcnow()
    msg = EmailMessage(
        id="msg1",
        thread_id="thread1",
        from_address=EmailAddress(address="user@example.com", name=""),
        to_addresses=[],
        cc_addresses=[],
        subject="Test",
        snippet="",
        date=now,
        labels=["INBOX", "UNREAD"],
        is_unread=True,
        is_starred=False,
        has_attachments=True,
        size_bytes=1024 * 1024,  # 1 MB
        category=EmailCategory.PRIMARY,
        importance=EmailImportance.MEDIUM,
    )
    
    # Use from_threads to properly calculate stats
    snapshot = MailboxSnapshot.from_threads(
        user_id="user123",
        threads=[EmailThread(id="thread1", messages=[msg])]
    )
    
    stats = MailboxStats.from_snapshot(snapshot)
    
    assert stats.user_id == "user123"
    assert stats.total_messages == 1
    assert stats.total_size_mb == 1.0
    assert stats.messages_with_attachments == 1
