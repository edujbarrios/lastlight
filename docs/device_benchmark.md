# Device Benchmark

The integrated device benchmark evaluates LastLight as a constrained system rather than timing one command in isolation.

It compares `lexical`, `bm25`, `c-lexical`, and balanced `adaptive` retrieval over the same deterministic evaluation cases and reports:

- Top-1 and Top-k accuracy;
- MRR;
- answer precision;
- refusal recall;
- answerable recall;
- mean and p95 retrieval latency;
- peak Python-traced memory during evaluation;
- measured or estimated energy per query;
- a safety-first strategy recommendation.

## Energy

The benchmark reuses LastLight's energy backends. In `auto` mode it uses Linux RAPL when available and otherwise labels the value as an estimate derived from elapsed time and the configured wattage. An explicit external cumulative counter can also be supplied.

Measured and estimated values remain labelled separately.

## Memory

The `Peak Python MB` column comes from Python's standard-library `tracemalloc`. It measures peak traced Python allocations during the evaluation run. It is portable and deterministic enough for comparisons inside LastLight, but it is not the same as whole-process RSS or total system memory.

The device section separately reports physical memory when the operating system exposes it through `sysconf`.

## Recommendation

The recommendation intentionally favors safety over raw recall or speed. Strategies are ranked by:

1. a safety score: 60% answer precision + 40% refusal recall;
2. Top-k accuracy;
3. lower energy/query;
4. lower p95 latency.

This policy makes the recommendation auditable. It is not a learned model and can be changed as the project's evaluation methodology evolves.

## Research use

For a publishable or CV-grade result, run the complete 238-case suite on each target device and use a real whole-device meter when claiming end-to-end energy/query. RAPL is appropriate when the claim is explicitly CPU/package energy.
