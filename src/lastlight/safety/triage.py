"""Deterministic follow-up checks for retrieved emergency knowledge."""

from __future__ import annotations

from ..retrieval.tokenizer import tokenize
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

SPANISH_QUESTION_MAP = {
    "Do you smell gas or fuel, or does anyone feel dizzy, weak, nauseated, or confused?":
        "¿Huele a gas o combustible, o alguien está mareado, débil, con náuseas o confuso?",
    "Can you move people to fresh air before doing anything else?":
        "¿Puedes llevar a las personas a un lugar con aire fresco antes de hacer otra cosa?",
    "Is anyone injured, bleeding heavily, unconscious, or not breathing normally?":
        "¿Hay alguien herido, con sangrado abundante, inconsciente o que no respira con normalidad?",
    "Do you have clean cloth, safe water, or first aid supplies nearby?":
        "¿Tienes cerca paños limpios, agua segura o material de primeros auxilios?",
    "Does the water smell like fuel, chemicals, sewage, or solvents?":
        "¿El agua huele a combustible, productos químicos, aguas residuales o disolventes?",
    "Can you boil it, or do you only have filters, cloth, or disinfectant?":
        "¿Puedes hervirla o solo tienes filtros, paños o desinfectante?",
    "How long has the refrigerator or freezer been without power?":
        "¿Cuánto tiempo llevan el frigorífico o el congelador sin electricidad?",
    "Does any food smell wrong, feel slimy, show mold, or have leaking packaging?":
        "¿Algún alimento huele mal, está viscoso, tiene moho o presenta un envase con fugas?",
    "Do you need to contact someone now, or can the phone stay in low-power mode?":
        "¿Necesitas contactar con alguien ahora o puede el teléfono permanecer en modo de bajo consumo?",
    "Have you written critical numbers or instructions on paper?":
        "¿Has anotado en papel los números o instrucciones importantes?",
    "Are you safer staying put than moving right now?":
        "¿Es más seguro permanecer donde estás que desplazarte ahora mismo?",
    "Can you confirm direction with more than one clue before traveling?":
        "¿Puedes confirmar la dirección con más de una referencia antes de desplazarte?",
    "Is anyone in immediate danger right now?":
        "¿Hay alguien en peligro inmediato ahora mismo?",
    "What is the next practical action you need to decide?":
        "¿Cuál es la siguiente acción práctica que necesitas decidir?",
}


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
        if any(_contains_triage_term(haystack, term) for term in terms):
            questions.extend(rule_questions)
        if len(questions) >= max_questions:
            break

    if not questions:
        questions.extend(GENERAL_CHECKS)

    unique = _dedupe(questions)[:max_questions]
    if result.document.language.casefold() == "es":
        unique = [SPANISH_QUESTION_MAP.get(question, question) for question in unique]
    return tuple(unique)


def append_follow_up_questions(answer: str, result: SearchResult | None) -> str:
    if result is None:
        return answer

    questions = suggest_follow_up_questions(result)
    if not questions:
        return answer

    checks = "\n".join(f"- {question}" for question in questions)
    heading = (
        "Comprobaciones de seguimiento:"
        if result.document.language.casefold() == "es"
        else "Follow-up checks:"
    )
    return f"{answer}\n\n{heading}\n{checks}"


def _result_text(result: SearchResult) -> str:
    document = result.document
    raw = " ".join(
        (
            document.title,
            document.path,
            document.body,
            " ".join(document.tags),
            result.passage,
            " ".join(result.matched_terms),
        )
    )
    return " ".join(tokenize(raw, keep_stopwords=True))


def _contains_triage_term(normalized: str, term: str) -> bool:
    normalized_term = " ".join(tokenize(term, keep_stopwords=True))
    if not normalized_term:
        return False
    return f" {normalized_term} " in f" {normalized} "


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
