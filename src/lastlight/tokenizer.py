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

QUERY_ALIASES = {
    "agua": ("water",),
    "bateria": ("battery",),
    "brujula": ("compass",),
    "calor": ("heat",),
    "comunicacion": ("communications",),
    "emergencia": ("emergency",),
    "frio": ("cold",),
    "generador": ("generator",),
    "hemorragia": ("bleeding",),
    "incendio": ("fire",),
    "linterna": ("lighting",),
    "perdido": ("lost",),
    "quemadura": ("burns",),
    "quemaduras": ("burns",),
    "radio": ("radio",),
    "refugio": ("shelter",),
    "rescate": ("rescue", "signaling"),
    "sangrado": ("bleeding",),
    "sed": ("dehydration",),
    "senal": ("signaling",),
    "senales": ("signaling",),
    "telefono": ("phone",),
}


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.casefold()


def tokenize(text: str, keep_stopwords: bool = False) -> list[str]:
    tokens = TOKEN_RE.findall(normalize_text(text))
    if keep_stopwords:
        return tokens
    return [token for token in tokens if token not in STOPWORDS and len(token) > 1]


def expand_query_tokens(tokens: list[str]) -> list[str]:
    expanded: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        for candidate in (token, *_simple_variants(token), *QUERY_ALIASES.get(token, ())):
            if candidate and candidate not in seen:
                seen.add(candidate)
                expanded.append(candidate)
    return expanded


def _simple_variants(token: str) -> tuple[str, ...]:
    if len(token) > 4 and token.endswith("es"):
        return (token[:-2],)
    if len(token) > 3 and token.endswith("s"):
        return (token[:-1],)
    return ()
