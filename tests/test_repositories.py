"""
Unit tests for repositories.

Tests data access layer logic.
"""

import pytest
from uuid import uuid4

from src.domain.exceptions import AgentNotFoundError
from src.domain.models import Agent, AgentStatus


@pytest.mark.unit
class TestInMemoryAgentRepository:
    """Test InMemoryAgentRepository."""

    @pytest.mark.asyncio
    async def test_save_and_get_by_id(self, agent_repository, sample_agent):
        """Test saving and retrieving an agent by ID."""
        await agent_repository.save(sample_agent)
        
        retrieved = await agent_repository.get_by_id(sample_agent.id)
        
        assert retrieved is not None
        assert retrieved.id == sample_agent.id
        assert retrieved.name == sample_agent.name

    @pytest.mark.asyncio
    async def test_get_by_name(self, agent_repository, sample_agent):
        """Test retrieving an agent by name."""
        await agent_repository.save(sample_agent)
        
        retrieved = await agent_repository.get_by_name(sample_agent.name)
        
        assert retrieved is not None
        assert retrieved.name == sample_agent.name

    @pytest.mark.asyncio
    async def test_get_nonexistent_agent(self, agent_repository):
        """Test getting a nonexistent agent returns None."""
        result = await agent_repository.get_by_id(uuid4())
        
        assert result is None

    @pytest.mark.asyncio
    async def test_list_all(self, agent_repository, sample_agent):
        """Test listing all agents."""
        # Save multiple agents
        await agent_repository.save(sample_agent)
        
        agent2 = Agent(
            name="agent2",
            description="Second agent",
            system_prompt="Test",
            model_provider="openai",
            model_name="gpt-4",
        )
        await agent_repository.save(agent2)
        
        agents = await agent_repository.list_all()
        
        assert len(agents) == 2

    @pytest.mark.asyncio
    async def test_list_with_pagination(self, agent_repository, sample_agent):
        """Test pagination in list_all."""
        # Save multiple agents
        for i in range(5):
            agent = Agent(
                name=f"agent_{i}",
                description="Test",
                system_prompt="Test",
                model_provider="openai",
                model_name="gpt-4",
            )
            await agent_repository.save(agent)
        
        # Get first page
        page1 = await agent_repository.list_all(limit=2, offset=0)
        assert len(page1) == 2
        
        # Get second page
        page2 = await agent_repository.list_all(limit=2, offset=2)
        assert len(page2) == 2
        
        # Ensure different results
        assert page1[0].id != page2[0].id

    @pytest.mark.asyncio
    async def test_delete(self, agent_repository, sample_agent):
        """Test deleting an agent."""
        await agent_repository.save(sample_agent)
        
        # Verify it exists
        assert await agent_repository.get_by_id(sample_agent.id) is not None
        
        # Delete
        await agent_repository.delete(sample_agent.id)
        
        # Verify it's gone
        assert await agent_repository.get_by_id(sample_agent.id) is None

    @pytest.mark.asyncio
    async def test_update_status(self, agent_repository, sample_agent):
        """Test updating agent status."""
        await agent_repository.save(sample_agent)
        
        await agent_repository.update_status(
            sample_agent.id,
            AgentStatus.RUNNING.value,
        )
        
        retrieved = await agent_repository.get_by_id(sample_agent.id)
        assert retrieved.status == AgentStatus.RUNNING

    @pytest.mark.asyncio
    async def test_update_status_nonexistent(self, agent_repository):
        """Test updating status of nonexistent agent raises error."""
        with pytest.raises(AgentNotFoundError):
            await agent_repository.update_status(
                uuid4(),
                AgentStatus.RUNNING.value,
            )


@pytest.mark.unit
class TestInMemoryToolRegistry:
    """Test InMemoryToolRegistry."""

    def test_register_and_get_tool(self, tool_registry, sample_tool):
        """Test registering and retrieving a tool."""
        tool_registry.register_tool(sample_tool)
        
        retrieved = tool_registry.get_tool(sample_tool.name)
        
        assert retrieved is not None
        assert retrieved.name == sample_tool.name

    def test_get_nonexistent_tool(self, tool_registry):
        """Test getting a nonexistent tool returns None."""
        result = tool_registry.get_tool("nonexistent")
        
        assert result is None

    def test_list_all_tools(self, tool_registry, sample_tool):
        """Test listing all tools."""
        tool_registry.register_tool(sample_tool)
        
        tools = tool_registry.list_all_tools()
        
        assert len(tools) == 1
        assert tools[0].name == sample_tool.name

    def test_get_tools_by_capability(self, tool_registry, sample_tool):
        """Test filtering tools by capability."""
        tool_registry.register_tool(sample_tool)
        
        from src.domain.models import AgentCapability
        
        tools = tool_registry.get_tools_by_capability(
            AgentCapability.WEB_SEARCH.value
        )
        
        assert len(tools) == 1
        assert tools[0].name == sample_tool.name
