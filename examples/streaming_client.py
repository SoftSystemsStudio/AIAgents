"""
Streaming API Client - Test client for streaming endpoint.

Simple client that connects to the streaming API and displays
tokens in real-time.
"""

import asyncio
import httpx
import json
import sys
from uuid import UUID


async def stream_agent_chat(agent_id: str, user_input: str, base_url: str = "http://localhost:8000"):
    """
    Stream chat with an agent via API.
    
    Args:
        agent_id: UUID of the agent
        user_input: Message to send
        base_url: API base URL
    """
    url = f"{base_url}/agents/{agent_id}/stream"
    
    payload = {"user_input": user_input}
    
    print(f"🌊 Streaming from: {url}")
    print(f"💬 User: {user_input}")
    print()
    print("🤖 Assistant: ", end="", flush=True)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream("POST", url, json=payload) as response:
            if response.status_code != 200:
                print(f"\n❌ Error: {response.status_code}")
                print(await response.aread())
                return
            
            # Process SSE stream
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]  # Remove "data: " prefix
                    
                    if data == "[DONE]":
                        print("\n")
                        print("✅ Stream complete")
                        break
                    elif data.startswith("[ERROR]"):
                        print(f"\n❌ Error: {data}")
                        break
                    else:
                        # Print token
                        print(data, end="", flush=True)


async def create_agent(base_url: str = "http://localhost:8000") -> str:
    """Create a test agent and return its ID."""
    url = f"{base_url}/agents"
    
    payload = {
        "name": "Streaming Chat Bot",
        "description": "A chatbot for testing streaming responses",
        "system_prompt": "You are a friendly and helpful chatbot. Respond naturally and conversationally.",
        "model_provider": "openai",
        "model_name": "gpt-4o-mini",
        "temperature": 0.8,
        "max_tokens": 500,
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        
        if response.status_code != 201:
            print(f"❌ Failed to create agent: {response.status_code}")
            print(response.text)
            sys.exit(1)
        
        agent_data = response.json()
        agent_id = agent_data["id"]
        print(f"✅ Created agent: {agent_data['name']} (ID: {agent_id})")
        return agent_id


async def interactive_chat(agent_id: str, base_url: str = "http://localhost:8000"):
    """Interactive chat session with streaming."""
    print()
    print("=" * 80)
    print("💬 INTERACTIVE STREAMING CHAT")
    print("=" * 80)
    print()
    print(f"Agent ID: {agent_id}")
    print("Type 'quit' or 'exit' to end the conversation")
    print()
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["quit", "exit", "bye"]:
                print("👋 Goodbye!")
                break
            
            # Stream response
            await stream_agent_chat(agent_id, user_input, base_url)
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


async def demo_mode(agent_id: str, base_url: str = "http://localhost:8000"):
    """Run demo conversation."""
    print()
    print("=" * 80)
    print("🎭 DEMO MODE - Streaming Conversation")
    print("=" * 80)
    print()
    
    demo_messages = [
        "Hello! What can you help me with?",
        "Tell me an interesting fact about AI",
        "Can you explain that in simpler terms?",
    ]
    
    for msg in demo_messages:
        await stream_agent_chat(agent_id, msg, base_url)
        print()
        await asyncio.sleep(1)  # Pause between messages


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Streaming API Client")
    parser.add_argument(
        "--agent-id",
        type=str,
        help="Agent ID (creates new agent if not provided)",
    )
    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["interactive", "demo"],
        default="interactive",
        help="Run mode: interactive chat or demo",
    )
    parser.add_argument(
        "--message",
        type=str,
        help="Send a single message and exit",
    )
    
    args = parser.parse_args()
    
    # Get or create agent
    agent_id = args.agent_id
    if not agent_id:
        print("Creating new agent...")
        agent_id = await create_agent(args.url)
    
    # Single message mode
    if args.message:
        await stream_agent_chat(agent_id, args.message, args.url)
        return
    
    # Interactive or demo mode
    if args.mode == "interactive":
        await interactive_chat(agent_id, args.url)
    else:
        await demo_mode(agent_id, args.url)


if __name__ == "__main__":
    print()
    print("🚀 Starting Streaming API Client...")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
