"""
Custom exceptions for step configuration management.
"""


class StepConfigError(Exception):
    """Base exception for step configuration errors."""
    pass


class StepValidationError(StepConfigError):
    """Raised when step configuration validation fails."""
    pass
