# Research Notes

LastLight asks:

What is the smallest amount of software, computation, storage, and energy required to preserve useful **retrieval** under severe constraints?

The core hypothesis is that a transparent retrieval system over human-readable, auditable knowledge packs can remain useful even when modern AI infrastructure is unavailable.

Core research directions include:

- measuring retrieval usefulness per kilobyte
- comparing lexical ranking with BM25 under tiny corpora
- testing multilingual and multi-pack retrieval
- improving refusal behavior under adversarial and out-of-domain queries
- evaluating constrained hardware performance
- measuring the cost of provenance and integrity checks

Generative experiments, tiny local language models and citation-aware synthesis are intentionally outside the core and belong in the planned `lastlight-labs` companion repository.

## Stress evaluation

The evaluation suite separates retrieval quality from the decision to answer. Cases may declare one expected tag, several tags for a multi-intent query, or `should_refuse` for requests that the local corpus cannot safely support.

The generated 238-case suite reports category-level results for spelling errors, short prompts, colloquial phrasing, regional Spanish, multi-intent scenarios, contradictory premises, adversarial instructions, and out-of-domain questions. Exact duplicate cases are removed. The 40 hand-curated seed cases remain separate so generated variants cannot be mistaken for independent human-authored scenarios.

Decision metrics use `HIGH` and `MEDIUM` confidence as acceptance:

- **False accept:** an expected-refusal case receives an accepted result.
- **False refusal:** an answerable case has no accepted result.
- **Answer precision:** accepted answerable cases divided by all accepted cases.
- **Refusal recall:** correctly refused cases divided by all expected-refusal cases.

BM25 remains intentionally small: scores are computed in memory at query time, avoiding a persistent index until there is evidence that startup cost or corpus size requires one.

See [`ECOSYSTEM.md`](../ECOSYSTEM.md) for the boundary between core research and companion projects.
