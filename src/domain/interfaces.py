"""
Domain Service Interfaces - Abstract contracts for services.

These interfaces define the contracts that must be implemented by infrastructure
adapters. Following the Dependency Inversion Principle from SOLID.
"""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional
from uuid import UUID

from .models import Agent, ExecutionResult, Message, Tool


class ILLMProvider(ABC):
    """
    Interface for LLM providers (OpenAI, Anthropic, etc.).
    
    This abstraction decouples the domain from specific LLM implementations,
    allowing easy swapping of providers without changing business logic.
    
    TODO: Add batch processing for multiple prompts
    """

    @abstractmethod
    async def generate_completion(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Message:
        """
        Generate a completion from the LLM.
        
        Args:
            messages: Conversation history
            model: Model identifier (e.g., "gpt-4", "claude-3-opus")
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            tools: Available tools in LLM schema format
            
        Returns:
            Generated message from the LLM
            
        Raises:
            LLMProviderError: If the API call fails
            RateLimitError: If rate limit is exceeded
        """
        pass

    @abstractmethod
    def stream_completion(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> AsyncIterator[str]:
        """
        Stream a completion from the LLM with real-time token delivery.
        
        Args:
            messages: Conversation history
            model: Model identifier
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            tools: Available tools in LLM schema format
            
        Yields:
            Tokens as they arrive from the LLM
            
        Raises:
            LLMProviderError: If the API call fails
            RateLimitError: If rate limit is exceeded
            
        Note:
            Tool calls are not supported in streaming mode.
        """
        pass

    @abstractmethod
    async def get_embedding(self, text: str, model: str = "default") -> List[float]:
        """
        Generate an embedding vector for the given text.
        
        Args:
            text: Input text to embed
            model: Embedding model identifier
            
        Returns:
            Embedding vector
        """
        pass

    @abstractmethod
    def get_token_count(self, text: str, model: str) -> int:
        """
        Count tokens in text for the given model.
        
        Important for cost estimation and context window management.
        """
        pass


class IVectorStore(ABC):
    """
    Interface for vector database operations.
    
    Provides semantic search capabilities for RAG (Retrieval-Augmented Generation).
    
    RISK: Vector stores can become bottlenecks at scale. Consider:
    - Connection pooling
    - Caching frequently accessed vectors
    - Sharding strategies for large collections
    """

    @abstractmethod
    async def create_collection(
        self,
        name: str,
        dimension: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Create a new vector collection."""
        pass

    @abstractmethod
    async def insert_vectors(
        self,
        collection: str,
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Insert vectors with associated metadata.
        
        Returns:
            List of vector IDs
        """
        pass

    @abstractmethod
    async def search(
        self,
        collection: str,
        query_vector: List[float],
        limit: int = 10,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for similar vectors.
        
        Returns:
            List of results with scores and payloads
        """
        pass

    @abstractmethod
    async def delete_collection(self, name: str) -> None:
        """Delete a vector collection."""
        pass


class IMessageQueue(ABC):
    """
    Interface for asynchronous message passing.
    
    Enables:
    - Agent-to-agent communication
    - Event-driven workflows
    - Task queuing and distribution
    
    TODO: Add dead letter queue support
    TODO: Add message priority levels
    """

    @abstractmethod
    async def publish(
        self,
        topic: str,
        message: Dict[str, Any],
        priority: int = 0,
    ) -> str:
        """
        Publish a message to a topic.
        
        Returns:
            Message ID
        """
        pass

    @abstractmethod
    async def subscribe(
        self,
        topic: str,
        callback: Any,  # Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> str:
        """
        Subscribe to a topic with a callback.
        
        Returns:
            Subscription ID
        """
        pass

    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from a topic."""
        pass

    @abstractmethod
    async def get_message(
        self,
        topic: str,
        timeout: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get a message from a topic (blocking).
        
        Returns:
            Message or None if timeout
        """
        pass


class IAgentRepository(ABC):
    """
    Repository interface for agent persistence.
    
    Following the Repository pattern to abstract data access.
    """

    @abstractmethod
    async def save(self, agent: Agent) -> None:
        """Persist an agent."""
        pass

    @abstractmethod
    async def get_by_id(self, agent_id: UUID) -> Optional[Agent]:
        """Retrieve an agent by ID."""
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Agent]:
        """Retrieve an agent by name."""
        pass

    @abstractmethod
    async def list_all(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Agent]:
        """List all agents with pagination."""
        pass

    @abstractmethod
    async def delete(self, agent_id: UUID) -> None:
        """Delete an agent."""
        pass

    @abstractmethod
    async def update_status(self, agent_id: UUID, status: str) -> None:
        """Update agent status efficiently without loading full entity."""
        pass


class IToolRegistry(ABC):
    """
    Registry interface for managing available tools.
    
    Tools are registered at startup and can be looked up by name
    or capability.
    """

    @abstractmethod
    def register_tool(self, tool: Tool) -> None:
        """Register a tool in the registry."""
        pass

    @abstractmethod
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        pass

    @abstractmethod
    def get_tools_by_capability(self, capability: str) -> List[Tool]:
        """Get all tools requiring a specific capability."""
        pass

    @abstractmethod
    def list_all_tools(self) -> List[Tool]:
        """List all registered tools."""
        pass

    @abstractmethod
    async def invoke_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Invoke a tool with parameters.
        
        Returns:
            Tool execution result
            
        Raises:
            ToolNotFoundError: If tool doesn't exist
            ToolExecutionError: If tool execution fails
        """
        pass


class IObservabilityService(ABC):
    """
    Interface for observability (logging, tracing, metrics).
    
    Provides structured logging, distributed tracing, and metrics
    without coupling to specific implementations (DataDog, New Relic, etc.).
    
    TODO: Add alerting interface
    """

    @abstractmethod
    def log(
        self,
        level: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Structured logging."""
        pass

    @abstractmethod
    def start_span(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> Any:
        """Start a distributed trace span."""
        pass

    @abstractmethod
    def record_metric(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record a metric value."""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of observability systems.
        
        Returns:
            Health status and details
        """
        pass
