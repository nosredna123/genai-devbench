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
            print("❌ ERROR: config.yaml not found", file=sys.stderr)
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
        
        # Initialize run tracking for all frameworks
        all_results = {}
        framework_run_counts = {}
        
        for framework_name in enabled_frameworks:
            existing_runs = find_runs(framework=framework_name)
            framework_run_counts[framework_name] = len(existing_runs)
            all_results[framework_name] = []
        
        # Display initial status
        print("Initial status:")
        for framework_name in enabled_frameworks:
            count = framework_run_counts[framework_name]
            if count >= max_runs:
                print(f"  • {framework_name.upper()}: ✓ Already completed ({count}/{max_runs} runs)")
            else:
                print(f"  • {framework_name.upper()}: {count}/{max_runs} runs")
        print()
        
        # Execute runs in round-robin fashion (framework with fewest runs goes first)
        start_time = time.time()
        total_runs_needed = sum(max_runs - framework_run_counts[fw] for fw in enabled_frameworks)
        completed_runs = 0
        
        logger.info(f"Starting interleaved execution: {total_runs_needed} total runs needed")
        
        while completed_runs < total_runs_needed:
            # Find framework with fewest runs that still needs more
            next_framework = min(
                (fw for fw in enabled_frameworks if framework_run_counts[fw] < max_runs),
                key=lambda fw: framework_run_counts[fw]
            )
            
            # Execute one run for the selected framework
            current_count = framework_run_counts[next_framework]
            run_num = current_count + 1
            
            run_start = time.time()
            run_id = generate_run_id()
            
            print(f"[{completed_runs + 1}/{total_runs_needed}] {next_framework.upper()} - Run {run_num}/{max_runs} | ID: {run_id} | {_timestamp()}")
            
            logger.info(f"Running {next_framework} - run {run_num}/{max_runs} | Run ID: {run_id}")
            
            runner = OrchestratorRunner(
                framework_name=next_framework,
                config_path=str(config_path),
                experiment_name=experiment_name,
                run_id=run_id
            )
            
            result = runner.execute_single_run()
            all_results[next_framework].append(result)
            
            # Update run count
            framework_run_counts[next_framework] += 1
            completed_runs += 1
            
            run_time = time.time() - run_start
            print(f"      ✓ Completed in {run_time:.1f}s [{_timestamp()}]")
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
        print("\n❌ Experiment interrupted by user", file=sys.stderr)
        logger.warning("Experiment interrupted by user")
        return 130
        
    except Exception as e:
        print(f"\n❌ EXPERIMENT FAILED: {e}", file=sys.stderr)
        logger.exception("Experiment failed")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
