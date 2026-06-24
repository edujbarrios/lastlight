# Contributing to LastLight

LastLight welcomes small, auditable contributions that improve offline usefulness under constrained conditions.

## Knowledge Contributions

1. Create a Markdown file.
2. Add optional metadata: `title`, `language`, `tags`, and `priority`.
3. Place it under `knowledge/`.
4. Run `make test`.
5. Run `make eval`.
6. Open a pull request.

Knowledge should be practical, source-conscious, calm, and clear. Do not add unsupported claims or advice that depends on hidden context.

## Code Contributions

Keep changes small, deterministic, and dependency-free. Prefer readable standard-library code over cleverness. Avoid network calls, telemetry, background workers, persistent daemons, GUI features, and third-party packages.

## Design Priorities

- Simplicity
- Transparency
- Auditability
- Reliability
- Extensibility
- Low-power operation
- Long-term maintainability

