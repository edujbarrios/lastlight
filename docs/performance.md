# Performance and Energy Estimates

LastLight is designed to be small enough to run as an emergency terminal utility. The table below was generated with:

```bash
python tools/benchmark.py --iterations 7 --watts 15
```

These timings were measured on a local Windows 11 machine with Python 3.12.7 on 2026-06-24. They include Python process startup, Markdown discovery, retrieval, formatting, and process exit.

Electricity use is an estimate, not a direct hardware measurement. It assumes 15 W of active system power while the command runs:

```text
estimated_mWh = watts * seconds / 3.6
```

For exact electricity measurements, use a power meter, battery discharge telemetry, or hardware-specific power sensors.

| Operation | Median time | Min | Max | Estimated energy |
| --- | ---: | ---: | ---: | ---: |
| Lexical query | 194.8 ms | 181.2 ms | 229.2 ms | 0.8118 mWh |
| BM25 query | 197.1 ms | 170.6 ms | 227.7 ms | 0.8214 mWh |
| Lexical evaluation | 354.8 ms | 311.8 ms | 383.2 ms | 1.4782 mWh |
| BM25 evaluation | 334.0 ms | 303.5 ms | 405.1 ms | 1.3918 mWh |
| Unit tests | 238.6 ms | 227.9 ms | 297.4 ms | 0.9941 mWh |

## Interpretation

The default single-query path completes in under a quarter second on this machine and uses less than 1 mWh under the 15 W estimate. That supports LastLight's design goal: useful retrieval with very small compute, memory, and energy demands.

The numbers should be treated as a reproducible baseline, not a universal claim. Hardware, storage speed, Python version, operating system, antivirus scanning, thermal state, and corpus size can change results.

