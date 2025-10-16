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
    aei = metrics['AUTR'] / math.log(1 + metrics['TOK_IN'])
    
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


def _generate_executive_summary(frameworks_data: Dict[str, List[Dict[str, float]]]) -> List[str]:
    """
    Generate executive summary section with key findings.
    
    Args:
        frameworks_data: Dict mapping framework names to lists of run metrics
    
    Returns:
        List of markdown lines for the executive summary section
    """
    lines = [
        "## Executive Summary",
        ""
    ]
    
    # Calculate aggregate statistics for summary
    aggregated = {}
    for framework, runs in frameworks_data.items():
        aggregated[framework] = {}
        # Get mean values for each metric
        all_metrics = set()
        for run in runs:
            all_metrics.update(run.keys())
        
        for metric in all_metrics:
            values = [run[metric] for run in runs if metric in run]
            if values:
                aggregated[framework][metric] = sum(values) / len(values)
    
    # Best performers section
    lines.extend([
        "### 🏆 Best Performers",
        ""
    ])
    
    # Most efficient (AEI)
    if all('AEI' in data for data in aggregated.values()):
        best_aei = max(aggregated.items(), key=lambda x: x[1].get('AEI', 0))
        lines.append(f"- **Most Efficient (AEI)**: {best_aei[0]} ({best_aei[1]['AEI']:.3f}) - best quality-per-token ratio")
    
    # Fastest (T_WALL_seconds)
    if all('T_WALL_seconds' in data for data in aggregated.values()):
        fastest = min(aggregated.items(), key=lambda x: x[1].get('T_WALL_seconds', float('inf')))
        time_seconds = fastest[1]['T_WALL_seconds']
        time_minutes = time_seconds / 60
        lines.append(f"- **Fastest (T_WALL)**: {fastest[0]} ({time_seconds:.1f}s / {time_minutes:.1f} min)")
    
    # Lowest token usage
    if all('TOK_IN' in data for data in aggregated.values()):
        lowest_tokens = min(aggregated.items(), key=lambda x: x[1].get('TOK_IN', float('inf')))
        tokens = lowest_tokens[1]['TOK_IN']
        lines.append(f"- **Lowest Token Usage**: {lowest_tokens[0]} ({tokens:,.0f} input tokens)")
    
    lines.extend(["", "### 📊 Key Insights", ""])
    
    # Test automation analysis
    if all('AUTR' in data for data in aggregated.values()):
        autr_values = [data['AUTR'] for data in aggregated.values()]
        if all(v == 1.0 for v in autr_values):
            lines.append("- ✅ All frameworks achieved perfect test automation (AUTR = 1.0)")
        else:
            avg_autr = sum(autr_values) / len(autr_values)
            lines.append(f"- Test automation varies across frameworks (average AUTR = {avg_autr:.2f})")
    
    # Quality metrics analysis
    quality_metrics = ['Q_star', 'ESR', 'CRUDe', 'MC']
    zero_quality_metrics = []
    for metric in quality_metrics:
        if all(metric in data and data[metric] == 0 for data in aggregated.values()):
            zero_quality_metrics.append(metric)
    
    if zero_quality_metrics:
        lines.append(f"- ⚠️ Quality metrics show zero values: {', '.join(zero_quality_metrics)} - may need verification")
    
    # Performance variation analysis
    if all('T_WALL_seconds' in data for data in aggregated.values()):
        times = [data['T_WALL_seconds'] for data in aggregated.values()]
        if len(times) > 1:
            max_time = max(times)
            min_time = min(times)
            if min_time > 0:
                variation = max_time / min_time
                lines.append(f"- Wall time varies {variation:.1f}x between fastest and slowest frameworks")
    
    if all('TOK_IN' in data for data in aggregated.values()):
        tokens = [data['TOK_IN'] for data in aggregated.values()]
        if len(tokens) > 1:
            max_tok = max(tokens)
            min_tok = min(tokens)
            if min_tok > 0:
                variation = max_tok / min_tok
                lines.append(f"- Token consumption varies {variation:.1f}x across frameworks")
    
    # Data quality alerts section
    lines.extend(["", "### ⚠️ Data Quality Alerts", ""])
    
    alerts = []
    
    # Check for all-zero metrics
    all_metrics = set()
    for data in aggregated.values():
        all_metrics.update(data.keys())
    
    for metric in sorted(all_metrics):
        values = [data.get(metric, None) for data in aggregated.values()]
        if all(v == 0 for v in values if v is not None):
            if metric not in ['HIT', 'HEU']:  # Expected to be zero
                alerts.append(f"- All frameworks show zero for `{metric}` - verify metric calculation")
    
    # Check for missing data
    for framework, data in aggregated.items():
        expected_metrics = ['AUTR', 'TOK_IN', 'TOK_OUT', 'T_WALL_seconds', 'Q_star', 'AEI']
        missing = [m for m in expected_metrics if m not in data]
        if missing:
            alerts.append(f"- Framework `{framework}` missing metrics: {', '.join(missing)}")
    
    if not alerts:
        lines.append("- No data quality issues detected")
    else:
        lines.extend(alerts)
    
    lines.extend(["", "---", ""])
    
    return lines


def generate_statistical_report(
    frameworks_data: Dict[str, List[Dict[str, float]]],
    output_path: str
) -> None:
    """
    Generate comprehensive statistical report in Markdown format.
    
    Creates a report with:
    - Aggregate statistics table (mean, median, CI for each metric)
    - Kruskal-Wallis test results for each metric
    - Pairwise comparisons with Cliff's delta effect sizes
    - Outlier detection results
    
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
    
    Raises:
        ValueError: If frameworks_data is empty or invalid.
    """
    if not frameworks_data:
        raise ValueError("frameworks_data cannot be empty")
    
    from pathlib import Path
    
    # Start markdown document
    lines = [
        "# Statistical Analysis Report",
        "",
        f"**Generated:** {_get_timestamp()}",
        "",
        f"**Frameworks:** {', '.join(frameworks_data.keys())}",
        "",
        "---",
        ""
    ]
    
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
        "**1. ChatDev** (OpenBMB/ChatDev)",
        "- Multi-agent collaborative framework with role-based AI agents (CEO, CTO, Programmer, Reviewer)",
        "- Waterfall-inspired workflow with distinct phases (design, coding, testing, documentation)",
        "- Repository: `github.com/OpenBMB/ChatDev` (commit: `52edb89`)",
        "",
        "**2. GHSpec** (GitHub Spec-Kit)",
        "- Specification-driven development framework following structured phases",
        "- Four-phase workflow: specification → planning → task breakdown → implementation",
        "- Sequential task execution with full context awareness",
        "- Repository: `github.com/github/spec-kit` (commit: `89f4b0b`)",
        "",
        "**3. BAEs** (Business Autonomous Entities)",
        "- API-based autonomous business entity framework",
        "- Kernel-mediated request processing with specialized entities",
        "- Repository: `github.com/gesad-lab/baes_demo` (commit: `1dd5736`)",
        "",
        "### 📋 Experimental Protocol",
        "",
        "#### **Standardized Task Sequence**",
        "",
        "All frameworks execute the **identical six-step evolution scenario** in strict sequential order:",
        "",
        "1. **Step 1**: Create CRUD application (Student/Course/Teacher with FastAPI + SQLite)",
        "2. **Step 2**: Add enrollment relationship (many-to-many Student-Course)",
        "3. **Step 3**: Add teacher assignment (many-to-one Course-Teacher)",
        "4. **Step 4**: Implement validation and error handling",
        "5. **Step 5**: Add pagination and filtering to all endpoints",
        "6. **Step 6**: Create comprehensive web UI for all operations",
        "",
        "*Natural language commands stored in version-controlled files (`config/prompts/step_1.txt` through `step_6.txt`) ensure perfect reproducibility across runs.*",
        "",
        "#### **Controlled Variables**",
        "",
        "To ensure fair comparison, the following variables are **held constant** across all frameworks:",
        "",
        "**Generative AI Model**:",
        "- Model: `gpt-4o-mini` (OpenAI GPT-4 Omni Mini)",
        "- Temperature: Framework default (typically 0.7-1.0)",
        "- All frameworks use the **same model version** for all steps",
        "",
        "**API Infrastructure**:",
        "- Each framework uses a **dedicated OpenAI API key** (prevents quota conflicts)",
        "- API keys: `OPENAI_API_KEY_BAES`, `OPENAI_API_KEY_CHATDEV`, `OPENAI_API_KEY_GHSPEC`",
        "- Token consumption measured via **OpenAI Usage API** (`/v1/organization/usage/completions`)",
        "- Time-window queries (Unix timestamps) ensure accurate attribution to each execution step",
        "",
        "**Execution Environment**:",
        "- Python 3.11+ isolated virtual environments per framework",
        "- Dependencies installed from framework-specific requirements at pinned commits",
        "- Single-threaded sequential execution (no parallelism)",
        "- 10-minute timeout per step (`step_timeout_seconds: 600`)",
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
        "- Model filter: `models=[\"gpt-4o-mini\"]` (isolates framework's usage)",
        "- Aggregates all API calls within time window (handles multi-request steps)",
        "",
        "**Timing (T_WALL_seconds, ZDI)**:",
        "- Wall-clock time: `time.time()` before/after each step (Python `time` module)",
        "- Zero-Downtime Intervals (ZDI): Idle time between consecutive steps",
        "",
        "**Automation Metrics (AUTR, HIT, HEU)**:",
        "- AUTR: Automated testing rate (test files generated / total steps)",
        "- HIT: Human-in-the-loop count (clarification requests detected in logs)",
        "- HEU: Human effort units (manual interventions required)",
        "",
        "**Quality Metrics (CRUDe, ESR, MC, Q\\*)**:",
        "- CRUDe: CRUD operations implemented (validated via API endpoint inspection)",
        "- ESR: Emerging state rate (successful evolution steps / total steps)",
        "- MC: Model call efficiency (successful calls / total calls)",
        "- Q\\*: Composite quality score (0.4·ESR + 0.3·CRUDe/12 + 0.3·MC)",
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
        "- **Model Consistency**: All frameworks use identical `gpt-4o-mini` model",
        "- **Command Consistency**: Same 6 natural language prompts in identical order",
        "- **Timing Isolation**: Dedicated API keys prevent cross-framework interference",
        "- **Environment Isolation**: Separate virtual environments prevent dependency conflicts",
        "- **Version Pinning**: Exact commit hashes ensure reproducible framework behavior",
        "",
        "**⚠️ Uncontrolled Threats:**",
        "- **Framework-Specific Behavior**: Each framework has unique internal prompts, agent coordination, and retry logic",
        "  - *Mitigation*: Documented in adapter implementations; accepted as inherent framework characteristics",
        "- **Non-Deterministic LLM Responses**: `gpt-4o-mini` may produce different outputs for identical inputs",
        "  - *Mitigation*: Fixed random seed (42) helps but doesn't guarantee full determinism",
        "  - *Statistical Control*: Multiple runs (5-25 per framework) with bootstrap CI to capture variance",
        "- **HITL Detection Accuracy**: Human-in-the-loop counts rely on keyword matching in logs",
        "  - *Limitation*: May miss implicit clarifications or false-positive on debug messages",
        "",
        "#### **External Validity**",
        "",
        "**Generalization Concerns:**",
        "- **Single Task Domain**: CRUD application (Student/Course/Teacher) may not represent all software types",
        "  - *Scope*: Results apply to data-driven web API development; may differ for other domains (ML, systems, mobile)",
        "- **Single Model**: Results specific to `gpt-4o-mini`; other models (GPT-4, Claude, Gemini) may alter rankings",
        "  - *Trade-off*: Chose `gpt-4o-mini` for cost and speed; representative of practical usage",
        "- **Framework Versions**: Pinned commits may not reflect latest improvements",
        "  - *Justification*: Ensures reproducibility; future studies can test newer versions",
        "",
        "#### **Construct Validity**",
        "",
        "**Metric Interpretation:**",
        "- **Token Usage (TOK_IN/TOK_OUT)**: Measures cost, not necessarily code quality",
        "  - *Caveat*: Lower tokens ≠ better software; high-quality output may justify higher consumption",
        "- **Quality Metrics (Q\\*, ESR, CRUDe)**: May show zero values due to:",
        "  - Missing validation logic in current implementation",
        "  - Framework output formats not matching expected patterns",
        "  - *Action Required*: Verify metric calculation before quality-based decisions (see Data Quality Alerts)",
        "- **AUTR (Automated Testing Rate)**: All frameworks achieve 100% but test quality not measured",
        "  - *Limitation*: Presence of test files ≠ comprehensive test coverage",
        "",
        "#### **Conclusion Validity**",
        "",
        "**Statistical Rigor:**",
        "- **Non-Parametric Tests**: Kruskal-Wallis and Dunn-Šidák avoid normality assumptions",
        "- **Effect Sizes**: Cliff's delta quantifies practical significance beyond p-values",
        "- **Bootstrap CI**: 95% confidence intervals with 10,000 resamples for stable estimates",
        "- **Small Sample Awareness**: Current results (5 runs) show large CI widths; p-values > 0.05 expected",
        "  - *Stopping Rule*: Experiment continues until CI half-width ≤ 10% of mean (25 runs max)",
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
        "- Analysis Scripts: `src/analysis/statistics.py` (this report generator), `src/analysis/visualizations.py`",
        "",
        "**Commit Hashes**:",
        "- ChatDev: `52edb89997b4312ad27d8c54584d0a6c59940135`",
        "- GHSpec: `89f4b0b38a42996376c0f083d47281a4c9196761`",
        "- BAEs: `1dd573633a98b8baa636c200bc1684cec7a8179f`",
        "",
        "---",
        ""
    ])
    
    # Add Metric Glossary
    lines.extend([
        "## Metric Definitions",
        "",
        "| Metric | Full Name | Description | Range | Ideal Value |",
        "|--------|-----------|-------------|-------|-------------|",
        "| **AUTR** | Automated User Testing Rate | % of tests auto-generated | 0-1 | Higher ↑ |",
        "| **AEI** | Automation Efficiency Index | Quality per token consumed | 0-∞ | Higher ↑ |",
        "| **Q\\*** | Quality Star | Composite quality score | 0-1 | Higher ↑ |",
        "| **ESR** | Emerging State Rate | % steps with successful evolution | 0-1 | Higher ↑ |",
        "| **CRUDe** | CRUD Evolution Coverage | CRUD operations implemented | 0-12 | Higher ↑ |",
        "| **MC** | Model Call Efficiency | Efficiency of LLM calls | 0-1 | Higher ↑ |",
        "| **TOK_IN** | Input Tokens | Total tokens sent to LLM | 0-∞ | Lower ↓ |",
        "| **TOK_OUT** | Output Tokens | Total tokens received from LLM | 0-∞ | Lower ↓ |",
        "| **T_WALL_seconds** | Wall Clock Time | Total elapsed time (seconds) | 0-∞ | Lower ↓ |",
        "| **ZDI** | Zero-Downtime Intervals | Idle time between steps (seconds) | 0-∞ | Lower ↓ |",
        "| **HIT** | Human-in-the-Loop Count | Manual interventions needed | 0-∞ | Lower ↓ |",
        "| **HEU** | Human Effort Units | Total manual effort required | 0-∞ | Lower ↓ |",
        "| **UTT** | User Task Total | Number of evolution steps | Fixed | 6 |",
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
        "**Bootstrap Confidence Intervals (CI)**",
        "- Estimates the range where true mean likely falls (95% confidence)",
        "- Example: `30,772 [2,503, 59,040]` means we're 95% confident the true mean is between 2,503 and 59,040",
        "- Wider intervals = more uncertainty; narrower intervals = more precise estimates",
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
    lines.extend(_generate_executive_summary(frameworks_data))
    
    # Collect all metrics
    all_metrics = set()
    for runs in frameworks_data.values():
        for run in runs:
            all_metrics.update(run.keys())
    
    all_metrics = sorted(all_metrics)
    
    # Section 1: Aggregate Statistics
    lines.extend([
        "## 1. Aggregate Statistics",
        "",
        "### Mean Values with 95% Bootstrap CI",
        "",
        "*Note: Token values shown with thousands separator; time in seconds (minutes if >60s)*",
        "",
        "**Performance Indicators:** 🟢 Best | 🟡 Middle | 🔴 Worst",
        ""
    ])
    
    # Table header
    header = "| Framework | " + " | ".join(all_metrics) + " |"
    separator = "|-----------|" + "|".join(["-" * 12 for _ in all_metrics]) + "|"
    lines.extend([header, separator])
    
    # First pass: collect all mean values for each metric to determine indicators
    framework_means = {}
    for framework, runs in frameworks_data.items():
        aggregated = bootstrap_aggregate_metrics(runs)
        framework_means[framework] = aggregated
    
    # Collect all values per metric for comparison
    metric_values = {}
    for metric in all_metrics:
        metric_values[metric] = []
        for framework in frameworks_data.keys():
            if metric in framework_means[framework]:
                metric_values[metric].append(framework_means[framework][metric]['mean'])
    
    # Table rows with indicators
    for framework in frameworks_data.keys():
        aggregated = framework_means[framework]
        row = f"| {framework} |"
        
        for metric in all_metrics:
            if metric in aggregated:
                stats = aggregated[metric]
                mean = stats['mean']
                ci_lower = stats['ci_lower']
                ci_upper = stats['ci_upper']
                
                # Format values with units
                formatted_mean = _format_metric_value(metric, mean, include_units=False)
                formatted_ci = _format_confidence_interval(ci_lower, ci_upper, metric)
                
                # Add performance indicator
                indicator = _get_performance_indicator(metric, mean, metric_values[metric])
                
                row += f" {formatted_mean} {formatted_ci}{indicator} |"
            else:
                row += " N/A |"
        
        lines.append(row)
    
    lines.extend(["", ""])
    
    # Section 2: Relative Performance
    relative_performance_lines = _generate_relative_performance(framework_means, all_metrics)
    lines.extend(relative_performance_lines)
    
    # Section 3: Kruskal-Wallis Tests
    lines.extend([
        "## 3. Kruskal-Wallis H-Tests",
        "",
        "Testing for significant differences across all frameworks.",
        "",
        "| Metric | H | p-value | Significant | Groups | N |",
        "|--------|---|---------|-------------|--------|---|"
    ])
    
    for metric in all_metrics:
        # Collect metric values by framework
        groups = {}
        for framework, runs in frameworks_data.items():
            groups[framework] = [run[metric] for run in runs if metric in run]
        
        if all(len(vals) > 0 for vals in groups.values()):
            result = kruskal_wallis_test(groups)
            sig = "✓ Yes" if result['significant'] else "✗ No"
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
    
    # Section 4: Pairwise Comparisons
    lines.extend([
        "## 4. Pairwise Comparisons",
        "",
        "Dunn-Šidák corrected pairwise tests with Cliff's delta effect sizes.",
        ""
    ])
    
    for metric in all_metrics:
        # Collect metric values by framework
        groups = {}
        for framework, runs in frameworks_data.items():
            groups[framework] = [run[metric] for run in runs if metric in run]
        
        if all(len(vals) > 0 for vals in groups.values()) and len(groups) >= 2:
            lines.append(f"### {metric}")
            lines.append("")
            lines.append("| Comparison | p-value | Significant | Cliff's δ | Effect Size |")
            lines.append("|------------|---------|-------------|-----------|-------------|")
            
            comparisons = pairwise_comparisons(groups)
            
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
    
    # Section 5: Outlier Detection
    lines.extend([
        "## 5. Outlier Detection",
        "",
        "Values > 3σ from median (per framework, per metric).",
        ""
    ])
    
    outliers_found = False
    for framework, runs in frameworks_data.items():
        framework_outliers = []
        
        for metric in all_metrics:
            values = [run[metric] for run in runs if metric in run]
            if len(values) >= 3:
                outlier_indices, outlier_values = identify_outliers(values)
                
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
    
    # Section 5: Composite Scores
    lines.extend([
        "## 5. Composite Scores",
        "",
        "**Q*** = 0.4·ESR + 0.3·(CRUDe/12) + 0.3·MC",
        "",
        "**AEI** = AUTR / log(1 + TOK_IN)",
        "",
        "| Framework | Q* Mean | Q* CI | AEI Mean | AEI CI |",
        "|-----------|---------|-------|----------|--------|"
    ])
    
    for framework, runs in frameworks_data.items():
        # Compute composite scores for each run
        q_star_values = []
        aei_values = []
        
        for run in runs:
            try:
                scores = compute_composite_scores(run)
                q_star_values.append(scores['Q*'])
                aei_values.append(scores['AEI'])
            except ValueError:
                # Missing required metrics, skip
                continue
        
        if q_star_values and aei_values:
            q_agg = bootstrap_aggregate_metrics([{'Q*': v} for v in q_star_values])
            aei_agg = bootstrap_aggregate_metrics([{'AEI': v} for v in aei_values])
            
            q_mean = _format_metric_value('Q*', q_agg['Q*']['mean'], include_units=False)
            q_ci = _format_confidence_interval(q_agg['Q*']['ci_lower'], q_agg['Q*']['ci_upper'], 'Q*')
            aei_mean = _format_metric_value('AEI', aei_agg['AEI']['mean'], include_units=False)
            aei_ci = _format_confidence_interval(aei_agg['AEI']['ci_lower'], aei_agg['AEI']['ci_upper'], 'AEI')
            
            lines.append(
                f"| {framework} | {q_mean} | {q_ci} | {aei_mean} | {aei_ci} |"
            )
        else:
            lines.append(f"| {framework} | N/A | N/A | N/A | N/A |")
    
    lines.extend(["", ""])
    
    # Section 6: Visual Summary
    lines.extend([
        "## 6. Visual Summary",
        "",
        "### Key Visualizations",
        "",
        "The following charts provide visual insights into framework performance:",
        "",
        "**Radar Chart** - Multi-dimensional comparison across 6 key metrics",
        "",
        "![Radar Chart](radar_chart.svg)",
        "",
        "**Pareto Plot** - Quality vs Cost trade-off analysis",
        "",
        "![Pareto Plot](pareto_plot.svg)",
        "",
        "**Timeline Chart** - CRUD evolution over execution steps",
        "",
        "![Timeline Chart](timeline_chart.svg)",
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
    
    if all('AEI' in data for data in simple_aggregated.values()):
        best_efficiency = max(simple_aggregated.items(), key=lambda x: x[1].get('AEI', 0))
        recommendations.append(
            f"**⚙️ Efficiency Leader**: **{best_efficiency[0]}** delivers the best quality-per-token ratio (AEI = {best_efficiency[1]['AEI']:.3f}), "
            f"making it ideal for balancing quality and cost."
        )
    
    if all('AUTR' in data for data in simple_aggregated.values()):
        autr_values = [data['AUTR'] for data in simple_aggregated.values()]
        if all(v == 1.0 for v in autr_values):
            recommendations.append(
                "**🤖 Automation**: All frameworks achieve perfect test automation (AUTR = 1.0) - "
                "automation quality is not a differentiating factor."
            )
    
    # Check for quality concerns
    quality_metrics = ['Q_star', 'ESR', 'CRUDe', 'MC']
    zero_metrics = []
    for metric in quality_metrics:
        if all(metric in data and data[metric] == 0 for data in simple_aggregated.values()):
            zero_metrics.append(metric)
    
    if zero_metrics:
        recommendations.append(
            f"**⚠️ Data Quality Alert**: Metrics {', '.join(zero_metrics)} show zero values across all frameworks. "
            f"Verify metric calculation before making quality-based decisions."
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
    
    if all('AEI' in data for data in simple_aggregated.values()):
        best_efficiency = max(simple_aggregated.items(), key=lambda x: x[1].get('AEI', 0))
        lines.append(f"| Balanced quality/cost | {best_efficiency[0]} | Best efficiency index (AEI) |")
    
    lines.extend(["", ""])
    
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


def _get_timestamp() -> str:
    """Get current UTC timestamp in ISO format."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
