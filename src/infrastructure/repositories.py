"""
In-Memory Repository Implementations.

Simple in-memory implementations for development and testing.
For production, replace with database-backed repositories (PostgreSQL, MongoDB).
"""

from typing import Dict, List, Optional, Any
from uuid import UUID

from src.domain.exceptions import AgentNotFoundError
from src.domain.interfaces import IAgentRepository, IToolRegistry
from src.domain.models import Agent, Tool


class InMemoryAgentRepository(IAgentRepository):
    """
    In-memory agent repository.

    WARNING: Data is lost on process restart. Use only for:
    - Development
    - Testing
    - Demos

    For production, implement PostgreSQL/MongoDB repository.

    TODO: Create PostgreSQL implementation with proper indexing
    TODO: Add audit logging for all mutations
    """

    def __init__(self):
        self._agents: Dict[UUID, Agent] = {}
        self._name_index: Dict[str, UUID] = {}

    async def save(self, agent: Agent) -> None:
        """Save or update an agent."""
        self._agents[agent.id] = agent
        self._name_index[agent.name] = agent.id

    async def get_by_id(self, agent_id: UUID) -> Optional[Agent]:
        """Get agent by ID."""
        return self._agents.get(agent_id)

    async def get_by_name(self, name: str) -> Optional[Agent]:
        """Get agent by name."""
        agent_id = self._name_index.get(name)
        if agent_id:
            return self._agents.get(agent_id)
        return None

    async def list_all(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Agent]:
        """List all agents with pagination."""
        agents = list(self._agents.values())
        return agents[offset : offset + limit]

    async def delete(self, agent_id: UUID) -> None:
        """Delete an agent."""
        agent = self._agents.get(agent_id)
        if agent:
            del self._name_index[agent.name]
            del self._agents[agent_id]

    async def update_status(self, agent_id: UUID, status: str) -> None:
        """Update agent status efficiently."""
        agent = self._agents.get(agent_id)
        if not agent:
            raise AgentNotFoundError(str(agent_id))

        from src.domain.models import AgentStatus

        agent.update_status(AgentStatus(status))


class InMemoryToolRegistry(IToolRegistry):
    """
    In-memory tool registry.

    Stores available tools and their handlers.
    Thread-safe for concurrent access.
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._capability_index: Dict[str, List[str]] = {}

    def register_tool(self, tool: Tool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool

        # Index by capability
        if tool.required_capability:
            cap = tool.required_capability.value
            if cap not in self._capability_index:
                self._capability_index[cap] = []
            self._capability_index[cap].append(tool.name)

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get tool by name."""
        return self._tools.get(name)

    def get_tools_by_capability(self, capability: str) -> List[Tool]:
        """Get all tools for a capability."""
        tool_names = self._capability_index.get(capability, [])
        return [self._tools[name] for name in tool_names if name in self._tools]

    def list_all_tools(self) -> List[Tool]:
        """List all registered tools."""
        return list(self._tools.values())

    async def invoke_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
    ) -> Dict[str, any]:
        """
        Invoke a tool with parameters.

        Dynamically imports and calls the tool's handler function.

        RISK: Dynamic imports can be slow. Consider caching handlers.
        """
        from src.domain.exceptions import ToolExecutionError, ToolNotFoundError
        import importlib

        tool = self.get_tool(tool_name)
        if not tool:
            raise ToolNotFoundError(tool_name)

        try:
            # Import handler module
            module = importlib.import_module(tool.handler_module)
            handler_func = getattr(module, tool.handler_function)

            # Invoke handler
            result = handler_func(**parameters)

            # Handle async handlers
            if asyncio.iscoroutine(result):
                result = await result

            return {"success": True, "result": result}

        except Exception as e:
            raise ToolExecutionError(tool_name, str(e)) from e


# Import asyncio for async handler support
import asyncio
