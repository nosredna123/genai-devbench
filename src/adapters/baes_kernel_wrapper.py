"""
Wrapper script to execute BAEs kernel in its isolated virtual environment.
This script is executed by the BAeSAdapter using subprocess with the venv's Python.
"""
import sys
import json
import os
from pathlib import Path


def execute_request(framework_dir: str, context_store_path: str, request: str, start_servers: bool) -> dict:
    """Execute a natural language request using BAEs kernel.
    
    Args:
        framework_dir: Path to BAEs framework directory
        context_store_path: Path to context store JSON file
        request: Natural language request text
        start_servers: Whether to start API/UI servers
        
    Returns:
        Dictionary with success status and result
    """
    # Add framework to path
    sys.path.insert(0, framework_dir)
    
    try:
        from baes.core.enhanced_runtime_kernel import EnhancedRuntimeKernel
        
        # Initialize kernel
        kernel = EnhancedRuntimeKernel(context_store_path)
        
        # Process request
        result = kernel.process_natural_language_request(
            request=request,
            start_servers=start_servers
        )
        
        return {
            'success': True,
            'result': result
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }


if __name__ == '__main__':
    if len(sys.argv) != 5:
        print(json.dumps({
            'success': False,
            'error': f'Usage: {sys.argv[0]} <framework_dir> <context_store_path> <request> <start_servers>'
        }))
        sys.exit(1)
    
    framework_dir = sys.argv[1]
    context_store_path = sys.argv[2]
    request = sys.argv[3]
    start_servers = sys.argv[4].lower() == 'true'
    
    result = execute_request(framework_dir, context_store_path, request, start_servers)
    print(json.dumps(result))
