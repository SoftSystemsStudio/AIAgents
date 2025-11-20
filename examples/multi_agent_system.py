"""
Multi-Agent System Example

Demonstrates how multiple agents can collaborate on complex tasks
using message passing and specialized roles.
"""

import asyncio
import os
from typing import List, Dict, Any
from uuid import UUID
from src.domain.models import Agent, Tool, ToolParameter, Message, MessageRole
from src.infrastructure.llm_providers import OpenAIProvider
from src.infrastructure.message_queue import RedisMessageQueue
from src.infrastructure.repositories import InMemoryAgentRepository, InMemoryToolRegistry
from src.infrastructure.observability import StructuredLogger
from src.application.orchestrator import AgentOrchestrator


class MultiAgentCoordinator:
    """
    Coordinates multiple agents working together.
    
    In production, this would be more sophisticated with:
    - Dynamic agent selection
    - Conversation history management
    - Error recovery and retry logic
    - Load balancing across agents
    """
    
    def __init__(
        self,
        agents: Dict[str, Agent],
        orchestrator: AgentOrchestrator,
        message_queue: RedisMessageQueue,
    ):
        self.agents = agents
        self.orchestrator = orchestrator
        self.message_queue = message_queue
        self.conversation_history: List[Dict[str, Any]] = []
    
    async def execute_workflow(self, task: str) -> Dict[str, Any]:
        """
        Execute a multi-agent workflow.
        
        Workflow:
        1. Planner analyzes task and creates plan
        2. Researcher gathers information (if needed)
        3. Executor performs the task
        4. Reviewer validates the result
        """
        
        print(f"\n{'='*60}")
        print(f"🎯 Starting Multi-Agent Workflow")
        print(f"{'='*60}\n")
        
        results = {}
        
        # Step 1: Planning
        print("📋 Step 1: Planning Agent")
        print("-" * 60)
        planner = self.agents["planner"]
        planning_prompt = f"""Analyze this task and create a step-by-step plan:

Task: {task}

Provide:
1. What information is needed
2. Steps to complete the task
3. Expected output format"""

        plan_result = await self.orchestrator.execute_agent(
            agent=planner,
            user_input=planning_prompt,
        )
        
        if not plan_result.success:
            return {"success": False, "error": "Planning failed"}
        
        results["plan"] = plan_result.output
        print(f"\n✅ Plan created:\n{plan_result.output}\n")
        
        # Step 2: Research
        print("\n🔍 Step 2: Research Agent")
        print("-" * 60)
        researcher = self.agents["researcher"]
        research_prompt = f"""Based on this plan, gather necessary information:

Plan:
{results['plan']}

Original Task: {task}

Provide relevant facts, data, and context needed to complete the task."""

        research_result = await self.orchestrator.execute_agent(
            agent=researcher,
            user_input=research_prompt,
        )
        
        if not research_result.success:
            return {"success": False, "error": "Research failed"}
        
        results["research"] = research_result.output
        print(f"\n✅ Research completed:\n{research_result.output}\n")
        
        # Step 3: Execution
        print("\n⚙️  Step 3: Executor Agent")
        print("-" * 60)
        executor = self.agents["executor"]
        execution_prompt = f"""Execute the task using the plan and research:

Task: {task}

Plan:
{results['plan']}

Research:
{results['research']}

Provide the final deliverable."""

        exec_result = await self.orchestrator.execute_agent(
            agent=executor,
            user_input=execution_prompt,
        )
        
        if not exec_result.success:
            return {"success": False, "error": "Execution failed"}
        
        results["execution"] = exec_result.output
        print(f"\n✅ Task executed:\n{exec_result.output}\n")
        
        # Step 4: Review
        print("\n🔎 Step 4: Reviewer Agent")
        print("-" * 60)
        reviewer = self.agents["reviewer"]
        review_prompt = f"""Review the work and provide feedback:

Original Task: {task}

Execution Result:
{results['execution']}

Evaluate:
1. Completeness
2. Accuracy
3. Quality
4. Suggestions for improvement"""

        review_result = await self.orchestrator.execute_agent(
            agent=reviewer,
            user_input=review_prompt,
        )
        
        if not review_result.success:
            return {"success": False, "error": "Review failed"}
        
        results["review"] = review_result.output
        print(f"\n✅ Review completed:\n{review_result.output}\n")
        
        return {
            "success": True,
            "results": results,
            "total_cost": sum([
                plan_result.estimated_cost,
                research_result.estimated_cost,
                exec_result.estimated_cost,
                review_result.estimated_cost,
            ]),
            "total_tokens": sum([
                plan_result.total_tokens,
                research_result.total_tokens,
                exec_result.total_tokens,
                review_result.total_tokens,
            ]),
        }


async def main():
    """Run multi-agent system example."""
    
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Please set OPENAI_API_KEY environment variable")
        return
    
    print("🤝 Multi-Agent System Example\n")
    print("=" * 60)
    print("\nThis example demonstrates agent collaboration with specialized roles:")
    print("  • Planner: Breaks down tasks into steps")
    print("  • Researcher: Gathers information and context")
    print("  • Executor: Performs the actual task")
    print("  • Reviewer: Validates quality and completeness")
    
    # Initialize infrastructure
    llm_provider = OpenAIProvider(api_key=api_key)
    agent_repo = InMemoryAgentRepository()
    tool_registry = InMemoryToolRegistry()
    observability = StructuredLogger(log_level="INFO")
    
    # Initialize message queue (optional, for async communication)
    try:
        message_queue = RedisMessageQueue(host="localhost", port=6379)
        print("\n✅ Connected to Redis for inter-agent messaging")
    except Exception as e:
        print(f"\n⚠️  Redis not available (optional): {e}")
        message_queue = None
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(
        llm_provider=llm_provider,
        tool_registry=tool_registry,
        agent_repository=agent_repo,
        observability=observability,
    )
    
    # Create specialized agents
    print("\n🤖 Creating specialized agents...")
    
    agents = {}
    
    # Planner Agent
    planner = Agent(
        name="planner",
        description="Expert at analyzing tasks and creating detailed plans",
        system_prompt="""You are an expert planning agent. Your role is to:
- Analyze tasks thoroughly
- Break them into clear, actionable steps
- Identify required information and resources
- Create logical execution sequences

Be detailed and systematic in your planning.""",
        model_provider="openai",
        model_name="gpt-4",
        temperature=0.3,
        max_tokens=1000,
    )
    await agent_repo.save(planner)
    agents["planner"] = planner
    print(f"   ✓ Created: {planner.name}")
    
    # Researcher Agent
    researcher = Agent(
        name="researcher",
        description="Expert at gathering and synthesizing information",
        system_prompt="""You are a research specialist. Your role is to:
- Gather relevant facts and data
- Provide context and background
- Cite sources when possible
- Synthesize information clearly

Be thorough and accurate in your research.""",
        model_provider="openai",
        model_name="gpt-4",
        temperature=0.5,
        max_tokens=1200,
    )
    await agent_repo.save(researcher)
    agents["researcher"] = researcher
    print(f"   ✓ Created: {researcher.name}")
    
    # Executor Agent
    executor = Agent(
        name="executor",
        description="Expert at implementing plans and creating deliverables",
        system_prompt="""You are an execution specialist. Your role is to:
- Follow plans carefully
- Use provided research and context
- Create high-quality deliverables
- Handle edge cases appropriately

Be precise and thorough in your execution.""",
        model_provider="openai",
        model_name="gpt-4",
        temperature=0.4,
        max_tokens=1500,
    )
    await agent_repo.save(executor)
    agents["executor"] = executor
    print(f"   ✓ Created: {executor.name}")
    
    # Reviewer Agent
    reviewer = Agent(
        name="reviewer",
        description="Expert at quality assurance and validation",
        system_prompt="""You are a quality reviewer. Your role is to:
- Evaluate completeness and accuracy
- Identify potential improvements
- Provide constructive feedback
- Ensure quality standards are met

Be objective and constructive in your reviews.""",
        model_provider="openai",
        model_name="gpt-4",
        temperature=0.3,
        max_tokens=800,
    )
    await agent_repo.save(reviewer)
    agents["reviewer"] = reviewer
    print(f"   ✓ Created: {reviewer.name}")
    
    # Create coordinator
    coordinator = MultiAgentCoordinator(
        agents=agents,
        orchestrator=orchestrator,
        message_queue=message_queue,
    )
    
    # Example collaborative tasks
    tasks = [
        "Design a simple REST API for managing user profiles with CRUD operations",
        "Create a strategy for implementing distributed tracing in a microservices architecture",
    ]
    
    # Execute each task with multiple agents
    for i, task in enumerate(tasks, 1):
        print(f"\n\n{'='*60}")
        print(f"📝 Task {i}: {task}")
        print(f"{'='*60}")
        
        result = await coordinator.execute_workflow(task)
        
        if result["success"]:
            print(f"\n{'='*60}")
            print("✨ Workflow Completed Successfully!")
            print(f"{'='*60}\n")
            print(f"📊 Overall Metrics:")
            print(f"   • Total tokens: {result['total_tokens']}")
            print(f"   • Total cost: ${result['total_cost']:.4f}")
            print(f"   • Agents involved: {len(agents)}")
        else:
            print(f"\n❌ Workflow failed: {result.get('error')}")
    
    # Cleanup
    if message_queue:
        await message_queue.close()
    
    print("\n\n" + "=" * 60)
    print("✨ Multi-agent example completed!")
    print("\nKey Takeaways:")
    print("  • Multiple agents can collaborate with specialized roles")
    print("  • Workflow coordination enables complex task completion")
    print("  • Each agent focuses on its area of expertise")
    print("  • Results are validated through review process")
    print("  • Costs and tokens are tracked across all agents")


if __name__ == "__main__":
    asyncio.run(main())
