"""Retrieval algorithms and resource-adaptive planning."""

from .adaptive import AdaptiveRetrievalConfig, AdaptiveRetrievalStrategy, ResourceProfile, RetrievalDecision
from .strategies import BM25RetrievalStrategy, LexicalRetrievalStrategy, select_passage

__all__ = [
    "AdaptiveRetrievalConfig",
    "AdaptiveRetrievalStrategy",
    "BM25RetrievalStrategy",
    "LexicalRetrievalStrategy",
    "ResourceProfile",
    "RetrievalDecision",
    "select_passage",
]
