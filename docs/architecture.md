# Architecture

LastLight uses clean architecture principles without heavy ceremony.

## Repository Pattern

`KnowledgeRepository` defines how the application obtains documents. `MarkdownKnowledgeRepository` implements that interface by recursively discovering Markdown files under `knowledge/`.

The same repository can also read a `.zip` knowledge pack. Markdown files inside the archive are loaded directly with the Python standard library, without extracting files or building an external database.

## Offline Index Builder

The optional index builder writes a human-readable JSON summary of the current knowledge base. It records document metadata, token counts, and term counts. The main query path does not require this index, so normal startup remains simple and low-cost.

## Strategy Pattern

`RetrievalStrategy` defines search behavior. `LexicalRetrievalStrategy` implements deterministic lexical ranking. `BM25RetrievalStrategy` implements an optional in-memory BM25 ranker for v0.2 experiments.

## Factory Pattern

`ApplicationFactory` wires the repository and retrieval strategy into `LastLightApp`.

## Command Pattern

Interactive mode, single-query mode, and evaluation mode are command objects. The CLI only selects a command and executes it.

Index building and streaming query output are also command-level behaviors. They do not introduce background workers or persistent services.

## Value Objects

The domain layer uses dataclasses for `KnowledgeDocument`, `SearchQuery`, `SearchResult`, and `EvaluationCase`.

## Dependency Boundaries

The application depends on interfaces. Markdown storage and lexical ranking are replaceable implementation details.

## Future Evolution

Future versions can add compressed packs, optional offline indexing, and citation-aware local generation without changing the knowledge contribution workflow.

## Experimental Synthesis

The optional `--synthesize` mode trains a tiny n-gram model only on the selected retrieved passage. It prints a generated note, the citation, and the original passage. This keeps the retrieval result visible and avoids using unsourced external knowledge.

## Optional Native Core

The optional C core is deliberately narrow. It counts token matches through a small `ctypes` bridge, while parsing, ranking, confidence scoring, and safety formatting remain in Python. If the native library is absent, the strategy falls back to Python match counting.
