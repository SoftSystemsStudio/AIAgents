"""
Simple Agent Example

Demonstrates basic agent creation and execution without tools.
Perfect for getting started with the platform.
"""

import asyncio
import os
from src.domain.models import Agent
from src.infrastructure.llm_providers import OpenAIProvider
from src.infrastructure.repositories import InMemoryAgentRepository, InMemoryToolRegistry
from src.infrastructure.observability import StructuredLogger
from src.application.orchestrator import AgentOrchestrator


async def main():
    """Run a simple agent that answers questions without tools."""
    
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Please set OPENAI_API_KEY environment variable")
        return
    
    print("🤖 Simple Agent Example\n")
    print("=" * 60)
    
    # Initialize infrastructure
    llm_provider = OpenAIProvider(api_key=api_key)
    agent_repo = InMemoryAgentRepository()
    tool_registry = InMemoryToolRegistry()
    observability = StructuredLogger(log_level="INFO")
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(
        llm_provider=llm_provider,
        tool_registry=tool_registry,
        agent_repository=agent_repo,
        observability=observability,
    )
    
    # Create a simple agent
    agent = Agent(
        name="helpful_assistant",
        description="A helpful AI assistant",
        system_prompt="""You are a helpful, friendly AI assistant. 
Provide clear, concise, and accurate answers.
Be conversational and engaging.""",
        model_provider="openai",
        model_name="gpt-4",
        temperature=0.7,
        max_tokens=500,
        max_iterations=3,
        timeout_seconds=30,
    )
    
    # Save agent
    await agent_repo.save(agent)
    print(f"✅ Created agent: {agent.name} (ID: {agent.id})\n")
    
    # Example questions
    questions = [
        "What are the benefits of clean architecture in software development?",
        "Explain the Single Responsibility Principle in simple terms.",
        "What is dependency injection and why is it useful?",
    ]
    
    # Execute agent for each question
    for i, question in enumerate(questions, 1):
        print(f"\n📝 Question {i}: {question}\n")
        print("-" * 60)
        
        result = await orchestrator.execute_agent(
            agent=agent,
            user_input=question,
        )
        
        if result.success:
            print(f"\n💬 Answer: {result.output}\n")
            print(f"📊 Metrics:")
            print(f"   • Tokens used: {result.total_tokens}")
            print(f"   • Duration: {result.duration_seconds:.2f}s")
            print(f"   • Cost: ${result.estimated_cost:.4f}")
            print(f"   • Iterations: {result.iterations}")
        else:
            print(f"\n❌ Error: {result.error}")
        
        print("-" * 60)
    
    print("\n✨ Example completed!")


if __name__ == "__main__":
    asyncio.run(main())
