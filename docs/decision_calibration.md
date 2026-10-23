# Decision calibration (independent of lastlight-bench)

This is an **offline, deterministic evidence acceptance policy**. Retrieval and
answerability are intentionally separate. No benchmark queries, answers or labels
from lastlight-bench were used for these rules or thresholds. The entirely
invented cobalt/copper corpus in tests/test_synthetic_calibration.py is a
**calibration/development fixture**, not a held-out final evaluation set. Never
select thresholds by repeatedly inspecting final benchmark errors.

## Four distinct quantities

1. **Relevance**: the existing backend's search score and lexical/BM25
   confidence for a *document*. Unchanged by this feature.
2. **Evidence sufficiency**: presence of query-specific support **in the
   selected passage** (time, quantity, role/identity, negation or list items),
   plus passage query-term coverage. A title or tag alone is not sufficient.
3. **Answer confidence**: only assigned after all acceptance gates. It may be
   MEDIUM despite a retrieved HIGH ranking. It is **not** a calibrated probability.
4. **Accept/reject**: deterministic refusal with an auditable reason. Refusals
   mean "cannot establish from this pack", not "the claim is false".

Raw retrieval is available through search() regardless of whether query()
refuses. Exact and IDF-weighted query coverage operate on original query
concepts; query aliases are match alternatives rather than extra denominator
terms. Rare terms are weighted by corpus document frequency, while constraints,
negations and quantities receive additional weight. Capitalized entities
receive a conservative heuristic boost. This is not linguistic entailment.

## Decision thresholds

Policy constants live in lastlight.safety.calibration.THRESHOLDS and have
corresponding synthetic unit tests. strength = score/(score + reference), with
**reference 0.65 lexical; 3.0 BM25**. These are *different* backend evidence
scales, not cross-backend probabilities. Margin/ratio are interpreted **only
within the same backend**, never combined across backends.

| Selected retrieval | Profile | Min strength | Min query coverage | Min weighted coverage | Min passage coverage | Min discriminative matches |
|---|---|---:|---:|---:|---:|---:|
| lexical | balanced | .35 | .20 | .22 | .13 | 1 |
| lexical | conservative | .50 | .35 | .45 | .40 | 2 |
| bm25 | balanced | .44 | .40 | .52 | .30 | 2 |
| bm25 | conservative | .55 | .50 | .65 | .45 | 2 |

In the balanced profile, explicitly pertinent temporal or quantity evidence may contribute a small +.03 credit to the passage-coverage gate after the independent sufficiency check; this never relaxes the conservative profile or risk rules.\n\nHigh-risk queries add +.03 and critical ones +.05 to weighted and passage
coverage requirements. A near tie (ratio under 1.12 for BM25) requires very
strong coverage or is refused. A clear margin is *not* sufficient on its own.
With BM25 + lexical verification disagreement, confidence is downgraded, or
the query is refused in conservative/high-risk mode.

### Adaptive mode

The adaptive planner still chooses BM25 or lexical according to its existing
energy/memory/risk policy. The **selected backend** is in
retrieval.strategy; the **requested strategy** in
retrieval.requested_strategy; the independent **decision profile** in
retrieval.decision_profile. BM25 may use a lexical top-1 cross-check only when
the primary BM25 path was already permitted. The cross-check uses document
identity, **never numeric score fusion**. Critical and high-risk queries
receive stricter decision evidence gates even under balanced.

### Unsupported and incomplete evidence

Time-relative mutable requests (today, right now, latest, current inventory,
remaining stock, future availability) and sensitive requests (secrets,
personal/private data, certification, prescribing and dose decisions) fail
closed. A static pack, even one with a printed date, cannot verify *live*
status or authorization. Nonvolatile historical evidence may still be
returned if it directly supports a noncurrent question.

Quantity questions need relevant quantities, temporal questions a pertinent
interval/condition, role questions an explicit identity/function, negations
an explicit negative rule, and list requests enough enumerated items. These
checks are deliberately conservative heuristics; no answer is generated or
inferred from outside the local passage.

## Running and evaluating

Run the synthetic development suite independently:

    python -m unittest discover -s tests -p 'test_synthetic_calibration.py'

Keep the final evaluation holdout **outside this repository and outside
threshold selection**. Report answerable recall, false acceptance, refusal
recall and top-1 ranking quality separately on the final holdout. Changes
to the development suite are not evidence of benchmark improvement.

Passage selection excludes heading-only windows if substantive text exists; headings may aid ranking but never substitute for answer-bearing evidence. Original backend token coverage also guards against weak near ties even when passage vocabulary is richer than matched_terms.
