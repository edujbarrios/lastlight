# LastLight

**Low-power RAG for offline disaster and infrastructure-failure guidance.**

LastLight is a tiny local RAG-style knowledge capsule. It searches Markdown knowledge packs, returns sourced passages, and refuses to answer when confidence is too low. It uses only the Python standard library: no cloud API, embeddings, vector database, telemetry, package install, browser, or background service.

While much of current AI research focuses on general-purpose LLMs, disasters and infrastructure collapse expose a narrower and practical AI systems problem: people often need accurate, auditable information from a solid local knowledge base when compute, battery, and network access are constrained. LastLight explores that gap through a low-power RAG-inspired design for austere environments, prioritizing robust retrieval, source traceability, refusal, and resource-aware execution over unconstrained generation.

## Inspiration

The repository's author was inspired by [*This War of Mine*](https://www.11bitstudios.com/games/this-war-of-mine/) when creating LastLight: a post-apocalyptic world where Internet and energy restrictions shape whether and how people can access knowledge. LastLight translates that premise into a practical offline system; it is an independent project and is not affiliated with the game or its creators.

## Benchmark

The current retrieval benchmark uses 238 deterministic cases from `data/eval.jsonl`. It covers baseline and scenario queries plus misspellings, terse prompts, colloquial language, regional Spanish, multi-intent emergencies, contradictory claims, adversarial instructions, and out-of-domain requests. `data/eval_core.jsonl` preserves the 40 curated seed cases and `tools/build_eval_dataset.py` reproducibly builds the stress suite.

Besides retrieval accuracy and MRR, the report measures answer precision, refusal recall, answerable recall, and results by category. Multi-intent cases require every expected topic to appear in the accepted top-k results; adversarial and out-of-domain cases are correct only when LastLight refuses to answer.

Current stress-suite results, generated with the commands shown below:

| Strategy | Cases | Top-1 | Top-3 | MRR | Answer precision | Refusal recall | Answerable recall | Mean latency |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Lexical | 238 | 62.18% | 63.45% | 0.518 | 89.60% | 62.50% | 81.58% | 40.146 ms |
| BM25 | 238 | 55.04% | 63.45% | 0.569 | 83.18% | 25.00% | 93.68% | 40.365 ms |

```bash
python src/main.py --eval --eval-output eval/results.json
python src/main.py --strategy bm25 --eval --eval-output eval/results-bm25.json
```

BM25 accepts more answerable cases, but its lower answer precision and refusal recall mean that it also accepts substantially more adversarial and out-of-domain queries. The default lexical strategy remains the safer current tradeoff.

The lower stress accuracy is intentional: it exposes concrete robustness gaps hidden by the original direct-query suite.

Historical results on the original 40 seed cases:

| Strategy | Top-1 | Top-3 | MRR | Mean search latency |
| --- | ---: | ---: | ---: | ---: |
| Lexical | 100.00% | 100.00% | 1.000 | 52.557 ms |
| BM25 | 92.50% | 100.00% | 0.958 | 52.535 ms |

Process-level timing on Windows 11 / Python 3.12.7 with 7 iterations and a 15 W energy estimate:

| Operation | Median time | Estimated energy |
| --- | ---: | ---: |
| Lexical query | 333.4 ms | 1.3894 mWh |
| BM25 query | 313.4 ms | 1.3060 mWh |
| Lexical evaluation | 1419.8 ms | 5.9159 mWh |
| BM25 evaluation | 1406.5 ms | 5.8606 mWh |
| Unit tests | 743.1 ms | 3.0961 mWh |

Full retrieval results are stored in [eval/results.json](eval/results.json), [eval/results-bm25.json](eval/results-bm25.json), and [eval/benchmark.md](eval/benchmark.md).

### Measured energy benchmarks

`tools/benchmark.py` distinguishes real hardware measurements from estimates. In `auto` mode it uses an explicit cumulative counter when supplied, otherwise top-level Linux RAPL package counters when available, and only then falls back to the wattage estimate.

```bash
python tools/benchmark.py --iterations 7
python tools/benchmark.py --iterations 7 --energy-source rapl
python tools/benchmark.py --iterations 7 \
  --energy-source counter \
  --energy-counter /path/to/cumulative_energy \
  --energy-unit mwh
```

RAPL is a real CPU/package energy measurement, not necessarily whole-device wall power. For end-to-end energy/query claims on Raspberry Pi-class hardware, prefer a whole-device meter whose cumulative reading can be exposed to the benchmark. See [Performance and Energy Measurement](docs/performance.md).

### Integrated device benchmark

Run one safety-first system report across lexical, BM25, C-backed lexical, and adaptive retrieval:

```bash
python src/main.py --benchmark
python src/main.py --benchmark --benchmark-json
python src/main.py --benchmark --benchmark-energy-source rapl
python src/main.py --benchmark --benchmark-max-cases 40
```

The report includes device/corpus information, Top-1 and Top-k accuracy, answer precision, refusal recall, p95 latency, peak Python-traced memory, measured or estimated energy/query, and an auditable strategy recommendation. See [Device Benchmark](docs/device_benchmark.md).

## Clone

```bash
git clone https://github.com/edujbarrios/lastlight.git
cd lastlight
```

## Run

```bash
python src/main.py
python src/main.py "how do I purify water"
python src/main.py --format json --top-k 5 "how do I purify water"
python src/main.py --format sources "how do I purify water"
python src/main.py --query-file field-questions.txt --query-output answers.jsonl
python src/main.py --query-file field-questions.txt --field-guide field-guide.md
python src/main.py --fail-on-refusal "how do I purify water"

# Resource-adaptive retrieval remains opt-in.
python src/main.py --strategy adaptive --mode balanced "how do I purify water"
python src/main.py --strategy adaptive --mode survival --energy-budget-mwh 0.4 "how do I purify water"
python src/main.py --strategy adaptive --mode survival --plan "how do I purify water"

# Verify a downloaded or locally built knowledge pack before using it.
python src/main.py --knowledge path/to/pack.zip --validate-pack
python src/main.py --knowledge path/to/pack.zip --verify-provenance
python src/main.py --knowledge path/to/pack.zip --verify-provenance --provenance-json

# Mount one pack.
python src/main.py --knowledge packs/water-es.zip "find safe water guidance"

# Or mount several independent packs at the same time.
python src/main.py \
  --knowledge packs/water-es.zip \
  --knowledge packs/first-aid-es.zip \
  --knowledge packs/blackout-es.zip \
  "necesito agua segura y primeros auxilios"
```

`--knowledge` is repeatable. LastLight can use **one or multiple packs at once** without merging the ZIP files: their documents form one searchable corpus while each result keeps the pack name, version, source, and local pack path that produced it.

## Adaptive retrieval

`--strategy adaptive` chooses between lexical, BM25, and the optional C-backed lexical path using a deterministic policy. The planner considers query risk, `survival` / `balanced` / `accuracy` mode, explicit energy and memory budgets, low-resource ARM/Termux detection, Linux battery percentage when available, and whether the native C core is loaded.

Critical-risk queries keep a safety-first lexical policy even in `accuracy` mode. Tight resource budgets, low battery, or low-resource targets select the lower-cost path and cap `top-k`. Use `--plan` to print the complete strategy decision and reason as JSON. The existing default remains fixed `lexical` retrieval for backwards compatibility.

See [Adaptive Retrieval](docs/adaptive_retrieval.md) for the decision order and thresholds.

## Auditable knowledge packs

A `lastlight-pack.json` manifest can describe not only version, languages, license, and source, but also publisher, publication/expiry dates, a provenance chain, and an optional deterministic `fingerprint_sha256`.

`--verify-provenance` independently calculates the pack fingerprint from the manifest and every Markdown document hash. It rejects expired packs, invalid dates, malformed provenance data, and declared fingerprints that no longer match the contents. Older-but-not-expired material can be flagged with a configurable freshness warning using `--stale-after-days`.

This contract is intentionally registry-neutral: packs can be distributed by USB, SD card, GitHub Releases, a static catalog, or another service and still be verified locally without a network dependency. See [Knowledge Pack Provenance](docs/pack_provenance.md).

## Frontend

Start the optional local web UI. It uses a low-brightness dark theme, opens with a short calm-and-safety checklist, shows the currently mounted packs, and attributes accepted passages back to their pack, version, source document, and confidence.

```bash
# Built-in knowledge.
python src/main.py --serve

# One downloaded pack.
python src/main.py --knowledge packs/water-es.zip --serve

# Several downloaded packs in the same local UI.
python src/main.py \
  --knowledge packs/water-es.zip \
  --knowledge packs/first-aid-es.zip \
  --knowledge packs/blackout-es.zip \
  --serve
```

Open `http://127.0.0.1:8765`. The web session keeps short-lived context for follow-up questions, and the pack strip makes it explicit which offline knowledge set is currently mounted.

<img src="docs/screenshots/lastlight-web.webp" alt="LastLight local web UI with three mounted knowledge packs and pack-level answer provenance" width="720">

## Features

- Offline terminal search over mirrored English and Spanish knowledge packs, or custom packs
- Mount one or multiple independent directory/ZIP knowledge packs in the same query, interactive, evaluation, or web session
- Per-result pack attribution with pack name, version, source, and local path
- Sourced answers with confidence, language, tags, and source paths
- Lexical, BM25, optional C-backed lexical, and resource-adaptive retrieval
- Auditable survival/balanced/accuracy policies with explicit energy and memory budgets
- Integrated safety/latency/memory/energy device benchmark with strategy recommendation
- Lightweight session memory for follow-up questions in interactive and web modes
- Deterministic triage checks after accepted terminal answers
- Directory and deterministic `.zip` knowledge packs
- Pack validation, export, metadata, SHA-256 audit indexes, provenance and freshness checks
- Registry-neutral pack fingerprints suitable for offline distribution catalogs
- Benchmark support for real Linux RAPL or external cumulative energy counters, with labelled estimate fallback
- Optional minimal dark local web UI with mounted-pack status and answer provenance
- Optional experimental n-gram synthesis and local model packs

## Commands

| Task | Command |
| --- | --- |
| Interactive mode | `python src/main.py` |
| Single query | `python src/main.py "stop bleeding"` |
| JSON query output | `python src/main.py --format json --top-k 5 "stop bleeding"` |
| Ranked source list | `python src/main.py --format sources "stop bleeding"` |
| Batch queries to JSONL | `python src/main.py --query-file questions.txt --query-output answers.jsonl` |
| Build an offline field guide | `python src/main.py --query-file questions.txt --field-guide field-guide.md` |
| Fail safely in scripts | `python src/main.py --fail-on-refusal "stop bleeding"` (exit 2 on refusal) |
| Use one pack | `python src/main.py --knowledge water.zip "save battery"` |
| Use multiple packs | `python src/main.py --knowledge water.zip --knowledge first-aid.zip "safe water and first aid"` |
| Filter language | `python src/main.py --language es "necesito ayuda"` |
| Evaluate retrieval | `python src/main.py --eval` |
| Integrated device benchmark | `python src/main.py --benchmark` |
| Benchmark JSON | `python src/main.py --benchmark --benchmark-json` |
| Benchmark with RAPL | `python src/main.py --benchmark --benchmark-energy-source rapl` |
| Rebuild stress dataset | `python tools/build_eval_dataset.py` |
| Custom eval JSON | `python src/main.py --eval --eval-output eval/results.json` |
| Choose fixed retrieval | `python src/main.py --strategy bm25 "purify water"` |
| Adaptive retrieval | `python src/main.py --strategy adaptive --mode balanced "purify water"` |
| Survival budget | `python src/main.py --strategy adaptive --mode survival --energy-budget-mwh 0.4 "purify water"` |
| Inspect retrieval plan | `python src/main.py --strategy adaptive --plan "purify water"` |
| Benchmark process energy | `python tools/benchmark.py --iterations 7` |
| Build C core | `python tools/build_c_core.py` |
| Inspect pack | `python src/main.py --pack-info` |
| List knowledge | `python src/main.py --list-knowledge` |
| Validate pack | `python src/main.py --validate-pack` |
| Verify pack provenance | `python src/main.py --knowledge pack.zip --verify-provenance` |
| Verify provenance as JSON | `python src/main.py --knowledge pack.zip --verify-provenance --provenance-json` |
| Export pack | `python src/main.py --export-pack dist/lastlight-core.zip` |
| Export only if valid | `python src/main.py --export-pack dist/lastlight-core.zip --require-valid-pack` |
| Import PDF | `python src/main.py --import-pdf guide.pdf --import-output knowledge/en/imported/guide.md --language en` |
| Build audit index | `python src/main.py --build-index data/lastlight.index.json` |
| Verify knowledge integrity | `python src/main.py --verify-index data/lastlight.index.json` |
| Device self-check | `python src/main.py --self-check` |
| Local web UI | `python src/main.py --serve` |
| Multi-pack web UI | `python src/main.py --knowledge water.zip --knowledge first-aid.zip --serve` |
| Run tests | `python -m unittest discover -s tests` |

## Knowledge

Add Markdown files under the matching language section, such as `knowledge/en/` or `knowledge/es/`:

```markdown
---
title: Water Purification
language: en
tags:
  - water
  - purification
priority: high
---

If water may be contaminated, boil it...
```

Knowledge packs can include `lastlight-pack.json` for reproducible metadata and provenance. Packs remain independent artifacts: verify them one at a time, then repeat `--knowledge` to mount any combination in LastLight. See [Knowledge Packs](docs/knowledge_packs.md) and [Knowledge Pack Provenance](docs/pack_provenance.md).

## Docs

- [Architecture](docs/architecture.md)
- [Adaptive Retrieval](docs/adaptive_retrieval.md)
- [Device Benchmark](docs/device_benchmark.md)
- [Knowledge Pack Provenance](docs/pack_provenance.md)
- [Roadmap](docs/roadmap.md)
- [Performance and Energy Measurement](docs/performance.md)
- [Platforms](docs/platforms.md)
- [Native C core](docs/native_core.md)
- [Local model packs](docs/local_models.md)
- [PDF ingest](docs/pdf_ingest.md)

## License

Mozilla Public License 2.0.
