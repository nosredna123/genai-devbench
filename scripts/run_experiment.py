#!/usr/bin/env python3
"""
Run experiment with multi-experiment support.

Wrapper around the orchestrator that handles:
- Experiment name resolution
- Registry updates
- Path management

Usage:
    python scripts/run_experiment.py EXPERIMENT_NAME [FRAMEWORK] [OPTIONS]
    
Examples:
    # Run all frameworks for experiment
    python scripts/run_experiment.py test_exp
    
    # Run specific framework
    python scripts/run_experiment.py test_exp baes
    
    # Use custom experiments directory
    python scripts/run_experiment.py test_exp --experiments-dir /path/to/custom/experiments
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.experiment_paths import ExperimentPaths, ExperimentNotFoundError
from src.utils.experiment_registry import get_registry, RegistryError
from src.orchestrator.runner import OrchestratorRunner
from src.utils.logger import get_logger

logger = get_logger(__name__, component="experiment_runner")


def run_experiment(experiment_name: str, framework: str = "all", experiments_base_dir: Path = None) -> None:
    """
    Run experiment for specified framework(s).
    
    Args:
        experiment_name: Name of experiment to run
        framework: Framework name (baes, chatdev, ghspec, or 'all')
        experiments_base_dir: Custom base directory for experiments
        
    Raises:
        ExperimentNotFoundError: If experiment doesn't exist
        ValueError: If framework invalid
    """
    # Validate experiment exists
    try:
        exp_paths = ExperimentPaths(experiment_name, experiments_base_dir=experiments_base_dir)
    except ExperimentNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    # Get registry
    registry = get_registry()
    
    # Get experiment metadata
    try:
        exp_metadata = registry.get_experiment(experiment_name)
    except RegistryError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    # Check if experiment is complete
    if exp_metadata.get('stopping_rule_met'):
        print(f"⚠ Experiment '{experiment_name}' has already met stopping rule")
        print(f"  Status: {exp_metadata.get('status')}")
        print(f"  Runs: {exp_metadata.get('total_runs')}/{exp_metadata.get('max_runs')}")
        confirm = input("Continue anyway? [y/N]: ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("Cancelled.")
            sys.exit(0)
    
    # Validate framework
    valid_frameworks = ['baes', 'chatdev', 'ghspec', 'all']
    if framework not in valid_frameworks:
        print(f"❌ Invalid framework: {framework}")
        print(f"Valid options: {', '.join(valid_frameworks)}")
        sys.exit(1)
    
    # Determine which frameworks to run
    if framework == 'all':
        frameworks_to_run = [
            fw_name for fw_name, fw_data in exp_metadata['frameworks'].items()
            if fw_data.get('enabled', False)
        ]
        
        if not frameworks_to_run:
            print(f"❌ No frameworks enabled in experiment '{experiment_name}'")
            sys.exit(1)
    else:
        # Check if framework is enabled
        if framework not in exp_metadata['frameworks']:
            print(f"❌ Framework '{framework}' not found in experiment '{experiment_name}'")
            sys.exit(1)
        
        if not exp_metadata['frameworks'][framework].get('enabled', False):
            print(f"❌ Framework '{framework}' is not enabled in experiment '{experiment_name}'")
            print(f"Enabled frameworks: {', '.join([fw for fw, data in exp_metadata['frameworks'].items() if data.get('enabled')])}")
            sys.exit(1)
        
        frameworks_to_run = [framework]
    
    # Print experiment info
    print("=" * 70)
    print(f"Running Experiment: {experiment_name}")
    print("=" * 70)
    print(f"Model: {exp_metadata.get('model')}")
    print(f"Frameworks: {', '.join(frameworks_to_run)}")
    print(f"Current runs: {exp_metadata.get('total_runs')}/{exp_metadata.get('max_runs')}")
    print(f"Status: {exp_metadata.get('status')}")
    print(f"Config: {exp_paths.config_path}")
    print("=" * 70)
    print()
    
    # Run each framework
    for fw_name in frameworks_to_run:
        print(f"\n▶ Running framework: {fw_name}")
        print("-" * 70)
        
        try:
            # Create runner with experiment context
            runner = OrchestratorRunner(
                framework_name=fw_name,
                config_path=str(exp_paths.config_path),
                experiment_name=experiment_name
            )
            
            # Execute run
            result = runner.execute_single_run()
            
            # Update registry
            registry.increment_run_count(experiment_name, fw_name)
            
            print(f"✓ Framework {fw_name} completed")
            print(f"  Run ID: {result.get('run_id')}")
            print(f"  Steps: {result.get('total_steps', 'N/A')}")
            print(f"  Tokens: {result.get('total_tokens', 'N/A')}")
            
        except Exception as e:
            logger.exception(f"Error running framework {fw_name}")
            print(f"❌ Framework {fw_name} failed: {e}")
            sys.exit(1)
    
    # Print summary
    print()
    print("=" * 70)
    print("✅ Experiment run completed!")
    print("=" * 70)
    
    # Get updated metadata
    exp_metadata = registry.get_experiment(experiment_name)
    print(f"Total runs: {exp_metadata.get('total_runs')}/{exp_metadata.get('max_runs')}")
    print(f"Status: {exp_metadata.get('status')}")
    
    if exp_metadata.get('stopping_rule_met'):
        print("\n🎉 Stopping rule met! Experiment complete.")
    
    print(f"\nResults: {exp_paths.runs_dir}")
    print(f"Manifest: {exp_paths.manifest_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Run experiment with multi-experiment support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all enabled frameworks
  python scripts/run_experiment.py test_exp
  
  # Run specific framework
  python scripts/run_experiment.py test_exp baes
  
  # Run multiple times
  for i in {1..5}; do python scripts/run_experiment.py test_exp; done
        """
    )
    
    parser.add_argument(
        'experiment',
        help='Experiment name'
    )
    
    parser.add_argument(
        'framework',
        nargs='?',
        default='all',
        choices=['all', 'baes', 'chatdev', 'ghspec'],
        help='Framework to run (default: all enabled frameworks)'
    )
    
    parser.add_argument(
        '--experiments-dir',
        type=Path,
        help='Custom base directory for experiments (default: ./experiments)'
    )
    
    args = parser.parse_args()
    
    try:
        run_experiment(args.experiment, args.framework, args.experiments_dir)
    
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(130)
    
    except Exception as e:
        logger.exception("Unexpected error during experiment run")
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
