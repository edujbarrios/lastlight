# LastLight

**Low-power, offline RAG for disaster and infrastructure-failure guidance.**

LastLight is a stdlib-only local retrieval system for constrained environments. It searches Markdown knowledge packs, returns sourced passages, keeps pack provenance visible, and refuses when confidence is too low.

No cloud API. No embeddings. No vector database. No telemetry. No package install required.

> Inspired by the resource-scarcity premise of *This War of Mine*. LastLight is an independent project and is not affiliated with the game or its creators.

## Why it exists

When Internet access, battery, compute, or infrastructure are unreliable, the useful question is not “how large is the model?” but “can I still retrieve trustworthy local guidance, know where it came from, and avoid answering when confidence is weak?”

LastLight focuses on that problem with:

- offline lexical, BM25, optional C-backed, and adaptive retrieval
- confidence-aware refusal
- one or multiple independent knowledge packs mounted at once
- pack attribution, versioning, SHA-256 integrity and provenance checks
- automatic ES/EN routing for multilingual corpora
- device benchmarking for latency, memory and measured/estimated energy
- a small local web UI with no runtime Internet dependency

## Frontend

The local web UI shows mounted packs and attributes accepted passages back to the pack, version, source document and confidence.

<img src="docs/screenshots/lastlight-web.png" alt="LastLight local web UI with three Spanish knowledge packs mounted and a Spanish sourced answer" width="760">

```bash
python src/main.py --serve
```

Open `http://127.0.0.1:8765`.

## Quick start

```bash
git clone https://github.com/edujbarrios/lastlight.git
cd lastlight

# Query the bundled knowledge.
python src/main.py "how do I purify water"

# Spanish queries are routed to Spanish knowledge when available.
python src/main.py "¿cómo potabilizo agua?"
```

### Use one knowledge pack

```bash
python src/main.py \
  --knowledge packs/water-es.zip \
  "¿cómo almaceno agua de forma segura?"
```

### Use several packs at the same time

`--knowledge` is repeatable. Packs stay independent; LastLight combines their documents into one searchable corpus while preserving pack-level attribution.

```bash
python src/main.py \
  --knowledge packs/water-es.zip \
  --knowledge packs/first-aid-es.zip \
  --knowledge packs/blackout-es.zip \
  "necesito agua segura y primeros auxilios"
```

The same works in the local UI:

```bash
python src/main.py \
  --knowledge packs/water-es.zip \
  --knowledge packs/first-aid-es.zip \
  --serve
```

### Verify a downloaded pack

```bash
python src/main.py --knowledge pack.zip --validate-pack
python src/main.py --knowledge pack.zip --verify-provenance
```

Pack-specific maintenance commands intentionally operate on one pack at a time; verify each artifact independently, then mount any combination for retrieval.

## Language behavior

Explicit `--language es` / `--language en` always wins. Without it, LastLight:

- automatically adopts the corpus language for monolingual packs
- routes clearly Spanish queries to `es` documents in mixed ES/EN corpora
- routes clearly English queries to `en`
- leaves ambiguous multilingual queries unfiltered instead of guessing

LastLight does not translate retrieved text: it returns the original sourced passage from the selected pack.

## Safety and provenance

Each accepted result can carry pack name, version, source and local path. `lastlight-pack.json` can also describe publisher, publication/expiry dates, provenance entries and an optional deterministic fingerprint.

```bash
python src/main.py --knowledge pack.zip --verify-provenance --provenance-json
```

This is registry-neutral: packs can arrive through USB, SD card, GitHub Releases, or a future static catalog and still be verified locally.

## Benchmark

The stress suite contains **238 deterministic cases**, including misspellings, terse prompts, regional Spanish, multi-intent emergencies, adversarial instructions and out-of-domain requests.

| Strategy | Top-1 | Top-3 | MRR | Answer precision | Refusal recall | Answerable recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Lexical | 62.18% | 63.45% | 0.518 | 89.60% | 62.50% | 81.58% |
| BM25 | 55.04% | 63.45% | 0.569 | 83.18% | 25.00% | 93.68% |

The default lexical strategy remains the safer current tradeoff because it gives up some answerable recall in exchange for stronger answer precision and refusal behavior.

```bash
python src/main.py --eval
python src/main.py --benchmark
python src/main.py --benchmark --benchmark-energy-source rapl
```

RAPL measurements are CPU/package energy, not necessarily whole-device wall power. See [Performance and Energy Measurement](docs/performance.md).

## Useful commands

| Task | Command |
| --- | --- |
| Interactive mode | `python src/main.py` |
| Query | `python src/main.py "stop bleeding"` |
| JSON output | `python src/main.py --format json "stop bleeding"` |
| Source ranking | `python src/main.py --format sources "stop bleeding"` |
| One pack | `python src/main.py --knowledge water.zip "safe water"` |
| Multiple packs | `python src/main.py --knowledge water.zip --knowledge first-aid.zip "safe water and first aid"` |
| Force Spanish | `python src/main.py --language es "necesito ayuda"` |
| Adaptive retrieval | `python src/main.py --strategy adaptive --mode balanced "purify water"` |
| Inspect adaptive plan | `python src/main.py --strategy adaptive --plan "purify water"` |
| Validate pack | `python src/main.py --knowledge pack.zip --validate-pack` |
| Verify provenance | `python src/main.py --knowledge pack.zip --verify-provenance` |
| List knowledge | `python src/main.py --list-knowledge` |
| Local web UI | `python src/main.py --serve` |
| Evaluate retrieval | `python src/main.py --eval` |
| Device benchmark | `python src/main.py --benchmark` |
| Run tests | `python -m unittest discover -s tests` |

## Docs

- [Architecture](docs/architecture.md)
- [Knowledge Packs](docs/knowledge_packs.md)
- [Knowledge Pack Provenance](docs/pack_provenance.md)
- [Adaptive Retrieval](docs/adaptive_retrieval.md)
- [Device Benchmark](docs/device_benchmark.md)
- [Performance and Energy Measurement](docs/performance.md)
- [Roadmap](docs/roadmap.md)

## License

Mozilla Public License 2.0.
