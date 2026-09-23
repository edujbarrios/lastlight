"""LastLight: offline intelligence under extreme constraints."""

from .api import LastLight
from .errors import ConfigurationError, LastLightError, PackError, PackValidationError
from .types import QueryResult, RetrievalMetadata, SourceDocument, SourceResult

__version__ = "0.1.1"

__all__ = [
    "ConfigurationError",
    "LastLight",
    "LastLightError",
    "PackError",
    "PackValidationError",
    "QueryResult",
    "RetrievalMetadata",
    "SourceDocument",
    "SourceResult",
    "__version__",
]
