"""LastLight: offline intelligence under extreme constraints."""

from .api import LastLight
from .safety.calibration_v3 import CalibrationConfig, StrategyCalibration
from .retrieval.sections import SectionConfig
from .errors import ConfigurationError, LastLightError, PackError, PackValidationError
from .types import (
    AdaptiveMode,
    DecisionMetadata,
    DecisionProfileName,
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

__version__ = "0.3.0"

__all__ = [
    "AdaptiveMode",
    "CalibrationConfig",
    "StrategyCalibration",
    "SectionConfig",
    "ConfigurationError",
    "DecisionMetadata",
    "DecisionProfileName",
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
