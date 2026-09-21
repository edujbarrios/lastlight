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

## Quick start

```bash
git clone https://github.com/edujbarrios/lastlight.git
cd lastlight

python src/main.py \
  --knowledge packs/water-es.zip \
  "¿cómo potabilizo agua?"
```

`--knowledge` is repeatable. Packs remain independent while LastLight searches them as one local corpus:

```bash
python src/main.py \
  --knowledge packs/water-es.zip \
  --knowledge packs/first-aid-es.zip \
  --knowledge packs/blackout-es.zip \
  "necesito agua segura y primeros auxilios"
```

## Knowledge packs

LastLight does not ship a fixed emergency corpus. [`knowledge/README.md`](knowledge/README.md) documents the pack format; knowledge can be distributed and updated independently from the runtime.

```text
water-es.zip
├── lastlight-pack.json
├── es/
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
python src/main.py --knowledge pack.zip --eval
```

## Useful commands

| Task | Command |
| --- | --- |
| One pack | `python src/main.py --knowledge water.zip "safe water"` |
| Multiple packs | `python src/main.py --knowledge water.zip --knowledge first-aid.zip "safe water and first aid"` |
| JSON output | `python src/main.py --knowledge water.zip --format json "safe water"` |
| Source ranking | `python src/main.py --knowledge water.zip --format sources "safe water"` |
| Force Spanish | `python src/main.py --knowledge water.zip --language es "necesito ayuda"` |
| Validate pack | `python src/main.py --knowledge pack.zip --validate-pack` |
| Verify provenance | `python src/main.py --knowledge pack.zip --verify-provenance` |
| Adaptive retrieval | `python src/main.py --knowledge pack.zip --strategy adaptive --mode balanced "agua"` |
| Inspect adaptive plan | `python src/main.py --knowledge pack.zip --strategy adaptive --plan "agua"` |
| Evaluation | `python src/main.py --knowledge pack.zip --eval` |
| Run tests | `python -m unittest discover -s tests` |

## Research direction

LastLight treats offline intelligence as a systems problem rather than a model-size competition: how much useful, trustworthy assistance can be preserved per unit of compute, memory, energy and stored knowledge when external infrastructure is unavailable?

The project is intended to make that tradeoff measurable and auditable rather than hiding it behind a remote service.

## Docs

- [Architecture](docs/architecture.md)
- [Knowledge Packs](docs/knowledge_packs.md)
- [Knowledge Pack Provenance](docs/pack_provenance.md)
- [Adaptive Retrieval](docs/adaptive_retrieval.md)
- [Ecosystem](ECOSYSTEM.md)

## License

Mozilla Public License 2.0.
