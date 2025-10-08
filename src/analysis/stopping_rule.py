"""
Stopping rule implementation for multi-framework experiments.

Implements bootstrap confidence intervals to determine convergence.
"""

import random
from typing import List, Dict, Any, Tuple
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Stopping rule configuration
MIN_RUNS = 5
MAX_RUNS = 25
CI_LEVEL = 0.95
HALF_WIDTH_THRESHOLD = 0.10  # 10% of mean
BOOTSTRAP_SAMPLES = 10000

# Metrics to check for convergence
CONVERGENCE_METRICS = ['AUTR', 'TOK_IN', 'T_WALL', 'CRUDe', 'ESR', 'MC']


def bootstrap_ci(data: List[float], n_bootstrap: int = BOOTSTRAP_SAMPLES, 
                 ci_level: float = CI_LEVEL) -> Tuple[float, float, float]:
    """
    Compute bootstrap confidence interval for the mean.
    
    Uses percentile method with resampling.
    
    Args:
        data: List of observed values
        n_bootstrap: Number of bootstrap resamples (default 10,000)
        ci_level: Confidence level (default 0.95 for 95% CI)
        
    Returns:
        Tuple of (mean, lower_bound, upper_bound)
    """
    if not data:
        return 0.0, 0.0, 0.0
        
    n = len(data)
    bootstrap_means = []
    
    # Generate bootstrap samples
    for _ in range(n_bootstrap):
        # Resample with replacement
        sample = random.choices(data, k=n)
        bootstrap_means.append(sum(sample) / n)
    
    # Sort bootstrap means
    bootstrap_means.sort()
    
    # Compute percentiles
    alpha = 1 - ci_level
    lower_idx = int(n_bootstrap * (alpha / 2))
    upper_idx = int(n_bootstrap * (1 - alpha / 2))
    
    mean = sum(data) / n
    lower = bootstrap_means[lower_idx]
    upper = bootstrap_means[upper_idx]
    
    return mean, lower, upper


def check_convergence(
    metrics_history: List[Dict[str, float]],
    framework: str,
    min_runs: int = MIN_RUNS,
    max_runs: int = MAX_RUNS,
    half_width_threshold: float = HALF_WIDTH_THRESHOLD
) -> Dict[str, Any]:
    """
    Check if stopping rule is satisfied for a framework.
    
    Stopping conditions:
    1. Minimum runs (default 5) must be completed
    2. For each key metric, 95% CI half-width ≤ 10% of mean
    3. Stop unconditionally at maximum runs (default 25)
    
    Args:
        metrics_history: List of metric dictionaries from completed runs
        framework: Framework name for logging
        min_runs: Minimum number of runs required
        max_runs: Maximum number of runs allowed
        half_width_threshold: Max allowed half-width as fraction of mean
        
    Returns:
        Dictionary with convergence status:
        {
            'should_stop': bool,
            'reason': str,
            'runs_completed': int,
            'convergence_details': {
                'AUTR': {'converged': bool, 'mean': float, 'ci': [lower, upper], 
                         'half_width_pct': float},
                ...
            }
        }
    """
    n_runs = len(metrics_history)
    
    # Check minimum runs
    if n_runs < min_runs:
        return {
            'should_stop': False,
            'reason': f'Insufficient runs ({n_runs}/{min_runs})',
            'runs_completed': n_runs,
            'convergence_details': {}
        }
    
    # Check maximum runs
    if n_runs >= max_runs:
        logger.info("Maximum runs reached",
                   extra={'metadata': {'framework': framework, 'runs': n_runs}})
        return {
            'should_stop': True,
            'reason': f'Maximum runs reached ({n_runs}/{max_runs})',
            'runs_completed': n_runs,
            'convergence_details': {}
        }
    
    # Check convergence for each metric
    convergence_details = {}
    all_converged = True
    
    for metric in CONVERGENCE_METRICS:
        # Extract metric values from history
        values = []
        for run_metrics in metrics_history:
            if metric in run_metrics:
                values.append(run_metrics[metric])
        
        if not values:
            logger.warning(f"Metric {metric} not found in history",
                         extra={'metadata': {'framework': framework}})
            all_converged = False
            continue
        
        # Compute bootstrap CI
        mean, lower, upper = bootstrap_ci(values)
        
        # Compute half-width as percentage of mean
        half_width = (upper - lower) / 2
        if mean > 0:
            half_width_pct = half_width / mean
        else:
            half_width_pct = float('inf')
        
        converged = half_width_pct <= half_width_threshold
        
        convergence_details[metric] = {
            'converged': converged,
            'mean': mean,
            'ci': [lower, upper],
            'half_width': half_width,
            'half_width_pct': half_width_pct,
            'n_samples': len(values)
        }
        
        if not converged:
            all_converged = False
            logger.info(f"Metric {metric} not yet converged",
                       extra={'metadata': {
                           'framework': framework,
                           'half_width_pct': half_width_pct,
                           'threshold': half_width_threshold
                       }})
    
    if all_converged:
        logger.info("All metrics converged",
                   extra={'metadata': {'framework': framework, 'runs': n_runs}})
        return {
            'should_stop': True,
            'reason': f'Convergence achieved for all metrics ({n_runs} runs)',
            'runs_completed': n_runs,
            'convergence_details': convergence_details
        }
    else:
        return {
            'should_stop': False,
            'reason': 'Not all metrics converged',
            'runs_completed': n_runs,
            'convergence_details': convergence_details
        }


def get_convergence_summary(convergence_result: Dict[str, Any]) -> str:
    """
    Generate human-readable convergence summary.
    
    Args:
        convergence_result: Result from check_convergence()
        
    Returns:
        Formatted summary string
    """
    lines = [
        f"Runs completed: {convergence_result['runs_completed']}",
        f"Should stop: {convergence_result['should_stop']}",
        f"Reason: {convergence_result['reason']}"
    ]
    
    if convergence_result['convergence_details']:
        lines.append("\nMetric convergence:")
        for metric, details in convergence_result['convergence_details'].items():
            status = "✓" if details['converged'] else "✗"
            lines.append(
                f"  {status} {metric}: mean={details['mean']:.3f}, "
                f"CI=[{details['ci'][0]:.3f}, {details['ci'][1]:.3f}], "
                f"half-width={details['half_width_pct']*100:.1f}%"
            )
    
    return "\n".join(lines)
