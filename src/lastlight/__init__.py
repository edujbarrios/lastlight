"""LastLight: offline intelligence under extreme constraints."""

from .api import LastLight
from .types import QueryResult, RetrievalMetadata, SourceResult

__version__ = "0.1.0"

__all__ = [
    "LastLight",
    "QueryResult",
    "RetrievalMetadata",
    "SourceResult",
    "__version__",
]
