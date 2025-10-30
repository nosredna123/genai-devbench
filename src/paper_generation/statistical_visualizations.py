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
        Format metric name for axis labels with units (T022).
        
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
            'cost': 'Cost (USD)',
            'success_rate': 'Success Rate (%)',
            'memory_usage': 'Memory Usage (MB)',
            'response_time': 'Response Time (ms)',
        }
        
        # Return mapped label or title-case the metric name
        return label_map.get(metric_name, metric_name.replace('_', ' ').title())
    
    def _magnitude_to_color(self, magnitude: str) -> str:
        """
        Map effect size magnitude to color for forest plots (T022).
        
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
