"""Deterministic knowledge pack export."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from .repository import PACK_MANIFEST

ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def export_pack(source_dir: Path | str, output_path: Path | str) -> Path:
    source = Path(source_dir)
    output = Path(output_path)
    if not source.exists():
        raise ValueError(f"knowledge source does not exist: {source}")
    if not source.is_dir():
        raise ValueError("knowledge source must be a directory for export")

    files = [
        path
        for path in source.rglob("*")
        if path.is_file()
        and (path.name == PACK_MANIFEST or path.suffix.casefold() == ".md")
    ]
    if not files:
        raise ValueError("knowledge source contains no exportable files")

    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w") as archive:
        for path in sorted(files, key=lambda item: item.relative_to(source).as_posix()):
            relative_path = path.relative_to(source).as_posix()
            info = ZipInfo(relative_path, ZIP_TIMESTAMP)
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    return output
