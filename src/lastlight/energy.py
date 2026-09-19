"""Hardware energy counters for reproducible offline benchmarks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

UNIT_TO_MWH = {
    "uj": 1.0 / 3_600_000.0,
    "mj": 1.0 / 3_600.0,
    "j": 1.0 / 3.6,
    "uwh": 1.0 / 1_000.0,
    "mwh": 1.0,
    "wh": 1_000.0,
}


@dataclass(frozen=True)
class EnergySnapshot:
    values_mwh: tuple[float, ...]
    max_values_mwh: tuple[float | None, ...] = ()


class EnergyMeter:
    """Minimal cumulative-energy meter interface."""

    name = "unknown"

    def sample(self) -> EnergySnapshot:
        raise NotImplementedError


class RaplEnergyMeter(EnergyMeter):
    """Read top-level Linux Intel/AMD RAPL package energy counters."""

    name = "rapl-package"

    def __init__(self, zones: tuple[Path, ...]) -> None:
        if not zones:
            raise ValueError("at least one RAPL zone is required")
        self.zones = zones

    @classmethod
    def discover(cls, root: Path | str = "/sys/class/powercap") -> "RaplEnergyMeter | None":
        root_path = Path(root)
        if not root_path.exists():
            return None

        zones: list[Path] = []
        for energy_path in sorted(root_path.glob("*/energy_uj")):
            zone = energy_path.parent
            # Count package/root domains once; child domains would double count energy.
            if zone.name.count(":") > 1:
                continue
            if not energy_path.is_file():
                continue
            zones.append(zone)

        return cls(tuple(zones)) if zones else None

    def sample(self) -> EnergySnapshot:
        values: list[float] = []
        maxima: list[float | None] = []
        for zone in self.zones:
            values.append(
                _read_number(zone / "energy_uj") * UNIT_TO_MWH["uj"]
            )
            max_path = zone / "max_energy_range_uj"
            maxima.append(
                _read_number(max_path) * UNIT_TO_MWH["uj"]
                if max_path.is_file()
                else None
            )
        return EnergySnapshot(tuple(values), tuple(maxima))


class CounterFileEnergyMeter(EnergyMeter):
    """Read one cumulative hardware counter from a text file."""

    name = "counter-file"

    def __init__(self, path: Path | str, unit: str = "mwh") -> None:
        unit = unit.casefold()
        if unit not in UNIT_TO_MWH:
            raise ValueError(f"unsupported energy unit: {unit}")
        self.path = Path(path)
        self.unit = unit

    def sample(self) -> EnergySnapshot:
        value = _read_number(self.path) * UNIT_TO_MWH[self.unit]
        return EnergySnapshot((value,), (None,))


def energy_delta_mwh(before: EnergySnapshot, after: EnergySnapshot) -> float:
    if len(before.values_mwh) != len(after.values_mwh):
        raise ValueError("energy snapshots have different counter counts")

    maxima = before.max_values_mwh or tuple(None for _ in before.values_mwh)
    if len(maxima) != len(before.values_mwh):
        raise ValueError("energy snapshot max counter count does not match values")

    total = 0.0
    for index, (start, end) in enumerate(zip(before.values_mwh, after.values_mwh)):
        if end >= start:
            total += end - start
            continue
        maximum = maxima[index]
        if maximum is None:
            raise ValueError("energy counter decreased without a wrap range")
        total += (maximum - start) + end
    return total


def discover_energy_meter(
    source: str = "auto",
    counter_path: Path | str | None = None,
    counter_unit: str = "mwh",
    rapl_root: Path | str = "/sys/class/powercap",
) -> EnergyMeter | None:
    source = source.casefold()
    if source not in {"auto", "rapl", "counter", "estimate"}:
        raise ValueError(f"unsupported energy source: {source}")

    if source == "estimate":
        return None
    if source == "counter":
        if counter_path is None:
            raise ValueError("counter energy source requires a counter path")
        return CounterFileEnergyMeter(counter_path, counter_unit)
    if source == "rapl":
        meter = RaplEnergyMeter.discover(rapl_root)
        if meter is None:
            raise ValueError("no top-level RAPL energy counters were found")
        return meter

    if counter_path is not None:
        return CounterFileEnergyMeter(counter_path, counter_unit)
    return RaplEnergyMeter.discover(rapl_root)


def _read_number(path: Path) -> float:
    try:
        return float(path.read_text(encoding="utf-8").strip())
    except OSError as error:
        raise RuntimeError(f"could not read energy counter {path}: {error}") from error
    except ValueError as error:
        raise RuntimeError(f"invalid numeric energy counter {path}") from error
