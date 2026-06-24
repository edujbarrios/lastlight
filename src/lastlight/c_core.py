"""Optional ctypes bridge for the tiny native retrieval core."""

from __future__ import annotations

import ctypes
import os
import platform
from pathlib import Path

from .util import project_root


def native_library_name() -> str:
    system = platform.system().casefold()
    if system == "windows":
        return "lastlight_core.dll"
    if system == "darwin":
        return "liblastlight_core.dylib"
    return "liblastlight_core.so"


def native_library_path() -> Path:
    custom = os.environ.get("LASTLIGHT_C_CORE")
    if custom:
        return Path(custom)
    return project_root() / "native" / native_library_name()


class OptionalCCore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or native_library_path()
        self.library = self._load(self.path)

    @property
    def available(self) -> bool:
        return self.library is not None

    def count_matches(self, query_tokens: list[str], document_tokens: list[str]) -> int:
        if self.library is None:
            return _python_count_matches(query_tokens, document_tokens)

        query_array = _to_c_string_array(query_tokens)
        document_array = _to_c_string_array(document_tokens)
        return int(
            self.library.lastlight_count_matches(
                query_array,
                len(query_tokens),
                document_array,
                len(document_tokens),
            )
        )

    def _load(self, path: Path) -> ctypes.CDLL | None:
        if not path.exists():
            return None
        library = ctypes.CDLL(str(path))
        library.lastlight_count_matches.argtypes = [
            ctypes.POINTER(ctypes.c_char_p),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_char_p),
            ctypes.c_size_t,
        ]
        library.lastlight_count_matches.restype = ctypes.c_int
        return library


def _to_c_string_array(tokens: list[str]) -> ctypes.Array[ctypes.c_char_p]:
    encoded = [token.encode("utf-8") for token in tokens]
    array_type = ctypes.c_char_p * len(encoded)
    return array_type(*encoded)


def _python_count_matches(query_tokens: list[str], document_tokens: list[str]) -> int:
    document_set = set(document_tokens)
    return sum(1 for token in query_tokens if token in document_set)

