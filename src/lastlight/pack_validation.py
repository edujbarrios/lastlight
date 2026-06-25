"""Knowledge pack validation for community publishing."""

from __future__ import annotations

from dataclasses import dataclass, field

from .interfaces import KnowledgeRepository

REQUIRED_MANIFEST_FIELDS = ("name", "version", "languages", "license", "source")


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
        warnings.append("repository does not expose pack metadata")
        return PackValidationReport(tuple(errors), tuple(warnings))

    pack = describe_pack()
    if not pack.metadata:
        errors.append("missing lastlight-pack.json manifest")
    else:
        for field_name in REQUIRED_MANIFEST_FIELDS:
            value = pack.metadata.get(field_name)
            if value in (None, "", []):
                errors.append(f"manifest missing required field: {field_name}")

    document_languages = sorted(
        {document.language for document in documents if document.language != "unknown"}
    )
    if document_languages and not pack.languages:
        errors.append("manifest languages do not describe document languages")

    missing_languages = [
        language for language in document_languages if language not in pack.languages
    ]
    for language in missing_languages:
        errors.append(f"manifest languages missing document language: {language}")

    unknown_language_count = sum(
        1 for document in documents if document.language == "unknown"
    )
    if unknown_language_count:
        warnings.append(
            f"{unknown_language_count} document(s) do not declare a language"
        )

    untagged_count = sum(1 for document in documents if not document.tags)
    if untagged_count:
        warnings.append(f"{untagged_count} document(s) do not declare tags")

    return PackValidationReport(tuple(errors), tuple(warnings))


def format_validation_report(report: PackValidationReport) -> str:
    lines = ["Pack validation: PASS" if report.ok else "Pack validation: FAIL"]
    for error in report.errors:
        lines.append(f"ERROR: {error}")
    for warning in report.warnings:
        lines.append(f"WARNING: {warning}")
    return "\n".join(lines)
