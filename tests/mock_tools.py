"""
Mock tool handlers for testing.

These are simple implementations used in tests.
"""


def mock_search_web(query: str, num_results: int = 5) -> dict:
    """Mock web search tool."""
    return {
        "query": query,
        "results": [
            {
                "title": f"Result {i}",
                "url": f"https://example.com/{i}",
                "snippet": f"Mock search result {i} for query: {query}",
            }
            for i in range(num_results)
        ],
    }


def mock_calculate(operation: str, a: float, b: float) -> dict:
    """Mock calculator tool."""
    operations = {
        "add": a + b,
        "subtract": a - b,
        "multiply": a * b,
        "divide": a / b if b != 0 else None,
    }
    
    result = operations.get(operation)
    
    return {
        "operation": operation,
        "a": a,
        "b": b,
        "result": result,
    }


async def mock_async_tool(param: str) -> dict:
    """Mock async tool for testing async handlers."""
    return {"processed": param.upper()}
