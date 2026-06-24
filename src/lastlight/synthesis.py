"""Citation-aware experimental synthesis from retrieved passages."""

from __future__ import annotations

from .domain import SearchResult
from .ngram import NGramLanguageModel
from .safety import DISCLAIMER, LOW_CONFIDENCE_RESPONSE

SYNTHESIS_WARNING = (
    "Experimental synthesis. Generated only from the retrieved passage below; "
    "use the cited passage as the authority."
)


def synthesize_answer(query: str, results: list[SearchResult]) -> str:
    acceptable = [result for result in results if result.confidence in {"HIGH", "MEDIUM"}]
    if not acceptable:
        return f"{LOW_CONFIDENCE_RESPONSE}\n\n{DISCLAIMER}"

    result = acceptable[0]
    model = NGramLanguageModel(order=2)
    model.train(result.passage)
    generated = model.generate(query, max_tokens=26)
    if not generated:
        generated = result.passage

    doc = result.document
    tags = ", ".join(doc.tags) if doc.tags else "none"
    return (
        f"[{result.confidence} CONFIDENCE]\n\n"
        f"{SYNTHESIS_WARNING}\n\n"
        f"Generated note:\n{generated}\n\n"
        f"Citation:\n"
        f"Title: {doc.title}\n"
        f"Source: {doc.path}\n"
        f"Language: {doc.language}\n"
        f"Tags: {tags}\n\n"
        f"Retrieved passage:\n{result.passage}\n\n"
        f"{DISCLAIMER}"
    )

