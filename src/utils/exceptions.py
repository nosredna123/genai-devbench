"""Custom exceptions for BAEs experiment framework.

This module defines exception classes for configuration validation,
metric validation, and migration errors.
"""


class ConfigValidationError(Exception):
    """Raised when configuration validation fails.
    
    This error indicates that required configuration keys are missing,
    have invalid values, or do not meet validation criteria.
    
    Examples:
        - Missing required key in experiment.yaml
        - Invalid value type for a configuration field
        - Configuration value is None when a value is required
    """


class ConfigMigrationError(Exception):
    """Raised when old configuration format is detected.
    
    This error indicates that the configuration file uses the deprecated
    3-subsection format (reliable_metrics, derived_metrics, excluded_metrics)
    instead of the new unified metrics section.
    
    The error message should include migration instructions and point to
    the CONFIG_MIGRATION_GUIDE.md documentation.
    """


class MetricsValidationError(Exception):
    """Raised when metrics validation fails.
    
    This error indicates that metrics found in run data do not match the
    metrics defined in the configuration, or other metric-related validation
    issues.
    
    Examples:
        - Metric key appears in metrics.json but not in experiment.yaml
        - Required metric is missing from run data
        - Metric data type does not match expected type
    """
