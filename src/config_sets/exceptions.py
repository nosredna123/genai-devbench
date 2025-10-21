"""Custom exceptions for config set management."""


class ConfigSetError(Exception):
    """Base exception for config set errors."""
    pass


class ConfigSetNotFoundError(ConfigSetError):
    """Raised when config set doesn't exist."""
    pass


class ConfigSetValidationError(ConfigSetError):
    """Raised when config set validation fails."""
    pass
