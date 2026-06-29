"""Safety and response formatting."""

from __future__ import annotations

from .domain import SearchResult

DISCLAIMER = (
    "Experimental offline research tool. Verify critical decisions with trusted "
    "human expertise whenever possible."
)

STARTUP_WARNING = (
    "LastLight is experimental and retrieval-only. It shows sourced passages; "
    "it does not replace professional emergency guidance."
)

LOW_CONFIDENCE_RESPONSE = (
    "I do not have enough confidence to answer this question from the current knowledge base."
)


def safe_answer(results: list[SearchResult]) -> str:
    acceptable = [result for result in results if result.confidence in {"HIGH", "MEDIUM"}]
    if not acceptable:
        return f"{LOW_CONFIDENCE_RESPONSE}\n\n{DISCLAIMER}"
    return format_result(acceptable[0])


def format_result(result: SearchResult) -> str:
    doc = result.document
    tags = ", ".join(doc.tags) if doc.tags else "none"
    return (
        f"[{result.confidence} CONFIDENCE]\n\n"
        f"Title: {doc.title}\n"
        f"Source: {doc.path}\n"
        f"Language: {doc.language}\n"
        f"Tags: {tags}\n\n"
        f"Passage:\n{result.passage}\n\n"
        f"{DISCLAIMER}"
    )


def result_to_dict(result: SearchResult) -> dict[str, object]:
    doc = result.document
    return {
        "title": doc.title,
        "source": doc.path,
        "language": doc.language,
        "tags": list(doc.tags),
        "priority": doc.priority,
        "score": result.score,
        "confidence": result.confidence,
        "passage": result.passage,
        "matched_terms": list(result.matched_terms),
    }
