# Low-Power Design

LastLight Core is designed to behave like a tiny emergency utility.

It avoids:

- polling
- background work
- animations
- telemetry
- network calls
- external databases
- expensive startup indexing
- required native extensions

The core loads local Markdown packs, ranks them deterministically, returns sourced passages, and exits. This keeps behavior inspectable and reduces idle resource use.

The optional audit index is created only when explicitly requested. Streaming output only flushes existing terminal output; neither feature starts a service, watches files, or performs background work.

The platform self-check is also explicit and one-shot. It reports Python version, platform, terminal availability, knowledge discovery, network independence, and dependency policy, then exits.

Pure Python is the compatibility baseline. Native acceleration, hardware benchmarking, browser interfaces, pack-authoring pipelines, and generation experiments are intentionally outside this repository and can evolve as companion projects without changing the offline core contract.
