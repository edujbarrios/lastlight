# Diagnosis: LastLight 0.2.2 (before 0.3.0 changes)

Recorded against main at `a16c7260992d6af5bdff365204dfac76f2067cfc`, before implementation. No per-case labels or corpus documents from lastlight-bench were inspected.

## Baseline and engineering hypothesis

The independent benchmark README reports BM25 Top-1 **86.1%**, MRR **0.921**, answer precision **92.9%**, answerable recall **48.1%**, refusal recall **100%**, and false acceptance **0%**. These are *external 0.2.2 baseline results*, not results from this branch. They suggest that ranking often identifies the correct source but the current acceptance policy misses evidence in answerable queries.

## Code-path review

- `retrieval/ranking.py`: lexical sums bounded body term frequency, title/tag boosts, text match bonus, and length/priority factors; `confidence_for_score` labels raw scores HIGH at >=1.45 and MEDIUM at >=0.55. BM25 uses per-unit TF and IDF `log(1+(N-df+0.5)/(df+0.5))`, `k1=1.2`, `b=0.75`; title tokens are repeated x3, tags x2. `confidence_for_bm25_score` labels HIGH at >=3 and MEDIUM at >=1. Cross-backend scores are not comparable.
- `retrieval/sections.py`: long documents (>=4000 chars) are split by Markdown heading, then into bounded overlapping chunks (1800 chars / 250 overlap); short documents preserve historical one-unit scoring. `strategies.py` keeps one highest-scoring unit per source, selects one sentence window, and throws away section-path evidence. A supporting paragraph/quantity may be outside that selected window.
- `safety/calibration.py`: independent lexical/BM25 balanced/conservative minimums for normalized strength, original-token coverage, IDF-like weighted coverage, passage coverage and number of discriminative matches. All must pass, potentially compounding false refusals. A near tie adds another hard gate; answer-type sufficiency uses local regex/heuristics. Relevance confidence HIGH is a ranking label, not permission to answer. The score normalization `score/(score+reference)` is not a probability.
- `retrieval/adaptive.py`: survival and resource constraints choose lexical; high/critical risk choose lexical except high risk in accuracy; otherwise BM25. BM25 uses lexical Top-1 identity for post-search verification. Accuracy does not spend extra resources to test multiple supporting passages/candidates.
- `application/app.py`: uses `retrieval_metadata` to choose a decision strategy, passes *full corpus* for DF statistics, and `query()`, `answer()`, `explain()` depend on this common decision layer. Public metadata exposes score, ratio, coverage and reasons but not section, calibrated score or canonical refusal code.

## Design direction (fixed before evaluation)

1. Keep individual ranking algorithms and scores for compatibility. Add deterministic rank fusion (RRF) as a separate strategy. No numeric cross-backend score fusion.
2. Retain short-document behavior; allow configurable section/chunk bounds and preserve heading/source attribution for long documents. Rerank passage windows by **answer-type support** and query evidence, not only dense overlapping keywords.
3. Model a public immutable `CalibrationConfig` with per-backend policies. Prefer separately measurable evidence signals and moderate, bounded support credits over a chain of brittle hard thresholds. Always apply mandatory dynamic/private/authority and missing-requested-fact refusals before score-based acceptance.
4. Return deterministic audit fields and structured refusal codes without breaking existing result shapes or changing the stable legacy refusal enum.
5. Validate against separate **invented** calibration and validation fixtures. Run untouched lastlight-bench only after implementation is frozen. Report results and resource costs; avoid revising the rules based on the 160 external cases.

## Known limitations

Pure lexical evidence detection cannot prove entailment, completeness or validity of a medical instruction. Higher recall must not be presented as infallibility. The independent benchmark is a final evaluation holdout, not calibration data.
