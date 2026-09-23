"""Validate release metadata before building or publishing LastLight.

The checker is stdlib-only so it can run in a fresh checkout before release tooling
is installed. It verifies the duplicated package version contract and, when given a
Git tag, requires the release tag to be exactly ``v<version>``.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
PACKAGE_INIT = ROOT / "src" / "lastlight" / "__init__.py"


def _extract(pattern: str, text: str, label: str) -> str:
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        raise SystemExit(f"could not find {label}")
    return match.group(1)


def project_metadata() -> tuple[str, str, str]:
    pyproject = PYPROJECT.read_text(encoding="utf-8")
    package_init = PACKAGE_INIT.read_text(encoding="utf-8")

    project_name = _extract(r'^name\s*=\s*"([^"]+)"', pyproject, "project name")
    project_version = _extract(
        r'^version\s*=\s*"([^"]+)"', pyproject, "project version"
    )
    package_version = _extract(
        r'^__version__\s*=\s*"([^"]+)"', package_init, "package __version__"
    )
    return project_name, project_version, package_version


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate LastLight release metadata")
    parser.add_argument(
        "--tag",
        help="optional Git release tag; must equal v<project version>",
    )
    args = parser.parse_args(argv)

    project_name, project_version, package_version = project_metadata()

    if project_name != "lastlight":
        raise SystemExit(
            f"unexpected distribution name: {project_name!r}; expected 'lastlight'"
        )
    if project_version != package_version:
        raise SystemExit(
            "version mismatch: "
            f"pyproject.toml={project_version!r}, lastlight.__version__={package_version!r}"
        )

    expected_tag = f"v{project_version}"
    if args.tag is not None and args.tag != expected_tag:
        raise SystemExit(
            f"release tag mismatch: got {args.tag!r}, expected {expected_tag!r}"
        )

    print(f"Release metadata: PASS ({project_name} {project_version})")
    if args.tag is not None:
        print(f"Release tag: PASS ({args.tag})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
