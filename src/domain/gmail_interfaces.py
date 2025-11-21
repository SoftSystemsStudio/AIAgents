"""
Gmail Solution Interfaces - Domain contracts for Gmail operations.

Defines the abstract interfaces that infrastructure adapters must implement
for Gmail cleanup functionality. Following Dependency Inversion Principle.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.domain.email_thread import EmailThread, EmailMessage


class IGmailClient(ABC):
    """
    Interface for Gmail API operations.
    
    This abstraction decouples the Gmail cleanup domain logic from
    the specific Gmail API implementation, enabling:
    - Testing with mock clients
    - Alternative email providers (Outlook, etc.)
    - Offline development and testing
    """

    @abstractmethod
    def list_threads(
        self,
        query: str = '',
        max_results: int = 100,
        label_ids: Optional[List[str]] = None,
    ) -> List[EmailThread]:
        """
        List email threads matching query.
        
        Args:
            query: Gmail search query (e.g., "is:unread older_than:30d")
            max_results: Maximum number of threads to return
            label_ids: Filter by label IDs (e.g., ["INBOX", "UNREAD"])
            
        Returns:
            List of EmailThread domain entities
            
        Raises:
            GmailAPIError: If API call fails
            AuthenticationError: If credentials are invalid
        """
        pass

    @abstractmethod
    def get_thread(self, thread_id: str) -> EmailThread:
        """
        Get a single thread with all messages.
        
        Args:
            thread_id: Gmail thread ID
            
        Returns:
            EmailThread with all messages loaded
            
        Raises:
            ThreadNotFoundError: If thread doesn't exist
            GmailAPIError: If API call fails
        """
        pass

    @abstractmethod
    def get_message(self, message_id: str) -> EmailMessage:
        """
        Get a single message by ID.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            EmailMessage domain entity
            
        Raises:
            MessageNotFoundError: If message doesn't exist
            GmailAPIError: If API call fails
        """
        pass

    @abstractmethod
    def modify_labels(
        self,
        message_id: str,
        add_labels: Optional[List[str]] = None,
        remove_labels: Optional[List[str]] = None,
    ) -> bool:
        """
        Modify labels on a message.
        
        Used for archive, mark read, apply categories, etc.
        
        Args:
            message_id: Gmail message ID
            add_labels: Labels to add (e.g., ["STARRED"])
            remove_labels: Labels to remove (e.g., ["INBOX", "UNREAD"])
            
        Returns:
            True if successful
            
        Raises:
            GmailAPIError: If operation fails
        """
        pass

    @abstractmethod
    def trash_message(self, message_id: str) -> bool:
        """
        Move message to trash.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            True if successful
            
        Raises:
            GmailAPIError: If operation fails
        """
        pass

    @abstractmethod
    def batch_modify_messages(
        self,
        message_ids: List[str],
        add_labels: Optional[List[str]] = None,
        remove_labels: Optional[List[str]] = None,
    ) -> Dict[str, int]:
        """
        Modify labels on multiple messages in a single API call.
        
        Significantly more efficient than individual modify_labels calls.
        
        Args:
            message_ids: List of Gmail message IDs (max 1000 per call)
            add_labels: Labels to add
            remove_labels: Labels to remove
            
        Returns:
            Dictionary with 'success' and 'failed' counts
            
        Raises:
            GmailAPIError: If operation fails
        """
        pass

    @abstractmethod
    def batch_archive_messages(self, message_ids: List[str]) -> Dict[str, int]:
        """
        Archive multiple messages (remove INBOX label).
        
        Args:
            message_ids: List of Gmail message IDs
            
        Returns:
            Dictionary with 'success' and 'failed' counts
        """
        pass

    @abstractmethod
    def batch_trash_messages(self, message_ids: List[str]) -> Dict[str, int]:
        """
        Move multiple messages to trash.
        
        Args:
            message_ids: List of Gmail message IDs
            
        Returns:
            Dictionary with 'success' and 'failed' counts
        """
        pass

    @abstractmethod
    def batch_mark_read(self, message_ids: List[str]) -> Dict[str, int]:
        """
        Mark multiple messages as read (remove UNREAD label).
        
        Args:
            message_ids: List of Gmail message IDs
            
        Returns:
            Dictionary with 'success' and 'failed' counts
        """
        pass

    @abstractmethod
    def get_labels(self) -> List[Dict[str, Any]]:
        """
        Get all available labels.
        
        Returns:
            List of label definitions with id, name, type
        """
        pass

    @abstractmethod
    def create_label(self, name: str) -> str:
        """
        Create a new label.
        
        Args:
            name: Label name
            
        Returns:
            Label ID
        """
        pass

    @abstractmethod
    def get_profile(self) -> Dict[str, Any]:
        """
        Get user's Gmail profile information.
        
        Returns:
            Profile with emailAddress, messagesTotal, threadsTotal
        """
        pass


class IGmailCleanupRepository(ABC):
    """
    Repository interface for Gmail cleanup run persistence.
    
    Stores cleanup execution history, metrics, and audit trails.
    """

    @abstractmethod
    async def save_cleanup_run(self, cleanup_run: Any) -> str:
        """
        Persist a cleanup run record.
        
        Args:
            cleanup_run: CleanupRun domain entity
            
        Returns:
            Run ID
        """
        pass

    @abstractmethod
    async def get_cleanup_run(self, run_id: str) -> Optional[Any]:
        """
        Retrieve a cleanup run by ID.
        
        Args:
            run_id: Cleanup run identifier
            
        Returns:
            CleanupRun or None if not found
        """
        pass

    @abstractmethod
    async def list_cleanup_runs(
        self,
        user_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Any]:
        """
        List cleanup runs with optional filtering.
        
        Args:
            user_id: Filter by user (optional)
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            List of CleanupRun entities
        """
        pass

    @abstractmethod
    async def get_cleanup_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get aggregated cleanup statistics for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Statistics dictionary with counts, totals, trends
        """
        pass


class IGmailObservability(ABC):
    """
    Observability interface for Gmail cleanup operations.
    
    Provides structured logging, metrics, and tracing specific
    to Gmail cleanup workflows.
    """

    @abstractmethod
    def log_cleanup_started(
        self,
        run_id: str,
        user_id: str,
        policy_id: str,
        dry_run: bool,
    ) -> None:
        """Log cleanup operation start."""
        pass

    @abstractmethod
    def log_cleanup_completed(
        self,
        run_id: str,
        duration_seconds: float,
        actions_performed: int,
        errors: int,
    ) -> None:
        """Log cleanup operation completion."""
        pass

    @abstractmethod
    def log_cleanup_error(
        self,
        run_id: str,
        error_type: str,
        error_message: str,
    ) -> None:
        """Log cleanup operation error."""
        pass

    @abstractmethod
    def record_emails_processed(
        self,
        count: int,
        user_id: str,
        action_type: str,
    ) -> None:
        """Record number of emails processed."""
        pass

    @abstractmethod
    def record_cleanup_duration(
        self,
        duration_seconds: float,
        user_id: str,
        status: str,
    ) -> None:
        """Record cleanup operation duration."""
        pass

    @abstractmethod
    def increment_error_count(
        self,
        error_type: str,
        user_id: str,
    ) -> None:
        """Increment error counter."""
        pass
