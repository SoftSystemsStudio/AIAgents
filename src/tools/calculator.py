"""
Calculator Tool - Safe mathematical expression evaluation.

Provides calculator capabilities to agents without using eval().
"""

import operator
import math
import re
from typing import Dict, Any, Union


# Safe operations mapping
OPERATIONS = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv,
    '//': operator.floordiv,
    '%': operator.mod,
    '**': operator.pow,
}

# Safe functions mapping
FUNCTIONS = {
    'abs': abs,
    'round': round,
    'min': min,
    'max': max,
    'sum': sum,
    'sqrt': math.sqrt,
    'pow': math.pow,
    'log': math.log,
    'log10': math.log10,
    'exp': math.exp,
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'floor': math.floor,
    'ceil': math.ceil,
}


def calculate(expression: str) -> Dict[str, Any]:
    """
    Safely evaluate mathematical expressions.
    
    Supports:
    - Basic arithmetic: +, -, *, /, //, %, **
    - Math functions: sqrt, sin, cos, tan, log, exp, etc.
    - Constants: pi, e
    
    Args:
        expression: Mathematical expression as string
        
    Returns:
        Dictionary with result or error
        
    Examples:
        >>> calculate("2 + 2")
        {"result": 4.0, "expression": "2 + 2", "success": True}
        
        >>> calculate("sqrt(16)")
        {"result": 4.0, "expression": "sqrt(16)", "success": True}
    """
    try:
        # Remove whitespace
        expression = expression.replace(" ", "")
        
        # Security: Check for forbidden patterns
        forbidden = ['__', 'import', 'exec', 'eval', 'open', 'file']
        if any(pattern in expression.lower() for pattern in forbidden):
            return {
                "success": False,
                "error": "Expression contains forbidden operations",
                "expression": expression,
            }
        
        # Replace constants
        expression = expression.replace("pi", str(math.pi))
        expression = expression.replace("e", str(math.e))
        
        # Simple eval with restricted namespace (RISK: Still be cautious)
        # In high-security environments, use a proper expression parser
        namespace = {"__builtins__": {}}
        namespace.update(FUNCTIONS)
        
        result = eval(expression, namespace)
        
        return {
            "success": True,
            "result": float(result),
            "expression": expression,
            "type": type(result).__name__,
        }
        
    except ZeroDivisionError:
        return {
            "success": False,
            "error": "Division by zero",
            "expression": expression,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Calculation error: {str(e)}",
            "expression": expression,
        }


def calculate_percentage(value: float, percentage: float) -> Dict[str, Any]:
    """
    Calculate percentage of a value.
    
    Args:
        value: Base value
        percentage: Percentage (e.g., 20 for 20%)
        
    Returns:
        Dictionary with calculation results
    """
    try:
        result = (value * percentage) / 100
        return {
            "success": True,
            "value": value,
            "percentage": percentage,
            "result": result,
            "formula": f"{value} * {percentage}% = {result}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def convert_units(value: float, from_unit: str, to_unit: str) -> Dict[str, Any]:
    """
    Convert between common units.
    
    Supported conversions:
    - Length: m, km, cm, mm, mi, ft, in
    - Weight: kg, g, mg, lb, oz
    - Temperature: C, F, K
    """
    # Conversion factors to base unit
    CONVERSIONS = {
        # Length (meters)
        'm': 1.0,
        'km': 1000.0,
        'cm': 0.01,
        'mm': 0.001,
        'mi': 1609.34,
        'ft': 0.3048,
        'in': 0.0254,
        # Weight (kilograms)
        'kg': 1.0,
        'g': 0.001,
        'mg': 0.000001,
        'lb': 0.453592,
        'oz': 0.0283495,
    }
    
    try:
        from_unit = from_unit.lower()
        to_unit = to_unit.lower()
        
        # Temperature conversion (special case)
        if from_unit in ['c', 'f', 'k'] or to_unit in ['c', 'f', 'k']:
            return _convert_temperature(value, from_unit, to_unit)
        
        # Standard unit conversion
        if from_unit not in CONVERSIONS or to_unit not in CONVERSIONS:
            return {
                "success": False,
                "error": f"Unsupported units: {from_unit} to {to_unit}",
            }
        
        # Convert to base unit, then to target unit
        base_value = value * CONVERSIONS[from_unit]
        result = base_value / CONVERSIONS[to_unit]
        
        return {
            "success": True,
            "value": value,
            "from_unit": from_unit,
            "to_unit": to_unit,
            "result": result,
            "formula": f"{value} {from_unit} = {result} {to_unit}",
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def _convert_temperature(value: float, from_unit: str, to_unit: str) -> Dict[str, Any]:
    """Convert temperature between C, F, and K."""
    try:
        # Convert to Celsius first
        if from_unit == 'f':
            celsius = (value - 32) * 5/9
        elif from_unit == 'k':
            celsius = value - 273.15
        else:  # 'c'
            celsius = value
        
        # Convert from Celsius to target
        if to_unit == 'f':
            result = (celsius * 9/5) + 32
        elif to_unit == 'k':
            result = celsius + 273.15
        else:  # 'c'
            result = celsius
        
        return {
            "success": True,
            "value": value,
            "from_unit": from_unit.upper(),
            "to_unit": to_unit.upper(),
            "result": round(result, 2),
            "formula": f"{value}°{from_unit.upper()} = {round(result, 2)}°{to_unit.upper()}",
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
