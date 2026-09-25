"""LastLight: offline intelligence under extreme constraints."""

from .api import LastLight
from .errors import ConfigurationError, LastLightError, PackError, PackValidationError
from .types import (
    AdaptiveMode,
    PackInfo,
    PackProvenance,
    PackValidation,
    QueryResult,
    RefusalReason,
    RetrievalMetadata,
    RetrievalStrategyName,
    SourceDocument,
    SourceResult,
)

__version__ = "0.1.4"

__all__ = [
    "AdaptiveMode",
    "ConfigurationError",
    "LastLight",
    "LastLightError",
    "PackError",
    "PackInfo",
    "PackProvenance",
    "PackValidation",
    "PackValidationError",
    "QueryResult",
    "RefusalReason",
    "RetrievalMetadata",
    "RetrievalStrategyName",
    "SourceDocument",
    "SourceResult",
    "__version__",
]
