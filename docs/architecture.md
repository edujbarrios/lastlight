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

`MarkdownKnowledgeRepository` keeps a deterministic in-process snapshot cache for repeated queries. Unchanged ZIP packs reuse parsed `KnowledgeDocument` values and parsed pack metadata after a lightweight archive file-stat check, avoiding repeated decompression, UTF-8 decoding, front-matter parsing, and SHA-256 hashing. Directory packs retain hot-reload behavior by scanning Markdown file metadata on each access; unchanged bodies reuse their parsed document objects, while additions, removals, renames, size changes, and normal filesystem edits change the snapshot fingerprint and trigger a reload. Pack manifests use the same file-fingerprint invalidation model. Cache entries are not retained when the source changes while it is being inspected.

The cache is deliberately process-local and ephemeral. It does not create a database or sidecar index, and callers still receive fresh list containers so application filtering cannot mutate cached repository state.

## Composite Repository

Multiple packs can be mounted together. `CompositeKnowledgeRepository` combines their documents into one retrieval corpus while retaining pack identity, version, source and local artifact path on each document. Packs remain separate files; they do not need to be merged or rewritten.

The composed document snapshot is also cached. When child repositories return the same immutable document objects and pack identity is unchanged, the composite layer reuses the already-decorated `KnowledgeDocument` values instead of repeating `dataclasses.replace()` across the full corpus. Any child snapshot or pack identity change rebuilds the composed corpus automatically.

This boundary is intentionally compatible with external catalogs and removable-media distribution: distribution can evolve independently from the offline runtime.

## Offline Index Builder

The optional index builder writes a human-readable JSON summary of a selected knowledge pack. It records pack metadata, document metadata, per-document SHA-256 hashes, token counts and term counts. The main query path does not require this index.

## Strategy Pattern

`RetrievalStrategy` defines search behavior. `LexicalRetrievalStrategy` implements deterministic lexical ranking. `BM25RetrievalStrategy` provides an optional in-memory BM25 ranker, and adaptive retrieval can select between core strategies under explicit resource constraints.

Documents of at least 4,000 characters use an internal hierarchical scoring layer before the selected retrieval strategy runs. Markdown structure is used first when available: ATX-heading sections become retrieval regions whose ranking titles preserve the heading hierarchy. Each region is then represented by bounded, paragraph-aware scoring units of at most 1,800 characters with up to 250 characters of complete trailing context carried into the next unit. Large documents without headings and guides containing a single oversized section therefore receive the same bounded ranking treatment instead of falling back to one flat document.

Lexical and BM25 score those internal units independently, then collapse them back to the best scored unit per original source document. Only after that collapse and the final `top_k` cut does LastLight build sentence windows and select passages. Passage extraction therefore runs only for results that can actually be returned, instead of spending CPU on losing chunks or lower-ranked sources.

Prepared retrieval units are cached by deterministic corpus signature for repeated queries. BM25 keeps its query-independent statistics cache on top of that unit cache. Lexical retrieval also caches query-independent body token counts, token sets, title/tag tokens, body lengths, and normalized searchable text, and expands/tokenizes each query once per corpus search rather than once per ranking unit. An unchanged large corpus therefore avoids repeated Markdown parsing, chunk construction, and lexical document tokenization across queries.

Any change to document path, source hash, title, tags, priority, or body invalidates the relevant prepared state. Documents below the large-document threshold retain the legacy document-level representation and established score behavior.

This hierarchical unit layer is intentionally internal: public results still expose the original document path, body, pack identity and provenance rather than synthetic chunk paths. The goal is to improve retrieval from manuals, field guides, and long unstructured notes without changing the Knowledge Pack contract or requiring pack authors to pre-split human-readable documents.

## Factory Pattern

`ApplicationFactory` wires repositories and retrieval strategies into `LastLightApp`.

## Command Pattern

Interactive mode, single-query mode, evaluation mode and system operations are command objects. The CLI selects a command and executes it; LastLight does not require background workers or persistent services.

## Value Objects

The domain layer uses dataclasses for `KnowledgeDocument`, `KnowledgePack`, `SearchQuery`, `SearchResult` and evaluation values.

## Verification boundary

The `core` GitHub Actions workflow runs the unit/integration suite on Python 3.10, 3.11, and 3.12, executes the core evaluation regression gate, validates the built distributions, installs the wheel in isolation, and verifies documented retrieval behavior.

## Dependency Boundaries

The application depends on interfaces. Markdown/ZIP storage and retrieval strategies are replaceable implementation details. The runtime depends only on local artifacts after download.

The repository deliberately excludes presentation, curated content, pack-authoring/ingestion pipelines, optional native acceleration, large benchmark/energy tooling and generation experiments. Browser interfaces, public catalogs, PDF/HTML ingestion, deterministic publishing workflows, native backends, hardware research and experimental generation belong in companion repositories. See [`ECOSYSTEM.md`](../ECOSYSTEM.md).

Pure Python is the compatibility baseline. Companion projects may depend on LastLight contracts, but LastLight must not depend on those projects.
