"""
Persistence Layer for Gmail Cleanup - Database storage.

Stores cleanup policies, runs, and audit trails.
"""

from typing import List, Optional
from datetime import datetime
import json

from src.domain.cleanup_policy import CleanupPolicy
from src.domain.metrics import CleanupRun


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
    
    def __init__(self):
        self._policies: dict = {}  # {user_id: {policy_id: CleanupPolicy}}
        self._runs: dict = {}  # {user_id: [CleanupRun]}
    
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
    PostgreSQL implementation.
    
    Schema:
    - gmail_cleanup_policies: Stores cleanup policies
    - gmail_cleanup_runs: Stores cleanup run metadata
    - gmail_cleanup_actions: Stores individual actions (audit trail)
    """
    
    def __init__(self, connection_string: str):
        """
        Initialize Postgres repository.
        
        Args:
            connection_string: PostgreSQL connection string
        """
        self.connection_string = connection_string
        # TODO: Initialize connection pool
    
    async def save_policy(self, policy: CleanupPolicy) -> None:
        """Save or update cleanup policy."""
        # TODO: Implement Postgres save
        # INSERT INTO gmail_cleanup_policies ...
        # ON CONFLICT (user_id, policy_id) DO UPDATE
        raise NotImplementedError("Postgres implementation pending")
    
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
