# Research Notes

LastLight asks:

What is the smallest amount of software, computation, storage, and energy required to preserve useful intelligence?

The v0.1 hypothesis is that a transparent retrieval system over human-readable Markdown can remain useful even when modern AI infrastructure is unavailable.

Future research directions include:

- measuring retrieval usefulness per kilobyte
- comparing lexical ranking with BM25 under tiny corpora
- testing multilingual knowledge packs
- evaluating constrained hardware performance
- exploring citation-only local generation

The v0.2 line keeps BM25 intentionally small: scores are computed in memory at query time, avoiding a persistent index until there is evidence that startup cost or corpus size requires one.

The v0.4 synthesis experiment is intentionally constrained. The n-gram model is trained only on the retrieved passage selected for the current query, and the original passage remains visible as the source of truth. This is a research step toward citation-aware generation, not a replacement for retrieval.

The v0.7 local model pack experiment builds JSON n-gram artifacts from the Markdown corpus. The current goal is measurement and auditability: document count, token count, transition count, and deterministic transitions. The model is not used by the default answer path.
