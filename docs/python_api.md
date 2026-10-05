# Python API

LastLight is designed as a library-first offline retrieval engine with a first-party CLI on top.

Install it from a local checkout:

```bash
python -m pip install .
```

The runtime still has no third-party dependencies. Installing the package only makes the `lastlight` module and CLI entrypoint available to other Python applications.

## Basic query

```python
from lastlight import LastLight

engine = LastLight(
    knowledge="examplepack/lastlight-example-en.zip",
)

result = engine.query(
    "The water supply is down and I have no bottled water. "
    "I found water that looks clear. What should I do before drinking it?"
)

if result.accepted:
    print(result.confidence)
    print(result.passage)
    for source in result.sources:
        print(source.title, source.path, source.score)
else:
    print("LastLight refused because the mounted knowledge did not support an answer.")
```

`query()` returns a stable `QueryResult` rather than CLI text, so UIs and other integrations do not need to parse terminal output.

## Confidence-aware decisions

LastLight 0.2 separates retrieval confidence from the final answer decision. The final decision combines the winner's strategy-specific confidence with query-term coverage and the score margin to the runner-up from the same retrieval execution.

```python
result = engine.query("How can I make collected water safer to drink?")

decision = result.decision
if decision is not None:
    print(decision.accepted)
    print(decision.confidence)
    print(decision.reason)
    print(decision.query_coverage)
    print(decision.score_margin)
```

The decision layer is deterministic. It does not compare numeric lexical scores with BM25 scores across different searches. A clear high-confidence winner remains `HIGH`; a near-tie between strong candidates can be downgraded to `MEDIUM`; and a weakly covered `MEDIUM` result with a nearly tied alternative can be refused as `insufficient_confidence`.

`search()` remains the raw ranked-source boundary and continues to expose the retrieval strategy's own score and confidence for each source.

## Explain a decision

`explain()` returns the same decision used by `query()` and `answer()`, together with retrieval-policy metadata and the ranked sources that supported it:

```python
explanation = engine.explain(
    "How long will food stay cold during a power outage?"
)

print(explanation.decision.reason)
print(explanation.decision.score)
print(explanation.decision.runner_up_score)
print(explanation.decision.score_ratio)
print(explanation.decision.query_terms)
print(explanation.decision.matched_terms)
print(explanation.retrieval.strategy)
```

This is intended for audit UIs, regression tests, and incident reproduction. It exposes evidence already available to the local runtime; it does not add telemetry or a network dependency.

## Multiple packs

```python
from lastlight import LastLight

engine = LastLight.from_packs(
    [
        "packs/water-en.zip",
        "packs/first-aid-en.zip",
        "packs/blackout-en.zip",
    ],
    strategy="adaptive",
    mode="balanced",
)
```

Packs remain independently versioned even when queried as one local corpus.

## Adaptive retrieval

```python
plan = engine.plan(
    "Someone is bleeding heavily. What should I do while help is on the way?"
)

print(plan.strategy)
print(plan.mode)
print(plan.risk)
print(plan.reason)
```

The public `RetrievalMetadata` contract lets a UI or benchmark display the planner decision without reaching into retrieval internals.

## Public contracts

The package root intentionally exposes a small API:

```python
from lastlight import (
    DecisionMetadata,
    LastLight,
    QueryExplanation,
    QueryResult,
    RetrievalMetadata,
    SourceResult,
)
```

Companion projects such as `lastlight-ui` and `lastlight-bench` should depend on these public contracts instead of importing modules from `lastlight.application`, `lastlight.retrieval`, or `lastlight.knowledge` directly.

Internal modules can then be refactored without forcing every ecosystem repository to change at the same time.

## CLI

Installing the package also installs the first-party CLI:

```bash
lastlight --help
lastlight --knowledge pack.zip "How can I make collected water safer to drink?"
```

The CLI uses the same public `LastLight` facade as other consumers. `python src/main.py ...` remains available when running directly from a source checkout.

## Distribution

This document covers local package installation only. Publishing releases to PyPI is a separate release concern and is intentionally handled independently from the runtime/library architecture.
