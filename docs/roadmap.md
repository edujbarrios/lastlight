# Roadmap

## v0.1

- Markdown knowledge base
- Recursive discovery
- Deterministic retrieval
- CLI
- Tests
- Evaluation suite

## v0.2

- BM25 strategy: implemented as optional in-memory retrieval
- Better multilingual support: started with deterministic query expansion
- Improved chunking: implemented for cleaner passage selection

## v0.3

- Compressed knowledge packs: basic `.zip` Markdown loading implemented
- Offline index builder: optional JSON audit index implemented
- Streaming retrieval: line-flushed terminal output implemented

## v0.4

- Tiny n-gram language model: experimental `--synthesize` mode implemented
- Citation-aware generation based exclusively on retrieved passages: implemented with warning, citation, and original passage display

## v0.5

- Raspberry Pi support: documented with `--self-check`
- Termux support: documented with `--self-check`
- Old laptop support: documented with low-power usage notes

## v0.6

- Optional C retrieval core: implemented as `--strategy c-lexical` with Python fallback

## v0.7

- Tiny local language models: auditable JSON n-gram model packs implemented
- Research into ultra-low-power AI systems: local model size and transition summaries available through `--model-info`

## v1.0

- Community-maintained emergency knowledge repository: started with pack manifest conventions, validation, and contribution checklist
- Multilingual knowledge packs: optional `lastlight-pack.json` metadata implemented for directories and `.zip` packs
- Reproducible offline intelligence system: audit indexes now include pack metadata
