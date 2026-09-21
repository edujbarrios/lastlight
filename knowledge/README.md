# Knowledge packs

LastLight intentionally does **not** ship a bundled emergency knowledge corpus in this directory. The runtime is designed to consume one or more independently distributed knowledge packs, usually as `.zip` files passed with repeated `--knowledge` arguments.

## ZIP layout

A pack is a normal ZIP archive. Keep `lastlight-pack.json` at the archive root and place Markdown documents underneath language/topic folders.

```text
water-es.zip
├── lastlight-pack.json
├── es/
│   ├── water/
│   │   ├── purification.md
│   │   └── storage.md
│   └── sanitation/
│       └── hygiene.md
└── sources/
    └── references.json
```

A multilingual pack can use more than one language directory:

```text
first-aid.zip
├── lastlight-pack.json
├── en/
│   └── medical/
│       └── bleeding.md
└── es/
    └── medical/
        └── bleeding.md
```

Markdown documents should include front matter when possible:

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

The manifest can carry versioning and provenance metadata:

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

## Validate and use a pack

```bash
python src/main.py --knowledge water-es.zip --validate-pack
python src/main.py --knowledge water-es.zip --verify-provenance
python src/main.py --knowledge water-es.zip "¿cómo potabilizo agua?"
```

Mount several packs by repeating `--knowledge`:

```bash
python src/main.py \
  --knowledge water-es.zip \
  --knowledge first-aid-es.zip \
  --knowledge blackout-es.zip \
  "necesito agua segura y primeros auxilios"
```

Packs remain independent artifacts; LastLight combines their documents for retrieval while preserving pack attribution.

## Planned knowledge platform

A separate web platform is planned for discovering, reading and downloading versioned LastLight knowledge packs as ZIP files. The intended flow is: browse knowledge online, download the packs needed for a device or scenario, transfer them if necessary by USB/SD card, verify them locally, and mount one or more packs in LastLight.

The platform is **not required at runtime**. LastLight remains fully offline after the ZIP files have been obtained, and packs can also be distributed through GitHub Releases, local storage, removable media, or any other channel.

For the full pack contract, see [`docs/knowledge_packs.md`](../docs/knowledge_packs.md) and [`docs/pack_provenance.md`](../docs/pack_provenance.md).
