# Architecture

LastLight uses clean architecture principles without heavy ceremony.

## Repository Pattern

`KnowledgeRepository` defines how the application obtains documents. `MarkdownKnowledgeRepository` implements that interface by recursively discovering Markdown files under `knowledge/`.

## Strategy Pattern

`RetrievalStrategy` defines search behavior. `LexicalRetrievalStrategy` implements deterministic lexical ranking. `BM25RetrievalStrategy` implements an optional in-memory BM25 ranker for v0.2 experiments.

## Factory Pattern

`ApplicationFactory` wires the repository and retrieval strategy into `LastLightApp`.

## Command Pattern

Interactive mode, single-query mode, and evaluation mode are command objects. The CLI only selects a command and executes it.

## Value Objects

The domain layer uses dataclasses for `KnowledgeDocument`, `SearchQuery`, `SearchResult`, and `EvaluationCase`.

## Dependency Boundaries

The application depends on interfaces. Markdown storage and lexical ranking are replaceable implementation details.

## Future Evolution

Future versions can add compressed packs, optional offline indexing, and citation-aware local generation without changing the knowledge contribution workflow.
