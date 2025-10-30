"""
Statistical Helper Functions for Paper Generation

Provides common statistical utilities including bootstrap confidence intervals,
effect size calculations, and result interpretation.
"""

from typing import Tuple, List
import numpy as np
from scipy import stats


def bootstrap_ci(
    data: List[float],
    statistic_fn=np.median,
    confidence_level: float = 0.95,
    n_iterations: int = 10000,
    random_seed: int = 42
) -> Tuple[float, float, float]:
    """
    Calculate bootstrap confidence interval for a statistic.
    
    Uses percentile method with fixed random seed for reproducibility.
    
    Args:
        data: Sample data
        statistic_fn: Function to calculate statistic (default: median)
        confidence_level: Confidence level (default: 0.95 for 95% CI)
        n_iterations: Number of bootstrap samples (default: 10,000)
        random_seed: Random seed for reproducibility (default: 42)
    
    Returns:
        Tuple of (statistic, lower_bound, upper_bound)
    
    Example:
        >>> data = [1.2, 2.3, 3.1, 2.8, 4.2]
        >>> median, lower, upper = bootstrap_ci(data)
        >>> print(f"Median: {median:.2f} [{lower:.2f}, {upper:.2f}]")
    """
    if len(data) == 0:
        raise ValueError("Cannot calculate bootstrap CI for empty data")
    
    # Calculate observed statistic
    observed = statistic_fn(data)
    
    # Generate bootstrap samples
    rng = np.random.RandomState(random_seed)
    bootstrap_stats = []
    
    for _ in range(n_iterations):
        sample = rng.choice(data, size=len(data), replace=True)
        bootstrap_stats.append(statistic_fn(sample))
    
    # Calculate percentile-based CI
    alpha = 1 - confidence_level
    lower_percentile = (alpha / 2) * 100
    upper_percentile = (1 - alpha / 2) * 100
    
    lower_bound = np.percentile(bootstrap_stats, lower_percentile)
    upper_bound = np.percentile(bootstrap_stats, upper_percentile)
    
    return observed, lower_bound, upper_bound


def cohens_d(group1: List[float], group2: List[float]) -> float:
    """
    Calculate Cohen's d effect size for two groups.
    
    Uses pooled standard deviation. Positive values indicate group1 > group2.
    
    Args:
        group1: First group data
        group2: Second group data
    
    Returns:
        Cohen's d effect size
    
    Effect size interpretation (Cohen, 1988):
        - |d| < 0.2: negligible
        - 0.2 ≤ |d| < 0.5: small
        - 0.5 ≤ |d| < 0.8: medium
        - |d| ≥ 0.8: large
    
    Example:
        >>> group1 = [5.2, 6.1, 5.8, 6.3]
        >>> group2 = [3.1, 3.8, 3.5, 4.2]
        >>> d = cohens_d(group1, group2)
        >>> print(f"Effect size: {d:.3f}")
    """
    if len(group1) == 0 or len(group2) == 0:
        raise ValueError("Cannot calculate Cohen's d for empty groups")
    
    n1, n2 = len(group1), len(group2)
    mean1, mean2 = np.mean(group1), np.mean(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    # Avoid division by zero
    if pooled_std == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_std


def cliffs_delta(group1: List[float], group2: List[float]) -> float:
    """
    Calculate Cliff's Delta effect size (non-parametric).
    
    Measures probability that a random value from group1 is greater than
    a random value from group2, adjusted for ties.
    
    Args:
        group1: First group data
        group2: Second group data
    
    Returns:
        Cliff's Delta effect size (range: -1 to +1)
    
    Effect size interpretation (Romano et al., 2006):
        - |δ| < 0.147: negligible
        - 0.147 ≤ |δ| < 0.33: small
        - 0.33 ≤ |δ| < 0.474: medium
        - |δ| ≥ 0.474: large
    
    Example:
        >>> group1 = [5.2, 6.1, 5.8, 6.3]
        >>> group2 = [3.1, 3.8, 3.5, 4.2]
        >>> delta = cliffs_delta(group1, group2)
        >>> print(f"Cliff's Delta: {delta:.3f}")
    """
    if len(group1) == 0 or len(group2) == 0:
        raise ValueError("Cannot calculate Cliff's Delta for empty groups")
    
    # Count comparisons
    greater = 0
    less = 0
    
    for x in group1:
        for y in group2:
            if x > y:
                greater += 1
            elif x < y:
                less += 1
            # Ties don't contribute
    
    total = len(group1) * len(group2)
    
    # Avoid division by zero
    if total == 0:
        return 0.0
    
    return (greater - less) / total


def interpret_effect_size(effect_size: float, measure: str = "cohens_d") -> str:
    """
    Interpret effect size magnitude according to conventional thresholds.
    
    Args:
        effect_size: Calculated effect size value
        measure: Type of effect size ("cohens_d" or "cliffs_delta")
    
    Returns:
        Interpretation string: "negligible", "small", "medium", or "large"
    
    References:
        - Cohen's d: Cohen, J. (1988). Statistical Power Analysis for the 
          Behavioral Sciences (2nd ed.). Routledge.
        - Cliff's Delta: Romano, J., Kromrey, J. D., Coraggio, J., & Skowronek, J. 
          (2006). Appropriate statistics for ordinal level data: Should we really 
          be using t-test and Cohen's d for evaluating group differences on the 
          NSSE and other surveys? In annual meeting of the Florida Association 
          of Institutional Research (Vol. 177).
    
    Example:
        >>> d = cohens_d([5.2, 6.1], [3.1, 3.8])
        >>> print(interpret_effect_size(d, "cohens_d"))
        'large'
    """
    abs_effect = abs(effect_size)
    
    if measure == "cohens_d":
        # Cohen (1988) thresholds
        if abs_effect < 0.2:
            return "negligible"
        elif abs_effect < 0.5:
            return "small"
        elif abs_effect < 0.8:
            return "medium"
        else:
            return "large"
    
    elif measure == "cliffs_delta":
        # Romano et al. (2006) thresholds
        if abs_effect < 0.147:
            return "negligible"
        elif abs_effect < 0.33:
            return "small"
        elif abs_effect < 0.474:
            return "medium"
        else:
            return "large"
    
    else:
        raise ValueError(f"Unknown effect size measure: {measure}. "
                        f"Use 'cohens_d' or 'cliffs_delta'")


def format_pvalue(p: float, precision: int = 3) -> str:
    """
    Format p-value according to APA 7th edition guidelines.
    
    Args:
        p: P-value to format (0.0 to 1.0)
        precision: Number of decimal places (default 3)
    
    Returns:
        Formatted string following APA conventions
    
    Rules:
        - p < 0.001: Report as "p < 0.001"
        - p ≥ 0.001: Report as "p = 0.XXX" (3 decimals, include leading zero)
        - p = 0.050: Report as "p = 0.050" (not "p = 0.05")
        - Always use equals sign or less-than, never "p = 0.000" or "p = 0.0000"
    
    Examples:
        >>> format_pvalue(0.0000023)
        'p < 0.001'
        >>> format_pvalue(0.0234)
        'p = 0.023'
        >>> format_pvalue(0.05)
        'p = 0.050'
        >>> format_pvalue(0.234)
        'p = 0.234'
    
    Reference:
        American Psychological Association. (2020). Publication Manual of the 
        American Psychological Association (7th ed.).
    """
    if p < 0.001:
        return "p < 0.001"
    elif p >= 1.0:
        return "p = 1.000"
    else:
        return f"p = {p:.{precision}f}"


def validate_ci(point_estimate: float, ci_lower: float, ci_upper: float) -> bool:
    """
    Validate that a confidence interval contains its point estimate.
    
    Args:
        point_estimate: The calculated statistic value
        ci_lower: Lower bound of confidence interval
        ci_upper: Upper bound of confidence interval
    
    Returns:
        True if CI is valid (contains point estimate), False otherwise
    
    Example:
        >>> # Valid CI
        >>> validate_ci(2.5, 2.0, 3.0)
        True
        >>> # Invalid CI (point estimate outside bounds)
        >>> validate_ci(2.5, 3.0, 4.0)
        False
    
    Note:
        A confidence interval should always contain its point estimate. If this
        validation fails, it indicates a bug in the bootstrap resampling logic
        (e.g., resampling from combined array instead of independent groups).
    """
    return ci_lower <= point_estimate <= ci_upper
