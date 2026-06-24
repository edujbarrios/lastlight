"""Compatibility checks for constrained offline environments."""

from __future__ import annotations

import os
import platform
import sys
from dataclasses import dataclass
from pathlib import Path

from .interfaces import KnowledgeRepository

MIN_PYTHON = (3, 10)


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


def run_self_check(repository: KnowledgeRepository) -> list[CheckResult]:
    documents = repository.list_documents()
    return [
        _python_version_check(),
        _platform_check(),
        CheckResult(
            "terminal",
            bool(getattr(sys.stdout, "isatty", lambda: False)()) or not sys.stdout.closed,
            "stdout is available",
        ),
        CheckResult(
            "knowledge",
            bool(documents),
            f"{len(documents)} markdown document(s) discovered",
        ),
        CheckResult(
            "network",
            True,
            "no network capability is required by LastLight",
        ),
        CheckResult(
            "dependencies",
            True,
            "Python standard library only",
        ),
    ]


def format_self_check(results: list[CheckResult]) -> str:
    lines = [
        "LastLight self-check",
        f"Python: {platform.python_version()}",
        f"Platform: {platform.platform()}",
        f"Machine: {platform.machine() or 'unknown'}",
        f"TERMUX_VERSION: {os.environ.get('TERMUX_VERSION', 'not set')}",
        "",
    ]
    for result in results:
        status = "OK" if result.ok else "FAIL"
        lines.append(f"[{status}] {result.name}: {result.detail}")
    return "\n".join(lines)


def is_low_resource_target() -> bool:
    machine = platform.machine().casefold()
    termux = bool(os.environ.get("TERMUX_VERSION") or "com.termux" in os.environ.get("PREFIX", ""))
    arm = machine.startswith(("arm", "aarch", "armv"))
    return termux or arm


def suggested_python_command() -> str:
    if os.name == "nt":
        return "python"
    return "python3"


def _python_version_check() -> CheckResult:
    current = sys.version_info[:3]
    ok = current >= MIN_PYTHON
    return CheckResult(
        "python",
        ok,
        f"requires >= {MIN_PYTHON[0]}.{MIN_PYTHON[1]}, found {current[0]}.{current[1]}.{current[2]}",
    )


def _platform_check() -> CheckResult:
    low_resource_note = "low-resource target detected" if is_low_resource_target() else "general platform"
    cwd = Path.cwd()
    return CheckResult("platform", True, f"{low_resource_note}; cwd={cwd}")

