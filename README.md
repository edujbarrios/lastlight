# LastLight

**Low-power RAG for offline disaster and infrastructure-failure guidance.**

LastLight is a tiny local RAG-style knowledge capsule. It searches Markdown knowledge packs, returns sourced passages, and refuses to answer when confidence is too low. It uses only the Python standard library: no cloud API, embeddings, vector database, telemetry, package install, browser, or background service.

While much of current AI research focuses on general-purpose LLMs, disasters and infrastructure collapse expose a narrower and practical AI systems problem: people often need accurate, auditable information from a solid local knowledge base when compute, battery, and network access are constrained. LastLight explores that gap through a low-power RAG-inspired design for austere environments, prioritizing robust retrieval, source traceability, and refusal over unconstrained generation.

## Clone

```bash
git clone https://github.com/edujbarrios/lastlight.git
cd lastlight
```

## Run

```bash
python src/main.py
python src/main.py "how do I purify water"

# Use --knowledge when adding an external knowledge pack beyond this repo's built-in knowledge.
python src/main.py --knowledge path/to/pack.zip "find north without a compass"
```

## Frontend

Start the optional local web UI. It uses a pure black, low-brightness theme, opens with a short calm-and-safety checklist, and shows only the answer passage:

```bash
python src/main.py --serve
```

Open `http://127.0.0.1:8765`.

The web session keeps short-lived context for follow-up questions.

![LastLight web UI](docs/screenshots/lastlight-web.png)

## Features

- Offline terminal search over `knowledge/en/`, `knowledge/es/`, or custom packs
- Sourced answers with confidence, language, tags, and source paths
- Lexical, BM25, and optional C-backed lexical retrieval
- Lightweight session memory for follow-up questions in interactive and web modes
- Deterministic triage checks after accepted terminal answers
- Directory and deterministic `.zip` knowledge packs
- Pack validation, export, metadata, and SHA-256 audit indexes
- Optional minimal dark local web UI
- Optional experimental n-gram synthesis and local model packs

## Benchmark

The current retrieval benchmark uses 40 direct, scenario-based, multi-intent, and Spanish disaster-response queries from `data/eval.jsonl`.

| Strategy | Top-1 | Top-3 | MRR | Mean search latency |
| --- | ---: | ---: | ---: | ---: |
| Lexical | 97.50% | 100.00% | 0.988 | 31.586 ms |
| BM25 | 95.00% | 100.00% | 0.971 | 31.613 ms |

Process-level timing on Windows 11 / Python 3.12.7 with 7 iterations and a 15 W energy estimate:

| Operation | Median time | Estimated energy |
| --- | ---: | ---: |
| Lexical query | 333.4 ms | 1.3894 mWh |
| BM25 query | 313.4 ms | 1.3060 mWh |
| Lexical evaluation | 1419.8 ms | 5.9159 mWh |
| BM25 evaluation | 1406.5 ms | 5.8606 mWh |
| Unit tests | 743.1 ms | 3.0961 mWh |

Full results are stored in [eval/results.json](eval/results.json), [eval/results-bm25.json](eval/results-bm25.json), and [eval/benchmark.md](eval/benchmark.md).

## Commands

| Task | Command |
| --- | --- |
| Interactive mode | `python src/main.py` |
| Single query | `python src/main.py "stop bleeding"` |
| Use another pack | `python src/main.py --knowledge path/to/pack.zip "save battery"` |
| Filter language | `python src/main.py --language es "necesito ayuda"` |
| Evaluate retrieval | `python src/main.py --eval` |
| Custom eval JSON | `python src/main.py --eval --eval-output eval/results.json` |
| Choose retrieval | `python src/main.py --strategy bm25 "purify water"` |
| Build C core | `python tools/build_c_core.py` |
| Inspect pack | `python src/main.py --pack-info` |
| List knowledge | `python src/main.py --list-knowledge` |
| Validate pack | `python src/main.py --validate-pack` |
| Export pack | `python src/main.py --export-pack dist/lastlight-core.zip` |
| Import PDF | `python src/main.py --import-pdf guide.pdf --import-output knowledge/en/imported/guide.md --language en` |
| Build audit index | `python src/main.py --build-index data/lastlight.index.json` |
| Device self-check | `python src/main.py --self-check` |
| Local web UI | `python src/main.py --serve` |
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

Knowledge packs can include `lastlight-pack.json` for reproducible metadata. See [docs/knowledge_packs.md](docs/knowledge_packs.md).

## Docs

- [Architecture](docs/architecture.md)
- [Roadmap](docs/roadmap.md)
- [Performance](docs/performance.md)
- [Platforms](docs/platforms.md)
- [Native C core](docs/native_core.md)
- [Local model packs](docs/local_models.md)
- [PDF ingest](docs/pdf_ingest.md)

## License

Mozilla Public License 2.0.
