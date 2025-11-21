"""
End-to-End Gmail Cleanup Workflow Tests

Demonstrates the complete workflow from Gmail API to cleanup execution.
These tests require real Gmail credentials but can run in dry-run mode.

Setup:
1. Place credentials.json in project root (from Google Cloud Console)
2. Run once to authenticate and generate token.pickle
3. Tests will use existing token for subsequent runs

To run:
    pytest tests/test_e2e_gmail_workflow.py -v -m e2e
"""
import pytest
from datetime import datetime
import os

from src.domain.cleanup_policy import CleanupPolicy
from src.domain.cleanup_rule_builder import (
    CleanupRuleBuilder,
    archive_old_promotions,
    delete_very_old,
)
from src.domain.email_thread import EmailCategory
from src.application.gmail_cleanup_use_cases import (
    ExecuteCleanupUseCase,
    AnalyzeInboxUseCase,
)
from src.infrastructure.gmail_persistence import InMemoryGmailCleanupRepository


# Skip these tests if Gmail credentials not available
pytestmark = pytest.mark.skipif(
    not os.path.exists('credentials.json'),
    reason="Gmail credentials.json not found"
)


@pytest.fixture
def gmail_client():
    """
    Provide real Gmail client (requires credentials).
    
    Note: This will prompt for OAuth on first run.
    """
    from src.infrastructure.gmail_client import GmailClient
    return GmailClient()


@pytest.fixture
def repository():
    """Provide in-memory repository for testing."""
    return InMemoryGmailCleanupRepository()


# ============================================================================
# Workflow Demonstration Tests
# ============================================================================

@pytest.mark.e2e
@pytest.mark.skipif(True, reason="Requires manual Gmail credentials setup")
def test_analyze_real_inbox(gmail_client):
    """
    Demonstrate analyzing a real Gmail inbox.
    
    This is a read-only operation that shows:
    - Fetching threads from Gmail API
    - Converting to domain entities
    - Generating mailbox statistics
    """
    use_case = AnalyzeInboxUseCase(gmail_client, None)
    
    # Analyze first 10 threads
    analysis = use_case.execute(
        user_id="me",
        policy=CleanupPolicy(
            id="demo",
            user_id="me",
            name="Demo Analysis",
            description="Demonstrate inbox analysis",
            cleanup_rules=[
                archive_old_promotions(days=30),
            ],
        ),
        max_threads=10,
    )
    
    # Verify structure
    assert "user_id" in analysis
    assert "snapshot" in analysis
    assert "recommendations" in analysis
    
    # Display results
    print(f"\n📊 Inbox Analysis:")
    print(f"  Total threads: {analysis['snapshot']['total_threads']}")
    print(f"  Total messages: {analysis['snapshot']['total_messages']}")
    print(f"  Size: {analysis['snapshot']['size_mb']:.2f} MB")
    print(f"  Health score: {analysis['health_score']:.1f}%")
    print(f"\n💡 Recommendations:")
    print(f"  Threads affected: {analysis['recommendations']['total_threads_affected']}")
    print(f"  Total actions: {analysis['recommendations']['total_actions']}")
    print(f"  Actions by type: {analysis['recommendations']['actions_by_type']}")


@pytest.mark.e2e
@pytest.mark.skipif(True, reason="Requires manual Gmail credentials setup")
def test_dry_run_with_real_gmail(gmail_client, repository):
    """
    Demonstrate dry-run cleanup with real Gmail data.
    
    Shows:
    - Reading real threads from Gmail
    - Applying cleanup rules
    - Generating action plan
    - NOT executing (dry-run mode)
    """
    policy = CleanupPolicy(
        id="dry-run-demo",
        user_id="me",
        name="Dry Run Demo",
        description="Safe demonstration of cleanup actions",
        cleanup_rules=[
            CleanupRuleBuilder()
                .category(EmailCategory.PROMOTIONS)
                .older_than_days(90)
                .archive()
                .build(),
            CleanupRuleBuilder()
                .older_than_days(365)
                .delete()
                .with_priority(200)
                .build(),
        ],
    )
    
    use_case = ExecuteCleanupUseCase(gmail_client, repository, None)
    
    # Execute in dry-run mode (safe, no changes)
    run = use_case.execute("me", policy, max_threads=20, dry_run=True)
    
    # Verify it was a dry run
    assert run.status.value == "dry_run"
    
    # Display plan
    print(f"\n📋 Dry-Run Cleanup Plan:")
    print(f"  Run ID: {run.id}")
    print(f"  Status: {run.status.value}")
    print(f"  Threads scanned: {run.before_snapshot.thread_count}")
    print(f"  Actions planned: {len(run.actions)}")
    
    # Break down by action type
    action_types = {}
    for action in run.actions:
        action_types[action.action_type] = action_types.get(action.action_type, 0) + 1
    
    print(f"\n  Action breakdown:")
    for action_type, count in action_types.items():
        print(f"    {action_type}: {count}")
    
    # Sample actions
    if run.actions:
        print(f"\n  Sample actions:")
        for action in run.actions[:3]:
            print(f"    - {action.action_type}: {action.message_subject}")


# ============================================================================
# Builder Pattern Demonstration
# ============================================================================

@pytest.mark.unit
def test_builder_pattern_examples():
    """
    Demonstrate CleanupRuleBuilder usage patterns.
    
    Shows various ways to create rules using the fluent API.
    """
    # Simple rule
    rule1 = (CleanupRuleBuilder()
             .older_than_days(30)
             .archive()
             .build())
    
    assert rule1.condition_type.value == "older_than_days"
    assert rule1.condition_value == "30"
    assert rule1.action.value == "archive"
    print(f"\n✅ Simple rule: {rule1.name}")
    
    # Category-based rule
    rule2 = (CleanupRuleBuilder()
             .category(EmailCategory.PROMOTIONS)
             .older_than_days(7)
             .archive()
             .with_priority(10)
             .build())
    
    assert rule2.condition_type.value == "category_is"
    assert rule2.priority == 10
    print(f"✅ Category rule: {rule2.name}")
    
    # Sender-based rule
    rule3 = (CleanupRuleBuilder()
             .sender_matches("@newsletters.com")
             .apply_label("AutoCleanup/Newsletters")
             .build())
    
    assert rule3.action.value == "apply_label"
    assert rule3.action_params["label"] == "AutoCleanup/Newsletters"
    print(f"✅ Sender rule: {rule3.name}")
    
    # Custom rule with all options
    rule4 = (CleanupRuleBuilder()
             .subject_contains("daily digest")
             .mark_read()
             .with_name("Mark Digests Read")
             .with_description("Automatically mark daily digests as read")
             .with_priority(50)
             .build())
    
    assert rule4.name == "Mark Digests Read"
    assert rule4.description == "Automatically mark daily digests as read"
    print(f"✅ Custom rule: {rule4.name}")
    
    # Using convenience factories
    rule5 = archive_old_promotions(days=30)
    rule6 = delete_very_old(days=180)
    
    print(f"✅ Factory rule 1: {rule5.name}")
    print(f"✅ Factory rule 2: {rule6.name}")


@pytest.mark.unit
def test_policy_creation_with_builder():
    """
    Demonstrate creating complete policies with builders.
    
    Shows how to combine multiple rules into a cohesive policy.
    """
    policy = CleanupPolicy(
        id="comprehensive-policy",
        user_id="user@example.com",
        name="Comprehensive Cleanup",
        description="Multi-rule cleanup strategy",
        cleanup_rules=[
            # Archive old promotions
            CleanupRuleBuilder()
                .category(EmailCategory.PROMOTIONS)
                .older_than_days(30)
                .archive()
                .with_priority(10)
                .build(),
            
            # Archive old social
            CleanupRuleBuilder()
                .category(EmailCategory.SOCIAL)
                .older_than_days(14)
                .archive()
                .with_priority(20)
                .build(),
            
            # Delete very old
            CleanupRuleBuilder()
                .older_than_days(365)
                .delete()
                .with_priority(100)
                .build(),
            
            # Mark old unread as read
            CleanupRuleBuilder()
                .is_unread(True)
                .older_than_days(90)
                .mark_read()
                .with_priority(50)
                .build(),
        ],
    )
    
    assert len(policy.cleanup_rules) == 4
    
    print(f"\n📋 Policy: {policy.name}")
    print(f"  Description: {policy.description}")
    print(f"  Rules: {len(policy.cleanup_rules)}")
    
    for i, rule in enumerate(policy.cleanup_rules, 1):
        print(f"    {i}. {rule.name} (priority: {rule.priority})")


# ============================================================================
# Safety Validation Tests
# ============================================================================

@pytest.mark.unit
def test_safety_guardrails_in_domain():
    """
    Verify safety guardrails are enforced at domain level.
    
    Shows that starred/important messages are protected.
    """
    from src.domain.email_thread import EmailMessage, EmailAddress, EmailCategory, EmailImportance
    from datetime import datetime
    
    # Create starred message
    starred_msg = EmailMessage(
        id="msg1",
        thread_id="thread1",
        from_address=EmailAddress(address="test@example.com", name="Test"),
        to_addresses=[EmailAddress(address="me@example.com", name="Me")],
        cc_addresses=[],
        subject="Important Email",
        snippet="This is important",
        date=datetime.now(),
        labels=["INBOX"],
        is_unread=True,
        is_starred=True,  # STARRED
        has_attachments=False,
        size_bytes=1024,
        category=EmailCategory.PRIMARY,
        importance=EmailImportance.HIGH,
    )
    
    # Create important message
    important_msg = EmailMessage(
        id="msg2",
        thread_id="thread2",
        from_address=EmailAddress(address="test@example.com", name="Test"),
        to_addresses=[EmailAddress(address="me@example.com", name="Me")],
        cc_addresses=[],
        subject="Important Email",
        snippet="This is important",
        date=datetime.now(),
        labels=["INBOX", "IMPORTANT"],  # IMPORTANT LABEL
        is_unread=True,
        is_starred=False,
        has_attachments=False,
        size_bytes=1024,
        category=EmailCategory.PRIMARY,
        importance=EmailImportance.HIGH,
    )
    
    # Create normal message (should be affected) - old enough to match
    from datetime import timedelta
    old_date = datetime.now() - timedelta(days=10)
    
    normal_msg = EmailMessage(
        id="msg3",
        thread_id="thread3",
        from_address=EmailAddress(address="test@example.com", name="Test"),
        to_addresses=[EmailAddress(address="me@example.com", name="Me")],
        cc_addresses=[],
        subject="Normal Email",
        snippet="This is normal",
        date=old_date,  # 10 days old
        labels=["INBOX"],
        is_unread=True,
        is_starred=False,
        has_attachments=False,
        size_bytes=1024,
        category=EmailCategory.PROMOTIONS,
        importance=EmailImportance.LOW,
    )
    
    # Aggressive policy (should match messages older than 1 day)
    policy = CleanupPolicy(
        id="aggressive",
        user_id="test",
        name="Aggressive Cleanup",
        description="Delete everything (testing safety)",
        cleanup_rules=[
            CleanupRuleBuilder()
                .older_than_days(1)
                .delete()
                .build(),
        ],
    )
    
    # Test safety guardrails
    starred_actions = policy.get_actions_for_message(starred_msg)
    important_actions = policy.get_actions_for_message(important_msg)
    normal_actions = policy.get_actions_for_message(normal_msg)
    
    # Verify protection
    assert len(starred_actions) == 0, "Starred message should be protected"
    assert len(important_actions) == 0, "Important message should be protected"
    assert len(normal_actions) > 0, "Normal message should have actions"
    
    print(f"\n🛡️ Safety Guardrails Validated:")
    print(f"  Starred message: {len(starred_actions)} actions (protected ✓)")
    print(f"  Important message: {len(important_actions)} actions (protected ✓)")
    print(f"  Normal message: {len(normal_actions)} actions (will be cleaned)")


# ============================================================================
# Documentation Test
# ============================================================================

@pytest.mark.unit
def test_workflow_documentation():
    """
    Document the complete workflow for end users.
    
    This test serves as living documentation.
    """
    workflow_doc = """
    
    ═══════════════════════════════════════════════════════════════
    GMAIL CLEANUP WORKFLOW - COMPLETE GUIDE
    ═══════════════════════════════════════════════════════════════
    
    PHASE 1: Setup
    ─────────────────────────────────────────────────────────────
    1. Get Gmail API credentials from Google Cloud Console
    2. Place credentials.json in project root
    3. Run once to authenticate: python -m src.infrastructure.gmail_client
    4. token.pickle will be created for future use
    
    PHASE 2: Analysis (Read-Only)
    ─────────────────────────────────────────────────────────────
    1. Create AnalyzeInboxUseCase with GmailClient
    2. Call analyze() with user_id and policy
    3. Review:
       - Total threads/messages
       - Size breakdown
       - Health score
       - Recommended actions
    
    PHASE 3: Dry-Run (Safe Preview)
    ─────────────────────────────────────────────────────────────
    1. Create ExecuteCleanupUseCase
    2. Build policy with CleanupRuleBuilder:
       - archive_old_promotions(days=30)
       - delete_very_old(days=365)
       - Custom rules with builder
    3. Call execute(dry_run=True)
    4. Review action plan:
       - What will be archived
       - What will be deleted
       - Message counts
    
    PHASE 4: Execute (Real Changes)
    ─────────────────────────────────────────────────────────────
    ⚠️  CAUTION: This modifies your Gmail account!
    
    1. Review dry-run results carefully
    2. Adjust policy if needed
    3. Call execute(dry_run=False)
    4. Changes are immediate and permanent
    5. Run is saved to repository for audit trail
    
    SAFETY FEATURES
    ─────────────────────────────────────────────────────────────
    ✓ Starred messages: NEVER touched
    ✓ Important messages: NEVER touched
    ✓ Archive before delete: Recommended pattern
    ✓ Dry-run first: Always test before executing
    ✓ Audit trail: All runs logged with unique IDs
    ✓ Undo capability: Query run history, retrieve affected threads
    
    BEST PRACTICES
    ─────────────────────────────────────────────────────────────
    1. Start with dry-run
    2. Use archive instead of delete initially
    3. Test with small batches (max_threads=10)
    4. Review action logs after execution
    5. Keep audit trail for compliance
    6. Use labels for reversible operations
    
    ═══════════════════════════════════════════════════════════════
    """
    
    print(workflow_doc)
    assert True  # Documentation test always passes
