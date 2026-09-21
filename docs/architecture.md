# Architecture

LastLight uses clean architecture principles without heavy ceremony.

## Repository Pattern

`KnowledgeRepository` defines how the application obtains documents. `MarkdownKnowledgeRepository` reads either a directory pack or a `.zip` pack directly with the Python standard library, without extraction or an external database.

The repository itself no longer ships an embedded emergency corpus. The project-level `knowledge/README.md` is format documentation and is deliberately excluded from retrieval. Real knowledge is expected to arrive through one or more independently distributed packs supplied with `--knowledge`.

A pack can include `lastlight-pack.json` at its root. The manifest records pack name, version, languages, license, source and provenance metadata. LastLight treats it as audit metadata, not executable configuration, and can still read a pack when it is absent.

Root-level `README.md` files are also treated as pack documentation rather than searchable knowledge. Markdown below language/topic directories remains normal retrieval content.

## Composite Repository

Multiple packs can be mounted together. `CompositeKnowledgeRepository` combines their documents into one retrieval corpus while retaining pack identity, version, source and local artifact path on each document. Packs remain separate files; they do not need to be merged or rewritten.

This boundary is intentionally compatible with a future external knowledge catalog: distribution can evolve independently from the offline runtime.

## Offline Index Builder

The optional index builder writes a human-readable JSON summary of a selected knowledge pack. It records pack metadata, document metadata, per-document SHA-256 hashes, token counts and term counts. The main query path does not require this index.

## Strategy Pattern

`RetrievalStrategy` defines search behavior. `LexicalRetrievalStrategy` implements deterministic lexical ranking. `BM25RetrievalStrategy` provides an optional in-memory BM25 ranker, and adaptive retrieval can select among available strategies under explicit resource constraints.

## Factory Pattern

`ApplicationFactory` wires repositories and retrieval strategies into `LastLightApp`.

## Command Pattern

Interactive mode, single-query mode, evaluation mode and system operations are command objects. The CLI selects a command and executes it; LastLight does not require background workers or persistent services.

## Value Objects

The domain layer uses dataclasses for `KnowledgeDocument`, `KnowledgePack`, `SearchQuery`, `SearchResult` and evaluation values.

## Dependency Boundaries

The application depends on interfaces. Markdown/ZIP storage and retrieval strategies are replaceable implementation details. A future web platform may publish packs, but the runtime depends only on local artifacts after download.

## Experimental Synthesis

The optional `--synthesize` mode trains a tiny n-gram model only on the selected retrieved passage. It prints a generated note, the citation and the original passage, keeping the retrieval result visible and avoiding unsourced external knowledge.

## Optional Native Core

The optional C core is deliberately narrow. It counts token matches through a small `ctypes` bridge, while parsing, ranking, confidence scoring and safety formatting remain in Python. If the native library is absent, the strategy falls back to Python match counting.

## Tiny Local Model Packs

The optional local model builder writes deterministic n-gram transitions to JSON. These model packs are research artifacts and are not required by the default answer path.
