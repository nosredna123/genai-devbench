"""
CLI module wrapper for orchestrator runner.

Makes runner.py executable as: python -m src.orchestrator.runner <framework>
"""

import sys
from src.orchestrator.runner import OrchestratorRunner
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Main CLI entry point."""
    if len(sys.argv) != 2:
        print("Usage: python -m src.orchestrator.runner {baes|chatdev|ghspec}")
        sys.exit(1)
        
    framework = sys.argv[1]
    
    if framework not in ['baes', 'chatdev', 'ghspec']:
        print(f"Error: Invalid framework '{framework}'")
        print("Valid options: baes, chatdev, ghspec")
        sys.exit(1)
        
    try:
        runner = OrchestratorRunner(framework)
        result = runner.execute_single_run()
        
        if result['status'] == 'success':
            print(f"\n✓ Run completed successfully")
            print(f"  Run ID: {result['run_id']}")
            print(f"  Archive: {result['archive_path']}")
            sys.exit(0)
        else:
            print(f"\n✗ Run failed: {result.get('error', 'Unknown error')}")
            print(f"  Run ID: {result.get('run_id', 'N/A')}")
            print(f"  Status: {result['status']}")
            sys.exit(1)
            
    except Exception as e:
        logger.error("Unexpected error in orchestrator",
                    extra={'metadata': {'error': str(e)}})
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
