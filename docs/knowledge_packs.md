# Knowledge Packs

LastLight knowledge packs are ordinary directories or `.zip` files containing Markdown.
They can optionally include `lastlight-pack.json` at the pack root.

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

Build an audit index that includes pack metadata:

```bash
python3 src/main.py --build-index data/lastlight.index.json
```

## Community Pack Checklist

1. Use Markdown files with clear source-grounded instructions.
2. Add front matter with `title`, `language`, `tags`, and `priority` where useful.
3. Include `lastlight-pack.json` at the pack root.
4. Run `--pack-info`, `--self-check`, and `--eval` before publishing.
5. Prefer small topic-focused packs over large unreviewable bundles.
