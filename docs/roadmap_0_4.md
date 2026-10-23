# LastLight 0.4.0 research and release plan

**Status: baseline preflight, not a release.** LastLight 0.3.0 remains the
published library version. This preparatory branch changes no retrieval,
calibration, packaging version, corpus, benchmark labels, or benchmark metrics.

## Corpus-v4 provenance blocker

The requested corpus-v4 experiment reports **44 lengthy documents** (28 English
and 16 Spanish), **21,376 words**, and **240 cases** (168 answerable and 72
refusals). These figures are supplied by the maintainer, not independently
reproduced results.

On 2026-10-23, the public `edujbarrios/lastlight-bench` `main` branch
(commit `2c353960eb9bafca1f567ff8e8f25aecc789eb87`) contains **32
Markdown documents**, **160 cases** (108 answerable and 52 refusals), and a
corpus manifest declaring version `3.0.0`. No public branch exposes a
matching 44-document corpus-v4 checkout.

A 160-case result may be useful as a separate historical comparison, but it
**cannot verify** the 240-case findings, the requested language/difficulty
slices, or the 0.4.0 release targets. Do not begin score/threshold tuning until
the actual v4 corpus and labels can be inspected and baseline behavior
reproduced.

## Existing evidence (maintainer-reported, not independently reproduced)

| Strategy | Top-1 | Precision | Answerable recall | Refusal recall | False accept |
|---|---:|---:|---:|---:|---:|
| Lexical | 81.0% | 94.9% | 56.0% | 98.6% | 1.4% |
| BM25 | 87.5% | 92.2% | 63.1% | 95.8% | 4.2% |
| Hybrid | 86.3% | 95.5% | 50.6% | 98.6% | 1.4% |
| Adaptive balanced | 85.7% | 92.1% | 62.5% | 97.2% | 2.8% |
| Adaptive accuracy | 87.5% | 92.3% | 64.3% | 95.8% | 4.2% |

These figures suggest that acceptance, not just document ranking, is the
primary bottleneck. They are **hypotheses for investigation**, not a validated
before-and-after result.

## Read-only baseline tooling

1. `tools/benchmark_v4_readiness.py` verifies document and case counts,
   language counts, answerability counts, the benchmark Git SHA, and SHA-256
   fingerprints of corpus documents and case-label bytes. It refuses v3.
2. `tools/controlled_v4_comparison.py` installs LastLight **0.2.2** and
   **0.3.0** in separate virtual environments, checks installed versions,
   and uses the unchanged external `lastlight_bench.runner.run_benchmark`
   metrics in independent processes. It performs three warmed repetitions,
   alternates configuration order, captures raw cases and aggregates, and
   verifies external input fingerprints after measurement. Hybrid is evaluated
   on 0.3.0 only, since it is not available in 0.2.2.
3. `tools/diagnose_v4_false_rejections.py` separately audits answerable
   cases with the expected document at Top-1 but no accepted answer. It records
   language, difficulty, tags, refusal reason and code, query/passage coverage,
   calibrated score, candidate margin, backend agreement, backend raw scores,
   and source sections when those API fields exist. This is **outside** the
   timed benchmark so the official metrics stay unchanged.
4. The `benchmark-v4-readiness` workflow preserves readiness JSON as an
   artifact. If the external repository is still v3, the comparison is
   **skipped explicitly** rather than using v3 as v4.

Example, after an accessible and pinned v4 checkout exists:

```bash
python tools/benchmark_v4_readiness.py \
    --checkout /path/to/lastlight-bench \
    --report /tmp/v4-preflight.json
python tools/controlled_v4_comparison.py \
    --benchmark /path/to/lastlight-bench \
    --workspace /tmp/controlled-venvs \
    --output /tmp/v4-comparison --repeats 3
```

The benchmark's query-timing loop includes `tracemalloc`; its measured
latency and Python allocation peak do **not** represent plain query latency
or process RSS. Cold-build time, uninstrumented warm latency, process RSS,
CPU drift, and memory per document/chunk must be measured separately before
making resource claims.

## Implementation design once baseline is reproduced

- **Evidence classification:** distinct deterministic ACCEPT, REVIEW and
  REFUSE states. Structural refusals (live data, private information,
  credentials, authority decisions) are immutable and never reviewed into
  acceptance by score increases. Treat requested-but-absent facts separately
  from out-of-domain and ambiguous candidates.
- **Review zone:** bounded extra verification for near-threshold candidates
  only. Recover substantive neighboring or complementary sections from the
  same source, track condition/negation/quantity evidence, and re-evaluate
  discriminative query terms. Never fabricate missing content or merge
  incompatible source documents.
- **Hybrid:** retain raw backend scores independently; estimate source
  agreement and normalized margins rather than rejecting on compressed RRF
  score ratios. Eliminate duplicate passage extraction or ranking preparation
  where profiling demonstrates actual overhead.
- **Adaptive:** survival has a minimal lexical path, balanced permits one
  bounded reconsideration, accuracy uses more candidates and multi-section
  verification. Record optional internal phase timings, off by default.
- **Bilingual:** audit Spanish tokenization and coverage using equivalent
  English/Spanish fixtures, conservative morphology, negation preservation,
  and separate language calibration only when independently supported.
- **Invariants:** score bounds, monotonic policy thresholds, deterministic
  decisions, preserved source attribution, no Hybrid duplicates, and no
  structural-refusal overrides.

Calibration requires **separate independently authored synthetic calibration,
validation and frozen test sets**. The 240 external holdout labels must not be
used for tuning or per-question exceptions.

## Proposed release gate

After actual v4 data is available, reproduce the maintainer's 0.3.0 baseline,
run the controlled 0.2.2/0.3.0 comparison, classify all false rejections,
and implement/test the above design. Then run Ruff, mypy, all unit tests on
Python 3.10/3.11/3.12, build wheel and sdist, install a wheel in a clean
environment, test the installed distribution, and report complete v4 results
with language/difficulty/tag slices and adverse trade-offs.

The maintainer's proposed targets are BM25 recall >=0.72, Hybrid recall >=0.68,
adaptive accuracy recall >=0.75, precision >=0.92, refusal recall >=0.95,
false accept <=0.05, BM25 and Hybrid Top-1 >=0.87, Hybrid latency reduction
>=25%, and EN/ES recall gap <8 percentage points. **None is yet verified**.
A suitable version after completing compatible new features would be
**0.4.0**, not another 0.3.0 publication.

A release should be a reviewed, validated implementation rather than a version
number change. Do not create a v0.4.0 tag, GitHub Release, or PyPI upload from
this baseline-preparation branch.
