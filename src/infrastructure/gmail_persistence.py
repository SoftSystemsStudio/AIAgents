"""
Persistence Layer for Gmail Cleanup - Database storage.

Stores cleanup policies, runs, and audit trails.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import asyncio
import uuid

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    asyncpg = None  # type: ignore

from src.domain.cleanup_policy import (
    CleanupPolicy,
    CleanupRule,
    RetentionPolicy,
    CleanupAction,
    RuleCondition,
    LabelingRule,
)
from src.domain.metrics import CleanupRun, CleanupStatus, CleanupAction as MetricAction, ActionStatus


class GmailCleanupRepository:
    """
    Repository for Gmail cleanup data.
    
    Abstract interface - can be implemented for different storage backends
    (Postgres, Supabase, SQLite, etc.)
    """
    
    async def save_policy(self, policy: CleanupPolicy) -> None:
        """Save or update cleanup policy."""
        raise NotImplementedError
    
    async def get_policy(self, user_id: str, policy_id: str) -> Optional[CleanupPolicy]:
        """Retrieve cleanup policy."""
        raise NotImplementedError
    
    async def list_policies(self, user_id: str) -> List[CleanupPolicy]:
        """List all policies for a user."""
        raise NotImplementedError
    
    async def delete_policy(self, user_id: str, policy_id: str) -> None:
        """Delete cleanup policy."""
        raise NotImplementedError
    
    async def save_run(self, run: CleanupRun) -> None:
        """Save cleanup run."""
        raise NotImplementedError
    
    async def get_run(self, user_id: str, run_id: str) -> Optional[CleanupRun]:
        """Retrieve cleanup run."""
        raise NotImplementedError
    
    async def list_runs(
        self,
        user_id: str,
        limit: int = 10,
        offset: int = 0,
    ) -> List[CleanupRun]:
        """List cleanup runs for a user."""
        raise NotImplementedError
    
    async def get_run_count(self, user_id: str) -> int:
        """Get total run count for user."""
        raise NotImplementedError


class InMemoryGmailCleanupRepository(GmailCleanupRepository):
    """
    In-memory implementation for testing and development.
    
    Data is lost when process restarts.
    """
    
    def __init__(self) -> None:
        self._policies: Dict[str, Dict[str, CleanupPolicy]] = {}  # {user_id: {policy_id: CleanupPolicy}}
        self._runs: Dict[str, List[CleanupRun]] = {}  # {user_id: [CleanupRun]}
    
    async def save_policy(self, policy: CleanupPolicy) -> None:
        """Save or update cleanup policy."""
        if policy.user_id not in self._policies:
            self._policies[policy.user_id] = {}
        
        policy.updated_at = datetime.utcnow()
        self._policies[policy.user_id][policy.id] = policy
    
    async def get_policy(self, user_id: str, policy_id: str) -> Optional[CleanupPolicy]:
        """Retrieve cleanup policy."""
        user_policies = self._policies.get(user_id, {})
        return user_policies.get(policy_id)
    
    async def list_policies(self, user_id: str) -> List[CleanupPolicy]:
        """List all policies for a user."""
        user_policies = self._policies.get(user_id, {})
        return list(user_policies.values())
    
    async def delete_policy(self, user_id: str, policy_id: str) -> None:
        """Delete cleanup policy."""
        if user_id in self._policies and policy_id in self._policies[user_id]:
            del self._policies[user_id][policy_id]
    
    async def save_run(self, run: CleanupRun) -> None:
        """Save cleanup run."""
        if run.user_id not in self._runs:
            self._runs[run.user_id] = []
        
        self._runs[run.user_id].append(run)
        
        # Sort by started_at (most recent first)
        self._runs[run.user_id].sort(key=lambda r: r.started_at, reverse=True)
    
    async def get_run(self, user_id: str, run_id: str) -> Optional[CleanupRun]:
        """Retrieve cleanup run."""
        user_runs = self._runs.get(user_id, [])
        for run in user_runs:
            if run.id == run_id:
                return run
        return None
    
    async def list_runs(
        self,
        user_id: str,
        limit: int = 10,
        offset: int = 0,
    ) -> List[CleanupRun]:
        """List cleanup runs for a user."""
        user_runs = self._runs.get(user_id, [])
        return user_runs[offset:offset + limit]
    
    async def get_run_count(self, user_id: str) -> int:
        """Get total run count for user."""
        return len(self._runs.get(user_id, []))


class PostgresGmailCleanupRepository(GmailCleanupRepository):
    """
    PostgreSQL implementation with asyncpg.
    
    Schema:
    - cleanup_policies: Stores cleanup policies
    - cleanup_runs: Stores cleanup run metadata
    - cleanup_actions: Stores individual actions (audit trail)
    """
    
    def __init__(self, connection_string: str):
        """
        Initialize Postgres repository.
        
        Args:
            connection_string: PostgreSQL connection string
        """
        if not ASYNCPG_AVAILABLE:
            raise RuntimeError("asyncpg not installed. Install with: pip install asyncpg")
        
        self.connection_string = connection_string
        self._pool: Optional[Any] = None  # asyncpg.Pool when available
        self._pool_lock = asyncio.Lock()
    
    async def _get_pool(self) -> Any:  # Returns asyncpg.Pool
        """Get or create connection pool."""
        if self._pool is None:
            async with self._pool_lock:
                if self._pool is None:
                    self._pool = await asyncpg.create_pool(
                        self.connection_string,
                        min_size=2,
                        max_size=10,
                        command_timeout=60,
                    )
        return self._pool
    
    async def close(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
    
    def _policy_to_dict(self, policy: CleanupPolicy) -> Dict[str, Any]:
        """Convert policy to dict for storage."""
        return {
            "id": policy.id,
            "user_id": policy.user_id,
            "name": policy.name,
            "description": getattr(policy, "description", ""),
            "cleanup_rules": [
                {
                    "id": rule.id,
                    "name": rule.name,
                    "description": rule.description,
                    "condition_type": rule.condition_type.value if hasattr(rule.condition_type, "value") else str(rule.condition_type),
                    "condition_value": rule.condition_value,
                    "action": rule.action.value if hasattr(rule.action, "value") else str(rule.action),
                    "action_params": getattr(rule, "action_params", {}),
                    "enabled": getattr(rule, "enabled", True),
                    "priority": getattr(rule, "priority", 100),
                    "created_at": rule.created_at,
                }
                for rule in getattr(policy, "cleanup_rules", [])
            ],
            "labeling_rules": [
                {
                    "id": lr.id,
                    "name": lr.name,
                    "label_to_apply": lr.label_to_apply,
                    "condition_type": lr.condition_type.value if hasattr(lr.condition_type, "value") else str(lr.condition_type),
                    "condition_value": lr.condition_value,
                    "enabled": getattr(lr, "enabled", True),
                }
                for lr in getattr(policy, "labeling_rules", [])
            ],
            "retention_policy": (
                {
                    "id": rp.id,
                    "name": rp.name,
                    "description": rp.description,
                    "rules": getattr(rp, "rules", []),
                    "default_retention_days": getattr(rp, "default_retention_days", 365),
                    "enabled": getattr(rp, "enabled", True),
                }
                if (rp := getattr(policy, "retention_policy", None)) is not None
                else None
            ),
            "auto_archive_promotions": getattr(policy, "auto_archive_promotions", False),
            "auto_archive_social": getattr(policy, "auto_archive_social", False),
            "auto_mark_read_old": getattr(policy, "auto_mark_read_old", False),
            "old_threshold_days": getattr(policy, "old_threshold_days", 30),
            "enabled": getattr(policy, "enabled", True),
            "created_at": policy.created_at,
            "updated_at": policy.updated_at,
        }
    
    def _dict_to_policy(self, data: Dict[str, Any]) -> CleanupPolicy:
        """Convert dict from storage to policy."""
        def _parse_datetime(val: Any) -> datetime:
            if isinstance(val, datetime):
                return val
            if isinstance(val, str):
                try:
                    return datetime.fromisoformat(val)
                except Exception:
                    return datetime.utcnow()
            return datetime.utcnow()

        rules: List[CleanupRule] = []
        for rule_data in data.get("cleanup_rules", []):
            cond = rule_data.get("condition_type")
            try:
                cond_enum = RuleCondition(cond) if cond else RuleCondition.SENDER_MATCHES
            except Exception:
                cond_enum = RuleCondition.SENDER_MATCHES

            try:
                action_enum = CleanupAction(rule_data.get("action")) if rule_data.get("action") else CleanupAction.SKIP
            except Exception:
                action_enum = CleanupAction.SKIP

            rules.append(CleanupRule(
                id=rule_data.get("id", str(uuid.uuid4())),
                name=rule_data.get("name", ""),
                description=rule_data.get("description", ""),
                condition_type=cond_enum,
                condition_value=rule_data.get("condition_value", ""),
                action=action_enum,
                action_params=rule_data.get("action_params", {}),
                enabled=rule_data.get("enabled", True),
                priority=rule_data.get("priority", 100),
                created_at=_parse_datetime(rule_data.get("created_at")),
            ))

        retention = None
        if data.get("retention_policy"):
            rp = data["retention_policy"]
            retention = RetentionPolicy(
                id=rp.get("id", str(uuid.uuid4())),
                name=rp.get("name", ""),
                description=rp.get("description", ""),
                rules=rp.get("rules", []),
                default_retention_days=rp.get("default_retention_days", 365),
                enabled=rp.get("enabled", True),
            )

        return CleanupPolicy(
            id=data["id"],
            user_id=data["user_id"],
            name=data["name"],
            description=data.get("description", ""),
            cleanup_rules=rules,
            labeling_rules=[],
            retention_policy=retention,
            auto_archive_promotions=data.get("auto_archive_promotions", False),
            auto_archive_social=data.get("auto_archive_social", False),
            auto_mark_read_old=data.get("auto_mark_read_old", False),
            old_threshold_days=data.get("old_threshold_days", 30),
            enabled=data.get("enabled", True),
            created_at=_parse_datetime(data.get("created_at")),
            updated_at=_parse_datetime(data.get("updated_at")) if data.get("updated_at") is not None else datetime.utcnow(),
        )
    
    async def save_policy(self, policy: CleanupPolicy) -> None:
        """Save or update cleanup policy."""
        pool = await self._get_pool()
        policy_dict = self._policy_to_dict(policy)
        
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO cleanup_policies (
                    id, user_id, name, rules, retention, dry_run, created_at, updated_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    rules = EXCLUDED.rules,
                    retention = EXCLUDED.retention,
                    dry_run = EXCLUDED.dry_run,
                    updated_at = EXCLUDED.updated_at
            """,
                policy_dict["id"],
                policy_dict["user_id"],
                policy_dict["name"],
                json.dumps(policy_dict["rules"]),
                json.dumps(policy_dict["retention"]) if policy_dict["retention"] else None,
                policy_dict["dry_run"],
                policy_dict["created_at"],
                policy_dict["updated_at"] or datetime.utcnow(),
            )
    
    async def get_policy(self, user_id: str, policy_id: str) -> Optional[CleanupPolicy]:
        """Retrieve cleanup policy."""
        # TODO: Implement Postgres get
        # SELECT * FROM gmail_cleanup_policies WHERE user_id = ? AND policy_id = ?
        raise NotImplementedError("Postgres implementation pending")
    
    async def list_policies(self, user_id: str) -> List[CleanupPolicy]:
        """List all policies for a user."""
        # TODO: Implement Postgres list
        # SELECT * FROM gmail_cleanup_policies WHERE user_id = ?
        raise NotImplementedError("Postgres implementation pending")
    
    async def delete_policy(self, user_id: str, policy_id: str) -> None:
        """Delete cleanup policy."""
        # TODO: Implement Postgres delete
        # DELETE FROM gmail_cleanup_policies WHERE user_id = ? AND policy_id = ?
        raise NotImplementedError("Postgres implementation pending")
    
    async def save_run(self, run: CleanupRun) -> None:
        """Save cleanup run."""
        # TODO: Implement Postgres save
        # INSERT INTO gmail_cleanup_runs (run_id, user_id, policy_id, ...)
        # INSERT INTO gmail_cleanup_actions (run_id, message_id, action_type, ...)
        raise NotImplementedError("Postgres implementation pending")
    
    async def get_run(self, user_id: str, run_id: str) -> Optional[CleanupRun]:
        """Retrieve cleanup run."""
        # TODO: Implement Postgres get
        # SELECT * FROM gmail_cleanup_runs WHERE user_id = ? AND run_id = ?
        # SELECT * FROM gmail_cleanup_actions WHERE run_id = ?
        raise NotImplementedError("Postgres implementation pending")
    
    async def list_runs(
        self,
        user_id: str,
        limit: int = 10,
        offset: int = 0,
    ) -> List[CleanupRun]:
        """List cleanup runs for a user."""
        # TODO: Implement Postgres list
        # SELECT * FROM gmail_cleanup_runs WHERE user_id = ?
        # ORDER BY started_at DESC LIMIT ? OFFSET ?
        raise NotImplementedError("Postgres implementation pending")
    
    async def get_run_count(self, user_id: str) -> int:
        """Get total run count for user."""
        # TODO: Implement Postgres count
        # SELECT COUNT(*) FROM gmail_cleanup_runs WHERE user_id = ?
        raise NotImplementedError("Postgres implementation pending")


# SQL Schema for Postgres
POSTGRES_SCHEMA = """
-- Cleanup policies table
CREATE TABLE IF NOT EXISTS gmail_cleanup_policies (
    user_id VARCHAR(255) NOT NULL,
    policy_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Policy configuration (stored as JSONB for flexibility)
    config JSONB NOT NULL,
    
    -- Metadata
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    PRIMARY KEY (user_id, policy_id)
);

CREATE INDEX idx_policies_user ON gmail_cleanup_policies(user_id);
CREATE INDEX idx_policies_enabled ON gmail_cleanup_policies(user_id, enabled);

-- Cleanup runs table
CREATE TABLE IF NOT EXISTS gmail_cleanup_runs (
    run_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    policy_id VARCHAR(255) NOT NULL,
    policy_name VARCHAR(255) NOT NULL,
    
    -- Status tracking
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    
    -- Timing
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_seconds FLOAT,
    
    -- Snapshots (stored as JSONB)
    before_snapshot JSONB,
    after_snapshot JSONB,
    
    -- Agent context
    agent_session_id VARCHAR(255),
    agent_model VARCHAR(100),
    agent_prompts JSONB,
    
    -- Indexes
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_runs_user ON gmail_cleanup_runs(user_id);
CREATE INDEX idx_runs_status ON gmail_cleanup_runs(user_id, status);
CREATE INDEX idx_runs_started ON gmail_cleanup_runs(user_id, started_at DESC);
CREATE INDEX idx_runs_policy ON gmail_cleanup_runs(user_id, policy_id);

-- Cleanup actions table (audit trail)
CREATE TABLE IF NOT EXISTS gmail_cleanup_actions (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(255) NOT NULL REFERENCES gmail_cleanup_runs(run_id) ON DELETE CASCADE,
    
    -- Action details
    message_id VARCHAR(255) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    action_params JSONB,
    
    -- Status
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    executed_at TIMESTAMP,
    
    -- Context for audit trail
    message_subject TEXT,
    message_from TEXT,
    message_date TIMESTAMP,
    
    -- Index
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_actions_run ON gmail_cleanup_actions(run_id);
CREATE INDEX idx_actions_message ON gmail_cleanup_actions(message_id);
CREATE INDEX idx_actions_type ON gmail_cleanup_actions(run_id, action_type);
CREATE INDEX idx_actions_status ON gmail_cleanup_actions(run_id, status);

-- View for quick stats
CREATE OR REPLACE VIEW gmail_cleanup_stats AS
SELECT 
    user_id,
    COUNT(*) as total_runs,
    COUNT(*) FILTER (WHERE status = 'completed') as successful_runs,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_runs,
    SUM(duration_seconds) as total_duration_seconds,
    AVG(duration_seconds) as avg_duration_seconds,
    MAX(started_at) as last_run_at
FROM gmail_cleanup_runs
GROUP BY user_id;

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_policies_updated_at BEFORE UPDATE ON gmail_cleanup_policies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
"""


def get_repository(backend: str = "memory", **kwargs) -> GmailCleanupRepository:
    """
    Factory function to get repository implementation.
    
    Args:
        backend: Repository backend ('memory', 'postgres')
        **kwargs: Backend-specific configuration
        
    Returns:
        Repository implementation
    """
    if backend == "memory":
        return InMemoryGmailCleanupRepository()
    elif backend == "postgres":
        connection_string = kwargs.get("connection_string")
        if not connection_string:
            raise ValueError("Postgres backend requires connection_string")
        return PostgresGmailCleanupRepository(connection_string)
    else:
        raise ValueError(f"Unknown backend: {backend}")
