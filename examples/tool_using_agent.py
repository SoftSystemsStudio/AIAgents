"""
Tool-Using Agent Example

Demonstrates how agents can use tools to perform actions and retrieve information.
Shows tool registration, permission management, and tool execution.
"""

import asyncio
import os
from datetime import datetime
from src.domain.models import Agent, AgentCapability, Tool, ToolParameter
from src.infrastructure.llm_providers import OpenAIProvider
from src.infrastructure.repositories import InMemoryAgentRepository, InMemoryToolRegistry
from src.infrastructure.observability import StructuredLogger
from src.application.orchestrator import AgentOrchestrator


# Tool handler implementations
def get_current_time(timezone: str = "UTC") -> dict:
    """Get current time in specified timezone."""
    current_time = datetime.utcnow().isoformat()
    return {
        "timezone": timezone,
        "current_time": current_time,
        "timestamp": datetime.utcnow().timestamp(),
    }


def calculate_math(expression: str) -> dict:
    """
    Safely evaluate mathematical expressions.
    
    IMPORTANT: In production, use a proper math parser (not eval).
    """
    try:
        # Simple allowlist for safety
        allowed_chars = set("0123456789+-*/(). ")
        if not all(c in allowed_chars for c in expression):
            return {"error": "Invalid characters in expression"}
        
        result = eval(expression, {"__builtins__": {}}, {})
        return {
            "expression": expression,
            "result": result,
            "success": True,
        }
    except Exception as e:
        return {
            "expression": expression,
            "error": str(e),
            "success": False,
        }


def search_documentation(query: str, topic: str = "general") -> dict:
    """Mock documentation search (replace with real search in production)."""
    docs = {
        "clean architecture": "Clean Architecture separates code into layers: Domain, Application, Infrastructure. The domain layer has no external dependencies.",
        "dependency injection": "Dependency Injection is a design pattern where dependencies are provided to a class rather than created by it.",
        "solid principles": "SOLID: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion.",
    }
    
    result = docs.get(query.lower(), "No documentation found for this query.")
    
    return {
        "query": query,
        "topic": topic,
        "result": result,
        "found": query.lower() in docs,
    }


async def main():
    """Run an agent with multiple tools."""
    
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Please set OPENAI_API_KEY environment variable")
        return
    
    print("🛠️  Tool-Using Agent Example\n")
    print("=" * 60)
    
    # Initialize infrastructure
    llm_provider = OpenAIProvider(api_key=api_key)
    agent_repo = InMemoryAgentRepository()
    tool_registry = InMemoryToolRegistry()
    observability = StructuredLogger(log_level="INFO")
    
    # Register tools
    print("\n📦 Registering tools...")
    
    # Time tool
    time_tool = Tool(
        name="get_current_time",
        description="Get the current time in a specified timezone",
        parameters=[
            ToolParameter(
                name="timezone",
                type="string",
                description="Timezone name (e.g., UTC, EST, PST)",
                required=False,
                default="UTC",
            )
        ],
        handler_module="examples.tool_using_agent",
        handler_function="get_current_time",
    )
    tool_registry.register_tool(time_tool)
    print(f"   ✓ Registered: {time_tool.name}")
    
    # Calculator tool
    calc_tool = Tool(
        name="calculate_math",
        description="Evaluate mathematical expressions safely",
        parameters=[
            ToolParameter(
                name="expression",
                type="string",
                description="Mathematical expression to evaluate (e.g., '(123 + 456) * 2')",
                required=True,
            )
        ],
        handler_module="examples.tool_using_agent",
        handler_function="calculate_math",
    )
    tool_registry.register_tool(calc_tool)
    print(f"   ✓ Registered: {calc_tool.name}")
    
    # Documentation search tool
    docs_tool = Tool(
        name="search_documentation",
        description="Search internal documentation for information",
        parameters=[
            ToolParameter(
                name="query",
                type="string",
                description="Search query",
                required=True,
            ),
            ToolParameter(
                name="topic",
                type="string",
                description="Documentation topic area",
                required=False,
                default="general",
            ),
        ],
        handler_module="examples.tool_using_agent",
        handler_function="search_documentation",
    )
    tool_registry.register_tool(docs_tool)
    print(f"   ✓ Registered: {docs_tool.name}")
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(
        llm_provider=llm_provider,
        tool_registry=tool_registry,
        agent_repository=agent_repo,
        observability=observability,
    )
    
    # Create agent with tool access
    agent = Agent(
        name="tool_assistant",
        description="An assistant that can use tools to help users",
        system_prompt="""You are a helpful assistant with access to tools.
When you need information or need to perform calculations, use the available tools.
Always use tools when appropriate rather than making up information.
Explain what you're doing when you use tools.""",
        model_provider="openai",
        model_name="gpt-4",
        temperature=0.3,
        max_tokens=1000,
        allowed_tools=["get_current_time", "calculate_math", "search_documentation"],
        max_iterations=5,
        timeout_seconds=60,
    )
    
    await agent_repo.save(agent)
    print(f"\n✅ Created agent: {agent.name}")
    print(f"   • Tools available: {', '.join(agent.allowed_tools)}")
    
    # Example tasks that require tools
    tasks = [
        "What time is it now? Then calculate how many seconds are in 24 hours.",
        "Search the documentation for 'dependency injection' and then calculate 100 * 50 + 25.",
        "Find information about SOLID principles.",
    ]
    
    # Execute agent for each task
    for i, task in enumerate(tasks, 1):
        print(f"\n\n{'=' * 60}")
        print(f"📋 Task {i}: {task}")
        print("=" * 60)
        
        result = await orchestrator.execute_agent(
            agent=agent,
            user_input=task,
        )
        
        if result.success:
            print(f"\n✅ Response:\n{result.output}\n")
            print(f"📊 Execution Metrics:")
            print(f"   • Tokens: {result.total_tokens} (prompt: {result.prompt_tokens}, completion: {result.completion_tokens})")
            print(f"   • Duration: {result.duration_seconds:.2f}s")
            print(f"   • Cost: ${result.estimated_cost:.4f}")
            print(f"   • Iterations: {result.iterations} (agent used tools {result.iterations - 1} times)")
        else:
            print(f"\n❌ Error: {result.error}")
    
    print("\n\n" + "=" * 60)
    print("✨ Tool-using agent example completed!")
    print("\nKey Takeaways:")
    print("  • Agents can automatically decide when to use tools")
    print("  • Tools extend agent capabilities beyond LLM knowledge")
    print("  • Tool execution is tracked in metrics and observability")
    print("  • Multiple tools can be chained in a single conversation")


if __name__ == "__main__":
    asyncio.run(main())
