#!/bin/bash
# Gmail Cleanup Agent Runner - Presentation Layer Entrypoint
# 
# This script is a thin CLI wrapper that instantiates use cases
# from src.application.gmail_cleanup_use_cases and runs them.
# 
# No business logic should live here - only dependency wiring
# and CLI argument handling.

set -e

cd "$(dirname "$0")"

# Load environment variables if .env exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Parse command line arguments
DRY_RUN="${DRY_RUN:-true}"
MAX_THREADS="${MAX_THREADS:-100}"
POLICY="${POLICY:-conservative}"

while [[ $# -gt 0 ]]; do
    case $1 in
        --execute)
            DRY_RUN=false
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --max-threads)
            MAX_THREADS="$2"
            shift 2
            ;;
        --policy)
            POLICY="$2"
            shift 2
            ;;
        --help)
            echo "Gmail Cleanup Agent - Production CLI"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dry-run         Preview actions without executing (default)"
            echo "  --execute         Execute cleanup actions"
            echo "  --max-threads N   Process up to N threads (default: 100)"
            echo "  --policy NAME     Use policy: conservative|moderate|aggressive (default: conservative)"
            echo "  --help            Show this help message"
            echo ""
            echo "Environment Variables:"
            echo "  DRY_RUN          Set to 'false' to execute (default: 'true')"
            echo "  MAX_THREADS      Maximum threads to process (default: 100)"
            echo "  POLICY           Cleanup policy name (default: 'conservative')"
            echo ""
            echo "Examples:"
            echo "  $0 --dry-run                    # Preview cleanup"
            echo "  $0 --execute --policy moderate  # Execute moderate cleanup"
            echo "  $0 --execute --max-threads 50   # Execute on 50 threads"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Export for Python script
export DRY_RUN
export MAX_THREADS
export POLICY

echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║          Gmail Cleanup Agent - Production CLI              ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Configuration:"
echo "  Mode:        $([ "$DRY_RUN" = "true" ] && echo "DRY RUN (preview only)" || echo "EXECUTE (will modify Gmail)")"
echo "  Max Threads: $MAX_THREADS"
echo "  Policy:      $POLICY"
echo ""

# Run the agent using src.application use cases directly
# examples/gmail_cleanup_agent.py is now a reference implementation
python3 -c "
import os
import sys

# Add src to path
sys.path.insert(0, 'src')

from application.gmail_cleanup_use_cases import (
    AnalyzeInboxUseCase,
    DryRunCleanupUseCase,
    ExecuteCleanupUseCase,
)
from infrastructure.gmail_client import GmailClient
from infrastructure.gmail_persistence import InMemoryGmailCleanupRepository
from infrastructure.gmail_observability import GmailCleanupObservability
from infrastructure.observability import ObservabilityProvider
from domain.cleanup_policy import CleanupPolicy

# Read configuration
dry_run = os.getenv('DRY_RUN', 'true').lower() == 'true'
max_threads = int(os.getenv('MAX_THREADS', '100'))
policy_name = os.getenv('POLICY', 'conservative')

# Wire up dependencies
gmail_client = GmailClient()
repository = InMemoryGmailCleanupRepository()
observability = GmailCleanupObservability(ObservabilityProvider())

# Create policy based on name
if policy_name == 'conservative':
    from domain.cleanup_rule_builder import CleanupRuleBuilder
    policy = (
        CleanupRuleBuilder()
        .archive_if_category('promotions')
        .archive_if_older_than_days(90)
        .never_touch_starred()
        .never_touch_important()
        .build()
    )
elif policy_name == 'moderate':
    from domain.cleanup_rule_builder import CleanupRuleBuilder
    policy = (
        CleanupRuleBuilder()
        .archive_if_category('promotions')
        .archive_if_category('social')
        .archive_if_older_than_days(60)
        .delete_if_older_than_days(180)
        .never_touch_starred()
        .never_touch_important()
        .build()
    )
elif policy_name == 'aggressive':
    from domain.cleanup_rule_builder import CleanupRuleBuilder
    policy = (
        CleanupRuleBuilder()
        .archive_if_category('promotions')
        .archive_if_category('social')
        .archive_if_category('updates')
        .archive_if_older_than_days(30)
        .delete_if_older_than_days(90)
        .never_touch_starred()
        .never_touch_important()
        .build()
    )
else:
    print(f'Unknown policy: {policy_name}')
    sys.exit(1)

# Get user email from Gmail profile
profile = gmail_client.get_profile()
user_id = profile.get('emailAddress', 'unknown')

print(f'User: {user_id}')
print(f'Policy: {policy.name}')
print('')

# Execute appropriate use case
if dry_run:
    print('Running dry run (preview only)...')
    print('')
    use_case = DryRunCleanupUseCase(gmail_client, observability)
    result = use_case.execute(user_id, policy, max_threads)
    
    print(f'Dry Run ID: {result.id}')
    print(f'Threads Analyzed: {len(result.threads_analyzed)}')
    print(f'Actions Planned: {len(result.actions)}')
    print('')
    print('Breakdown:')
    summary = result.get_summary()
    for action_type, count in summary.get('actions_by_type', {}).items():
        print(f'  {action_type}: {count}')
    print('')
    print('✅ Dry run complete. Use --execute to apply changes.')
else:
    print('⚠️  EXECUTING CLEANUP - This will modify your Gmail!')
    print('')
    use_case = ExecuteCleanupUseCase(gmail_client, repository, observability)
    result = use_case.execute(user_id, policy, max_threads, dry_run=False)
    
    print(f'Cleanup Run ID: {result.id}')
    print(f'Status: {result.status.value}')
    print(f'Duration: {result.duration_seconds:.1f}s')
    print(f'Actions Performed: {len(result.actions)}')
    print(f'  Successful: {result.actions_successful}')
    print(f'  Failed: {result.actions_failed}')
    print('')
    print('Results:')
    print(f'  Emails Deleted: {result.emails_deleted}')
    print(f'  Emails Archived: {result.emails_archived}')
    print(f'  Storage Freed: {result.storage_freed_mb:.1f} MB')
    print('')
    print('✅ Cleanup complete!')
"

