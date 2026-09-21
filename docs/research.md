# Research Notes

LastLight Core asks:

What is the smallest amount of software, computation and storage required to preserve useful **retrieval** under severe constraints?

The core hypothesis is that a transparent retrieval system over human-readable, auditable knowledge packs can remain useful even when modern AI infrastructure is unavailable.

Core research directions include:

- comparing lexical ranking with BM25 on small local corpora
- testing multilingual and multi-pack retrieval
- improving refusal behavior under adversarial and out-of-domain queries
- keeping provenance and integrity checks cheap and inspectable
- preserving predictable behavior on constrained devices without hidden services

Generative experiments, native acceleration, large stress datasets, hardware profiles and energy/latency experiments are intentionally outside the core. They belong in companion repositories such as `lastlight-labs`, `lastlight-native` and `lastlight-bench`.

## Core regression suite

The core keeps `data/eval_core.jsonl`, the small hand-curated seed suite used to catch retrieval and refusal regressions. Cases may declare one expected tag, several tags for a multi-intent query, or `should_refuse` for requests that the mounted corpus cannot safely support.

Decision metrics use `HIGH` and `MEDIUM` confidence as acceptance:

- **False accept:** an expected-refusal case receives an accepted result.
- **False refusal:** an answerable case has no accepted result.
- **Answer precision:** accepted answerable cases divided by all accepted cases.
- **Refusal recall:** correctly refused cases divided by all expected-refusal cases.

The larger generated 238-case stress suite, category dashboards, reproducible hardware profiles and power measurements are benchmark/research artifacts rather than runtime requirements. They should live in `lastlight-bench`, which can depend on the core without making the core depend on them.

BM25 remains intentionally small: scores are computed in memory at query time, avoiding a persistent vector or search service.

See [`ECOSYSTEM.md`](../ECOSYSTEM.md) for the boundary between core research and companion projects.
