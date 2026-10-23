# Changelog

## [0.3.0] — proposed, not published

- Added separate publicly configurable lexical, BM25 and hybrid evidence calibrators.
- Added offline reciprocal-rank fusion (`hybrid`) without cross-backend score addition.
- Added optional `SectionConfig` for deterministic bounded section chunks and source headings.
- Added optional per-source backend scores and per-answer bounded evidence score, refusal codes, and deterministic explanations.
- Increased adaptive accuracy verification depth while retaining low-resource/survival resource choices.
- Added isolated invented evidence calibration and invariant tests and a pre-change diagnostic report.
- Preserved 0.2.2 raw lexical/BM25 score conventions and existing basic result shapes.

Publication requires a passed independent benchmark, documented trade-offs,
maintainer review and explicit authorization. No performance claim is made
until the untouched held-out evaluation has been completed and recorded.

## [0.2.2] — 2026-10-23

- Evidence-aware, strategy-specific abstention and a conservative decision profile.
