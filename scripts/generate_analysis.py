#!/usr/bin/env python3
"""Analysis entry point that uses VisualizationFactory.

This script loads run data, computes statistics, generates visualizations,
and produces a comprehensive statistical report. It replaces the embedded
Python code in analyze_results.sh with a cleaner, config-driven approach.

Usage:
    python generate_analysis.py [--output-dir OUTPUT_DIR] [--config CONFIG]
    
Arguments:
    --output-dir: Directory to save analysis outputs (default: ./analysis_output)
    --config: Path to experiment config YAML (default: config/experiment.yaml)
"""

import argparse
import sys
from pathlib import Path
from collections import defaultdict
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.report_generator import (
    bootstrap_aggregate_metrics,
    compute_composite_scores,
    generate_statistical_report
)
from src.analysis.visualization_factory import VisualizationFactory
from src.orchestrator.config_loader import load_config
from src.utils.logger import get_logger
from src.orchestrator.manifest_manager import get_manifest, find_runs

logger = get_logger(__name__)


def load_run_data(runs_dir: Path) -> tuple[dict, dict]:
    """Load all verified run data from manifest.
    
    Args:
        runs_dir: Path to runs directory
        
    Returns:
        Tuple of (frameworks_data, timeline_data) where:
            - frameworks_data: {framework: [run1_metrics, run2_metrics, ...]}
            - timeline_data: {framework: {step_num: {metric: [val1, val2, ...]}}}
    """
    frameworks_data = defaultdict(list)
    timeline_data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    
    # Get manifest
    try:
        manifest = get_manifest()
        logger.info("Manifest loaded: %d total runs across %d frameworks", 
                    manifest['total_runs'], len(manifest['frameworks']))
    except FileNotFoundError:
        logger.error("Manifest file not found. Run experiments first or rebuild manifest.")
        sys.exit(1)
    except (IOError, json.JSONDecodeError) as e:
        logger.error("Failed to load manifest: %s", e)
        sys.exit(1)
    
    # Query all runs from manifest
    all_runs = find_runs()
    
    if not all_runs:
        logger.error("No runs found in manifest")
        sys.exit(1)
    
    logger.info("Found %d runs in manifest", len(all_runs))
    
    # Load metrics for each run
    for run_entry in all_runs:
        framework_name = run_entry['framework']
        run_id = run_entry['run_id']
        
        # Build path to metrics file
        run_dir = runs_dir / framework_name / run_id
        metrics_file = run_dir / "metrics.json"
        
        if not metrics_file.exists():
            logger.warning("Metrics file not found for run %s: %s", run_id, metrics_file)
            continue
        
        try:
            with open(metrics_file, 'r', encoding='utf-8') as f:
                metrics = json.load(f)
            
            # ✅ FILTER: Only include runs with verified reconciliation status
            reconciliation = metrics.get('usage_api_reconciliation', {})
            verification_status = reconciliation.get('verification_status', 'none')
            
            if verification_status != 'verified':
                logger.warning(
                    "Skipping run %s: reconciliation status '%s' (not verified)",
                    run_id, verification_status
                )
                continue
            
            # Extract aggregate metrics for analysis (only numeric metrics)
            if 'aggregate_metrics' in metrics:
                frameworks_data[framework_name].append(metrics['aggregate_metrics'])
            else:
                logger.warning("No aggregate_metrics found in run %s", run_id)
            
            # Load step-by-step data for timeline charts
            # Collect values from ALL runs for later aggregation
            if 'steps' in metrics and isinstance(metrics['steps'], list):
                for step in metrics['steps']:
                    step_num = step.get('step_number')
                    if step_num is not None:
                        # Map lowercase step fields to uppercase metric names
                        metric_mapping = {
                            'api_calls': 'API_CALLS',
                            'tokens_in': 'TOK_IN',
                            'tokens_out': 'TOK_OUT',
                            'duration_seconds': 'duration_seconds'
                        }
                        # Collect all step-level metrics across runs
                        for step_field, metric_name in metric_mapping.items():
                            if step_field in step:
                                # Append value to list for aggregation
                                timeline_data[framework_name][step_num][metric_name].append(step[step_field])
        
        except json.JSONDecodeError as e:
            logger.error("Failed to parse %s: %s", metrics_file, e)
            continue
        except (IOError, KeyError) as e:
            logger.error("Error loading %s: %s", metrics_file, e)
            continue
    
    if not frameworks_data:
        logger.error("No valid metrics loaded from manifest runs")
        sys.exit(1)
    
    # Log filtering summary
    total_loaded = sum(len(runs) for runs in frameworks_data.values())
    logger.info("✅ Loaded %d VERIFIED runs (reconciliation complete)", total_loaded)
    logger.info("Breakdown by framework:")
    for fw, runs in frameworks_data.items():
        logger.info("  %s: %d verified runs", fw, len(runs))
    
    return dict(frameworks_data), dict(timeline_data)


def aggregate_timeline_data(
    timeline_data: dict,
    aggregation: str = 'mean'
) -> dict:
    """Aggregate timeline data across multiple runs.
    
    Args:
        timeline_data: Raw timeline data with lists of values
            {framework: {step_num: {metric: [val1, val2, ...]}}}
        aggregation: Aggregation method - 'mean', 'median', or 'last'
        
    Returns:
        Aggregated timeline data
        {framework: {step_num: {metric: aggregated_value}}}
    """
    aggregated = {}
    
    for framework, steps in timeline_data.items():
        aggregated[framework] = {}
        for step_num, metrics in steps.items():
            aggregated[framework][step_num] = {}
            for metric, values in metrics.items():
                if not values:
                    aggregated[framework][step_num][metric] = 0
                    continue
                
                # Apply aggregation method
                if aggregation == 'mean':
                    aggregated[framework][step_num][metric] = sum(values) / len(values)
                elif aggregation == 'median':
                    sorted_values = sorted(values)
                    n = len(sorted_values)
                    if n % 2 == 0:
                        aggregated[framework][step_num][metric] = (
                            sorted_values[n//2 - 1] + sorted_values[n//2]
                        ) / 2
                    else:
                        aggregated[framework][step_num][metric] = sorted_values[n//2]
                elif aggregation == 'last':
                    aggregated[framework][step_num][metric] = values[-1]
                else:
                    # Default to mean
                    aggregated[framework][step_num][metric] = sum(values) / len(values)
    
    return aggregated


def compute_aggregates(frameworks_data: dict) -> dict:
    """Compute aggregate statistics for each framework.
    
    Args:
        frameworks_data: Raw run-level data
        
    Returns:
        Dictionary mapping framework to aggregated metrics
        {framework: {metric: mean_value, ...}}
    """
    logger.info("Computing aggregate metrics...")
    aggregated_data = {}
    
    for framework, runs in frameworks_data.items():
        aggregated = bootstrap_aggregate_metrics(runs)
        aggregated_data[framework] = {
            metric: stats['mean']
            for metric, stats in aggregated.items()
        }
        
        # Add composite scores
        try:
            composite = compute_composite_scores(aggregated_data[framework])
            aggregated_data[framework].update(composite)
        except ValueError as e:
            logger.warning("Could not compute composite scores for %s: %s", framework, e)
    
    return aggregated_data


def main():
    """Main entry point for analysis."""
    parser = argparse.ArgumentParser(description='Generate statistical analysis and visualizations')
    parser.add_argument('--output-dir', default='./analysis_output',
                       help='Directory to save outputs (default: ./analysis_output)')
    parser.add_argument('--config', default='config/experiment.yaml',
                       help='Path to config file (default: config/experiment.yaml)')
    parser.add_argument('--runs-dir', default='./runs',
                       help='Directory containing run data (default: ./runs)')
    args = parser.parse_args()
    
    # Paths
    runs_dir = Path(args.runs_dir)
    output_dir = Path(args.output_dir)
    config_file = Path(args.config)
    
    # Validate runs directory exists
    if not runs_dir.exists():
        logger.error("Runs directory not found: %s", runs_dir)
        logger.error("Please run experiments first using ./runners/run_experiment.sh")
        sys.exit(1)
    
    # Create output directory
    logger.info("Creating output directory: %s", output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load configuration
    logger.info("Loading configuration from: %s", config_file)
    try:
        config = load_config(str(config_file))
    except (IOError, ValueError) as e:
        logger.error("Failed to load config: %s", e)
        sys.exit(1)
    
    # Step 1: Load run data
    logger.info("Loading run data from manifest...")
    frameworks_data, timeline_data = load_run_data(runs_dir)
    
    # Step 2: Compute aggregate metrics
    aggregated_data = compute_aggregates(frameworks_data)
    
    # Step 2.5: Aggregate timeline data for charts
    # Get aggregation method from config (default to 'mean')
    timeline_aggregation = 'mean'
    if 'visualizations' in config:
        for _chart_name, chart_config in config['visualizations'].items():
            if 'aggregation' in chart_config:
                timeline_aggregation = chart_config['aggregation']
                break
    
    logger.info("Aggregating timeline data using method: %s", timeline_aggregation)
    aggregated_timeline_data = aggregate_timeline_data(timeline_data, timeline_aggregation)
    
    # Step 3: Generate visualizations using factory
    logger.info("Generating visualizations...")
    try:
        factory = VisualizationFactory(config)
        
        # Validate config before generating
        errors = factory.validate_config()
        if errors:
            logger.warning("Config validation errors:")
            for error in errors:
                logger.warning("  - %s", error)
        
        # Generate all enabled charts
        results = factory.generate_all(
            frameworks_data=frameworks_data,
            aggregated_data=aggregated_data,
            timeline_data=aggregated_timeline_data,  # Use aggregated timeline
            output_dir=str(output_dir)
        )
        
        # Log summary
        succeeded = sum(1 for success in results.values() if success)
        total = len(results)
        logger.info("Generated %d/%d visualizations successfully", succeeded, total)
        
    except (ValueError, IOError) as e:
        logger.error("Visualization generation failed: %s", e)
        # Continue to report generation even if visualizations fail
    
    # Step 4: Generate statistical report
    logger.info("Generating statistical report...")
    try:
        generate_statistical_report(
            frameworks_data,
            str(output_dir / "report.md")
        )
        logger.info("✓ Statistical report saved")
    except (ValueError, IOError) as e:
        logger.error("Failed to generate report: %s", e)
        sys.exit(1)
    
    # Step 5: Summary
    logger.info("=" * 60)
    logger.info("Analysis complete!")
    logger.info("Output directory: %s", output_dir)
    logger.info("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
