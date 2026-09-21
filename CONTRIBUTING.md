# Contributing to LastLight Core

LastLight welcomes small, auditable contributions that improve offline retrieval under constrained conditions.

## Core code contributions

Changes in this repository should directly improve the runtime contract: loading/verifying packs, multi-pack composition, retrieval, language routing, refusal/safety behavior, provenance, or the dependency-free CLI/API.

Keep changes deterministic and standard-library only. Avoid network calls, telemetry, background workers, persistent daemons, GUI features, content catalogs, hardware benchmark suites, native-only dependencies, and experimental generation in the core.

Before opening a pull request:

```bash
python -m unittest discover -s tests
```

For retrieval-policy changes, also run the small core regression suite against an appropriate local knowledge pack:

```bash
python src/main.py --knowledge path/to/pack.zip --eval
```

## Knowledge contributions

The core repository does not contain curated emergency knowledge. `knowledge/README.md` documents the pack format only.

Knowledge content should be developed as independently versioned packs (planned home: `lastlight-packs`). Pack-authoring and ingestion utilities belong in `lastlight-pack-tools`.

## Companion projects

Presentation, distribution, curated content, native acceleration, hardware benchmarking, and experimental generation are intentionally separate from the core. See [ECOSYSTEM.md](ECOSYSTEM.md) before adding a new subsystem.

## Design priorities

- Simplicity
- Transparency
- Auditability
- Reliability
- Extensibility
- Low-power operation
- Long-term maintainability
