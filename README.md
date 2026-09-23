# LastLight

**Low-power, offline retrieval for disaster and infrastructure-failure guidance.**

Most modern AI research moves in one direction: larger models, larger context windows, more accelerators, more memory, and increasingly capable cloud infrastructure. That direction is useful, but it leaves a different question relatively unexplored: **what happens when the infrastructure itself is the problem?**

LastLight explores the reverse case. It asks how much useful machine-assisted reasoning can remain available when connectivity is unreliable or absent, power is scarce, hardware is modest, and a remote model cannot be assumed to exist.

The goal is not to reproduce a general-purpose cloud LLM on a tiny device. LastLight is designed for a narrower and more auditable job: **retrieve practical knowledge locally, show where it came from, operate within strict resource constraints, and refuse when the available evidence is not strong enough to support an answer.**

That makes it useful for scenarios such as prolonged outages, damaged communications infrastructure, remote field work, low-power devices, emergency preparation, or any environment where access to external services cannot be guaranteed.

LastLight works entirely from local knowledge packs. A device can carry one or several independently versioned packs—for example water, first aid, blackout procedures, communications, or navigation—and search them together without requiring a network connection.

No cloud API. No embeddings. No vector database. No telemetry. No package install required.

> Inspired by the resource-scarcity premise of *This War of Mine*. LastLight is an independent project and is not affiliated with the game or its creators.

## What LastLight provides

- mount **one or multiple** directory/ZIP knowledge packs at once
- deterministic lexical, BM25 and resource-adaptive retrieval
- sourced passages with pack and document traceability
- confidence-aware refusal instead of fabricating unsupported answers
- ES/EN language routing without silently translating source material
- pack metadata, validation, SHA-256 integrity, provenance and freshness checks
- a stdlib-only CLI suitable for constrained and disconnected systems

## Use LastLight as a Python library

LastLight is library-first: the CLI is a first-party client of the same public Python API that can be used by `lastlight-ui`, `lastlight-bench`, or other integrations.

Install it from a checkout:

```bash
python -m pip install .
```

Then query a local pack without parsing CLI output:

```python
from lastlight import LastLight

engine = LastLight(
    knowledge="examplepack/lastlight-example-en.zip",
    strategy="adaptive",
    mode="balanced",
)

result = engine.query(
    "The water supply is down and I have no bottled water. "
    "I found water that looks clear. What should I do before drinking it?"
)

if result.accepted:
    print(result.confidence)
    print(result.passage)
    print(result.sources[0].path)
```

`QueryResult`, `SourceResult`, and `RetrievalMetadata` are stable public contracts intended for companion repositories. See [Python API](docs/python_api.md) for multi-pack and adaptive examples.

## Try it in 30 seconds

The repository includes one deliberately small English demo archive at [`examplepack/lastlight-example-en.zip`](examplepack/lastlight-example-en.zip). It exists only so a new visitor can understand the system without downloading anything else.

```bash
git clone https://github.com/edujbarrios/lastlight.git
cd lastlight

python src/main.py \
  --knowledge examplepack/lastlight-example-en.zip \
  --validate-pack
```

```text
Pack validation: PASS
```

Ask a natural-language question and inspect the ranked source:

```bash
python src/main.py \
  --knowledge examplepack/lastlight-example-en.zip \
  --format sources \
  "The water supply is down and I have no bottled water. I found water that looks clear. What should I do before drinking it?"
```

Current default lexical result:

```text
Sources for: The water supply is down and I have no bottled water. I found water that looks clear. What should I do before drinking it?
1. [HIGH] Safe water during an emergency | lastlight-example-en.zip:en/water/purification.md | score=2.539 | tags=water, purification, emergency
```

The same question in normal text mode retrieves this answer:

```text
LastLight is experimental and retrieval-only. It shows sourced passages; it does not replace professional emergency guidance.

[HIGH CONFIDENCE]

Title: Safe water during an emergency
Source: lastlight-example-en.zip:en/water/purification.md
Language: en
Tags: water, purification, emergency

Passage:
If safe bottled water is not available, bring clear water to a rolling boil for 1 minute. At elevations above 6,500 feet (about 2,000 meters), boil water for 3 minutes. Let it cool and store it in clean, sanitized containers with tight covers.

Experimental offline research tool. Verify critical decisions with trusted human expertise whenever possible.

Follow-up checks:
- Does the water smell like fuel, chemicals, sewage, or solvents?
- Can you boil it, or do you only have filters, cloth, or disinfectant?
```

And when the pack does not contain enough evidence for the question, LastLight refuses instead of inventing an answer:

```bash
python src/main.py \
  --knowledge examplepack/lastlight-example-en.zip \
  "How do I repair a diesel engine that will not start?"
```

```text
I do not have enough confidence to answer this question from the current knowledge base.
```

## Compare retrieval strategies

LastLight exposes two fixed retrieval strategies and one adaptive policy. Adaptive retrieval is **strategy selection**, not a hidden model or a simultaneous blend of lexical and BM25 scores: it deterministically chooses the retrieval path for the current query and resource policy.

Using the same natural-language water query, fixed lexical retrieval returns the source above with a lexical score of `2.539`:

```bash
python src/main.py \
  --knowledge examplepack/lastlight-example-en.zip \
  --strategy lexical \
  --format sources \
  "The water supply is down and I have no bottled water. I found water that looks clear. What should I do before drinking it?"
```

Fixed BM25 ranks the same document first, using its own scoring scale:

```bash
python src/main.py \
  --knowledge examplepack/lastlight-example-en.zip \
  --strategy bm25 \
  --format sources \
  "The water supply is down and I have no bottled water. I found water that looks clear. What should I do before drinking it?"
```

```text
1. [HIGH] Safe water during an emergency | lastlight-example-en.zip:en/water/purification.md | score=7.159 | tags=water, purification, emergency
```

The numeric scores are **not comparable across lexical and BM25**; only ranking and confidence within each strategy are meaningful.

Adaptive mode makes the choice explicit. For this water query, the planner classifies the query as `high` risk:

| Mode | Selected strategy | Effective top-k | Why |
| --- | --- | ---: | --- |
| `survival` | lexical | 2 | caps retrieval cost |
| `balanced` | lexical | 3 | keeps high-risk queries on the safety-first path |
| `accuracy` | BM25 | 3 | uses BM25 when unconstrained and the query is not critical |

Inspect the decision directly:

```bash
python src/main.py \
  --knowledge examplepack/lastlight-example-en.zip \
  --strategy adaptive \
  --mode balanced \
  --plan \
  "The water supply is down and I have no bottled water. I found water that looks clear. What should I do before drinking it?"
```

Stable fields from the plan are:

```json
{
  "effective_top_k": 3,
  "mode": "balanced",
  "reason": "high-risk query in a safety-first mode",
  "risk": "high",
  "strategy": "lexical"
}
```

For a normal-risk query, balanced mode can switch to BM25:

```bash
python src/main.py \
  --knowledge examplepack/lastlight-example-en.zip \
  --strategy adaptive \
  --mode balanced \
  --plan \
  "The power has been out for several hours. How long will food stay safe in my refrigerator if I keep the door closed?"
```

```json
{
  "mode": "balanced",
  "reason": "balanced mode with sufficient detected resources",
  "risk": "normal",
  "strategy": "bm25"
}
```

Tight explicit budgets override the normal policy and force the lower-cost lexical path:

```bash
python src/main.py \
  --knowledge examplepack/lastlight-example-en.zip \
  --strategy adaptive \
  --mode balanced \
  --energy-budget-mwh 0.4 \
  --plan \
  "The power has been out for several hours. How long will food stay safe in my refrigerator if I keep the door closed?"
```

See [Adaptive Retrieval](docs/adaptive_retrieval.md) for the complete decision order and resource-policy thresholds.

The example pack is **onboarding data, not the distribution model**. Maintained knowledge packs, the UI, pack-authoring tools and the future catalog are intended to evolve in separate companion repositories. See [Ecosystem](ECOSYSTEM.md).

## Use your own knowledge packs

LastLight does not ship a fixed emergency corpus. [`knowledge/README.md`](knowledge/README.md) documents the pack format; real knowledge can be distributed and updated independently from the runtime.

One pack:

```bash
python src/main.py \
  --knowledge packs/water-en.zip \
  "We have no running water after the outage. How can I make collected water safer to drink?"
```

`--knowledge` is repeatable. Packs remain independent while LastLight searches them as one local corpus:

```bash
python src/main.py \
  --knowledge packs/water-en.zip \
  --knowledge packs/first-aid-en.zip \
  --knowledge packs/blackout-en.zip \
  "Someone is bleeding heavily and the power is out. What guidance is available?"
```

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

Verify a downloaded pack before using it:

```bash
python src/main.py --knowledge pack.zip --validate-pack
python src/main.py --knowledge pack.zip --verify-provenance
```

See [Knowledge Packs](docs/knowledge_packs.md) and [Knowledge Pack Provenance](docs/pack_provenance.md).

## Language behavior

Explicit `--language es` / `--language en` always wins. Without it, LastLight adopts a monolingual corpus language automatically and conservatively routes clear ES/EN queries inside mixed corpora. Retrieved passages remain in the original pack language; LastLight does not silently translate them.

## Evaluation

`--eval` runs a small deterministic regression suite for retrieval and refusal behavior.

```bash
python src/main.py --knowledge examplepack/lastlight-example-en.zip --eval
```

The committed example ZIP also has integration coverage for pack validation, HIGH-confidence water and bleeding retrieval, and an out-of-domain refusal case.

## Useful commands

| Task | Command |
| --- | --- |
| Try the bundled demo | `python src/main.py --knowledge examplepack/lastlight-example-en.zip "The water supply is down and I have no bottled water. I found water that looks clear. What should I do before drinking it?"` |
| One external pack | `python src/main.py --knowledge water.zip "What should I do if the water supply is unsafe?"` |
| Multiple packs | `python src/main.py --knowledge water.zip --knowledge first-aid.zip "What guidance do I have for safe water and a serious wound?"` |
| Fixed lexical | `python src/main.py --knowledge water.zip --strategy lexical "How can I make collected water safer?"` |
| Fixed BM25 | `python src/main.py --knowledge water.zip --strategy bm25 "How can I make collected water safer?"` |
| Adaptive balanced | `python src/main.py --knowledge water.zip --strategy adaptive --mode balanced "How can I make collected water safer?"` |
| Inspect adaptive plan | `python src/main.py --knowledge water.zip --strategy adaptive --mode balanced --plan "How can I make collected water safer?"` |
| JSON output | `python src/main.py --knowledge water.zip --format json "How can I make this water safer to drink?"` |
| Source ranking | `python src/main.py --knowledge water.zip --format sources "How can I make this water safer to drink?"` |
| Force Spanish | `python src/main.py --knowledge water.zip --language es "necesito ayuda"` |
| Validate pack | `python src/main.py --knowledge pack.zip --validate-pack` |
| Verify provenance | `python src/main.py --knowledge pack.zip --verify-provenance` |
| Run tests | `python -m unittest discover -s tests` |

## Research direction

LastLight treats offline intelligence as a systems problem rather than a model-size competition: how much useful, trustworthy assistance can be preserved per unit of compute, memory, energy and stored knowledge when external infrastructure is unavailable?

The project is intended to make that tradeoff measurable and auditable rather than hiding it behind a remote service.

## Docs

- [Architecture](docs/architecture.md)
- [Python API](docs/python_api.md)
- [Knowledge Packs](docs/knowledge_packs.md)
- [Knowledge Pack Provenance](docs/pack_provenance.md)
- [Adaptive Retrieval](docs/adaptive_retrieval.md)
- [Ecosystem](ECOSYSTEM.md)

## License

Mozilla Public License 2.0.
