"""
Visualization generators for BAEs experiment analysis.

This module provides publication-quality visualization functions:
- radar_chart(): Multi-framework radar plots for 6 key metrics
- pareto_plot(): Quality vs cost scatter plots
- timeline_chart(): CRUD coverage and downtime over experiment steps
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np


def radar_chart(
    frameworks_data: Dict[str, Dict[str, float]],
    output_path: str,
    metrics: Optional[List[str]] = None,
    title: str = "Framework Comparison - Radar Chart"
) -> None:
    """
    Generate a radar chart comparing multiple frameworks across metrics.
    
    Args:
        frameworks_data: Dict mapping framework names to metric dictionaries.
                        Example: {
                            "BAEs": {"AUTR": 0.85, "TOK_IN": 12000, ...},
                            "ChatDev": {"AUTR": 0.72, "TOK_IN": 15000, ...}
                        }
        output_path: Path to save the SVG file.
        metrics: List of metric names to plot. Defaults to [AUTR, TOK_IN, T_WALL, CRUDe, ESR, MC].
        title: Chart title.
    
    Raises:
        ValueError: If frameworks_data is empty or metrics are missing.
    """
    if not frameworks_data:
        raise ValueError("frameworks_data cannot be empty")
    
    # Default metrics: 6 key metrics from experiment spec
    if metrics is None:
        metrics = ["AUTR", "TOK_IN", "T_WALL", "CRUDe", "ESR", "MC"]
    
    # Validate all frameworks have all metrics
    for framework, data in frameworks_data.items():
        missing = [m for m in metrics if m not in data]
        if missing:
            raise ValueError(f"Framework {framework} missing metrics: {missing}")
    
    # Normalize metrics to [0, 1] range for radar chart
    normalized_data = {}
    metric_ranges = {}
    
    for metric in metrics:
        values = [frameworks_data[fw][metric] for fw in frameworks_data]
        min_val = min(values)
        max_val = max(values)
        metric_ranges[metric] = (min_val, max_val)
        
        # Normalize each framework's value
        for framework in frameworks_data:
            if framework not in normalized_data:
                normalized_data[framework] = {}
            
            raw_value = frameworks_data[framework][metric]
            if max_val == min_val:
                # All values identical, set to 0.5
                normalized_data[framework][metric] = 0.5
            else:
                normalized_data[framework][metric] = (raw_value - min_val) / (max_val - min_val)
    
    # Number of variables
    num_vars = len(metrics)
    
    # Compute angle for each axis
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    
    # Complete the circle
    angles += angles[:1]
    
    # Create figure with polar projection
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
    
    # Define colors for frameworks (up to 5 frameworks)
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    # Plot each framework
    for idx, (framework, data) in enumerate(normalized_data.items()):
        values = [data[metric] for metric in metrics]
        values += values[:1]  # Complete the circle
        
        color = colors[idx % len(colors)]
        ax.plot(angles, values, 'o-', linewidth=2, label=framework, color=color)
        ax.fill(angles, values, alpha=0.15, color=color)
    
    # Set labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics, size=12)
    
    # Set y-axis limits and labels
    ax.set_ylim(0, 1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'], size=10)
    
    # Add grid
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Add title and legend
    ax.set_title(title, size=16, pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=12)
    
    # Save as SVG
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, format='svg', bbox_inches='tight', dpi=300)
    plt.close()
    
    print(f"Radar chart saved to {output_path}")


def pareto_plot(
    frameworks_data: Dict[str, Dict[str, float]],
    output_path: str,
    title: str = "Pareto Plot: Q* vs TOK_IN"
) -> None:
    """
    Generate a Pareto plot showing quality (Q*) vs cost (TOK_IN).
    
    This scatter plot helps identify the optimal trade-off between
    quality and token consumption across frameworks.
    
    Args:
        frameworks_data: Dict mapping framework names to metric dictionaries.
                        Must contain "Q*" and "TOK_IN" keys.
        output_path: Path to save the SVG file.
        title: Chart title.
    
    Raises:
        ValueError: If frameworks_data is empty or missing required metrics.
    """
    if not frameworks_data:
        raise ValueError("frameworks_data cannot be empty")
    
    # Validate required metrics
    required = ["Q*", "TOK_IN"]
    for framework, data in frameworks_data.items():
        missing = [m for m in required if m not in data]
        if missing:
            raise ValueError(f"Framework {framework} missing metrics: {missing}")
    
    # Extract data
    frameworks = list(frameworks_data.keys())
    q_star_values = [frameworks_data[fw]["Q*"] for fw in frameworks]
    tok_in_values = [frameworks_data[fw]["TOK_IN"] for fw in frameworks]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Define colors for frameworks
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    # Plot scatter points
    for idx, framework in enumerate(frameworks):
        color = colors[idx % len(colors)]
        ax.scatter(
            tok_in_values[idx],
            q_star_values[idx],
            s=200,
            alpha=0.7,
            color=color,
            edgecolors='black',
            linewidth=1.5,
            label=framework
        )
        
        # Add framework label next to point
        ax.annotate(
            framework,
            (tok_in_values[idx], q_star_values[idx]),
            xytext=(10, 10),
            textcoords='offset points',
            fontsize=11,
            bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.3)
        )
    
    # Add Pareto frontier (optional enhancement)
    # Sort by TOK_IN and connect dominant points
    sorted_indices = np.argsort(tok_in_values)
    sorted_tok = [tok_in_values[i] for i in sorted_indices]
    sorted_q = [q_star_values[i] for i in sorted_indices]
    
    # Find Pareto frontier points (maximize Q*, minimize TOK_IN)
    pareto_points = []
    max_q_so_far = -np.inf
    for tok, q in zip(sorted_tok, sorted_q):
        if q > max_q_so_far:
            pareto_points.append((tok, q))
            max_q_so_far = q
    
    if len(pareto_points) > 1:
        pareto_tok, pareto_q = zip(*pareto_points)
        ax.plot(
            pareto_tok,
            pareto_q,
            'k--',
            alpha=0.4,
            linewidth=1,
            label='Pareto Frontier'
        )
    
    # Set labels and title
    ax.set_xlabel('TOK_IN (Token Input)', fontsize=14)
    ax.set_ylabel('Q* (Quality Score)', fontsize=14)
    ax.set_title(title, fontsize=16, pad=20)
    
    # Add grid
    ax.grid(True, linestyle='--', alpha=0.5)
    
    # Add legend
    ax.legend(loc='best', fontsize=12)
    
    # Format axes
    ax.tick_params(labelsize=12)
    
    # Save as SVG
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, format='svg', bbox_inches='tight', dpi=300)
    plt.close()
    
    print(f"Pareto plot saved to {output_path}")


def timeline_chart(
    timeline_data: Dict[str, Dict[int, Dict[str, float]]],
    output_path: str,
    title: str = "Timeline: CRUD Coverage & Downtime"
) -> None:
    """
    Generate a timeline chart showing CRUD coverage and downtime over steps.
    
    This dual-axis chart displays:
    - Left axis (bars): CRUD coverage count (0-12) per step
    - Right axis (line): Downtime incidents per step
    
    Args:
        timeline_data: Dict mapping framework names to step-indexed data.
                      Example: {
                          "BAEs": {
                              1: {"CRUDe": 8, "ZDI": 0},
                              2: {"CRUDe": 10, "ZDI": 1},
                              ...
                          }
                      }
        output_path: Path to save the SVG file.
        title: Chart title.
    
    Raises:
        ValueError: If timeline_data is empty or missing required metrics.
    """
    if not timeline_data:
        raise ValueError("timeline_data cannot be empty")
    
    # Validate structure and extract steps
    all_steps = set()
    for framework, steps_data in timeline_data.items():
        if not steps_data:
            raise ValueError(f"Framework {framework} has no step data")
        
        all_steps.update(steps_data.keys())
        
        for step, metrics in steps_data.items():
            if "CRUDe" not in metrics or "ZDI" not in metrics:
                raise ValueError(
                    f"Framework {framework} step {step} missing CRUDe or ZDI"
                )
    
    steps = sorted(all_steps)
    num_steps = len(steps)
    
    # Create figure with dual y-axes
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()
    
    # Define colors and bar width
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    num_frameworks = len(timeline_data)
    bar_width = 0.8 / num_frameworks
    
    frameworks = list(timeline_data.keys())
    
    # Plot CRUD coverage as grouped bars (left axis)
    for idx, framework in enumerate(frameworks):
        crude_values = []
        for step in steps:
            if step in timeline_data[framework]:
                crude_values.append(timeline_data[framework][step]["CRUDe"])
            else:
                crude_values.append(0)
        
        x_positions = np.arange(num_steps) + idx * bar_width
        color = colors[idx % len(colors)]
        
        ax1.bar(
            x_positions,
            crude_values,
            bar_width,
            label=f"{framework} CRUD",
            color=color,
            alpha=0.7,
            edgecolor='black',
            linewidth=0.5
        )
    
    # Plot downtime incidents as lines (right axis)
    for idx, framework in enumerate(frameworks):
        zdi_values = []
        for step in steps:
            if step in timeline_data[framework]:
                zdi_values.append(timeline_data[framework][step]["ZDI"])
            else:
                zdi_values.append(0)
        
        x_positions = np.arange(num_steps) + 0.4  # Center of grouped bars
        color = colors[idx % len(colors)]
        
        ax2.plot(
            x_positions,
            zdi_values,
            marker='o',
            linewidth=2,
            markersize=8,
            label=f"{framework} Downtime",
            color=color,
            linestyle='--'
        )
    
    # Configure left axis (CRUD coverage)
    ax1.set_xlabel('Step', fontsize=14)
    ax1.set_ylabel('CRUD Coverage (0-12)', fontsize=14, color='black')
    ax1.set_ylim(0, 12)
    ax1.set_yticks(range(0, 13, 2))
    ax1.tick_params(axis='y', labelcolor='black', labelsize=12)
    ax1.tick_params(axis='x', labelsize=12)
    
    # Configure right axis (downtime)
    ax2.set_ylabel('Downtime Incidents (ZDI)', fontsize=14, color='darkred')
    ax2.tick_params(axis='y', labelcolor='darkred', labelsize=12)
    
    # Set x-axis
    ax1.set_xticks(np.arange(num_steps) + 0.4)
    ax1.set_xticklabels([f"Step {s}" for s in steps])
    
    # Add title
    ax1.set_title(title, fontsize=16, pad=20)
    
    # Add grid (only on left axis)
    ax1.grid(True, axis='y', linestyle='--', alpha=0.5)
    
    # Combine legends from both axes
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(
        lines1 + lines2,
        labels1 + labels2,
        loc='upper left',
        fontsize=10,
        ncol=2
    )
    
    # Save as SVG
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, format='svg', bbox_inches='tight', dpi=300)
    plt.close()
    
    print(f"Timeline chart saved to {output_path}")


def load_metrics_from_run(run_dir: str) -> Dict[str, float]:
    """
    Load metrics from a single run directory.
    
    Args:
        run_dir: Path to run directory containing metrics.json.
    
    Returns:
        Dict of metric names to values.
    
    Raises:
        FileNotFoundError: If metrics.json doesn't exist.
        json.JSONDecodeError: If metrics.json is malformed.
    """
    metrics_path = Path(run_dir) / "metrics.json"
    
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    
    with open(metrics_path, 'r') as f:
        return json.load(f)


def aggregate_framework_metrics(
    framework_run_dirs: List[str]
) -> Dict[str, float]:
    """
    Aggregate metrics across multiple runs of the same framework.
    
    Computes mean values for all metrics across runs.
    
    Args:
        framework_run_dirs: List of paths to run directories for a framework.
    
    Returns:
        Dict of metric names to mean values.
    
    Raises:
        ValueError: If framework_run_dirs is empty.
    """
    if not framework_run_dirs:
        raise ValueError("framework_run_dirs cannot be empty")
    
    # Load all runs
    all_metrics = []
    for run_dir in framework_run_dirs:
        metrics = load_metrics_from_run(run_dir)
        all_metrics.append(metrics)
    
    # Compute means
    metric_names = all_metrics[0].keys()
    aggregated = {}
    
    for metric in metric_names:
        values = [m[metric] for m in all_metrics]
        aggregated[metric] = np.mean(values)
    
    return aggregated
