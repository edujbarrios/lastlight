"""Tiny session memory for follow-up questions."""

from __future__ import annotations

from dataclasses import dataclass

from .app import LastLightApp
from .domain import SearchResult
from .safety import LOW_CONFIDENCE_RESPONSE, safe_answer
from .triage import append_follow_up_questions, first_acceptable_result

FOLLOW_UP_PREFIXES = (
    "and ",
    "also ",
    "what about",
    "what if",
    "what should",
    "how about",
    "then ",
    "next ",
    "can i",
    "should i",
)

SHORT_FOLLOW_UP_TERMS = {
    "again",
    "after",
    "before",
    "inside",
    "indoors",
    "night",
    "now",
    "outside",
    "then",
    "there",
    "this",
    "that",
    "with",
    "without",
}


@dataclass
class SessionMemory:
    query: str = ""
    title: str = ""
    tags: tuple[str, ...] = ()
    matched_terms: tuple[str, ...] = ()

    @property
    def has_context(self) -> bool:
        return bool(self.query or self.title or self.tags or self.matched_terms)

    def context_text(self) -> str:
        return " ".join(
            value
            for value in (
                self.query,
                self.title,
                " ".join(self.tags),
                " ".join(self.matched_terms),
            )
            if value
        )


class LastLightSession:
    def __init__(self, app: LastLightApp) -> None:
        self.app = app
        self.memory = SessionMemory()

    def clear(self) -> None:
        self.memory = SessionMemory()

    def search(self, query: str, top_k: int = 3) -> list[SearchResult]:
        search_text = self._contextual_query(query)
        results = self.app.search(search_text, top_k=top_k)
        self._remember(query, results)
        return results

    def answer(self, query: str) -> str:
        results = self.search(query, top_k=3)
        return append_follow_up_questions(
            safe_answer(results), first_acceptable_result(results)
        )

    def answer_passage(self, query: str) -> str:
        results = self.search(query, top_k=3)
        result = first_acceptable_result(results)
        if result is not None:
            return result.passage
        return LOW_CONFIDENCE_RESPONSE

    def _contextual_query(self, query: str) -> str:
        if not self.memory.has_context or not _looks_like_follow_up(query):
            return query
        return f"{self.memory.context_text()} {query}"

    def _remember(self, query: str, results: list[SearchResult]) -> None:
        for result in results:
            if result.confidence in {"HIGH", "MEDIUM"}:
                self.memory = SessionMemory(
                    query=query,
                    title=result.document.title,
                    tags=result.document.tags,
                    matched_terms=result.matched_terms,
                )
                return


def _looks_like_follow_up(query: str) -> bool:
    normalized = query.strip().casefold()
    if not normalized:
        return False
    if normalized.startswith(FOLLOW_UP_PREFIXES):
        return True
    words = normalized.replace("?", "").split()
    return len(words) <= 4 and (
        normalized.endswith("?") or bool(SHORT_FOLLOW_UP_TERMS.intersection(words))
    )
