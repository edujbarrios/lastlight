# Knowledge Packs

LastLight knowledge packs are ordinary directories or `.zip` files containing Markdown.
They can optionally include `lastlight-pack.json` at the pack root.
The bundled pack keeps English documents under `en/` and Spanish documents under `es/`.
Archive entries under hidden directories or `__MACOSX/` are ignored when loading `.zip` packs.

```json
{
  "name": "LastLight Core Emergency Knowledge Pack",
  "version": "0.1.0",
  "languages": ["en", "es"],
  "description": "Core offline emergency knowledge included with LastLight.",
  "license": "MPL-2.0",
  "source": "https://github.com/edujbarrios/lastlight"
}
```

The manifest is intentionally small. It helps people audit a pack before using it,
record which languages it claims to cover, and reproduce an offline capsule later.
If no manifest is present, LastLight still works and infers basic language coverage
from document front matter.

Inspect a pack:

```bash
python3 src/main.py --pack-info
python3 src/main.py --knowledge path/to/pack.zip --pack-info
```

Validate a pack before publishing it:

```bash
python3 src/main.py --validate-pack
python3 src/main.py --knowledge path/to/pack.zip --validate-pack
```

Export a directory pack as a deterministic `.zip`:

```bash
python3 src/main.py --export-pack dist/lastlight-core.zip
python3 src/main.py --export-pack dist/lastlight-core.zip --require-valid-pack
```

The export command prints a SHA-256 checksum so the copied pack can be verified
on another machine. Use `--require-valid-pack` to stop the export when validation
finds missing manifest fields or document-language mismatches.

Build an audit index that includes pack metadata:

```bash
python3 src/main.py --build-index data/lastlight.index.json
```

The audit index includes pack metadata and per-document SHA-256 hashes.

## Mounting Multiple Packs

Query, interactive, evaluation, local web, and `--list-knowledge` flows can mount more than one pack by repeating `--knowledge`:

```bash
python3 src/main.py \
  --knowledge packs/water-es.zip \
  --knowledge packs/first-aid-es.zip \
  --knowledge packs/blackout-es.zip \
  "como puedo potabilizar agua"
```

LastLight combines the mounted packs into one searchable corpus. Documents keep the pack name, version, source, and local pack path that produced them, so text and JSON answers can be traced back to the downloaded artifact.

This is intentionally compatible with a future web catalog: a user can download several independent `.zip` packs, verify each pack locally, then mount any combination without rebuilding LastLight or merging the archives together.

Pack-specific maintenance commands remain intentionally single-pack operations. For example, provenance verification and export should be run against each downloaded pack independently before the packs are mounted together for retrieval.

A typical future catalog workflow can therefore be:

```bash
python3 src/main.py --knowledge downloads/water-es.zip --verify-provenance
python3 src/main.py --knowledge downloads/first-aid-es.zip --verify-provenance
python3 src/main.py \
  --knowledge downloads/water-es.zip \
  --knowledge downloads/first-aid-es.zip \
  "necesito agua segura y primeros auxilios"
```

## Community Pack Checklist

1. Use Markdown files with clear source-grounded instructions.
2. Add front matter with `title`, `language`, `tags`, and `priority` where useful.
3. Place documents under language sections such as `en/` and `es/`.
4. Include `lastlight-pack.json` at the pack root.
5. Run `--pack-info`, `--validate-pack`, `--self-check`, and `--eval` before publishing.
6. Export with `--export-pack` when distributing a `.zip` pack.
7. Prefer small topic-focused packs over large unreviewable bundles.
