"""LastLight: offline intelligence under extreme constraints."""

from .api import LastLight
from .errors import ConfigurationError, LastLightError, PackError, PackValidationError
from .types import (
    AdaptiveMode,
    DecisionMetadata,
    PackInfo,
    PackProvenance,
    PackValidation,
    QueryExplanation,
    QueryResult,
    RefusalReason,
    RetrievalMetadata,
    RetrievalStrategyName,
    SourceDocument,
    SourceResult,
)

__version__ = "0.2.0"

__all__ = [
    "AdaptiveMode",
    "ConfigurationError",
    "DecisionMetadata",
    "LastLight",
    "LastLightError",
    "PackError",
    "PackInfo",
    "PackProvenance",
    "PackValidation",
    "PackValidationError",
    "QueryExplanation",
    "QueryResult",
    "RefusalReason",
    "RetrievalMetadata",
    "RetrievalStrategyName",
    "SourceDocument",
    "SourceResult",
    "__version__",
]
