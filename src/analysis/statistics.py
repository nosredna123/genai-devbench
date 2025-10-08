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
        ""
    ])
    
    # Table header
    header = "| Framework | " + " | ".join(all_metrics) + " |"
    separator = "|-----------|" + "|".join(["-" * 12 for _ in all_metrics]) + "|"
    lines.extend([header, separator])
    
    # Table rows
    for framework, runs in frameworks_data.items():
        aggregated = bootstrap_aggregate_metrics(runs)
        row = f"| {framework} |"
        
        for metric in all_metrics:
            if metric in aggregated:
                stats = aggregated[metric]
                mean = stats['mean']
                ci_lower = stats['ci_lower']
                ci_upper = stats['ci_upper']
                row += f" {mean:.3f} [{ci_lower:.3f}, {ci_upper:.3f}] |"
            else:
                row += " N/A |"
        
        lines.append(row)
    
    lines.extend(["", ""])
    
    # Section 2: Kruskal-Wallis Tests
    lines.extend([
        "## 2. Kruskal-Wallis H-Tests",
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
        else:
            lines.append(f"| {metric} | N/A | N/A | N/A | N/A | N/A |")
    
    lines.extend(["", ""])
    
    # Section 3: Pairwise Comparisons
    lines.extend([
        "## 3. Pairwise Comparisons",
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
            
            for comp in comparisons:
                pair = f"{comp['group1']} vs {comp['group2']}"
                sig = "✓" if comp['significant'] else "✗"
                delta = comp['cliff_delta']
                effect = comp['effect_size']
                
                lines.append(
                    f"| {pair} | {comp['p_value']:.4f} | {sig} | "
                    f"{delta:.3f} | {effect} |"
                )
            
            lines.extend(["", ""])
    
    # Section 4: Outlier Detection
    lines.extend([
        "## 4. Outlier Detection",
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
            
            q_mean = q_agg['Q*']['mean']
            q_ci = f"[{q_agg['Q*']['ci_lower']:.3f}, {q_agg['Q*']['ci_upper']:.3f}]"
            aei_mean = aei_agg['AEI']['mean']
            aei_ci = f"[{aei_agg['AEI']['ci_lower']:.3f}, {aei_agg['AEI']['ci_upper']:.3f}]"
            
            lines.append(
                f"| {framework} | {q_mean:.3f} | {q_ci} | {aei_mean:.3f} | {aei_ci} |"
            )
        else:
            lines.append(f"| {framework} | N/A | N/A | N/A | N/A |")
    
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
