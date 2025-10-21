"""Main entry point for experiment execution."""

import sys
import time
from pathlib import Path
from datetime import datetime

from src.orchestrator.runner import OrchestratorRunner
from src.orchestrator.config_loader import load_config
from src.orchestrator.manifest_manager import find_runs
from src.utils.logger import get_logger
from src.utils.isolation import generate_run_id

logger = get_logger(__name__)


def _timestamp():
    """Get current timestamp string."""
    return datetime.now().strftime("%H:%M:%S")


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
        
        # Get enabled frameworks
        enabled_frameworks = [
            name for name, fw_config in config.get('frameworks', {}).items()
            if fw_config.get('enabled', False)
        ]
        
        if not enabled_frameworks:
            logger.error("No frameworks enabled in configuration")
            return 1
        
        # Get max runs from stopping_rule (required)
        stopping_rule = config.get('stopping_rule')
        if not stopping_rule:
            logger.error("Missing 'stopping_rule' section in config.yaml")
            return 1
        
        max_runs = stopping_rule.get('max_runs')
        if max_runs is None:
            logger.error("Missing 'stopping_rule.max_runs' in config.yaml")
            return 1
        
        # Print header
        print()
        print("=" * 60)
        print(f"  🧪 Experiment: {experiment_name}")
        print("=" * 60)
        print(f"  Model:      {model}")
        print(f"  Frameworks: {', '.join(enabled_frameworks)}")
        print(f"  Max runs:   {max_runs} per framework")
        print(f"  Started:    {_timestamp()}")
        print("=" * 60)
        print(f"  💡 Full logs: runs/<framework>/<run_id>/logs/run.log")
        print("=" * 60)
        print()
        
        # Run each framework
        all_results = {}
        start_time = time.time()
        
        for idx, framework_name in enumerate(enabled_frameworks, 1):
            # Check how many runs already exist for this framework
            existing_runs = find_runs(framework=framework_name)
            existing_count = len(existing_runs)
            
            logger.info(f"Starting {framework_name} runs")
            
            print(f"[{idx}/{len(enabled_frameworks)}] Framework: {framework_name.upper()} [{_timestamp()}]")
            
            if existing_count >= max_runs:
                logger.info(f"{framework_name} already has {existing_count}/{max_runs} runs, skipping")
                print(f"      ✓ Already completed ({existing_count}/{max_runs} runs)\n")
                all_results[framework_name] = []
                continue
            
            # Calculate how many more runs are needed
            runs_needed = max_runs - existing_count
            logger.info(f"{framework_name}: {existing_count} existing runs, {runs_needed} more needed")
            
            if existing_count > 0:
                print(f"      Progress: {existing_count}/{max_runs} runs complete")
                print(f"      Executing: {runs_needed} remaining runs")
            else:
                print(f"      Executing: {runs_needed} runs")
            
            framework_results = []
            for run_num in range(existing_count + 1, max_runs + 1):
                run_start = time.time()
                run_id = generate_run_id()
                print(f"      → Run {run_num}/{max_runs} | ID: {run_id} | {_timestamp()}")
                
                logger.info(f"Running {framework_name} - run {run_num}/{max_runs} | Run ID: {run_id}")
                
                runner = OrchestratorRunner(
                    framework_name=framework_name,
                    config_path=str(config_path),
                    experiment_name=experiment_name,
                    run_id=run_id
                )
                
                result = runner.execute_single_run()
                framework_results.append(result)
                
                run_time = time.time() - run_start
                print(f"      ✓ Completed in {run_time:.1f}s [{_timestamp()}]")
            
            all_results[framework_name] = framework_results
            print()
        
        total_time = time.time() - start_time
        logger.info("Experiment completed successfully")
        logger.info(f"Results saved to: {Path('runs').absolute()}")
        
        # Print summary
        print("=" * 60)
        print("  ✅ Experiment Complete!")
        print("=" * 60)
        print(f"  Finished:   {_timestamp()}")
        print(f"  Duration:   {total_time:.1f}s ({total_time/60:.1f} minutes)")
        print(f"  Results:    {Path('runs').absolute()}")
        print("=" * 60)
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
