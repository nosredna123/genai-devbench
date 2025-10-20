"""Main entry point for experiment execution."""

import sys
from pathlib import Path

from src.orchestrator.runner import OrchestratorRunner
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
        
        # Validate required configuration fields
        experiment_name = config.get('experiment_name')
        if not experiment_name:
            logger.error("Missing 'experiment_name' in config.yaml")
            return 1
        
        model = config.get('model')
        if not model:
            logger.error("Missing 'model' in config.yaml")
            return 1
        
        print("=" * 41)
        print(f"Running experiment: {experiment_name}")
        print("=" * 41)
        print()
        print("Configuration:")
        print(f"  Model: {model}")
        
        # Get enabled frameworks
        enabled_frameworks = [
            name for name, fw_config in config.get('frameworks', {}).items()
            if fw_config.get('enabled', False)
        ]
        
        if not enabled_frameworks:
            logger.error("No frameworks enabled in configuration")
            return 1
        
        print(f"  Frameworks: {', '.join(enabled_frameworks)}")
        
        # Get max runs from stopping_rule (required)
        stopping_rule = config.get('stopping_rule')
        if not stopping_rule:
            logger.error("Missing 'stopping_rule' section in config.yaml")
            return 1
        
        max_runs = stopping_rule.get('max_runs')
        if max_runs is None:
            logger.error("Missing 'stopping_rule.max_runs' in config.yaml")
            return 1
        
        total_runs = len(enabled_frameworks) * max_runs
        print(f"  Max runs per framework: {max_runs}")
        print()
        print("This may take a while...")
        print()
        
        # Run each framework
        all_results = {}
        for framework_name in enabled_frameworks:
            logger.info(f"Starting {framework_name} runs")
            framework_results = []
            
            for run_num in range(1, max_runs + 1):
                logger.info(f"Running {framework_name} - run {run_num}/{max_runs}")
                
                runner = OrchestratorRunner(
                    framework_name=framework_name,
                    config_path=str(config_path),
                    experiment_name=experiment_name
                )
                
                result = runner.run()
                framework_results.append(result)
            
            all_results[framework_name] = framework_results
        
        logger.info("Experiment completed successfully")
        logger.info(f"Results saved to: {Path('runs').absolute()}")
        
        # Print summary
        print()
        print("=" * 41)
        print("✅ Experiment completed!")
        print("=" * 41)
        print(f"Results directory: {Path('runs').absolute()}")
        print()
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("Experiment interrupted by user")
        return 130
        
    except Exception as e:
        logger.exception("Experiment failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
