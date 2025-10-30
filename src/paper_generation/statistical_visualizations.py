"""
Statistical Visualization Generator for Enhanced Statistical Reports

This module generates publication-quality statistical visualizations as SVG files:
- Box plots: Show median, quartiles, whiskers, outliers
- Violin plots: Show distribution shapes with kernel density estimation
- Forest plots: Show effect sizes with confidence intervals
- Q-Q plots: Assess normality with Shapiro-Wilk p-values

Design: Part of spec 011-enhance-statistical-report, Phase 6 (US3A Visualizations P2)
Tasks: T022-T027
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import warnings

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server/script use
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy import stats

from src.utils.statistical_helpers import format_pvalue
from .statistical_analyzer import (
    MetricDistribution,
    EffectSize,
    AssumptionCheck,
    Visualization,
    VisualizationType,
    TestType,
)
from .models import (
    RegressionResult,
    RankData,
    StabilityMetric,
    OutlierInfo,
)


class StatisticalVisualizationGenerator:
    """
    Generates publication-quality statistical visualizations for experiment analysis.
    
    All plots are saved as SVG files for inclusion in papers/reports.
    Uses colorblind-friendly palettes and publication styling.
    
    Attributes:
        output_dir: Base directory for visualization output
        style: Matplotlib/seaborn style (default: seaborn colorblind palette)
        fig_dir: Full path to figures/statistical/ subdirectory
    """
    
    def __init__(self, output_dir: str, style: str = "seaborn-v0_8-colorblind"):
        """
        Initialize visualization generator.
        
        Args:
            output_dir: Base output directory (e.g., 'tmp/test_paper2/')
            style: Matplotlib style preset
        """
        self.output_dir = Path(output_dir)
        self.style = style
        self.fig_dir = self.output_dir / "figures" / "statistical"
        
        # Create output directory
        self.fig_dir.mkdir(parents=True, exist_ok=True)
        
        # Apply publication styling
        self._apply_publication_styling()
    
    def _apply_publication_styling(self):
        """Configure matplotlib/seaborn for publication-quality output (T022)."""
        # Set style
        try:
            plt.style.use(self.style)
        except:
            # Fallback to default if style not available
            warnings.warn(f"Style '{self.style}' not available, using default")
        
        # Set seaborn context and palette
        sns.set_context("paper", font_scale=1.2)
        sns.set_palette("colorblind")
        
        # Configure matplotlib rcParams for publications
        plt.rcParams.update({
            'figure.figsize': (8, 6),
            'figure.dpi': 100,
            'savefig.dpi': 300,
            'savefig.format': 'svg',
            'savefig.bbox': 'tight',
            'font.family': 'sans-serif',
            'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica'],
            'font.size': 10,
            'axes.labelsize': 11,
            'axes.titlesize': 12,
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            'legend.fontsize': 10,
            'legend.frameon': True,
            'legend.framealpha': 0.9,
            'axes.grid': True,
            'grid.alpha': 0.3,
            'axes.axisbelow': True,
        })
    
    def _validate_output_path(self, output_path: str) -> Path:
        """
        Validate and return absolute output path (T022).
        
        Args:
            output_path: Relative or absolute path to output file
            
        Returns:
            Absolute Path object
        """
        path = Path(output_path)
        if not path.is_absolute():
            path = self.fig_dir / path
        
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        return path
    
    def _format_metric_label(self, metric_name: str) -> str:
        """
        Format metric name for axis labels with units (T008, T022).
        
        Args:
            metric_name: Raw metric name (e.g., 'execution_time')
            
        Returns:
            Formatted label with units (e.g., 'Execution Time (seconds)')
        """
        # Common metric name mappings
        label_map = {
            'execution_time': 'Execution Time (seconds)',
            'api_calls': 'API Calls (count)',
            'tokens_used': 'Tokens Used (count)',
            'tokens_in': 'Input Tokens (count)',
            'tokens_out': 'Output Tokens (count)',
            'tokens_total': 'Total Tokens (count)',
            'cached_tokens': 'Cached Tokens (count)',
            'total_cost_usd': 'Total Cost (USD)',
            'cost': 'Cost (USD)',
            'success_rate': 'Success Rate (%)',
            'memory_usage': 'Memory Usage (MB)',
            'response_time': 'Response Time (ms)',
        }
        
        # Return mapped label or title-case the metric name
        return label_map.get(metric_name, metric_name.replace('_', ' ').title())
    
    def _magnitude_to_color(self, magnitude: str) -> str:
        """
        Map effect size magnitude to color for visualizations (T007, T022).
        
        Uses WCAG 2.1 colorblind-accessible palette per FR-017.
        Color scheme: gray=negligible, green=small, orange=medium, red=large
        
        Args:
            magnitude: Effect size magnitude ('negligible', 'small', 'medium', 'large')
            
        Returns:
            Hex color code
        """
        color_map = {
            'negligible': '#999999',  # Gray
            'small': '#77DD77',       # Pastel green  
            'medium': '#FFB347',      # Pastel orange
            'large': '#FF6961',       # Pastel red
        }
        return color_map.get(magnitude.lower(), '#999999')
    
    def generate_box_plot(
        self,
        metric_name: str,
        distributions: List[MetricDistribution]
    ) -> Visualization:
        """
        Generate box plot showing distribution comparison (T023).
        
        Box plot shows:
        - Median (line inside box)
        - Q1 and Q3 (box edges)
        - Whiskers (1.5×IQR)
        - Outliers (individual points)
        
        Args:
            metric_name: Name of metric being plotted
            distributions: List of MetricDistribution objects (one per framework)
            
        Returns:
            Visualization metadata object
        """
        _, ax = plt.subplots(figsize=(8, 6))
        
        # Prepare data
        data = [dist.values for dist in distributions]
        labels = [dist.group_name for dist in distributions]
        
        # Feature 013: Detect zero-variance distributions using relative thresholds
        zero_variance_detected = []
        for i, dist in enumerate(distributions):
            # Exact zero check
            if dist.std_dev == 0.0 or len(set(dist.values)) == 1:
                zero_variance_detected.append(i)
                continue
            
            # Relative variance check (coefficient of variation < 1%)
            iqr = dist.q3 - dist.q1
            relative_std = abs(dist.std_dev / dist.mean) if dist.mean != 0 else float('inf')
            relative_iqr = abs(iqr / dist.median) if dist.median != 0 else float('inf')
            
            # Only flag as zero-variance if BOTH relative measures < 1%
            if relative_std < 0.01 and relative_iqr < 0.01:
                zero_variance_detected.append(i)
        
        # Create box plot only for distributions with variance
        normal_data = [data[i] for i in range(len(data)) if i not in zero_variance_detected]
        normal_labels = [labels[i] for i in range(len(labels)) if i not in zero_variance_detected]
        
        if normal_data:
            bp = ax.boxplot(
                normal_data,
                labels=normal_labels,
                patch_artist=True,
                showfliers=True,
                notch=False,
                widths=0.6,
            )
            
            # Color boxes with colorblind-friendly palette
            colors = sns.color_palette("colorblind", len(normal_data))
            for patch, color in zip(bp['boxes'], colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)
            
            # Style whiskers, caps, medians
            for element in ['whiskers', 'caps']:
                plt.setp(bp[element], color='black', linewidth=1.2)
            plt.setp(bp['medians'], color='darkred', linewidth=2)
            plt.setp(bp['fliers'], marker='o', markerfacecolor='red', 
                     markersize=5, alpha=0.6, markeredgecolor='darkred')
        
        # Feature 013: Add visual indicators for zero-variance distributions
        if zero_variance_detected:
            # Build complete label list for x-axis
            all_positions = []
            all_labels = []
            
            # Add normal data positions and labels
            if normal_data:
                all_positions.extend(range(1, len(normal_data) + 1))
                all_labels.extend(normal_labels)
            
            # Add zero-variance indicators
            for i, idx in enumerate(zero_variance_detected):
                dist = distributions[idx]
                x_pos = len(normal_data) + i + 1
                
                # Draw horizontal line at mean
                ax.hlines(
                    y=dist.mean,
                    xmin=x_pos - 0.3,
                    xmax=x_pos + 0.3,
                    color='red',
                    linewidth=3,
                    label='Zero Variance' if i == 0 else ""
                )
                
                # Add annotation
                ax.annotate(
                    'No variation',
                    xy=(x_pos, dist.mean),
                    xytext=(x_pos + 0.4, dist.mean),
                    fontsize=8,
                    color='red',
                    ha='left',
                    va='center'
                )
                
                # Add to label lists
                all_positions.append(x_pos)
                all_labels.append(labels[idx])
            
            # Set all labels at once (avoids mismatch)
            ax.set_xticks(all_positions)
            ax.set_xticklabels(all_labels)
        
        # Labels and title
        ax.set_ylabel(self._format_metric_label(metric_name))
        ax.set_xlabel('Framework')
        ax.set_title(f'Distribution Comparison: {self._format_metric_label(metric_name)}')
        
        # Grid
        ax.yaxis.grid(True, alpha=0.3)
        ax.set_axisbelow(True)
        
        # Feature 013: Add legend if zero-variance detected
        if zero_variance_detected:
            ax.legend(loc='best', fontsize=8)
        
        # Save
        output_filename = f"box_plot_{metric_name}.svg"
        output_path = self._validate_output_path(output_filename)
        plt.savefig(output_path, format='svg', bbox_inches='tight')
        plt.close()
        
        # Create title and caption
        title = f'Distribution Comparison: {self._format_metric_label(metric_name)}'
        caption = (
            f"Box plot comparing {self._format_metric_label(metric_name)} across frameworks. "
            f"Box shows median (red line) and quartiles (Q1-Q3). "
            f"Whiskers extend to 1.5×IQR. Red dots indicate outliers."
        )
        
        # Feature 013: Update caption if zero-variance detected
        if zero_variance_detected:
            caption += (
                " Red horizontal lines indicate distributions with zero variance (no variation in values)."
            )
        
        return Visualization(
            viz_type=VisualizationType.BOXPLOT,
            metric_name=metric_name,
            file_path=output_path,
            format="svg",
            title=title,
            caption=caption,
            groups=[d.group_name for d in distributions],
        )
    
    def generate_violin_plot(
        self,
        metric_name: str,
        distributions: List[MetricDistribution]
    ) -> Visualization:
        """
        Generate violin plot showing distribution shapes (T024).
        
        Violin plot shows:
        - Kernel density estimation (shape)
        - Quartile lines (inner='quartile')
        - Full data distribution
        
        Args:
            metric_name: Name of metric being plotted
            distributions: List of MetricDistribution objects
            
        Returns:
            Visualization metadata object
        """
        _, ax = plt.subplots(figsize=(8, 6))
        
        # Prepare data for seaborn
        import pandas as pd
        
        data_list = []
        for dist in distributions:
            for value in dist.values:
                data_list.append({
                    'Framework': dist.group_name,
                    'Value': value,
                })
        
        df = pd.DataFrame(data_list)
        
        # Create violin plot
        sns.violinplot(
            data=df,
            x='Framework',
            y='Value',
            palette='colorblind',
            inner='quartile',  # Show quartile lines
            ax=ax,
        )
        
        # Labels and title
        ax.set_ylabel(self._format_metric_label(metric_name))
        ax.set_xlabel('Framework')
        ax.set_title(f'Distribution Shape: {self._format_metric_label(metric_name)}')
        
        # Grid
        ax.yaxis.grid(True, alpha=0.3)
        ax.set_axisbelow(True)
        
        # Save
        output_filename = f"violin_plot_{metric_name}.svg"
        output_path = self._validate_output_path(output_filename)
        plt.savefig(output_path, format='svg', bbox_inches='tight')
        plt.close()
        
        # Create title and caption
        title = f'Distribution Shape: {self._format_metric_label(metric_name)}'
        caption = (
            f"Violin plot showing {self._format_metric_label(metric_name)} distribution shapes. "
            f"Width indicates density at each value. Inner lines show quartiles (Q1, median, Q3)."
        )
        
        return Visualization(
            viz_type=VisualizationType.VIOLIN,
            metric_name=metric_name,
            file_path=output_path,
            format="svg",
            title=title,
            caption=caption,
            groups=[d.group_name for d in distributions],
        )
    
    def generate_forest_plot(
        self,
        metric_name: str,
        effect_sizes: List[EffectSize]
    ) -> Visualization:
        """
        Generate forest plot showing effect sizes with confidence intervals (T025).
        
        Forest plot shows:
        - Point estimates (markers)
        - 95% confidence intervals (error bars)
        - Reference line at 0 (no effect)
        - Color coding by magnitude
        
        Args:
            metric_name: Name of metric being compared
            effect_sizes: List of EffectSize objects
            
        Returns:
            Visualization metadata object
        """
        _, ax = plt.subplots(figsize=(10, max(6, len(effect_sizes) * 0.8)))
        
        # Prepare data
        y_positions = np.arange(len(effect_sizes))
        values = [es.value for es in effect_sizes]
        ci_lowers = [es.ci_lower for es in effect_sizes]
        ci_uppers = [es.ci_upper for es in effect_sizes]
        labels = [f"{es.group1} vs {es.group2}" for es in effect_sizes]
        colors = [self._magnitude_to_color(es.magnitude) for es in effect_sizes]
        
        # Calculate error bar lengths (must be positive)
        errors_lower = [abs(values[i] - ci_lowers[i]) for i in range(len(values))]
        errors_upper = [abs(ci_uppers[i] - values[i]) for i in range(len(values))]
        
        # Feature 013: Detect deterministic CIs (complete separation)
        deterministic_ci_detected = []
        for i, es in enumerate(effect_sizes):
            if abs(es.value) == 1.0 and es.ci_lower == es.ci_upper:
                deterministic_ci_detected.append(i)
        
        # Plot horizontal error bars
        for i, (y, val, err_low, err_up, color, es) in enumerate(
            zip(y_positions, values, errors_lower, errors_upper, colors, effect_sizes)
        ):
            # Feature 013: Use different styling for deterministic CIs
            if i in deterministic_ci_detected:
                # Complete separation: open marker, red edge, larger size
                ax.errorbar(
                    val, y,
                    xerr=[[err_low], [err_up]],
                    fmt='o',
                    markersize=12,
                    markerfacecolor='none',
                    markeredgecolor='red',
                    markeredgewidth=2.5,
                    ecolor='red',
                    capsize=5,
                    capthick=2,
                    linewidth=2,
                    alpha=0.8,
                    label='Complete Separation' if i == deterministic_ci_detected[0] else "",
                )
            else:
                # Normal rendering
                ax.errorbar(
                    val, y,
                    xerr=[[err_low], [err_up]],
                    fmt='o',
                    markersize=8,
                    color=color,
                    ecolor=color,
                    capsize=5,
                    capthick=2,
                    linewidth=2,
                    alpha=0.8,
                    label=es.magnitude if i == 0 or es.magnitude != effect_sizes[i-1].magnitude else "",
                )
        
        # Reference line at 0 (no effect)
        ax.axvline(x=0, color='black', linestyle='--', linewidth=1.5, alpha=0.7, label='No effect')
        
        # Y-axis labels
        ax.set_yticks(y_positions)
        ax.set_yticklabels(labels)
        
        # X-axis label
        measure_name = effect_sizes[0].measure.value if effect_sizes else "Effect Size"
        ax.set_xlabel(f'{measure_name} (95% CI)')
        ax.set_title(f'Effect Sizes: {self._format_metric_label(metric_name)}')
        
        # Grid
        ax.xaxis.grid(True, alpha=0.3)
        ax.set_axisbelow(True)
        
        # Legend (unique magnitudes only)
        handles, labels_legend = ax.get_legend_handles_labels()
        by_label = dict(zip(labels_legend, handles))
        ax.legend(by_label.values(), by_label.keys(), loc='best')
        
        # Tight layout
        plt.tight_layout()
        
        # Save
        output_filename = f"forest_plot_{metric_name}.svg"
        output_path = self._validate_output_path(output_filename)
        plt.savefig(output_path, format='svg', bbox_inches='tight')
        plt.close()
        
        # Create title and caption
        title = f'Effect Sizes: {self._format_metric_label(metric_name)}'
        caption = (
            f"Forest plot of effect sizes for {self._format_metric_label(metric_name)}. "
            f"Points show {measure_name} estimates with 95% confidence intervals. "
            f"Colors indicate magnitude: green (small), orange (medium), red (large), gray (negligible). "
            f"Dashed line at 0 indicates no effect."
        )
        
        # Feature 013: Update caption if deterministic CIs detected
        if deterministic_ci_detected:
            caption += (
                " Open red markers indicate complete separation (|effect| = 1.0 with no uncertainty)."
            )
        
        return Visualization(
            viz_type=VisualizationType.EFFECT_FOREST,
            metric_name=metric_name,
            file_path=output_path,
            format="svg",
            title=title,
            caption=caption,
            groups=list(set([es.group1 for es in effect_sizes] + [es.group2 for es in effect_sizes])),
        )
    
    def generate_qq_plot(
        self,
        metric_name: str,
        distribution: MetricDistribution,
        normality_test: AssumptionCheck
    ) -> Visualization:
        """
        Generate Q-Q plot for normality assessment (T026).
        
        Q-Q plot shows:
        - Theoretical quantiles vs sample quantiles
        - 45-degree reference line (perfect normality)
        - Shapiro-Wilk p-value annotation
        - Visual assessment of normality
        
        Args:
            metric_name: Name of metric being assessed
            distribution: MetricDistribution object for one framework
            normality_test: AssumptionCheck with Shapiro-Wilk results
            
        Returns:
            Visualization metadata object
        """
        _, ax = plt.subplots(figsize=(7, 7))
        
        # Generate Q-Q plot
        stats.probplot(distribution.values, dist="norm", plot=ax)
        
        # Enhance styling
        line = ax.get_lines()[1]  # Reference line
        line.set_color('red')
        line.set_linewidth(2)
        line.set_linestyle('--')
        line.set_alpha(0.7)
        
        points = ax.get_lines()[0]  # Data points
        points.set_markersize(7)
        points.set_alpha(0.7)
        
        # Title with framework name
        ax.set_title(
            f'Q-Q Plot: {self._format_metric_label(metric_name)}\n'
            f'Framework: {distribution.group_name}'
        )
        ax.set_xlabel('Theoretical Quantiles')
        ax.set_ylabel('Sample Quantiles')
        
        # Add Shapiro-Wilk results annotation
        p_value = normality_test.p_value
        is_normal = normality_test.passes
        
        annotation_text = (
            f"Shapiro-Wilk Test\n"
            f"{format_pvalue(p_value)}\n"
            f"{'✅ Appears normal' if is_normal else '⚠️ Non-normal'}\n"
            f"(α = 0.05)"
        )
        
        # Place annotation box
        box_color = '#d4edda' if is_normal else '#f8d7da'  # Light green or light red
        text_color = '#155724' if is_normal else '#721c24'  # Dark green or dark red
        
        ax.text(
            0.05, 0.95,
            annotation_text,
            transform=ax.transAxes,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor=box_color, alpha=0.8, edgecolor=text_color),
            fontsize=9,
            color=text_color,
        )
        
        # Grid
        ax.grid(True, alpha=0.3)
        ax.set_axisbelow(True)
        
        # Save
        output_filename = f"qq_plot_{metric_name}_{distribution.group_name}.svg"
        output_path = self._validate_output_path(output_filename)
        plt.savefig(output_path, format='svg', bbox_inches='tight')
        plt.close()
        
        # Create title and caption
        title = f'Q-Q Plot: {self._format_metric_label(metric_name)} - {distribution.group_name}'
        caption = (
            f"Q-Q plot assessing normality of {self._format_metric_label(metric_name)} "
            f"for {distribution.group_name}. "
            f"Points close to red line indicate normal distribution. "
            f"Shapiro-Wilk test: {format_pvalue(p_value)} "
            f"({'normal' if is_normal else 'non-normal'} at α = 0.05)."
        )
        
        return Visualization(
            viz_type=VisualizationType.QQ_PLOT,
            metric_name=metric_name,
            file_path=output_path,
            format="svg",
            title=title,
            caption=caption,
            groups=[distribution.group_name],
        )
    
    def generate_all_visualizations(
        self,
        findings: 'StatisticalFindings'
    ) -> Dict[str, List[Visualization]]:
        """
        Generate all visualizations for complete experiment analysis (T027).
        
        For each metric, generates:
        - 1 box plot (all frameworks)
        - 1 violin plot (all frameworks)
        - 1 forest plot (all pairwise effect sizes)
        - N Q-Q plots (one per framework)
        
        Args:
            findings: StatisticalFindings object with complete analysis results
            
        Returns:
            Dictionary mapping metric_name → list of Visualization objects
        """
        all_visualizations = {}
        
        # Group data by metric
        metrics_data = {}
        
        # Collect distributions by metric
        for dist in findings.distributions:
            if dist.metric_name not in metrics_data:
                metrics_data[dist.metric_name] = {
                    'distributions': [],
                    'effect_sizes': [],
                    'normality_checks': {},
                }
            metrics_data[dist.metric_name]['distributions'].append(dist)
        
        # Collect effect sizes by metric
        for es in findings.effect_sizes:
            if es.metric_name in metrics_data:
                metrics_data[es.metric_name]['effect_sizes'].append(es)
        
        # Collect normality checks by metric and framework
        for check in findings.assumption_checks:
            if check.test_type == TestType.SHAPIRO_WILK and check.metric_name in metrics_data:
                # Assumption: single framework per check (from Phase 3 implementation)
                framework = check.groups_tested[0] if check.groups_tested else None
                if framework:
                    metrics_data[check.metric_name]['normality_checks'][framework] = check
        
        # Generate visualizations for each metric
        for metric_name, data in metrics_data.items():
            visualizations = []
            
            distributions = data['distributions']
            effect_sizes = data['effect_sizes']
            normality_checks = data['normality_checks']
            
            # Box plot (if we have distributions)
            if distributions:
                try:
                    viz = self.generate_box_plot(metric_name, distributions)
                    visualizations.append(viz)
                except Exception as e:
                    warnings.warn(f"Failed to generate box plot for {metric_name}: {e}")
            
            # Violin plot (if we have distributions)
            if distributions:
                try:
                    viz = self.generate_violin_plot(metric_name, distributions)
                    visualizations.append(viz)
                except Exception as e:
                    warnings.warn(f"Failed to generate violin plot for {metric_name}: {e}")
            
            # Forest plot (if we have effect sizes)
            if effect_sizes:
                try:
                    viz = self.generate_forest_plot(metric_name, effect_sizes)
                    visualizations.append(viz)
                except Exception as e:
                    warnings.warn(f"Failed to generate forest plot for {metric_name}: {e}")
            
            # Q-Q plots (one per framework, if we have normality checks)
            for dist in distributions:
                framework = dist.group_name
                if framework in normality_checks:
                    try:
                        viz = self.generate_qq_plot(
                            metric_name,
                            dist,
                            normality_checks[framework]
                        )
                        visualizations.append(viz)
                    except Exception as e:
                        warnings.warn(f"Failed to generate Q-Q plot for {metric_name} ({framework}): {e}")
            
            all_visualizations[metric_name] = visualizations
        
        return all_visualizations
    
    # ========================================================================
    # Enhanced Statistical Visualizations (Feature 015)
    # ========================================================================
    
    def generate_effect_size_panel(
        self,
        effect_sizes: Dict[str, List[EffectSize]],
        metrics: Optional[List[str]] = None,
        comparisons: Optional[List[Tuple[str, str]]] = None,
        show_ci: bool = True,
        mark_complete_separation: bool = True
    ) -> Visualization:
        """
        Generate faceted panel plot showing effect sizes across all metrics (T014-T023, US1).
        
        Creates a multi-metric visualization with one subplot per metric, showing all
        pairwise framework comparisons with color-coded magnitude and confidence intervals.
        
        Args:
            effect_sizes: Dict mapping metric name → list of EffectSize objects
            metrics: Optional filter for which metrics to include (None = all)
            comparisons: Optional filter for which comparisons to include (None = all)
            show_ci: Whether to display 95% confidence intervals as error bars
            mark_complete_separation: Whether to use special markers for |δ| = 1.0
        
        Returns:
            Visualization object with metadata
        
        Raises:
            ValueError: If effect_sizes is empty or metrics contains unknown metric
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # T021: Validate inputs
        if not effect_sizes:
            raise ValueError(
                "effect_sizes dictionary is empty. Cannot generate effect size panel. "
                "Ensure statistical analysis has computed effect sizes before visualization."
            )
        
        # Filter metrics if specified
        if metrics is None:
            metrics = list(effect_sizes.keys())
        else:
            # T022: Validate metrics exist
            unknown = set(metrics) - set(effect_sizes.keys())
            if unknown:
                valid = sorted(effect_sizes.keys())
                raise ValueError(
                    f"Unknown metrics: {sorted(unknown)}. "
                    f"Valid metrics are: {valid}"
                )
        
        # T023: Handle >10 metrics
        if len(metrics) > 10:
            logger.warning(
                f"Effect size panel requested for {len(metrics)} metrics. "
                f"This may create a very large plot. Consider focusing on top 10 "
                f"metrics by variance or effect size magnitude."
            )
            # For now, proceed with all metrics but warn user
        
        n_metrics = len(metrics)
        
        # T015: Create subplot grid
        fig, axes = plt.subplots(
            nrows=n_metrics,
            ncols=1,
            figsize=(10, 3 * n_metrics),
            sharey=False,  # Each metric may have different scales
            squeeze=False
        )
        
        # T016: Plot effect sizes for each metric
        for idx, metric_name in enumerate(metrics):
            ax = axes[idx, 0]
            metric_effects = effect_sizes[metric_name]
            
            # Filter comparisons if specified
            if comparisons is not None:
                metric_effects = [
                    e for e in metric_effects
                    if (e.group1, e.group2) in comparisons or
                       (e.group2, e.group1) in comparisons
                ]
            
            if not metric_effects:
                ax.text(
                    0.5, 0.5, "No effect sizes available",
                    ha='center', va='center', transform=ax.transAxes
                )
                ax.set_title(self._format_metric_label(metric_name))
                continue
            
            # Prepare data for plotting
            comparison_labels = []
            effect_values = []
            ci_lower = []
            ci_upper = []
            colors = []
            markers = []
            
            for effect in metric_effects:
                comparison_labels.append(f"{effect.group1} vs {effect.group2}")
                effect_values.append(effect.value)
                ci_lower.append(effect.ci_lower)
                ci_upper.append(effect.ci_upper)
                colors.append(self._magnitude_to_color(effect.magnitude))
                
                # T018: Mark complete separation
                if mark_complete_separation and abs(effect.value) == 1.0:
                    markers.append('o')  # Will use fillstyle='none' below
                else:
                    markers.append('o')
            
            # Plot effect sizes
            y_pos = np.arange(len(comparison_labels))
            
            for i, (y, val, lower, upper, color, marker) in enumerate(
                zip(y_pos, effect_values, ci_lower, ci_upper, colors, markers)
            ):
                # T018: Complete separation gets open markers
                if mark_complete_separation and abs(val) == 1.0:
                    fillstyle = 'none'
                    markersize = 8
                    linewidth = 2
                else:
                    fillstyle = 'full'
                    markersize = 6
                    linewidth = 1.5
                
                # T017: Add confidence intervals if requested
                if show_ci and lower is not None and upper is not None:
                    ax.errorbar(
                        val, y,
                        xerr=[[val - lower], [upper - val]],
                        fmt=marker,
                        color=color,
                        fillstyle=fillstyle,
                        markersize=markersize,
                        linewidth=linewidth,
                        capsize=4,
                        capthick=1.5
                    )
                else:
                    ax.plot(
                        val, y,
                        marker=marker,
                        color=color,
                        fillstyle=fillstyle,
                        markersize=markersize,
                        linestyle='none'
                    )
            
            # T019: Format subplot
            ax.set_yticks(y_pos)
            ax.set_yticklabels(comparison_labels)
            ax.axvline(x=0, color='black', linestyle='--', linewidth=0.8, alpha=0.5)
            ax.set_xlabel("Effect Size (Cliff's δ)")
            ax.set_xlim(-1.1, 1.1)
            ax.set_title(self._format_metric_label(metric_name), fontweight='bold')
            ax.grid(True, alpha=0.3)
        
        # T019: Add legend (shared across all subplots)
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#999999', label='Negligible'),
            Patch(facecolor='#77DD77', label='Small'),
            Patch(facecolor='#FFB347', label='Medium'),
            Patch(facecolor='#FF6961', label='Large'),
        ]
        if mark_complete_separation:
            # Add complete separation marker to legend
            from matplotlib.lines import Line2D
            legend_elements.append(
                Line2D([0], [0], marker='o', color='w',
                       markerfacecolor='none', markeredgecolor='#FF6961',
                       markersize=8, markeredgewidth=2,
                       label='Complete Separation (|δ|=1.0)')
            )
        
        fig.legend(
            handles=legend_elements,
            loc='upper right',
            bbox_to_anchor=(0.98, 0.98),
            framealpha=0.9
        )
        
        plt.tight_layout(rect=[0, 0, 1, 0.97])  # Leave space for legend
        
        # T020: Save and return visualization
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"effect_size_panel_{timestamp}.svg"
        output_path = self._validate_output_path(output_filename)
        
        try:
            plt.savefig(output_path, format='svg', dpi=300, bbox_inches='tight')
            logger.info(f"Effect size panel saved to {output_path}")
        finally:
            plt.close(fig)  # T113: Memory management
        
        return Visualization(
            viz_type=VisualizationType.EFFECT_PANEL,
            metric_name="all_metrics",
            file_path=output_path,
            format="svg",
            title=f"Effect Size Panel: {len(metrics)} Metrics",
            caption=(
                f"Faceted panel showing effect sizes (Cliff's δ) for all pairwise "
                f"framework comparisons across {len(metrics)} metrics. Colors indicate "
                f"magnitude: gray=negligible, green=small, orange=medium, red=large. "
                f"Error bars show 95% confidence intervals. Complete separation "
                f"(|δ|=1.0) marked with open circles."
            ),
            groups=list(set(
                group
                for metric_effects in effect_sizes.values()
                for effect in metric_effects
                for group in [effect.group1, effect.group2]
            ))
        )
    
    def generate_efficiency_plot(
        self,
        time_distributions: Dict[str, MetricDistribution],
        cost_distributions: Dict[str, MetricDistribution],
        time_metric: str = "execution_time",
        cost_metric: str = "total_cost_usd",
        use_log_scale: bool = False,
        show_error_bars: bool = True,
        jitter: float = 0.0
    ) -> Visualization:
        """
        Generate cost vs time efficiency scatter plot (T024-T032, US2).
        
        Creates a scatter plot showing framework efficiency quadrants (fast-cheap,
        slow-expensive, etc.) with optional log scaling and error bars.
        
        Args:
            time_distributions: Dict mapping framework → MetricDistribution for time
            cost_distributions: Dict mapping framework → MetricDistribution for cost
            time_metric: Name of time metric (for axis label)
            cost_metric: Name of cost metric (for axis label)
            use_log_scale: Whether to use symlog scale for x-axis (handles zeros)
            show_error_bars: Whether to show mean ± 1 std as error bars
            jitter: Amount of random jitter (0.0 = none, 0.1 = 10% of range)
        
        Returns:
            Visualization object with metadata
        
        Raises:
            ValueError: If framework sets don't match between time and cost
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # T031: Validate framework consistency
        time_frameworks = set(time_distributions.keys())
        cost_frameworks = set(cost_distributions.keys())
        if time_frameworks != cost_frameworks:
            raise ValueError(
                f"Framework mismatch between time and cost distributions. "
                f"Time has: {sorted(time_frameworks)}, "
                f"Cost has: {sorted(cost_frameworks)}"
            )
        
        frameworks = sorted(time_frameworks)
        
        # T025: Create figure and setup scatter plot
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Get colorblind palette
        colors = sns.color_palette("colorblind", n_colors=len(frameworks))
        
        # T026: Plot data points with optional jittering
        for idx, framework in enumerate(frameworks):
            time_dist = time_distributions[framework]
            cost_dist = cost_distributions[framework]
            
            time_mean = time_dist.mean
            cost_mean = cost_dist.mean
            time_std = time_dist.std_dev
            cost_std = cost_dist.std_dev
            
            # Apply jitter if requested
            if jitter > 0:
                time_range = time_dist.max_value - time_dist.min_value
                cost_range = cost_dist.max_value - cost_dist.min_value
                time_jitter = np.random.normal(0, jitter * time_range)
                cost_jitter = np.random.normal(0, jitter * cost_range)
                time_plot = time_mean + time_jitter
                cost_plot = cost_mean + cost_jitter
            else:
                time_plot = time_mean
                cost_plot = cost_mean
            
            # T032: Handle zero variance
            if time_std == 0 or cost_std == 0:
                logger.warning(
                    f"Framework '{framework}' has zero variance in "
                    f"{'time' if time_std == 0 else 'cost'}. "
                    f"Plotting point without error bars."
                )
                show_error_bars_for_this = False
            else:
                show_error_bars_for_this = show_error_bars
            
            # T027: Add error bars if requested
            if show_error_bars_for_this:
                ax.errorbar(
                    time_plot, cost_plot,
                    xerr=time_std,
                    yerr=cost_std,
                    fmt='o',
                    color=colors[idx],
                    markersize=10,
                    capsize=5,
                    capthick=2,
                    label=framework,
                    alpha=0.8
                )
            else:
                ax.scatter(
                    time_plot, cost_plot,
                    color=colors[idx],
                    s=100,
                    label=framework,
                    alpha=0.8,
                    edgecolors='black',
                    linewidths=1
                )
        
        # T028: Apply log scale if requested
        if use_log_scale:
            ax.set_xscale('symlog', linthresh=1.0)
            time_label = f"{self._format_metric_label(time_metric)} (log scale)"
        else:
            time_label = self._format_metric_label(time_metric)
        
        # T029: Add axis labels, title, legend
        ax.set_xlabel(time_label, fontsize=12, fontweight='bold')
        ax.set_ylabel(self._format_metric_label(cost_metric), fontsize=12, fontweight='bold')
        ax.set_title('Cost vs Time Efficiency Analysis', fontsize=14, fontweight='bold')
        ax.legend(loc='best', framealpha=0.9, fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # Add quadrant reference lines (optional visual aid)
        if len(frameworks) > 0:
            # Compute median time and cost across all frameworks for reference
            all_times = [time_distributions[f].mean for f in frameworks]
            all_costs = [cost_distributions[f].mean for f in frameworks]
            median_time = np.median(all_times)
            median_cost = np.median(all_costs)
            
            ax.axvline(median_time, color='gray', linestyle=':', linewidth=1, alpha=0.5)
            ax.axhline(median_cost, color='gray', linestyle=':', linewidth=1, alpha=0.5)
        
        plt.tight_layout()
        
        # T030: Save and return visualization
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"efficiency_{time_metric}_vs_{cost_metric}.svg"
        output_path = self._validate_output_path(output_filename)
        
        try:
            plt.savefig(output_path, format='svg', dpi=300, bbox_inches='tight')
            logger.info(f"Efficiency plot saved to {output_path}")
        finally:
            plt.close(fig)
        
        return Visualization(
            viz_type=VisualizationType.EFFICIENCY,
            metric_name=f"{time_metric}_vs_{cost_metric}",
            file_path=output_path,
            format="svg",
            title="Cost-Performance Efficiency Analysis",
            caption=(
                f"Scatter plot showing {cost_metric} vs {time_metric} trade-offs across "
                f"frameworks. Each point represents a framework's mean performance with "
                f"error bars showing ±1 standard deviation. Quadrant reference lines show "
                f"median values. Lower-left quadrant = fast and cheap (most efficient)."
            ),
            groups=frameworks
        )
    
    def generate_regression_plot(
        self,
        x_distributions: Dict[str, MetricDistribution],
        y_distributions: Dict[str, MetricDistribution],
        x_metric: str,
        y_metric: str,
        show_equations: bool = True,
        show_r_squared: bool = True,
        cached_tokens: Optional[Dict[str, MetricDistribution]] = None
    ) -> Visualization:
        """
        Generate regression plot with framework-specific lines (T033-T045, US3).
        
        Creates scatter plot with linear regression lines per framework, showing
        token-to-cost relationships and highlighting cost structure differences.
        
        Args:
            x_distributions: Dict mapping framework → MetricDistribution for x-axis
            y_distributions: Dict mapping framework → MetricDistribution for y-axis
            x_metric: Name of x metric (typically tokens_in or tokens_total)
            y_metric: Name of y metric (typically total_cost_usd)
            show_equations: Whether to annotate with y = mx + b equations
            show_r_squared: Whether to include R² values in annotations
            cached_tokens: Optional dict for 3rd dimension (via marker size)
        
        Returns:
            Visualization object with metadata
        
        Raises:
            ValueError: If x or y distributions have zero variance
        """
        import logging
        from scipy import stats as scipy_stats
        
        logger = logging.getLogger(__name__)
        
        frameworks = sorted(x_distributions.keys())
        
        # T034: Create figure and setup
        fig, ax = plt.subplots(figsize=(12, 8))
        colors = sns.color_palette("colorblind", n_colors=len(frameworks))
        
        regression_results = {}
        
        # T035-T037: Fit regression and plot for each framework
        for idx, framework in enumerate(frameworks):
            x_dist = x_distributions[framework]
            y_dist = y_distributions[framework]
            
            x_values = np.array(x_dist.values)
            y_values = np.array(y_dist.values)
            
            # T043: Check minimum sample size
            if len(x_values) < 3:
                logger.warning(
                    f"Framework '{framework}' has n={len(x_values)} < 3. "
                    f"Skipping regression (insufficient data for meaningful fit)."
                )
                # Plot points only, no regression line
                ax.scatter(x_values, y_values, color=colors[idx], 
                          label=f"{framework} (n={len(x_values)})", alpha=0.6, s=50)
                continue
            
            # T044: Check variance
            if np.var(x_values) == 0 or np.var(y_values) == 0:
                raise ValueError(
                    f"Cannot fit regression for framework '{framework}': "
                    f"zero variance in {'x' if np.var(x_values) == 0 else 'y'}-axis. "
                    f"All {x_metric if np.var(x_values) == 0 else y_metric} values "
                    f"are identical. Check data quality."
                )
            
            # Fit linear regression
            slope, intercept, r_value, p_value, std_err = scipy_stats.linregress(
                x_values, y_values
            )
            
            # T036: Store results
            regression_results[framework] = RegressionResult(
                slope=slope,
                intercept=intercept,
                r_squared=r_value**2,
                std_err=std_err
            )
            
            # T040: Handle cached_tokens as marker size
            if cached_tokens and framework in cached_tokens:
                cached_dist = cached_tokens[framework]
                # Use cached token ratio as size: more caching = larger markers
                cache_ratios = np.array(cached_dist.values) / (x_values + 1e-9)
                sizes = 50 + cache_ratios * 200  # Scale: 50-250
            else:
                sizes = 50
            
            # Plot scatter points
            ax.scatter(x_values, y_values, color=colors[idx], 
                      label=framework, alpha=0.6, s=sizes, edgecolors='black', linewidths=0.5)
            
            # Plot regression line
            x_range = np.linspace(x_values.min(), x_values.max(), 100)
            y_pred = slope * x_range + intercept
            ax.plot(x_range, y_pred, color=colors[idx], linewidth=2, linestyle='--', alpha=0.8)
            
            # T038-T039: Annotate with equation and R²
            if show_equations or show_r_squared:
                # Position annotation near the regression line
                mid_x = np.median(x_range)
                mid_y = slope * mid_x + intercept
                
                parts = []
                if show_equations:
                    # T045: Check for flat line
                    if abs(slope) < 1e-6:
                        parts.append(f"y = {intercept:.4f} (no relationship)")
                    else:
                        parts.append(f"y = {slope:.4f}x + {intercept:.4f}")
                
                if show_r_squared:
                    parts.append(f"R² = {r_value**2:.3f}")
                
                annotation = ", ".join(parts)
                ax.annotate(
                    f"{framework}: {annotation}",
                    xy=(mid_x, mid_y),
                    xytext=(10, 10 * (idx - len(frameworks)//2)),
                    textcoords='offset points',
                    fontsize=8,
                    bbox=dict(boxstyle='round,pad=0.3', facecolor=colors[idx], alpha=0.3)
                )
        
        # T041: Add axis labels, title, legend
        ax.set_xlabel(self._format_metric_label(x_metric), fontsize=12, fontweight='bold')
        ax.set_ylabel(self._format_metric_label(y_metric), fontsize=12, fontweight='bold')
        ax.set_title(f'{y_metric} vs {x_metric} Regression Analysis', fontsize=14, fontweight='bold')
        ax.legend(loc='best', framealpha=0.9, fontsize=10)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # T042: Save and return
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"regression_{x_metric}_vs_{y_metric}.svg"
        output_path = self._validate_output_path(output_filename)
        
        try:
            plt.savefig(output_path, format='svg', dpi=300, bbox_inches='tight')
            logger.info(f"Regression plot saved to {output_path}")
        finally:
            plt.close(fig)
        
        return Visualization(
            viz_type=VisualizationType.REGRESSION,
            metric_name=f"{x_metric}_vs_{y_metric}",
            file_path=output_path,
            format="svg",
            title=f"Regression Analysis: {y_metric} vs {x_metric}",
            caption=(
                f"Linear regression analysis showing relationship between {x_metric} and "
                f"{y_metric} with framework-specific fitted lines. Slope differences reveal "
                f"cost structure variations (e.g., base cost vs per-token rate). "
                f"{'Marker size indicates cached token ratio. ' if cached_tokens else ''}"
                f"Dashed lines show regression fits with equations and R² values annotated."
            ),
            groups=frameworks
        )
    
    def generate_overlap_plot(
        self,
        distribution_a: MetricDistribution,
        distribution_b: MetricDistribution,
        metric_name: str,
        effect_size: EffectSize,
        p_value: float,
        plot_type: str = "density"
    ) -> Visualization:
        """
        Generate 2-way distribution overlap plot (T046-T056, US4).
        
        Creates focused comparison showing distribution overlap for groups with
        small but statistically significant effect sizes.
        
        Args:
            distribution_a: MetricDistribution for first group
            distribution_b: MetricDistribution for second group
            metric_name: Name of metric being compared
            effect_size: EffectSize object for this comparison
            p_value: Statistical significance value
            plot_type: "density" for KDE or "violin" for violin plot
        
        Returns:
            Visualization object with metadata
        
        Raises:
            ValueError: If n=1 for either group (cannot compute KDE)
        """
        import logging
        from scipy import integrate
        
        logger = logging.getLogger(__name__)
        
        # T056: Check sample sizes
        if distribution_a.n_samples < 2 or distribution_b.n_samples < 2:
            raise ValueError(
                f"Cannot compute KDE with n=1. "
                f"{distribution_a.group_name} has n={distribution_a.n_samples}, "
                f"{distribution_b.group_name} has n={distribution_b.n_samples}. "
                f"Overlap plot requires at least 2 samples per group."
            )
        
        # T047: Create figure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        group_a = distribution_a.group_name
        group_b = distribution_b.group_name
        
        # T048-T049: Plot based on type
        if plot_type == "density":
            # Use seaborn KDE plot
            values_a = np.array(distribution_a.values)
            values_b = np.array(distribution_b.values)
            
            sns.kdeplot(values_a, ax=ax, label=group_a, fill=True, alpha=0.5, linewidth=2)
            sns.kdeplot(values_b, ax=ax, label=group_b, fill=True, alpha=0.5, linewidth=2)
            
            # T050: Compute overlap coefficient
            try:
                # Get KDE objects for integration
                from scipy.stats import gaussian_kde
                kde_a = gaussian_kde(values_a)
                kde_b = gaussian_kde(values_b)
                
                # Define common range
                x_min = min(values_a.min(), values_b.min())
                x_max = max(values_a.max(), values_b.max())
                x_range = np.linspace(x_min, x_max, 1000)
                
                # Compute overlap: integral of min(density_a, density_b)
                density_a = kde_a(x_range)
                density_b = kde_b(x_range)
                overlap_density = np.minimum(density_a, density_b)
                overlap_coef = integrate.simpson(overlap_density, x_range)
                
                # T052: Add shaded overlap region
                ax.fill_between(x_range, 0, overlap_density, 
                               color='purple', alpha=0.3, label='Overlap')
                
            except Exception as e:
                logger.warning(f"Could not compute overlap coefficient: {e}")
                overlap_coef = np.nan
        
        elif plot_type == "violin":
            # Create 2-way violin plot
            data = [distribution_a.values, distribution_b.values]
            positions = [0, 1]
            parts = ax.violinplot(data, positions=positions, showmeans=True, 
                                 showextrema=True, widths=0.7)
            
            # Color violins
            colors = sns.color_palette("colorblind", 2)
            for pc, color in zip(parts['bodies'], colors):
                pc.set_facecolor(color)
                pc.set_alpha(0.7)
            
            ax.set_xticks(positions)
            ax.set_xticklabels([group_a, group_b])
            
            # For violin, overlap is harder to quantify
            overlap_coef = np.nan
        
        # T055: Check for identical distributions
        if abs(effect_size.value) < 0.01:
            ax.text(0.5, 0.95, "Practical Equivalence",
                   transform=ax.transAxes, ha='center', va='top',
                   fontsize=12, fontweight='bold',
                   bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
        
        # T051, T053: Add annotations and labels
        stats_text = (
            f"Effect Size (Cliff's δ): {effect_size.value:.3f} ({effect_size.magnitude})\n"
            f"p-value: {p_value:.4f}\n"
        )
        if not np.isnan(overlap_coef):
            stats_text += f"Overlap Coefficient: {overlap_coef:.3f}"
        
        ax.text(0.02, 0.98, stats_text,
               transform=ax.transAxes, va='top', ha='left',
               fontsize=10,
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
        
        ax.set_xlabel(self._format_metric_label(metric_name), fontsize=12, fontweight='bold')
        if plot_type == "density":
            ax.set_ylabel('Density', fontsize=12, fontweight='bold')
        else:
            ax.set_ylabel(self._format_metric_label(metric_name), fontsize=12, fontweight='bold')
        
        ax.set_title(f'Distribution Overlap: {group_a} vs {group_b}', 
                    fontsize=14, fontweight='bold')
        ax.legend(loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        # T054: Save and return
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"overlap_{metric_name}_{group_a}_vs_{group_b}.svg"
        output_path = self._validate_output_path(output_filename)
        
        try:
            plt.savefig(output_path, format='svg', dpi=300, bbox_inches='tight')
            logger.info(f"Overlap plot saved to {output_path}")
        finally:
            plt.close(fig)
        
        return Visualization(
            viz_type=VisualizationType.OVERLAP,
            metric_name=metric_name,
            file_path=output_path,
            format="svg",
            title=f"Distribution Overlap: {group_a} vs {group_b}",
            caption=(
                f"Two-way distribution comparison for {metric_name} showing overlap between "
                f"{group_a} and {group_b}. Effect size: {effect_size.value:.3f} "
                f"({effect_size.magnitude}), p={p_value:.4f}. "
                f"{'Shaded purple region shows distribution overlap. ' if plot_type == 'density' else ''}"
                f"Used for nuanced analysis when differences are statistically significant "
                f"but practically small (|δ| < 0.3)."
            ),
            groups=[group_a, group_b]
        )
    
    def generate_normalized_cost_plot(
        self,
        cost_distributions: Dict[str, MetricDistribution],
        quality_distributions: Dict[str, MetricDistribution],
        quality_metric_name: str
    ) -> Visualization:
        """
        Generate normalized cost-per-quality-unit bar chart (T057-T066, US5).
        
        Creates horizontal bar chart showing cost efficiency across frameworks
        when normalized by quality output. Handles zero/invalid quality scores.
        
        Args:
            cost_distributions: Dict mapping framework -> cost MetricDistribution
            quality_distributions: Dict mapping framework -> quality MetricDistribution
            quality_metric_name: Name of quality metric for labeling
        
        Returns:
            Visualization object with metadata
        
        Raises:
            ValueError: If frameworks mismatch between cost and quality dicts
        """
        import logging
        
        logger = logging.getLogger(__name__)
        
        # T057: Validate framework alignment
        cost_frameworks = set(cost_distributions.keys())
        quality_frameworks = set(quality_distributions.keys())
        
        if cost_frameworks != quality_frameworks:
            raise ValueError(
                f"Framework mismatch between cost and quality. "
                f"Cost frameworks: {cost_frameworks}, "
                f"Quality frameworks: {quality_frameworks}"
            )
        
        frameworks = sorted(cost_frameworks)
        
        # T058, T059: Compute normalized costs
        normalized_costs = {}
        errors = {}
        warnings = []
        
        for framework in frameworks:
            cost_mean = cost_distributions[framework].mean
            quality_mean = quality_distributions[framework].mean
            
            # T066: Handle zero/negative quality
            if quality_mean <= 0:
                warnings.append(
                    f"{framework} has non-positive quality mean ({quality_mean:.4f}), "
                    f"using quality=1.0 for normalization"
                )
                quality_mean = 1.0
            
            normalized_costs[framework] = cost_mean / quality_mean
            
            # Error propagation: σ(a/b) ≈ (a/b) * sqrt((σ_a/a)² + (σ_b/b)²)
            cost_std = cost_distributions[framework].std_dev
            quality_std = quality_distributions[framework].std_dev
            
            rel_cost_err = cost_std / cost_mean if cost_mean > 0 else 0
            rel_quality_err = quality_std / quality_mean if quality_mean > 0 else 0
            
            errors[framework] = normalized_costs[framework] * np.sqrt(
                rel_cost_err**2 + rel_quality_err**2
            )
        
        if warnings:
            for warning in warnings:
                logger.warning(warning)
        
        # T060, T061: Create horizontal bar chart
        fig, ax = plt.subplots(figsize=(10, max(6, len(frameworks) * 0.8)))
        
        y_positions = np.arange(len(frameworks))
        values = [normalized_costs[fw] for fw in frameworks]
        error_bars = [errors[fw] for fw in frameworks]
        
        # Color bars by relative performance
        colors = []
        if values:
            min_val = min(values)
            for val in values:
                if val == min_val:
                    colors.append('#77DD77')  # Green for best (lowest cost/quality)
                elif val > 2 * min_val:
                    colors.append('#FF6961')  # Red for poor
                else:
                    colors.append('#FFB347')  # Orange for moderate
        
        bars = ax.barh(y_positions, values, xerr=error_bars, 
                      color=colors, alpha=0.7, capsize=5, edgecolor='black', linewidth=1.5)
        
        # T062: Add value labels on bars
        for i, (val, err) in enumerate(zip(values, error_bars)):
            ax.text(val + err + 0.02 * max(values), i, f'${val:.4f}',
                   va='center', ha='left', fontsize=10, fontweight='bold')
        
        ax.set_yticks(y_positions)
        ax.set_yticklabels(frameworks, fontsize=11)
        ax.set_xlabel(f'Cost per {quality_metric_name} Unit (USD)', 
                     fontsize=12, fontweight='bold')
        ax.set_title(f'Cost Efficiency: Normalized by {quality_metric_name}',
                    fontsize=14, fontweight='bold')
        
        # T063: Add reference line at median
        if values:
            median_val = np.median(values)
            ax.axvline(median_val, color='gray', linestyle='--', linewidth=2, 
                      alpha=0.7, label=f'Median (${median_val:.4f})')
            ax.legend(loc='best', framealpha=0.9)
        
        ax.grid(True, alpha=0.3, axis='x')
        ax.set_xlim(left=0)
        
        # T064: Add interpretation note
        note = (
            "Lower values indicate better cost efficiency (more quality per dollar). "
            "Error bars show propagated uncertainty from cost and quality measurements."
        )
        ax.text(0.5, -0.15, note, transform=ax.transAxes,
               ha='center', va='top', fontsize=9, style='italic',
               wrap=True)
        
        plt.tight_layout()
        
        # T065: Save and return
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"normalized_cost_{quality_metric_name}.svg"
        output_path = self._validate_output_path(output_filename)
        
        try:
            plt.savefig(output_path, format='svg', dpi=300, bbox_inches='tight')
            logger.info(f"Normalized cost plot saved to {output_path}")
        finally:
            plt.close(fig)
        
        return Visualization(
            viz_type=VisualizationType.NORMALIZED_COST,
            metric_name=f"cost_per_{quality_metric_name}",
            file_path=output_path,
            format="svg",
            title=f"Cost Efficiency: Normalized by {quality_metric_name}",
            caption=(
                f"Horizontal bar chart showing cost per unit of {quality_metric_name} "
                f"across frameworks. Green bars indicate best efficiency (lowest cost/quality), "
                f"red bars indicate poor efficiency (>2x minimum). Error bars account for "
                f"uncertainty propagation from both cost and quality measurements. "
                f"{' '.join(warnings) if warnings else ''}"
            ),
            groups=frameworks
        )
    
    def generate_rank_plot(
        self,
        rank_data: List[RankData],
        frameworks: List[str]
    ) -> Visualization:
        """
        Generate metric-wise ranking heatmap (T067-T077, US6).
        
        Creates heatmap showing how frameworks rank across multiple metrics,
        with special handling for tied ranks.
        
        Args:
            rank_data: List of RankData objects (framework, metric, rank, tied)
            frameworks: Ordered list of framework names for rows
        
        Returns:
            Visualization object with metadata
        
        Raises:
            ValueError: If rank_data is empty or frameworks list is empty
        """
        import logging
        
        logger = logging.getLogger(__name__)
        
        # T067: Validate inputs
        if not rank_data:
            raise ValueError("Cannot create rank plot with empty rank_data")
        if not frameworks:
            raise ValueError("Cannot create rank plot with empty frameworks list")
        
        # T068: Pivot data into matrix
        metrics = sorted(list(set(rd.metric for rd in rank_data)))
        
        # Initialize rank matrix (frameworks x metrics)
        rank_matrix = np.full((len(frameworks), len(metrics)), np.nan)
        tied_matrix = np.zeros((len(frameworks), len(metrics)), dtype=bool)
        
        framework_idx = {fw: i for i, fw in enumerate(frameworks)}
        metric_idx = {m: i for i, m in enumerate(metrics)}
        
        for rd in rank_data:
            if rd.framework in framework_idx and rd.metric in metric_idx:
                i = framework_idx[rd.framework]
                j = metric_idx[rd.metric]
                rank_matrix[i, j] = rd.rank
                tied_matrix[i, j] = rd.tied
        
        # T069, T070: Create heatmap
        fig, ax = plt.subplots(figsize=(max(10, len(metrics) * 1.2), 
                                       max(6, len(frameworks) * 0.8)))
        
        # Use diverging colormap: lower ranks (better) are green, higher ranks are red
        # Reverse so rank 1 (best) is darkest green
        cmap = sns.diverging_palette(145, 10, as_cmap=True)  # Green to red
        
        sns.heatmap(rank_matrix, ax=ax, cmap=cmap, 
                   annot=True, fmt='.1f', 
                   cbar_kws={'label': 'Rank (1=best)'},
                   xticklabels=[self._format_metric_label(m) for m in metrics],
                   yticklabels=frameworks,
                   linewidths=1, linecolor='white',
                   vmin=1, vmax=len(frameworks))
        
        # T071, T072: Mark tied ranks with asterisks
        for i in range(len(frameworks)):
            for j in range(len(metrics)):
                if tied_matrix[i, j]:
                    rank_val = rank_matrix[i, j]
                    if not np.isnan(rank_val):
                        # Add asterisk to indicate tie
                        ax.text(j + 0.5, i + 0.7, '*', 
                               ha='center', va='center',
                               fontsize=16, fontweight='bold', color='blue')
        
        # T077: Check for framework dominating all metrics
        mean_ranks = np.nanmean(rank_matrix, axis=1)
        if not np.all(np.isnan(mean_ranks)):
            best_framework_idx = np.nanargmin(mean_ranks)
            best_framework = frameworks[best_framework_idx]
            best_mean_rank = mean_ranks[best_framework_idx]
            
            if best_mean_rank <= 1.5:  # Average rank ≤ 1.5 suggests dominance
                ax.text(0.5, 1.05, f"⭐ {best_framework} dominates (avg rank: {best_mean_rank:.2f})",
                       transform=ax.transAxes, ha='center', va='bottom',
                       fontsize=12, fontweight='bold',
                       bbox=dict(boxstyle='round', facecolor='gold', alpha=0.7))
        
        ax.set_title('Framework Rankings Across Metrics', 
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('')  # Remove default xlabel
        ax.set_ylabel('Framework', fontsize=12, fontweight='bold')
        
        # T076: Add legend for tied ranks
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='white', edgecolor='blue', label='* = Tied rank')
        ]
        ax.legend(handles=legend_elements, loc='upper left', 
                 bbox_to_anchor=(1.15, 1.0), framealpha=0.9)
        
        plt.tight_layout()
        
        # T073-T075: Save and return
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = "rank_heatmap.svg"
        output_path = self._validate_output_path(output_filename)
        
        try:
            plt.savefig(output_path, format='svg', dpi=300, bbox_inches='tight')
            logger.info(f"Rank heatmap saved to {output_path}")
        finally:
            plt.close(fig)
        
        # Compute caption details
        tied_count = np.sum(tied_matrix)
        total_comparisons = len(frameworks) * len(metrics)
        
        return Visualization(
            viz_type=VisualizationType.RANK,
            metric_name="multi_metric_ranking",
            file_path=output_path,
            format="svg",
            title="Framework Rankings Across Metrics",
            caption=(
                f"Heatmap showing framework rankings across {len(metrics)} metrics. "
                f"Rank 1 (green) indicates best performance, higher ranks (red) indicate "
                f"worse performance. Asterisks (*) mark tied ranks. "
                f"{tied_count}/{total_comparisons} cells show ties. "
                f"Useful for identifying overall winners and metric-specific strengths."
            ),
            groups=frameworks
        )
    
    def generate_stability_plot(
        self,
        stability_metrics: List[StabilityMetric],
        cv_threshold: float = 0.3
    ) -> Visualization:
        """
        Generate coefficient of variation (CV) plot (T078-T088, US7).
        
        Creates scatter plot showing metric stability across frameworks using
        coefficient of variation (std/mean). Lower CV = more stable/reproducible.
        
        Args:
            stability_metrics: List of StabilityMetric objects
            cv_threshold: Threshold for stable/unstable classification (default 0.3)
        
        Returns:
            Visualization object with metadata
        
        Raises:
            ValueError: If stability_metrics is empty
        """
        import logging
        
        logger = logging.getLogger(__name__)
        
        # T078: Validate inputs
        if not stability_metrics:
            raise ValueError("Cannot create stability plot with empty stability_metrics")
        
        # T079: Extract unique frameworks and metrics
        frameworks = sorted(list(set(sm.framework for sm in stability_metrics)))
        metrics = sorted(list(set(sm.metric for sm in stability_metrics)))
        
        # T080, T081: Create scatter plot
        fig, ax = plt.subplots(figsize=(12, max(6, len(frameworks) * 0.6)))
        
        # Group by framework for colored scatter
        colors = sns.color_palette("colorblind", len(frameworks))
        framework_colors = {fw: colors[i] for i, fw in enumerate(frameworks)}
        
        for sm in stability_metrics:
            color = framework_colors[sm.framework]
            marker = 'o' if sm.is_stable else 'X'  # Circle for stable, X for unstable
            size = 100 if sm.is_stable else 150
            
            ax.scatter(sm.cv_value, sm.metric, 
                      color=color, marker=marker, s=size, 
                      alpha=0.7, edgecolors='black', linewidths=1.5,
                      label=sm.framework if sm == next(
                          (x for x in stability_metrics if x.framework == sm.framework), None
                      ) else "")
        
        # T082: Add vertical threshold line
        ax.axvline(cv_threshold, color='red', linestyle='--', linewidth=2,
                  alpha=0.7, label=f'Stability Threshold (CV={cv_threshold})')
        
        # T083: Add shaded stability zone
        ax.axvspan(0, cv_threshold, alpha=0.1, color='green', 
                  label='Stable Zone (CV < threshold)')
        ax.axvspan(cv_threshold, ax.get_xlim()[1], alpha=0.1, color='red',
                  label='Unstable Zone (CV ≥ threshold)')
        
        # Format metric labels
        metric_labels = [self._format_metric_label(m) for m in metrics]
        ax.set_yticks(range(len(metrics)))
        ax.set_yticklabels(metric_labels, fontsize=10)
        
        ax.set_xlabel('Coefficient of Variation (CV = σ/μ)', 
                     fontsize=12, fontweight='bold')
        ax.set_ylabel('Metric', fontsize=12, fontweight='bold')
        ax.set_title('Metric Stability Across Frameworks',
                    fontsize=14, fontweight='bold')
        
        # T087: Check for universally unstable metrics
        metric_stability = {}
        for metric in metrics:
            metric_sms = [sm for sm in stability_metrics if sm.metric == metric]
            unstable_count = sum(1 for sm in metric_sms if not sm.is_stable)
            metric_stability[metric] = unstable_count / len(metric_sms) if metric_sms else 0
        
        universally_unstable = [m for m, ratio in metric_stability.items() if ratio >= 0.8]
        if universally_unstable:
            warning_text = "⚠️ Unstable across frameworks: " + ", ".join(
                self._format_metric_label(m) for m in universally_unstable
            )
            ax.text(0.5, 1.05, warning_text,
                   transform=ax.transAxes, ha='center', va='bottom',
                   fontsize=10, fontweight='bold',
                   bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7),
                   wrap=True)
        
        # T085, T086: Handle legend (remove duplicates)
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys(), 
                 loc='best', framealpha=0.9, fontsize=9)
        
        ax.grid(True, alpha=0.3, axis='x')
        ax.set_xlim(left=0)
        
        # T088: Add interpretation note
        note = (
            f"○ = Stable (CV < {cv_threshold}), ✕ = Unstable (CV ≥ {cv_threshold}). "
            "Lower CV indicates more reproducible results across runs. "
            "High CV suggests nondeterministic behavior or high variance."
        )
        ax.text(0.5, -0.12, note, transform=ax.transAxes,
               ha='center', va='top', fontsize=9, style='italic')
        
        plt.tight_layout()
        
        # T084: Save and return
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = "stability_cv.svg"
        output_path = self._validate_output_path(output_filename)
        
        try:
            plt.savefig(output_path, format='svg', dpi=300, bbox_inches='tight')
            logger.info(f"Stability plot saved to {output_path}")
        finally:
            plt.close(fig)
        
        # Compute summary stats
        stable_count = sum(1 for sm in stability_metrics if sm.is_stable)
        total_count = len(stability_metrics)
        
        return Visualization(
            viz_type=VisualizationType.STABILITY,
            metric_name="coefficient_of_variation",
            file_path=output_path,
            format="svg",
            title="Metric Stability Across Frameworks",
            caption=(
                f"Scatter plot showing coefficient of variation (CV = σ/μ) for each "
                f"framework-metric combination. {stable_count}/{total_count} measurements "
                f"are stable (CV < {cv_threshold}). Circles indicate stable metrics, "
                f"X markers indicate unstable metrics. "
                f"{'Universally unstable metrics: ' + ', '.join(universally_unstable) + '. ' if universally_unstable else ''}"
                f"Useful for identifying reliability of benchmarking results."
            ),
            groups=frameworks
        )
    
    def generate_outlier_run_plot(
        self,
        outlier_data: List[OutlierInfo],
        framework_name: str,
        metric_name: str,
        all_values: List[float]
    ) -> Visualization:
        """
        Generate outlier run identification plot (T089-T099, US8).
        
        Creates box plot with individual run markers, highlighting outliers
        detected via IQR method.
        
        Args:
            outlier_data: List of OutlierInfo objects for all runs
            framework_name: Name of framework being analyzed
            metric_name: Name of metric being analyzed
            all_values: All run values for context
        
        Returns:
            Visualization object with metadata
        
        Raises:
            ValueError: If outlier_data is empty or all_values is empty
        """
        import logging
        
        logger = logging.getLogger(__name__)
        
        # T089: Validate inputs
        if not outlier_data:
            raise ValueError("Cannot create outlier plot with empty outlier_data")
        if not all_values:
            raise ValueError("Cannot create outlier plot with empty all_values")
        
        # T090, T091: Create box plot with individual points
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Extract values
        values = np.array(all_values)
        outlier_indices = {od.run_index for od in outlier_data if od.is_outlier}
        
        # Create box plot
        bp = ax.boxplot([values], vert=False, widths=0.5, patch_artist=True,
                        boxprops=dict(facecolor='lightblue', alpha=0.7),
                        medianprops=dict(color='red', linewidth=2),
                        whiskerprops=dict(linewidth=1.5),
                        capprops=dict(linewidth=1.5))
        
        # T092, T093: Overlay individual runs with color coding
        y_positions = np.ones(len(values)) + np.random.normal(0, 0.02, len(values))  # Jitter
        
        for i, (val, y_pos) in enumerate(zip(values, y_positions)):
            if i in outlier_indices:
                # Outlier: red X marker
                ax.scatter(val, y_pos, marker='X', s=150, 
                          color='red', edgecolors='darkred', linewidths=2,
                          alpha=0.9, zorder=3,
                          label='Outlier' if i == min(outlier_indices) else "")
            else:
                # Normal: blue circle marker
                ax.scatter(val, y_pos, marker='o', s=80,
                          color='blue', edgecolors='darkblue', linewidths=1,
                          alpha=0.6, zorder=2,
                          label='Normal Run' if i == 0 else "")
        
        # T095: Add run index labels for outliers
        for od in outlier_data:
            if od.is_outlier:
                ax.text(od.value, 1.0 + 0.15, f'Run {od.run_index}',
                       ha='center', va='bottom', fontsize=9,
                       bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
        
        # T094: Annotate IQR factor
        if outlier_data:
            iqr_factor = outlier_data[0].iqr_factor
            ax.text(0.02, 0.98, f'IQR Factor: {iqr_factor}×',
                   transform=ax.transAxes, va='top', ha='left',
                   fontsize=11, fontweight='bold',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
        
        # T098: Check if no outliers found
        outlier_count = len(outlier_indices)
        if outlier_count == 0:
            ax.text(0.5, 1.15, '✓ No Outliers Detected',
                   transform=ax.transAxes, ha='center', va='bottom',
                   fontsize=12, fontweight='bold',
                   bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))
        
        ax.set_xlabel(self._format_metric_label(metric_name), 
                     fontsize=12, fontweight='bold')
        ax.set_yticks([1])
        ax.set_yticklabels([framework_name], fontsize=11, fontweight='bold')
        ax.set_title(f'Outlier Detection: {framework_name} - {metric_name}',
                    fontsize=14, fontweight='bold')
        
        # T096: Handle legend (remove duplicates)
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys(),
                 loc='best', framealpha=0.9)
        
        ax.grid(True, alpha=0.3, axis='x')
        
        # T099: Add interpretation note
        note = (
            f"Box plot shows quartiles (Q1, median, Q3) and whiskers at "
            f"{iqr_factor}×IQR. Red X markers indicate outlier runs. "
            f"{outlier_count}/{len(values)} runs identified as outliers. "
            "Useful for data quality assessment and identifying anomalous benchmark runs."
        )
        ax.text(0.5, -0.15, note, transform=ax.transAxes,
               ha='center', va='top', fontsize=9, style='italic')
        
        plt.tight_layout()
        
        # T097: Save and return
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"outlier_{framework_name}_{metric_name}.svg"
        output_path = self._validate_output_path(output_filename)
        
        try:
            plt.savefig(output_path, format='svg', dpi=300, bbox_inches='tight')
            logger.info(f"Outlier plot saved to {output_path}")
        finally:
            plt.close(fig)
        
        return Visualization(
            viz_type=VisualizationType.OUTLIER_RUN,
            metric_name=metric_name,
            file_path=output_path,
            format="svg",
            title=f"Outlier Detection: {framework_name} - {metric_name}",
            caption=(
                f"Box plot with individual run markers for {framework_name} on {metric_name}. "
                f"Outliers detected using {iqr_factor}×IQR method: {outlier_count}/{len(values)} "
                f"runs flagged. Red X markers indicate outliers, blue circles indicate normal runs. "
                f"Outlier runs: {', '.join(f'#{od.run_index}' for od in outlier_data if od.is_outlier)}. "
                f"Used for data quality validation and identifying problematic benchmark executions."
            ),
            groups=[framework_name]
        )
    
    def generate_all_enhanced_plots(
        self,
        statistical_findings: 'StatisticalFindings',
        quality_metric: str = "completeness_rate",
        cv_threshold: float = 0.3,
        iqr_factor: float = 1.5
    ) -> List[Visualization]:
        """
        Generate all enhanced statistical plots in one call (T100-T108, Phase 11).
        
        Orchestrates batch generation of all 8 new visualization types from a single
        StatisticalFindings object. Handles missing data gracefully.
        
        Args:
            statistical_findings: Complete statistical analysis results
            quality_metric: Name of quality metric for normalized cost (default "completeness_rate")
            cv_threshold: Threshold for stability classification (default 0.3)
            iqr_factor: IQR multiplier for outlier detection (default 1.5)
        
        Returns:
            List of Visualization objects for all successfully generated plots
        """
        import logging
        
        logger = logging.getLogger(__name__)
        logger.info("Starting batch generation of enhanced statistical plots")
        
        # Validate input - fail fast if fundamentally broken
        if not statistical_findings:
            raise ValueError("statistical_findings cannot be None")
        if not hasattr(statistical_findings, 'distributions'):
            raise AttributeError("statistical_findings must have 'distributions' attribute")
        if not hasattr(statistical_findings, 'effect_sizes'):
            raise AttributeError("statistical_findings must have 'effect_sizes' attribute")
        
        visualizations = []
        
        # STEP 1: Transform flat lists into nested dictionaries for easier access
        # Build metric_distributions: Dict[metric_name, Dict[framework, MetricDistribution]]
        metric_distributions = {}
        for dist in statistical_findings.distributions:
            if dist.metric_name not in metric_distributions:
                metric_distributions[dist.metric_name] = {}
            metric_distributions[dist.metric_name][dist.group_name] = dist
        
        # Build effect_sizes_by_metric: Dict[metric_name, Dict[comparison_key, EffectSize]]
        effect_sizes_by_metric = {}
        for es in statistical_findings.effect_sizes:
            if es.metric_name not in effect_sizes_by_metric:
                effect_sizes_by_metric[es.metric_name] = {}
            pair_key = f"{es.group1} vs {es.group2}"
            effect_sizes_by_metric[es.metric_name][pair_key] = es
        
        # Build raw_run_data: Dict[metric_name, Dict[framework, List[float]]]
        raw_run_data = {}
        for dist in statistical_findings.distributions:
            if dist.metric_name not in raw_run_data:
                raw_run_data[dist.metric_name] = {}
            # MetricDistribution.values is np.ndarray - convert to list
            raw_run_data[dist.metric_name][dist.group_name] = dist.values.tolist() if hasattr(dist.values, 'tolist') else list(dist.values)
        
        logger.info(f"Transformed data: {len(metric_distributions)} metrics, "
                   f"{len(effect_sizes_by_metric)} metrics with effect sizes, "
                   f"{len(raw_run_data)} metrics with raw data")
        
        # FAIL FAST: Core data must exist
        if not metric_distributions:
            raise ValueError("No metric distributions found in statistical_findings - cannot generate visualizations")
        if not effect_sizes_by_metric:
            raise ValueError("No effect sizes found in statistical_findings - cannot generate visualizations")
        
        # T101: US1 - Effect Size Panel (REQUIRED - fail if missing)
        logger.info("Generating effect size panels...")
        for metric, effect_sizes in effect_sizes_by_metric.items():
            # effect_sizes is a dict mapping "A vs B" -> EffectSize; the
            # generator expects a mapping metric -> list[EffectSize], so
            # convert accordingly to avoid treating the metric string as an
            # iterable (which previously caused single-character metric handling).
            metric_map = {metric: list(effect_sizes.values())}
            viz = self.generate_effect_size_panel(metric_map)
            visualizations.append(viz)
            logger.info(f"✓ Generated effect size panel for {metric}")
        
        # T102: US2 - Efficiency Plot (REQUIRED if time+cost metrics exist)
        logger.info("Generating efficiency plot...")
        time_dists = {k: v for k, v in metric_distributions.items() 
                     if 'time' in k.lower() or 'duration' in k.lower()}
        cost_dists = {k: v for k, v in metric_distributions.items()
                     if 'cost' in k.lower()}
        
        if time_dists and cost_dists:
            time_metric = list(time_dists.keys())[0]
            cost_metric = list(cost_dists.keys())[0]
            
            viz = self.generate_efficiency_plot(
                time_distributions=time_dists[time_metric],  # Dict[framework, MetricDistribution]
                cost_distributions=cost_dists[cost_metric],  # Dict[framework, MetricDistribution]
                time_metric=time_metric,
                cost_metric=cost_metric
            )
            visualizations.append(viz)
            logger.info(f"✓ Generated efficiency plot ({time_metric} vs {cost_metric})")
        else:
            # This is an EXPECTED edge case - not all experiments track time/cost
            logger.warning(f"⚠ Skipping efficiency plot - missing required metrics (time: {bool(time_dists)}, cost: {bool(cost_dists)})")
        
        # T103: US3 - Regression Plot (REQUIRED if token+cost metrics exist)
        logger.info("Generating regression plot...")
        token_dists = {k: v for k, v in metric_distributions.items()
                      if 'token' in k.lower() and 'total' in k.lower()}
        cost_dists = {k: v for k, v in metric_distributions.items()
                     if 'cost' in k.lower() and 'total' in k.lower()}
        
        if token_dists and cost_dists:
            token_metric = list(token_dists.keys())[0]
            cost_metric = list(cost_dists.keys())[0]
            
            # Extract cached tokens if available (optional)
            cached_dists = {k: v for k, v in metric_distributions.items()
                           if 'cached' in k.lower() and 'token' in k.lower()}
            cached_metric = list(cached_dists.keys())[0] if cached_dists else None
            
            viz = self.generate_regression_plot(
                x_distributions=token_dists[token_metric],  # Dict[framework, MetricDistribution]
                y_distributions=cost_dists[cost_metric],    # Dict[framework, MetricDistribution]
                x_metric=token_metric,
                y_metric=cost_metric,
                cached_tokens=cached_dists.get(cached_metric) if cached_metric else None
            )
            visualizations.append(viz)
            logger.info(f"✓ Generated regression plot ({token_metric} vs {cost_metric})")
        else:
            # EXPECTED edge case - not all experiments have token/cost data
            logger.warning(f"⚠ Skipping regression plot - missing required metrics (tokens: {bool(token_dists)}, cost: {bool(cost_dists)})")
        
        # T104: US4 - Overlap Plots (OPTIONAL - only for small effect sizes)
        logger.info("Checking for overlap plots (small effect sizes)...")
        overlap_count = 0
        for metric, effect_sizes in effect_sizes_by_metric.items():
            for pair_key, es in effect_sizes.items():
                # Generate overlap plot for small effects (|δ| < 0.3)
                if abs(es.value) < 0.3 and metric in metric_distributions:
                    # Extract the two groups from pair_key
                    parts = pair_key.split(' vs ')
                    if len(parts) == 2:
                        group_a, group_b = parts[0], parts[1]
                        
                        # Get distributions for both groups
                        if group_a in metric_distributions[metric] and group_b in metric_distributions[metric]:
                            dist_a = metric_distributions[metric][group_a]
                            dist_b = metric_distributions[metric][group_b]
                            
                            # Find corresponding p-value from statistical tests
                            p_value = 0.05  # Default - should find from statistical_tests
                            for test in statistical_findings.statistical_tests:
                                if (test.metric_name == metric and 
                                    set([group_a, group_b]) == set(test.groups)):
                                    p_value = test.p_value
                                    break
                            
                            viz = self.generate_overlap_plot(
                                dist_a,
                                dist_b,
                                metric,
                                es,
                                p_value,
                                plot_type="density"
                            )
                            visualizations.append(viz)
                            overlap_count += 1
                            logger.info(f"✓ Generated overlap plot for {metric} ({group_a} vs {group_b}, δ={es.value:.3f})")
        
        if overlap_count == 0:
            logger.info("ℹ No small effect sizes detected - overlap plots not needed")
        
        # T105: US5 - Normalized Cost Plot (OPTIONAL - requires cost + quality metric)
        logger.info("Generating normalized cost plot...")
        cost_dists_full = {k: v for k, v in metric_distributions.items()
                     if 'cost' in k.lower() and 'total' in k.lower()}
        quality_dists = {k: v for k, v in metric_distributions.items()
                        if quality_metric in k.lower()}
        
        if cost_dists_full and quality_dists:
            cost_metric_name = list(cost_dists_full.keys())[0]
            quality_metric_key = list(quality_dists.keys())[0]
            
            viz = self.generate_normalized_cost_plot(
                cost_dists_full[cost_metric_name],
                quality_dists[quality_metric_key],
                quality_metric_key
            )
            visualizations.append(viz)
            logger.info(f"✓ Generated normalized cost plot (cost per {quality_metric_key})")
        else:
            # EXPECTED edge case - quality metrics are optional
            logger.warning(f"⚠ Skipping normalized cost plot - missing quality metric '{quality_metric}' (cost: {bool(cost_dists_full)})")
        
        # T106: US6 - Rank Plot (REQUIRED - all experiments have rankable metrics)
        logger.info("Generating rank plot...")
        rank_data = []
        frameworks = set()
        
        for metric_name, dist_dict in metric_distributions.items():
            if isinstance(dist_dict, dict):
                # Determine if lower is better (True for time/cost, False for quality/accuracy)
                is_lower_better = any(keyword in metric_name.lower() 
                                    for keyword in ['time', 'cost', 'duration', 'latency'])
                
                # Sort frameworks by mean (ascending for lower_better, descending otherwise)
                sorted_frameworks = sorted(
                    dist_dict.items(),
                    key=lambda x: x[1].mean,
                    reverse=not is_lower_better
                )
                
                # Assign ranks (1 = best)
                for rank, (framework, dist) in enumerate(sorted_frameworks, start=1):
                    frameworks.add(framework)
                    # Check for ties with previous rank
                    tied = False
                    if rank > 1:
                        prev_mean = sorted_frameworks[rank-2][1].mean
                        if abs(dist.mean - prev_mean) < 1e-6:
                            tied = True
                    
                    rank_data.append(RankData(
                        framework=framework,
                        metric=metric_name,
                        rank=rank,
                        tied=tied
                    ))
        
        if rank_data and len(frameworks) >= 2:
            viz = self.generate_rank_plot(rank_data, list(frameworks))
            visualizations.append(viz)
            logger.info(f"✓ Generated rank plot for {len(frameworks)} frameworks across {len(metric_distributions)} metrics")
        else:
            # This should NEVER happen if we have distributions - FAIL FAST
            raise ValueError(f"Insufficient data for rank plot: {len(frameworks)} frameworks, {len(rank_data)} rank entries")
        
        # T107: US7 - Stability Plot (REQUIRED - all experiments have variability metrics)
        logger.info("Generating stability plot...")
        stability_metrics = []
        
        for metric_name, dist_dict in metric_distributions.items():
            if isinstance(dist_dict, dict):
                for framework, dist in dist_dict.items():
                    # Compute coefficient of variation (CV = std_dev/mean)
                    cv_value = dist.std_dev / dist.mean if dist.mean > 0 else float('inf')
                    is_stable = cv_value < cv_threshold
                    
                    stability_metrics.append(StabilityMetric(
                        framework=framework,
                        metric=metric_name,
                        cv_value=cv_value,
                        is_stable=is_stable
                    ))
        
        if stability_metrics:
            viz = self.generate_stability_plot(stability_metrics, cv_threshold)
            visualizations.append(viz)
            logger.info(f"✓ Generated stability plot ({len(stability_metrics)} measurements)")
        else:
            # This should NEVER happen - FAIL FAST
            raise ValueError("No stability metrics could be computed from distributions")
        
        # T108: US8 - Outlier Run Plots (OPTIONAL - only if outliers detected)
        logger.info("Checking for outlier run plots...")
        outlier_plot_count = 0
        for metric_name, framework_data in raw_run_data.items():
            for framework, values in framework_data.items():
                # Get the corresponding distribution for outlier info
                if metric_name in metric_distributions and framework in metric_distributions[metric_name]:
                    dist = metric_distributions[metric_name][framework]
                    
                    # Check if this distribution has outliers
                    if hasattr(dist, 'outliers') and len(dist.outliers) > 0:
                        # Build OutlierInfo list
                        outlier_info = []
                        iqr = dist.q3 - dist.q1
                        fence_lower = dist.q1 - iqr_factor * iqr
                        fence_upper = dist.q3 + iqr_factor * iqr
                        
                        for idx, value in enumerate(values):
                            is_outlier = value < fence_lower or value > fence_upper
                            # Calculate IQR factor (how many IQRs away from median)
                            if is_outlier:
                                if value < fence_lower:
                                    iqr_distance = (dist.q1 - value) / iqr if iqr > 0 else 0
                                else:
                                    iqr_distance = (value - dist.q3) / iqr if iqr > 0 else 0
                            else:
                                iqr_distance = 0.0
                            
                            outlier_info.append(OutlierInfo(
                                run_index=idx,
                                value=value,
                                is_outlier=is_outlier,
                                iqr_factor=iqr_distance
                            ))
                        
                        viz = self.generate_outlier_run_plot(
                            outlier_info,
                            framework,
                            metric_name,
                            values
                        )
                        visualizations.append(viz)
                        outlier_plot_count += 1
                        logger.info(f"✓ Generated outlier plot for {metric_name} / {framework}")
        
        if outlier_plot_count == 0:
            logger.info("ℹ No outliers detected - outlier run plots not needed")
        else:
            logger.info(f"✓ Generated {outlier_plot_count} outlier run plots")
        
        logger.info(f"Batch generation complete: {len(visualizations)} plots generated")
        return visualizations

