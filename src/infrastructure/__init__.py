"""
Infrastructure Layer - Concrete implementations of domain interfaces.

This layer contains:
- LLM provider adapters (OpenAI, Anthropic)
- Vector store adapters (Qdrant, Chroma)
- Message queue implementations (Redis)
- Repository implementations
- External service integrations

Clean Architecture Rule: This layer depends on the domain layer but not vice versa.
"""
