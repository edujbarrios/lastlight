# Constrained Platform Notes

LastLight targets ordinary Python installations on low-resource devices. It does not require package installation, a browser, a server, cloud credentials, telemetry, or background services.

Run a compatibility check:

```bash
python3 src/main.py --self-check
```

On Windows, use:

```bash
python src/main.py --self-check
```

## Raspberry Pi

Use the system Python when available:

```bash
python3 src/main.py "how do I purify water"
```

Recommended habits:

- keep the knowledge directory on local storage
- prefer lexical retrieval for the lowest compute path
- use `--build-index` only when explicitly auditing a knowledge pack
- avoid running evaluation repeatedly on battery unless needed

## Termux

From a Termux shell, run:

```bash
python src/main.py --self-check
python src/main.py "como ahorrar bateria del telefono"
```

The project does not need Android services, network permissions, or a web server. Keep knowledge packs in a readable local path and use `--knowledge path/to/pack.zip` when carrying compressed packs.

## Old Laptops

LastLight should run on old laptops as long as Python 3.10 or newer is available. The default retrieval mode reads Markdown files, ranks them, prints a sourced passage, and exits.

For the lowest power path:

```bash
python3 src/main.py "how do I save phone battery"
```

Avoid optional modes such as repeated evaluation, index building, and synthesis when battery is scarce.

