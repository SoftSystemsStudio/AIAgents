"""
Streaming Agent Example - Real-time token delivery.

Demonstrates:
- Streaming LLM responses for better UX
- Real-time token display
- Server-sent events (SSE) pattern
- Comparison with non-streaming mode
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.domain.models import Agent
from src.infrastructure.llm_providers import OpenAIProvider
from src.infrastructure.repositories import InMemoryAgentRepository, InMemoryToolRegistry
from src.infrastructure.observability import StructuredLogger
from src.application.orchestrator import AgentOrchestrator
from src.config import get_config


async def streaming_example():
    """Demonstrate streaming vs non-streaming responses."""
    # Configuration
    config = get_config()
    
    # Ensure API key is set
    if not config.llm.openai_api_key:
        print("❌ Error: OPENAI_API_KEY not set")
        print("Please set it: export OPENAI_API_KEY='your-key'")
        return
    
    # Initialize dependencies
    llm_provider = OpenAIProvider(api_key=config.llm.openai_api_key)
    agent_repo = InMemoryAgentRepository()
    tool_registry = InMemoryToolRegistry()
    logger = StructuredLogger()
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(
        llm_provider=llm_provider,
        agent_repository=agent_repo,
        tool_registry=tool_registry,
        observability=logger,
    )
    
    # Create agent
    agent = Agent(
        name="Streaming Assistant",
        description="An agent that demonstrates streaming responses",
        system_prompt="You are a helpful assistant. Provide detailed, informative responses.",
        model_provider="openai",
        model_name="gpt-4o-mini",  # Fast model for demo
        temperature=0.7,
        max_tokens=500,
    )
    
    await agent_repo.save(agent)
    
    # Test query
    query = "Explain what streaming responses are and why they're useful in AI chat applications. Include 3 key benefits."
    
    print("=" * 80)
    print("🌊 STREAMING AGENT DEMO")
    print("=" * 80)
    print()
    
    # === STREAMING MODE ===
    print("📡 STREAMING MODE (Real-time token delivery)")
    print("-" * 80)
    print(f"💬 Query: {query}")
    print()
    print("🤖 Response (streaming):")
    print()
    
    # Stream response token by token
    async for token in orchestrator.stream_agent_response(
        agent=agent,
        user_input=query,
    ):
        print(token, end="", flush=True)
    
    print("\n")
    print("-" * 80)
    print("✅ Streaming complete - tokens arrived in real-time!")
    print()
    
    # === COMPARISON: NON-STREAMING MODE ===
    print()
    print("⏳ NON-STREAMING MODE (Wait for complete response)")
    print("-" * 80)
    
    # Create a new agent for clean history
    agent2 = Agent(
        name="Non-Streaming Assistant",
        description="An agent for comparison",
        system_prompt="You are a helpful assistant. Provide detailed, informative responses.",
        model_provider="openai",
        model_name="gpt-4o-mini",
        temperature=0.7,
        max_tokens=500,
    )
    await agent_repo.save(agent2)
    
    print(f"💬 Query: {query}")
    print()
    print("⏳ Waiting for complete response...")
    print()
    
    # Non-streaming execution
    result = await orchestrator.execute_agent(
        agent=agent2,
        user_input=query,
    )
    
    print("🤖 Response (non-streaming):")
    print()
    print(result.output)
    print()
    print("-" * 80)
    print("✅ Response received all at once")
    print()
    
    # === METRICS COMPARISON ===
    print()
    print("📊 COMPARISON")
    print("=" * 80)
    print()
    print("Streaming Mode:")
    print("  ✓ Tokens appear immediately")
    print("  ✓ Better perceived performance")
    print("  ✓ Users can start reading sooner")
    print("  ✓ Ideal for chat interfaces")
    print("  ✗ No tool calling support (in this implementation)")
    print()
    print("Non-Streaming Mode:")
    print("  ✓ Full tool calling support")
    print("  ✓ Complete execution metrics")
    print("  ✓ Better for API integrations")
    print("  ✗ Users wait for complete response")
    print("  ✗ Worse perceived latency")
    print()
    print(f"📈 Metrics from non-streaming execution:")
    print(f"   Duration: {result.duration_seconds:.2f}s")
    print(f"   Tokens: {result.total_tokens}")
    print(f"   Cost: ${result.estimated_cost:.4f}")
    print()


async def api_streaming_example():
    """Example of calling the streaming API endpoint."""
    print()
    print("=" * 80)
    print("🌐 STREAMING API EXAMPLE")
    print("=" * 80)
    print()
    print("To use streaming via the REST API:")
    print()
    print("1. Start the API server:")
    print("   python src/api/rest.py")
    print()
    print("2. Create an agent:")
    print("   curl -X POST http://localhost:8000/agents \\")
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"name": "Chat Bot", "system_prompt": "You are helpful"}\'')
    print()
    print("3. Stream responses:")
    print("   curl -X POST http://localhost:8000/agents/{agent_id}/stream \\")
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"user_input": "Tell me a story"}\'')
    print()
    print("4. You'll receive Server-Sent Events (SSE):")
    print("   data: Once")
    print("   data: upon")
    print("   data: a")
    print("   data: time")
    print("   data: [DONE]")
    print()
    print("💡 Integration Tips:")
    print("   - Use EventSource in JavaScript for browser clients")
    print("   - Use httpx or aiohttp with streaming for Python clients")
    print("   - Handle [DONE] and [ERROR] markers properly")
    print("   - Set Connection: keep-alive header")
    print()


if __name__ == "__main__":
    # Run both examples
    asyncio.run(streaming_example())
    asyncio.run(api_streaming_example())
