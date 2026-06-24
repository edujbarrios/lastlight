"""Build the optional LastLight C retrieval core with a system compiler."""

from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "native" / "lastlight_core.c"


def output_path() -> Path:
    system = platform.system().casefold()
    if system == "windows":
        return ROOT / "native" / "lastlight_core.dll"
    if system == "darwin":
        return ROOT / "native" / "liblastlight_core.dylib"
    return ROOT / "native" / "liblastlight_core.so"


def build_command(compiler: str, output: Path) -> list[str]:
    system = platform.system().casefold()
    if system == "windows" and compiler.lower().endswith("cl.exe"):
        return [compiler, "/LD", str(SOURCE), f"/Fe:{output}"]
    return [compiler, "-O2", "-shared", "-fPIC", str(SOURCE), "-o", str(output)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build optional LastLight C core.")
    parser.add_argument("--cc", default=None, help="C compiler command")
    args = parser.parse_args(argv)

    compiler = args.cc or shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
    if not compiler:
        print("No C compiler found. LastLight will keep using the Python retrieval core.")
        return 1

    output = output_path()
    command = build_command(compiler, output)
    subprocess.run(command, cwd=ROOT, check=True)
    print(f"Wrote optional C core: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

