# LastLight

**Low-power, offline RAG for disaster and infrastructure-failure guidance.**

LastLight is a stdlib-only local retrieval system for constrained environments. It searches downloaded Markdown knowledge packs, returns sourced passages, preserves pack provenance, and refuses when confidence is too low.

No cloud API. No embeddings. No vector database. No telemetry. No package install required.

> Inspired by the resource-scarcity premise of *This War of Mine*. LastLight is an independent project and is not affiliated with the game or its creators.

## What it does

- mounts **one or multiple** independent directory/ZIP knowledge packs at once
- keeps pack name, version, source and local path attached to retrieved documents
- supports lexical, BM25, optional C-backed and adaptive retrieval
- refuses low-confidence answers instead of fabricating guidance
- routes Spanish/English queries to matching documents when possible
- validates pack structure, SHA-256 integrity, provenance and freshness metadata
- benchmarks latency, memory and measured/estimated energy
- includes a tiny local web UI with no runtime Internet dependency

## Frontend

The local web UI shows mounted packs and attributes accepted passages back to their pack, version, source document and confidence.

<img src="docs/screenshots/lastlight-web.png" alt="LastLight local web UI with multiple Spanish knowledge packs mounted" width="760">

## Quick start

```bash
git clone https://github.com/edujbarrios/lastlight.git
cd lastlight

# Query one downloaded pack.
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

Run the same mounted packs in the local web UI:

```bash
python src/main.py \
  --knowledge packs/water-es.zip \
  --knowledge packs/first-aid-es.zip \
  --serve
```

Then open `http://127.0.0.1:8765`.

## Knowledge packs

LastLight no longer ships an embedded emergency corpus in `knowledge/`. That directory now documents the pack format only; actual knowledge is expected to arrive as independently versioned packs.

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

The platform will remain optional: once packs are downloaded, LastLight continues to work fully offline.

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
| Web UI | `python src/main.py --knowledge water.zip --serve` |
| JSON output | `python src/main.py --knowledge water.zip --format json "safe water"` |
| Source ranking | `python src/main.py --knowledge water.zip --format sources "safe water"` |
| Force Spanish | `python src/main.py --knowledge water.zip --language es "necesito ayuda"` |
| Validate pack | `python src/main.py --knowledge pack.zip --validate-pack` |
| Verify provenance | `python src/main.py --knowledge pack.zip --verify-provenance` |
| Adaptive retrieval | `python src/main.py --knowledge pack.zip --strategy adaptive --mode balanced "agua"` |
| Device benchmark | `python src/main.py --knowledge pack.zip --benchmark` |
| Run tests | `python -m unittest discover -s tests` |

## Docs

- [Architecture](docs/architecture.md)
- [Knowledge Packs](docs/knowledge_packs.md)
- [Knowledge Pack Provenance](docs/pack_provenance.md)
- [Adaptive Retrieval](docs/adaptive_retrieval.md)
- [Device Benchmark](docs/device_benchmark.md)
- [Performance and Energy Measurement](docs/performance.md)

## License

Mozilla Public License 2.0.
