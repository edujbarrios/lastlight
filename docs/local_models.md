# Tiny Local Model Packs

LastLight can build experimental local n-gram model packs from the Markdown knowledge base.

These models are:

- local
- deterministic
- JSON
- auditable
- optional
- not used by the default answer path

Build a model:

```bash
python src/main.py --build-model data/lastlight.model.json
```

Inspect a model:

```bash
python src/main.py --model-info data/lastlight.model.json
```

Change the n-gram order:

```bash
python src/main.py --build-model data/lastlight.model.json --model-order 3
```

Generated model files are ignored by git by default through `*.model.json`.

## Why This Exists

The goal is research, not fluency. A tiny local model pack lets contributors inspect how much language structure can be preserved in a small, deterministic artifact derived only from the local knowledge base.

The default LastLight behavior remains retrieval-first. The cited Markdown passage is still the authority.

