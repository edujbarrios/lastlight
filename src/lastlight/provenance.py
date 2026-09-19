"""Knowledge-pack provenance and freshness verification."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date, datetime, timezone

from .interfaces import KnowledgeRepository

PROVENANCE_FIELDS = ("publisher", "published_at", "source")


@dataclass(frozen=True)
class PackProvenanceReport:
    pack_name: str
    version: str
    fingerprint_sha256: str
    publisher: str = "unknown"
    published_at: str | None = None
    expires_at: str | None = None
    age_days: int | None = None
    expired: bool = False
    errors: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, object]:
        return {
            "pack": self.pack_name,
            "version": self.version,
            "publisher": self.publisher,
            "published_at": self.published_at,
            "expires_at": self.expires_at,
            "age_days": self.age_days,
            "expired": self.expired,
            "fingerprint_sha256": self.fingerprint_sha256,
            "ok": self.ok,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


def verify_pack_provenance(
    repository: KnowledgeRepository,
    *,
    today: date | None = None,
    stale_after_days: int = 365,
) -> PackProvenanceReport:
    if stale_after_days < 1:
        raise ValueError("stale_after_days must be at least 1")

    today = today or datetime.now(timezone.utc).date()
    documents = repository.list_documents()
    describe_pack = getattr(repository, "describe_pack", None)
    pack = describe_pack() if callable(describe_pack) else None
    metadata = dict(getattr(pack, "metadata", {}) or {})

    errors: list[str] = []
    warnings: list[str] = []
    for field_name in PROVENANCE_FIELDS:
        if metadata.get(field_name) in (None, "", []):
            warnings.append(f"manifest missing provenance field: {field_name}")

    publisher = str(metadata.get("publisher") or "unknown")
    published_text = _optional_text(metadata.get("published_at"))
    expires_text = _optional_text(metadata.get("expires_at"))
    published = _parse_date(published_text, "published_at", errors)
    expires = _parse_date(expires_text, "expires_at", errors)

    age_days: int | None = None
    if published is not None:
        age_days = (today - published).days
        if age_days < 0:
            errors.append("published_at is in the future")
        elif age_days > stale_after_days:
            warnings.append(
                f"pack is {age_days} days old; freshness threshold is {stale_after_days} days"
            )

    expired = bool(expires is not None and expires < today)
    if expired:
        errors.append(f"pack expired on {expires.isoformat()}")
    if published is not None and expires is not None and expires < published:
        errors.append("expires_at is earlier than published_at")

    provenance = metadata.get("provenance")
    if provenance is None:
        warnings.append("manifest does not include a provenance chain")
    elif not isinstance(provenance, list):
        errors.append("manifest provenance must be a list")
    else:
        for index, item in enumerate(provenance):
            if not isinstance(item, dict):
                errors.append(f"provenance entry {index} must be an object")
                continue
            if not item.get("source"):
                errors.append(f"provenance entry {index} missing source")

    fingerprint = pack_fingerprint(documents, metadata)
    expected_fingerprint = _optional_text(metadata.get("fingerprint_sha256"))
    if expected_fingerprint and expected_fingerprint.casefold() != fingerprint.casefold():
        errors.append("manifest fingerprint_sha256 does not match pack contents")

    return PackProvenanceReport(
        pack_name=str(getattr(pack, "name", "knowledge")),
        version=str(getattr(pack, "version", "unknown")),
        fingerprint_sha256=fingerprint,
        publisher=publisher,
        published_at=published_text,
        expires_at=expires_text,
        age_days=age_days,
        expired=expired,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def pack_fingerprint(documents: list[object], metadata: dict[str, object]) -> str:
    manifest = {key: value for key, value in metadata.items() if key != "fingerprint_sha256"}
    entries = [
        {
            "path": str(getattr(document, "path", "")),
            "sha256": str(getattr(document, "source_sha256", "")),
        }
        for document in documents
    ]
    entries.sort(key=lambda item: (item["path"], item["sha256"]))
    payload = json.dumps(
        {"manifest": manifest, "documents": entries},
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def format_provenance_report(report: PackProvenanceReport) -> str:
    lines = [
        "Pack provenance: PASS" if report.ok else "Pack provenance: FAIL",
        f"Pack: {report.pack_name} {report.version}",
        f"Publisher: {report.publisher}",
        f"Fingerprint: {report.fingerprint_sha256}",
    ]
    if report.published_at:
        age = f" ({report.age_days} days old)" if report.age_days is not None else ""
        lines.append(f"Published: {report.published_at}{age}")
    if report.expires_at:
        lines.append(f"Expires: {report.expires_at}")
    for error in report.errors:
        lines.append(f"ERROR: {error}")
    for warning in report.warnings:
        lines.append(f"WARNING: {warning}")
    return "\n".join(lines)


def _optional_text(value: object) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _parse_date(value: str | None, field_name: str, errors: list[str]) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        errors.append(f"{field_name} must use ISO date format YYYY-MM-DD")
        return None
