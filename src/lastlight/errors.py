"""Public exception hierarchy for LastLight library consumers."""


class LastLightError(Exception):
    """Base class for errors raised by the public LastLight API."""


class ConfigurationError(LastLightError, ValueError):
    """Raised when the library is configured with an unsupported option."""


class PackError(LastLightError):
    """Base class for knowledge-pack errors."""


class PackValidationError(PackError):
    """Raised when a knowledge pack fails validation."""
