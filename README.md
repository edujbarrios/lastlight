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
en/first-aid/severe-bleeding.md
en
('first-aid', 'bleeding', 'hemorrhage')
('bleeding', 'emergency', 'services', 'waiting')
```

Source paths are **pack-relative and stable**: the same document keeps the same logical path whether the pack is a directory, a ZIP file, or the ZIP is renamed. Pack identity metadata (`pack_name`, `pack_version`, `pack_source`, and `pack_path`) is preserved consistently whether one pack or several packs are mounted. Once the package and knowledge pack are local, querying does not require a network connection.

## Confidence-aware refusal

LastLight does not turn every weak match into an answer. The public result makes that decision explicit:

```python
from lastlight import LastLight

engine = LastLight("lastlight-example-en.zip")
result = engine.query("How do I repair a diesel engine that will not start?")

print(result.accepted)
print(result.confidence)
print(result.passage)
print(result.refusal_reason)
```

```text
False
None
None
no_matching_knowledge
```

Callers should use `result.accepted` as the answer boundary rather than treating every retrieval candidate as an answer.

## Public Python API

The library is designed around a small public surface:

```python
from lastlight import (
    LastLight,
    QueryResult,
    RetrievalMetadata,
    SourceResult,
    PackInfo,
    PackValidation,
    PackProvenance,
)
```

The main operations are:

```python
engine.query(text)            # structured QueryResult
engine.search(text)           # ranked SourceResult values
engine.answer(text)           # formatted text response
engine.plan(text)             # adaptive retrieval metadata
engine.packs()                # mounted pack metadata
engine.validate_packs()       # structured validation reports
engine.verify_provenance()    # integrity/freshness reports
```

These package-root contracts are the intended integration boundary for UIs, benchmarks and other companion repositories. Explicit knowledge sources are validated at this public boundary, so missing, empty, or unsupported paths fail fast instead of looking like empty retrieval results. Public retrieval methods also require `top_k` to be an integer greater than or equal to 1. See [Python API](docs/python_api.md).

## Compare retrieval strategies

LastLight exposes two fixed retrieval strategies plus an adaptive planner. The examples below are checked against the built wheel in CI.

```python
from lastlight import LastLight

query = (
    "The power has been out for several hours. "
    "How long will food stay safe in my refrigerator if I keep the door closed?"
)

for strategy in ("lexical", "bm25"):
    result = LastLight(
        "lastlight-example-en.zip",
        strategy=strategy,
    ).query(query)

    source = result.sources[0]
    print(strategy, source.title, f"score={source.score:.3f}", source.confidence)
    print(result.passage)
```

Observed output:

```text
lexical Food safety during a power outage score=4.918 HIGH
Keep refrigerator and freezer doors closed as much as possible. As a reference, an unopened refrigerator keeps food cold for about 4 hours.

bm25 Food safety during a power outage score=11.475 HIGH
Keep refrigerator and freezer doors closed as much as possible. As a reference, an unopened refrigerator keeps food cold for about 4 hours.
```

Score scales are strategy-specific, so lexical and BM25 numeric scores should **not** be compared directly.

### Adaptive strategy selection

Adaptive mode does not blend lexical and BM25 scores. It deterministically chooses a retrieval strategy from query risk, operating mode and resource policy.

```python
for mode in ("survival", "balanced", "accuracy"):
    plan = LastLight(
        "lastlight-example-en.zip",
        strategy="adaptive",
        mode=mode,
    ).plan(query)

    print(mode, plan.strategy, plan.effective_top_k, plan.risk, plan.reason)
```

Observed decisions:

```text
survival lexical 2 normal survival mode caps retrieval cost
balanced bm25 3 normal balanced mode with sufficient detected resources
accuracy bm25 3 normal accuracy mode with no active resource constraint
```

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

See [Adaptive Retrieval](docs/adaptive_retrieval.md) for the decision order and policy thresholds.

## Use multiple knowledge packs

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

result = engine.query("Someone is bleeding heavily. What guidance is available?")

for source in result.sources:
    print(source.pack_name, source.path, source.confidence, source.score)
```

This is the intended integration point for projects such as `lastlight-ui` and `lastlight-bench`: import the library instead of spawning and parsing the CLI.

## Knowledge Pack Format v1

Distributable LastLight packs use an explicit versioned manifest contract. A typical pack looks like:

```text
water-en.zip
├── lastlight-pack.json
└── en/
    └── water/
        ├── purification.md
        └── storage.md
```

A minimal manifest starts with:

```json
{
  "format_version": 1,
  "name": "Emergency Water EN",
  "version": "1.0.0",
  "languages": ["en"],
  "license": "CC-BY-4.0",
  "source": "https://example.org/water"
}
```

`format_version` identifies the LastLight pack schema; `version` identifies the knowledge content release. Validation checks the schema version, required field types, semantic content version, language codes, provenance entries and optional SHA-256 fingerprints.

Pack loading rejects unsafe ZIP paths and duplicate normalized archive members, limits uncompressed Markdown sizes/counts, and applies a manifest size limit in both ZIP and directory packs. Directory manifests and Markdown documents may not escape the pack root through symlinks. Directory and ZIP packs also use matching Markdown-discovery rules, including case-insensitive `.md` extensions and ignoring hidden/`__MACOSX` metadata paths. Malformed pack data is reported through the public `PackError` hierarchy.

See [Knowledge Packs](docs/knowledge_packs.md) and [Knowledge Pack Provenance](docs/pack_provenance.md).

## Core evaluation gate

LastLight ships a small deterministic evaluation suite **inside the installed package**. It covers answerable queries and expected refusals against the example corpus. CI runs the same suite on Python 3.10, 3.11 and 3.12 and blocks regressions below the core thresholds for top-1 accuracy, answer precision, refusal recall and answerable recall.

The larger stress, hardware and energy benchmark suites belong in `lastlight-bench`; the core suite is deliberately small and release-oriented.

From a checkout you can also run:

```bash
lastlight --knowledge examplepack/lastlight-example-en.zip --eval
```

## Language behavior

```python
engine = LastLight(
    "pack.zip",
    language="es",
)
```

An explicit language always wins. Without one, LastLight adopts a monolingual corpus language automatically and conservatively routes clear Spanish/English queries inside mixed corpora. Retrieved passages remain in their original language; LastLight does not silently translate them.

## CLI utilities

The CLI is a first-party interface but remains secondary to the Python API. Installing from PyPI also installs the `lastlight` command.

```bash
lastlight --help
lastlight --knowledge pack.zip --validate-pack
lastlight --knowledge pack.zip --verify-provenance
lastlight --knowledge pack.zip --format sources "How can I make this water safer?"
```

## Development and verification

```bash
git clone https://github.com/edujbarrios/lastlight.git
cd lastlight
python -m pip install -e .
python tools/check_core.py
```

CI tests Python 3.10, 3.11 and 3.12, runs the core evaluation gate, builds wheel and source distributions, validates package metadata, installs the built wheel in isolation, verifies packaged resources and executes the documented library behavior.

## Research direction

LastLight treats offline intelligence as a systems problem rather than a model-size competition:

> How much useful, trustworthy assistance can be preserved per unit of compute, memory, energy and stored knowledge when external infrastructure is unavailable?

The project is intended to make that trade-off measurable and auditable rather than hiding it behind a remote service.

## Ecosystem direction

```text
lastlight-ui ──────► lastlight
lastlight-bench ───► lastlight
other integrations ► lastlight
```

Knowledge packs, pack-authoring tools and a future catalog can evolve independently around the Pack Format v1 contract. See [Ecosystem](ECOSYSTEM.md).

## Docs

- [Python API](docs/python_api.md)
- [Architecture](docs/architecture.md)
- [Knowledge Packs](docs/knowledge_packs.md)
- [Knowledge Pack Provenance](docs/pack_provenance.md)
- [Adaptive Retrieval](docs/adaptive_retrieval.md)
- [Ecosystem](ECOSYSTEM.md)

## License

Mozilla Public License 2.0.
