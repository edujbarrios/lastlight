"""Compatibility module: deterministic calibrated answer acceptance."""

from .calibration import AnswerDecision, DecisionThresholds, THRESHOLDS, evaluate_answer_decision

__all__ = ["AnswerDecision", "DecisionThresholds", "THRESHOLDS", "evaluate_answer_decision"]
