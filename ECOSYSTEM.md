# LastLight Ecosystem

`edujbarrios/lastlight` is the **core runtime**. It should remain small, auditable, offline-first, and independently useful.

The project is intended to evolve as a family of focused repositories rather than a monorepo.

## Core repository: `lastlight`

Owns only the stable offline engine and contracts:

- knowledge-pack loading from directories and `.zip` files
- multi-pack composition and pack-level attribution
- retrieval, ranking and passage selection
- confidence/refusal behavior and safety formatting
- language routing
- pack validation, integrity and provenance verification
- core CLI and evaluation interfaces
- resource-aware runtime behavior

The core must never require a network connection, browser, hosted service, account, telemetry backend, or external database.

## Planned companion repositories

### `lastlight-web`

Local browser UI for the core runtime. It can show mounted packs, provenance, confidence and session history without changing retrieval semantics.

Dependency direction: `lastlight-web` depends on `lastlight`; the core must not depend on the UI.

### `lastlight-hub`

Public website/catalog for discovering and reading knowledge packs online and downloading versioned `.zip` artifacts.

Possible responsibilities:

- browse/search packs by topic, language and region
- human-readable pack pages
- version/changelog display
- provenance/freshness metadata
- ZIP and checksum publication
- optional signature/trust information later

The hub is a distribution convenience, never a runtime dependency.

### `lastlight-packs`

Source repository for curated knowledge packs and their release artifacts. Content review, sourcing and update cadence live here rather than in the core engine.

Possible pack families include water, first aid, blackout, communications, navigation, shelter, wildfire and region-specific variants.

### `lastlight-pack-tools`

Authoring and publishing utilities that are useful to pack maintainers but unnecessary for normal retrieval.

Candidates:

- PDF/HTML/text ingestion
- manifest scaffolding
- deterministic ZIP builds
- source/reference linting
- checksum/fingerprint generation
- future digital signing
- catalog metadata generation

### `lastlight-native`

Optional accelerated retrieval backends implemented in C, Rust or another low-level language. The contract should remain compatible with the pure-Python core and fall back cleanly when an accelerator is unavailable.

### `lastlight-bench`

Reproducible evaluation and constrained-hardware benchmarking:

- stress datasets
- retrieval comparisons
- latency/memory reports
- RAPL/external energy measurements
- Raspberry Pi / Android / low-power device profiles

This keeps research artifacts and large benchmark outputs out of the runtime repository.

### `lastlight-labs`

Experimental work that should not define core behavior, such as tiny local generation models, synthesis experiments or alternative retrieval research.

## Repository rule

A feature belongs in `lastlight` only when the offline retrieval runtime needs it to load, verify, search, attribute or safely return local knowledge.

If a feature is primarily about presentation, distribution, content production, optional acceleration, hardware research or experimentation, it belongs in a companion repository.

## Possible future GitHub organization

If the ecosystem grows beyond a few repositories, moving them under a dedicated GitHub organization such as `lastlight-project` would make the ownership model clearer:

```text
lastlight-project/
├── lastlight
├── lastlight-web
├── lastlight-hub
├── lastlight-packs
├── lastlight-pack-tools
├── lastlight-native
├── lastlight-bench
└── lastlight-labs
```

The core should remain independently clonable and fully functional with local packs even if every companion service is unavailable.
