"""
Tool Registration Helper - Register all built-in tools.

Simplifies tool registration by providing pre-configured tool definitions.
"""

from typing import List
from src.domain.models import Tool, ToolParameter, AgentCapability
from src.domain.interfaces import IToolRegistry


def register_calculator_tools(registry: IToolRegistry) -> List[str]:
    """Register calculator tools."""
    tools_registered = []
    
    # Basic calculator
    calc_tool = Tool(
        name="calculate",
        description="Evaluate mathematical expressions safely. Supports arithmetic, functions like sqrt, sin, cos, and constants pi, e.",
        parameters=[
            ToolParameter(
                name="expression",
                type="string",
                description="Mathematical expression to evaluate (e.g., '(2 + 3) * 4', 'sqrt(16)', 'sin(pi/2)')",
                required=True,
            )
        ],
        handler_module="src.tools.calculator",
        handler_function="calculate",
    )
    registry.register_tool(calc_tool)
    tools_registered.append(calc_tool.name)
    
    # Percentage calculator
    percentage_tool = Tool(
        name="calculate_percentage",
        description="Calculate percentage of a value",
        parameters=[
            ToolParameter(
                name="value",
                type="number",
                description="Base value",
                required=True,
            ),
            ToolParameter(
                name="percentage",
                type="number",
                description="Percentage (e.g., 20 for 20%)",
                required=True,
            ),
        ],
        handler_module="src.tools.calculator",
        handler_function="calculate_percentage",
    )
    registry.register_tool(percentage_tool)
    tools_registered.append(percentage_tool.name)
    
    # Unit converter
    unit_tool = Tool(
        name="convert_units",
        description="Convert between common units (length, weight, temperature)",
        parameters=[
            ToolParameter(
                name="value",
                type="number",
                description="Value to convert",
                required=True,
            ),
            ToolParameter(
                name="from_unit",
                type="string",
                description="Source unit (e.g., 'm', 'km', 'kg', 'lb', 'C', 'F')",
                required=True,
            ),
            ToolParameter(
                name="to_unit",
                type="string",
                description="Target unit",
                required=True,
            ),
        ],
        handler_module="src.tools.calculator",
        handler_function="convert_units",
    )
    registry.register_tool(unit_tool)
    tools_registered.append(unit_tool.name)
    
    return tools_registered


def register_web_search_tools(registry: IToolRegistry) -> List[str]:
    """Register web search tools."""
    tools_registered = []
    
    # Web search
    search_tool = Tool(
        name="search_web",
        description="Search the internet for information. Returns relevant results from search engines.",
        parameters=[
            ToolParameter(
                name="query",
                type="string",
                description="Search query",
                required=True,
            ),
            ToolParameter(
                name="num_results",
                type="integer",
                description="Number of results to return (1-10)",
                required=False,
                default=5,
            ),
        ],
        required_capability=AgentCapability.WEB_SEARCH,
        handler_module="src.tools.web_search",
        handler_function="search_web",
    )
    registry.register_tool(search_tool)
    tools_registered.append(search_tool.name)
    
    # Webpage fetcher
    webpage_tool = Tool(
        name="get_webpage_content",
        description="Fetch and extract text content from a webpage URL",
        parameters=[
            ToolParameter(
                name="url",
                type="string",
                description="URL to fetch",
                required=True,
            ),
            ToolParameter(
                name="max_length",
                type="integer",
                description="Maximum content length",
                required=False,
                default=5000,
            ),
        ],
        required_capability=AgentCapability.WEB_SEARCH,
        handler_module="src.tools.web_search",
        handler_function="get_webpage_content",
    )
    registry.register_tool(webpage_tool)
    tools_registered.append(webpage_tool.name)
    
    return tools_registered


def register_file_operation_tools(registry: IToolRegistry) -> List[str]:
    """Register file operation tools."""
    tools_registered = []
    
    # Read file
    read_tool = Tool(
        name="read_file",
        description="Read contents of a file from allowed directories",
        parameters=[
            ToolParameter(
                name="file_path",
                type="string",
                description="Path to file",
                required=True,
            ),
        ],
        required_capability=AgentCapability.FILE_ACCESS,
        handler_module="src.tools.file_operations",
        handler_function="read_file",
    )
    registry.register_tool(read_tool)
    tools_registered.append(read_tool.name)
    
    # Write file
    write_tool = Tool(
        name="write_file",
        description="Write content to a file in allowed directories",
        parameters=[
            ToolParameter(
                name="file_path",
                type="string",
                description="Path to file",
                required=True,
            ),
            ToolParameter(
                name="content",
                type="string",
                description="Content to write",
                required=True,
            ),
            ToolParameter(
                name="overwrite",
                type="boolean",
                description="Allow overwriting existing files",
                required=False,
                default=False,
            ),
        ],
        required_capability=AgentCapability.FILE_ACCESS,
        handler_module="src.tools.file_operations",
        handler_function="write_file",
    )
    registry.register_tool(write_tool)
    tools_registered.append(write_tool.name)
    
    # List directory
    list_tool = Tool(
        name="list_directory",
        description="List files and directories in a path",
        parameters=[
            ToolParameter(
                name="directory_path",
                type="string",
                description="Path to directory",
                required=True,
            ),
            ToolParameter(
                name="pattern",
                type="string",
                description="Optional glob pattern (e.g., '*.txt')",
                required=False,
            ),
        ],
        required_capability=AgentCapability.FILE_ACCESS,
        handler_module="src.tools.file_operations",
        handler_function="list_directory",
    )
    registry.register_tool(list_tool)
    tools_registered.append(list_tool.name)
    
    return tools_registered


def register_code_execution_tools(registry: IToolRegistry) -> List[str]:
    """Register code execution tools."""
    tools_registered = []
    
    # Execute Python
    exec_tool = Tool(
        name="execute_python_code",
        description="Execute Python code in a sandboxed environment. WARNING: Use with caution.",
        parameters=[
            ToolParameter(
                name="code",
                type="string",
                description="Python code to execute",
                required=True,
            ),
        ],
        required_capability=AgentCapability.CODE_EXECUTION,
        handler_module="src.tools.code_execution",
        handler_function="execute_python_code",
        max_calls_per_minute=5,  # Rate limit code execution
    )
    registry.register_tool(exec_tool)
    tools_registered.append(exec_tool.name)
    
    # Validate syntax
    validate_tool = Tool(
        name="validate_python_syntax",
        description="Validate Python code syntax without executing it",
        parameters=[
            ToolParameter(
                name="code",
                type="string",
                description="Python code to validate",
                required=True,
            ),
        ],
        handler_module="src.tools.code_execution",
        handler_function="validate_python_syntax",
    )
    registry.register_tool(validate_tool)
    tools_registered.append(validate_tool.name)
    
    return tools_registered


def register_all_tools(registry: IToolRegistry) -> dict:
    """
    Register all built-in tools.
    
    Returns dictionary with categories and tool names.
    """
    registered = {}
    
    registered["calculator"] = register_calculator_tools(registry)
    registered["web_search"] = register_web_search_tools(registry)
    registered["file_operations"] = register_file_operation_tools(registry)
    registered["code_execution"] = register_code_execution_tools(registry)
    
    return registered
