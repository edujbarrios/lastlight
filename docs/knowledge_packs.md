# Knowledge Packs

LastLight knowledge packs are ordinary directories or `.zip` files containing Markdown documents plus optional metadata. The core repository does not ship a built-in emergency corpus: knowledge is distributed separately and mounted at runtime.

The project-level [`knowledge/README.md`](../knowledge/README.md) is the short format reference. It is intentionally excluded from retrieval.

## Recommended ZIP layout

```text
pack.zip
├── lastlight-pack.json
├── en/
│   └── topic/
│       └── guide.md
├── es/
│   └── topic/
│       └── guide.md
└── sources/
    └── references.json
```

A root `README.md` is allowed for human-facing pack documentation and is ignored by retrieval. Archive entries under hidden directories or `__MACOSX/` are also ignored.

Each Markdown document should include front matter when possible:

```markdown
---
title: Water purification
language: es
tags:
  - water
  - purification
priority: high
---

Contenido del documento...
```

## Manifest

`lastlight-pack.json` lives at the pack root. A minimal example:

```json
{
  "name": "Emergency Water ES",
  "version": "1.0.0",
  "languages": ["es"],
  "license": "CC-BY-4.0",
  "source": "https://example.org/water",
  "publisher": "Example Publisher",
  "published_at": "2026-09-01",
  "provenance": [
    {"source": "https://example.org/reference"}
  ]
}
```

If no manifest is present, LastLight can still load the documents and infer basic language coverage from document front matter.

## Validate and inspect

The core validates artifacts it is asked to consume:

```bash
python src/main.py --knowledge pack.zip --pack-info
python src/main.py --knowledge pack.zip --validate-pack
python src/main.py --knowledge pack.zip --verify-provenance
```

These operations are intentionally single-pack operations. Audit each artifact independently before mounting it with others.

Pack creation, PDF/HTML ingestion, deterministic ZIP publishing and future signing workflows belong in the planned `lastlight-pack-tools` companion repository rather than the runtime core.

## Mounting multiple packs

Query, interactive, evaluation and knowledge-list flows can mount more than one pack by repeating `--knowledge`:

```bash
python src/main.py \
  --knowledge packs/water-es.zip \
  --knowledge packs/first-aid-es.zip \
  --knowledge packs/blackout-es.zip \
  "¿cómo consigo agua segura y trato una herida?"
```

LastLight combines the documents into one searchable corpus while retaining the pack name, version, source and local artifact path that produced each document.

## Distribution model

Packs are registry-neutral. They can arrive through GitHub Releases, USB/SD card, local storage, a static site or another distribution channel. After the files are local, LastLight does not require Internet access.

A separate `lastlight-hub` web platform is planned for browsing, reading and downloading versioned LastLight packs as ZIP files. The hub is a distribution layer, not a runtime dependency: users should be able to download only the packs relevant to their language, region or scenario and later mount any combination offline.

## Community pack checklist

1. Keep packs topic-focused and reviewable.
2. Put searchable guidance in Markdown below language/topic directories.
3. Add `title`, `language`, `tags` and `priority` front matter where useful.
4. Add `lastlight-pack.json` with version, license, source and publisher/provenance metadata.
5. Keep source references auditable and date-sensitive guidance fresh.
6. Run `--pack-info`, `--validate-pack` and `--verify-provenance` before distribution.
7. Prefer a root `README.md` for human documentation; LastLight will not index it.

See [Knowledge Pack Provenance](pack_provenance.md) for the integrity and freshness model, and [`ECOSYSTEM.md`](../ECOSYSTEM.md) for repository boundaries.
