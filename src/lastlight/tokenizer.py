"""Deterministic Unicode normalization and tokenization."""

from __future__ import annotations

import re
import unicodedata

ENGLISH_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "for", "from",
    "how", "i", "if", "in", "is", "it", "of", "on", "or", "the", "this", "to",
    "what", "when", "with", "you", "your",
}

SPANISH_STOPWORDS = {
    "a", "al", "como", "con", "de", "del", "el", "en", "es", "la", "las", "los",
    "para", "por", "que", "si", "un", "una", "y",
}

STOPWORDS = ENGLISH_STOPWORDS | SPANISH_STOPWORDS
TOKEN_RE = re.compile(r"[a-z0-9]+")


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.casefold()


def tokenize(text: str, keep_stopwords: bool = False) -> list[str]:
    tokens = TOKEN_RE.findall(normalize_text(text))
    if keep_stopwords:
        return tokens
    return [token for token in tokens if token not in STOPWORDS and len(token) > 1]

