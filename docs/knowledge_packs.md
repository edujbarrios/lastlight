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
```

The export command prints a SHA-256 checksum so the copied pack can be verified
on another machine.

Build an audit index that includes pack metadata:

```bash
python3 src/main.py --build-index data/lastlight.index.json
```

The audit index includes pack metadata and per-document SHA-256 hashes.

## Community Pack Checklist

1. Use Markdown files with clear source-grounded instructions.
2. Add front matter with `title`, `language`, `tags`, and `priority` where useful.
3. Place documents under language sections such as `en/` and `es/`.
4. Include `lastlight-pack.json` at the pack root.
5. Run `--pack-info`, `--validate-pack`, `--self-check`, and `--eval` before publishing.
6. Export with `--export-pack` when distributing a `.zip` pack.
7. Prefer small topic-focused packs over large unreviewable bundles.
