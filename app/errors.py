"""Shared application error types."""


class ApplicationError(Exception):
    """Base class for application-specific errors."""


class ConfigurationError(ApplicationError):
    """Raised when environment or local paths are invalid."""


class NormalizationError(ApplicationError):
    """Raised when raw sample artifacts cannot be normalized safely."""