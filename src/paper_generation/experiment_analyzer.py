"""
ExperimentAnalyzer: Analyzes raw experiment run data.

Reads raw run metrics from experiment_dir/runs/ and generates aggregated
statistics and reports in the output directory.
"""

import json
import logging
import statistics
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict
import yaml

from .exceptions import ExperimentDataError
from src.utils.cost_calculator import CostCalculator

logger = logging.getLogger(__name__)


class ExperimentAnalyzer:
    """
    Analyzes raw experiment run data and generates aggregated statistics.
    
    Reads from: experiment_dir/runs/{framework}/{run_id}/metrics.json
    Writes to: output_dir/metrics.json, output_dir/statistical_report.md
    """
    
    def __init__(self, experiment_dir: Path, output_dir: Path):
        """
        Initialize analyzer.
        
        Args:
            experiment_dir: Root experiment directory with runs/
            output_dir: Where to write analysis results
        """
        self.experiment_dir = experiment_dir
        self.output_dir = output_dir
        self.runs_dir = experiment_dir / "runs"
        
        if not self.runs_dir.exists():
            raise ExperimentDataError(
                message=f"Runs directory not found: {self.runs_dir}",
                remediation="Ensure experiment has completed and generated run data"
            )
        
        # Load experiment config for model and pricing
        self.config = self._load_experiment_config()
        self.default_model = self.config.get('model', 'gpt-4o-mini')
        self.pricing_config = self.config.get('pricing', {}).get('models', {})
        
        logger.debug(f"Loaded config: model={self.default_model}, pricing for {len(self.pricing_config)} models")
    
    def _load_experiment_config(self) -> Dict[str, Any]:
        """Load experiment config.yaml from experiment directory."""
        config_file = self.experiment_dir / "config.yaml"
        
        if not config_file.exists():
            logger.warning(f"Config file not found: {config_file}, using defaults")
            return {}
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Failed to load config: {e}, using defaults")
            return {}
    
    def analyze(self) -> Dict[str, Any]:
        """
        Perform complete analysis of experiment runs.
        
        Returns:
            Dict with aggregated metrics for all frameworks
            
        Raises:
            ExperimentDataError: If no valid run data found
        """
        logger.info("Analyzing experiment runs from: %s", self.runs_dir)
        
        # Find all framework directories
        framework_dirs = [d for d in self.runs_dir.iterdir() if d.is_dir()]
        if not framework_dirs:
            raise ExperimentDataError(
                message=f"No framework directories found in {self.runs_dir}",
                remediation="Ensure experiment has completed successfully"
            )
        
        logger.info("Found %d frameworks: %s", len(framework_dirs), 
                   [d.name for d in framework_dirs])
        
        # Aggregate metrics for each framework
        frameworks_data = {}
        for framework_dir in framework_dirs:
            framework_name = framework_dir.name
            aggregated = self._aggregate_framework_metrics(framework_dir)
            if aggregated:
                frameworks_data[framework_name] = aggregated
        
        if not frameworks_data:
            raise ExperimentDataError(
                message="No valid framework metrics found",
                remediation="Check that run directories contain metrics.json files"
            )
        
        # Write results to output directory
        self._write_metrics_json(frameworks_data)
        self._write_statistical_report(frameworks_data)
        
        logger.info("Analysis complete: %d frameworks analyzed", len(frameworks_data))
        
        return frameworks_data
    
    def _aggregate_framework_metrics(self, framework_dir: Path) -> Dict[str, Any]:
        """Aggregate metrics across all runs for a framework."""
        logger.debug("Analyzing framework: %s", framework_dir.name)
        
        # Find all run directories (UUIDs)
        run_dirs = [d for d in framework_dir.iterdir() if d.is_dir()]
        logger.debug("Found %d run directories for %s", len(run_dirs), framework_dir.name)
        
        # Collect metrics from all runs with their run_ids
        all_runs = []
        run_data = []  # Individual run data for statistical analysis
        
        for run_dir in run_dirs:
            metrics = self._load_run_metrics(run_dir)
            if metrics:
                all_runs.append(metrics)
                # Extract individual run data
                run_data.append({
                    "run_id": run_dir.name,
                    "execution_time": self._extract_metric_value(metrics, "duration_total"),
                    "total_cost_usd": self._extract_metric_value(metrics, "cost_total"),
                    "api_calls": self._extract_metric_value(metrics, "api_calls_total"),
                    "tokens_in": self._extract_metric_value(metrics, "tokens_in"),
                    "tokens_out": self._extract_metric_value(metrics, "tokens_out"),
                    "tokens_total": self._extract_metric_value(metrics, "tokens_total"),
                    "cached_tokens": self._extract_metric_value(metrics, "cached_tokens"),
                })
        
        if not all_runs:
            logger.warning("No valid metrics found for %s", framework_dir.name)
            return {}
        
        logger.info("Loaded %d valid runs for %s", len(all_runs), framework_dir.name)
        
        # Aggregate statistics
        aggregated = {
            "num_runs": len(all_runs),
            "runs": run_data,  # Individual run data for statistical analysis
            "execution_time": self._aggregate_metric(all_runs, "duration_total"),
            "total_cost_usd": self._aggregate_metric(all_runs, "cost_total"),
            "api_calls": self._aggregate_metric(all_runs, "api_calls_total"),
            "tokens_in": self._aggregate_metric(all_runs, "tokens_in"),
            "tokens_out": self._aggregate_metric(all_runs, "tokens_out"),
            "tokens_total": self._aggregate_metric(all_runs, "tokens_total"),
            "cached_tokens": self._aggregate_metric(all_runs, "cached_tokens"),
        }
        
        return aggregated
    
    def _load_run_metrics(self, run_dir: Path) -> Dict[str, Any]:
        """Load metrics from a single run directory."""
        metrics_file = run_dir / "metrics.json"
        if not metrics_file.exists():
            logger.debug("Metrics file not found: %s", metrics_file)
            return None
        
        try:
            with open(metrics_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Failed to load %s: %s", metrics_file, str(e))
            return None
    
    def _extract_metric_value(self, metrics: Dict[str, Any], metric_name: str) -> float:
        """Extract a single metric value from run data."""
        value = None
        
        # Try to find the metric in the run data
        if metric_name in metrics:
            value = metrics[metric_name]
        # Compute from steps for duration
        elif metric_name == "duration_total" and "steps" in metrics:
            value = sum(step.get("duration_seconds", 0) for step in metrics["steps"])
        # Get from aggregate_metrics (primary source for API/token data)
        elif "aggregate_metrics" in metrics:
            agg = metrics["aggregate_metrics"]
            if metric_name == "cost_total":
                # Calculate cost dynamically from token data using experiment's pricing
                tokens_in = agg.get("TOK_IN", 0)
                tokens_out = agg.get("TOK_OUT", 0)
                cached_tokens = agg.get("CACHED_TOKENS", 0)
                model = metrics.get("model", self.default_model)
                
                if tokens_in > 0 or tokens_out > 0:
                    value = self._calculate_cost(
                        model=model,
                        tokens_in=tokens_in,
                        tokens_out=tokens_out,
                        cached_tokens=cached_tokens
                    )
                else:
                    value = 0.0
            elif metric_name == "api_calls_total":
                value = agg.get("API_CALLS", 0)
            elif metric_name == "tokens_in":
                value = agg.get("TOK_IN", 0)
            elif metric_name == "tokens_out":
                value = agg.get("TOK_OUT", 0)
            elif metric_name == "tokens_total":
                value = agg.get("TOK_IN", 0) + agg.get("TOK_OUT", 0)
            elif metric_name == "cached_tokens":
                value = agg.get("CACHED_TOKENS", 0)
        
        return value if value is not None else 0
    
    def _calculate_cost(
        self,
        model: str,
        tokens_in: int,
        tokens_out: int,
        cached_tokens: int = 0
    ) -> float:
        """
        Calculate cost using experiment's pricing configuration.
        
        Falls back to CostCalculator if pricing not in config.
        """
        # Try to use experiment's pricing config
        if model in self.pricing_config:
            pricing = self.pricing_config[model]
            input_price = pricing.get('input_price', 0)
            cached_price = pricing.get('cached_price', 0)
            output_price = pricing.get('output_price', 0)
            
            # Calculate costs (pricing is per million tokens)
            uncached_tokens = tokens_in - cached_tokens
            uncached_input_cost = (uncached_tokens * input_price) / 1_000_000
            cached_input_cost = (cached_tokens * cached_price) / 1_000_000
            output_cost = (tokens_out * output_price) / 1_000_000
            
            return uncached_input_cost + cached_input_cost + output_cost
        else:
            # Fallback to CostCalculator with default pricing
            try:
                calculator = CostCalculator(model)
                cost_result = calculator.calculate_cost(
                    tokens_in=tokens_in,
                    tokens_out=tokens_out,
                    cached_tokens=cached_tokens
                )
                return cost_result['total_cost']
            except Exception as e:
                logger.warning(f"Failed to calculate cost for model {model}: {e}")
                return 0.0
    
    
    def _aggregate_metric(self, runs: List[Dict], metric_name: str) -> Dict[str, float]:
        """Calculate statistics for a specific metric across runs."""
        values = []
        
        for run in runs:
            # Use _extract_metric_value for consistency
            value = self._extract_metric_value(run, metric_name)
            values.append(value)
        
        if not values:
            logger.debug("No values found for metric: %s", metric_name)
            return {"mean": 0, "std": 0, "min": 0, "max": 0, "count": 0}
        
        return {
            "mean": statistics.mean(values),
            "std": statistics.stdev(values) if len(values) > 1 else 0,
            "min": min(values),
            "max": max(values),
            "count": len(values)
        }
    
    def _write_metrics_json(self, frameworks_data: Dict[str, Any]):
        """Write aggregated metrics to JSON file."""
        output_file = self.output_dir / "metrics.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(frameworks_data, f, indent=2)
        
        logger.info("Metrics written to: %s", output_file)
    
    def _write_statistical_report(self, frameworks_data: Dict[str, Any]):
        """Generate statistical analysis report in Markdown."""
        output_file = self.output_dir / "statistical_report.md"
        
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
            if "tokens_in" in data:
                tokens_in = data["tokens_in"]
                report.append(f"| {framework} | Tokens In | {tokens_in['mean']:.0f} | {tokens_in['std']:.0f} |")
            if "tokens_out" in data:
                tokens_out = data["tokens_out"]
                report.append(f"| {framework} | Tokens Out | {tokens_out['mean']:.0f} | {tokens_out['std']:.0f} |")
            if "cached_tokens" in data:
                cached = data["cached_tokens"]
                report.append(f"| {framework} | Cached Tokens | {cached['mean']:.0f} | {cached['std']:.0f} |")
            if "tokens_total" in data:
                tokens = data["tokens_total"]
                report.append(f"| {framework} | Total Tokens | {tokens['mean']:.0f} | {tokens['std']:.0f} |")
        
        report.append("\n## Key Findings\n")
        report.append(f"- Comparative analysis across {len(frameworks_data)} frameworks\n")
        report.append("- Statistical significance tests would require additional analysis\n")
        report.append("- Data collected from raw experiment runs\n")
        
        # Write report
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        
        logger.info("Statistical report written to: %s", output_file)
