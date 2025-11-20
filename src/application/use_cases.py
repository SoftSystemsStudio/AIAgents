"""
Use Cases - Application-specific business workflows.

Each use case represents a specific user action or business process.
"""

from typing import Dict, Optional
from uuid import UUID

from src.domain.exceptions import AgentNotFoundError
from src.domain.interfaces import IAgentRepository, ILLMProvider, IObservabilityService, IToolRegistry
from src.domain.models import Agent, AgentCapability, ExecutionResult
from src.application.orchestrator import AgentOrchestrator


class CreateAgentUseCase:
    """
    Use case for creating a new agent.
    
    Validates configuration and persists the agent.
    """

    def __init__(self, agent_repository: IAgentRepository):
        self.agent_repository = agent_repository

    async def execute(
        self,
        name: str,
        description: str,
        system_prompt: str,
        model_provider: str,
        model_name: str,
        capabilities: list[AgentCapability] = None,
        allowed_tools: list[str] = None,
        **kwargs,
    ) -> Agent:
        """
        Create and persist a new agent.
        
        Args:
            name: Agent name
            description: Agent description
            system_prompt: System prompt defining agent behavior
            model_provider: LLM provider (openai, anthropic)
            model_name: Model identifier
            capabilities: List of capabilities to grant
            allowed_tools: List of tool names the agent can use
            **kwargs: Additional agent configuration
            
        Returns:
            Created agent
        """
        # Check if agent name already exists
        existing = await self.agent_repository.get_by_name(name)
        if existing:
            raise ValueError(f"Agent with name '{name}' already exists")

        # Create agent
        agent = Agent(
            name=name,
            description=description,
            system_prompt=system_prompt,
            model_provider=model_provider,
            model_name=model_name,
            capabilities=capabilities or [],
            allowed_tools=allowed_tools or [],
            **kwargs,
        )

        # Persist
        await self.agent_repository.save(agent)

        return agent


class ExecuteAgentUseCase:
    """
    Use case for executing an agent.
    
    Orchestrates agent execution and returns results.
    """

    def __init__(
        self,
        agent_repository: IAgentRepository,
        orchestrator: AgentOrchestrator,
    ):
        self.agent_repository = agent_repository
        self.orchestrator = orchestrator

    async def execute(
        self,
        agent_id: UUID,
        user_input: str,
        context: Optional[Dict] = None,
    ) -> ExecutionResult:
        """
        Execute an agent with user input.
        
        Args:
            agent_id: ID of agent to execute
            user_input: User's input message
            context: Optional context dictionary
            
        Returns:
            Execution result with output and metrics
            
        Raises:
            AgentNotFoundError: If agent doesn't exist
        """
        # Load agent
        agent = await self.agent_repository.get_by_id(agent_id)
        if not agent:
            raise AgentNotFoundError(str(agent_id))

        # Execute via orchestrator
        result = await self.orchestrator.execute_agent(
            agent=agent,
            user_input=user_input,
            context=context,
        )

        return result


class GetAgentUseCase:
    """Use case for retrieving an agent."""

    def __init__(self, agent_repository: IAgentRepository):
        self.agent_repository = agent_repository

    async def execute_by_id(self, agent_id: UUID) -> Agent:
        """Get agent by ID."""
        agent = await self.agent_repository.get_by_id(agent_id)
        if not agent:
            raise AgentNotFoundError(str(agent_id))
        return agent

    async def execute_by_name(self, name: str) -> Agent:
        """Get agent by name."""
        agent = await self.agent_repository.get_by_name(name)
        if not agent:
            raise AgentNotFoundError(name)
        return agent


class ListAgentsUseCase:
    """Use case for listing agents."""

    def __init__(self, agent_repository: IAgentRepository):
        self.agent_repository = agent_repository

    async def execute(self, limit: int = 100, offset: int = 0) -> list[Agent]:
        """List all agents with pagination."""
        return await self.agent_repository.list_all(limit=limit, offset=offset)


class DeleteAgentUseCase:
    """Use case for deleting an agent."""

    def __init__(self, agent_repository: IAgentRepository):
        self.agent_repository = agent_repository

    async def execute(self, agent_id: UUID) -> None:
        """
        Delete an agent.
        
        Args:
            agent_id: ID of agent to delete
            
        Raises:
            AgentNotFoundError: If agent doesn't exist
        """
        agent = await self.agent_repository.get_by_id(agent_id)
        if not agent:
            raise AgentNotFoundError(str(agent_id))

        await self.agent_repository.delete(agent_id)
