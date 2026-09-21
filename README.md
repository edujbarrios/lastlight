# LastLight

**Low-power, offline retrieval for disaster and infrastructure-failure guidance.**

`edujbarrios/lastlight` is **LastLight Core**: the small, auditable runtime that loads local knowledge packs, retrieves sourced passages, preserves provenance, and refuses when confidence is too low.

No cloud API. No embeddings. No vector database. No telemetry. No package install required.

> Inspired by the resource-scarcity premise of *This War of Mine*. LastLight is an independent project and is not affiliated with the game or its creators.

## Core scope

This repository owns only the stable offline engine and contracts:

- mount **one or multiple** directory/ZIP knowledge packs at once
- lexical, BM25 and resource-adaptive retrieval
- confidence-aware refusal and source traceability
- ES/EN language routing
- pack metadata, validation, SHA-256 integrity, provenance and freshness checks
- a stdlib-only CLI and a small deterministic regression suite

Presentation, pack publishing, content, native acceleration, hardware benchmarking and experimental generation belong in companion repositories. See [ECOSYSTEM.md](ECOSYSTEM.md).

## Quick start

```bash
git clone https://github.com/edujbarrios/lastlight.git
cd lastlight

python src/main.py \
  --knowledge packs/water-es.zip \
  "¿cómo potabilizo agua?"
```

`--knowledge` is repeatable. Packs stay independent while LastLight searches them as one corpus:

```bash
python src/main.py \
  --knowledge packs/water-es.zip \
  --knowledge packs/first-aid-es.zip \
  --knowledge packs/blackout-es.zip \
  "necesito agua segura y primeros auxilios"
```

## Knowledge packs

LastLight Core does not ship an emergency corpus. [`knowledge/README.md`](knowledge/README.md) documents the pack format; real knowledge is expected to arrive as independently versioned packs.

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

Explicit `--language es` / `--language en` always wins. Without it, LastLight adopts a monolingual corpus language automatically and conservatively routes clear ES/EN queries inside mixed corpora. Retrieved passages remain in the original pack language; the core does not silently translate them.

## Core evaluation

`--eval` is a lightweight regression check for retrieval/refusal behavior. The core keeps only the small seed suite; larger stress datasets, hardware profiles, latency/memory studies and energy measurements belong in the planned `lastlight-bench` repository.

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
| Core evaluation | `python src/main.py --knowledge pack.zip --eval` |
| Run tests | `python -m unittest discover -s tests` |

## Ecosystem

This repository is intentionally the core, not a monorepo. Companion repository boundaries are described in [ECOSYSTEM.md](ECOSYSTEM.md).

## Docs

- [Architecture](docs/architecture.md)
- [Knowledge Packs](docs/knowledge_packs.md)
- [Knowledge Pack Provenance](docs/pack_provenance.md)
- [Adaptive Retrieval](docs/adaptive_retrieval.md)

## License

Mozilla Public License 2.0.
