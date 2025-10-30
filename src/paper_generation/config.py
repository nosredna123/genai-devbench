"""
Statistical analysis configuration.

This module centralizes thresholds and parameters used in statistical analysis,
making them adjustable and well-documented.

Feature 013: Statistical Analysis Enhancements
"""
from dataclasses import dataclass


@dataclass
class StatisticalConfig:
    """
    Configuration for statistical analysis thresholds and parameters.
    
    Attributes:
        variance_threshold: Minimum variance for meaningful analysis (default: 0.01)
        iqr_threshold: Minimum IQR for box plot rendering (default: 0.01)
        alpha: Significance level for hypothesis tests (default: 0.05)
        normality_sample_size_threshold: Minimum samples for Shapiro-Wilk test (default: 3)
        bootstrap_iterations: Number of bootstrap iterations for CI estimation (default: 10000)
        bootstrap_confidence_level: Confidence level for bootstrap CIs (default: 0.95)
        min_group_size: Minimum group size for valid comparisons (default: 2)
    """
    
    # Variance quality thresholds
    variance_threshold: float = 0.01
    iqr_threshold: float = 0.01
    
    # Hypothesis testing parameters
    alpha: float = 0.05
    normality_sample_size_threshold: int = 3
    
    # Bootstrap parameters
    bootstrap_iterations: int = 10000
    bootstrap_confidence_level: float = 0.95
    
    # Sample size requirements
    min_group_size: int = 2
    
    def __post_init__(self):
        """Validate configuration parameters."""
        if not 0 < self.alpha < 1:
            raise ValueError(f"alpha must be between 0 and 1, got {self.alpha}")
        if self.variance_threshold < 0:
            raise ValueError(f"variance_threshold must be non-negative, got {self.variance_threshold}")
        if self.iqr_threshold < 0:
            raise ValueError(f"iqr_threshold must be non-negative, got {self.iqr_threshold}")
        if self.bootstrap_iterations < 1000:
            raise ValueError(f"bootstrap_iterations should be at least 1000, got {self.bootstrap_iterations}")
        if not 0 < self.bootstrap_confidence_level < 1:
            raise ValueError(
                f"bootstrap_confidence_level must be between 0 and 1, got {self.bootstrap_confidence_level}"
            )
        if self.min_group_size < 2:
            raise ValueError(f"min_group_size must be at least 2, got {self.min_group_size}")
