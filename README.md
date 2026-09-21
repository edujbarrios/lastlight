# LastLight

**Low-power, offline RAG for disaster and infrastructure-failure guidance.**

LastLight is the **core runtime** of the LastLight ecosystem: a stdlib-only local retrieval engine for constrained environments. It searches downloaded Markdown knowledge packs, returns sourced passages, preserves pack provenance, and refuses when confidence is too low.

No cloud API. No embeddings. No vector database. No telemetry. No package install required.

> Inspired by the resource-scarcity premise of *This War of Mine*. LastLight is an independent project and is not affiliated with the game or its creators.

## Core scope

This repository owns the offline engine and its stable contracts:

- mount **one or multiple** directory/ZIP knowledge packs at once
- lexical, BM25, optional C-backed and adaptive retrieval
- confidence-aware refusal and source traceability
- ES/EN language routing
- pack metadata, validation, SHA-256 integrity, provenance and freshness checks
- CLI, evaluation and constrained-device diagnostics

User interfaces, knowledge distribution, pack authoring and other product surfaces are intentionally developed as separate companion projects. See [ECOSYSTEM.md](ECOSYSTEM.md).

## Quick start

```bash
git clone https://github.com/edujbarrios/lastlight.git
cd lastlight

python src/main.py \
  --knowledge packs/water-es.zip \
  "¿cómo potabilizo agua?"
```

`--knowledge` is repeatable, so several packs can be searched as one corpus without merging their ZIP files:

```bash
python src/main.py \
  --knowledge packs/water-es.zip \
  --knowledge packs/first-aid-es.zip \
  --knowledge packs/blackout-es.zip \
  "necesito agua segura y primeros auxilios"
```

## Knowledge packs

LastLight does not ship an embedded emergency corpus. The [`knowledge/`](knowledge/) directory documents the pack format; actual knowledge is expected to arrive as independently versioned packs.

A typical ZIP looks like:

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

See [`knowledge/README.md`](knowledge/README.md) for the expected ZIP structure and [`docs/knowledge_packs.md`](docs/knowledge_packs.md) for the full contract.

Verify a downloaded pack before using it:

```bash
python src/main.py --knowledge pack.zip --validate-pack
python src/main.py --knowledge pack.zip --verify-provenance
```

Pack-specific maintenance commands intentionally operate on one pack at a time. Verify each artifact independently, then mount any combination for retrieval.

### Planned knowledge platform

A separate web platform is planned for browsing, reading and downloading versioned LastLight knowledge packs as `.zip` files. The intended flow is: discover knowledge online → download selected packs → transfer them if necessary by USB/SD → verify locally → mount one or more packs in LastLight.

The platform is optional by design: once packs are downloaded, the core runtime remains fully offline.

## Language behavior

Explicit `--language es` / `--language en` always wins. Without it, LastLight automatically adopts a monolingual corpus language and conservatively routes clear ES/EN queries inside mixed corpora. Retrieved passages are returned in their original pack language; LastLight does not silently translate them.

## Benchmark

The stress suite contains **238 deterministic cases**, including misspellings, regional Spanish, multi-intent emergencies, adversarial instructions and out-of-domain requests.

| Strategy | Top-1 | Top-3 | MRR | Answer precision | Refusal recall | Answerable recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Lexical | 62.18% | 63.45% | 0.518 | 89.60% | 62.50% | 81.58% |
| BM25 | 55.04% | 63.45% | 0.569 | 83.18% | 25.00% | 93.68% |

The default lexical strategy remains the safer current tradeoff because it gives up some answerable recall in exchange for stronger answer precision and refusal behavior.

```bash
python src/main.py --benchmark
python src/main.py --benchmark --benchmark-energy-source rapl
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
| Device benchmark | `python src/main.py --knowledge pack.zip --benchmark` |
| Run tests | `python -m unittest discover -s tests` |

## Ecosystem

This repository is intentionally the core, not a monorepo. Planned companion repositories and their boundaries are described in [ECOSYSTEM.md](ECOSYSTEM.md).

## Docs

- [Architecture](docs/architecture.md)
- [Knowledge Packs](docs/knowledge_packs.md)
- [Knowledge Pack Provenance](docs/pack_provenance.md)
- [Adaptive Retrieval](docs/adaptive_retrieval.md)
- [Device Benchmark](docs/device_benchmark.md)
- [Performance and Energy Measurement](docs/performance.md)

## License

Mozilla Public License 2.0.
