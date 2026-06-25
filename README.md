# LastLight

**Offline emergency knowledge retrieval for low-power, no-network conditions.**

LastLight is a tiny local RAG-style knowledge capsule. It searches a human-readable Markdown knowledge base, returns sourced passages, and refuses to answer when confidence is too low.

It uses only the Python standard library. No cloud APIs, embeddings, vector database, telemetry, package install, browser, or background service are required.

## What It Does

- Runs fully offline from the terminal
- Searches Markdown files under `knowledge/`
- Supports directory and `.zip` knowledge packs
- Returns citations, confidence, language, tags, and source passages
- Supports lexical, BM25, and optional C-backed lexical retrieval
- Builds audit indexes with per-document SHA-256 hashes
- Validates and exports deterministic knowledge packs
- Includes optional experimental local n-gram synthesis and model packs

## Quick Start

Interactive mode:

```bash
python3 src/main.py
```

Single query:

```bash
python3 src/main.py "how do I purify water"
```

Use a zip or alternate knowledge directory:

```bash
python3 src/main.py --knowledge path/to/pack.zip "find north without a compass"
python3 src/main.py --knowledge path/to/knowledge "stop bleeding"
```

On Windows, use `python` instead of `python3` if needed.

## Core Commands

Run evaluation:

```bash
python3 src/main.py --eval
```

Choose retrieval strategy:

```bash
python3 src/main.py --strategy lexical "save phone battery"
python3 src/main.py --strategy bm25 "save phone battery"
python3 src/main.py --strategy c-lexical "save phone battery"
```

Build the optional C core first if you want native match counting:

```bash
python3 tools/build_c_core.py
```

Inspect, validate, and export knowledge packs:

```bash
python3 src/main.py --pack-info
python3 src/main.py --validate-pack
python3 src/main.py --export-pack dist/lastlight-core.zip
```

Build an offline audit index:

```bash
python3 src/main.py --build-index data/lastlight.index.json
```

Check constrained-device compatibility:

```bash
python3 src/main.py --self-check
```

Experimental local model tools:

```bash
python3 src/main.py --synthesize "how do I purify water"
python3 src/main.py --build-model data/lastlight.model.json
python3 src/main.py --model-info data/lastlight.model.json
```

## Knowledge Format

Add Markdown files anywhere under `knowledge/`:

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

Knowledge packs can include `lastlight-pack.json` for reproducible metadata:

```json
{
  "name": "LastLight Core Emergency Knowledge Pack",
  "version": "0.1.0",
  "languages": ["en", "es"],
  "license": "MPL-2.0",
  "source": "https://github.com/edujbarrios/lastlight"
}
```

See [docs/knowledge_packs.md](docs/knowledge_packs.md) for pack publishing.

## Test

```bash
python3 -m unittest discover -s tests
```

Make targets:

```bash
make run
make test
make eval
```

## Design Notes

LastLight is retrieval-first: evidence over fluency, refusal over hallucination, and offline-first operation. The default path reads Markdown, ranks documents, prints sourced passages, and exits.

More detail:

- [Architecture](docs/architecture.md)
- [Roadmap](docs/roadmap.md)
- [Performance](docs/performance.md)
- [Platforms](docs/platforms.md)
- [Native C core](docs/native_core.md)
- [Local model packs](docs/local_models.md)

## License

Mozilla Public License 2.0.
