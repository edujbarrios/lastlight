# Architecture

LastLight uses a small package-oriented architecture with no runtime dependencies outside the Python standard library.

## Source layout

The implementation under `src/lastlight/` is grouped by responsibility:

```text
lastlight/
├── application/   # app service, factory, sessions, language routing
├── cli/           # argument parsing and command handlers
├── evaluation/    # deterministic regression evaluation
├── knowledge/     # repositories, Markdown/ZIP packs, validation, provenance, index
├── retrieval/     # tokenization, chunking, ranking, lexical/BM25/adaptive search
├── safety/        # confidence-aware answers and deterministic follow-up checks
└── shared/        # domain models, protocols, compatibility and path utilities
```

A few thin top-level modules remain as compatibility facades for established imports such as `lastlight.factory` and `lastlight.repository`. New implementation code belongs in the responsibility packages above.

`src/main.py` remains the stable executable entrypoint.

## Repository Pattern

`KnowledgeRepository` defines how the application obtains documents. `MarkdownKnowledgeRepository` reads either a directory pack or a `.zip` pack directly with the Python standard library, without extraction or an external database.

The repository itself does not ship an embedded emergency corpus. The project-level `knowledge/README.md` is format documentation and is deliberately excluded from retrieval. Real knowledge is expected to arrive through one or more independently distributed packs supplied with `--knowledge`.

A pack can include `lastlight-pack.json` at its root. The manifest records pack name, version, languages, license, source and provenance metadata. LastLight treats it as audit metadata, not executable configuration, and can still read a pack when it is absent.

Root-level `README.md` files are treated as pack documentation rather than searchable knowledge. Markdown below language/topic directories remains normal retrieval content.

## Composite Repository

Multiple packs can be mounted together. `CompositeKnowledgeRepository` combines their documents into one retrieval corpus while retaining pack identity, version, source and local artifact path on each document. Packs remain separate files; they do not need to be merged or rewritten.

This boundary is intentionally compatible with external catalogs and removable-media distribution: distribution can evolve independently from the offline runtime.

## Offline Index Builder

The optional index builder writes a human-readable JSON summary of a selected knowledge pack. It records pack metadata, document metadata, per-document SHA-256 hashes, token counts and term counts. The main query path does not require this index.

## Strategy Pattern

`RetrievalStrategy` defines search behavior. `LexicalRetrievalStrategy` implements deterministic lexical ranking. `BM25RetrievalStrategy` provides an optional in-memory BM25 ranker, and adaptive retrieval can select between core strategies under explicit resource constraints.

## Factory Pattern

`ApplicationFactory` wires repositories and retrieval strategies into `LastLightApp`.

## Command Pattern

Interactive mode, single-query mode, evaluation mode and system operations are command objects. The CLI selects a command and executes it; LastLight does not require background workers or persistent services.

## Value Objects

The domain layer uses dataclasses for `KnowledgeDocument`, `KnowledgePack`, `SearchQuery`, `SearchResult` and evaluation values.

## Verification boundary

The `core` GitHub Actions workflow runs the unit/integration suite on Python 3.10 and 3.12 and performs CLI smoke tests against the committed English example pack: pack validation, a natural-language retrieval query and an expected refusal.

## Dependency Boundaries

The application depends on interfaces. Markdown/ZIP storage and retrieval strategies are replaceable implementation details. The runtime depends only on local artifacts after download.

The repository deliberately excludes presentation, curated content, pack-authoring/ingestion pipelines, optional native acceleration, large benchmark/energy tooling and generation experiments. Browser interfaces, public catalogs, PDF/HTML ingestion, deterministic publishing workflows, native backends, hardware research and experimental generation belong in companion repositories. See [`ECOSYSTEM.md`](../ECOSYSTEM.md).

Pure Python is the compatibility baseline. Companion projects may depend on LastLight contracts, but LastLight must not depend on those projects.
