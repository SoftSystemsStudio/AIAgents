"""
REST API Layer - FastAPI application for the AI Agents platform.

Provides HTTP endpoints for:
- Agent management (CRUD)
- Agent execution
- Tool management
- Health checks and metrics
"""

from contextlib import asynccontextmanager
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.config import get_config
from src.domain.models import Agent, AgentCapability, AgentStatus, ExecutionResult
from src.domain.exceptions import AgentNotFoundError, AgentExecutionError
from src.infrastructure.llm_providers import OpenAIProvider
from src.infrastructure.repositories import InMemoryAgentRepository, InMemoryToolRegistry
from src.infrastructure.observability import StructuredLogger, PrometheusObservability
from src.application.orchestrator import AgentOrchestrator
from src.application.use_cases import (
    CreateAgentUseCase,
    ExecuteAgentUseCase,
    GetAgentUseCase,
    ListAgentsUseCase,
    DeleteAgentUseCase,
)


# Global dependencies (initialized in lifespan)
_dependencies = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Initializes dependencies on startup and cleans up on shutdown.
    """
    # Startup
    config = get_config()
    
    # Initialize observability
    if config.observability.enable_metrics:
        observability = PrometheusObservability(
            log_level=config.observability.log_level,
            metrics_port=config.observability.metrics_port,
        )
    else:
        observability = StructuredLogger(log_level=config.observability.log_level)
    
    observability.log("info", "Starting AI Agents API server", {"env": config.app_env})
    
    # Initialize LLM provider
    if config.llm.openai_api_key:
        llm_provider = OpenAIProvider(api_key=config.llm.openai_api_key)
    else:
        raise ValueError("No LLM provider API key configured")
    
    # Initialize repositories
    agent_repo = InMemoryAgentRepository()
    tool_registry = InMemoryToolRegistry()
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(
        llm_provider=llm_provider,
        tool_registry=tool_registry,
        agent_repository=agent_repo,
        observability=observability,
    )
    
    # Store in global dependencies
    _dependencies.update({
        "config": config,
        "observability": observability,
        "llm_provider": llm_provider,
        "agent_repo": agent_repo,
        "tool_registry": tool_registry,
        "orchestrator": orchestrator,
    })
    
    observability.log("info", "API server initialized successfully")
    
    yield
    
    # Shutdown
    observability.log("info", "Shutting down API server")


# Create FastAPI app
app = FastAPI(
    title="AI Agents Platform API",
    description="Production-grade AI agents with clean architecture",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models

class CreateAgentRequest(BaseModel):
    """Request model for creating an agent."""
    
    name: str = Field(..., description="Unique agent name")
    description: str = Field(..., description="Agent description")
    system_prompt: str = Field(..., description="System prompt defining agent behavior")
    model_provider: str = Field(..., description="LLM provider (openai, anthropic)")
    model_name: str = Field(..., description="Model identifier (e.g., gpt-4)")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(4000, gt=0, description="Maximum tokens per response")
    capabilities: List[AgentCapability] = Field(default_factory=list)
    allowed_tools: List[str] = Field(default_factory=list)
    max_iterations: int = Field(10, gt=0, description="Maximum execution iterations")
    timeout_seconds: int = Field(300, gt=0, description="Execution timeout")


class AgentResponse(BaseModel):
    """Response model for agent data."""
    
    id: UUID
    name: str
    description: str
    model_provider: str
    model_name: str
    status: AgentStatus
    capabilities: List[AgentCapability]
    allowed_tools: List[str]
    created_at: str
    updated_at: str


class ExecuteAgentRequest(BaseModel):
    """Request model for agent execution."""
    
    user_input: str = Field(..., description="User input message")
    stream: bool = Field(False, description="Stream response in real-time")


class ExecutionResultResponse(BaseModel):
    """Response model for execution results."""
    
    agent_id: UUID
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    duration_seconds: float
    iterations: int
    estimated_cost: float
    final_status: AgentStatus


class HealthResponse(BaseModel):
    """Response model for health checks."""
    
    status: str
    version: str
    environment: str
    services: dict


# API Endpoints

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AI Agents Platform API",
        "version": "0.1.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Verifies that all critical services are operational.
    """
    config = _dependencies["config"]
    observability = _dependencies["observability"]
    
    # Check observability health
    obs_health = await observability.health_check()
    
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        environment=config.app_env,
        services={
            "observability": obs_health,
            "llm_provider": "operational",
            "agent_repository": "operational",
        },
    )


@app.post("/agents", response_model=AgentResponse, status_code=status.HTTP_201_CREATED, tags=["Agents"])
async def create_agent(request: CreateAgentRequest):
    """
    Create a new agent.
    
    Creates and persists a new AI agent with the specified configuration.
    """
    agent_repo = _dependencies["agent_repo"]
    observability = _dependencies["observability"]
    
    observability.log("info", "Creating new agent", {"name": request.name})
    
    try:
        use_case = CreateAgentUseCase(agent_repo)
        agent = await use_case.execute(
            name=request.name,
            description=request.description,
            system_prompt=request.system_prompt,
            model_provider=request.model_provider,
            model_name=request.model_name,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            capabilities=request.capabilities,
            allowed_tools=request.allowed_tools,
            max_iterations=request.max_iterations,
            timeout_seconds=request.timeout_seconds,
        )
        
        observability.log("info", "Agent created successfully", {"agent_id": str(agent.id)})
        
        return AgentResponse(
            id=agent.id,
            name=agent.name,
            description=agent.description,
            model_provider=agent.model_provider,
            model_name=agent.model_name,
            status=agent.status,
            capabilities=agent.capabilities,
            allowed_tools=agent.allowed_tools,
            created_at=agent.created_at.isoformat(),
            updated_at=agent.updated_at.isoformat(),
        )
        
    except ValueError as e:
        observability.log("error", "Agent creation failed", {"error": str(e)})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        observability.log("error", "Unexpected error creating agent", {"error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@app.get("/agents", response_model=List[AgentResponse], tags=["Agents"])
async def list_agents(limit: int = 100, offset: int = 0):
    """
    List all agents with pagination.
    
    Returns a paginated list of all agents in the system.
    """
    agent_repo = _dependencies["agent_repo"]
    
    use_case = ListAgentsUseCase(agent_repo)
    agents = await use_case.execute(limit=limit, offset=offset)
    
    return [
        AgentResponse(
            id=agent.id,
            name=agent.name,
            description=agent.description,
            model_provider=agent.model_provider,
            model_name=agent.model_name,
            status=agent.status,
            capabilities=agent.capabilities,
            allowed_tools=agent.allowed_tools,
            created_at=agent.created_at.isoformat(),
            updated_at=agent.updated_at.isoformat(),
        )
        for agent in agents
    ]


@app.get("/agents/{agent_id}", response_model=AgentResponse, tags=["Agents"])
async def get_agent(agent_id: UUID):
    """
    Get an agent by ID.
    
    Retrieves detailed information about a specific agent.
    """
    agent_repo = _dependencies["agent_repo"]
    
    try:
        use_case = GetAgentUseCase(agent_repo)
        agent = await use_case.execute_by_id(agent_id)
        
        return AgentResponse(
            id=agent.id,
            name=agent.name,
            description=agent.description,
            model_provider=agent.model_provider,
            model_name=agent.model_name,
            status=agent.status,
            capabilities=agent.capabilities,
            allowed_tools=agent.allowed_tools,
            created_at=agent.created_at.isoformat(),
            updated_at=agent.updated_at.isoformat(),
        )
        
    except AgentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent {agent_id} not found")


@app.delete("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Agents"])
async def delete_agent(agent_id: UUID):
    """
    Delete an agent.
    
    Permanently removes an agent from the system.
    """
    agent_repo = _dependencies["agent_repo"]
    observability = _dependencies["observability"]
    
    try:
        use_case = DeleteAgentUseCase(agent_repo)
        await use_case.execute(agent_id)
        
        observability.log("info", "Agent deleted", {"agent_id": str(agent_id)})
        
    except AgentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent {agent_id} not found")


@app.post("/agents/{agent_id}/execute", response_model=ExecutionResultResponse, tags=["Execution"])
async def execute_agent(agent_id: UUID, request: ExecuteAgentRequest, background_tasks: BackgroundTasks):
    """
    Execute an agent with user input.
    
    Runs the agent with the provided input and returns the result.
    For long-running tasks, consider using background execution.
    """
    agent_repo = _dependencies["agent_repo"]
    orchestrator = _dependencies["orchestrator"]
    observability = _dependencies["observability"]
    
    observability.log("info", "Executing agent", {
        "agent_id": str(agent_id),
        "input_length": len(request.user_input)
    })
    
    try:
        use_case = ExecuteAgentUseCase(agent_repo, orchestrator)
        result = await use_case.execute(
            agent_id=agent_id,
            user_input=request.user_input,
        )
        
        # Record metrics
        observability.record_metric(
            "agent_execution",
            1.0,
            {"agent_id": str(agent_id), "status": "success" if result.success else "failed"},
        )
        
        if result.success:
            observability.log("info", "Agent execution completed", {
                "agent_id": str(agent_id),
                "duration": result.duration_seconds,
                "tokens": result.total_tokens,
            })
        
        return ExecutionResultResponse(
            agent_id=result.agent_id,
            success=result.success,
            output=result.output,
            error=result.error,
            total_tokens=result.total_tokens,
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            duration_seconds=result.duration_seconds,
            iterations=result.iterations,
            estimated_cost=result.estimated_cost,
            final_status=result.final_status,
        )
        
    except AgentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent {agent_id} not found")
    except AgentExecutionError as e:
        observability.log("error", "Agent execution error", {"agent_id": str(agent_id), "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        observability.log("error", "Unexpected execution error", {"agent_id": str(agent_id), "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@app.post("/agents/{agent_id}/stream", tags=["Execution"])
async def stream_agent_response(agent_id: UUID, request: ExecuteAgentRequest):
    """
    Stream agent response in real-time.
    
    Returns a server-sent events (SSE) stream with tokens as they arrive.
    Provides better UX for chat interfaces.
    
    Note: Tool calling is not supported in streaming mode.
    """
    agent_repo = _dependencies["agent_repo"]
    orchestrator = _dependencies["orchestrator"]
    observability = _dependencies["observability"]
    
    observability.log("info", "Starting streaming execution", {
        "agent_id": str(agent_id),
        "input_length": len(request.user_input)
    })
    
    try:
        # Get agent
        use_case = GetAgentUseCase(agent_repo)
        agent = await use_case.execute_by_id(agent_id)
        
        async def event_generator():
            """Generate SSE events for streaming."""
            try:
                async for token in orchestrator.stream_agent_response(
                    agent=agent,
                    user_input=request.user_input,
                ):
                    # Send token as SSE
                    yield f"data: {token}\n\n"
                
                # Send completion marker
                yield "data: [DONE]\n\n"
                
                observability.log("info", "Streaming execution completed", {
                    "agent_id": str(agent_id),
                })
                
            except Exception as e:
                observability.log("error", "Streaming execution failed", {
                    "agent_id": str(agent_id),
                    "error": str(e)
                })
                yield f"data: [ERROR] {str(e)}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            },
        )
        
    except AgentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent {agent_id} not found")
    except Exception as e:
        observability.log("error", "Failed to start streaming", {
            "agent_id": str(agent_id),
            "error": str(e)
        })
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """
    Get application metrics.
    
    Returns Prometheus-compatible metrics if enabled.
    """
    config = _dependencies["config"]
    
    if not config.observability.enable_metrics:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metrics not enabled")
    
    return {
        "message": "Metrics available at Prometheus endpoint",
        "endpoint": f"http://localhost:{config.observability.metrics_port}/metrics",
    }


if __name__ == "__main__":
    import uvicorn
    
    config = get_config()
    
    uvicorn.run(
        "src.api.rest:app",
        host="0.0.0.0",
        port=8000,
        reload=config.is_development(),
        log_level=config.observability.log_level.lower(),
    )
