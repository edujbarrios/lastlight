# LastLight

**Low-power RAG for offline disaster and infrastructure-failure guidance.**

LastLight is a tiny local RAG-style knowledge capsule. It searches Markdown knowledge packs, returns sourced passages, and refuses to answer when confidence is too low. It uses only the Python standard library: no cloud API, embeddings, vector database, telemetry, package install, browser, or background service.

While much of current AI research focuses on general-purpose LLMs, disasters and infrastructure collapse expose a narrower and practical AI systems problem: people often need accurate, auditable information from a solid local knowledge base when compute, battery, and network access are constrained. LastLight explores that gap through a low-power RAG-inspired design for austere environments, prioritizing robust retrieval, source traceability, and refusal over unconstrained generation.

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

Full results are stored in [eval/results.json](eval/results.json), [eval/results-bm25.json](eval/results-bm25.json), and [eval/benchmark.md](eval/benchmark.md).

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
python src/main.py --fail-on-refusal "how do I purify water"

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

<img src="docs/screenshots/lastlight-web.png" alt="LastLight web UI" width="720">

## Features

- Offline terminal search over mirrored English and Spanish knowledge packs, or custom packs
- Sourced answers with confidence, language, tags, and source paths
- Lexical, BM25, and optional C-backed lexical retrieval
- Lightweight session memory for follow-up questions in interactive and web modes
- Deterministic triage checks after accepted terminal answers
- Directory and deterministic `.zip` knowledge packs
- Pack validation, export, metadata, and SHA-256 audit indexes
- Optional minimal dark local web UI
- Optional experimental n-gram synthesis and local model packs

## Commands

| Task | Command |
| --- | --- |
| Interactive mode | `python src/main.py` |
| Single query | `python src/main.py "stop bleeding"` |
| JSON query output | `python src/main.py --format json --top-k 5 "stop bleeding"` |
| Ranked source list | `python src/main.py --format sources "stop bleeding"` |
| Batch queries to JSONL | `python src/main.py --query-file questions.txt --query-output answers.jsonl` |
| Fail safely in scripts | `python src/main.py --fail-on-refusal "stop bleeding"` (exit 2 on refusal) |
| Use another pack | `python src/main.py --knowledge path/to/pack.zip "save battery"` |
| Filter language | `python src/main.py --language es "necesito ayuda"` |
| Evaluate retrieval | `python src/main.py --eval` |
| Rebuild stress dataset | `python tools/build_eval_dataset.py` |
| Custom eval JSON | `python src/main.py --eval --eval-output eval/results.json` |
| Choose retrieval | `python src/main.py --strategy bm25 "purify water"` |
| Build C core | `python tools/build_c_core.py` |
| Inspect pack | `python src/main.py --pack-info` |
| List knowledge | `python src/main.py --list-knowledge` |
| Validate pack | `python src/main.py --validate-pack` |
| Export pack | `python src/main.py --export-pack dist/lastlight-core.zip` |
| Export only if valid | `python src/main.py --export-pack dist/lastlight-core.zip --require-valid-pack` |
| Import PDF | `python src/main.py --import-pdf guide.pdf --import-output knowledge/en/imported/guide.md --language en` |
| Build audit index | `python src/main.py --build-index data/lastlight.index.json` |
| Verify knowledge integrity | `python src/main.py --verify-index data/lastlight.index.json` |
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
