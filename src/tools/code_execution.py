"""
Code Execution Tool - Sandboxed Python code execution.

Provides safe code execution capabilities for agents.
"""

import sys
import io
from typing import Dict, Any
import ast
import traceback
from contextlib import redirect_stdout, redirect_stderr


def execute_python_code(code: str, timeout: int = 5) -> Dict[str, Any]:
    """
    Execute Python code in a restricted environment.
    
    WARNING: Code execution is inherently risky. This implementation provides
    basic sandboxing but should NOT be used in production without additional
    security measures:
    
    - Use Docker containers for isolation
    - Implement proper resource limits (CPU, memory, disk)
    - Use libraries like RestrictedPython
    - Run in separate processes with timeout enforcement
    - Implement network isolation
    
    Args:
        code: Python code to execute
        timeout: Execution timeout in seconds
        
    Returns:
        Dictionary with execution results
        
    TODO: Implement proper sandboxing with Docker/containers
    TODO: Add resource limits (CPU, memory)
    TODO: Add network isolation
    TODO: Implement timeout enforcement
    """
    try:
        # Parse code to check for dangerous operations
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {
                "success": False,
                "error": f"Syntax error: {str(e)}",
                "code": code,
            }
        
        # Check for forbidden operations
        forbidden_names = {
            'eval', 'exec', 'compile', '__import__', 'open', 'file',
            'input', 'raw_input', 'execfile', 'reload', 'quit', 'exit',
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in forbidden_names:
                return {
                    "success": False,
                    "error": f"Forbidden operation: {node.id}",
                    "code": code,
                }
            if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                # In production, allow only specific safe modules
                pass
        
        # Create restricted namespace
        safe_builtins = {
            'abs': abs,
            'all': all,
            'any': any,
            'bool': bool,
            'dict': dict,
            'enumerate': enumerate,
            'filter': filter,
            'float': float,
            'int': int,
            'len': len,
            'list': list,
            'map': map,
            'max': max,
            'min': min,
            'range': range,
            'reversed': reversed,
            'round': round,
            'set': set,
            'sorted': sorted,
            'str': str,
            'sum': sum,
            'tuple': tuple,
            'zip': zip,
            'print': print,
        }
        
        namespace = {
            '__builtins__': safe_builtins,
        }
        
        # Capture stdout and stderr
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        
        # Execute code
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            exec(code, namespace)
        
        # Get output
        stdout_output = stdout_buffer.getvalue()
        stderr_output = stderr_buffer.getvalue()
        
        # Extract variables (exclude builtins and private)
        variables = {
            k: str(v)
            for k, v in namespace.items()
            if not k.startswith('_') and k != '__builtins__'
        }
        
        return {
            "success": True,
            "stdout": stdout_output,
            "stderr": stderr_output,
            "variables": variables,
            "code": code,
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "code": code,
        }


def validate_python_syntax(code: str) -> Dict[str, Any]:
    """
    Validate Python code syntax without executing.
    
    Args:
        code: Python code to validate
        
    Returns:
        Dictionary with validation results
    """
    try:
        ast.parse(code)
        return {
            "success": True,
            "valid": True,
            "message": "Code syntax is valid",
            "code": code,
        }
    except SyntaxError as e:
        return {
            "success": True,
            "valid": False,
            "error": str(e),
            "line": e.lineno,
            "offset": e.offset,
            "code": code,
        }


def format_python_code(code: str) -> Dict[str, Any]:
    """
    Format Python code using basic formatting.
    
    In production, integrate with black or autopep8.
    
    Args:
        code: Python code to format
        
    Returns:
        Dictionary with formatted code
    """
    try:
        # Basic formatting (in production, use black)
        import textwrap
        
        formatted = textwrap.dedent(code).strip()
        
        return {
            "success": True,
            "formatted_code": formatted,
            "original_code": code,
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "code": code,
        }
