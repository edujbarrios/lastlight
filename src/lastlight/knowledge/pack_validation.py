"""Knowledge pack validation for community publishing."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .interfaces import KnowledgeRepository

PACK_FORMAT_VERSION = 1
REQUIRED_MANIFEST_FIELDS = (
    "format_version",
    "name",
    "version",
    "languages",
    "license",
    "source",
)
_VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$")
_LANGUAGE_RE = re.compile(r"^[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$")
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


@dataclass(frozen=True)
class PackValidationReport:
    errors: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_pack(repository: KnowledgeRepository) -> PackValidationReport:
    describe_pack = getattr(repository, "describe_pack", None)
    documents = repository.list_documents()
    errors: list[str] = []
    warnings: list[str] = []

    if not documents:
        errors.append("pack contains no Markdown documents")

    if not callable(describe_pack):
        errors.append("repository does not expose pack metadata")
        return PackValidationReport(tuple(errors), tuple(warnings))

    pack = describe_pack()
    metadata = dict(pack.metadata or {})
    if not metadata:
        errors.append("missing lastlight-pack.json manifest")
    else:
        _validate_manifest(metadata, errors, warnings)

    document_languages = sorted(
        {document.language for document in documents if document.language != "unknown"}
    )
    manifest_languages = tuple(str(value) for value in metadata.get("languages", ()) if isinstance(value, str)) if isinstance(metadata.get("languages"), list) else ()
    for language in document_languages:
        if language not in manifest_languages:
            errors.append(f"manifest languages missing document language: {language}")

    unknown_language_count = sum(1 for document in documents if document.language == "unknown")
    if unknown_language_count:
        warnings.append(f"{unknown_language_count} document(s) do not declare a language")

    misplaced_language_count = sum(
        1
        for document in documents
        if document.language != "unknown"
        and not _path_contains_language_section(document.path, document.language)
    )
    if misplaced_language_count:
        warnings.append(f"{misplaced_language_count} document(s) are outside their language section")

    untagged_count = sum(1 for document in documents if not document.tags)
    if untagged_count:
        warnings.append(f"{untagged_count} document(s) do not declare tags")

    return PackValidationReport(tuple(errors), tuple(warnings))


def _validate_manifest(metadata: dict[str, object], errors: list[str], warnings: list[str]) -> None:
    for field_name in REQUIRED_MANIFEST_FIELDS:
        value = metadata.get(field_name)
        if value in (None, "", []):
            errors.append(f"manifest missing required field: {field_name}")

    format_version = metadata.get("format_version")
    if isinstance(format_version, bool) or not isinstance(format_version, int):
        errors.append("manifest format_version must be an integer")
    elif format_version != PACK_FORMAT_VERSION:
        errors.append(
            f"unsupported pack format_version: {format_version}; runtime supports {PACK_FORMAT_VERSION}"
        )

    for field_name in ("name", "version", "license", "source"):
        value = metadata.get(field_name)
        if value is not None and not isinstance(value, str):
            errors.append(f"manifest {field_name} must be a string")

    version = metadata.get("version")
    if isinstance(version, str) and version and not _VERSION_RE.fullmatch(version):
        errors.append("manifest version must use semantic version form MAJOR.MINOR.PATCH")

    languages = metadata.get("languages")
    if languages is not None:
        if not isinstance(languages, list) or not languages:
            errors.append("manifest languages must be a non-empty list")
        else:
            seen: set[str] = set()
            for language in languages:
                if not isinstance(language, str) or not _LANGUAGE_RE.fullmatch(language):
                    errors.append(f"manifest language code is invalid: {language!r}")
                    continue
                normalized = language.casefold()
                if normalized in seen:
                    errors.append(f"manifest language code is duplicated: {language}")
                seen.add(normalized)

    fingerprint = metadata.get("fingerprint_sha256")
    if fingerprint is not None and (
        not isinstance(fingerprint, str) or not _SHA256_RE.fullmatch(fingerprint)
    ):
        errors.append("manifest fingerprint_sha256 must be 64 hexadecimal characters")

    provenance = metadata.get("provenance")
    if provenance is not None:
        if not isinstance(provenance, list):
            errors.append("manifest provenance must be a list")
        else:
            for index, item in enumerate(provenance):
                if not isinstance(item, dict):
                    errors.append(f"manifest provenance entry {index} must be an object")
                elif not isinstance(item.get("source"), str) or not item.get("source"):
                    errors.append(f"manifest provenance entry {index} missing source")

    publisher = metadata.get("publisher")
    if publisher is not None and not isinstance(publisher, str):
        errors.append("manifest publisher must be a string")
    if publisher in (None, ""):
        warnings.append("manifest does not declare a publisher")


def _path_contains_language_section(path: str, language: str) -> bool:
    normalized = path.replace("\\", "/")
    section = f"/{language.casefold()}/"
    return normalized.casefold().startswith(f"{language.casefold()}/") or section in normalized.casefold()


def format_validation_report(report: PackValidationReport) -> str:
    lines = ["Pack validation: PASS" if report.ok else "Pack validation: FAIL"]
    for error in report.errors:
        lines.append(f"ERROR: {error}")
    for warning in report.warnings:
        lines.append(f"WARNING: {warning}")
    return "\n".join(lines)
