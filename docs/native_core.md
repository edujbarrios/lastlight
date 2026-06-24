# Optional C Retrieval Core

LastLight's default retrieval path is pure Python. The optional C core is an experiment for constrained devices where a small native function may help with token-match filtering.

The C core is not required. If no compiled library is present, `--strategy c-lexical` automatically falls back to the Python implementation for the native match-count step.

## Build

Use a system C compiler:

```bash
python tools/build_c_core.py
```

You can also pass a compiler explicitly:

```bash
python tools/build_c_core.py --cc gcc
```

The generated library is written under `native/` and is intentionally ignored by git:

- Windows: `native/lastlight_core.dll`
- Linux: `native/liblastlight_core.so`
- macOS: `native/liblastlight_core.dylib`

## Use

```bash
python src/main.py --strategy c-lexical "how do I purify water"
python src/main.py --strategy c-lexical --eval
```

## Design

The native core only counts token matches. Markdown loading, metadata parsing, safety checks, confidence scoring, source formatting, and fallback behavior remain in Python.

This keeps the optional native surface small enough to audit.

