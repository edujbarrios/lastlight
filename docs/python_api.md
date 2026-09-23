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
    LastLight,
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
