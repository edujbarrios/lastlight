"""Evidence-oriented strategy calibration.

All scores remain on their original backend scale. This module builds a
bounded decision score from independent signals, not a probability estimate.
The legacy evaluator remains available for integrations that import it.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Sequence

from ..retrieval.tokenizer import tokenize
from ..shared.domain import KnowledgeDocument, SearchResult
from . import calibration as legacy


@dataclass(frozen=True)
class StrategyCalibration:
    """Thresholds in [0, 1] for one backend, independent of raw-score scale."""

    min_strength: float
    min_evidence_coverage: float
    min_passage_coverage: float
    min_decision_score: float
    ambiguity_ratio: float = 1.08

    def __post_init__(self) -> None:
        for name in (
            "min_strength", "min_evidence_coverage",
            "min_passage_coverage", "min_decision_score",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within [0, 1]")
        if self.ambiguity_ratio < 1.0:
            raise ValueError("ambiguity_ratio must be >= 1")


@dataclass(frozen=True)
class CalibrationConfig:
    """Public offline calibration policies; increase minima to require more proof.

    The balanced policies were selected with invented fixtures, never from
    lastlight-bench labels. Conservative mode adds a fixed evidence penalty.
    """

    lexical: StrategyCalibration = field(
        default_factory=lambda: StrategyCalibration(.37, .30, .28, .45, 1.05)
    )
    bm25: StrategyCalibration = field(
        default_factory=lambda: StrategyCalibration(.48, .32, .28, .47, 1.08)
    )
    hybrid: StrategyCalibration = field(
        default_factory=lambda: StrategyCalibration(.45, .37, .30, .49, 1.06)
    )
    conservative_delta: float = .12
    weight_strength: float = .22
    weight_coverage: float = .33
    weight_passage: float = .30
    weight_title: float = .10
    weight_agreement: float = .05

    def __post_init__(self) -> None:
        if not 0 <= self.conservative_delta <= .5:
            raise ValueError("conservative_delta must be within [0, 0.5]")
        weights = (
            self.weight_strength, self.weight_coverage, self.weight_passage,
            self.weight_title, self.weight_agreement
        )
        if any(w < 0 or w > 1 for w in weights) or abs(sum(weights) - 1) > 1e-8:
            raise ValueError("calibration signal weights must be nonnegative and sum to 1")


def _focus_terms(query: str) -> tuple[str, ...]:
    """Remove narrative filler, retaining constraints and distinctive concepts."""
    terms = legacy._query_terms(query)
    return tuple(t for t in terms if t not in legacy._GENERIC and
                 t not in {"did", "does", "may", "might", "could", "during",
                           "will", "would", "now", "right", "please", "tell",
                           "need", "want", "person", "someone", "get", "make",
                           "using", "use", "them", "their", "your", "this",
                           "there", "than", "then", "also", "any", "some",
                           "been", "have", "has", "with", "without"} or
                 t in legacy._NEGATIONS | legacy._CONSTRAINTS)


def _fraction(terms: Sequence[str], tokens: set[str], corpus: Sequence[KnowledgeDocument],
              query: str) -> float:
    if not terms:
        return 0.0
    return legacy._weighted_coverage(tuple(terms), tokens,
                                     legacy._document_frequency(corpus), len(corpus), query)


def _code(reason: str, accepted: bool, *, no_results: bool = False) -> str | None:
    if accepted:
        return None
    if no_results or reason in {"no_matching_knowledge", "low_base_confidence",
                                "weak_absolute_evidence", "insufficient_query_coverage"}:
        return "OUT_OF_DOMAIN" if no_results or reason == "no_matching_knowledge" else "INSUFFICIENT_EVIDENCE"
    if "ambiguous" in reason or "disagree" in reason:
        return "AMBIGUOUS_CANDIDATES"
    if reason == "requires_live_or_future_evidence":
        return "DYNAMIC_INFORMATION_REQUIRED"
    if reason == "requires_authority_decision":
        return "AUTHORITY_DECISION_REQUIRED"
    if reason == "requires_authorized_or_private_evidence":
        return "PRIVATE_OR_CREDENTIAL_DATA"
    if reason in {"missing_quantity_evidence", "missing_temporal_evidence",
                  "missing_identity_evidence", "missing_negative_evidence",
                  "incomplete_list_evidence", "empty_passage"}:
        return "MISSING_REQUESTED_FACT"
    return "INSUFFICIENT_EVIDENCE"


def evaluate_calibrated_decision(
    query_text: str,
    results: list[SearchResult],
    *,
    strategy: str = "lexical",
    profile: str = "balanced",
    corpus: Sequence[KnowledgeDocument] | None = None,
    verification_agreement: bool | None = None,
    config: CalibrationConfig | None = None,
) -> legacy.AnswerDecision:
    """Evaluate passage evidence and return a fully auditable answer decision."""
    if strategy not in ("lexical", "bm25", "hybrid"):
        raise ValueError(f"unsupported decision strategy: {strategy}")
    if profile not in ("balanced", "conservative"):
        raise ValueError(f"unsupported decision profile: {profile}")
    config = config if config is not None else CalibrationConfig()
    documents = tuple(corpus) if corpus is not None else tuple(r.document for r in results)
    # Legacy provides established coverage, score-margin, and mandatory
    # request-type checks. RRF needs its own score reference (not BM25's).
    previous = legacy.evaluate_answer_decision(
        query_text, results, strategy="bm25" if strategy == "hybrid" else strategy,
        profile=profile, corpus=documents,
        verification_agreement=verification_agreement,
    )
    if not results:
        return replace(previous, strategy=strategy, refusal_code="OUT_OF_DOMAIN",
                       explanation="No local source matched this query.")
    winner = results[0]
    passage = winner.passage
    gate = legacy._unsupported_intent(query_text)
    enough, fact_reason = legacy._passage_sufficiency(query_text, passage)
    # Non-negotiable evidence and authorization gates precede calibrated scores.
    if gate is not None or not enough:
        reason = gate or fact_reason
        return replace(
            previous, strategy=strategy, accepted=False, result=None, confidence=None,
            reason=reason, refusal_reason="insufficient_confidence",
            evidence_sufficient=False,
            refusal_code=_code(reason, False),
            explanation="The requested fact or authorization is not established by the passage.",
        )

    terms = _focus_terms(query_text)
    passage_tokens = set(tokenize(passage, keep_stopwords=True))
    heading_text = winner.section or ""
    title_tokens = set(tokenize(winner.document.title + " " + heading_text +
                                " " + " ".join(winner.document.tags), keep_stopwords=True))
    hits = set(winner.matched_terms) | passage_tokens
    coverage = _fraction(terms, hits, documents, query_text)
    passage_coverage = _fraction(terms, passage_tokens, documents, query_text)
    title_coverage = _fraction(terms, title_tokens, documents, query_text)
    raw_strength = (
        winner.score / (winner.score + .028) if strategy == "hybrid"
        else legacy._strength(winner.score, strategy)
    )
    agreement = (
        1.0 if verification_agreement is True or len(winner.backend_scores) == 2
        else .4 if verification_agreement is None else 0.0
    )
    calibrated = max(0.0, min(1.0,
        raw_strength * config.weight_strength
        + coverage * config.weight_coverage
        + passage_coverage * config.weight_passage
        + title_coverage * config.weight_title
        + agreement * config.weight_agreement
    ))
    policy = getattr(config, strategy)
    penalty = config.conservative_delta if profile == "conservative" else 0.0
    ratio = previous.score_ratio
    # RRF scores are meaningful only against other RRF scores; never compare
    # the backend_scores values from different ranking systems.
    near_tie = ratio is not None and ratio < policy.ambiguity_ratio
    runner_passage = results[1].passage if len(results) > 1 else ""
    runner_evidence = _fraction(terms, set(tokenize(runner_passage)), documents, query_text)
    uncorroborated = verification_agreement is False and profile == "conservative"
    ambiguous = (near_tie and runner_evidence + .12 >= passage_coverage
                 and (strategy == "hybrid" or coverage < .65))
    # A relevant passage with a clear direct answer can compensate for
    # missing narrative query vocabulary; no single raw score can do so.
    accepted = (
        winner.confidence in {"HIGH", "MEDIUM"}
        and raw_strength >= policy.min_strength + penalty / 2
        and coverage >= policy.min_evidence_coverage + penalty
        and passage_coverage >= policy.min_passage_coverage + penalty
        and calibrated >= policy.min_decision_score + penalty
        and not ambiguous and not uncorroborated
    )
    if ambiguous or uncorroborated:
        reason = "ambiguous_evidence"
    elif not accepted:
        reason = "insufficient_passage_coverage" if passage_coverage < policy.min_passage_coverage + penalty else "insufficient_query_coverage"
    else:
        reason = "calibrated_passage_evidence"
    confidence = (
        "HIGH" if accepted and calibrated >= .60 and not near_tie and winner.confidence == "HIGH" else
        "MEDIUM" if accepted else None
    )
    return replace(
        previous, strategy=strategy, accepted=accepted,
        result=winner if accepted else None, confidence=confidence,
        reason=reason, refusal_reason=None if accepted else "insufficient_confidence",
        evidence_sufficient=enough, relevance_strength=raw_strength,
        weighted_query_coverage=coverage, passage_coverage=passage_coverage,
        calibrated_score=calibrated, refusal_code=_code(reason, accepted),
        explanation=(
            f"Evidence score {calibrated:.3f}; focus coverage {coverage:.3f}; "
            f"passage coverage {passage_coverage:.3f}; "
            + ("passage supports the request." if accepted else "local evidence is insufficient.")
        ),
    )
