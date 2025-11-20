"""
Test fixtures and utilities.

Provides reusable fixtures for testing.
"""

import pytest
from uuid import uuid4

from src.domain.models import (
    Agent,
    AgentCapability,
    AgentStatus,
    Message,
    MessageRole,
    Tool,
    ToolParameter,
)
from src.infrastructure.repositories import InMemoryAgentRepository, InMemoryToolRegistry
from src.infrastructure.observability import StructuredLogger


@pytest.fixture
def sample_agent() -> Agent:
    """Create a sample agent for testing."""
    return Agent(
        name="test_agent",
        description="A test agent",
        system_prompt="You are a helpful test assistant.",
        model_provider="openai",
        model_name="gpt-4",
        temperature=0.7,
        max_tokens=1000,
        capabilities=[AgentCapability.WEB_SEARCH],
        allowed_tools=["search_web"],
        max_iterations=5,
        timeout_seconds=60,
    )


@pytest.fixture
def sample_message() -> Message:
    """Create a sample message for testing."""
    return Message(
        role=MessageRole.USER,
        content="Hello, how are you?",
    )


@pytest.fixture
def sample_tool() -> Tool:
    """Create a sample tool for testing."""
    return Tool(
        name="search_web",
        description="Search the web for information",
        parameters=[
            ToolParameter(
                name="query",
                type="string",
                description="Search query",
                required=True,
            ),
            ToolParameter(
                name="num_results",
                type="integer",
                description="Number of results to return",
                required=False,
                default=5,
            ),
        ],
        required_capability=AgentCapability.WEB_SEARCH,
        handler_module="tests.mock_tools",
        handler_function="mock_search_web",
    )


@pytest.fixture
def agent_repository() -> InMemoryAgentRepository:
    """Create an in-memory agent repository."""
    return InMemoryAgentRepository()


@pytest.fixture
def tool_registry() -> InMemoryToolRegistry:
    """Create an in-memory tool registry."""
    return InMemoryToolRegistry()


@pytest.fixture
def observability() -> StructuredLogger:
    """Create an observability service."""
    return StructuredLogger(log_level="DEBUG")


@pytest.fixture
async def populated_agent_repository(
    agent_repository: InMemoryAgentRepository,
    sample_agent: Agent,
) -> InMemoryAgentRepository:
    """Create a repository with a sample agent."""
    await agent_repository.save(sample_agent)
    return agent_repository


@pytest.fixture
def populated_tool_registry(
    tool_registry: InMemoryToolRegistry,
    sample_tool: Tool,
) -> InMemoryToolRegistry:
    """Create a tool registry with a sample tool."""
    tool_registry.register_tool(sample_tool)
    return tool_registry
