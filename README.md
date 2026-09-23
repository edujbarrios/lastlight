# LastLight

[![PyPI version](https://img.shields.io/pypi/v/lastlight.svg)](https://pypi.org/project/lastlight/)
[![Python versions](https://img.shields.io/pypi/pyversions/lastlight.svg)](https://pypi.org/project/lastlight/)

**A stdlib-only Python library for low-power, offline retrieval in disaster and infrastructure-failure scenarios.**

Most modern AI systems assume that connectivity, cloud compute, large models and abundant power are available. LastLight explores the reverse case: **how much useful, auditable assistance can remain available when the infrastructure itself is unreliable?**

LastLight is intentionally narrow. It retrieves practical knowledge from local Markdown/ZIP packs, exposes the source passages and ranking metadata, adapts retrieval strategy to resource policy, and refuses when the available evidence is too weak to support an answer.

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

Download the small demo knowledge pack used by the repository examples:

```bash
curl -L \
  https://raw.githubusercontent.com/edujbarrios/lastlight/main/examplepack/lastlight-example-en.zip \
  -o lastlight-example-en.zip
```

Then use LastLight as a normal Python library:

```python
from lastlight import LastLight

query = (
    "The water supply is down and I have no bottled water. "
    "I found water that looks clear. What should I do before drinking it?"
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

Observed with the published `lastlight 0.1.0` wheel:

```text
True
HIGH
Safe water during an emergency
2.539
If safe bottled water is not available, bring clear water to a rolling boil for 1 minute. At elevations above 6,500 feet (about 2,000 meters), boil water for 3 minutes. Let it cool and store it in clean, sanitized containers with tight covers.
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
lastlight-example-en.zip:en/water/purification.md
en
('water', 'purification', 'emergency')
('before', 'bottled', 'clear', 'that', 'water')
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
engine.search(text)  # ranked SourceResult-compatible search results
engine.answer(text)  # formatted text response
engine.plan(text)    # RetrievalMetadata for adaptive retrieval
```

`QueryResult`, `SourceResult`, and `RetrievalMetadata` are the stable contracts intended for UIs, benchmarks and other companion repositories. See [Python API](docs/python_api.md).

## Compare retrieval strategies

LastLight exposes two fixed retrieval strategies plus an adaptive planner. The examples below are executed against the installed wheel in CI so README behavior stays tied to the packaged library, not only to the source tree.

### Lexical vs BM25

```python
from lastlight import LastLight

query = (
    "The water supply is down and I have no bottled water. "
    "I found water that looks clear. What should I do before drinking it?"
)

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
```

Observed output:

```text
lexical Safe water during an emergency score=2.539 HIGH
bm25 Safe water during an emergency score=7.159 HIGH
```

The numeric score scales are strategy-specific, so `2.539` and `7.159` should **not** be compared directly. What matters is ranking and confidence within each retrieval strategy.

### Adaptive strategy selection

Adaptive mode does not blend lexical and BM25 scores. It deterministically chooses a retrieval strategy from the query risk, operating mode and resource policy.

```python
from lastlight import LastLight

query = (
    "The water supply is down and I have no bottled water. "
    "I found water that looks clear. What should I do before drinking it?"
)

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

Observed decisions for this high-risk water query:

```text
survival lexical 2 high survival mode caps retrieval cost
balanced lexical 3 high high-risk query in a safety-first mode
accuracy bm25 3 high accuracy mode with no active resource constraint
```

The same `balanced` mode can choose BM25 for a normal-risk query:

```python
food_query = (
    "The power has been out for several hours. "
    "How long will food stay safe in my refrigerator if I keep the door closed?"
)

plan = LastLight(
    "lastlight-example-en.zip",
    strategy="adaptive",
    mode="balanced",
).plan(food_query)

print(plan.strategy)
print(plan.risk)
print(plan.reason)
```

```text
bm25
normal
balanced mode with sufficient detected resources
```

Explicit resource budgets can change the plan:

```python
plan = LastLight(
    "lastlight-example-en.zip",
    strategy="adaptive",
    mode="balanced",
    energy_budget_mwh=0.4,
).plan(food_query)

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

This is the intended integration point for projects such as a future `lastlight-ui` or `lastlight-bench`: they import the library rather than spawning and parsing the CLI.

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

CI currently verifies Python 3.10 and 3.12, builds wheel and source distributions, installs the built wheel in an isolated environment, and executes the library examples for lexical retrieval, BM25 retrieval, adaptive planning and refusal behavior.

## Research direction

LastLight treats offline intelligence as a systems problem rather than a model-size competition:

> How much useful, trustworthy assistance can be preserved per unit of compute, memory, energy and stored knowledge when external infrastructure is unavailable?

The project is intended to make that tradeoff measurable and auditable rather than hiding it behind a remote service.

## Ecosystem direction

The runtime is now library-first so companion projects can depend on a stable Python API:

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
