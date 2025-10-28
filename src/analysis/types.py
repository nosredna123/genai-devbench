"""Type definitions for analysis module.

This module defines dataclasses and type aliases used throughout
the analysis module for report generation and metrics discovery.
"""

from dataclasses import dataclass
from typing import Set


@dataclass
class MetricsDiscoveryResult:
    """Result of auto-discovering metrics from run data.
    
    This dataclass holds the partitioned sets of metrics after scanning
    experiment run files to determine which metrics have actual collected
    data versus which are defined but unmeasured.
    
    Attributes:
        metrics_with_data: Set of metric keys that have collected values
            in at least one run file
        metrics_without_data: Set of metric keys defined in config but
            with no collected data in any run file
        unknown_metrics: Set of metric keys found in run data but not
            defined in the configuration (should be empty after validation)
        run_count: Total number of run files scanned during discovery
    
    Example:
        >>> result = MetricsDiscoveryResult(
        ...     metrics_with_data={'TOK_IN', 'TOK_OUT', 'COST_USD'},
        ...     metrics_without_data={'AUTR', 'CODE_QUAL'},
        ...     unknown_metrics=set(),
        ...     run_count=15
        ... )
        >>> print(f"Measured: {len(result.metrics_with_data)}")
        Measured: 3
    """
    metrics_with_data: Set[str]
    metrics_without_data: Set[str]
    unknown_metrics: Set[str]
    run_count: int
