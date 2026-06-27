# LastLight Benchmark

Run on Windows 11 with Python 3.12.7 on 2026-06-27.

Commands:

```bash
python src/main.py --eval --eval-output eval/results.json
python src/main.py --strategy bm25 --eval --eval-output eval/results-bm25.json
python tools/benchmark.py --iterations 7 --watts 15
```

Retrieval benchmark over 40 complex emergency cases:

| Strategy | Cases | Top-1 | Top-3 | MRR | Mean search latency |
| --- | ---: | ---: | ---: | ---: | ---: |
| Lexical | 40 | 97.50% | 100.00% | 0.988 | 31.586 ms |
| BM25 | 40 | 95.00% | 100.00% | 0.971 | 31.613 ms |

Process-level timing and estimated energy:

Benchmark iterations: 7
Assumed active system power: 15.0 W
Python: 3.12.7
Platform: Windows-11-10.0.26200-SP0

| Operation | Median time | Min | Max | Estimated energy |
| --- | ---: | ---: | ---: | ---: |
| Lexical query | 333.4 ms | 314.4 ms | 377.5 ms | 1.3894 mWh |
| BM25 query | 313.4 ms | 294.9 ms | 336.4 ms | 1.3060 mWh |
| Lexical evaluation | 1419.8 ms | 1323.5 ms | 1533.2 ms | 5.9159 mWh |
| BM25 evaluation | 1406.5 ms | 1329.5 ms | 1491.3 ms | 5.8606 mWh |
| Unit tests | 743.1 ms | 699.2 ms | 852.4 ms | 3.0961 mWh |

These are local measurements, not universal claims. Hardware, OS scheduling,
storage, antivirus, thermal state, Python version, and corpus size can change
timings.
