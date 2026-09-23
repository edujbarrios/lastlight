# LastLight

[![PyPI version](https://img.shields.io/pypi/v/lastlight.svg)](https://pypi.org/project/lastlight/)
[![Python versions](https://img.shields.io/pypi/pyversions/lastlight.svg)](https://pypi.org/project/lastlight/)

**A stdlib-only Python library for low-power, offline retrieval in disaster and infrastructure-failure scenarios.**

Most modern AI systems assume that connectivity, cloud compute, large models and abundant power are available. LastLight explores the reverse case: **how much useful, auditable assistance can remain available when the infrastructure itself is unreliable?**

LastLight retrieves practical knowledge from local Markdown/ZIP packs, exposes source passages and ranking metadata, adapts retrieval strategy to resource policy, and refuses when the available evidence is too weak to support an answer.

No cloud API. No embeddings. No vector database. No telemetry. No runtime dependencies outside the Python standard library.

## Install

LastLight is published on [PyPI](https://pypi.org/project/lastlight/):

```bash
python -m pip install lastlight
```

Python 3.10+ is supported.

For development from a checkout:

```bash
python -m pip install -e .
```

## Try it in 30 seconds

Download the small demo knowledge pack used by the examples:

```bash
curl -L \
  https://raw.githubusercontent.com/edujbarrios/lastlight/main/examplepack/lastlight-example-en.zip \
  -o lastlight-example-en.zip
```

Then use LastLight as a normal Python library:

```python
from lastlight import LastLight

query = (
    "Someone has a deep cut and is bleeding heavily. "
    "What should I do while waiting for emergency services?"
)

engine = LastLight(
    "lastlight-example-en.zip",
    strategy="lexical",
)

result = engine.query(query)

print(result.accepted)
print(result.confidence)
print(result.sources[0].title)
print(f"{result.sources[0].score:.3f}")
print(result.passage)
```

Observed output:

```text
True
HIGH
Severe external bleeding
2.748
For life-threatening external bleeding, call emergency services as soon as possible. Apply firm, continuous direct pressure to the wound with a dressing or clean material.
```

The source object remains available for attribution and inspection:

```python
source = result.sources[0]

print(source.path)
print(source.language)
print(source.tags)
print(source.matched_terms)
```

```text
lastlight-example-en.zip:en/first-aid/severe-bleeding.md
en
('first-aid', 'bleeding', 'hemorrhage')
('bleeding', 'emergency', 'services', 'waiting')
```

Once the package and knowledge pack are local, querying does not require a network connection.

## Confidence-aware refusal

LastLight does not turn every weak match into an answer. The public result makes that decision explicit:

```python
from lastlight import LastLight

engine = LastLight("lastlight-example-en.zip")

result = engine.query(
    "How do I repair a diesel engine that will not start?"
)

print(result.accepted)
print(result.confidence)
print(result.passage)
```

```text
False
None
None
```

A refused query may still contain LOW-confidence retrieval candidates in `result.sources`; callers should use `result.accepted` as the answer boundary.

## Public Python API

The library is designed around a small public surface:

```python
from lastlight import (
    LastLight,
    QueryResult,
    RetrievalMetadata,
    SourceResult,
)
```

The main operations are:

```python
engine.query(text)   # structured QueryResult
engine.search(text)  # ranked retrieval results
engine.answer(text)  # formatted text response
engine.plan(text)    # adaptive retrieval plan
```

`QueryResult`, `SourceResult`, and `RetrievalMetadata` are the stable contracts intended for UIs, benchmarks and other companion repositories. See [Python API](docs/python_api.md).

## Compare retrieval strategies

LastLight exposes two fixed retrieval strategies plus an adaptive planner. The examples below are verified against the built wheel in CI so the README stays tied to the packaged library rather than only to the source tree.

This query has an immediately useful answer and is also useful for comparing ranking behavior:

```python
from lastlight import LastLight

query = (
    "The power has been out for several hours. "
    "How long will food stay safe in my refrigerator if I keep the door closed?"
)
```

### Lexical vs BM25

```python
for strategy in ("lexical", "bm25"):
    result = LastLight(
        "lastlight-example-en.zip",
        strategy=strategy,
    ).query(query)

    source = result.sources[0]
    print(
        strategy,
        source.title,
        f"score={source.score:.3f}",
        source.confidence,
    )
    print(result.passage)
```

Observed output:

```text
lexical Food safety during a power outage score=4.918 HIGH
Keep refrigerator and freezer doors closed as much as possible. As a reference, an unopened refrigerator keeps food cold for about 4 hours.

bm25 Food safety during a power outage score=11.475 HIGH
Keep refrigerator and freezer doors closed as much as possible. As a reference, an unopened refrigerator keeps food cold for about 4 hours.
```

The numeric score scales are strategy-specific, so `4.918` and `11.475` should **not** be compared directly. What matters is ranking and confidence within each retrieval strategy.

### Adaptive strategy selection

Adaptive mode does not blend lexical and BM25 scores. It deterministically chooses a retrieval strategy from query risk, operating mode and resource policy.

```python
for mode in ("survival", "balanced", "accuracy"):
    plan = LastLight(
        "lastlight-example-en.zip",
        strategy="adaptive",
        mode=mode,
    ).plan(query)

    print(
        mode,
        plan.strategy,
        plan.effective_top_k,
        plan.risk,
        plan.reason,
    )
```

Observed decisions:

```text
survival lexical 2 normal survival mode caps retrieval cost
balanced bm25 3 normal balanced mode with sufficient detected resources
accuracy bm25 3 normal accuracy mode with no active resource constraint
```

The same query therefore demonstrates the trade-off clearly: `survival` caps retrieval cost with lexical search, while `balanced` and `accuracy` can choose BM25 when resources allow it.

Explicit resource budgets can change the plan:

```python
plan = LastLight(
    "lastlight-example-en.zip",
    strategy="adaptive",
    mode="balanced",
    energy_budget_mwh=0.4,
).plan(query)

print(plan.strategy)
print(plan.effective_top_k)
print(plan.reason)
```

```text
lexical
2
energy budget is at or below 0.5 mWh/query
```

See [Adaptive Retrieval](docs/adaptive_retrieval.md) for the complete decision order and policy thresholds.

## Use multiple knowledge packs

Packs remain independently versioned and distributable, while the library can search several as one local corpus:

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

result = engine.query(
    "Someone is bleeding heavily and the power is out. "
    "What guidance is available?"
)

for source in result.sources:
    print(source.path, source.confidence, source.score)
```

This is the intended integration point for projects such as `lastlight-ui` or `lastlight-bench`: they import the library instead of spawning and parsing the CLI.

## Knowledge packs

LastLight does not ship a fixed emergency corpus. Runtime knowledge is external and can be distributed separately from the Python package.

A typical pack looks like:

```text
water-en.zip
├── lastlight-pack.json
├── en/
│   └── water/
│       ├── purification.md
│       └── storage.md
└── sources/
    └── references.json
```

[`knowledge/README.md`](knowledge/README.md) documents the pack format. See also [Knowledge Packs](docs/knowledge_packs.md) and [Knowledge Pack Provenance](docs/pack_provenance.md).

## Language behavior

Language selection is also available from the library:

```python
engine = LastLight(
    "pack.zip",
    language="es",
)
```

An explicit language always wins. Without one, LastLight adopts a monolingual corpus language automatically and conservatively routes clear Spanish/English queries inside mixed corpora. Retrieved passages remain in their original language; LastLight does not silently translate them.

## CLI utilities

The CLI remains a first-party interface, but it is secondary to the Python API. Installing from PyPI also installs the `lastlight` command.

Useful operational commands include:

```bash
lastlight --help
lastlight --knowledge pack.zip --validate-pack
lastlight --knowledge pack.zip --verify-provenance
lastlight --knowledge pack.zip --format sources "How can I make this water safer?"
```

The CLI and the Python API use the same runtime implementation.

## Development and verification

From a checkout:

```bash
git clone https://github.com/edujbarrios/lastlight.git
cd lastlight
python -m pip install -e .
python tools/check_core.py
```

CI verifies Python 3.10 and 3.12, builds wheel and source distributions, installs the built wheel in an isolated environment, and executes the library examples for lexical retrieval, BM25 retrieval, adaptive planning and refusal behavior.

## Research direction

LastLight treats offline intelligence as a systems problem rather than a model-size competition:

> How much useful, trustworthy assistance can be preserved per unit of compute, memory, energy and stored knowledge when external infrastructure is unavailable?

The project is intended to make that trade-off measurable and auditable rather than hiding it behind a remote service.

## Ecosystem direction

The runtime is library-first so companion projects can depend on a stable Python API:

```text
lastlight-ui ──────► lastlight
lastlight-bench ───► lastlight
other integrations ► lastlight
```

Knowledge packs, pack-authoring tools and a future catalog can evolve independently around the same pack contract. See [Ecosystem](ECOSYSTEM.md).

## Docs

- [Python API](docs/python_api.md)
- [Architecture](docs/architecture.md)
- [Knowledge Packs](docs/knowledge_packs.md)
- [Knowledge Pack Provenance](docs/pack_provenance.md)
- [Adaptive Retrieval](docs/adaptive_retrieval.md)
- [Ecosystem](ECOSYSTEM.md)

## License

Mozilla Public License 2.0.
