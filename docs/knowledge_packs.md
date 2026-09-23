# Knowledge Packs

LastLight knowledge packs are ordinary directories or `.zip` files containing Markdown documents plus a `lastlight-pack.json` manifest. The core repository does not ship a built-in emergency corpus: knowledge is distributed separately and mounted at runtime.

The project-level [`knowledge/README.md`](../knowledge/README.md) is the short format reference. It is intentionally excluded from retrieval.

## Pack Format v1

`format_version` describes the LastLight pack schema, while `version` is the version of the knowledge content itself. LastLight 0.1.x supports pack format `1`.

A valid v1 manifest requires:

- `format_version`: integer `1`
- `name`: non-empty string
- `version`: semantic version in `MAJOR.MINOR.PATCH` form
- `languages`: non-empty list of language codes such as `en`, `es`, or `pt-BR`
- `license`: non-empty string
- `source`: non-empty string identifying the origin of the pack

`publisher`, `published_at`, `expires_at`, `provenance`, and `fingerprint_sha256` are supported provenance/integrity fields. Unknown extra fields are preserved for forward-compatible metadata, but changing the pack format requires a new `format_version`.

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
└── README.md
```

A root `README.md` is allowed for human-facing pack documentation and is ignored by retrieval. Archive entries under hidden directories or `__MACOSX/` are also ignored.

Each Markdown document should include front matter:

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

`lastlight-pack.json` lives at the pack root. A minimal v1 example:

```json
{
  "format_version": 1,
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

A directory without a manifest can still be inspected by the low-level repository loader, but it is **not a valid distributable LastLight v1 pack** and `--validate-pack` will fail it.

## Validate and inspect

```bash
lastlight --knowledge pack.zip --pack-info
lastlight --knowledge pack.zip --validate-pack
lastlight --knowledge pack.zip --verify-provenance
```

Validation rejects unsupported format versions, invalid manifest field types, invalid semantic content versions, duplicate/invalid language codes, malformed provenance entries, and malformed SHA-256 fingerprints.

These operations are intentionally single-pack operations. Audit each artifact independently before mounting it with others.

Pack creation, PDF/HTML ingestion, deterministic ZIP publishing and signing workflows belong in the planned `lastlight-pack-tools` companion repository rather than the runtime core.

## Mounting multiple packs

```python
from lastlight import LastLight

engine = LastLight.from_packs([
    "packs/water-es.zip",
    "packs/first-aid-es.zip",
    "packs/blackout-es.zip",
])
```

LastLight combines the documents into one searchable corpus while retaining pack identity and attribution on each result.

## Distribution model

Packs are registry-neutral. They can arrive through GitHub Releases, USB/SD card, local storage, a static site or another distribution channel. After the files are local, LastLight does not require Internet access.

A separate `lastlight-hub` can later browse and distribute versioned packs without becoming a runtime dependency.

## Community pack checklist

1. Set `format_version` to `1`.
2. Keep packs topic-focused and reviewable.
3. Put searchable guidance in Markdown below language/topic directories.
4. Add `title`, `language`, `tags` and `priority` front matter.
5. Use a semantic content version such as `1.0.0`.
6. Declare license, source, language coverage and publisher/provenance metadata.
7. Keep source references auditable and date-sensitive guidance fresh.
8. Run `--validate-pack` and `--verify-provenance` before distribution.

See [Knowledge Pack Provenance](pack_provenance.md) for the integrity and freshness model, and [`ECOSYSTEM.md`](../ECOSYSTEM.md) for repository boundaries.
