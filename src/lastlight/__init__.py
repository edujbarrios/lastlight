"""LastLight: offline intelligence under extreme constraints."""

from .api import LastLight
from .errors import ConfigurationError, LastLightError, PackError, PackValidationError
from .types import (
    PackInfo,
    PackProvenance,
    PackValidation,
    QueryResult,
    RetrievalMetadata,
    SourceDocument,
    SourceResult,
)

__version__ = "0.1.1"

__all__ = [
    "ConfigurationError",
    "LastLight",
    "LastLightError",
    "PackError",
    "PackInfo",
    "PackProvenance",
    "PackValidation",
    "PackValidationError",
    "QueryResult",
    "RetrievalMetadata",
    "SourceDocument",
    "SourceResult",
    "__version__",
]
