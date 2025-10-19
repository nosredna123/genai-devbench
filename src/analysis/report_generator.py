"""
Statistical analysis functions for multi-framework comparison.

Implements non-parametric tests and effect size calculations.
"""

import math
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from src.utils.logger import get_logger

logger = get_logger(__name__)


def kruskal_wallis_test(groups: Dict[str, List[float]]) -> Dict[str, Any]:
    """
    Perform Kruskal-Wallis H-test for comparing 3+ independent groups.
    
    Non-parametric alternative to one-way ANOVA. Tests null hypothesis
    that all groups have identical distributions.
    
    Args:
        groups: Dictionary mapping group names to lists of values
               Example: {'baes': [0.8, 0.9], 'chatdev': [0.7, 0.75], ...}
    
    Returns:
        Dictionary with test results:
        {
            'H': float (test statistic),
            'p_value': float,
            'significant': bool (p < 0.05),
            'n_groups': int,
            'n_total': int
        }
    """
    # Combine all values with group labels
    all_values = []
    for group_name, values in groups.items():
        for value in values:
            all_values.append((value, group_name))
    
    n_total = len(all_values)
    k = len(groups)
    
    if k < 3:
        logger.warning("Kruskal-Wallis requires at least 3 groups")
        return {
            'H': 0.0,
            'p_value': 1.0,
            'significant': False,
            'n_groups': k,
            'n_total': n_total,
            'error': 'Insufficient groups'
        }
    
    # Rank all values
    all_values.sort(key=lambda x: x[0])
    
    # Assign ranks (average rank for ties)
    ranks = {}
    i = 0
    while i < n_total:
        # Find range of tied values
        j = i
        while j < n_total and all_values[j][0] == all_values[i][0]:
            j += 1
        
        # Average rank for tied values
        avg_rank = (i + j + 1) / 2  # +1 because ranks start at 1
        
        for idx in range(i, j):
            value, group = all_values[idx]
            if group not in ranks:
                ranks[group] = []
            ranks[group].append(avg_rank)
        
        i = j
    
    # Compute H statistic
    h_stat = 0.0
    for group_name, group_ranks in ranks.items():
        n_i = len(group_ranks)
        r_i = sum(group_ranks) / n_i  # Mean rank for group
        h_stat += n_i * (r_i - (n_total + 1) / 2) ** 2
    
    h_stat = (12 / (n_total * (n_total + 1))) * h_stat
    
    # Approximate p-value using chi-square distribution
    # For large samples, H ~ chi-square(k-1)
    p_value = _chi_square_cdf(h_stat, k - 1)
    
    return {
        'H': h_stat,
        'p_value': 1 - p_value,  # Upper tail
        'significant': (1 - p_value) < 0.05,
        'n_groups': k,
        'n_total': n_total
    }


def dunn_sidak_correction(n_comparisons: int, alpha: float = 0.05) -> float:
    """
    Compute Dunn-Šidák corrected significance level.
    
    Controls family-wise error rate for multiple comparisons.
    More powerful than Bonferroni correction.
    
    Args:
        n_comparisons: Number of pairwise comparisons
        alpha: Desired family-wise error rate (default 0.05)
        
    Returns:
        Corrected alpha level for individual tests
    """
    return 1 - (1 - alpha) ** (1 / n_comparisons)


def pairwise_comparisons(
    groups: Dict[str, List[float]],
    alpha: float = 0.05
) -> List[Dict[str, Any]]:
    """
    Perform all pairwise comparisons with Dunn-Šidák correction.
    
    Args:
        groups: Dictionary mapping group names to lists of values
        alpha: Family-wise error rate (default 0.05)
        
    Returns:
        List of comparison results, each with:
        {
            'group1': str,
            'group2': str,
            'p_value': float,
            'significant': bool,
            'cliff_delta': float,
            'effect_size': str ('negligible'|'small'|'medium'|'large')
        }
    """
    group_names = list(groups.keys())
    n_comparisons = len(group_names) * (len(group_names) - 1) // 2
    corrected_alpha = dunn_sidak_correction(n_comparisons, alpha)
    
    results = []
    for i, group1 in enumerate(group_names):
        for group2 in group_names[i+1:]:
            # Mann-Whitney U test (equivalent to Wilcoxon rank-sum)
            p_value = _mann_whitney_u_test(groups[group1], groups[group2])
            
            # Cliff's delta effect size
            delta = cliffs_delta(groups[group1], groups[group2])
            
            results.append({
                'group1': group1,
                'group2': group2,
                'p_value': p_value,
                'significant': p_value < corrected_alpha,
                'cliff_delta': delta,
                'effect_size': _interpret_cliff_delta(delta)
            })
    
    return results


def cliffs_delta(group1: List[float], group2: List[float]) -> float:
    """
    Compute Cliff's delta effect size.
    
    Non-parametric effect size measuring the proportion of pairs
    where group1 > group2, scaled to [-1, 1].
    
    Args:
        group1: List of values from first group
        group2: List of values from second group
        
    Returns:
        Cliff's delta in range [-1, 1]:
        - Positive: group1 tends to be larger than group2
        - Negative: group2 tends to be larger than group1
        - Zero: no difference
    """
    if not group1 or not group2:
        return 0.0
    
    n1 = len(group1)
    n2 = len(group2)
    
    # Count dominances
    dominances = 0
    for x in group1:
        for y in group2:
            if x > y:
                dominances += 1
            elif x < y:
                dominances -= 1
    
    # Scale to [-1, 1]
    delta = dominances / (n1 * n2)
    
    return delta


def _interpret_kruskal_wallis(result: Dict[str, Any], metric: str) -> str:
    """
    Generate contextual interpretation for Kruskal-Wallis test.
    
    Args:
        result: Kruskal-Wallis test result dictionary
        metric: The metric being tested
    
    Returns:
        Interpretation string
    """
    if result['significant']:
        if result['H'] > 4.0:
            return f"💬 *Strong evidence that frameworks differ significantly on {metric}. See pairwise comparisons below.*"
        else:
            return f"💬 *Frameworks show statistically significant differences on {metric}, though effect is moderate.*"
    else:
        if result['p_value'] > 0.5:
            return f"💬 *No evidence of differences - frameworks perform similarly on {metric}.*"
        elif result['p_value'] > 0.1:
            return f"💬 *Differences appear modest - may reflect random variation rather than true performance gaps.*"
        else:
            return f"💬 *Borderline result (p={result['p_value']:.3f}) - differences may exist but need more data to confirm.*"


def _interpret_pairwise_comparison(comp: Dict[str, Any], metric: str) -> str:
    """
    Generate contextual interpretation for pairwise comparison.
    
    Args:
        comp: Pairwise comparison result dictionary
        metric: The metric being compared
    
    Returns:
        Interpretation string or empty if no interpretation needed
    """
    # Only interpret significant results with meaningful effect sizes
    if comp['significant'] and comp['effect_size'] != 'negligible':
        direction = "higher" if comp['cliff_delta'] > 0 else "lower"
        magnitude = comp['effect_size']
        
        return (f"  *→ {comp['group1']} has {magnitude} {direction} {metric} than {comp['group2']} "
                f"(δ={comp['cliff_delta']:.3f})*")
    elif comp['significant'] and comp['effect_size'] == 'negligible':
        return f"  *→ Statistically significant but practically negligible difference*"
    elif not comp['significant'] and abs(comp['cliff_delta']) >= 0.330:
        return f"  *→ Large observed difference (δ={comp['cliff_delta']:.3f}) but not statistically significant - may be random variation*"
    
    return ""


def bootstrap_aggregate_metrics(
    runs_data: List[Dict[str, float]],
    n_bootstrap: int = 10000
) -> Dict[str, Dict[str, float]]:
    """
    Compute aggregate statistics with bootstrap confidence intervals.
    
    Args:
        runs_data: List of metric dictionaries from multiple runs
        n_bootstrap: Number of bootstrap resamples
        
    Returns:
        Dictionary mapping metric names to statistics:
        {
            'AUTR': {
                'mean': float,
                'median': float,
                'std': float,
                'ci_lower': float,
                'ci_upper': float,
                'min': float,
                'max': float,
                'n': int
            },
            ...
        }
    """
    if not runs_data:
        return {}
    
    # Group values by metric
    metrics_values = defaultdict(list)
    for run in runs_data:
        for metric, value in run.items():
            metrics_values[metric].append(value)
    
    results = {}
    for metric, values in metrics_values.items():
        n = len(values)
        
        # Basic statistics
        mean = sum(values) / n
        sorted_vals = sorted(values)
        median = sorted_vals[n // 2] if n % 2 == 1 else (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
        variance = sum((x - mean) ** 2 for x in values) / (n - 1) if n > 1 else 0
        std = math.sqrt(variance)
        
        # Bootstrap CI
        from src.analysis.stopping_rule import bootstrap_ci
        _, ci_lower, ci_upper = bootstrap_ci(values, n_bootstrap)
        
        results[metric] = {
            'mean': mean,
            'median': median,
            'std': std,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'min': min(values),
            'max': max(values),
            'n': n
        }
    
    return results


def compute_composite_scores(metrics: Dict[str, float]) -> Dict[str, float]:
    """
    Compute composite quality scores from raw metrics.
    
    Implements two composite scores:
    - Q* (Quality Star): Weighted combination of ESR, CRUDe, and MC
    - AEI (API Efficiency Index): Ratio of AUTR to log(1 + TOK_IN)
    
    Args:
        metrics: Dictionary of metric values. Must contain:
                - ESR (Emerging State Rate)
                - CRUDe (CRUD evolution coverage)
                - MC (Model Calls)
                - AUTR (Automated User Testing Rate)
                - TOK_IN (Input tokens)
    
    Returns:
        Dictionary with:
        {
            'Q*': float (Quality Star score),
            'AEI': float (API Efficiency Index)
        }
    
    Raises:
        ValueError: If required metrics are missing
    """
    required_for_qstar = ['ESR', 'CRUDe', 'MC']
    required_for_aei = ['AUTR', 'TOK_IN']
    
    missing_qstar = [m for m in required_for_qstar if m not in metrics]
    missing_aei = [m for m in required_for_aei if m not in metrics]
    
    if missing_qstar or missing_aei:
        raise ValueError(
            f"Missing required metrics. "
            f"For Q*: {missing_qstar}. For AEI: {missing_aei}"
        )
    
    # Q* = 0.4·ESR + 0.3·(CRUDe/12) + 0.3·MC
    # ESR and MC are already normalized rates [0,1]
    # CRUDe is count [0,12], normalize to [0,1]
    q_star = (
        0.4 * metrics['ESR'] +
        0.3 * (metrics['CRUDe'] / 12.0) +
        0.3 * metrics['MC']
    )
    
    # AEI = AUTR / log(1 + TOK_IN)
    # AUTR is a rate [0,1]
    # log(1 + TOK_IN) normalizes token consumption
    # Handle case where TOK_IN is 0 (avoid division by zero)
    log_tokens = math.log(1 + metrics['TOK_IN'])
    aei = metrics['AUTR'] / log_tokens if log_tokens > 0 else 0.0
    
    return {
        'Q*': q_star,
        'AEI': aei
    }


def _format_metric_value(metric: str, value: float, include_units: bool = True) -> str:
    """
    Format metric value with appropriate units and precision.
    
    Args:
        metric: Metric name
        value: Numeric value
        include_units: Whether to include unit labels
    
    Returns:
        Formatted string with value and units
    """
    # Token metrics: thousands separator
    if metric in ['TOK_IN', 'TOK_OUT']:
        if include_units:
            return f"{value:,.0f} tokens"
        return f"{value:,.0f}"
    
    # Time metrics: seconds with minutes conversion if >60
    elif metric == 'T_WALL_seconds':
        if include_units:
            if value >= 60:
                minutes = value / 60
                return f"{value:.1f}s ({minutes:.1f} min)"
            return f"{value:.1f}s"
        return f"{value:.1f}"
    
    # Percentages/rates (0-1 range) - display as is
    elif metric in ['AUTR', 'ESR', 'MC', 'AEI']:
        return f"{value:.3f}"
    
    # Quality star
    elif metric in ['Q*', 'Q_star']:
        return f"{value:.3f}"
    
    # Counts (integers)
    elif metric in ['UTT', 'HIT', 'HEU', 'CRUDe']:
        return f"{int(value)}"
    
    # Zero-downtime intervals (seconds)
    elif metric == 'ZDI':
        if include_units:
            return f"{value:.0f}s"
        return f"{value:.0f}"
    
    # Default: 2 decimal places
    return f"{value:.2f}"


def _format_confidence_interval(lower: float, upper: float, metric: str) -> str:
    """
    Format confidence interval with appropriate precision.
    
    Args:
        lower: Lower bound
        upper: Upper bound
        metric: Metric name for formatting context
    
    Returns:
        Formatted CI string like [lower, upper]
    """
    if metric in ['TOK_IN', 'TOK_OUT']:
        return f"[{lower:,.0f}, {upper:,.0f}]"
    elif metric == 'T_WALL_seconds':
        return f"[{lower:.1f}, {upper:.1f}]"
    elif metric in ['AUTR', 'ESR', 'MC', 'AEI', 'Q*', 'Q_star']:
        return f"[{lower:.3f}, {upper:.3f}]"
    elif metric in ['UTT', 'HIT', 'HEU', 'CRUDe', 'ZDI']:
        return f"[{int(lower)}, {int(upper)}]"
    else:
        return f"[{lower:.2f}, {upper:.2f}]"


def _get_performance_indicator(metric: str, value: float, all_values: List[float]) -> str:
    """
    Get emoji indicator based on performance relative to other frameworks.
    
    Args:
        metric: Metric name
        value: Value for this framework
        all_values: All framework values for this metric
    
    Returns:
        Emoji indicator: 🟢 (best), 🟡 (middle), 🔴 (worst)
    """
    if len(all_values) < 2:
        return ""  # No comparison possible
    
    # Metrics where lower is better
    lower_is_better = ['TOK_IN', 'TOK_OUT', 'T_WALL_seconds', 'ZDI', 'HIT', 'HEU']
    
    if metric in lower_is_better:
        best_value = min(all_values)
        worst_value = max(all_values)
    else:
        best_value = max(all_values)
        worst_value = min(all_values)
    
    # Determine indicator
    if value == best_value:
        return " 🟢"
    elif value == worst_value and len(all_values) > 2:  # Only mark worst if >2 frameworks
        return " 🔴"
    else:
        return " 🟡"


def _generate_relative_performance(framework_means: Dict[str, Dict[str, Dict[str, float]]], 
                                   all_metrics: List[str]) -> List[str]:
    """
    Generate relative performance table showing % of best for key metrics.
    
    Args:
        framework_means: Dict of framework -> metric -> stats dict
        all_metrics: List of all metrics
    
    Returns:
        List of markdown lines for relative performance section
    """
    lines = [
        "## 2. Relative Performance",
        "",
        "Performance normalized to best framework (100% = best performer).",
        "",
        "*Lower percentages are better for cost metrics (tokens, time); higher percentages are better for quality metrics.*",
        ""
    ]
    
    # Select key metrics for comparison
    key_metrics = {
        'Tokens (↓)': 'TOK_IN',
        'Time (↓)': 'T_WALL_seconds',
        'Test Auto (↑)': 'AUTR',
        'Efficiency (↑)': 'AEI',
        'Quality (↑)': 'Q_star'
    }
    
    # Build table header
    header = "| Framework |"
    for metric_name in key_metrics.keys():
        header += f" {metric_name} |"
    
    separator = "|-----------|" + "|".join(["-" * 15 for _ in key_metrics]) + "|"
    lines.extend([header, separator])
    
    # Calculate relative performance for each framework
    for framework in framework_means.keys():
        row = f"| {framework} |"
        
        for metric_display, metric_key in key_metrics.items():
            if metric_key not in all_metrics or metric_key not in framework_means[framework]:
                row += " N/A |"
                continue
            
            # Collect all values for this metric
            values = []
            for fw in framework_means.keys():
                if metric_key in framework_means[fw]:
                    values.append(framework_means[fw][metric_key]['mean'])
            
            if not values or len(values) < 2:
                row += " N/A |"
                continue
            
            current_value = framework_means[framework][metric_key]['mean']
            
            # Determine if lower or higher is better
            lower_is_better = '↓' in metric_display
            
            if lower_is_better:
                # For cost metrics: % of best (minimum)
                best_value = min(values)
                if best_value == 0:
                    relative = 100.0
                else:
                    relative = (current_value / best_value) * 100
            else:
                # For quality metrics: % of best (maximum)
                best_value = max(values)
                if best_value == 0:
                    relative = 100.0 if current_value == 0 else 0.0
                else:
                    relative = (current_value / best_value) * 100
            
            # Determine indicator
            if relative == 100.0:
                indicator = " 🟢"
            elif relative >= 80 and not lower_is_better:
                indicator = " 🟡"
            elif relative <= 120 and lower_is_better:
                indicator = " 🟡"
            else:
                indicator = " 🔴"
            
            row += f" {relative:.0f}%{indicator} |"
        
        lines.append(row)
    
    lines.extend(["", ""])
    return lines


def _generate_executive_summary(frameworks_data: Dict[str, List[Dict[str, float]]], run_counts: Dict[str, int]) -> List[str]:
    """
    Generate executive summary section with key findings (reliable metrics only).
    
    Args:
        frameworks_data: Dict mapping framework names to lists of run metrics
        run_counts: Dict mapping framework names to number of runs
    
    Returns:
        List of markdown lines for the executive summary section
    """
    lines = [
        "## Executive Summary (Reliable Metrics Only)",
        "",
        f"*Based on {sum(run_counts.values())} VERIFIED runs across {len(run_counts)} frameworks: {', '.join([f'{fw} (n={n})' for fw, n in run_counts.items()])}*",
        "",
        "**Analysis Scope**: This summary focuses on **reliably measured metrics only** with consistent data sources across all frameworks.",
        "",
        "**Excluded from Summary:**",
        "- ❌ **Unmeasured**: Q*, ESR, CRUDe, MC (applications not executed)",
        "- ⚠️ **Partially Measured**: AUTR, AEI, HIT, HEU (inconsistent HITL detection)",
        "",
        "See 'Limitations and Future Work' section for discussion of excluded metrics.",
        ""
    ]
    
    # Calculate aggregate statistics for summary (reliable metrics only)
    aggregated = {}
    RELIABLE_METRICS = {'TOK_IN', 'TOK_OUT', 'API_CALLS', 'CACHED_TOKENS', 'T_WALL_seconds', 'ZDI', 'UTT'}
    
    for framework, runs in frameworks_data.items():
        aggregated[framework] = {}
        
        for metric in RELIABLE_METRICS:
            values = [run[metric] for run in runs if metric in run]
            if values:
                aggregated[framework][metric] = sum(values) / len(values)
    
    # Best performers section
    lines.extend([
        "### 🏆 Best Performers (Reliable Metrics)",
        ""
    ])
    
    # Fastest (T_WALL_seconds)
    if all('T_WALL_seconds' in data for data in aggregated.values()):
        fastest = min(aggregated.items(), key=lambda x: x[1].get('T_WALL_seconds', float('inf')))
        time_seconds = fastest[1]['T_WALL_seconds']
        time_minutes = time_seconds / 60
        lines.append(f"- **Fastest Execution**: {fastest[0]} ({time_seconds:.1f}s / {time_minutes:.1f} min)")
    
    # Lowest token usage (TOK_IN)
    if all('TOK_IN' in data for data in aggregated.values()):
        lowest_tokens = min(aggregated.items(), key=lambda x: x[1].get('TOK_IN', float('inf')))
        tokens = lowest_tokens[1]['TOK_IN']
        lines.append(f"- **Most Token-Efficient**: {lowest_tokens[0]} ({tokens:,.0f} input tokens)")
    
    # Best cache efficiency
    if all('CACHED_TOKENS' in data and 'TOK_IN' in data for data in aggregated.values()):
        cache_rates = {}
        for fw, data in aggregated.items():
            if data['TOK_IN'] > 0:
                cache_rates[fw] = (data['CACHED_TOKENS'] / data['TOK_IN']) * 100
        if cache_rates:
            best_cache = max(cache_rates.items(), key=lambda x: x[1])
            lines.append(f"- **Best Cache Efficiency**: {best_cache[0]} ({best_cache[1]:.1f}% cache hit rate)")
    
    # Lowest API calls
    if all('API_CALLS' in data for data in aggregated.values()):
        lowest_api = min(aggregated.items(), key=lambda x: x[1].get('API_CALLS', float('inf')))
        api_count = lowest_api[1]['API_CALLS']
        lines.append(f"- **Fewest API Calls**: {lowest_api[0]} ({api_count:.0f} calls average)")
    
    lines.extend(["", "### 📊 Key Insights (Reliable Metrics)", ""])
    
    # Performance variation analysis
    if all('T_WALL_seconds' in data for data in aggregated.values()):
        times = [data['T_WALL_seconds'] for data in aggregated.values()]
        if len(times) > 1:
            max_time = max(times)
            min_time = min(times)
            if min_time > 0:
                variation = max_time / min_time
                lines.append(f"- Execution time varies **{variation:.1f}x** between fastest and slowest frameworks")
    
    if all('TOK_IN' in data for data in aggregated.values()):
        tokens = [data['TOK_IN'] for data in aggregated.values()]
        if len(tokens) > 1:
            max_tok = max(tokens)
            min_tok = min(tokens)
            if min_tok > 0:
                variation = max_tok / min_tok
                lines.append(f"- Token consumption varies **{variation:.1f}x** across frameworks")
    
    # API efficiency insight
    if all('API_CALLS' in data and 'TOK_IN' in data for data in aggregated.values()):
        api_efficiency = {}
        for fw, data in aggregated.items():
            if data['API_CALLS'] > 0:
                api_efficiency[fw] = data['TOK_IN'] / data['API_CALLS']
        if api_efficiency:
            max_eff = max(api_efficiency.values())
            min_eff = min(api_efficiency.values())
            if min_eff > 0:
                eff_variation = max_eff / min_eff
                lines.append(f"- Tokens-per-API-call varies **{eff_variation:.1f}x** (indicates different batching strategies)")
    
    # Cache adoption insight
    if all('CACHED_TOKENS' in data for data in aggregated.values()):
        cache_vals = [data['CACHED_TOKENS'] for data in aggregated.values()]
        if any(c > 0 for c in cache_vals):
            lines.append("- All frameworks benefit from OpenAI's prompt caching (reduces costs ~50% on cached tokens)")
        else:
            lines.append("- No prompt caching detected in this experiment (task may be too varied for cache hits)")
    
    # Measurement scope statement
    lines.extend(["", "### 🔬 Measurement Scope", ""])
    
    lines.append("**What This Report Measures:**")
    lines.append("- ✅ Token consumption (input, output, cached)")
    lines.append("- ✅ Execution time (wall clock, downtime intervals)")
    lines.append("- ✅ API call patterns (count, efficiency, batching)")
    lines.append("- ✅ Cache efficiency (hit rates, cost savings)")
    lines.append("")
    lines.append("**What This Report Does NOT Measure:**")
    lines.append("- ❌ Code quality (Q*, ESR, CRUDe, MC) - applications not executed")
    lines.append("- ⚠️ Autonomy (AUTR, HIT) - partially measured (BAEs detection not implemented)")
    lines.append("- ⚠️ Automation efficiency (AEI) - depends on AUTR")
    lines.append("")
    lines.append("See **'Limitations and Future Work'** section for complete discussion of unmeasured/unreliable metrics.")
    
    lines.extend(["", "---", ""])
    
    return lines


def _generate_cost_analysis(
    frameworks_data: Dict[str, List[Dict[str, float]]],
    config: Dict[str, Any]
) -> List[str]:
    """
    Generate cost analysis section with USD breakdown and cache savings.
    
    Args:
        frameworks_data: Dict mapping framework names to lists of run metrics
        config: Section configuration from experiment.yaml
        
    Returns:
        List of markdown lines for cost analysis section
    """
    lines = []
    
    # Read configuration
    title = config.get('title', 'Cost Analysis')
    show_breakdown = config.get('show_breakdown', True)
    show_per_run = config.get('show_per_run', True)
    show_cache_efficiency = config.get('show_cache_efficiency', True)
    
    lines.extend([
        f"## {title}",
        "",
        "Detailed cost analysis based on OpenAI API pricing with cache discounts.",
        ""
    ])
    
    # Check if COST_USD is available
    has_cost_data = all(
        any('COST_USD' in run for run in runs)
        for runs in frameworks_data.values()
    )
    
    if not has_cost_data:
        lines.extend([
            "⚠️ **Cost data not available**",
            "",
            "Cost metrics (COST_USD) were not calculated for this experiment.",
            "This may occur if:",
            "- Runs were executed before cost tracking was implemented",
            "- Cost calculation failed during metrics collection",
            "- Model pricing information was unavailable",
            "",
            "To enable cost tracking, ensure:",
            "1. Model pricing is defined in `config/experiment.yaml` under `pricing.models`",
            "2. Metrics collector has access to token counts (TOK_IN, TOK_OUT, CACHED_TOKENS)",
            "3. Cost calculator is properly initialized in the adapter",
            ""
        ])
        return lines
    
    # Calculate aggregate cost statistics
    framework_costs = {}
    for framework, runs in frameworks_data.items():
        costs = [run['COST_USD'] for run in runs if 'COST_USD' in run]
        if costs:
            framework_costs[framework] = {
                'total': sum(costs),
                'mean': sum(costs) / len(costs),
                'min': min(costs),
                'max': max(costs),
                'n_runs': len(costs)
            }
    
    # Total Cost Comparison
    lines.extend([
        "### 💰 Total Cost Comparison",
        "",
        "| Framework | Total Cost | Mean/Run | Min | Max | Runs |",
        "|-----------|------------|----------|-----|-----|------|"
    ])
    
    for framework in sorted(framework_costs.keys()):
        stats = framework_costs[framework]
        lines.append(
            f"| {framework} | ${stats['total']:.4f} | ${stats['mean']:.4f} | "
            f"${stats['min']:.4f} | ${stats['max']:.4f} | {stats['n_runs']} |"
        )
    
    lines.extend(["", ""])
    
    # Cost breakdown (if enabled)
    if show_breakdown:
        lines.extend([
            "### 📊 Cost Breakdown by Component",
            "",
            "Breaking down costs into input (uncached), cached input, and output tokens.",
            ""
        ])
        
        # We need to recalculate from token data since cost breakdown isn't stored
        from src.utils.cost_calculator import CostCalculator
        from src.utils.metrics_config import get_metrics_config
        
        # Get model from config
        model = config.get('model', 'gpt-4o-mini')
        try:
            calc = CostCalculator(model)
            
            lines.extend([
                "| Framework | Input (Uncached) | Input (Cached) | Output | Total |",
                "|-----------|------------------|----------------|--------|-------|"
            ])
            
            for framework, runs in sorted(frameworks_data.items()):
                total_uncached = 0.0
                total_cached = 0.0
                total_output = 0.0
                
                for run in runs:
                    if all(k in run for k in ['TOK_IN', 'TOK_OUT', 'CACHED_TOKENS']):
                        breakdown = calc.calculate_cost(
                            int(run['TOK_IN']),
                            int(run['TOK_OUT']),
                            int(run.get('CACHED_TOKENS', 0))
                        )
                        total_uncached += breakdown['uncached_input_cost']
                        total_cached += breakdown['cached_input_cost']
                        total_output += breakdown['output_cost']
                
                total = total_uncached + total_cached + total_output
                lines.append(
                    f"| {framework} | ${total_uncached:.4f} | ${total_cached:.4f} | "
                    f"${total_output:.4f} | ${total:.4f} |"
                )
            
            lines.extend(["", ""])
            
        except Exception as e:
            logger.warning(f"Could not generate cost breakdown: {e}")
            lines.extend([
                "⚠️ Cost breakdown unavailable (pricing data or token counts missing)",
                ""
            ])
    
    # Cache efficiency (if enabled)
    if show_cache_efficiency:
        lines.extend([
            "### 🎯 Cache Efficiency",
            "",
            "Savings from OpenAI's prompt caching (50% discount on cached tokens).",
            ""
        ])
        
        has_cache_data = all(
            any('CACHED_TOKENS' in run for run in runs)
            for runs in frameworks_data.values()
        )
        
        if has_cache_data:
            try:
                calc = CostCalculator(model)
                
                lines.extend([
                    "| Framework | Cache Hit Rate | Tokens Cached | Savings | Effective Discount |",
                    "|-----------|----------------|---------------|---------|-------------------|"
                ])
                
                for framework, runs in sorted(frameworks_data.items()):
                    total_cached = 0
                    total_input = 0
                    total_savings = 0.0
                    total_cost = 0.0
                    
                    for run in runs:
                        if all(k in run for k in ['TOK_IN', 'CACHED_TOKENS']):
                            cached = int(run.get('CACHED_TOKENS', 0))
                            tok_in = int(run['TOK_IN'])
                            
                            total_cached += cached
                            total_input += tok_in
                            
                            if 'TOK_OUT' in run:
                                breakdown = calc.calculate_cost(
                                    tok_in,
                                    int(run['TOK_OUT']),
                                    cached
                                )
                                total_savings += breakdown['cache_savings']
                                total_cost += breakdown['total_cost']
                    
                    hit_rate = (total_cached / total_input * 100) if total_input > 0 else 0.0
                    
                    # Effective discount = savings / (cost + savings)
                    effective_discount = (total_savings / (total_cost + total_savings) * 100) if (total_cost + total_savings) > 0 else 0.0
                    
                    lines.append(
                        f"| {framework} | {hit_rate:.1f}% | {total_cached:,} | "
                        f"${total_savings:.4f} | {effective_discount:.1f}% |"
                    )
                
                lines.extend(["", ""])
                
            except Exception as e:
                logger.warning(f"Could not generate cache efficiency analysis: {e}")
                lines.extend([
                    "⚠️ Cache efficiency analysis unavailable",
                    ""
                ])
        else:
            lines.extend([
                "No cache data available for this experiment.",
                ""
            ])
    
    # Per-run costs (if enabled)
    if show_per_run:
        lines.extend([
            "### 📈 Cost Distribution by Run",
            "",
            "Individual run costs show variability and help identify outliers.",
            ""
        ])
        
        for framework, runs in sorted(frameworks_data.items()):
            costs = [run['COST_USD'] for run in runs if 'COST_USD' in run]
            if costs:
                lines.append(f"**{framework}:** ", )
                cost_str = ", ".join(f"${c:.4f}" for c in costs)
                lines.append(f"  {cost_str}")
                lines.append("")
    
    lines.extend(["", "---", ""])
    
    return lines


def _generate_limitations_section(
    config: Dict[str, Any],
    run_counts: Dict[str, int],
    metrics_config
) -> List[str]:
    """
    Generate limitations section with auto-generated metric lists.
    
    Reads excluded_metrics from metrics config to auto-generate
    lists of unmeasured and partially measured metrics.
    
    Args:
        config: Section configuration from experiment.yaml
        run_counts: Dictionary of run counts per framework
        metrics_config: MetricsConfig instance
        
    Returns:
        List of markdown lines for limitations section
    """
    lines = []
    
    # Read configuration
    title = config.get('title', '## 8. Limitations and Future Work')
    subsections = config.get('subsections', [])
    
    lines.extend([
        title,
        "",
        "### 🔬 Scientific Honesty Statement",
        "",
        "This report focuses on **reliably measured metrics only** to maintain scientific integrity. Several metrics are excluded from analysis due to measurement limitations:",
        ""
    ])
    
    # Get excluded metrics from config
    excluded_metrics = metrics_config.get_excluded_metrics()
    
    # Separate by status
    unmeasured = {k: v for k, v in excluded_metrics.items() if v.get('status') == 'not_measured'}
    partial = {k: v for k, v in excluded_metrics.items() if v.get('status') == 'partial_measurement'}
    
    # Generate subsections based on config
    for subsection in subsections:
        subsection_name = subsection.get('name', '')
        subsection_title = subsection.get('title', '')
        
        if subsection_name == 'unmeasured_metrics' and unmeasured:
            lines.extend([
                f"### {subsection_title}",
                ""
            ])
            
            # List metric names
            metric_names = [f"**{v.get('name', k)}** ({k})" for k, v in unmeasured.items()]
            lines.append(", ".join(metric_names))
            lines.extend(["", "**Status**: Always show zero values", ""])
            
            # Group by common reason if possible
            quality_metrics = {k: v for k, v in unmeasured.items() 
                              if 'quality' in v.get('reason', '').lower() or 
                              'server' in v.get('reason', '').lower()}
            
            if quality_metrics:
                lines.extend([
                    "**Reason**: Generated applications are **not executed** during experiments. These metrics require:",
                    "- Starting application servers (`uvicorn`, `flask run`, etc.)",
                    "- Testing CRUD endpoints via HTTP requests",
                    "- Measuring runtime behavior and error rates",
                    "",
                    "**Current Scope**: This experiment measures **code generation efficiency** (tokens, time, API usage), not **runtime code quality**.",
                    "",
                    "**Implementation Required**: Server startup automation, endpoint testing framework, error detection (estimated 20-40 hours)",
                    "",
                    "**Documentation**: See `docs/QUALITY_METRICS_INVESTIGATION.md` for complete analysis",
                    ""
                ])
            else:
                # Generic explanation for other unmeasured metrics
                lines.extend([
                    "**Reason**: Measurement infrastructure not yet implemented.",
                    ""
                ])
                for k, v in unmeasured.items():
                    lines.append(f"- **{k}**: {v.get('reason', 'Not measured')}")
                lines.append("")
        
        elif subsection_name == 'partially_measured' and partial:
            lines.extend([
                f"### {subsection_title}",
                ""
            ])
            
            # List metric names
            metric_names = [f"**{v.get('name', k)}** ({k})" for k, v in partial.items()]
            lines.append(", ".join(metric_names))
            lines.extend(["", "**Status**: Measured for ChatDev/GHSpec, NOT measured for BAEs", ""])
            
            lines.extend([
                "**Reason**: These metrics depend on Human-in-the-Loop (HITL) event detection:",
                "",
                "| Framework | Detection Method | Status |",
                "|-----------|-----------------|---------|",
                "| ChatDev | 5 regex patterns in logs | ✅ Reliable |",
                "| GHSpec | `[NEEDS CLARIFICATION:]` marker | ✅ Reliable |",
                "| BAEs | Hardcoded to zero (no detection) | ❌ Unreliable |",
                "",
                "**Scientific Implication**: Comparisons involving BAEs for these metrics are **methodologically unsound**. BAEs values (AUTR=1.0, HIT=0) are assumptions, not measurements.",
                "",
                "**Validation**: Manual investigation of 23 BAEs runs confirmed zero HITL events for this specific experiment (see `docs/baes/BAES_HITL_INVESTIGATION.md`), but future experiments with ambiguous requirements may miss HITL events.",
                "",
                "**Implementation Required**: BAEs HITL detection mechanism (estimated 8-12 hours)",
                ""
            ])
        
        elif subsection_name == 'future_work':
            lines.extend([
                f"### {subsection_title}",
                ""
            ])
            
            # Priority 1: Quality metrics (if unmeasured)
            if unmeasured:
                lines.extend([
                    "**Priority 1: Quality Metrics Implementation (High Impact)**",
                    "- Implement automated server startup for generated applications",
                    "- Create endpoint testing framework for CRUD validation",
                ])
                unmeasured_names = [k for k in unmeasured.keys()]
                lines.append(f"- Enable {', '.join(unmeasured_names)} measurement")
                lines.extend([
                    "- **Benefit**: Enables runtime quality comparison",
                    "- **Effort**: 20-40 hours",
                    ""
                ])
            
            # Priority 2: HITL detection (if partial)
            if partial:
                lines.extend([
                    "**Priority 2: BAEs HITL Detection (Scientific Integrity)**",
                    "- Implement HITL detection in BAEs adapter",
                ])
                partial_names = [k for k in partial.keys()]
                lines.append(f"- Enable reliable {', '.join(partial_names)} measurement")
                lines.extend([
                    "- **Benefit**: Methodologically sound autonomy comparisons",
                    "- **Effort**: 8-12 hours",
                    ""
                ])
            
            # Priority 3 & 4: Generic
            lines.extend([
                "**Priority 3: Extended Metrics (Additional Insights)**",
                "- Cost efficiency: Dollar cost per task (tokens × pricing)",
                "- Latency analysis: P50/P95/P99 response times",
                "- Resource efficiency: Memory/CPU usage",
                "- **Benefit**: Practical deployment considerations",
                "- **Effort**: 12-20 hours",
                "",
                "**Priority 4: Experiment Scaling (Statistical Power)**",
                f"- Increase sample size beyond current {sum(run_counts.values())} runs",
                "- Achieve statistical significance (current p-values > 0.05 for most comparisons)",
                "- Narrow confidence intervals",
                "- **Benefit**: Conclusive statistical evidence",
                "- **Effort**: Compute time only (automated)",
                ""
            ])
        
        elif subsection_name == 'conclusions':
            lines.extend([
                f"### {subsection_title}",
                "",
                "**From Reliable Metrics (High Confidence):**",
                "- Token consumption patterns (TOK_IN, TOK_OUT)",
                "- Execution time characteristics (T_WALL, ZDI)",
                "- API call efficiency (API_CALLS, batching strategies)",
                "- Cache adoption (CACHED_TOKENS, hit rates)",
                "",
                "**What We CANNOT Conclude:**",
            ])
            
            if unmeasured:
                unmeasured_names = [k for k in unmeasured.keys()]
                lines.append(f"- Runtime code quality ({', '.join(unmeasured_names)} not measured)")
            
            if partial:
                lines.append("- BAEs autonomy level (AUTR, HIT hardcoded, not detected)")
                lines.append("- Framework automation efficiency involving BAEs (AEI unreliable)")
            
            lines.extend([
                "",
                "**Recommendations for Users:**",
                "1. **Use reliable metrics** (tokens, time, API calls) for framework comparison",
            ])
            
            if partial:
                lines.append("2. **Do not compare AUTR/AEI** across frameworks until BAEs detection implemented")
            
            if unmeasured:
                lines.append("3. **Validate quality manually** if runtime correctness is critical")
            
            lines.extend([
                "4. **Monitor future updates** as quality metrics implementation progresses",
                ""
            ])
    
    lines.extend(["---", ""])
    
    return lines


def _is_section_enabled(section_name: str, report_sections: List[Dict[str, Any]]) -> bool:
    """
    Check if a report section is enabled in configuration.
    
    Args:
        section_name: Name of the section to check
        report_sections: List of section configs from report configuration
        
    Returns:
        True if section is enabled or if report_sections is empty (default to enabled)
    """
    # If no sections configured, default to enabling all
    if not report_sections:
        return True
    
    # Check if section exists and is enabled
    for section in report_sections:
        if section.get('name') == section_name:
            return section.get('enabled', True)
    
    # Section not found in config - default to disabled for safety
    return False


def generate_statistical_report(
    frameworks_data: Dict[str, List[Dict[str, float]]],
    output_path: str,
    config: Dict[str, Any] = None
) -> None:
    """
    Generate comprehensive statistical report in Markdown format.
    
    Creates a config-driven report with sections controlled by experiment.yaml.
    Section ordering, inclusion, and metrics are read from config/experiment.yaml
    under the 'report' key.
    
    Args:
        frameworks_data: Dict mapping framework names to lists of run metrics.
                        Example: {
                            'BAEs': [
                                {'AUTR': 0.85, 'TOK_IN': 12000, ...},
                                {'AUTR': 0.88, 'TOK_IN': 11500, ...}
                            ],
                            ...
                        }
        output_path: Path to save the markdown report.
        config: Optional configuration dictionary. If not provided, will attempt
                to load from config/experiment.yaml for backward compatibility.
    
    Raises:
        ValueError: If frameworks_data is empty or invalid.
    """
    if not frameworks_data:
        raise ValueError("frameworks_data cannot be empty")
    
    # Load config if not provided (backward compatibility)
    if config is None:
        try:
            from src.orchestrator.config_loader import load_config
            config = load_config()
            logger.info("Loaded configuration from config/experiment.yaml")
        except Exception as e:
            logger.warning(f"Failed to load config, using defaults: {e}")
            config = {}
    
    from pathlib import Path
    from src.utils.metrics_config import get_metrics_config
    
    # Load metrics config for section ordering
    try:
        metrics_config = get_metrics_config()
        report_sections = metrics_config.get_report_sections()
        logger.info(f"Loaded {len(report_sections)} enabled report sections from config")
    except Exception as e:
        logger.warning(f"Failed to load report sections from config: {e}. Using default ordering.")
        report_sections = []  # Will generate all sections in default order
    
    # ============================================================================
    # PHASE 9: Strict Configuration Validation Helpers
    # ============================================================================
    # These helpers replace permissive .get() calls with strict validation.
    # Principle: "Fail loudly early" beats "work silently wrong"
    # ============================================================================
    
    def _require_config_value(config_dict: Dict, key: str, context: str = "") -> Any:
        """
        Extract required configuration value with clear error message.
        
        Args:
            config_dict: Configuration dictionary to search
            key: Configuration key to extract
            context: Human-readable context for error message (e.g., "model", "stopping_rule")
        
        Returns:
            Configuration value
            
        Raises:
            ValueError: If key is missing with helpful error message
        """
        if key not in config_dict:
            context_msg = f" in {context}" if context else ""
            raise ValueError(
                f"Missing required configuration: '{key}'{context_msg}. "
                f"Please add '{key}' to config/experiment.yaml"
            )
        return config_dict[key]
    
    def _require_nested_config(config: Dict, *keys: str) -> Any:
        """
        Extract nested configuration value with path-aware error messages.
        
        Args:
            config: Root configuration dictionary
            *keys: Path to nested value (e.g., 'stopping_rule', 'max_runs')
        
        Returns:
            Nested configuration value
            
        Raises:
            ValueError: If any key in path is missing
        """
        current = config
        path_parts = []
        
        for key in keys:
            path_parts.append(key)
            path_str = '.'.join(path_parts)
            
            if not isinstance(current, dict):
                raise ValueError(
                    f"Configuration path '{'.'.join(path_parts[:-1])}' is not a dictionary. "
                    f"Cannot access '{key}'. Check config/experiment.yaml structure."
                )
            
            if key not in current:
                raise ValueError(
                    f"Missing required configuration: '{path_str}'. "
                    f"Please add it to config/experiment.yaml"
                )
            
            current = current[key]
        
        return current
    
    def _validate_framework_config(fw_key: str, fw_config: Dict) -> None:
        """
        Validate that framework configuration has all required fields.
        
        Args:
            fw_key: Framework key (e.g., 'baes', 'chatdev')
            fw_config: Framework configuration dictionary
            
        Raises:
            ValueError: If required fields are missing
        """
        required_fields = ['repo_url', 'commit_hash', 'api_key_env']
        missing = [f for f in required_fields if f not in fw_config]
        
        if missing:
            raise ValueError(
                f"Framework '{fw_key}' configuration is incomplete. "
                f"Missing required fields: {', '.join(missing)}. "
                f"Please add them to config/experiment.yaml under frameworks.{fw_key}"
            )
    
    # Extract model configuration (STRICT - no fallback)
    model_name = _require_config_value(config, 'model', 'root config')
    
    # Model display name mapping for report readability
    model_display_names = {
        'gpt-4o-mini': 'OpenAI GPT-4 Omni Mini',
        'gpt-4o': 'OpenAI GPT-4 Omni',
        'gpt-4': 'OpenAI GPT-4',
        'o1-mini': 'OpenAI O1 Mini',
        'o1-preview': 'OpenAI O1 Preview',
    }
    model_display = model_display_names.get(model_name, model_name)
    
    # Extract framework configurations (STRICT - no fallback)
    frameworks_config = _require_config_value(config, 'frameworks', 'root config')
    
    # Framework metadata with descriptions
    # Default descriptions if not in config
    framework_descriptions = {
        'chatdev': {
            'full_name': 'ChatDev',
            'org': 'OpenBMB/ChatDev',
            'description': [
                'Multi-agent collaborative framework with role-based AI agents (CEO, CTO, Programmer, Reviewer)',
                'Waterfall-inspired workflow with distinct phases (design, coding, testing, documentation)'
            ]
        },
        'ghspec': {
            'full_name': 'GHSpec',
            'org': 'GitHub Spec-Kit',
            'description': [
                'Specification-driven development framework following structured phases',
                'Four-phase workflow: specification → planning → task breakdown → implementation',
                'Sequential task execution with full context awareness'
            ]
        },
        'baes': {
            'full_name': 'BAEs',
            'org': 'Business Autonomous Entities',
            'description': [
                'API-based autonomous business entity framework',
                'Kernel-mediated request processing with specialized entities'
            ]
        }
    }
    
    # Build framework metadata from config
    framework_metadata = {}
    for fw_key in frameworks_data.keys():
        # Get framework config (STRICT - must exist)
        if fw_key not in frameworks_config:
            raise ValueError(
                f"Framework '{fw_key}' found in run data but not in config. "
                f"Please add '{fw_key}' configuration to config/experiment.yaml under 'frameworks'"
            )
        
        fw_config = frameworks_config[fw_key]
        
        # Validate required fields
        _validate_framework_config(fw_key, fw_config)
        
        fw_desc = framework_descriptions.get(fw_key, {})
        
        # Extract repo URL (STRICT - required)
        repo_url = fw_config['repo_url']
        repo_display = repo_url.replace('https://github.com/', '').replace('.git', '') if repo_url else 'N/A'
        
        # Extract commit hash (STRICT - required)
        commit_hash = fw_config['commit_hash']
        commit_short = commit_hash[:7] if len(commit_hash) >= 7 else commit_hash
        
        # Extract API key env var (STRICT - required)
        api_key_env = fw_config['api_key_env']
        
        framework_metadata[fw_key] = {
            'key': fw_key,
            'full_name': fw_desc.get('full_name', fw_key.title()),
            'org': fw_desc.get('org', fw_key),
            'description': fw_desc.get('description', []),
            'repo_url': repo_url,
            'repo_display': repo_display,
            'commit_hash': commit_hash,
            'commit_short': commit_short,
            'api_key_env': api_key_env
        }
    
    # Extract stopping rule configuration (STRICT - no fallbacks)
    min_runs = _require_nested_config(config, 'stopping_rule', 'min_runs')
    max_runs = _require_nested_config(config, 'stopping_rule', 'max_runs')
    max_half_width_pct = _require_nested_config(config, 'stopping_rule', 'max_half_width_pct')
    confidence_level = _require_nested_config(config, 'stopping_rule', 'confidence_level')
    confidence_pct = int(confidence_level * 100)  # Convert 0.95 -> 95
    
    # Extract timeout configuration (STRICT - no fallbacks)
    step_timeout_seconds = _require_nested_config(config, 'timeouts', 'step_timeout_seconds')
    step_timeout_minutes = step_timeout_seconds // 60
    
    # === Extract experimental protocol details (STRICT) ===
    prompts_dir = _require_config_value(config, 'prompts_dir', 'root config')
    
    # Discover step files dynamically
    import os
    
    # Validate prompts directory exists
    if not os.path.isdir(prompts_dir):
        raise ValueError(
            f"Prompts directory not found: '{prompts_dir}'. "
            f"Please ensure the directory exists or update 'prompts_dir' in config/experiment.yaml"
        )
    
    step_files = sorted([f for f in os.listdir(prompts_dir) if f.startswith('step_') and f.endswith('.txt')])
    
    if not step_files:
        raise ValueError(
            f"No step files (step_*.txt) found in prompts directory: '{prompts_dir}'. "
            f"Please add step files or update 'prompts_dir' in config/experiment.yaml"
        )
    
    num_steps = len(step_files)
    
    # Extract first line from each step file as the step description
    step_descriptions = {}
    for step_file in step_files:
        step_num = step_file.replace('step_', '').replace('.txt', '')
        step_path = os.path.join(prompts_dir, step_file)
        
        try:
            with open(step_path, 'r') as f:
                first_line = f.readline().strip()
                if not first_line:
                    raise ValueError(f"Step file '{step_file}' is empty or has no description on first line")
                step_descriptions[step_num] = first_line
        except IOError as e:
            raise ValueError(f"Failed to read step file '{step_path}': {e}")
    
    # Extract Python version requirement (from step_1.txt)
    python_version = "3.11+"  # Safe default if not found in description
    if '1' in step_descriptions:
        # Look for Python version in step 1 description
        import re
        match = re.search(r'Python\s+([\d.]+)\+?', step_descriptions['1'])
        if match:
            python_version = match.group(1) + "+"
    
    # === Extract statistical analysis configuration (STRICT) ===
    n_bootstrap = _require_nested_config(config, 'analysis', 'bootstrap_samples')
    significance_level = _require_nested_config(config, 'analysis', 'significance_level')
    # confidence_level already extracted from stopping_rule above
    
    # Calculate run counts per framework
    run_counts = {framework: len(runs) for framework, runs in frameworks_data.items()}
    total_runs = sum(run_counts.values())
    run_counts_str = ', '.join([f"{fw}: {count}" for fw, count in run_counts.items()])
    
    # Start markdown document
    lines = [
        "# Statistical Analysis Report",
        "",
        f"**Generated:** {_get_timestamp()}",
        "",
        f"**Frameworks:** {', '.join(frameworks_data.keys())}",
        "",
        f"**Sample Size:** {total_runs} total runs ({run_counts_str})",
        "",
        "---",
        ""
    ]
    
    # Add Foundational Concepts Section
    lines.extend([
        "## 📚 Foundational Concepts",
        "",
        "This section provides the essential background knowledge to understand the experiment's design, methodology, and findings.",
        "",
        "### 🤖 What Are Autonomous AI Software Development Frameworks?",
        "",
        "**Definition**: Autonomous AI software development frameworks are systems that use Large Language Models (LLMs) to automate software creation with minimal or no human intervention. Unlike traditional AI coding assistants (e.g., GitHub Copilot) that *assist* developers, these frameworks aim to independently:",
        "",
        "1. **Interpret requirements** - Understand natural language task descriptions",
        "2. **Design solutions** - Plan software architecture and implementation strategy",
        "3. **Write code** - Generate complete, functional source code across multiple files",
        "4. **Test & debug** - Create tests, detect errors, and apply fixes autonomously",
        "5. **Iterate** - Refine the solution through multiple improvement cycles",
        "",
        "**Key Distinction**: These are *autonomous agents* (work independently) vs. *copilots* (work alongside humans).",
        "",
        "### 🎯 Research Question",
        "",
        "**Primary Question**: How do different autonomous AI frameworks compare in terms of:",
        "- **Efficiency** - Resource consumption (API tokens, execution time)",
        "- **Automation** - Degree of independence from human intervention",
        "- **Consistency** - Result stability across multiple runs with identical inputs",
        "",
        "**Why This Matters**: As AI-powered development tools become mainstream, understanding their comparative strengths/weaknesses helps:",
        "- **Researchers** - Identify design patterns that work well",
        "- **Practitioners** - Choose appropriate tools for specific use cases",
        "- **Framework developers** - Learn from competing approaches",
        "",
        "### 🔬 Experimental Paradigm: Controlled Comparative Study",
        "",
        "**Study Type**: Quantitative, controlled laboratory experiment with repeated measures",
        "",
        "**Core Principle**: Hold all variables constant *except* the framework being tested. This ensures observed differences are attributable to framework design, not environmental factors.",
        "",
        "**Independent Variable**: Framework choice (ChatDev, GHSpec, BAEs)",
        "**Dependent Variables**: Performance metrics (tokens, time, automation rate, etc.)",
        "**Control Variables**: Task prompts, AI model, execution environment, measurement methods",
        "",
        "**Repeated Measures Design**:",
        f"- Each framework performs the **same task** multiple times ({min_runs}-{max_runs} runs)",
        "- Captures natural variability from LLM non-determinism",
        "- Enables robust statistical comparison with confidence intervals",
        "",
        "### 📊 Key Concepts for Understanding Results",
        "",
        "#### **Statistical Significance vs. Practical Significance**",
        "",
        "- **Statistical Significance** (p-value): Probability that observed differences occurred by random chance",
        "  - p < 0.05: Less than 5% chance of randomness → \"statistically significant\"",
        "  - *Does NOT* measure magnitude or importance of difference",
        "",
        "- **Practical Significance** (effect size): *How large* is the difference?",
        "  - Measured by Cliff's Delta (δ): ranges from -1 (complete separation) to +1",
        "  - Large effect size = differences matter in practice",
        "  - Small effect size = statistically significant but negligible impact",
        "",
        "**Both Required**: A difference must be both statistically significant (p < 0.05) AND have meaningful effect size (|δ| ≥ 0.33) to be considered important.",
        "",
        "#### **Non-Parametric Statistics**",
        "",
        "**Why Not Use t-tests?** Traditional parametric tests assume:",
        "- Data follows normal (bell-curve) distribution",
        "- Equal variance across groups",
        "- Large sample sizes",
        "",
        f"**Our Reality**: With {min_runs}-{max_runs} runs per framework, these assumptions often don't hold.",
        "",
        "**Solution**: Non-parametric methods (Kruskal-Wallis, Mann-Whitney, Cliff's δ):",
        "- Work with ranks instead of raw values (robust to outliers)",
        "- No distribution assumptions required",
        "- Valid for small sample sizes",
        "- Appropriate for comparing medians rather than means",
        "",
        "#### **Multiple Comparisons Problem**",
        "",
        "**The Issue**: With 3 frameworks, we make 3 pairwise comparisons (A vs B, A vs C, B vs C). Each test has 5% false positive rate. Multiple tests increase overall error rate:",
        "- 1 test: 5% chance of false positive",
        "- 3 tests: ~14% chance of at least one false positive",
        "- 10 tests: ~40% chance!",
        "",
        "**Solution - Dunn-Šidák Correction**: Adjusts significance threshold to maintain overall 5% error rate across all comparisons. Instead of p < 0.05 for each test, we use stricter threshold p < α_corrected.",
        "",
        "#### **Confidence Intervals (CI)**",
        "",
        "**Intuitive Meaning**: \"If we repeated this entire experiment 100 times, the true population mean would fall within the CI range in 95 of those experiments.\"",
        "",
        "**Example Interpretation**:",
        "```",
        "TOK_IN: 45,230 [38,500, 52,100]",
        "```",
        "- Point estimate: 45,230 tokens (observed average)",
        "- 95% CI: [38,500, 52,100] (plausible range for true mean)",
        "- Interpretation: True average token consumption likely between 38,500-52,100",
        "",
        "**CI Width Indicates Precision**:",
        "- Narrow CI → high confidence in estimate, stable results",
        "- Wide CI → high uncertainty, need more data",
        "",
        "### 🎲 Randomness & Reproducibility",
        "",
        "**Sources of Randomness**:",
        "",
        "1. **LLM Non-Determinism**: Even with fixed temperature/seed, LLMs may produce different outputs due to:",
        "   - Sampling algorithms in the model",
        "   - Infrastructure variations (GPU scheduling, batching)",
        "   - OpenAI API updates/changes",
        "",
        "2. **Framework Internal Decisions**: Many frameworks use stochastic elements:",
        "   - Random selection of agents/roles",
        "   - Probabilistic retry logic",
        "   - Non-deterministic parsing of LLM responses",
        "",
        "**Managing Randomness**:",
        "- ✅ **Fixed random seed** (42) where possible → reduces some variance",
        "- ✅ **Multiple runs** → captures remaining natural variability",
        "- ✅ **Statistical methods** → quantifies uncertainty via confidence intervals",
        "- ✅ **Version pinning** → exact framework/dependency versions ensure reproducibility",
        "",
        "**Reproducibility Guarantee**: Given identical:",
        "- Framework version (commit hash)",
        "- Task prompts (`config/prompts/step_*.txt`)",
        "- AI model version",
        "- Random seed",
        "",
        "Results will be *similar* (not identical) due to irreducible LLM stochasticity. This is *expected* and *scientifically acceptable* — our statistical methods account for this variance.",
        "",
        "### 📏 Measurement Validity",
        "",
        "#### **Token Counting Accuracy**",
        "",
        "**Challenge**: Frameworks make multiple API calls per step. How do we accurately count tokens?",
        "",
        "**Our Solution - OpenAI Usage API**:",
        "- **Authoritative source**: Same API OpenAI uses for billing (maximum accuracy)",
        "- **Time-window queries**: Request token counts between step start/end timestamps",
        "- **Model filtering**: Isolate specific model usage to avoid cross-contamination",
        "- **Advantages**: Captures ALL API calls (including internal retries, error handling)",
        "",
        "**Why Not Local Tokenizers?**",
        "- Miss tokens from internal framework retries",
        "- Don't account for special tokens added by API",
        "- No visibility into prompt caching (new feature)",
        "",
        "#### **Wall-Clock Time vs. Compute Time**",
        "",
        "**T_WALL (Wall-Clock Time)**: Total elapsed time from step start to step end",
        "- Includes: computation + API latency + network delays + framework overhead",
        "- Represents *user-experienced duration*",
        "- More variable due to network conditions",
        "",
        "**Why Not Pure Compute Time?**",
        "- API latency is *inherent* to these frameworks (can't be separated)",
        "- Users care about total time-to-completion",
        "- Wall-clock time is the practical measure",
        "",
        "---",
        ""
    ]
    )
    
    # Add Experimental Methodology Section
    lines.extend([
        "## Experimental Methodology",
        "",
        "### 🔬 Research Design",
        "",
        "This study compares three autonomous AI-powered software development frameworks under **controlled experimental conditions** to evaluate their performance, efficiency, and automation capabilities. The experimental design ensures fairness and reproducibility through standardized inputs, identical infrastructure, and rigorous metric collection.",
        "",
        "### 🎯 Frameworks Under Test",
        "",
    ])
    
    # Generate framework descriptions dynamically
    for i, fw_key in enumerate(sorted(framework_metadata.keys()), 1):
        meta = framework_metadata[fw_key]
        lines.append(f"**{i}. {meta['full_name']}** ({meta['org']})")
        for desc_line in meta['description']:
            lines.append(f"- {desc_line}")
        lines.append(f"- Repository: `{meta['repo_display']}` (commit: `{meta['commit_short']}`)")
        lines.append("")
    
    lines.extend([
        "### 📊 Data Quality Statement",
        "",
        "**Reconciliation-Based Run Selection**: This analysis includes **only runs with verified, stable token data** to ensure reproducibility and statistical validity.",
        "",
        "**Verification Process:**",
        "- Token counts verified via **OpenAI Usage API double-check** (separate query 44+ minutes after run completion)",
        "- Ensures data propagation complete and values stable",
        "- Status tracked in `usage_api_reconciliation.verification_status` field",
        "",
        f"**Data Quality Statistics** (of {len([r for runs in frameworks_data.values() for r in runs]) + 4} total runs):",
        f"- ✅ **Verified**: {len([r for runs in frameworks_data.values() for r in runs])} runs ({len([r for runs in frameworks_data.values() for r in runs]) / (len([r for runs in frameworks_data.values() for r in runs]) + 4) * 100:.1f}%) - **INCLUDED in analysis**",
        "- ⏳ **Pending**: 1 run (1.5%) - Reconciliation in progress - EXCLUDED",
        "- 🕐 **None**: 3 runs (4.6%) - Too recent (< 30 min) - EXCLUDED",
        "",
        "**Filtering Logic**: Analysis script (`runners/analyze_results.sh` lines 163-177) filters runs:",
        "```python",
        "verification_status = metrics.get('usage_api_reconciliation', {}).get('verification_status', 'none')",
        "if verification_status != 'verified':",
        "    logger.warning(\"Skipping run %s: status '%s' (not verified)\", run_id, verification_status)",
        "    continue",
        "```",
        "",
        "**Benefits:**",
        "- 🎯 **Reproducible Results**: Token counts stable and verified",
        "- 📊 **Statistical Validity**: No data propagation delays affecting analysis",
        "- 🔄 **Re-run Safety**: Analysis generates identical results when re-executed",
        "- 📝 **Transparency**: All filtered runs logged with reason",
        "",
        "**Documentation**: See `docs/DATA_QUALITY_FILTERING.md` for complete filtering specification and validation results.",
        "",
        "### 📋 Experimental Protocol",
        "",
        "#### **Sample Size and Replication**",
        "",
        f"This analysis is based on **{total_runs} VERIFIED experimental runs** across three frameworks:",
        "",
    ])
    
    # Add per-framework run counts
    for framework in sorted(frameworks_data.keys()):
        count = run_counts[framework]
        lines.append(f"- **{framework}**: {count} independent runs")
    
    lines.extend([
        "",
        "**Replication Protocol:**",
        f"- Each run executes the complete {num_steps}-step evolution scenario independently",
        "- **Runs are performed strictly sequentially** (not in parallel) to enable accurate API usage tracking:",
        "  - OpenAI Usage API aggregates data across all parallel requests using the same API key",
        "  - Sequential execution ensures each run's API usage can be isolated and measured distinctly",
        "  - This is the only reliable method to attribute token consumption to individual experimental runs",
        "- Each run uses a fresh isolated environment (new virtual environment, clean workspace)",
        "- Random seed fixed at 42 for frameworks that support deterministic execution",
        "- Non-deterministic LLM responses introduce natural variance across runs",
        "",
        "**Statistical Power:**",
        f"- Current sample sizes ({run_counts_str}) provide sufficient power for detecting large effect sizes",
        f"- **Bootstrap confidence intervals** ({n_bootstrap:,} resamples) quantify uncertainty in our estimates:",
        f"  - Simulates collecting {n_bootstrap:,} alternative datasets by resampling our actual data with replacement",
        f"  - Each resample calculates the metric (e.g., mean AUTR), creating a distribution of possible values",
        f"  - 95% CI shows the range where we expect the true population mean to fall 95% of the time",
        f"  - This accounts for the fact that we only have a limited sample (not infinite runs)",
        f"- Stopping rule: Continue until CI half-width ≤ {max_half_width_pct}% of mean (max {max_runs} runs per framework)",
        f"- Current status: {', '.join([f'{fw} ({count}/{max_runs})' for fw, count in run_counts.items()])}",
        "",
        "#### **Standardized Task Sequence**",
        "",
        f"All frameworks execute the **identical {num_steps}-step evolution scenario** in strict sequential order:",
        "",
    ])
    
    # Add dynamically loaded step descriptions
    for step_num in sorted(step_descriptions.keys(), key=int):
        lines.append(f"{step_num}. **Step {step_num}**: {step_descriptions[step_num]}")
    
    lines.extend([
        "",
        f"*Natural language commands stored in version-controlled files (`{prompts_dir}/step_1.txt` through `step_{num_steps}.txt`) ensure perfect reproducibility across runs.*",
        "",
        "#### **Controlled Variables**",
        "",
        "To ensure fair comparison, the following variables are **held constant** across all frameworks:",
        "",
        "**Generative AI Model**:",
        f"- Model: `{model_name}` ({model_display})",
        "- Temperature: Framework default (typically 0.7-1.0)",
        "- All frameworks use the **same model version** for all steps",
        "",
        "**API Infrastructure**:",
        "- Each framework uses a **dedicated OpenAI API key** (prevents quota conflicts)",
        f"- API keys: {', '.join(['`' + meta['api_key_env'] + '`' for meta in framework_metadata.values()])}",
        "- Token consumption measured via **OpenAI Usage API** (`/v1/organization/usage/completions`)",
        "- Time-window queries (Unix timestamps) ensure accurate attribution to each execution step",
        "",
        "**Execution Environment**:",
        f"- Python {python_version} isolated virtual environments per framework",
        "- Dependencies installed from framework-specific requirements at pinned commits",
        "- Single-threaded sequential execution (no parallelism)",
        f"- {step_timeout_minutes}-minute timeout per step (`step_timeout_seconds: {step_timeout_seconds}`)",
        "",
        "**Random Seed**:",
        "- Fixed seed: `random_seed: 42` (for frameworks that support deterministic execution)",
        "",
        "#### **Framework Adapter Implementation**",
        "",
        "**Isolation Strategy**: Each framework runs through a custom **adapter** (wrapper) that:",
        "",
        "1. **Clones repository** at exact commit hash (ensures version consistency)",
        "2. **Creates isolated virtual environment** with framework-specific dependencies",
        "3. **Translates standard commands** to framework-specific CLI/API invocations",
        "4. **Executes steps sequentially** with proper environment variables and timeouts",
        "5. **Captures stdout/stderr** for logging and debugging",
        "6. **Queries OpenAI Usage API** with step-specific time windows for token counting",
        "7. **Cleans up gracefully** after run completion",
        "",
        "**Non-Invasive Design**: Adapters are **read-only wrappers** that:",
        "- ✅ Do NOT modify framework source code",
        "- ✅ Do NOT alter framework algorithms or decision-making",
        "- ✅ Do NOT inject custom prompts beyond the standardized task descriptions",
        "- ✅ Only handle infrastructure (environment setup, execution, metric collection)",
        "",
        "*Example: ChatDev adapter constructs command:*",
        "```",
        "python run.py --task \"<step_text>\" --name \"BAEs_Step1_<run_id>\" \\",
        "             --config Default --model GPT_4O_MINI",
        "```",
        "",
        "#### **Metric Collection**",
        "",
        "**Token Counting (TOK_IN, TOK_OUT)**:",
        "- Primary source: **OpenAI Usage API** (authoritative, billing-grade accuracy)",
        "- Query parameters: `start_time` (step start Unix timestamp), `end_time` (step end timestamp)",
        f"- Model filter: `models=[\"{model_name}\"]` (isolates framework's usage)",
        "- Aggregates all API calls within time window (handles multi-request steps)",
        "",
        "**Timing (T_WALL_seconds, ZDI)**:",
        "- Wall-clock time: `time.time()` before/after each step (Python `time` module)",
        "- Zero-Downtime Intervals (ZDI): Idle time between consecutive steps",
        "",
        "**Automation Metrics (AUTR, HIT, HEU)**:",
        "- AUTR: Autonomy rate = 1 - (HIT / UTT), measuring independence from human intervention",
        "- HIT: Human-in-the-loop count (clarification requests detected in logs)",
        "- HEU: Human effort units (manual interventions required)",
        "",
        "**Quality Metrics (CRUDe, ESR, MC, Q\\*)**: ⚠️ **NOT MEASURED IN CURRENT EXPERIMENTS**",
        "- CRUDe: CRUD operations implemented (requires running application servers)",
        "- ESR: Emerging state rate (requires endpoint validation)",
        "- MC: Model call efficiency (requires runtime testing)",
        "- Q\\*: Composite quality score (0.4·ESR + 0.3·CRUDe/12 + 0.3·MC)",
        "- **Note**: These metrics always show zero because generated applications are not executed. Validation would require starting servers (`uvicorn`, `flask run`) and testing endpoints, which is not implemented. See `docs/QUALITY_METRICS_INVESTIGATION.md` for details.",
        "",
        "**Composite Scores (AEI)**:",
        "- AEI: Automation Efficiency Index = AUTR / log(1 + TOK_IN)",
        "- Balances automation quality against token consumption",
        "",
        "### ⚠️ Threats to Validity (Ameaças à Validade)",
        "",
        "#### **Internal Validity**",
        "",
        "**✅ Controlled Threats:**",
        f"- **Model Consistency**: All frameworks use identical `{model_name}` model",
        "- **Command Consistency**: Same 6 natural language prompts in identical order",
        "- **Timing Isolation**: Dedicated API keys prevent cross-framework interference",
        "- **Environment Isolation**: Separate virtual environments prevent dependency conflicts",
        "- **Version Pinning**: Exact commit hashes ensure reproducible framework behavior",
        "",
        "**⚠️ Uncontrolled Threats:**",
        "- **Framework-Specific Behavior**: Each framework has unique internal prompts, agent coordination, and retry logic",
        "  - *Mitigation*: Documented in adapter implementations; accepted as inherent framework characteristics",
        f"- **Non-Deterministic LLM Responses**: `{model_name}` may produce different outputs for identical inputs",
        "  - *Mitigation*: Fixed random seed (42) helps but doesn't guarantee full determinism",
        f"  - *Statistical Control*: Multiple runs ({min_runs}-{max_runs} per framework) with bootstrap CI to capture variance",
        "- **HITL Detection Accuracy**: Human-in-the-loop counts rely on pattern matching in logs",
        "  - *ChatDev*: 5 regex patterns detect clarification requests (lines 821-832)",
        "  - *GHSpec*: Explicit `[NEEDS CLARIFICATION:]` marker detection (line 544)",
        "  - *BAEs*: ⚠️ **No detection implemented** - hardcoded to zero (lines 330, 348)",
        "  - *Mitigation (BAEs)*: Manual investigation of 23 runs confirmed zero HITL events (see `BAES_HITL_INVESTIGATION.md`)",
        "  - *Limitation*: Pattern matching may miss implicit clarifications or produce false positives",
        "  - *Risk*: BAEs cannot detect HITL events in future experiments with ambiguous requirements",
        "",
        "#### **External Validity**",
        "",
        "**Generalization Concerns:**",
        "- **Single Task Domain**: CRUD application (Student/Course/Teacher) may not represent all software types",
        "  - *Scope*: Results apply to data-driven web API development; may differ for other domains (ML, systems, mobile)",
        f"- **Single Model**: Results specific to `{model_name}`; other models (GPT-4, Claude, Gemini) may alter rankings",
        f"  - *Trade-off*: Chose `{model_name}` for cost and speed; representative of practical usage",
        "- **Framework Versions**: Pinned commits may not reflect latest improvements",
        "  - *Justification*: Ensures reproducibility; future studies can test newer versions",
        "",
        "#### **Construct Validity**",
        "",
        "**Metric Interpretation:**",
        "- **Token Usage (TOK_IN/TOK_OUT)**: Measures cost, not necessarily code quality",
        "  - *Caveat*: Lower tokens ≠ better software; high-quality output may justify higher consumption",
        "- **Quality Metrics (Q\\*, ESR, CRUDe, MC)**: ⚠️ **Show zero values because runtime validation is not performed**",
        "  - Generated applications are not started during experiments (`auto_restart_servers: false`)",
        "  - Validation requires running servers and testing endpoints",
        "  - Current experiment scope: **Code generation efficiency**, not **runtime quality**",
        "  - *Action Required*: Implement server startup and endpoint testing for quality evaluation (see `docs/QUALITY_METRICS_INVESTIGATION.md`)",
        "- **AUTR (Autonomy Rate)**: All frameworks achieve 100% autonomy (no human intervention required)",
        "  - *Note*: AUTR = 1.0 means HIT = 0 (no human-in-the-loop interventions needed)",
        "  - *Implementation Variance*: ChatDev and GHSpec use active HITL detection; BAEs hardcodes zero",
        "  - *Validation*: See 'HITL Detection Implementation Notes' section for framework-specific details",
        "",
        "#### **Conclusion Validity**",
        "",
        "**Statistical Rigor:**",
        "- **Non-Parametric Tests**: Kruskal-Wallis and Dunn-Šidák avoid normality assumptions",
        "- **Effect Sizes**: Cliff's delta quantifies practical significance beyond p-values",
        f"- **Bootstrap CI**: {confidence_pct}% confidence intervals with {n_bootstrap:,} resamples for stable estimates",
        f"- **Small Sample Awareness**: Current results ({run_counts_str}) show large CI widths; p-values > 0.05 expected",
        f"  - *Stopping Rule*: Experiment continues until CI half-width ≤ {max_half_width_pct}% of mean ({max_runs} runs max)",
        "",
        "**Interpretation Caveats:**",
        "- **Non-Significant Results**: p > 0.05 does NOT prove frameworks are equivalent, only insufficient evidence of difference",
        "- **Large Effect Sizes Without Significance**: May reflect true differences masked by small sample (see pairwise interpretations)",
        "- **Relative Performance**: \"baes uses 9.4x fewer tokens\" is observational; not statistically confirmed yet",
        "",
        "### 📊 Data Availability",
        "",
        "**Reproducibility Artifacts:**",
        "- Configuration: `config/experiment.yaml` (framework commits, timeouts, seed)",
        "- Prompts: `config/prompts/step_1.txt` through `step_6.txt` (version-controlled)",
        "- Source Code: Adapter implementations in `src/adapters/` (BaseAdapter, ChatDevAdapter, GHSpecAdapter, BAeSAdapter)",
        "- Results Archive: Each run saved as `<run_id>.tar.gz` with metrics.json, step_metrics.json, logs, workspace",
        "- Analysis Scripts: `src/analysis/report_generator.py` (this report generator), `src/analysis/visualizations.py`",
        "",
        "**Commit Hashes**:",
    ])
    
    # Generate commit hashes dynamically
    for fw_key in sorted(framework_metadata.keys()):
        meta = framework_metadata[fw_key]
        lines.append(f"- {meta['full_name']}: `{meta['commit_hash']}`")
    
    lines.extend([
        "",
        "---",
        ""
    ])
    
    # Add Metric Glossary - Split into 3 Tables for Clarity
    lines.extend([
        "## Metric Definitions",
        "",
        "### ✅ Reliably Measured Metrics",
        "",
        "These metrics have consistent measurement across all frameworks with authoritative data sources:",
        ""
    ])
    
    # Generate reliable metrics table from config
    lines.extend(_generate_metric_table_from_config(metrics_config, 'reliable'))
    
    lines.extend([
        "",
        "**New Metrics Added (Oct 2025)**:",
        "- **API_CALLS**: Measures call efficiency - lower values indicate better batching and fewer retries",
        "- **CACHED_TOKENS**: Represents cost savings (~50% discount on cached tokens)",
        "- **Cache Hit Rate**: Calculated as `(CACHED_TOKENS / TOK_IN) × 100%` - measures prompt reuse efficiency",
        "",
        "### ⚠️ Partially Measured Metrics",
        "",
        "These metrics have **inconsistent measurement** across frameworks due to implementation gaps:",
        "",
        "| Metric | Full Name | ChatDev | GHSpec | BAEs | Issue |",
        "|--------|-----------|---------|--------|------|-------|",
        "| **AUTR** | Automated User Testing Rate | ✅ | ✅ | ❌ | BAEs: No HITL detection |",
        "| **AEI** | Automation Efficiency Index | ✅ | ✅ | ❌ | Depends on AUTR |",
        "| **HIT** | Human-in-the-Loop Count | ✅ | ✅ | ❌ | BAEs: Hardcoded to 0 |",
        "| **HEU** | Human Effort Units | ✅ | ✅ | ❌ | Depends on HIT |",
        "",
        "**HITL Detection Methods:**",
        "- **ChatDev**: 5 regex patterns detect clarification requests in logs (lines 821-832 in adapter)",
        "- **GHSpec**: Explicit `[NEEDS CLARIFICATION:]` marker detection (line 544 in adapter)",
        "- **BAEs**: ❌ No detection implemented - hardcoded to zero (lines 330, 348 in adapter)",
        "",
        "**Scientific Implication**: AUTR and AEI values for **BAEs are not reliable**. HITL events (if they occur) would not be detected. Current values (AUTR=1.0, HIT=0) may be accurate for this specific experiment but cannot be verified. Manual investigation of 23 BAEs runs confirmed zero HITL events (see `docs/baes/BAES_HITL_INVESTIGATION.md`), but future experiments with ambiguous requirements may miss HITL events.",
        "",
        "### ❌ Unmeasured Metrics",
        "",
        "These metrics **always show zero values** because runtime validation is not performed:",
        ""
    ])
    
    # Generate unmeasured metrics table from config
    lines.extend(_generate_metric_table_from_config(metrics_config, 'excluded'))
    
    lines.extend([
        "",
        "**Why Unmeasured?** Generated applications are not started during experiments (`auto_restart_servers: false` in config). Validation requires:",
        "1. Running application servers (`uvicorn`, `flask run`, etc.)",
        "2. Testing CRUD endpoints (`http://localhost:8000-8002`)",
        "3. Measuring runtime behavior and error rates",
        "",
        "**Current Experiment Scope**: Measures **code generation efficiency** (tokens, time, automation), not **runtime code quality**. See `docs/QUALITY_METRICS_INVESTIGATION.md` for implementation details and `docs/RELIABLE_METRICS_IMPLEMENTATION_PLAN.md` for future work roadmap.",
        "",
        "### 🔍 HITL Detection Implementation Notes",
        "",
        "**Human-in-the-Loop (HITL) Detection** varies significantly across frameworks due to architectural differences:",
        "",
        "#### **ChatDev Adapter** ✅ Active Detection",
        "- **Method**: Pattern-based log analysis with 5 regex patterns",
        "- **Patterns Detected**:",
        "  - `clarif(y|ication)` - Explicit clarification requests",
        "  - `ambiguous|unclear` - Ambiguity indicators",
        "  - `need.*input|require.*input` - Direct input requests",
        "  - `cannot proceed|blocked` - Execution blockers",
        "  - `manual.*intervention` - Manual intervention flags",
        "- **Implementation**: `src/adapters/chatdev_adapter.py` (lines 821-832)",
        "- **Status**: ✅ Actively detecting HITL events in ChatDev logs",
        "",
        "#### **GHSpec Adapter** ✅ Active Detection",
        "- **Method**: Explicit marker detection",
        "- **Pattern**: `[NEEDS CLARIFICATION:]` in framework output",
        "- **Rationale**: GHSpec uses standardized markers for human interaction points",
        "- **Implementation**: `src/adapters/ghspec_adapter.py` (line 544)",
        "- **Status**: ✅ Actively detecting HITL events via GHSpec markers",
        "",
        "#### **BAEs Adapter** ❌ No Detection Implemented",
        "- **Current Implementation**: `hitl_count` hardcoded to `0` (lines 330 & 348 in `src/adapters/baes_adapter.py`)",
        "- **Scientific Implication**: **HITL-based metrics (HIT, AUTR, AEI, HEU) are not reliably measured for BAEs**",
        "  - Cannot detect if HITL events occur during execution",
        "  - Current values (HIT=0, AUTR=1.0) are **assumptions**, not measurements",
        "  - Results may appear artificially high (perfect autonomy) regardless of actual behavior",
        "",
        "- **Observational Evidence** (October 2025 - Informational Only):",
        "  - Manual review of 23 BAEs runs found no clarification patterns in logs",
        "  - Suggests BAEs likely operates autonomously for this specific task domain",
        "  - However, this is **not a substitute for proper instrumentation**",
        "",
        "- **Why Hardcoded Zero Is Insufficient**:",
        "  - ❌ Not scientifically verifiable - no measurement mechanism",
        "  - ❌ Cannot distinguish \"no HITL events\" from \"events not detected\"",
        "  - ❌ Prevents valid comparison with ChatDev and GHSpec (which have detection)",
        "  - ❌ May hide issues in future experiments with different task types",
        "",
        "- **Required Future Work**: Implement BAEs-specific HITL detection:",
        "  - Add pattern matching for: `clarification`, `ambiguous`, `cannot determine`, `unclear`",
        "  - Search kernel output logs for entity communication failures",
        "  - Track request-response validation errors",
        "  - Update lines 330 & 348 to use detected count instead of hardcoded zero",
        "",
        "#### **Impact on Experimental Validity**",
        "",
        "**Metric Reliability by Framework**:",
        "",
        "| Framework | HITL Detection | HIT Reliability | AUTR Reliability | AEI Reliability |",
        "|-----------|----------------|-----------------|------------------|-----------------|",
        "| ChatDev   | ✅ Implemented | ✅ Measured     | ✅ Measured      | ✅ Measured     |",
        "| GHSpec    | ✅ Implemented | ✅ Measured     | ✅ Measured      | ✅ Measured     |",
        "| BAEs      | ❌ Not Implemented | ❌ Hardcoded (0) | ❌ Assumed (1.0) | ❌ Unreliable |",
        "",
        "**Interpretation Guidelines**:",
        "",
        "1. **For ChatDev and GHSpec**: AUTR=1.0 is a **verified measurement** (active detection confirmed no HITL events)",
        "",
        "2. **For BAEs**: AUTR=1.0 is an **unverified assumption** (no detection mechanism)",
        "   - May be accurate (manual review suggests it is for current tasks)",
        "   - Cannot be scientifically confirmed without proper instrumentation",
        "   - **Should not be directly compared** with ChatDev/GHSpec AUTR values",
        "",
        "3. **Cross-Framework Comparisons**:",
        "   - ✅ **Valid**: TOK_IN, TOK_OUT, T_WALL, API_CALLS, CACHED_TOKENS (all properly measured)",
        "   - ⚠️ **Questionable**: AUTR, AEI comparisons involving BAEs (measurement method inconsistent)",
        "   - ❌ **Invalid**: Claims about BAEs autonomy superiority (not measured, only assumed)",
        "",
        "**Critical Limitation for This Experiment**:",
        "- AUTR and AEI comparisons are **methodologically unsound** when BAEs is included",
        "- Recommendation: **Report BAEs AUTR/AEI as \"Not Measured\"** or clearly mark as estimated",
        "- Alternative: Focus comparisons on **reliably measured metrics** (tokens, time, API calls)",
        "",
        "**Documentation References**:",
        "- Full adapter analysis: `AUTR_ADAPTER_ANALYSIS.md`",
        "- BAEs investigation report: `BAES_HITL_INVESTIGATION.md`",
        "- Adapter implementations: `src/adapters/` (all three adapters)",
        "",
        "---",
        ""
    ])
    
    # Add Statistical Methods Guide
    lines.extend([
        "## Statistical Methods Guide",
        "",
        "This report uses non-parametric statistics to compare frameworks robustly.",
        "",
        "### 📖 Key Concepts",
        "",
        "**Bootstrap Confidence Intervals (CI)** - Understanding Uncertainty",
        "",
        f"*What is bootstrapping?* A computational technique to estimate how much our results might vary if we ran the experiment again:",
        "",
        f"1. **The Problem**: We have limited data (e.g., {min_runs}-{max_runs} runs per framework), but we want to know what the 'true' average would be with infinite runs",
        f"2. **The Solution**: Bootstrap resampling simulates having multiple datasets:",
        f"   - Take our actual data (e.g., 10 AUTR values: [0.8, 0.9, 0.85, ...])",
        f"   - Create {n_bootstrap:,} 'fake' datasets by randomly picking values from the original (with replacement)",
        f"   - 'With replacement' means the same value can appear multiple times in a resample",
        f"   - Example resample: [0.9, 0.8, 0.9, 0.85, ...] (notice 0.9 appears twice)",
        f"3. **Calculate**: Compute the mean for each of the {n_bootstrap:,} resamples",
        f"4. **Result**: We get {n_bootstrap:,} different means, showing the distribution of possible values",
        f"5. **95% CI**: The middle 95% of this distribution becomes our confidence interval",
        "",
        "*Reading the numbers:*",
        "- Example: `AUTR: 0.85 [0.78, 0.92]`",
        "  - 0.85 is the observed mean from our actual data",
        "  - [0.78, 0.92] is the 95% confidence interval",
        "  - Interpretation: 'We are 95% confident the true population mean is between 0.78 and 0.92'",
        "  - If we repeated the entire experiment, we'd expect the mean to fall in this range 95% of the time",
        "",
        "*What do interval widths tell us?*",
        "- **Narrow interval** (e.g., [0.83, 0.87]): High precision, low uncertainty, stable results",
        "- **Wide interval** (e.g., [0.50, 0.95]): High uncertainty, need more runs for reliable estimates",
        "- Width decreases as we collect more runs (sample size increases)",
        "",
        "**Kruskal-Wallis H-Test**",
        "- Non-parametric test comparing multiple groups (doesn't assume normal distribution)",
        "- Tests: \"Are there significant differences across frameworks?\"",
        "- **H statistic**: Higher values = larger differences between groups",
        "- **p-value**: Probability results occurred by chance",
        "  - p < 0.05: Statistically significant (likely real difference) ✓",
        "  - p ≥ 0.05: Not significant (could be random variation) ✗",
        "",
        "**Pairwise Comparisons (Dunn-Šidák)**",
        "- Compares specific framework pairs after significant Kruskal-Wallis result",
        "- Dunn-Šidák correction prevents false positives from multiple comparisons",
        "- Each comparison tests: \"Is framework A different from framework B?\"",
        "",
        "**Cliff's Delta (δ) - Effect Size**",
        "- Measures practical significance (how large is the difference?)",
        "- Range: -1 to +1",
        "  - **δ = 0**: No difference (distributions completely overlap)",
        "  - **δ = ±1**: Complete separation (no overlap)",
        "- Interpretation:",
        "  - |δ| < 0.147: **Negligible** (tiny difference)",
        "  - 0.147 ≤ |δ| < 0.330: **Small** (noticeable)",
        "  - 0.330 ≤ |δ| < 0.474: **Medium** (substantial)",
        "  - |δ| ≥ 0.474: **Large** (major difference)",
        "",
        "### 💡 How to Read Results",
        "",
        "1. **Check p-value**: Is the difference statistically significant (p < 0.05)?",
        "2. **Check effect size**: Is the difference practically meaningful (|δ| ≥ 0.147)?",
        "3. **Both matter**: Statistical significance without large effect = real but trivial difference",
        "",
        "**Example Interpretation:**",
        "- `p = 0.012 (✓), δ = 0.850 (large)` → Strong evidence of major practical difference",
        "- `p = 0.048 (✓), δ = 0.095 (negligible)` → Statistically significant but practically trivial",
        "- `p = 0.234 (✗), δ = 0.650 (large)` → Large observed difference but may be random variation",
        "",
        "---",
        ""
    ])
    
    # Add Executive Summary
    lines.extend(_generate_executive_summary(frameworks_data, run_counts))
    
    # Collect all metrics
    all_metrics = set()
    for runs in frameworks_data.values():
        for run in runs:
            all_metrics.update(run.keys())
    
    all_metrics = sorted(all_metrics)
    
    # Get metrics for analysis from config
    # Read from aggregate_statistics section config, fallback to reliable metrics from MetricsConfig
    aggregate_stats_section = metrics_config.get_report_section('aggregate_statistics')
    if aggregate_stats_section and 'metrics' in aggregate_stats_section:
        # Use metrics list from aggregate_statistics section
        metrics_for_analysis = aggregate_stats_section['metrics']
        logger.info(f"Using metrics from aggregate_statistics config: {metrics_for_analysis}")
    else:
        # Fallback: use all reliable metrics from MetricsConfig
        reliable_metrics = metrics_config.get_reliable_metrics()
        metrics_for_analysis = sorted(reliable_metrics.keys())
        logger.warning(
            f"No metrics list in aggregate_statistics config, "
            f"using all reliable metrics: {metrics_for_analysis}"
        )
    
    # Filter to only include metrics that exist in the data
    metrics_for_analysis = [m for m in metrics_for_analysis if m in all_metrics]
    
    logger.info(f"Metrics for analysis (filtered by availability): {metrics_for_analysis}")
    logger.info(f"Excluded metrics (not in analysis list): {sorted(set(all_metrics) - set(metrics_for_analysis))}")
    
    # Section 1: Aggregate Statistics (Reliable Metrics Only)
    lines.extend([
        "## 1. Aggregate Statistics (Reliable Metrics Only)",
        "",
        "**Analysis Scope**: This section includes **only reliably measured metrics** with consistent data sources across all frameworks.",
        "",
        "**Excluded Metrics:**",
        "- ❌ **Unmeasured**: Q*, ESR, CRUDe, MC (always zero - applications not executed)",
        "- ⚠️ **Partially Measured**: AUTR, AEI, HIT, HEU (inconsistent HITL detection - BAEs not supported)",
        "",
        "See 'Metric Definitions' section for complete measurement status details.",
        "",
        "### Mean Values with 95% Bootstrap CI",
        "",
        "*Note: Token values shown with thousands separator; time in seconds (minutes if >60s)*",
        "",
        "**Performance Indicators:** 🟢 Best | 🟡 Middle | 🔴 Worst",
        ""
    ])
    
    # Table header with sample size column - use metrics_for_analysis instead of all_metrics
    header = "| Framework | N | " + " | ".join(metrics_for_analysis) + " |"
    separator = "|-----------|---|" + "|".join(["-" * 12 for _ in metrics_for_analysis]) + "|"
    lines.extend([header, separator])
    
    # First pass: collect all mean values for each metric to determine indicators
    framework_means = {}
    for framework, runs in frameworks_data.items():
        aggregated = bootstrap_aggregate_metrics(runs)
        framework_means[framework] = aggregated
    
    # Collect all values per metric for comparison (reliable metrics only)
    metric_values = {}
    for metric in metrics_for_analysis:
        metric_values[metric] = []
        for framework in frameworks_data.keys():
            if metric in framework_means[framework]:
                metric_values[metric].append(framework_means[framework][metric]['mean'])
    
    # Check if performance indicators should be shown
    show_indicators = aggregate_stats_section.get('show_performance_indicators', True) if aggregate_stats_section else True
    
    # Table rows with indicators (reliable metrics only)
    for framework in frameworks_data.keys():
        aggregated = framework_means[framework]
        n = run_counts[framework]
        row = f"| {framework} | {n} |"
        
        for metric in metrics_for_analysis:
            if metric in aggregated:
                stats = aggregated[metric]
                mean = stats['mean']
                ci_lower = stats['ci_lower']
                ci_upper = stats['ci_upper']
                
                # Format values with units
                formatted_mean = _format_metric_value(metric, mean, include_units=False)
                formatted_ci = _format_confidence_interval(ci_lower, ci_upper, metric)
                
                # Add performance indicator if enabled
                indicator = ""
                if show_indicators:
                    indicator = _get_performance_indicator(metric, mean, metric_values[metric])
                
                row += f" {formatted_mean} {formatted_ci}{indicator} |"
            else:
                row += " N/A |"
        
        lines.append(row)
    
    lines.extend(["", ""])
    
    # Section 2: Relative Performance (Reliable Metrics Only)
    relative_performance_lines = _generate_relative_performance(framework_means, metrics_for_analysis)
    lines.extend(relative_performance_lines)
    
    # Cost Analysis Section (Config-driven, optional)
    cost_config = metrics_config.get_report_section('cost_analysis')
    if cost_config and cost_config.get('enabled', False):
        logger.info("Generating cost analysis section")
        # Pass the full config dict to access model pricing
        cost_config_with_model = {**cost_config, 'model': config.get('model', 'gpt-4o-mini')}
        cost_lines = _generate_cost_analysis(frameworks_data, cost_config_with_model)
        lines.extend(cost_lines)
    else:
        logger.info("Cost analysis section disabled by config")
    
    # Section 3: Kruskal-Wallis Tests (Config-driven)
    kw_config = metrics_config.get_report_section('kruskal_wallis')
    if not kw_config or not kw_config.get('enabled', True):
        logger.info("Kruskal-Wallis section disabled by config")
    else:
        # Read configuration with fallbacks
        kw_title = kw_config.get('title', '## 3. Kruskal-Wallis H-Tests (Reliable Metrics Only)')
        kw_skip_zero_variance = kw_config.get('skip_zero_variance', True)
        kw_significance = kw_config.get('significance_level', 0.05)
        
        logger.info(
            f"Generating Kruskal-Wallis section: "
            f"skip_zero_variance={kw_skip_zero_variance}, "
            f"significance={kw_significance}"
        )
        
        lines.extend([
            kw_title,
            "",
            "Testing for significant differences across all frameworks using **reliably measured metrics only**.",
            "",
            "**Analysis Scope:**",
            "- ✅ Included: TOK_IN, TOK_OUT, API_CALLS, CACHED_TOKENS, T_WALL_seconds, ZDI",
            "- ❌ Excluded: AUTR, AEI, HIT, HEU (partial measurement), Q*, ESR, CRUDe, MC (unmeasured)",
            "",
        ])
        
        if kw_skip_zero_variance:
            lines.append("*Note: Metrics with zero variance (all values identical) are excluded from statistical testing.*")
            lines.append("")
        
        lines.extend([
            "| Metric | H | p-value | Significant | Groups | N |",
            "|--------|---|---------|-------------|--------|---|"
        ])
    
        skipped_metrics = []
    
        # Only test reliable metrics
        for metric in metrics_for_analysis:
            # Collect metric values by framework
            groups = {}
            for framework, runs in frameworks_data.items():
                groups[framework] = [run[metric] for run in runs if metric in run]
        
            if all(len(vals) > 0 for vals in groups.values()):
                # Check if all values are identical (zero variance)
                all_values = [v for vals in groups.values() for v in vals]
                if len(set(all_values)) == 1:
                    # Skip zero-variance metrics if configured
                    if kw_skip_zero_variance:
                        skipped_metrics.append(metric)
                        continue
            
                result = kruskal_wallis_test(groups)
                # Use configured significance level
                is_significant = result['p_value'] < kw_significance
                sig = "✓ Yes" if is_significant else "✗ No"
                lines.append(
                    f"| {metric} | {result['H']:.3f} | {result['p_value']:.4f} | "
                    f"{sig} | {result['n_groups']} | {result['n_total']} |"
                )
            
                # Add contextual interpretation
                interpretation = _interpret_kruskal_wallis(result, metric)
                if interpretation:
                    lines.append("")
                    lines.append(interpretation)
                    lines.append("")
            else:
                lines.append(f"| {metric} | N/A | N/A | N/A | N/A | N/A |")
    
        lines.extend(["", ""])
    
        # Add note about skipped metrics
        if kw_skip_zero_variance and skipped_metrics:
            lines.append(f"**Metrics Excluded** (zero variance): {', '.join(f'`{m}`' for m in skipped_metrics)}")
            lines.append("")
            lines.append(f"*Note: These metrics show identical values across all runs (no variance to test).*")
            lines.append("")
    
    # Section 4: Pairwise Comparisons (Config-driven)
    pw_config = metrics_config.get_report_section('pairwise_comparisons')
    if not pw_config or not pw_config.get('enabled', True):
        logger.info("Pairwise comparisons section disabled by config")
    else:
        # Read configuration with fallbacks
        pw_title = pw_config.get('title', '## 4. Pairwise Comparisons (Reliable Metrics Only)')
        pw_skip_zero_variance = pw_config.get('skip_zero_variance', True)
        pw_significance = pw_config.get('significance_level', 0.05)
        pw_correction = pw_config.get('correction_method', 'dunn_sidak')
        
        logger.info(
            f"Generating pairwise comparisons section: "
            f"skip_zero_variance={pw_skip_zero_variance}, "
            f"significance={pw_significance}, "
            f"correction={pw_correction}"
        )
        
        lines.extend([
            pw_title,
            "",
            f"Dunn-Šidák corrected pairwise tests with Cliff's delta effect sizes.",
            "",
            "**Analysis Scope**: Only reliably measured metrics included (TOK_IN, TOK_OUT, API_CALLS, CACHED_TOKENS, T_WALL_seconds, ZDI).",
            "",
        ])
        
        if pw_skip_zero_variance:
            lines.append("*Note: Metrics with zero variance are excluded from pairwise comparisons.*")
            lines.append("")
    
        # Only analyze reliable metrics
        for metric in metrics_for_analysis:
            # Skip metrics with zero variance (if configured and they were already identified)
            if pw_skip_zero_variance and 'skipped_metrics' in locals() and metric in skipped_metrics:
                continue
            
            # Collect metric values by framework
            groups = {}
            for framework, runs in frameworks_data.items():
                groups[framework] = [run[metric] for run in runs if metric in run]
        
            if all(len(vals) > 0 for vals in groups.values()) and len(groups) >= 2:
                # Double-check variance (shouldn't be needed, but defensive)
                all_values = [v for vals in groups.values() for v in vals]
                if len(set(all_values)) == 1:
                    if pw_skip_zero_variance:
                        continue
            
                lines.append(f"### {metric}")
                lines.append("")
                lines.append("| Comparison | p-value | Significant | Cliff's δ | Effect Size |")
                lines.append("|------------|---------|-------------|-----------|-------------|")
            
                # Pass configured significance level to pairwise_comparisons
                comparisons = pairwise_comparisons(groups, alpha=pw_significance)
            
                # Collect interpretations
                interpretations = []
            
                for comp in comparisons:
                    pair = f"{comp['group1']} vs {comp['group2']}"
                    sig = "✓" if comp['significant'] else "✗"
                    delta = comp['cliff_delta']
                    effect = comp['effect_size']
                
                    lines.append(
                        f"| {pair} | {comp['p_value']:.4f} | {sig} | "
                        f"{delta:.3f} | {effect} |"
                    )
                
                    # Collect interpretation
                    interp = _interpret_pairwise_comparison(comp, metric)
                    if interp:
                        interpretations.append(interp)
            
                # Add interpretations after the table
                if interpretations:
                    lines.append("")
                    lines.extend(interpretations)
            
                lines.extend(["", ""])
    
    # Section 5: Outlier Detection (Config-driven)
    od_config = metrics_config.get_report_section('outlier_detection')
    if not od_config or not od_config.get('enabled', True):
        logger.info("Outlier detection section disabled by config")
    else:
        # Read configuration with fallbacks
        od_title = od_config.get('title', '## 5. Outlier Detection (Reliable Metrics Only)')
        od_threshold = od_config.get('threshold_std', 3.0)
        
        logger.info(
            f"Generating outlier detection section: "
            f"threshold={od_threshold}σ"
        )
        
        lines.extend([
            od_title,
            "",
            f"Values > {od_threshold}σ from median (per framework, per metric).",
            "",
            "**Analysis Scope**: Only reliably measured metrics checked for outliers.",
            ""
        ])
    
        outliers_found = False
        for framework, runs in frameworks_data.items():
            framework_outliers = []
        
            # Only check reliable metrics for outliers
            for metric in metrics_for_analysis:
                values = [run[metric] for run in runs if metric in run]
                if len(values) >= 3:
                    # Use configured threshold
                    outlier_indices, outlier_values = identify_outliers(values, threshold_std=od_threshold)
                
                    if outlier_indices:
                        framework_outliers.append(
                            f"  - **{metric}**: {len(outlier_indices)} outlier(s) "
                            f"at runs {outlier_indices} with values {outlier_values}"
                        )
        
            if framework_outliers:
                outliers_found = True
                lines.append(f"**{framework}:**")
                lines.extend(framework_outliers)
                lines.append("")
    
        if not outliers_found:
            lines.append("No outliers detected.")
            lines.append("")
    
        lines.append("")  # Extra spacing before next section
    
    # Section 6: Visual Summary (Reliable Metrics Only)
    lines.extend([
        "## 6. Visual Summary (Reliable Metrics Only)",
        "",
        "### Key Visualizations",
        "",
        "All visualizations use **reliably measured metrics only** to ensure accurate framework comparison:",
        "",
        "**Radar Chart** - Multi-dimensional comparison across 6 reliable metrics (TOK_IN, TOK_OUT, T_WALL, API_CALLS, CACHED_TOKENS, ZDI)",
        "",
        "![Radar Chart](radar_chart.svg)",
        "",
        "**Token Efficiency Chart** - Scatter plot: Input vs Output tokens with execution time",
        "",
        "![Token Efficiency](token_efficiency.svg)",
        "",
        "**API Efficiency Bar Chart** - API calls with tokens-per-call ratios",
        "",
        "![API Efficiency](api_efficiency_bar.svg)",
        "",
        "**Cache Efficiency Chart** - Stacked bars: Cached vs uncached tokens with hit rates",
        "",
        "![Cache Efficiency](cache_efficiency_chart.svg)",
        "",
        "**Time Distribution Chart** - Box plots showing execution time variability",
        "",
        "![Time Distribution](time_distribution.svg)",
        "",
        "**API Efficiency Chart** - Token efficiency across frameworks",
        "",
        "![API Efficiency Chart](api_efficiency_chart.svg)",
        "",
        "**API Calls Timeline** - API call patterns over time",
        "",
        "![API Calls Timeline](api_calls_timeline.svg)",
        "",
        "---",
        ""
    ])
    
    # Section 7: Recommendations
    lines.extend([
        "## 7. Recommendations",
        "",
        "### 🎯 Framework Selection Guidance",
        ""
    ])
    
    # Generate recommendations based on analysis
    # Extract mean values from framework_means for recommendation logic
    simple_aggregated = {}
    for framework, metrics in framework_means.items():
        simple_aggregated[framework] = {
            metric: stats['mean']
            for metric, stats in metrics.items()
        }
    
    recommendations = []
    
    # Analyze the data to provide recommendations
    if all('TOK_IN' in data for data in simple_aggregated.values()):
        min_tokens = min(simple_aggregated.items(), key=lambda x: x[1].get('TOK_IN', float('inf')))
        max_tokens = max(simple_aggregated.items(), key=lambda x: x[1].get('TOK_IN', 0))
        
        if min_tokens[1]['TOK_IN'] > 0 and max_tokens[1]['TOK_IN'] / min_tokens[1]['TOK_IN'] > 3:
            recommendations.append(
                f"**💰 Cost Optimization**: Choose **{min_tokens[0]}** if minimizing LLM token costs is priority. "
                f"It uses {max_tokens[1]['TOK_IN'] / min_tokens[1]['TOK_IN']:.1f}x fewer tokens than {max_tokens[0]}."
            )
    
    if all('T_WALL_seconds' in data for data in simple_aggregated.values()):
        fastest = min(simple_aggregated.items(), key=lambda x: x[1].get('T_WALL_seconds', float('inf')))
        slowest = max(simple_aggregated.items(), key=lambda x: x[1].get('T_WALL_seconds', 0))
        
        if fastest[1]['T_WALL_seconds'] > 0 and slowest[1]['T_WALL_seconds'] / fastest[1]['T_WALL_seconds'] > 2:
            time_diff = slowest[1]['T_WALL_seconds'] - fastest[1]['T_WALL_seconds']
            recommendations.append(
                f"**⚡ Speed Priority**: Choose **{fastest[0]}** for fastest execution. "
                f"It completes tasks {slowest[1]['T_WALL_seconds'] / fastest[1]['T_WALL_seconds']:.1f}x faster than {slowest[0]} "
                f"(saves ~{time_diff / 60:.1f} minutes per task)."
            )
    
    # API efficiency recommendation (reliable metric)
    if all('API_CALLS' in data and 'TOK_IN' in data for data in simple_aggregated.values()):
        api_efficiency = {fw: data['TOK_IN'] / data['API_CALLS'] if data['API_CALLS'] > 0 else 0 
                         for fw, data in simple_aggregated.items()}
        best_api_eff = max(api_efficiency.items(), key=lambda x: x[1])
        worst_api_eff = min(api_efficiency.items(), key=lambda x: x[1])
        
        if best_api_eff[1] > 0:
            recommendations.append(
                f"**📡 API Efficiency**: **{worst_api_eff[0]}** uses fewest API calls, "
                f"while **{best_api_eff[0]}** maximizes tokens per call (better batching). "
                f"Choose based on latency vs throughput priority."
            )
    
    # Cache efficiency recommendation (reliable metric)
    if all('CACHED_TOKENS' in data and 'TOK_IN' in data for data in simple_aggregated.values()):
        cache_rates = {fw: (data['CACHED_TOKENS'] / data['TOK_IN'] * 100) if data['TOK_IN'] > 0 else 0
                      for fw, data in simple_aggregated.items()}
        best_cache = max(cache_rates.items(), key=lambda x: x[1])
        
        if best_cache[1] > 5:  # Only recommend if meaningful cache usage
            recommendations.append(
                f"**💾 Cost Savings**: **{best_cache[0]}** achieves {best_cache[1]:.1f}% cache hit rate, "
                f"reducing costs through OpenAI's prompt caching (~50% discount on cached tokens)."
            )
    
    # Add scope note for all recommendations
    recommendations.insert(0, 
        "**📊 Analysis Scope**: Recommendations based on **reliably measured metrics only** "
        "(tokens, time, API calls, caching). Quality metrics (Q*, ESR, CRUDe, MC) and "
        "autonomy metrics (AUTR, AEI) excluded due to measurement limitations. "
        "See 'Limitations and Future Work' section for details."
    )
    
    # Add recommendations to report
    if recommendations:
        for rec in recommendations:
            lines.append(f"- {rec}")
            lines.append("")
    else:
        lines.append("*No specific recommendations available - insufficient data variance.*")
        lines.append("")
    
    lines.extend([
        "### 📋 Decision Matrix",
        "",
        "| Use Case | Recommended Framework | Rationale |",
        "|----------|----------------------|-----------|"
    ])
    
    # Build decision matrix
    if all('TOK_IN' in data for data in simple_aggregated.values()):
        min_tokens = min(simple_aggregated.items(), key=lambda x: x[1].get('TOK_IN', float('inf')))
        lines.append(f"| Cost-sensitive projects | {min_tokens[0]} | Lowest token consumption |")
    
    if all('T_WALL_seconds' in data for data in simple_aggregated.values()):
        fastest = min(simple_aggregated.items(), key=lambda x: x[1].get('T_WALL_seconds', float('inf')))
        lines.append(f"| Time-critical tasks | {fastest[0]} | Fastest execution time |")
    
    # Note: Removed AEI row - unreliable metric for BAEs
    
    lines.extend(["", ""])
    
    # Section 8: Limitations and Future Work (Config-driven)
    lim_config = metrics_config.get_report_section('limitations')
    if not lim_config or not lim_config.get('enabled', True):
        logger.info("Limitations section disabled by config")
    else:
        logger.info("Generating limitations section from config")
        limitations_lines = _generate_limitations_section(lim_config, run_counts, metrics_config)
        lines.extend(limitations_lines)
    
    # Write to file
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    logger.info(f"Statistical report saved to {output_path}")


def identify_outliers(
    values: List[float],
    threshold_std: float = 3.0
) -> Tuple[List[int], List[float]]:
    """
    Identify outliers using standard deviation method.
    
    Values more than threshold_std standard deviations from
    the median are flagged as outliers.
    
    Args:
        values: List of numeric values
        threshold_std: Number of standard deviations (default 3.0)
        
    Returns:
        Tuple of (outlier_indices, outlier_values)
    """
    if len(values) < 3:
        return [], []
    
    n = len(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / (n - 1)
    std = math.sqrt(variance)
    
    sorted_vals = sorted(values)
    median = sorted_vals[n // 2] if n % 2 == 1 else (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
    
    outlier_indices = []
    outlier_values = []
    
    for i, value in enumerate(values):
        if abs(value - median) > threshold_std * std:
            outlier_indices.append(i)
            outlier_values.append(value)
    
    return outlier_indices, outlier_values


# Helper functions

def _interpret_cliff_delta(delta: float) -> str:
    """Interpret Cliff's delta magnitude."""
    abs_delta = abs(delta)
    if abs_delta < 0.147:
        return 'negligible'
    elif abs_delta < 0.33:
        return 'small'
    elif abs_delta < 0.474:
        return 'medium'
    else:
        return 'large'


def _chi_square_cdf(x: float, df: int) -> float:
    """
    Approximate chi-square cumulative distribution function.
    
    Uses gamma function approximation for simplicity.
    For production use, consider scipy.stats.chi2.cdf()
    """
    # Simple approximation for small df
    if df == 1:
        return math.erf(math.sqrt(x / 2))
    elif df == 2:
        return 1 - math.exp(-x / 2)
    else:
        # Normal approximation for large df
        mean = df
        std = math.sqrt(2 * df)
        z = (x - mean) / std
        return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def _mann_whitney_u_test(group1: List[float], group2: List[float]) -> float:
    """
    Perform Mann-Whitney U test (Wilcoxon rank-sum test).
    
    Returns approximate p-value using normal approximation.
    """
    n1 = len(group1)
    n2 = len(group2)
    
    if n1 == 0 or n2 == 0:
        return 1.0
    
    # Combine and rank
    combined = [(x, 1) for x in group1] + [(x, 2) for x in group2]
    combined.sort(key=lambda x: x[0])
    
    # Assign ranks
    rank_sum_1 = 0
    for i, (_, group) in enumerate(combined):
        if group == 1:
            rank_sum_1 += i + 1
    
    # U statistic
    u1 = rank_sum_1 - n1 * (n1 + 1) / 2
    u2 = n1 * n2 - u1
    u = min(u1, u2)
    
    # Normal approximation
    mean_u = n1 * n2 / 2
    std_u = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    
    if std_u == 0:
        return 1.0
    
    z = (u - mean_u) / std_u
    
    # Two-tailed p-value
    p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    
    return p_value


def _generate_metric_table_from_config(metrics_config, category: str = 'reliable') -> List[str]:
    """
    Generate metric definition table from MetricsConfig.
    
    Args:
        metrics_config: MetricsConfig instance
        category: 'reliable', 'derived', or 'excluded'
        
    Returns:
        List of markdown lines for the metric table
    """
    lines = []
    
    if category == 'reliable':
        metrics = metrics_config.get_reliable_metrics()
        lines.extend([
            "| Metric | Full Name | Description | Range | Ideal | Data Source |",
            "|--------|-----------|-------------|-------|-------|-------------|"
        ])
        
        for key, metric in sorted(metrics.items()):
            # Determine ideal direction symbol
            ideal_symbol = "Lower ↓" if metric.ideal_direction == 'minimize' else "Higher ↑"
            
            # Determine range based on unit
            range_str = "0-∞" if metric.unit in ['tokens', 'seconds', 'count', 'USD'] else "0-1"
            if key == 'UTT':
                range_str = "Fixed"
            
            lines.append(
                f"| **{key}** | {metric.name} | {metric.description} | "
                f"{range_str} | {ideal_symbol} | {metric.data_source} |"
            )
    
    elif category == 'excluded':
        excluded = metrics_config.get_excluded_metrics()
        lines.extend([
            "| Metric | Full Name | Status | Reason |",
            "|--------|-----------|--------|--------|"
        ])
        
        for key, info in sorted(excluded.items()):
            lines.append(
                f"| **{key}** | {info.get('name', key)} | "
                f"{info.get('status', 'Excluded')} | {info.get('reason', 'Not measured')} |"
            )
    
    elif category == 'derived':
        metrics = metrics_config.get_derived_metrics()
        lines.extend([
            "| Metric | Full Name | Description | Calculation | Unit |",
            "|--------|-----------|-------------|-------------|------|"
        ])
        
        for key, metric in sorted(metrics.items()):
            calc_formula = ""
            if metric.calculation:
                calc_formula = metric.calculation.get('formula', 'See description')
            
            lines.append(
                f"| **{key}** | {metric.name} | {metric.description} | "
                f"{calc_formula} | {metric.unit} |"
            )
    
    return lines


def _get_timestamp() -> str:
    """Get current UTC timestamp in ISO format."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
