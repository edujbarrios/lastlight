# LastLight

**Offline emergency knowledge retrieval for low-power, no-network conditions.**

LastLight is a tiny local RAG-style knowledge capsule. It searches Markdown knowledge packs, returns sourced passages, and refuses to answer when confidence is too low. It uses only the Python standard library: no cloud API, embeddings, vector database, telemetry, package install, browser, or background service.

## Clone

```bash
git clone https://github.com/edujbarrios/lastlight.git
cd lastlight
```

## Run

```bash
python3 src/main.py
python3 src/main.py "how do I purify water"
python3 src/main.py --knowledge path/to/pack.zip "find north without a compass"
```

On Windows, use `python` instead of `python3` if needed.

## Frontend

Start the optional local web UI. It uses a pure black, low-brightness theme:

```bash
python3 src/main.py --serve
```

Open `http://127.0.0.1:8765`.

![LastLight web UI](docs/screenshots/lastlight-web.png)

## Features

- Offline terminal search over `knowledge/en/`, `knowledge/es/`, or custom packs
- Sourced answers with confidence, language, tags, and source paths
- Lexical, BM25, and optional C-backed lexical retrieval
- Directory and deterministic `.zip` knowledge packs
- Pack validation, export, metadata, and SHA-256 audit indexes
- Optional minimal dark local web UI
- Optional experimental n-gram synthesis and local model packs

## Commands

| Task | Command |
| --- | --- |
| Interactive mode | `python3 src/main.py` |
| Single query | `python3 src/main.py "stop bleeding"` |
| Use another pack | `python3 src/main.py --knowledge path/to/pack.zip "save battery"` |
| Filter language | `python3 src/main.py --language es "necesito ayuda"` |
| Evaluate retrieval | `python3 src/main.py --eval` |
| Custom eval JSON | `python3 src/main.py --eval --eval-output eval/results.json` |
| Choose retrieval | `python3 src/main.py --strategy bm25 "purify water"` |
| Build C core | `python3 tools/build_c_core.py` |
| Inspect pack | `python3 src/main.py --pack-info` |
| List knowledge | `python3 src/main.py --list-knowledge` |
| Validate pack | `python3 src/main.py --validate-pack` |
| Export pack | `python3 src/main.py --export-pack dist/lastlight-core.zip` |
| Build audit index | `python3 src/main.py --build-index data/lastlight.index.json` |
| Device self-check | `python3 src/main.py --self-check` |
| Local web UI | `python3 src/main.py --serve` |
| Run tests | `python3 -m unittest discover -s tests` |

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

## License

Mozilla Public License 2.0.
