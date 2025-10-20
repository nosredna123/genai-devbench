"""Main entry point for experiment execution."""

import sys
from pathlib import Path

from src.orchestrator.runner import ExperimentRunner
from src.orchestrator.config_loader import load_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Execute experiment."""
    try:
        # Load configuration
        config_path = Path('config.yaml')
        if not config_path.exists():
            logger.error("config.yaml not found")
            return 1
        
        config = load_config(config_path)
        
        experiment_name = config.get('experiment_name', 'unnamed')
        logger.info(f"Starting experiment: {experiment_name}")
        logger.info(f"Model: {config.get('model', 'unknown')}")
        
        # Create runner
        runner = ExperimentRunner(config)
        
        # Execute experiment
        results = runner.run()
        
        logger.info("Experiment completed successfully")
        logger.info(f"Results saved to: {Path('runs').absolute()}")
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("Experiment interrupted by user")
        return 130
        
    except Exception as e:
        logger.exception("Experiment failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
