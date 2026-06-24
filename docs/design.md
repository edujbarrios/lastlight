# Low-Power Design

LastLight is designed to feel like a tiny emergency utility.

It avoids:

- polling
- background work
- animations
- progress bars
- telemetry
- network calls
- external databases
- expensive startup indexing

The v0.1 implementation loads Markdown files, ranks them deterministically, prints a sourced passage, and exits. This keeps behavior easy to inspect and reduces idle energy use.

Newer experimental features keep that constraint. The offline index builder runs only when explicitly requested, and streaming output only flushes existing response lines to the terminal. Neither feature starts a service, watches files, or performs background work.

The platform self-check is also explicit and one-shot. It reports Python version, platform, terminal availability, knowledge discovery, network independence, and dependency policy, then exits.
