"""Deterministic follow-up checks for retrieved emergency knowledge."""

from __future__ import annotations

from .domain import SearchResult

TRIAGE_RULES: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (
        ("carbon-monoxide", "carbon monoxide", "generator", "gas", "fuel"),
        (
            "Do you smell gas or fuel, or does anyone feel dizzy, weak, nauseated, or confused?",
            "Can you move people to fresh air before doing anything else?",
        ),
    ),
    (
        ("bleeding", "wound", "burn", "injury", "injured", "medical", "unconscious"),
        (
            "Is anyone injured, bleeding heavily, unconscious, or not breathing normally?",
            "Do you have clean cloth, safe water, or first aid supplies nearby?",
        ),
    ),
    (
        ("water", "dehydration", "purification", "boil", "drink"),
        (
            "Does the water smell like fuel, chemicals, sewage, or solvents?",
            "Can you boil it, or do you only have filters, cloth, or disinfectant?",
        ),
    ),
    (
        ("food", "refrigerator", "freezer", "spoiled", "perishable"),
        (
            "How long has the refrigerator or freezer been without power?",
            "Does any food smell wrong, feel slimy, show mold, or have leaking packaging?",
        ),
    ),
    (
        ("battery", "phone", "radio", "communication", "signal"),
        (
            "Do you need to contact someone now, or can the phone stay in low-power mode?",
            "Have you written critical numbers or instructions on paper?",
        ),
    ),
    (
        ("navigation", "compass", "lost", "north", "direction"),
        (
            "Are you safer staying put than moving right now?",
            "Can you confirm direction with more than one clue before traveling?",
        ),
    ),
)

GENERAL_CHECKS = (
    "Is anyone in immediate danger right now?",
    "What is the next practical action you need to decide?",
)


def first_acceptable_result(results: list[SearchResult]) -> SearchResult | None:
    for result in results:
        if result.confidence in {"HIGH", "MEDIUM"}:
            return result
    return None


def suggest_follow_up_questions(
    result: SearchResult, max_questions: int = 2
) -> tuple[str, ...]:
    """Return small triage questions grounded in the retrieved result."""

    if max_questions <= 0 or result.confidence not in {"HIGH", "MEDIUM"}:
        return ()

    haystack = _result_text(result)
    questions: list[str] = []
    for terms, rule_questions in TRIAGE_RULES:
        if any(term in haystack for term in terms):
            questions.extend(rule_questions)
        if len(questions) >= max_questions:
            break

    if not questions:
        questions.extend(GENERAL_CHECKS)

    return tuple(_dedupe(questions)[:max_questions])


def append_follow_up_questions(answer: str, result: SearchResult | None) -> str:
    if result is None:
        return answer

    questions = suggest_follow_up_questions(result)
    if not questions:
        return answer

    checks = "\n".join(f"- {question}" for question in questions)
    return f"{answer}\n\nFollow-up checks:\n{checks}"


def _result_text(result: SearchResult) -> str:
    document = result.document
    return " ".join(
        (
            document.title,
            document.path,
            document.body,
            " ".join(document.tags),
            result.passage,
            " ".join(result.matched_terms),
        )
    ).casefold()


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        key = value.casefold()
        if key in seen:
            continue
        seen.add(key)
        unique.append(value)
    return unique
