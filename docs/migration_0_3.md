# Migrating from 0.2.2 to 0.3.0

This guide covers the 0.3.0 distribution and its backwards-compatible public APIs.

## Compatibility

The existing `LastLight(knowledge, strategy="lexical"|"bm25"|"adaptive",
decision_profile="balanced"|"conservative")`, `query`, `search`, `answer`,
`explain`, and `plan` methods remain available.

`source.score` is unchanged for lexical and BM25. It is **never a probability**.
When `strategy="hybrid"`, `source.score` is a bounded RRF rank-fusion score,
which must not be numerically compared to BM25 or lexical scores.
Only use `result.accepted` to determine whether to show a grounded passage.

```python
from lastlight import LastLight

old_style = LastLight("pack.zip", strategy="bm25")
answer = old_style.query("How do I store a quartz filter?")
print(answer.accepted, answer.refusal_reason)
```

The safety semantics have improved: more answerable evidence may be recognized
in passage windows, but previous accept/refuse decisions are **not** contractual.
The underlying 0.2.2 deterministic evaluator remains importable from
`lastlight.safety.decision` for specialized legacy integrations; the 0.3.0
application factory uses the improved policy.

## Opt into hybrid retrieval

```python
from lastlight import LastLight

engine = LastLight("pack.zip", strategy="hybrid")
result = engine.query("How is the quartz battery stored?")
if result.accepted:
    print(result.passage)
for source in result.sources:
    print(source.path, source.section, source.backend_scores)
```

Hybrid runs both lexical and BM25 and merges source identities with reciprocal
rank fusion. Duplicate paths within the same pack are collapsed; original raw
backend scores remain in `backend_scores`.

## Customize acceptance or section limits

```python
from lastlight import LastLight, CalibrationConfig, StrategyCalibration, SectionConfig

calibration = CalibrationConfig(
    bm25=StrategyCalibration(
        min_strength=0.48,
        min_evidence_coverage=0.32,
        min_passage_coverage=0.28,
        min_decision_score=0.47,
        ambiguity_ratio=1.08,
    ),
)
engine = LastLight(
    "pack.zip", strategy="bm25",
    decision_profile="balanced",
    calibration=calibration,
    sections=SectionConfig(min_chars=1000, max_chars=1500, overlap_chars=150),
)
result = engine.query("How is the quartz battery stored?")
print(result.decision.refusal_code, result.decision.explanation)
```

The section controls apply to the retriever without altering short documents
whose bodies are below `min_chars`. All section results preserve their source
document and a heading path where applicable.

## Audit fields added

`SourceResult.section`, `SourceResult.backend_scores`, and
`SourceResult.calibrated_score` are optional. `DecisionMetadata` adds
`calibrated_score` in [0,1], `refusal_code`, `explanation` and `section`.
`RetrievalMetadata` keeps the selected strategy and requested strategy
separate; adaptive accuracy can verify more lexical candidates and records the
cost in `verification_candidates` where available.

Old `refusal_reason` remains `no_matching_knowledge` or
`insufficient_confidence`; use the additional `refusal_code` for richer
machine-readable reasons. See [decision calibration](decision_calibration.md).

## Limitations

LastLight remains offline and extractive, not a semantic theorem prover.
Evidence sufficiency is heuristic. A source may be current in its own context
without proving a live status. Always verify critical operational guidance
with a trusted authority.
