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


def _infer_format_from_path(output_path: str) -> str:
    """Infer image format from file extension.
    
    Args:
        output_path: Path to output file
        
    Returns:
        Format string for matplotlib savefig (e.g., 'png', 'svg', 'pdf')
        
    Example:
        >>> _infer_format_from_path('chart.png')
        'png'
        >>> _infer_format_from_path('chart.svg')
        'svg'
    """
    extension = Path(output_path).suffix.lower().lstrip('.')
    # Map common extensions to matplotlib format names
    format_map = {
        'png': 'png',
        'svg': 'svg',
        'pdf': 'pdf',
        'jpg': 'jpeg',
        'jpeg': 'jpeg',
    }
    return format_map.get(extension, 'png')  # Default to PNG if unknown


# Friendly metric labels for visualizations
METRIC_LABELS = {
    'AUTR': 'Test Automation\nRate',
    'TOK_IN': 'Input Tokens',
    'T_WALL_seconds': 'Wall Time\n(seconds)',
    'CRUDe': 'CRUD\nCoverage',
    'ESR': 'Emerging State\nRate',
    'MC': 'Model Call\nEfficiency',
    'Q*': 'Quality\nScore',
    'AEI': 'Automation\nEfficiency',
    'TOK_OUT': 'Output Tokens',
    'ZDI': 'Downtime\n(seconds)',
    'HIT': 'Human\nInterventions',
    'HEU': 'Human\nEffort',
    'UTT': 'Task\nCount',
    'API_CALLS': 'API Calls\n(count)',
    'CACHED_TOKENS': 'Cached Tokens',
    'CACHE_HIT_RATE': 'Cache Hit\nRate (%)',
}


def _get_metric_label(metric: str) -> str:
    """Get friendly label for metric, fallback to metric name if not in map."""
    return METRIC_LABELS.get(metric, metric)


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
                            "BAEs": {"TOK_IN": 12000, "TOK_OUT": 8000, ...},
                            "ChatDev": {"TOK_IN": 15000, "TOK_OUT": 10000, ...}
                        }
        output_path: Path to save the SVG file.
        metrics: List of metric names to plot. Defaults to 6 reliably measured metrics:
                [TOK_IN, TOK_OUT, T_WALL_seconds, API_CALLS, CACHED_TOKENS, ZDI].
        title: Chart title.
    
    Raises:
        ValueError: If frameworks_data is empty or metrics are missing.
    """
    if not frameworks_data:
        raise ValueError("frameworks_data cannot be empty")
    
    # Default metrics: 6 reliably measured metrics (no AUTR/CRUDe/ESR/MC)
    # See docs/RELIABLE_METRICS_IMPLEMENTATION_PLAN.md for rationale
    if metrics is None:
        metrics = ["TOK_IN", "TOK_OUT", "T_WALL_seconds", "API_CALLS", "CACHED_TOKENS", "ZDI"]
    
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
    
    # Set labels - use friendly names
    ax.set_xticks(angles[:-1])
    friendly_labels = [_get_metric_label(m) for m in metrics]
    ax.set_xticklabels(friendly_labels, size=11)
    
    # Set y-axis limits and labels
    ax.set_ylim(0, 1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'], size=10)
    
    # Add grid
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Add title and legend
    ax.set_title(title, size=16, pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=12)
    
    # Save with format inferred from filename extension
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, format=_infer_format_from_path(output_path), bbox_inches='tight', dpi=300)
    plt.close()
    
    print(f"Radar chart saved to {output_path}")


def pareto_plot(
    frameworks_data: Dict[str, Dict[str, float]],
    output_path: str,
    title: str = "Pareto Plot: Q* vs TOK_IN"
) -> None:
    """
    Generate a Pareto plot showing quality (Q*) vs cost (TOK_IN).
    
    ⚠️ DEPRECATED: This visualization uses Q* which is not measured
    in current experiments (always 0). Will be re-enabled once quality
    metrics are implemented. See docs/RELIABLE_METRICS_IMPLEMENTATION_PLAN.md
    
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
    import warnings
    warnings.warn(
        "pareto_plot() deprecated: uses unmeasured metric Q* (always 0). "
        "Skipping visualization generation. See docs/RELIABLE_METRICS_IMPLEMENTATION_PLAN.md",
        DeprecationWarning,
        stacklevel=2
    )
    return  # Early exit - skip generation
    
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
    
    # Set labels and title with friendly names
    ax.set_xlabel('Input Tokens', fontsize=14)
    ax.set_ylabel('Quality Score (Q*)', fontsize=14)
    ax.set_title(title, fontsize=16, pad=20)
    
    # Add grid
    ax.grid(True, linestyle='--', alpha=0.5)
    
    # Add legend outside plot area (upper right, outside)
    ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), fontsize=12, 
              frameon=True, fancybox=True, shadow=True)
    
    # Format axes
    ax.tick_params(labelsize=12)
    
    # Save as SVG
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, format=_infer_format_from_path(output_path), bbox_inches='tight', dpi=300)
    plt.close()
    
    print(f"Pareto plot saved to {output_path}")


def timeline_chart(
    timeline_data: Dict[str, Dict[int, Dict[str, float]]],
    output_path: str,
    title: str = "Timeline: CRUD Coverage & Downtime"
) -> None:
    """
    Generate a timeline chart showing CRUD coverage and downtime over steps.
    
    ⚠️ DEPRECATED: This visualization uses CRUDe which is not measured
    in current experiments (always 0). Will be re-enabled once quality
    metrics are implemented. See docs/RELIABLE_METRICS_IMPLEMENTATION_PLAN.md
    
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
    import warnings
    warnings.warn(
        "timeline_chart() deprecated: uses unmeasured metric CRUDe (always 0). "
        "Skipping visualization generation. See docs/RELIABLE_METRICS_IMPLEMENTATION_PLAN.md",
        DeprecationWarning,
        stacklevel=2
    )
    return  # Early exit - skip generation
    
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
    
    # Configure left axis (CRUD coverage) with friendly labels
    ax1.set_xlabel('Evolution Step', fontsize=14)
    ax1.set_ylabel('CRUD Operations Coverage (0-12)', fontsize=14, color='black')
    ax1.set_ylim(0, 12)
    ax1.set_yticks(range(0, 13, 2))
    ax1.tick_params(axis='y', labelcolor='black', labelsize=12)
    ax1.tick_params(axis='x', labelsize=12)
    
    # Configure right axis (downtime) with friendly labels
    ax2.set_ylabel('Downtime (seconds)', fontsize=14, color='darkred')
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
    plt.savefig(output_path, format=_infer_format_from_path(output_path), bbox_inches='tight', dpi=300)
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


def api_efficiency_chart(
    frameworks_data: Dict[str, Dict[str, float]],
    output_path: str,
    title: str = "API Efficiency: Calls vs Token Consumption"
) -> None:
    """
    Generate a scatter plot showing API calls vs total tokens for each framework.
    
    This visualization helps understand:
    - Which frameworks make more efficient use of each API call
    - Token-per-call ratio differences between frameworks
    - Trade-offs between call frequency and token consumption
    
    Args:
        frameworks_data: Dict mapping framework names to metric dictionaries.
                        Must contain 'API_CALLS', 'TOK_IN', and 'TOK_OUT' keys.
        output_path: Path to save the SVG file.
        title: Chart title.
    
    Raises:
        ValueError: If frameworks_data is empty or missing required metrics.
    """
    if not frameworks_data:
        raise ValueError("frameworks_data cannot be empty")
    
    # Validate required metrics
    required = ['API_CALLS', 'TOK_IN', 'TOK_OUT']
    for framework, data in frameworks_data.items():
        missing = [m for m in required if m not in data]
        if missing:
            raise ValueError(f"Framework {framework} missing metrics: {missing}")
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # Colors for each framework
    colors = {'baes': '#2E86AB', 'chatdev': '#A23B72', 'ghspec': '#F18F01'}
    markers = {'baes': 'o', 'chatdev': 's', 'ghspec': '^'}
    
    # Plot each framework
    for framework, data in frameworks_data.items():
        api_calls = data['API_CALLS']
        total_tokens = data['TOK_IN'] + data['TOK_OUT']
        tokens_per_call = total_tokens / api_calls if api_calls > 0 else 0
        
        color = colors.get(framework.lower(), '#333333')
        marker = markers.get(framework.lower(), 'o')
        
        # Plot point
        ax.scatter(api_calls, total_tokens, s=200, alpha=0.7, 
                  color=color, marker=marker, label=framework, edgecolors='black', linewidth=1.5)
        
        # Add annotation with tokens/call ratio
        ax.annotate(f'{tokens_per_call:,.0f} tok/call',
                   xy=(api_calls, total_tokens),
                   xytext=(10, 10), textcoords='offset points',
                   fontsize=9, alpha=0.8,
                   bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.2))
    
    # Add diagonal lines showing constant tokens-per-call ratios
    if frameworks_data:
        max_calls = max(data['API_CALLS'] for data in frameworks_data.values())
        max_tokens = max(data['TOK_IN'] + data['TOK_OUT'] for data in frameworks_data.values())
        
        # Draw reference lines for common ratios (e.g., 1000, 2000, 5000 tokens/call)
        for ratio in [500, 1000, 2000, 5000]:
            if ratio * max_calls * 0.1 < max_tokens * 1.5:  # Only draw if relevant
                x_line = np.linspace(0, max_calls * 1.2, 100)
                y_line = ratio * x_line
                ax.plot(x_line, y_line, '--', alpha=0.3, linewidth=1, color='gray')
                # Label the line
                label_x = max_calls * 0.9
                label_y = ratio * label_x
                if label_y < max_tokens * 1.3:
                    ax.text(label_x, label_y, f'{ratio:,} tok/call', 
                           fontsize=8, alpha=0.5, rotation=45, va='bottom')
    
    ax.set_xlabel('API Calls (count)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Total Tokens (Input + Output)', fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper left', fontsize=10, framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle=':')
    
    # Add interpretation note
    note = "← Lower left = More efficient (fewer calls, fewer tokens)\n→ Upper right = Less efficient (more calls, more tokens)\nSlope = Tokens per call"
    ax.text(0.98, 0.02, note, transform=ax.transAxes,
           fontsize=8, alpha=0.6, ha='right', va='bottom',
           bbox=dict(boxstyle='round,pad=0.5', facecolor='wheat', alpha=0.3))
    
    plt.tight_layout()
    plt.savefig(output_path, format=_infer_format_from_path(output_path), dpi=300, bbox_inches='tight')
    plt.close()


def cache_efficiency_chart(
    frameworks_data: Dict[str, Dict[str, float]],
    output_path: str,
    title: str = "Cache Efficiency Analysis"
) -> None:
    """
    Generate a bar chart showing cache hit rates and cached token percentages.
    
    This visualization compares:
    - Cache hit rate (% of input tokens served from cache)
    - Absolute cached tokens count
    - Potential cost savings from caching
    
    Args:
        frameworks_data: Dict mapping framework names to metric dictionaries.
                        Must contain 'TOK_IN' and 'CACHED_TOKENS' keys.
        output_path: Path to save the SVG file.
        title: Chart title.
    
    Raises:
        ValueError: If frameworks_data is empty or missing required metrics.
    """
    if not frameworks_data:
        raise ValueError("frameworks_data cannot be empty")
    
    # Validate required metrics
    required = ['TOK_IN', 'CACHED_TOKENS']
    for framework, data in frameworks_data.items():
        missing = [m for m in required if m not in data]
        if missing:
            raise ValueError(f"Framework {framework} missing metrics: {missing}")
    
    # Calculate cache hit rates
    cache_data = {}
    for framework, data in frameworks_data.items():
        tok_in = data['TOK_IN']
        cached = data['CACHED_TOKENS']
        hit_rate = (cached / tok_in * 100) if tok_in > 0 else 0
        cache_data[framework] = {
            'hit_rate': hit_rate,
            'cached_tokens': cached,
            'total_input': tok_in
        }
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    frameworks = list(cache_data.keys())
    colors = {'baes': '#2E86AB', 'chatdev': '#A23B72', 'ghspec': '#F18F01'}
    bar_colors = [colors.get(fw.lower(), '#333333') for fw in frameworks]
    
    # Subplot 1: Cache Hit Rate (%)
    hit_rates = [cache_data[fw]['hit_rate'] for fw in frameworks]
    bars1 = ax1.bar(frameworks, hit_rates, color=bar_colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    
    # Add value labels on bars
    for bar, rate in zip(bars1, hit_rates):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{rate:.1f}%',
                ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    ax1.set_ylabel('Cache Hit Rate (%)', fontsize=12, fontweight='bold')
    ax1.set_title('Cache Hit Rate by Framework', fontsize=13, fontweight='bold', pad=15)
    ax1.set_ylim(0, max(hit_rates) * 1.2 if hit_rates else 100)
    ax1.grid(True, alpha=0.3, axis='y', linestyle=':')
    ax1.set_axisbelow(True)
    
    # Subplot 2: Cached Tokens (absolute count)
    cached_tokens = [cache_data[fw]['cached_tokens'] for fw in frameworks]
    bars2 = ax2.bar(frameworks, cached_tokens, color=bar_colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    
    # Add value labels on bars
    for bar, tokens in zip(bars2, cached_tokens):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{tokens:,.0f}',
                ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    ax2.set_ylabel('Cached Tokens (count)', fontsize=12, fontweight='bold')
    ax2.set_title('Total Cached Tokens', fontsize=13, fontweight='bold', pad=15)
    ax2.set_ylim(0, max(cached_tokens) * 1.2 if cached_tokens else 1000)
    ax2.grid(True, alpha=0.3, axis='y', linestyle=':')
    ax2.set_axisbelow(True)
    
    # Format y-axis with thousands separator
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))
    
    # Add interpretation note
    note = "Higher cache hit rate = Better prompt reuse\nCost savings ≈ 50% for cached tokens"
    fig.text(0.5, 0.02, note, ha='center', fontsize=9, alpha=0.6,
            bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.3))
    
    plt.suptitle(title, fontsize=15, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0.05, 1, 0.96])
    plt.savefig(output_path, format=_infer_format_from_path(output_path), dpi=300, bbox_inches='tight')
    plt.close()


def api_calls_timeline(
    frameworks_timeline_data: Dict[str, Dict[int, Dict[str, float]]],
    output_path: str,
    title: str = "API Calls Evolution Across Steps"
) -> None:
    """
    Generate a line chart showing API call patterns across experiment steps.
    
    This visualization tracks:
    - How API call frequency changes as complexity increases
    - Which frameworks scale API usage with task complexity
    - Step-by-step API efficiency patterns
    
    Args:
        frameworks_timeline_data: Dict mapping framework names to step-wise metrics.
                                 Example: {
                                     'BAEs': {
                                         1: {'API_CALLS': 5, 'TOK_IN': 1000, ...},
                                         2: {'API_CALLS': 8, 'TOK_IN': 1500, ...}
                                     },
                                     ...
                                 }
        output_path: Path to save the SVG file.
        title: Chart title.
    
    Raises:
        ValueError: If frameworks_timeline_data is empty.
    """
    if not frameworks_timeline_data:
        raise ValueError("frameworks_timeline_data cannot be empty")
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 7))
    
    colors = {'baes': '#2E86AB', 'chatdev': '#A23B72', 'ghspec': '#F18F01'}
    markers = {'baes': 'o', 'chatdev': 's', 'ghspec': '^'}
    
    # Plot each framework
    for framework, step_data in frameworks_timeline_data.items():
        if not step_data:
            continue
        
        # Extract steps and API calls
        steps = sorted(step_data.keys())
        api_calls = [step_data[step].get('API_CALLS', 0) for step in steps]
        
        color = colors.get(framework.lower(), '#333333')
        marker = markers.get(framework.lower(), 'o')
        
        # Plot line with markers
        ax.plot(steps, api_calls, marker=marker, linewidth=2.5, markersize=10,
               label=framework, color=color, alpha=0.8)
        
        # Add value labels at each point (formatted to 2 decimal places)
        for step, calls in zip(steps, api_calls):
            # Format: show 2 decimals if < 10, otherwise integer
            if calls < 10:
                label_text = f'{calls:.2f}'
            else:
                label_text = f'{int(round(calls))}'
            ax.annotate(label_text, xy=(step, calls), xytext=(0, 8),
                       textcoords='offset points', ha='center',
                       fontsize=9, alpha=0.7, fontweight='bold')
    
    ax.set_xlabel('Experiment Step', fontsize=12, fontweight='bold')
    ax.set_ylabel('API Calls (count)', fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper left', fontsize=11, framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle=':')
    ax.set_axisbelow(True)
    
    # Set integer x-axis (steps 1-6)
    if frameworks_timeline_data:
        all_steps = []
        for step_data in frameworks_timeline_data.values():
            all_steps.extend(step_data.keys())
        if all_steps:
            ax.set_xticks(range(1, max(all_steps) + 1))
    
    # Add task complexity annotations
    task_labels = {
        1: "Basic CRUD",
        2: "Relationships",
        3: "Constraints",
        4: "Validation",
        5: "Filtering",
        6: "Full UI"
    }
    
    # Add subtle background shading for complexity zones
    ax.axvspan(0.5, 2.5, alpha=0.05, color='green', label='_Simple')
    ax.axvspan(2.5, 4.5, alpha=0.05, color='orange', label='_Medium')
    ax.axvspan(4.5, 6.5, alpha=0.05, color='red', label='_Complex')
    
    # Add interpretation note
    note = "Upward trend = Framework needs more API calls as complexity increases\nFlat line = Consistent API efficiency across tasks"
    ax.text(0.98, 0.02, note, transform=ax.transAxes,
           fontsize=8, alpha=0.6, ha='right', va='bottom',
           bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', alpha=0.3))
    
    plt.tight_layout()
    plt.savefig(output_path, format=_infer_format_from_path(output_path), dpi=300, bbox_inches='tight')
    plt.close()


def token_efficiency_chart(
    frameworks_data: Dict[str, List[Dict[str, float]]],
    output_path: str,
    title: str = "Token Efficiency: Input vs Output"
) -> None:
    """
    Generate scatter plot showing input vs output token relationship.
    
    Shows how frameworks trade off input context vs output generation.
    Marker size represents execution time, enabling 3-dimensional comparison.
    
    Args:
        frameworks_data: Dict mapping framework names to lists of run metrics.
                        Each run must contain: TOK_IN, TOK_OUT, T_WALL_seconds
        output_path: Path to save the SVG file.
        title: Chart title.
    
    Raises:
        ValueError: If frameworks_data is empty or missing required metrics.
    """
    if not frameworks_data:
        raise ValueError("frameworks_data cannot be empty")
    
    # Validate required metrics
    required = ["TOK_IN", "TOK_OUT", "T_WALL_seconds"]
    for framework, runs in frameworks_data.items():
        if not runs:
            raise ValueError(f"Framework {framework} has no run data")
        for run in runs:
            missing = [m for m in required if m not in run]
            if missing:
                raise ValueError(f"Framework {framework} run missing metrics: {missing}")
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Define colors for frameworks
    colors = {'baes': '#1f77b4', 'chatdev': '#ff7f0e', 'ghspec': '#2ca02c'}
    markers = {'baes': 'o', 'chatdev': 's', 'ghspec': '^'}
    
    # Plot each framework
    for framework, runs in frameworks_data.items():
        tok_in = [run["TOK_IN"] for run in runs]
        tok_out = [run["TOK_OUT"] for run in runs]
        t_wall = [run["T_WALL_seconds"] for run in runs]
        
        # Normalize time for marker sizes (50-500 range)
        min_time = min(t_wall)
        max_time = max(t_wall)
        if max_time > min_time:
            sizes = [50 + 450 * ((t - min_time) / (max_time - min_time)) for t in t_wall]
        else:
            sizes = [250] * len(t_wall)
        
        color = colors.get(framework.lower(), '#666666')
        marker = markers.get(framework.lower(), 'o')
        
        ax.scatter(
            tok_in,
            tok_out,
            s=sizes,
            c=color,
            marker=marker,
            alpha=0.6,
            edgecolors='black',
            linewidth=1.5,
            label=framework
        )
        
        # Add trend line
        if len(tok_in) > 1:
            z = np.polyfit(tok_in, tok_out, 1)
            p = np.poly1d(z)
            x_trend = np.linspace(min(tok_in), max(tok_in), 100)
            ax.plot(x_trend, p(x_trend), '--', color=color, alpha=0.5, linewidth=2)
    
    # Add diagonal reference line (1:1 ratio)
    all_tokens = []
    for runs in frameworks_data.values():
        all_tokens.extend([run["TOK_IN"] for run in runs])
        all_tokens.extend([run["TOK_OUT"] for run in runs])
    
    if all_tokens:
        max_token = max(all_tokens)
        ax.plot([0, max_token], [0, max_token], 'k:', alpha=0.3, linewidth=1, label='1:1 ratio')
    
    # Labels and formatting
    ax.set_xlabel('Input Tokens (TOK_IN)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Output Tokens (TOK_OUT)', fontsize=14, fontweight='bold')
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='upper left', fontsize=12, framealpha=0.9)
    
    # Add interpretation note
    note = ("Marker size ∝ Execution time\n"
            "Points above 1:1 line = More verbose output\n"
            "Points below 1:1 line = Concise output")
    ax.text(0.98, 0.02, note, transform=ax.transAxes,
           fontsize=9, alpha=0.7, ha='right', va='bottom',
           bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', alpha=0.5))
    
    # Save as SVG
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, format=_infer_format_from_path(output_path), bbox_inches='tight', dpi=300)
    plt.close()
    
    print(f"Token efficiency chart saved to {output_path}")


def api_efficiency_bar_chart(
    frameworks_data: Dict[str, Dict[str, float]],
    output_path: str,
    title: str = "API Call Efficiency by Framework"
) -> None:
    """
    Generate bar chart comparing API call efficiency.
    
    Shows API_CALLS count with annotations for tokens-per-call ratio,
    enabling comparison of batching and retry strategies.
    
    Args:
        frameworks_data: Dict mapping framework names to aggregated metrics.
                        Must contain: API_CALLS, TOK_IN
        output_path: Path to save the SVG file.
        title: Chart title.
    
    Raises:
        ValueError: If frameworks_data is empty or missing required metrics.
    """
    if not frameworks_data:
        raise ValueError("frameworks_data cannot be empty")
    
    # Validate required metrics
    required = ["API_CALLS", "TOK_IN"]
    for framework, data in frameworks_data.items():
        missing = [m for m in required if m not in data]
        if missing:
            raise ValueError(f"Framework {framework} missing metrics: {missing}")
    
    # Extract data
    frameworks = list(frameworks_data.keys())
    api_calls = [frameworks_data[fw]["API_CALLS"] for fw in frameworks]
    tok_in = [frameworks_data[fw]["TOK_IN"] for fw in frameworks]
    
    # Calculate tokens per call
    tokens_per_call = [tok / calls if calls > 0 else 0 
                      for tok, calls in zip(tok_in, api_calls)]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Define colors
    colors = {'baes': '#1f77b4', 'chatdev': '#ff7f0e', 'ghspec': '#2ca02c'}
    bar_colors = [colors.get(fw.lower(), '#666666') for fw in frameworks]
    
    # Create bars
    x_pos = np.arange(len(frameworks))
    bars = ax.bar(x_pos, api_calls, color=bar_colors, alpha=0.7, 
                  edgecolor='black', linewidth=1.5)
    
    # Add value labels on bars
    for i, (bar, calls, tpc) in enumerate(zip(bars, api_calls, tokens_per_call)):
        height = bar.get_height()
        # API calls count
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{int(calls)}',
               ha='center', va='bottom', fontsize=12, fontweight='bold')
        # Tokens per call
        ax.text(bar.get_x() + bar.get_width()/2., height/2,
               f'{int(tpc):,}\ntok/call',
               ha='center', va='center', fontsize=10, 
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    
    # Labels and formatting
    ax.set_xlabel('Framework', fontsize=14, fontweight='bold')
    ax.set_ylabel('API Calls (count)', fontsize=14, fontweight='bold')
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(frameworks, fontsize=12)
    ax.grid(True, axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # Add interpretation note
    note = ("Lower bars = Fewer API calls (more efficient batching)\n"
            "Higher tok/call = Better token utilization per request")
    ax.text(0.98, 0.98, note, transform=ax.transAxes,
           fontsize=9, alpha=0.7, ha='right', va='top',
           bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', alpha=0.5))
    
    # Save as SVG
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, format=_infer_format_from_path(output_path), bbox_inches='tight', dpi=300)
    plt.close()
    
    print(f"API efficiency bar chart saved to {output_path}")


def cache_efficiency_chart(
    frameworks_data: Dict[str, Dict[str, float]],
    output_path: str,
    title: str = "Cache Hit Rate Comparison"
) -> None:
    """
    Generate stacked bar chart showing cache efficiency.
    
    Shows proportion of cached vs uncached tokens, with percentage labels
    indicating cache hit rate for each framework.
    
    Args:
        frameworks_data: Dict mapping framework names to aggregated metrics.
                        Must contain: TOK_IN, CACHED_TOKENS
        output_path: Path to save the SVG file.
        title: Chart title.
    
    Raises:
        ValueError: If frameworks_data is empty or missing required metrics.
    """
    if not frameworks_data:
        raise ValueError("frameworks_data cannot be empty")
    
    # Validate required metrics
    required = ["TOK_IN", "CACHED_TOKENS"]
    for framework, data in frameworks_data.items():
        missing = [m for m in required if m not in data]
        if missing:
            raise ValueError(f"Framework {framework} missing metrics: {missing}")
    
    # Extract data
    frameworks = list(frameworks_data.keys())
    tok_in = [frameworks_data[fw]["TOK_IN"] for fw in frameworks]
    cached = [frameworks_data[fw]["CACHED_TOKENS"] for fw in frameworks]
    uncached = [tin - cac for tin, cac in zip(tok_in, cached)]
    
    # Calculate hit rates
    hit_rates = [(cac / tin * 100) if tin > 0 else 0 
                 for cac, tin in zip(cached, tok_in)]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Define colors
    colors_uncached = {'baes': '#1f77b4', 'chatdev': '#ff7f0e', 'ghspec': '#2ca02c'}
    colors_cached = {'baes': '#88c9ff', 'chatdev': '#ffb366', 'ghspec': '#7fdb7f'}
    
    bar_colors_uncached = [colors_uncached.get(fw.lower(), '#666666') for fw in frameworks]
    bar_colors_cached = [colors_cached.get(fw.lower(), '#aaaaaa') for fw in frameworks]
    
    # Create stacked bars
    x_pos = np.arange(len(frameworks))
    width = 0.6
    
    bars_uncached = ax.bar(x_pos, uncached, width, label='Uncached Tokens',
                           color=bar_colors_uncached, alpha=0.8, 
                           edgecolor='black', linewidth=1.5)
    
    bars_cached = ax.bar(x_pos, cached, width, bottom=uncached,
                         label='Cached Tokens', color=bar_colors_cached, 
                         alpha=0.8, edgecolor='black', linewidth=1.5)
    
    # Add percentage labels
    for i, (fw, rate, tin) in enumerate(zip(frameworks, hit_rates, tok_in)):
        # Total tokens at top
        ax.text(i, tin, f'{int(tin):,}', ha='center', va='bottom',
               fontsize=11, fontweight='bold')
        
        # Cache hit rate in middle
        ax.text(i, tin/2, f'{rate:.1f}%\ncache hit',
               ha='center', va='center', fontsize=12, fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.4', facecolor='white', 
                        edgecolor='black', linewidth=2, alpha=0.9))
    
    # Labels and formatting
    ax.set_xlabel('Framework', fontsize=14, fontweight='bold')
    ax.set_ylabel('Tokens', fontsize=14, fontweight='bold')
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(frameworks, fontsize=12)
    ax.grid(True, axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    ax.legend(loc='upper right', fontsize=12, framealpha=0.9)
    
    # Add interpretation note
    note = ("Higher cache hit rate = Better prompt reuse\n"
            "Lower total tokens = More efficient overall")
    ax.text(0.02, 0.98, note, transform=ax.transAxes,
           fontsize=9, alpha=0.7, ha='left', va='top',
           bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', alpha=0.5))
    
    # Save as SVG
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, format=_infer_format_from_path(output_path), bbox_inches='tight', dpi=300)
    plt.close()
    
    print(f"Cache efficiency chart saved to {output_path}")


def time_distribution_chart(
    frameworks_data: Dict[str, List[Dict[str, float]]],
    output_path: str,
    title: str = "Execution Time Distribution"
) -> None:
    """
    Generate box plot showing execution time variability.
    
    Shows distribution of T_WALL_seconds across runs for each framework,
    including median, quartiles, and outliers.
    
    Args:
        frameworks_data: Dict mapping framework names to lists of run metrics.
                        Each run must contain: T_WALL_seconds
        output_path: Path to save the SVG file.
        title: Chart title.
    
    Raises:
        ValueError: If frameworks_data is empty or missing required metrics.
    """
    if not frameworks_data:
        raise ValueError("frameworks_data cannot be empty")
    
    # Validate required metrics and extract time data
    time_data = []
    frameworks = []
    for framework, runs in frameworks_data.items():
        if not runs:
            raise ValueError(f"Framework {framework} has no run data")
        
        times = []
        for run in runs:
            if "T_WALL_seconds" not in run:
                raise ValueError(f"Framework {framework} run missing T_WALL_seconds")
            times.append(run["T_WALL_seconds"])
        
        frameworks.append(framework)
        time_data.append(times)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Define colors
    colors = {'baes': '#1f77b4', 'chatdev': '#ff7f0e', 'ghspec': '#2ca02c'}
    box_colors = [colors.get(fw.lower(), '#666666') for fw in frameworks]
    
    # Create box plot
    bp = ax.boxplot(time_data, labels=frameworks, patch_artist=True,
                    widths=0.6, showmeans=True,
                    meanprops=dict(marker='D', markerfacecolor='red', 
                                  markeredgecolor='black', markersize=8),
                    medianprops=dict(color='black', linewidth=2),
                    boxprops=dict(linewidth=1.5, edgecolor='black'),
                    whiskerprops=dict(linewidth=1.5),
                    capprops=dict(linewidth=1.5),
                    flierprops=dict(marker='o', markerfacecolor='red', 
                                   markersize=8, alpha=0.5))
    
    # Color the boxes
    for patch, color in zip(bp['boxes'], box_colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    # Overlay individual points with jitter
    for i, (times, color) in enumerate(zip(time_data, box_colors)):
        x = np.random.normal(i + 1, 0.04, size=len(times))
        ax.scatter(x, times, alpha=0.4, s=50, color=color, edgecolors='black', linewidth=0.5)
    
    # Add median and mean value labels with smart positioning to avoid overlap
    for i, times in enumerate(time_data):
        median = np.median(times)
        mean = np.mean(times)
        
        # Calculate vertical separation needed
        y_range = ax.get_ylim()[1] - ax.get_ylim()[0]
        min_separation = y_range * 0.05  # 5% of chart height
        
        # If mean and median are too close, offset them vertically
        if abs(mean - median) < min_separation:
            # Place median at its actual position
            ax.text(i + 1, median, f'  Med: {median:.1f}s',
                   va='center', ha='left', fontsize=10, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                           alpha=0.8, edgecolor='black', linewidth=1))
            # Offset mean label above median
            offset = min_separation if mean >= median else -min_separation
            ax.text(i + 1, median + offset, f'  Avg: {mean:.1f}s',
                   va='center', ha='left', fontsize=9, alpha=0.9,
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', 
                           alpha=0.8, edgecolor='orange', linewidth=0.5))
        else:
            # They're far apart, place each at its actual value
            ax.text(i + 1, median, f'  Med: {median:.1f}s',
                   va='center', ha='left', fontsize=10, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                           alpha=0.8, edgecolor='black', linewidth=1))
            ax.text(i + 1, mean, f'  Avg: {mean:.1f}s',
                   va='center', ha='left', fontsize=9, alpha=0.9,
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', 
                           alpha=0.8, edgecolor='orange', linewidth=0.5))
    
    # Labels and formatting
    ax.set_xlabel('Framework', fontsize=14, fontweight='bold')
    ax.set_ylabel('Execution Time (seconds)', fontsize=14, fontweight='bold')
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.grid(True, axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # Add legend for box plot components
    legend_elements = [
        plt.Line2D([0], [0], marker='D', color='w', markerfacecolor='red',
                  markeredgecolor='black', markersize=8, label='Mean'),
        plt.Line2D([0], [0], color='black', linewidth=2, label='Median'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red',
                  markersize=8, alpha=0.5, label='Outliers')
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=11, framealpha=0.9)
    
    # Add interpretation note
    note = ("Box = Q1 to Q3 (middle 50%)\n"
            "Whiskers = Min/Max (excluding outliers)\n"
            "Narrow box = Consistent performance")
    ax.text(0.02, 0.98, note, transform=ax.transAxes,
           fontsize=9, alpha=0.7, ha='left', va='top',
           bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', alpha=0.5))
    
    # Save as SVG
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, format=_infer_format_from_path(output_path), bbox_inches='tight', dpi=300)
    plt.close()
    
    print(f"Time distribution chart saved to {output_path}")

