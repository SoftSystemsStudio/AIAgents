"""
RAG (Retrieval-Augmented Generation) Agent Example

Demonstrates how to build an agent with semantic search capabilities
using a vector database for context retrieval.
"""

import asyncio
import os
from typing import List
from src.domain.models import Agent, Tool, ToolParameter
from src.infrastructure.llm_providers import OpenAIProvider
from src.infrastructure.vector_stores import ChromaVectorStore
from src.infrastructure.repositories import InMemoryAgentRepository, InMemoryToolRegistry
from src.infrastructure.observability import StructuredLogger
from src.application.orchestrator import AgentOrchestrator


# Sample knowledge base about the platform
KNOWLEDGE_BASE = [
    {
        "id": "doc1",
        "content": "Clean Architecture separates code into layers: Domain (business logic), Application (use cases), Infrastructure (external services). Each layer has clear dependencies flowing inward.",
        "metadata": {"topic": "architecture", "type": "concept"},
    },
    {
        "id": "doc2",
        "content": "The Agent class represents an AI agent with configuration (model, temperature), state (conversation history), and behavior (system prompt, allowed tools). Agents execute through the AgentOrchestrator.",
        "metadata": {"topic": "agents", "type": "implementation"},
    },
    {
        "id": "doc3",
        "content": "Tools extend agent capabilities. Each tool has a name, description, parameters, and handler function. Tools require proper capability permissions to be used by agents.",
        "metadata": {"topic": "tools", "type": "feature"},
    },
    {
        "id": "doc4",
        "content": "Observability is provided through structured logging (structlog), distributed tracing (OpenTelemetry), and metrics (Prometheus). All agent executions are automatically instrumented.",
        "metadata": {"topic": "observability", "type": "infrastructure"},
    },
    {
        "id": "doc5",
        "content": "LLM providers are abstracted through the ILLMProvider interface. Currently supports OpenAI and easily extensible to Anthropic, Cohere, or custom providers. Includes automatic retry logic.",
        "metadata": {"topic": "llm", "type": "integration"},
    },
    {
        "id": "doc6",
        "content": "Vector stores enable semantic search through the IVectorStore interface. Supported implementations: Qdrant (production), ChromaDB (development). Used for RAG and memory systems.",
        "metadata": {"topic": "vectordb", "type": "infrastructure"},
    },
]


class RAGContext:
    """Context holder for RAG tool."""
    
    def __init__(self, llm_provider: OpenAIProvider, vector_store: ChromaVectorStore):
        self.llm_provider = llm_provider
        self.vector_store = vector_store
        self.collection_name = "knowledge_base"


# Global context (in production, use dependency injection)
_rag_context: RAGContext = None


async def search_knowledge_base(query: str, num_results: int = 3) -> dict:
    """
    Search the knowledge base using semantic search.
    
    Returns relevant documents based on query similarity.
    """
    try:
        # Generate query embedding
        query_embedding = await _rag_context.llm_provider.get_embedding(query)
        
        # Search vector store
        results = await _rag_context.vector_store.search(
            collection=_rag_context.collection_name,
            query_vector=query_embedding,
            limit=num_results,
        )
        
        # Format results
        documents = []
        for result in results:
            documents.append({
                "content": result["payload"]["content"],
                "score": result["score"],
                "metadata": result["payload"]["metadata"],
            })
        
        return {
            "query": query,
            "num_results": len(documents),
            "documents": documents,
            "success": True,
        }
        
    except Exception as e:
        return {
            "query": query,
            "error": str(e),
            "success": False,
        }


async def setup_knowledge_base(
    llm_provider: OpenAIProvider,
    vector_store: ChromaVectorStore,
) -> None:
    """Initialize vector store with knowledge base documents."""
    
    collection_name = "knowledge_base"
    
    print("\n📚 Setting up knowledge base...")
    
    # Create collection
    try:
        await vector_store.create_collection(
            name=collection_name,
            dimension=1536,  # OpenAI embedding dimension
        )
        print(f"   ✓ Created collection: {collection_name}")
    except Exception as e:
        # Collection might already exist
        print(f"   ℹ Collection may already exist: {e}")
    
    # Generate embeddings for all documents
    print(f"   • Generating embeddings for {len(KNOWLEDGE_BASE)} documents...")
    
    vectors = []
    payloads = []
    ids = []
    
    for doc in KNOWLEDGE_BASE:
        embedding = await llm_provider.get_embedding(doc["content"])
        vectors.append(embedding)
        payloads.append({
            "content": doc["content"],
            "metadata": doc["metadata"],
        })
        ids.append(doc["id"])
    
    # Insert into vector store
    await vector_store.insert_vectors(
        collection=collection_name,
        vectors=vectors,
        payloads=payloads,
        ids=ids,
    )
    
    print(f"   ✓ Indexed {len(KNOWLEDGE_BASE)} documents")


async def main():
    """Run RAG agent example."""
    
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Please set OPENAI_API_KEY environment variable")
        return
    
    print("🔍 RAG (Retrieval-Augmented Generation) Agent Example\n")
    print("=" * 60)
    
    # Initialize infrastructure
    llm_provider = OpenAIProvider(api_key=api_key)
    
    # Use ChromaDB for simplicity (no external service needed)
    vector_store = ChromaVectorStore(persist_directory="./chroma_data")
    
    agent_repo = InMemoryAgentRepository()
    tool_registry = InMemoryToolRegistry()
    observability = StructuredLogger(log_level="INFO")
    
    # Set up RAG context
    global _rag_context
    _rag_context = RAGContext(llm_provider, vector_store)
    
    # Initialize knowledge base
    await setup_knowledge_base(llm_provider, vector_store)
    
    # Register RAG tool
    print("\n🛠️  Registering RAG tool...")
    
    rag_tool = Tool(
        name="search_knowledge_base",
        description="Search the internal knowledge base for relevant information. Use this to find accurate information about the platform.",
        parameters=[
            ToolParameter(
                name="query",
                type="string",
                description="Search query describing what information you need",
                required=True,
            ),
            ToolParameter(
                name="num_results",
                type="integer",
                description="Number of results to return (1-5)",
                required=False,
                default=3,
            ),
        ],
        handler_module="examples.rag_agent",
        handler_function="search_knowledge_base",
    )
    tool_registry.register_tool(rag_tool)
    print(f"   ✓ Registered: {rag_tool.name}")
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(
        llm_provider=llm_provider,
        tool_registry=tool_registry,
        agent_repository=agent_repo,
        observability=observability,
    )
    
    # Create RAG agent
    agent = Agent(
        name="knowledge_assistant",
        description="An assistant that uses RAG to answer questions accurately",
        system_prompt="""You are a knowledgeable assistant with access to a documentation knowledge base.

When asked a question:
1. Use the search_knowledge_base tool to find relevant information
2. Base your answer on the retrieved documents
3. Cite when information comes from the knowledge base
4. If the knowledge base doesn't have relevant info, say so clearly

Be accurate and grounded in the retrieved information.""",
        model_provider="openai",
        model_name="gpt-4",
        temperature=0.3,  # Lower temperature for factual responses
        max_tokens=800,
        allowed_tools=["search_knowledge_base"],
        max_iterations=5,
        timeout_seconds=60,
    )
    
    await agent_repo.save(agent)
    print(f"\n✅ Created RAG agent: {agent.name}")
    
    # Example questions
    questions = [
        "How is the code organized in this platform? What architectural pattern is used?",
        "How do I create and use tools with agents?",
        "What observability features are available?",
        "How do I integrate a new LLM provider?",
    ]
    
    # Execute agent for each question
    for i, question in enumerate(questions, 1):
        print(f"\n\n{'=' * 60}")
        print(f"❓ Question {i}: {question}")
        print("=" * 60)
        
        result = await orchestrator.execute_agent(
            agent=agent,
            user_input=question,
        )
        
        if result.success:
            print(f"\n💬 Answer:\n{result.output}\n")
            print(f"📊 Metrics:")
            print(f"   • Tokens: {result.total_tokens}")
            print(f"   • Duration: {result.duration_seconds:.2f}s")
            print(f"   • Cost: ${result.estimated_cost:.4f}")
            print(f"   • Knowledge base searches: {result.iterations - 1}")
        else:
            print(f"\n❌ Error: {result.error}")
    
    print("\n\n" + "=" * 60)
    print("✨ RAG agent example completed!")
    print("\nKey Takeaways:")
    print("  • RAG grounds LLM responses in factual knowledge")
    print("  • Semantic search finds relevant docs even with different wording")
    print("  • Vector databases enable efficient similarity search")
    print("  • Agents can cite sources and admit when info is unavailable")
    print("\nℹ️  Knowledge base stored in: ./chroma_data/")


if __name__ == "__main__":
    asyncio.run(main())
