from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import helpers  # noqa: F401
from lastlight.energy import (
    CounterFileEnergyMeter,
    EnergySnapshot,
    RaplEnergyMeter,
    discover_energy_meter,
    energy_delta_mwh,
)


class EnergyTests(unittest.TestCase):
    def test_counter_file_converts_joules_to_mwh(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            counter = Path(tmp) / "energy"
            counter.write_text("3.6\n", encoding="utf-8")
            sample = CounterFileEnergyMeter(counter, "j").sample()

        self.assertAlmostEqual(sample.values_mwh[0], 1.0, places=6)

    def test_delta_handles_monotonic_counter(self) -> None:
        before = EnergySnapshot((10.0, 20.0), (100.0, 100.0))
        after = EnergySnapshot((10.4, 20.7), (100.0, 100.0))

        self.assertAlmostEqual(energy_delta_mwh(before, after), 1.1, places=6)

    def test_delta_handles_counter_wrap(self) -> None:
        before = EnergySnapshot((9.0,), (10.0,))
        after = EnergySnapshot((1.0,), (10.0,))

        self.assertAlmostEqual(energy_delta_mwh(before, after), 2.0, places=6)

    def test_rapl_discovery_ignores_child_domains(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "intel-rapl:0"
            package.mkdir()
            (package / "energy_uj").write_text("3600000", encoding="utf-8")
            (package / "max_energy_range_uj").write_text(
                "36000000", encoding="utf-8"
            )
            child = root / "intel-rapl:0:0"
            child.mkdir()
            (child / "energy_uj").write_text("9999999", encoding="utf-8")

            meter = RaplEnergyMeter.discover(root)
            self.assertIsNotNone(meter)
            assert meter is not None
            sample = meter.sample()

        self.assertEqual(len(sample.values_mwh), 1)
        self.assertAlmostEqual(sample.values_mwh[0], 1.0, places=6)
        self.assertAlmostEqual(sample.max_values_mwh[0] or 0.0, 10.0, places=6)

    def test_auto_prefers_explicit_counter_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            counter = root / "meter.txt"
            counter.write_text("2.5", encoding="utf-8")

            meter = discover_energy_meter(
                "auto",
                counter_path=counter,
                counter_unit="mwh",
                rapl_root=root / "missing",
            )

        self.assertIsInstance(meter, CounterFileEnergyMeter)

    def test_rapl_source_fails_when_counter_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                discover_energy_meter("rapl", rapl_root=Path(tmp) / "missing")


if __name__ == "__main__":
    unittest.main()
