# Performance and Energy Measurement

LastLight is designed to be small enough to run as an emergency terminal utility. Timing and energy measurements are intentionally reproducible and explicit about whether energy is **measured** or **estimated**.

## Run the benchmark

```bash
python tools/benchmark.py --iterations 7
```

The default `--energy-source auto` behavior is:

1. use an explicit cumulative hardware counter if `--energy-counter` is supplied,
2. otherwise use top-level Linux RAPL package counters when available,
3. otherwise fall back to a timing-based estimate using `--watts` (15 W by default).

The output labels every row as `measured` or `estimated`; measured and estimated energy should not be compared as though they were the same instrumentation.

## Real hardware energy counters

### Linux RAPL

On supported Intel/AMD Linux systems, force package-energy measurement with:

```bash
python tools/benchmark.py --iterations 7 --energy-source rapl
```

LastLight reads top-level `energy_uj` counters under `/sys/class/powercap` and handles normal counter wraparound using `max_energy_range_uj` when exposed by the kernel.

RAPL measures CPU/package domains, not necessarily the complete wall-power draw of the device. It is still a real hardware counter, but the scope must be reported accurately.

### External or board-specific cumulative counter

For Raspberry Pi-class devices, USB power meters, development boards, or another sensor that can expose a cumulative energy value as a text file, use:

```bash
python tools/benchmark.py \
  --energy-source counter \
  --energy-counter /path/to/cumulative_energy \
  --energy-unit mwh
```

Supported counter units are `uj`, `mj`, `j`, `uwh`, `mwh`, and `wh`. The file must contain a cumulative numeric energy reading; LastLight samples it immediately before and after each benchmark iteration.

You can also pass `--energy-counter` with the default `auto` mode. In that case the explicit counter takes precedence over RAPL.

## Estimated fallback

To deliberately reproduce the original timing-based estimate:

```bash
python tools/benchmark.py --iterations 7 --energy-source estimate --watts 15
```

The fallback formula is:

```text
estimated_mWh = watts * seconds / 3.6
```

This is useful for historical comparison but is not a direct energy measurement.

## Historical baseline

The earlier baseline below was measured on Windows 11 with Python 3.12.7 on 2026-06-24 using an Intel Core i7 11th generation CPU and 16 GB DDR4 RAM. Its energy column used the 15 W estimate rather than a hardware energy counter.

| Operation | Median time | Min | Max | Estimated energy |
| --- | ---: | ---: | ---: | ---: |
| Lexical query | 194.8 ms | 181.2 ms | 229.2 ms | 0.8118 mWh |
| BM25 query | 197.1 ms | 170.6 ms | 227.7 ms | 0.8214 mWh |
| Lexical evaluation | 354.8 ms | 311.8 ms | 383.2 ms | 1.4782 mWh |
| BM25 evaluation | 334.0 ms | 303.5 ms | 405.1 ms | 1.3918 mWh |
| Unit tests | 238.6 ms | 227.9 ms | 297.4 ms | 0.9941 mWh |

## Interpretation

Report the measurement source alongside every energy number. Hardware, storage speed, Python version, operating system, antivirus scanning, thermal state, corpus size, meter resolution, and the electrical domain covered by the sensor can all change results.

For a CV or research result, prefer a whole-device external meter when claiming end-to-end energy/query. RAPL is appropriate when the claim is explicitly CPU/package energy. The estimator is useful only when clearly labelled as an estimate.
