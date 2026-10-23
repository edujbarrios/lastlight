# Changelog

## [0.3.1] — 2026-10-23

- Added read-only corpus-v4 benchmark identity and integrity checks.
- Added a controlled, independent-process 0.2.2 versus 0.3.0 comparison runner and a separate false-rejection audit utility for use when the actual v4 data becomes available.
- Added deterministic regression tests for benchmark identity, changed labels, and malformed answerability fields.
- Documented the reproducibility blocker and proposed 0.4.0 research/release gates.
- Updated the README with the latest-release badges for PyPI and GitHub and explicit 0.3.1 installation instructions.
- No changes to retrieval, calibration, public runtime APIs, or the external benchmark repository; no 0.4.0 performance improvements are claimed.


## [0.3.0] — 2026-10-23

- Added separate publicly configurable lexical, BM25 and hybrid evidence calibrators.
- Added offline reciprocal-rank fusion (`hybrid`) without cross-backend score addition.
- Added optional `SectionConfig` for deterministic bounded section chunks and source headings.
- Added optional per-source backend scores and per-answer bounded evidence score, refusal codes, and deterministic explanations.
- Increased adaptive accuracy verification depth while retaining low-resource/survival resource choices.
- Added isolated invented evidence calibration and invariant tests and a pre-change diagnostic report.
- Preserved 0.2.2 raw lexical/BM25 score conventions and existing basic result shapes.

Maintainer-approved publication following successful Python 3.10–3.12
library tests, static checks, wheel and sdist builds, and a clean-wheel
installation. A pre-release external diagnostic showed an acceptance-safety
trade-off; no benchmark threshold or infallibility claim is made.

## [0.2.2] — 2026-10-23

- Evidence-aware, strategy-specific abstention and a conservative decision profile.
