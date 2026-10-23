"""Evidence-aware, strategy-specific answer calibration (standard library only).

The ranker's confidence describes relevance, never permission to answer.
Scores are never compared across retrieval backends; normalized strength is
a monotonic strategy-specific diagnostic, not a probability.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date
from typing import Sequence

from ..retrieval.adaptive import classify_query_risk
from ..retrieval.tokenizer import QUERY_ALIASES, normalize_text, tokenize
from ..shared.domain import KnowledgeDocument, SearchResult

_GENERIC = frozenset({
    "someone", "somebody", "please", "tell", "about", "has", "have", "does",
    "will", "stay", "long", "should", "would", "could", "help", "know",
    "information", "details", "guide", "emergency", "situation", "now",
    "have", "that", "found", "looks", "should", "would", "supply", "down",
    "been", "several", "out", "my", "some", "could", "there", "was", "were",
    "today", "currently", "latest", "right", "current", "available",
    "actualmente", "ahora", "hoy", "ultimo", "cuanto", "cuantos",
    "cuando", "quien", "quienes", "cual", "cuales", "what", "who",
    "which", "where", "how", "many", "much", "can",
})
_CONSTRAINTS = frozenset({
    "only", "unless", "except", "without", "before", "after", "minimum",
    "maximum", "at", "least", "more", "less", "under", "over", "between",
    "solo", "excepto", "sin", "antes", "despues", "minimo", "maximo",
    "hasta", "desde", "superior", "inferior",
})
_NEGATIONS = frozenset({
    "no", "not", "never", "cannot", "cant", "dont", "mustnt", "prohibited",
    "prohibido", "nunca", "jamas", "ningun", "ninguna", "sin",
})
_NEGATIVE_EVIDENCE = _NEGATIONS | frozenset({
    "avoid", "forbidden", "unsafe", "do not", "only if", "unless", "except",
    "evite", "prohibe", "prohibida", "prohibido", "solamente", "unicamente",
})
_QUANTITY = re.compile(r"\b(how much|how many|amount|quantity|cuanto|cuanta|cuantos|cuantas|cantidad)\b")
_TIME = re.compile(r"\b(when|how long|how soon|cuando|cuanto tiempo|durante cuanto|plazo)\b")
_IDENTITY = re.compile(r"\b(who|whose|quien|quienes|de quien)\b")
_LIST = re.compile(r"\b(list|enumerate|which items|all the|lista|enumera|cuales son|todos los)\b")
_NUMBER = re.compile(r"\b\d+(?:[.,]\d+)?\b")
_QUANTITY_EVIDENCE = re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:%|percent|liters?|litros?|ml|mg|kg|grams?|gramos?|minutes?|minutos?|hours?|horas?|days?|dias?|weeks?|semanas?|meters?|metros?|feet|ft|units?|unidades?)\b")
_TIME_EVIDENCE = re.compile(r"\b(before|after|until|once|when|during|if|at|hours?|days?|minutes?|weeks?|months?|years?|antes|despues|hasta|cuando|durante|si|horas?|dias?|minutos?|meses?|anos?)\b")
_ROLE_EVIDENCE = re.compile(r"\b(officer|operator|coordinator|authority|doctor|clinician|responder|team|person|leader|manager|medico|responsable|autoridad|equipo|encargado|director)\b")
_MUTABLE = re.compile(
    r"\b(now|right now|today|currently|at present|latest|most recent|"
    r"up.to.date|live|real.time|current stock|in stock|remaining|"
    r"how much remains|available now|availability|who was the last|"
    r"who is the current|next week|tomorrow|future|forecast|"
    r"ahora|hoy|actualmente|en este momento|ultima hora|ultimo|"
    r"disponibilidad|existencias|inventario actual|quedan|"
    r"cuanto queda|manana|proximo)\b"
)
_SENSITIVE = re.compile(
    r"\b(password|passphrase|credential|api key|secret|token de acceso|"
    r"contrasena|clave privada|secreto|credencial|private data|personal data|"
    r"datos privados|datos personales|medical record|historial clinico|"
    r"certify|certified|certification|certificar|certificado|"
    r"prescribe|prescription|dosage|dose|recetar|prescribir|dosis)\b"
)
_AUTHORITY = re.compile(r"\b(approve|authorize|authorized|license|permit|decide|"
                        r"aprobar|autorizar|licencia|permiso|decision oficial)\b")


@dataclass(frozen=True)
class DecisionThresholds:
    min_strength: float
    min_coverage: float
    min_weighted_coverage: float
    min_passage_coverage: float
    min_discriminative_matches: int


# Fixed policy defaults from an independent synthetic calibration cohort.
# They are not learned from, or selected against, lastlight-bench.
THRESHOLDS: dict[str, dict[str, DecisionThresholds]] = {
    "lexical": {
        "balanced": DecisionThresholds(0.35, 0.20, 0.22, 0.13, 1),
        "conservative": DecisionThresholds(0.50, 0.35, 0.45, 0.40, 2),
    },
    "bm25": {
        "balanced": DecisionThresholds(0.44, 0.40, 0.52, 0.30, 2),
        "conservative": DecisionThresholds(0.55, 0.50, 0.65, 0.45, 2),
    },
}


@dataclass(frozen=True)
class AnswerDecision:
    """Four distinct layers: relevance, passage sufficiency, confidence, accept."""

    accepted: bool
    result: SearchResult | None
    confidence: str | None
    reason: str
    refusal_reason: str | None
    score: float | None
    runner_up_score: float | None
    score_margin: float | None
    score_ratio: float | None
    query_coverage: float
    query_terms: tuple[str, ...]
    matched_terms: tuple[str, ...]
    strategy: str = "lexical"
    profile: str = "balanced"
    risk: str = "normal"
    relevance_strength: float = 0.0
    weighted_query_coverage: float = 0.0
    passage_coverage: float = 0.0
    discriminative_matches: int = 0
    evidence_sufficient: bool = False
    verification_agreement: bool | None = None


def evaluate_answer_decision(
    query_text: str,
    results: list[SearchResult],
    *,
    strategy: str = "lexical",
    profile: str = "balanced",
    corpus: Sequence[KnowledgeDocument] | None = None,
    verification_agreement: bool | None = None,
) -> AnswerDecision:
    """Evaluate an answer without changing retrieval order or hallucinating content.

    The score ratio and margin are calculated only inside the selected backend.
    Query coverage is based on original query concepts, not alias-expanded counts.
    A retrieved document's title/tags cannot substitute for passage evidence.
    """
    if strategy == "adaptive":
        strategy = "bm25"  # direct callers should pass the adaptive chosen backend
    if strategy not in THRESHOLDS:
        raise ValueError(f"unsupported decision strategy: {strategy}")
    if profile not in THRESHOLDS[strategy]:
        raise ValueError(f"unsupported decision profile: {profile}")

    terms = _query_terms(query_text)
    risk = classify_query_risk(query_text)
    winner = results[0] if results else None
    second = results[1] if len(results) > 1 else None
    second_score = second.score if second else None
    margin = winner.score - second.score if winner and second else None
    ratio = _score_ratio(winner.score, second_score) if winner else None
    matched = tuple(sorted(set(winner.matched_terms))) if winner else ()
    # Third-party retrieval adapters may omit matched_terms. Derive a
    # conservative fallback from *passage* tokens, never title-only matches.
    if winner and not matched:
        matched = tuple(sorted(set(tokenize(winner.passage, keep_stopwords=True))))
    documents = tuple(corpus) if corpus is not None else tuple(result.document for result in results)
    frequency = _document_frequency(documents)
    n = len(documents)
    passage_tokens = set(tokenize(winner.passage, keep_stopwords=True)) if winner else set()
    # A ranker's matched_terms can omit inflectional/translated evidence that
    # is genuinely present in the passage. Count that evidence without giving
    # credit for title/tag-only terms.
    evidence_tokens = set(matched) | passage_tokens
    weighted = _weighted_coverage(terms, evidence_tokens, frequency, n, query_text)
    coverage = _coverage(terms, evidence_tokens)
    passage_coverage = _weighted_coverage(terms, passage_tokens, frequency, n, query_text)
    discriminative = _discriminative_matches(terms, matched, passage_tokens, frequency, n, query_text)
    strength = _strength(winner.score, strategy) if winner else 0.0
    evidence_sufficient, evidence_reason = _passage_sufficiency(query_text, winner.passage) if winner else (False, "no_matching_knowledge")

    def finish(accepted: bool, reason: str, confidence: str | None = None) -> AnswerDecision:
        return AnswerDecision(
            accepted=accepted,
            result=winner if accepted else None,
            confidence=confidence if accepted else None,
            reason=reason,
            refusal_reason=None if accepted else (
                "no_matching_knowledge" if winner is None else "insufficient_confidence"
            ),
            score=winner.score if winner else None,
            runner_up_score=second_score,
            score_margin=margin,
            score_ratio=ratio,
            query_coverage=coverage,
            query_terms=terms,
            matched_terms=matched,
            strategy=strategy,
            profile=profile,
            risk=risk,
            relevance_strength=strength,
            weighted_query_coverage=weighted,
            passage_coverage=passage_coverage,
            discriminative_matches=discriminative,
            evidence_sufficient=evidence_sufficient,
            verification_agreement=verification_agreement,
        )

    if winner is None:
        return finish(False, "no_matching_knowledge")

    # A static local pack cannot attest to live states, private access or a
    # professional/authority decision. Even dated text is not a live oracle.
    intent = _unsupported_intent(query_text)
    if intent is not None:
        return finish(False, intent)
    if not evidence_sufficient:
        return finish(False, evidence_reason)
    if winner.confidence == "LOW" or not math.isfinite(winner.score):
        return finish(False, "low_base_confidence")

    bounds = THRESHOLDS[strategy][profile]
    risk_offset = 0.05 if risk == "critical" else 0.03 if risk == "high" else 0.0
    if strength < bounds.min_strength:
        return finish(False, "weak_absolute_evidence")
    if coverage < bounds.min_coverage or weighted < bounds.min_weighted_coverage + risk_offset:
        return finish(False, "insufficient_query_coverage")
    if passage_coverage < bounds.min_passage_coverage + risk_offset:
        return finish(False, "insufficient_passage_coverage")
    required_matches = min(bounds.min_discriminative_matches, len(terms))
    if discriminative < required_matches:
        return finish(False, "insufficient_discriminative_matches")

    # Near-tied medium candidates matching only one original query concept
    # remain ambiguous, even if passage vocabulary increases raw coverage.
    # HIGH neighbours are also unsafe on a thin original rank signal.
    original_rank_coverage = _coverage(terms, matched)
    if (second is not None and ratio is not None and ratio < 1.15
        and len(terms) >= 4 and original_rank_coverage < 0.25):
        return finish(False, "weak_query_coverage_and_ambiguous_margin")

    ambiguous = second is not None and ratio is not None and ratio < (
        1.12 if strategy == "bm25" else 1.05
    )
    if ambiguous and strategy == "bm25" and (
        weighted < 0.82 or passage_coverage < 0.65
    ):
        return finish(False, "ambiguous_evidence")
    if ambiguous and winner.confidence == "MEDIUM" and coverage < 0.28:
        return finish(False, "weak_query_coverage_and_ambiguous_margin")
    if verification_agreement is False and (
        strategy == "bm25" and (profile == "conservative" or risk != "normal")
    ):
        return finish(False, "retrieval_strategies_disagree")

    if ambiguous and winner.confidence == "HIGH":
        return finish(True, "ambiguous_high_confidence_matches", "MEDIUM")
    if verification_agreement is False:
        return finish(True, "secondary_retrieval_disagrees", "MEDIUM")
    high = winner.confidence == "HIGH" and strength >= (
        0.55 if strategy == "lexical" else 0.65
    ) and (not ambiguous)
    reason = (
        "strong_match_clear_margin" if high and ratio is not None and ratio >= 1.5
        else "strong_match" if high
        else "supported_match_clear_margin" if ratio is not None and ratio >= 1.5
        else "supported_match"
    )
    return finish(True, reason, "HIGH" if high else "MEDIUM")


def _query_terms(query_text: str) -> tuple[str, ...]:
    # Keep negations and constraints as content even if the ranker drops them.
    tokens = tokenize(query_text, keep_stopwords=True)
    return tuple(dict.fromkeys(
        token for token in tokens
        if (token not in {"a", "an", "and", "are", "as", "at", "be", "by", "do",
                         "for", "from", "how", "i", "if", "in", "is", "it", "of",
                         "on", "or", "the", "this", "to", "what", "when", "with",
                         "you", "your", "de", "del", "el", "en", "es", "la", "las",
                         "los", "para", "por", "que", "si", "un", "una", "y",
                         "con", "al", "como"}
            or token in _NEGATIONS or token in _CONSTRAINTS)
        and len(token) > 1
    ))


def _term_hit(term: str, matched: set[str]) -> bool:
    if term in matched:
        return True
    # Match both directions of the built-in bilingual aliases, without
    # increasing the number of query concepts in the denominator.
    alternatives = (*QUERY_ALIASES.get(term, ()),
                    *(key for key, aliases in QUERY_ALIASES.items() if term in aliases))
    candidates = (term, *alternatives)
    return any(
        candidate in matched
        or (candidate.endswith("s") and candidate[:-1] in matched)
        or (candidate.endswith("es") and candidate[:-2] in matched)
        or (candidate + "s" in matched)
        or (candidate + "es" in matched)
        for candidate in candidates
    )


def _coverage(terms: tuple[str, ...], matched: Sequence[str]) -> float:
    if not terms:
        return 0.0
    found = set(matched)
    return sum(_term_hit(term, found) for term in terms) / len(terms)


def _document_frequency(corpus: Sequence[KnowledgeDocument]) -> Counter[str]:
    df: Counter[str] = Counter()
    for document in corpus:
        df.update(set(tokenize(document.title + " " + " ".join(document.tags) + " " + document.body)))
    return df


def _term_weight(term: str, df: Counter[str], n: int, query: str) -> float:
    weight = 0.40 if term in _GENERIC else 1.0
    if n >= 2:
        weight *= 0.65 + math.log1p((n + 0.5) / (df.get(term, 0) + 0.5))
    if term.isdigit() or term in _NEGATIONS:
        weight *= 2.3
    elif term in _CONSTRAINTS:
        weight *= 1.9
    elif len(term) >= 8 and term not in _GENERIC:
        weight *= 1.25
    # Mid-sentence capitalized entities and acronyms, without external NER.
    raw = re.findall(r"\b[A-Za-z][A-Za-z0-9]*\b", query)
    if any(normalize_text(token) == term and (token.isupper() or token[0].isupper())
           for token in raw[1:]):
        weight *= 1.5
    return weight


def _weighted_coverage(
    terms: tuple[str, ...], matched: Sequence[str] | set[str],
    df: Counter[str], n: int, query: str,
) -> float:
    if not terms:
        return 0.0
    found = set(matched)
    weights = [_term_weight(term, df, n, query) for term in terms]
    total = sum(weights)
    return sum(w for term, w in zip(terms, weights) if _term_hit(term, found)) / total if total else 0.0


def _discriminative_matches(
    terms: tuple[str, ...], matched: tuple[str, ...], passage: set[str],
    df: Counter[str], n: int, query: str,
) -> int:
    found = set(matched)
    return sum(
        _term_hit(t, found) and _term_hit(t, passage)
        for t in terms
        if t not in _GENERIC and (
            n < 2 or df.get(t, 0) < n or len(t) >= 5
            or t in _CONSTRAINTS or t in _NEGATIONS
        )
    )


def _passage_sufficiency(query: str, passage: str) -> tuple[bool, str]:
    q = normalize_text(query)
    p = normalize_text(passage)
    if not p.strip():
        return False, "empty_passage"
    # Numbers, dates and prohibitions in unrelated footnotes are not evidence.
    concepts = [term for term in _query_terms(q)
                if term not in _GENERIC | _NEGATIONS | _CONSTRAINTS]
    sentences = re.split(r"(?<=[.!?])\s+|\n+", p)
    pertinent = [sentence for sentence in sentences
                 if not concepts or any(
                     _term_hit(term, set(tokenize(sentence, keep_stopwords=True)))
                     for term in concepts
                 )]
    if _QUANTITY.search(q) and not any(
        _QUANTITY_EVIDENCE.search(s) or _NUMBER.search(s) for s in pertinent
    ):
        return False, "missing_quantity_evidence"
    if _TIME.search(q) and not any(
        _TIME_EVIDENCE.search(s) or _NUMBER.search(s) for s in pertinent
    ):
        return False, "missing_temporal_evidence"
    if _IDENTITY.search(q) and not any(
        _ROLE_EVIDENCE.search(s) or re.search(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b", passage)
        for s in pertinent
    ):
        return False, "missing_identity_evidence"
    # A negative *constraint* (forbidden/without/never) demands explicit
    # negative evidence. "I have no bottled water" is situational context,
    # not a request for a prohibition to be proved.
    negative_intent = bool(re.search(
        r"\b(without|never|must not|should not|cannot|is it forbidden|"
        r"sin|nunca|no se debe|esta prohibido|prohibido|no puedo)\b", q
    ))
    if negative_intent and not any(
        set(tokenize(s, keep_stopwords=True)).intersection(_NEGATIVE_EVIDENCE)
        for s in pertinent
    ):
        return False, "missing_negative_evidence"
    if _LIST.search(q) and not (
        len(re.findall(r"[,;]", " ".join(pertinent))) >= 2
        or len(re.findall(r"(?:^|\n)\s*[-*0-9]+[.) -]", passage)) >= 2
        or len(re.split(r"\b(?:and|or|y)\b", " ".join(pertinent))) >= 3
    ):
        return False, "incomplete_list_evidence"
    return True, "passage_supported"


def _unsupported_intent(query: str) -> str | None:
    q = normalize_text(query)
    if _SENSITIVE.search(q):
        return "requires_authorized_or_private_evidence"
    if _MUTABLE.search(q):
        return "requires_live_or_future_evidence"
    if _AUTHORITY.search(q) and re.search(
        r"\b(who|can you|please|is it|do i have|quien|puedes|esta|autoridad)\b", q
    ):
        return "requires_authority_decision"
    return None


def _strength(score: float, strategy: str) -> float:
    if not math.isfinite(score) or score <= 0:
        return 0.0
    reference = 3.0 if strategy == "bm25" else 0.65
    return score / (score + reference)


def _score_ratio(score: float, runner_up_score: float | None) -> float | None:
    if runner_up_score is None:
        return None
    if runner_up_score <= 0:
        return float("inf") if score > 0 else 1.0
    return score / runner_up_score
