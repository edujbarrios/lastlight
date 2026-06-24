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

