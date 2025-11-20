"""
Domain Exceptions - Business logic errors.

Custom exceptions that represent domain-specific error conditions.
These are caught and handled by the application layer.
"""


class DomainError(Exception):
    """Base exception for all domain errors."""

    pass


class AgentError(DomainError):
    """Base exception for agent-related errors."""

    pass


class AgentNotFoundError(AgentError):
    """Raised when an agent cannot be found."""

    def __init__(self, agent_id: str):
        super().__init__(f"Agent not found: {agent_id}")
        self.agent_id = agent_id


class AgentExecutionError(AgentError):
    """Raised when agent execution fails."""

    def __init__(self, agent_id: str, reason: str):
        super().__init__(f"Agent {agent_id} execution failed: {reason}")
        self.agent_id = agent_id
        self.reason = reason


class AgentTimeoutError(AgentError):
    """Raised when agent execution exceeds timeout."""

    def __init__(self, agent_id: str, timeout_seconds: int):
        super().__init__(f"Agent {agent_id} timed out after {timeout_seconds}s")
        self.agent_id = agent_id
        self.timeout_seconds = timeout_seconds


class InvalidAgentStateError(AgentError):
    """Raised when an operation is invalid for the current agent state."""

    def __init__(self, agent_id: str, current_state: str, operation: str):
        super().__init__(
            f"Cannot perform {operation} on agent {agent_id} in state {current_state}"
        )
        self.agent_id = agent_id
        self.current_state = current_state
        self.operation = operation


class ToolError(DomainError):
    """Base exception for tool-related errors."""

    pass


class ToolNotFoundError(ToolError):
    """Raised when a tool cannot be found."""

    def __init__(self, tool_name: str):
        super().__init__(f"Tool not found: {tool_name}")
        self.tool_name = tool_name


class ToolExecutionError(ToolError):
    """Raised when tool execution fails."""

    def __init__(self, tool_name: str, reason: str):
        super().__init__(f"Tool {tool_name} execution failed: {reason}")
        self.tool_name = tool_name
        self.reason = reason


class ToolPermissionError(ToolError):
    """Raised when an agent lacks permission to use a tool."""

    def __init__(self, tool_name: str, agent_id: str, required_capability: str):
        super().__init__(
            f"Agent {agent_id} lacks {required_capability} capability to use {tool_name}"
        )
        self.tool_name = tool_name
        self.agent_id = agent_id
        self.required_capability = required_capability


class LLMProviderError(DomainError):
    """Base exception for LLM provider errors."""

    pass


class RateLimitError(LLMProviderError):
    """Raised when rate limit is exceeded."""

    def __init__(self, provider: str, retry_after: int):
        super().__init__(f"{provider} rate limit exceeded. Retry after {retry_after}s")
        self.provider = provider
        self.retry_after = retry_after


class InvalidModelError(LLMProviderError):
    """Raised when an invalid model is specified."""

    def __init__(self, provider: str, model: str):
        super().__init__(f"Invalid model {model} for provider {provider}")
        self.provider = provider
        self.model = model


class VectorStoreError(DomainError):
    """Base exception for vector store errors."""

    pass


class CollectionNotFoundError(VectorStoreError):
    """Raised when a collection cannot be found."""

    def __init__(self, collection_name: str):
        super().__init__(f"Collection not found: {collection_name}")
        self.collection_name = collection_name


class MessageQueueError(DomainError):
    """Base exception for message queue errors."""

    pass


class ValidationError(DomainError):
    """Raised when domain validation fails."""

    pass
