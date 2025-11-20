"""
Unit tests for domain models.

Tests core business logic and validation.
"""

import pytest
from uuid import UUID

from src.domain.models import (
    Agent,
    AgentCapability,
    AgentStatus,
    Message,
    MessageRole,
    Tool,
    ToolParameter,
)


@pytest.mark.unit
class TestMessage:
    """Test Message model."""

    def test_create_message(self):
        """Test creating a valid message."""
        msg = Message(
            role=MessageRole.USER,
            content="Hello world",
        )
        
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello world"
        assert isinstance(msg.id, UUID)
        assert msg.metadata == {}

    def test_message_immutable(self):
        """Test that messages are immutable."""
        msg = Message(role=MessageRole.USER, content="Test")
        
        with pytest.raises(Exception):  # Pydantic ValidationError
            msg.content = "Modified"

    def test_empty_content_validation(self):
        """Test that empty content is rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            Message(role=MessageRole.USER, content="")

    def test_whitespace_only_content(self):
        """Test that whitespace-only content is rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            Message(role=MessageRole.USER, content="   ")


@pytest.mark.unit
class TestAgent:
    """Test Agent model."""

    def test_create_agent(self):
        """Test creating a valid agent."""
        agent = Agent(
            name="test_agent",
            description="Test agent",
            system_prompt="You are helpful",
            model_provider="openai",
            model_name="gpt-4",
        )
        
        assert agent.name == "test_agent"
        assert agent.status == AgentStatus.IDLE
        assert isinstance(agent.id, UUID)
        assert len(agent.conversation_history) == 0

    def test_agent_name_validation(self):
        """Test agent name cannot be empty."""
        with pytest.raises(ValueError, match="cannot be empty"):
            Agent(
                name="",
                description="Test",
                system_prompt="Test",
                model_provider="openai",
                model_name="gpt-4",
            )

    def test_add_message_to_history(self, sample_agent, sample_message):
        """Test adding messages to conversation history."""
        initial_count = len(sample_agent.conversation_history)
        
        sample_agent.add_message(sample_message)
        
        assert len(sample_agent.conversation_history) == initial_count + 1
        assert sample_agent.conversation_history[-1] == sample_message

    def test_update_status(self, sample_agent):
        """Test updating agent status."""
        initial_time = sample_agent.updated_at
        
        sample_agent.update_status(AgentStatus.RUNNING)
        
        assert sample_agent.status == AgentStatus.RUNNING
        assert sample_agent.updated_at > initial_time

    def test_temperature_validation(self):
        """Test temperature must be in valid range."""
        with pytest.raises(ValueError):
            Agent(
                name="test",
                description="Test",
                system_prompt="Test",
                model_provider="openai",
                model_name="gpt-4",
                temperature=3.0,  # Too high
            )

    def test_max_tokens_validation(self):
        """Test max_tokens must be positive."""
        with pytest.raises(ValueError):
            Agent(
                name="test",
                description="Test",
                system_prompt="Test",
                model_provider="openai",
                model_name="gpt-4",
                max_tokens=-100,
            )


@pytest.mark.unit
class TestTool:
    """Test Tool model."""

    def test_create_tool(self):
        """Test creating a valid tool."""
        tool = Tool(
            name="test_tool",
            description="A test tool",
            handler_module="test_module",
            handler_function="test_func",
        )
        
        assert tool.name == "test_tool"
        assert isinstance(tool.id, UUID)

    def test_tool_name_must_be_identifier(self):
        """Test tool name must be a valid Python identifier."""
        with pytest.raises(ValueError, match="valid Python identifier"):
            Tool(
                name="invalid-name",  # Hyphens not allowed
                description="Test",
                handler_module="test",
                handler_function="func",
            )

    def test_to_llm_schema(self):
        """Test converting tool to LLM schema format."""
        tool = Tool(
            name="test_tool",
            description="A test tool",
            parameters=[
                ToolParameter(
                    name="arg1",
                    type="string",
                    description="First argument",
                    required=True,
                ),
                ToolParameter(
                    name="arg2",
                    type="integer",
                    description="Second argument",
                    required=False,
                ),
            ],
            handler_module="test",
            handler_function="func",
        )
        
        schema = tool.to_llm_schema()
        
        assert schema["name"] == "test_tool"
        assert schema["description"] == "A test tool"
        assert "parameters" in schema
        assert "arg1" in schema["parameters"]["properties"]
        assert "arg1" in schema["parameters"]["required"]
        assert "arg2" not in schema["parameters"]["required"]
