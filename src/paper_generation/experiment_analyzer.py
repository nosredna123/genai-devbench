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
from src.utils.statistical_helpers import format_pvalue
from .statistical_analyzer import StatisticalAnalyzer
from .statistical_visualizations import StatisticalVisualizationGenerator
from .educational_content import EducationalContentGenerator

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
        
        # T033: Perform statistical analysis
        logger.info("Performing comprehensive statistical analysis...")
        
        # Initialize statistical analyzers
        statistical_analyzer = StatisticalAnalyzer(alpha=0.05, random_seed=42)
        viz_generator = StatisticalVisualizationGenerator(output_dir=str(self.output_dir))
        educational_generator = EducationalContentGenerator(reading_level=8)
        
        # Perform statistical analysis
        statistical_findings = statistical_analyzer.analyze_experiment(frameworks_data)
        
        # Generate visualizations
        visualizations = viz_generator.generate_all_visualizations(statistical_findings)
        
        # Update findings with visualization data (flatten dict to list)
        statistical_findings.visualizations = [
            viz for viz_list in visualizations.values() for viz in viz_list
        ]
        
        # Generate statistical reports
        logger.info("Generating statistical reports...")
        self._generate_statistical_report_summary(statistical_findings, educational_generator)
        self._generate_statistical_report_full(statistical_findings, educational_generator)
        
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
        skipped_unverified = 0
        
        for run_dir in run_dirs:
            metrics = self._load_run_metrics(run_dir)
            if metrics:
                # Check verification status - only include verified runs
                if self._is_run_verified(metrics):
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
                else:
                    skipped_unverified += 1
                    logger.debug("Skipped unverified run: %s", run_dir.name)
        
        if not all_runs:
            logger.warning("No valid metrics found for %s", framework_dir.name)
            return {}
        
        if skipped_unverified > 0:
            logger.info("Loaded %d verified runs for %s (skipped %d unverified)", 
                       len(all_runs), framework_dir.name, skipped_unverified)
        else:
            logger.info("Loaded %d verified runs for %s", len(all_runs), framework_dir.name)
        
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
    
    def _is_run_verified(self, metrics: Dict[str, Any]) -> bool:
        """
        Check if a run has been verified through usage API reconciliation.
        
        A run is considered verified if:
        - usage_api_reconciliation.verification_status == "verified"
        
        Args:
            metrics: Run metrics dictionary
            
        Returns:
            True if run is verified, False otherwise
        """
        if "usage_api_reconciliation" not in metrics:
            return False
        
        reconciliation = metrics["usage_api_reconciliation"]
        verification_status = reconciliation.get("verification_status", "")
        
        return verification_status == "verified"
    
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
    
    def _generate_statistical_report_summary(
        self,
        findings,  # StatisticalFindings
        educational_content  # EducationalContentGenerator
    ) -> None:
        """
        Generate statistical_report_summary.md (T034).
        
        Creates a concise summary report (<300 lines) with:
        - Quick Start Guide
        - Executive Summary
        - Key Findings (with effect sizes)
        - Critical Visualizations (3-5 embedded)
        - Power Recommendations
        
        Args:
            findings: StatisticalFindings from analysis
            educational_content: EducationalContentGenerator for explanations
        """
        output_file = self.output_dir / "statistical_report_summary.md"
        
        sections = []
        
        # Quick Start Guide
        sections.append(educational_content.generate_quick_start_guide(findings))
        sections.append("\n---\n")
        
        # Executive Summary
        sections.append("## Executive Summary\n")
        sections.append(f"**Experiment**: {findings.experiment_name}\n")
        sections.append(f"**Analysis Date**: {findings.timestamp}\n")
        sections.append(f"**Frameworks Analyzed**: {len(set(d.group_name for d in findings.distributions))}\n")
        sections.append(f"**Metrics Analyzed**: {len(findings.metrics_analyzed)}\n")
        sections.append(f"**Statistical Tests**: {len(findings.statistical_tests)}\n")
        sections.append(f"**Significant Results**: {findings.n_significant_tests}\n")
        sections.append(f"**Large Effects**: {findings.n_large_effects}\n\n")
        
        # Key Findings
        sections.append("## 📊 Key Findings\n\n")
        
        for test in findings.statistical_tests:
            sections.append(f"### {test.metric_name}\n\n")
            sections.append(f"**Test Used**: {test.test_type.value}\n\n")
            sections.append(f"**Result**: {'✅ Significant' if test.is_significant else '❌ Not Significant'} ({format_pvalue(test.p_value)})\n\n")
            sections.append(f"{test.interpretation}\n\n")
            
            # Add corresponding effect sizes
            metric_effects = [e for e in findings.effect_sizes if e.metric_name == test.metric_name]
            if metric_effects:
                sections.append("**Effect Sizes**:\n\n")
                for effect in metric_effects:
                    comparison = f"{effect.group1} vs {effect.group2}"
                    sections.append(
                        f"- {comparison}: {effect.measure.value} = {effect.value:.3f} "
                        f"({effect.magnitude}, 95% CI: [{effect.ci_lower:.3f}, {effect.ci_upper:.3f}])\n"
                    )
                sections.append("\n")
        
        # Critical Visualizations (top 3-5)
        sections.append("## 📈 Critical Visualizations\n\n")
        
        # Select up to 5 most important visualizations
        viz_priority = []
        for metric in findings.metrics_analyzed[:2]:  # Top 2 metrics
            # Box plot
            box_plots = [v for v in findings.visualizations 
                        if v.viz_type.value == 'boxplot' and v.metric_name == metric]
            if box_plots:
                viz_priority.append(box_plots[0])
            
            # Forest plot
            forest_plots = [v for v in findings.visualizations 
                           if v.viz_type.value == 'effect_forest' and v.metric_name == metric]
            if forest_plots:
                viz_priority.append(forest_plots[0])
        
        for viz in viz_priority[:5]:
            # Make path relative to output_dir
            rel_path = Path(viz.file_path).relative_to(self.output_dir)
            sections.append(f"### {viz.title}\n\n")
            sections.append(f"![{viz.caption}]({rel_path})\n\n")
            sections.append(f"*{viz.caption}*\n\n")
        
        # Power Recommendations
        if findings.power_warnings:
            sections.append("## ⚠️ Power Analysis & Recommendations\n\n")
            for warning in findings.power_warnings:
                sections.append(f"- {warning}\n")
            sections.append("\n")
        
        # Write report
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(''.join(sections))
        
        logger.info("Summary report written to: %s", output_file)
    
    # T031-T033: Power analysis section generation
    def _generate_power_analysis_section(
        self,
        findings,  # StatisticalFindings
        educational_content  # EducationalContentGenerator
    ) -> str:
        """
        Generate Power Analysis section with tables and recommendations.
        
        Creates:
        - Introduction to power analysis
        - Power analysis results table (T032)
        - Sample size recommendations table (T033)
        - Educational content
        
        Args:
            findings: StatisticalFindings with statistical_tests
            educational_content: EducationalContentGenerator for explanations
        
        Returns:
            Formatted markdown string for Section 5
        """
        sections = []
        
        # Introduction
        sections.append("Statistical power is the probability of detecting a true effect when it exists. ")
        sections.append("By convention, power ≥ 0.80 (80%) is considered adequate, meaning there is at least ")
        sections.append("an 80% chance of detecting a real difference if one exists.\n\n")
        
        # Check if we have tests with power information
        tests_with_power = [t for t in findings.statistical_tests 
                           if hasattr(t, 'achieved_power') and t.achieved_power is not None]
        
        if not tests_with_power:
            sections.append("*No power analysis available for this experiment.*\n\n")
            return ''.join(sections)
        
        # T032: Power Analysis Results Table
        sections.append("### Power Analysis Results\n\n")
        sections.append("This table shows the achieved statistical power for each comparison, ")
        sections.append("indicating the reliability of the test results.\n\n")
        
        sections.append("| Comparison | Metric | Test Type | Effect Size | Achieved Power | Adequacy | Status |\n")
        sections.append("|------------|--------|-----------|-------------|----------------|----------|--------|\n")
        
        inadequate_tests = []
        
        for test in tests_with_power:
            # Build comparison string
            if len(test.groups) == 2:
                comparison = f"{test.groups[0]} vs {test.groups[1]}"
            else:
                comparison = f"{len(test.groups)} groups"
            
            # Format test type
            test_type_display = test.test_type.value.replace('_', ' ').title()
            
            # Get effect size from statistical tests (use statistic as proxy if needed)
            effect_size_str = "N/A"
            if hasattr(test, 'effect_size'):
                effect_size_str = f"{test.effect_size:.3f}"
            
            # Format power
            if test.achieved_power is not None:
                power_str = f"{test.achieved_power:.3f}"
                
                # Determine adequacy
                if test.achieved_power >= 0.80:
                    adequacy = "Adequate"
                    status = "✅"
                elif test.achieved_power >= 0.50:
                    adequacy = "Marginal"
                    status = "⚠️"
                    inadequate_tests.append(test)
                else:
                    adequacy = "Inadequate"
                    status = "❌"
                    inadequate_tests.append(test)
            else:
                power_str = "N/A"
                adequacy = "Indeterminate"
                status = "❓"
            
            sections.append(
                f"| {comparison} | {test.metric_name} | {test_type_display} | "
                f"{effect_size_str} | {power_str} | {adequacy} | {status} |\n"
            )
        
        sections.append("\n")
        
        # T033: Sample Size Recommendations
        if inadequate_tests:
            sections.append("### Sample Size Recommendations\n\n")
            sections.append("The following comparisons have inadequate or marginal power (< 0.80). ")
            sections.append("To achieve 80% power, consider increasing sample sizes as recommended:\n\n")
            
            sections.append("| Comparison | Metric | Current n | Achieved Power | Recommended n | Additional Runs Needed |\n")
            sections.append("|------------|--------|-----------|----------------|---------------|------------------------|\n")
            
            for test in inadequate_tests:
                if not hasattr(test, 'recommended_n') or test.recommended_n is None:
                    continue
                
                # Build comparison string
                if len(test.groups) == 2:
                    comparison = f"{test.groups[0]} vs {test.groups[1]}"
                    # Get current sample sizes
                    current_n = len(test.group_data[test.groups[0]])
                else:
                    comparison = f"{len(test.groups)} groups"
                    # Average sample size
                    current_n = int(sum(len(vals) for vals in test.group_data.values()) / len(test.groups))
                
                power_str = f"{test.achieved_power:.3f}" if test.achieved_power else "N/A"
                additional = max(0, test.recommended_n - current_n)
                
                sections.append(
                    f"| {comparison} | {test.metric_name} | {current_n} | "
                    f"{power_str} | {test.recommended_n} | {additional} |\n"
                )
            
            sections.append("\n")
            sections.append("**Note**: Recommended sample sizes assume equal group sizes and are calculated ")
            sections.append("to achieve 80% power at α = 0.05. Actual requirements may vary based on ")
            sections.append("effect size stability and data characteristics.\n\n")
        else:
            sections.append("### ✅ All Comparisons Adequately Powered\n\n")
            sections.append("All statistical comparisons have achieved power ≥ 0.80, indicating ")
            sections.append("sufficient sample size to reliably detect true effects.\n\n")
        
        # Educational content
        if findings.power_analyses and len(findings.power_analyses) > 0:
            sections.append("### Understanding Power Analysis\n\n")
            # Use the first power analysis for educational explanation
            sections.append(educational_content.explain_power_analysis(findings.power_analyses[0]))
            sections.append("\n")
        
        return ''.join(sections)
    
    def _generate_statistical_report_full(
        self,
        findings,  # StatisticalFindings
        educational_content  # EducationalContentGenerator
    ) -> None:
        """
        Generate statistical_report_full.md (T035).
        
        Creates a comprehensive report (800-1200 lines) with:
        - Quick Start Guide
        - Descriptive Statistics (with skew/kurtosis)
        - Normality Assessment (with Q-Q plots)
        - Assumption Validation (Levene)
        - Statistical Comparisons (tests + effect sizes)
        - Power Analysis
        - Statistical Methodology
        - Glossary
        
        Args:
            findings: StatisticalFindings from analysis
            educational_content: EducationalContentGenerator for explanations
        """
        output_file = self.output_dir / "statistical_report_full.md"
        
        sections = []
        
        # Quick Start Guide
        sections.append(educational_content.generate_quick_start_guide(findings))
        sections.append("\n---\n")
        
        # Table of Contents
        sections.append("## Table of Contents\n\n")
        sections.append("1. [Descriptive Statistics](#descriptive-statistics)\n")
        sections.append("2. [Normality Assessment](#normality-assessment)\n")
        sections.append("3. [Assumption Validation](#assumption-validation)\n")
        sections.append("4. [Statistical Comparisons](#statistical-comparisons)\n")
        # DISABLED: Power Analysis section removed (post-hoc power is statistically problematic)
        # sections.append("5. [Power Analysis](#power-analysis)\n")
        sections.append("5. [Statistical Methodology](#statistical-methodology)\n")
        sections.append("6. [Glossary](#glossary)\n\n")
        sections.append("---\n\n")
        
        # 1. Descriptive Statistics
        sections.append("## 1. Descriptive Statistics\n\n")
        
        for metric in findings.metrics_analyzed:
            metric_dists = [d for d in findings.distributions if d.metric_name == metric]
            if not metric_dists:
                continue
            
            sections.append(f"### {metric}\n\n")
            sections.append("| Framework | n | Mean | Median | Std Dev | Min | Max | Q1 | Q3 | IQR | Skewness | Kurtosis | Outliers |\n")
            sections.append("|-----------|---|------|--------|---------|-----|-----|----|----|-----|----------|----------|----------|\n")
            
            for dist in metric_dists:
                iqr = dist.q3 - dist.q1
                
                # T054-T055: Bold primary summary based on skewness (FR-032)
                if dist.primary_summary == "median":
                    # Bold median and IQR for skewed distributions
                    sections.append(
                        f"| {dist.group_name} | {dist.n_samples} | {dist.mean:.2f} | **{dist.median:.2f}** | "
                        f"{dist.std_dev:.2f} | {dist.min_value:.2f} | {dist.max_value:.2f} | {dist.q1:.2f} | "
                        f"{dist.q3:.2f} | **{iqr:.2f}** | {dist.skewness:.2f} | {dist.kurtosis:.2f} | "
                        f"{dist.n_outliers} |\n"
                    )
                else:
                    # Bold mean and SD for normally distributed data
                    sections.append(
                        f"| {dist.group_name} | {dist.n_samples} | **{dist.mean:.2f}** | {dist.median:.2f} | "
                        f"**{dist.std_dev:.2f}** | {dist.min_value:.2f} | {dist.max_value:.2f} | {dist.q1:.2f} | "
                        f"{dist.q3:.2f} | {iqr:.2f} | {dist.skewness:.2f} | {dist.kurtosis:.2f} | "
                        f"{dist.n_outliers} |\n"
                    )
            sections.append("\n")
            
            # T058: Add skewness warning for severely skewed distributions (FR-034)
            severe_skew_dists = [d for d in metric_dists if d.skewness_flag == "severe"]
            if severe_skew_dists:
                sections.append("**⚠️ Note on Skewness**: ")
                sections.append(f"This metric shows severe skewness (|skewness| > 2.0) for some frameworks. ")
                sections.append("**Median and IQR are emphasized** (shown in bold) as they are more robust ")
                sections.append("to outliers and extreme values than mean and standard deviation. ")
                sections.append("The median represents the center of the distribution, while IQR captures ")
                sections.append("the spread of the middle 50% of values.\n\n")
            
            # T056-T057: Add interpretation text mentioning appropriate summary first (FR-033)
            for dist in metric_dists:
                if dist.primary_summary == "median":
                    # Mention median first for skewed distributions
                    sections.append(f"**{dist.group_name}**: ")
                    sections.append(f"The median value is {dist.median:.2f} with an IQR of {dist.q3 - dist.q1:.2f}, ")
                    sections.append(f"indicating typical performance and variability. ")
                    sections.append(f"(Mean: {dist.mean:.2f}, SD: {dist.std_dev:.2f}). ")
                    sections.append(f"*{dist.summary_explanation}*\n\n")
                else:
                    # Mention mean first for normally distributed data
                    sections.append(f"**{dist.group_name}**: ")
                    sections.append(f"The mean value is {dist.mean:.2f} (SD: {dist.std_dev:.2f}), ")
                    sections.append(f"with a median of {dist.median:.2f} and IQR of {dist.q3 - dist.q1:.2f}. ")
                    sections.append(f"*{dist.summary_explanation}*\n\n")
        
        # 2. Normality Assessment
        sections.append("## 2. Normality Assessment\n\n")
        sections.append("### Shapiro-Wilk Test Results\n\n")
        
        normality_checks = [a for a in findings.assumption_checks 
                           if a.test_type.value == 'shapiro_wilk']
        
        if normality_checks:
            sections.append("| Metric | Framework | W-statistic | p-value | Result | Interpretation |\n")
            sections.append("|--------|-----------|-------------|---------|--------|----------------|\n")
            
            for check in normality_checks:
                result = "✅ Normal" if check.passes else "❌ Non-normal"
                sections.append(
                    f"| {check.metric_name} | {', '.join(check.groups_tested)} | "
                    f"{check.statistic:.4f} | {format_pvalue(check.p_value)} | {result} | "
                    f"{check.interpretation} |\n"
                )
            sections.append("\n")
        
        # Q-Q Plots
        qq_plots = [v for v in findings.visualizations if v.viz_type.value == 'qq']
        if qq_plots:
            sections.append("### Q-Q Plots\n\n")
            for viz in qq_plots:
                rel_path = Path(viz.file_path).relative_to(self.output_dir)
                sections.append(f"![{viz.caption}]({rel_path})\n\n")
        
        # 3. Assumption Validation
        sections.append("## 3. Assumption Validation\n\n")
        
        variance_checks = [a for a in findings.assumption_checks 
                          if a.test_type.value == 'levene']
        
        if variance_checks:
            sections.append("### Levene's Test (Variance Homogeneity)\n\n")
            sections.append("| Metric | Frameworks | W-statistic | p-value | Result | Recommendation |\n")
            sections.append("|--------|------------|-------------|---------|--------|----------------|\n")
            
            for check in variance_checks:
                result = "✅ Equal variances" if check.passes else "❌ Unequal variances"
                recommendation = check.recommendation if check.recommendation else "N/A"
                sections.append(
                    f"| {check.metric_name} | {', '.join(check.groups_tested)} | "
                    f"{check.statistic:.4f} | {format_pvalue(check.p_value)} | {result} | "
                    f"{recommendation} |\n"
                )
            sections.append("\n")
        
        # 4. Statistical Comparisons
        sections.append("## 4. Statistical Comparisons\n\n")
        
        # T047: Check if multiple comparison correction was applied (FR-024)
        correction_applied = any(
            hasattr(test, 'correction_method') and test.correction_method != "none" 
            for test in findings.statistical_tests
        )
        
        if correction_applied:
            sections.append("**Note**: Multiple comparison correction applied. ")
            sections.append("Both raw and adjusted p-values are reported below.\n\n")
        
        for test in findings.statistical_tests:
            sections.append(f"### {test.metric_name}\n\n")
            
            # T047: Display both raw and adjusted p-values when correction applied (FR-023, FR-024)
            if hasattr(test, 'pvalue_raw') and hasattr(test, 'pvalue_adjusted'):
                if test.correction_method != "none":
                    sections.append(f"**Raw p-value**: {format_pvalue(test.pvalue_raw)}\n\n")
                    sections.append(f"**Adjusted p-value**: {format_pvalue(test.pvalue_adjusted)} ({test.correction_method})\n\n")
                    sections.append(f"**Significance**: Based on adjusted p-value\n\n")
            
            # Test explanation
            sections.append(educational_content.explain_statistical_test(test))
            sections.append("\n")
            
            # Effect sizes for this metric
            metric_effects = [e for e in findings.effect_sizes if e.metric_name == test.metric_name]
            if metric_effects:
                sections.append("#### Effect Sizes\n\n")
                for effect in metric_effects:
                    sections.append(educational_content.explain_effect_size(effect))
                    sections.append("\n")
            
            # Forest plot if available
            forest_plots = [v for v in findings.visualizations 
                           if v.viz_type.value == 'forest' and v.metric_name == test.metric_name]
            if forest_plots:
                viz = forest_plots[0]
                rel_path = Path(viz.file_path).relative_to(self.output_dir)
                sections.append(f"![{viz.caption}]({rel_path})\n\n")
        
        # 5. Power Analysis (T031-T033)
        # DISABLED: Post-hoc power analysis removed per expert statistical review
        # Post-hoc power (calculated from observed data) is directly correlated with p-values
        # and provides no independent information about study adequacy.
        # Recommendation: Use a priori power analysis for prospective study planning instead.
        # Code kept for backward compatibility but section excluded from report output.
        # See: docs/STATISTICAL_FIXES_NEEDED.md for detailed rationale
        # sections.append("## 5. Power Analysis\n\n")
        # sections.append(self._generate_power_analysis_section(findings, educational_content))
        # sections.append("\n")
        
        # 5. Statistical Methodology (renumbered from 6 after removing Power Analysis)
        sections.append("## 5. Statistical Methodology\n\n")
        sections.append(findings.methodology_text)
        sections.append("\n\n")
        
        # Add practical significance interpretation guidance
        sections.append("### Interpreting Statistical vs. Practical Significance\n\n")
        sections.append(
            "Statistical significance (p-value < 0.05) indicates that an observed difference "
            "is unlikely to be due to random chance alone. However, **statistical significance "
            "does not automatically imply practical importance**.\n\n"
        )
        sections.append(
            "**Effect sizes** provide the magnitude of differences and should be considered alongside "
            "p-values when evaluating practical significance:\n\n"
        )
        sections.append("- **Cohen's d**: |d| < 0.2 negligible, 0.2-0.5 small, 0.5-0.8 medium, >0.8 large\n")
        sections.append("- **Cliff's Delta**: |δ| < 0.147 negligible, 0.147-0.33 small, 0.33-0.474 medium, >0.474 large\n\n")
        sections.append(
            "For performance benchmarks, even small effect sizes may be practically meaningful "
            "if they translate to measurable improvements in real-world applications. "
            "Conversely, large effect sizes on metrics with zero or near-zero variance "
            "(e.g., cached tokens that are always identical) may reflect data characteristics "
            "rather than meaningful performance differences.\n\n"
        )
        sections.append(
            "**Recommendation**: Consider both statistical significance, effect size magnitude, "
            "and domain-specific context when drawing conclusions about framework performance.\n\n"
        )
        
        # Reproducibility Information
        sections.append("### Reproducibility Information\n\n")
        sections.append("| Parameter | Value |\n")
        sections.append("|-----------|-------|\n")
        for key, value in findings.metadata.items():
            sections.append(f"| {key} | {value} |\n")
        sections.append("\n")
        
        # 6. Glossary (renumbered from 7 after removing Power Analysis)
        sections.append("## 6. Glossary\n\n")
        sections.append(educational_content.generate_glossary())
        sections.append("\n")
        
        # Write report
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(''.join(sections))
        
        logger.info("Full report written to: %s (%d chars)", 
                   output_file, len(''.join(sections)))

