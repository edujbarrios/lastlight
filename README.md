# LastLight

**Offline intelligence under extreme constraints.**

> Everybody is focusing on making advances in AI, LLMs... etc, but what happens when there is a blackout and you are running out of battery in a para-apocalyptic environment?

LastLight is a tiny, offline, extensible knowledge capsule for preserving critical human knowledge under severe resource constraints. In practical terms, it is an extremely lightweight local RAG system: it retrieves relevant passages from a human-readable Markdown knowledge base and refuses to answer when confidence is too low.

It is an experimental indie AI research project by **Eduardo J. Barrios** exploring how much useful intelligence can survive when computation, energy, connectivity, and hardware are limited.

## Vision

Most AI research scales upward: larger models, larger datasets, larger clusters, larger energy budgets. LastLight explores the opposite direction:

- smaller systems
- lower energy consumption
- higher transparency
- higher auditability
- offline-first operation
- graceful degradation under catastrophic conditions

The goal is not to build the smartest assistant. The goal is to build the most useful assistant possible when almost everything else has failed.

## Philosophy

LastLight follows a retrieval-first philosophy:

- Retrieval over generation
- Evidence over fluency
- Refusal over hallucination
- Offline-first
- Terminal-first
- Human-readable knowledge
- Low energy usage
- Open-source by default
- Long-term maintainability
- Community contribution

If LastLight cannot find a sufficiently confident source in its local knowledge base, it refuses to answer.

## Micro-RAG

LastLight can be understood as a micro-RAG system built for blackout conditions.

Traditional RAG systems often depend on embeddings, vector databases, cloud APIs, web services, large language models, and continuous infrastructure. LastLight keeps the same core idea, retrieve grounded knowledge before answering, but strips the system down to the smallest useful form:

- Markdown files instead of a database
- lexical retrieval instead of embeddings
- deterministic ranking instead of model scoring
- sourced passages instead of generated prose
- confidence thresholds instead of fluent guessing
- terminal execution instead of a web interface
- no network, no telemetry, no package installation

This is not meant to compete with full-scale AI assistants. It is meant to function when full-scale AI is unavailable. The research question is whether a tiny, auditable retrieval system can still provide useful, source-grounded intelligence on ordinary hardware with very little energy.

## How It Works

Knowledge is stored as ordinary Markdown under `knowledge/`. Files are discovered recursively at runtime. Metadata is optional and lives in a small front matter block:

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

No knowledge is hardcoded into Python source files. A contributor can add a Markdown file, rerun LastLight, and immediately make that knowledge searchable.

## Architecture

LastLight v0.1 is a retrieval-only RAG implementation. It uses no neural models, embeddings, databases, cloud APIs, browser, GUI, telemetry, daemon, or background threads.

It uses deterministic lexical retrieval:

- recursive Markdown discovery
- metadata extraction
- Unicode normalization
- English and Spanish stopwords
- lexical matching
- title, tag, phrase, priority, and rare-term boosts
- top-k ranking
- confidence scoring

It also includes an optional lightweight BM25 strategy:

- no persistent index
- no external database
- computed in memory per query
- title and tag boosts through repeated tokens
- selectable with `--strategy bm25`

Design patterns are intentionally lightweight:

- Repository Pattern: `KnowledgeRepository`, `MarkdownKnowledgeRepository`
- Strategy Pattern: `RetrievalStrategy`, `LexicalRetrievalStrategy`
- Factory Pattern: `ApplicationFactory`
- Command Pattern: interactive, query, and evaluation commands
- Value Objects: `KnowledgeDocument`, `SearchQuery`, `SearchResult`, `EvaluationCase`

## Run

Interactive mode:

```bash
python3 src/main.py
```

Single query:

```bash
python3 src/main.py "how do I purify water"
```

Evaluation:

```bash
python3 src/main.py --eval
```

Optional BM25 retrieval:

```bash
python3 src/main.py --strategy bm25 "how do I save phone battery"
python3 src/main.py --strategy bm25 --eval
```

Make targets:

```bash
make run
make test
make eval
```

On Windows, use `python` instead of `python3` if needed.

## Test

```bash
python3 -m unittest discover -s tests
```

The project uses only the Python standard library. There are no third-party dependencies and no package installation step.

## Add Knowledge

1. Create a Markdown file.
2. Add optional metadata.
3. Place it anywhere under `knowledge/`.
4. Run tests.
5. Run evaluation.
6. Submit a pull request.

No code changes should be necessary.

## Low-Power Design

LastLight avoids polling, progress bars, animations, background work, network calls, and expensive startup tasks. It reads Markdown, ranks documents, prints sourced passages, and exits.

## Roadmap

v0.1:

- Markdown knowledge base
- Recursive discovery
- Deterministic retrieval
- CLI
- Tests
- Evaluation suite

v0.2:

- BM25 strategy: implemented as optional `--strategy bm25`
- Better multilingual support: basic deterministic query expansion
- Improved chunking: lightweight passage chunking for cleaner excerpts

v0.3:

- Compressed knowledge packs
- Offline index builder
- Streaming retrieval

v0.4:

- Tiny n-gram language model
- Citation-aware generation based exclusively on retrieved passages

v0.5:

- Raspberry Pi support
- Termux support
- Old laptop support

v0.6:

- Optional C retrieval core

v0.7:

- Tiny local language models
- Research into ultra-low-power AI systems

v1.0:

- Community-maintained emergency knowledge repository
- Multilingual knowledge packs
- Reproducible offline intelligence system

## License

Mozilla Public License 2.0.
