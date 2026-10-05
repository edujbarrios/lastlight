"""Deterministic answer acceptance and confidence calibration."""

from __future__ import annotations

from dataclasses import dataclass

from ..retrieval.tokenizer import expand_query_tokens, tokenize
from .domain import SearchResult


@dataclass(frozen=True)
class AnswerDecision:
    """Internal evidence used to accept, downgrade, or refuse a retrieved answer."""

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


def evaluate_answer_decision(query_text: str, results: list[SearchResult]) -> AnswerDecision:
    """Combine rank confidence, query coverage, and winner margin deterministically.

    Retrieval score scales remain strategy-specific. The decision layer therefore
    uses ratios only between results produced by the same search execution.
    """

    query_terms = _query_terms(query_text)
    if not results:
        return AnswerDecision(
            accepted=False,
            result=None,
            confidence=None,
            reason="no_matching_knowledge",
            refusal_reason="no_matching_knowledge",
            score=None,
            runner_up_score=None,
            score_margin=None,
            score_ratio=None,
            query_coverage=0.0,
            query_terms=query_terms,
            matched_terms=(),
        )

    winner = results[0]
    runner_up = results[1] if len(results) > 1 else None
    matched_terms = tuple(sorted(set(winner.matched_terms)))
    coverage = _query_coverage(query_terms, matched_terms)
    runner_up_score = runner_up.score if runner_up is not None else None
    score_margin = winner.score - runner_up_score if runner_up_score is not None else None
    score_ratio = _score_ratio(winner.score, runner_up_score)

    if winner.confidence not in {"HIGH", "MEDIUM"}:
        return _decision(
            winner,
            accepted=False,
            confidence=None,
            reason="low_base_confidence",
            refusal_reason="insufficient_confidence",
            runner_up_score=runner_up_score,
            score_margin=score_margin,
            score_ratio=score_ratio,
            coverage=coverage,
            query_terms=query_terms,
            matched_terms=matched_terms,
        )

    if winner.confidence == "MEDIUM":
        weak_coverage = len(query_terms) >= 4 and coverage < 0.25
        ambiguous = (
            runner_up is not None
            and runner_up.confidence in {"HIGH", "MEDIUM"}
            and score_ratio is not None
            and score_ratio < 1.15
        )
        if weak_coverage and ambiguous:
            return _decision(
                winner,
                accepted=False,
                confidence=None,
                reason="weak_query_coverage_and_ambiguous_margin",
                refusal_reason="insufficient_confidence",
                runner_up_score=runner_up_score,
                score_margin=score_margin,
                score_ratio=score_ratio,
                coverage=coverage,
                query_terms=query_terms,
                matched_terms=matched_terms,
            )

        reason = (
            "supported_match_clear_margin"
            if score_ratio is not None and score_ratio >= 1.5
            else "supported_match"
        )
        return _decision(
            winner,
            accepted=True,
            confidence="MEDIUM",
            reason=reason,
            refusal_reason=None,
            runner_up_score=runner_up_score,
            score_margin=score_margin,
            score_ratio=score_ratio,
            coverage=coverage,
            query_terms=query_terms,
            matched_terms=matched_terms,
        )

    ambiguous_high = (
        runner_up is not None
        and runner_up.confidence == "HIGH"
        and score_ratio is not None
        and score_ratio < 1.05
        and coverage < 0.5
    )
    if ambiguous_high:
        return _decision(
            winner,
            accepted=True,
            confidence="MEDIUM",
            reason="ambiguous_high_confidence_matches",
            refusal_reason=None,
            runner_up_score=runner_up_score,
            score_margin=score_margin,
            score_ratio=score_ratio,
            coverage=coverage,
            query_terms=query_terms,
            matched_terms=matched_terms,
        )

    reason = (
        "strong_match_clear_margin"
        if score_ratio is not None and score_ratio >= 1.5
        else "strong_match"
    )
    return _decision(
        winner,
        accepted=True,
        confidence="HIGH",
        reason=reason,
        refusal_reason=None,
        runner_up_score=runner_up_score,
        score_margin=score_margin,
        score_ratio=score_ratio,
        coverage=coverage,
        query_terms=query_terms,
        matched_terms=matched_terms,
    )


def _decision(
    winner: SearchResult,
    *,
    accepted: bool,
    confidence: str | None,
    reason: str,
    refusal_reason: str | None,
    runner_up_score: float | None,
    score_margin: float | None,
    score_ratio: float | None,
    coverage: float,
    query_terms: tuple[str, ...],
    matched_terms: tuple[str, ...],
) -> AnswerDecision:
    return AnswerDecision(
        accepted=accepted,
        result=winner if accepted else None,
        confidence=confidence,
        reason=reason,
        refusal_reason=refusal_reason,
        score=winner.score,
        runner_up_score=runner_up_score,
        score_margin=score_margin,
        score_ratio=score_ratio,
        query_coverage=coverage,
        query_terms=query_terms,
        matched_terms=matched_terms,
    )


def _query_terms(query_text: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(expand_query_tokens(tokenize(query_text))))


def _query_coverage(query_terms: tuple[str, ...], matched_terms: tuple[str, ...]) -> float:
    if not query_terms:
        return 0.0
    matched = set(matched_terms)
    return len(set(query_terms).intersection(matched)) / len(set(query_terms))


def _score_ratio(score: float, runner_up_score: float | None) -> float | None:
    if runner_up_score is None:
        return None
    if runner_up_score <= 0:
        return float("inf") if score > 0 else 1.0
    return score / runner_up_score
