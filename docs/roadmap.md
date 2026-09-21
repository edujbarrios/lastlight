# Core Roadmap

This roadmap covers only `edujbarrios/lastlight`, the offline core runtime. UI, pack publishing, ingestion, native acceleration and generation experiments belong in companion repositories described in [`ECOSYSTEM.md`](../ECOSYSTEM.md).

## Current core

- Markdown directory and ZIP knowledge packs
- repeated `--knowledge` for multi-pack retrieval
- pack-level attribution
- pure-Python lexical and BM25 retrieval
- resource-adaptive retrieval policies
- confidence-aware refusal
- deterministic ES/EN routing
- pack validation, integrity indexes and provenance/freshness checks
- offline CLI, batch queries and field-guide output
- deterministic evaluation and constrained-device diagnostics

## Next core milestones

### Pack contract hardening

- canonical pack-relative fingerprint paths so directory and ZIP representations hash consistently
- explicit pack-format version field
- compatibility checks between core and pack format versions
- clearer distinction between integrity and publisher authenticity

### Runtime boundaries

- stable Python API for companion frontends and tools
- documented extension points for external retrieval accelerators
- structured machine-readable runtime/status output
- preserve zero-network and stdlib-only default behavior

### Safety and evaluation

- expand refusal regression coverage
- improve multilingual routing without hidden translation
- publish stable evaluation profiles for core retrieval behavior
- keep safety policy changes auditable and deterministic

### Portability

- continue validating ordinary Linux, Windows, macOS, Termux and low-resource ARM targets
- keep the pure-Python path as the compatibility baseline

## Outside this repository

The following are intentionally not core roadmap items:

- browser/desktop/mobile UI
- public knowledge-pack catalog
- curated knowledge content
- PDF/HTML ingestion and pack publishing
- digital-signing infrastructure
- C/Rust/native acceleration implementations
- experimental local generation/synthesis
- large hardware benchmark datasets and dashboards

Those belong in focused companion repositories rather than expanding the core into a monorepo.
