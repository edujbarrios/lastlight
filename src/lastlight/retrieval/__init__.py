"""Retrieval algorithms and resource-adaptive planning."""

from .adaptive import AdaptiveRetrievalConfig, AdaptiveRetrievalStrategy, ResourceProfile, RetrievalDecision
from .strategies import BM25RetrievalStrategy, LexicalRetrievalStrategy, select_passage
from .hybrid import HybridRetrievalStrategy, reciprocal_rank_fusion
from .sections import SectionConfig

__all__ = [
    "AdaptiveRetrievalConfig",
    "AdaptiveRetrievalStrategy",
    "BM25RetrievalStrategy",
    "LexicalRetrievalStrategy",
    "HybridRetrievalStrategy",
    "SectionConfig",
    "reciprocal_rank_fusion",
    "ResourceProfile",
    "RetrievalDecision",
    "select_passage",
]
