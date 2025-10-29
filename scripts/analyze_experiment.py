#!/usr/bin/env python3
"""
Analyze experiment runs and generate analysis files for paper generation.

This script reads raw run data from an experiment directory and generates:
- analysis/metrics.json: Aggregated metrics statistics
- analysis/statistical_report.md: Statistical analysis report

Usage:
    python scripts/analyze_experiment.py <experiment_dir> [--output-dir <dir>]
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
import statistics

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_run_metrics(run_dir: Path) -> Dict[str, Any]:
    """Load metrics from a single run directory."""
    metrics_file = run_dir / "metrics.json"
    if not metrics_file.exists():
        logger.warning(f"Metrics file not found: {metrics_file}")
        return None
    
    try:
        with open(metrics_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load {metrics_file}: {e}")
        return None


def aggregate_framework_metrics(framework_dir: Path) -> Dict[str, Any]:
    """Aggregate metrics across all runs for a framework."""
    logger.info(f"Analyzing framework: {framework_dir.name}")
    
    # Find all run directories (UUIDs)
    run_dirs = [d for d in framework_dir.iterdir() if d.is_dir()]
    logger.info(f"Found {len(run_dirs)} runs for {framework_dir.name}")
    
    # Collect metrics from all runs
    all_runs = []
    for run_dir in run_dirs:
        metrics = load_run_metrics(run_dir)
        if metrics:
            all_runs.append(metrics)
    
    if not all_runs:
        logger.warning(f"No valid metrics found for {framework_dir.name}")
        return {}
    
    logger.info(f"Loaded {len(all_runs)} valid runs for {framework_dir.name}")
    
    # Aggregate statistics
    aggregated = {
        "num_runs": len(all_runs),
        "execution_time": aggregate_metric(all_runs, "duration_total"),
        "total_cost_usd": aggregate_metric(all_runs, "cost_total"),
        "api_calls": aggregate_metric(all_runs, "api_calls_total"),
        "tokens_total": aggregate_metric(all_runs, "tokens_total"),
    }
    
    return aggregated


def aggregate_metric(runs: List[Dict], metric_name: str) -> Dict[str, float]:
    """Calculate statistics for a specific metric across runs."""
    values = []
    
    for run in runs:
        # Try to find the metric in the run data
        value = None
        
        # Check top-level
        if metric_name in run:
            value = run[metric_name]
        # Check if it's a computed total from steps
        elif metric_name == "duration_total" and "steps" in run:
            value = sum(step.get("duration_seconds", 0) for step in run["steps"])
        elif metric_name == "cost_total" and "steps" in run:
            value = sum(step.get("cost", 0) for step in run["steps"])
        elif metric_name == "api_calls_total" and "steps" in run:
            value = sum(step.get("api_calls", 0) for step in run["steps"])
        elif metric_name == "tokens_total" and "steps" in run:
            value = sum(step.get("tokens_used", 0) for step in run["steps"])
        
        if value is not None:
            values.append(value)
    
    if not values:
        logger.warning(f"No values found for metric: {metric_name}")
        return {"mean": 0, "std": 0, "min": 0, "max": 0, "count": 0}
    
    return {
        "mean": statistics.mean(values),
        "std": statistics.stdev(values) if len(values) > 1 else 0,
        "min": min(values),
        "max": max(values),
        "count": len(values)
    }


def generate_statistical_report(frameworks_data: Dict[str, Any], output_file: Path):
    """Generate statistical analysis report in Markdown."""
    report = []
    report.append("# Statistical Analysis Report\n")
    report.append(f"Generated from {len(frameworks_data)} frameworks\n")
    report.append("\n## Framework Comparison\n")
    
    # Create comparison table
    report.append("\n### Execution Time\n")
    report.append("| Framework | Mean (s) | Std Dev | Min | Max | Runs |")
    report.append("|-----------|----------|---------|-----|-----|------|")
    
    for framework, data in sorted(frameworks_data.items()):
        if "execution_time" in data:
            et = data["execution_time"]
            report.append(
                f"| {framework} | {et['mean']:.2f} | {et['std']:.2f} | "
                f"{et['min']:.2f} | {et['max']:.2f} | {et['count']} |"
            )
    
    report.append("\n### Cost Analysis\n")
    report.append("| Framework | Mean ($) | Std Dev | Min | Max | Runs |")
    report.append("|-----------|----------|---------|-----|-----|------|")
    
    for framework, data in sorted(frameworks_data.items()):
        if "total_cost_usd" in data:
            cost = data["total_cost_usd"]
            report.append(
                f"| {framework} | ${cost['mean']:.4f} | ${cost['std']:.4f} | "
                f"${cost['min']:.4f} | ${cost['max']:.4f} | {cost['count']} |"
            )
    
    report.append("\n### API Usage\n")
    report.append("| Framework | Metric | Mean | Std Dev |")
    report.append("|-----------|--------|------|---------|")
    
    for framework, data in sorted(frameworks_data.items()):
        if "api_calls" in data:
            calls = data["api_calls"]
            report.append(f"| {framework} | API Calls | {calls['mean']:.2f} | {calls['std']:.2f} |")
        if "tokens_total" in data:
            tokens = data["tokens_total"]
            report.append(f"| {framework} | Total Tokens | {tokens['mean']:.0f} | {tokens['std']:.0f} |")
    
    report.append("\n## Key Findings\n")
    report.append("- Comparative analysis across {} frameworks\n".format(len(frameworks_data)))
    report.append("- Statistical significance tests would require additional analysis\n")
    report.append("- Data collected from raw experiment runs\n")
    
    # Write report
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        f.write('\n'.join(report))
    
    logger.info(f"Statistical report written to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Analyze experiment runs')
    parser.add_argument('experiment_dir', type=Path, help='Path to experiment directory')
    parser.add_argument('--output-dir', type=Path, help='Override output directory (default: experiment_dir/analysis)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate experiment directory
    if not args.experiment_dir.exists():
        logger.error(f"Experiment directory not found: {args.experiment_dir}")
        sys.exit(1)
    
    runs_dir = args.experiment_dir / "runs"
    if not runs_dir.exists():
        logger.error(f"Runs directory not found: {runs_dir}")
        sys.exit(1)
    
    # Determine output directory
    output_dir = args.output_dir if args.output_dir else args.experiment_dir / "analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Analyzing experiment: {args.experiment_dir}")
    logger.info(f"Output directory: {output_dir}")
    
    # Find all framework directories
    framework_dirs = [d for d in runs_dir.iterdir() if d.is_dir()]
    logger.info(f"Found {len(framework_dirs)} frameworks: {[d.name for d in framework_dirs]}")
    
    # Aggregate metrics for each framework
    frameworks_data = {}
    for framework_dir in framework_dirs:
        framework_name = framework_dir.name
        aggregated = aggregate_framework_metrics(framework_dir)
        if aggregated:
            frameworks_data[framework_name] = aggregated
    
    if not frameworks_data:
        logger.error("No valid framework data found")
        sys.exit(1)
    
    # Write metrics.json
    metrics_output = output_dir / "metrics.json"
    with open(metrics_output, 'w') as f:
        json.dump(frameworks_data, f, indent=2)
    logger.info(f"Metrics written to: {metrics_output}")
    
    # Generate statistical report
    report_output = output_dir / "statistical_report.md"
    generate_statistical_report(frameworks_data, report_output)
    
    logger.info("✅ Analysis complete!")
    logger.info(f"   - Metrics: {metrics_output}")
    logger.info(f"   - Report: {report_output}")
    logger.info("")
    logger.info("You can now run paper generation:")
    logger.info(f"   python scripts/generate_paper.py {args.experiment_dir}")


if __name__ == "__main__":
    main()
