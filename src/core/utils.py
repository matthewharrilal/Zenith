"""
Utility functions for common operations
"""
from typing import Dict, Any, Optional

def handle_error(operation_name: str, error: Exception, fallback_value: Optional[Any] = None) -> Dict[str, Any]:
    """
    Centralized error handling for consistent error responses
    
    Args:
        operation_name: Name of the operation that failed
        error: The exception that occurred
        fallback_value: Optional fallback value to return
    
    Returns:
        Dict with error information
    """
    print(f"Error in {operation_name}: {error}")
    
    if fallback_value is not None:
        return {"success": False, "error": str(error), "fallback": fallback_value}
    else:
        return {"success": False, "error": str(error)}

def safe_execute(operation_name: str, func, *args, **kwargs) -> Dict[str, Any]:
    """
    Safely execute a function with error handling
    
    Args:
        operation_name: Name of the operation for error reporting
        func: Function to execute
        *args, **kwargs: Arguments to pass to the function
    
    Returns:
        Dict with success/error information
    """
    try:
        result = func(*args, **kwargs)
        return {"success": True, "result": result}
    except Exception as e:
        return handle_error(operation_name, e)
