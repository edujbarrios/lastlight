# Adaptive Retrieval

LastLight can select a retrieval strategy at query time while keeping the decision deterministic and inspectable.

Enable it with:

```bash
python src/main.py --strategy adaptive "how do I purify water"
```

The planner considers four inputs:

1. query risk (`critical`, `high`, or `normal`),
2. operating mode (`survival`, `balanced`, or `accuracy`),
3. explicit energy and memory budgets,
4. a small local device profile: ARM/Termux detection, physical memory when available, battery percentage on Linux power-supply sysfs, and availability of the optional C core.

It never calls the network and adds no third-party dependency.

## Modes

### Survival

Caps retrieval to at most two results and prefers the optional C-backed lexical path when the native core is available. Otherwise it uses the deterministic Python lexical strategy.

```bash
python src/main.py --strategy adaptive --mode survival "find a safe water source"
```

### Balanced

This is the default adaptive policy. High-risk queries stay on the lexical safety-first path. Normal queries can use BM25 when no active resource constraint is detected.

```bash
python src/main.py --strategy adaptive --mode balanced "organize a field kit"
```

### Accuracy

Normal and high-risk queries may use BM25 when resources are not constrained. Critical-risk queries still stay on lexical retrieval because the current stress benchmark gives lexical retrieval the stronger refusal profile.

```bash
python src/main.py --strategy adaptive --mode accuracy "radio communication plan"
```

## Explicit budgets

Budgets are policy inputs, not measurements. They let an operator impose a hard resource preference even when LastLight cannot read battery or memory telemetry from the platform.

```bash
python src/main.py --strategy adaptive \
  --energy-budget-mwh 0.4 \
  --memory-budget-mb 64 \
  "how do I purify water"
```

An energy budget at or below `0.5 mWh/query` or a memory budget at or below `64 MB` selects the low-cost path. These thresholds are intentionally simple and auditable; they can be recalibrated from real-device benchmarks rather than hidden inside a learned model.

## Inspect the decision

Use `--plan` to run retrieval once and print the selected policy as JSON without formatting an answer:

```bash
python src/main.py --strategy adaptive --mode survival --plan "how do I purify water"
```

Example shape:

```json
{
  "battery_percent": 18.0,
  "effective_top_k": 2,
  "energy_budget_mwh": null,
  "low_resource_target": true,
  "memory_budget_mb": null,
  "memory_mb": 512,
  "mode": "survival",
  "reason": "survival mode caps retrieval cost",
  "risk": "high",
  "strategy": "c-lexical"
}
```

Values depend on the device and query. `c-lexical` still retains the existing Python fallback if the native library disappears after profiling.

## Decision priority

The planner applies constraints in this order:

1. survival mode or tight explicit resource budget,
2. low detected battery or ARM/Termux low-resource target,
3. critical-risk safety policy,
4. high-risk balanced policy,
5. requested accuracy/balanced policy.

This makes every strategy choice reproducible from the printed metadata.
