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
