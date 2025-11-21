"""
Use cases for Gmail cleanup solution.

These use cases are now deprecated. Import from:
src.application.gmail_cleanup_use_cases instead.
"""

# Legacy imports for backward compatibility
try:
    from src.application.gmail_cleanup_use_cases import (
        AnalyzeInboxUseCase,
        DryRunCleanupUseCase,
        ExecuteCleanupUseCase,
    )
    
    __all__ = [
        "AnalyzeInboxUseCase",
        "DryRunCleanupUseCase",
        "ExecuteCleanupUseCase",
    ]
except ImportError:
    # Graceful fallback if file hasn't been moved yet
    __all__ = []

