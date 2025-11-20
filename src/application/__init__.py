"""
Application Layer - Use cases and orchestration.

This layer contains:
- Use case implementations (business workflows)
- Agent orchestration and execution
- Command and query handlers
- Application services

Clean Architecture Rule: This layer depends on domain but not on infrastructure details.
Infrastructure is injected via dependency injection.
"""
