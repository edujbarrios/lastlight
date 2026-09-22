"""Deterministic language routing for offline retrieval."""

from __future__ import annotations

import re

from .domain import KnowledgeDocument

_WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)

_SPANISH_TERMS = {
    "agua", "ayuda", "bateria", "batería", "beber", "calor", "comida",
    "como", "cómo", "donde", "dónde", "emergencia", "fuego", "frio", "frío",
    "herida", "hervir", "inundacion", "inundación", "necesito", "primeros",
    "refugio", "sangre", "segura", "seguro", "terremoto", "sin", "con",
    "para", "que", "qué", "una", "uno", "unos", "unas", "el", "la", "los", "las",
}

_ENGLISH_TERMS = {
    "water", "help", "battery", "drink", "heat", "food", "how", "where",
    "emergency", "fire", "cold", "wound", "boil", "flood", "need", "first",
    "aid", "shelter", "blood", "safe", "earthquake", "without", "with", "for",
    "what", "the", "a", "an",
}

_SPANISH_CHARS = set("áéíóúüñ¿¡")


def corpus_languages(documents: list[KnowledgeDocument]) -> tuple[str, ...]:
    """Return known document languages in deterministic order."""
    languages = {
        document.language.casefold()
        for document in documents
        if document.language and document.language.casefold() not in {"unknown", "und"}
    }
    return tuple(sorted(languages))


def infer_query_language(text: str, available: tuple[str, ...]) -> str | None:
    """Infer Spanish or English only when the query provides useful evidence."""
    normalized = text.strip().casefold()
    if not normalized:
        return None

    words = _WORD_RE.findall(normalized)
    spanish_score = sum(word in _SPANISH_TERMS for word in words)
    english_score = sum(word in _ENGLISH_TERMS for word in words)

    if any(char in _SPANISH_CHARS for char in normalized):
        spanish_score += 2

    if "es" in available and spanish_score > english_score and spanish_score > 0:
        return "es"
    if "en" in available and english_score > spanish_score and english_score > 0:
        return "en"
    return None


def resolve_retrieval_language(
    text: str,
    documents: list[KnowledgeDocument],
    explicit_language: str | None = None,
) -> str | None:
    """Resolve the language used to filter documents for one retrieval call.

    Explicit CLI/API configuration always wins. Otherwise a monolingual corpus
    adopts its only language automatically. Multilingual corpora use conservative
    ES/EN query detection and leave ambiguous queries unfiltered.
    """
    if explicit_language:
        return explicit_language.casefold()

    available = corpus_languages(documents)
    if len(available) == 1:
        return available[0]
    return infer_query_language(text, available)
