"""Command objects for CLI modes."""

from __future__ import annotations

import json
from pathlib import Path

from .app import LastLightApp
from .compat import format_self_check, run_self_check
from .evaluation import (
    DEFAULT_EVAL_OUTPUT,
    build_evaluation_report,
    format_evaluation_report,
    write_evaluation_report,
)
from .indexer import write_index
from .interfaces import KnowledgeRepository
from .local_model import summarize_local_model, write_local_model
from .pack_export import export_pack, sha256_file
from .pack_validation import format_validation_report, validate_pack
from .pdf_ingest import document_to_markdown, load_pdf
from .safety import (
    LOW_CONFIDENCE_RESPONSE,
    STARTUP_WARNING,
    result_to_dict,
    safe_answer,
)
from .session import LastLightSession
from .synthesis import synthesize_answer
from .triage import first_acceptable_result
from .web import serve


class InteractiveCommand:
    def __init__(self, app: LastLightApp) -> None:
        self.app = app

    def execute(self) -> int:
        session = LastLightSession(self.app)
        print(STARTUP_WARNING)
        print("Type a question, 'clear' to reset context, or 'exit' to quit.")
        while True:
            try:
                query = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return 0
            if query.casefold() in {"exit", "quit", ":q"}:
                return 0
            if query.casefold() in {"clear", ":clear"}:
                session.clear()
                print("Context cleared.")
                continue
            if not query:
                continue
            print(session.answer(query))
        return 0


class QueryCommand:
    def __init__(
        self,
        app: LastLightApp,
        query: str,
        stream: bool = False,
        synthesize: bool = False,
        output_format: str = "text",
        top_k: int = 3,
    ) -> None:
        self.app = app
        self.query = query
        self.stream = stream
        self.synthesize = synthesize
        self.output_format = output_format
        self.top_k = max(top_k, 1)

    def execute(self) -> int:
        if self.output_format == "json":
            print(self._json_output())
            return 0

        print(STARTUP_WARNING)
        print()
        answer = (
            self.app.synthesize(self.query, top_k=self.top_k)
            if self.synthesize
            else self.app.answer(self.query, top_k=self.top_k)
        )
        if self.stream:
            for line in answer.splitlines():
                print(line, flush=True)
        else:
            print(answer)
        return 0

    def _json_output(self) -> str:
        results = self.app.search(self.query, top_k=self.top_k)
        accepted = first_acceptable_result(results)
        payload: dict[str, object] = {
            "query": self.query,
            "accepted": accepted is not None,
            "answer": (
                synthesize_answer(self.query, results)
                if self.synthesize
                else safe_answer(results)
            ),
            "results": [result_to_dict(result) for result in results],
        }
        if accepted is None:
            payload["message"] = LOW_CONFIDENCE_RESPONSE
        return json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True)


class EvaluationCommand:
    def __init__(
        self, app: LastLightApp, output_path: Path | str = DEFAULT_EVAL_OUTPUT
    ) -> None:
        self.app = app
        self.output_path = output_path

    def execute(self) -> int:
        report = build_evaluation_report(self.app)
        print(format_evaluation_report(report))
        output = write_evaluation_report(report, self.output_path)
        print(f"Wrote evaluation report: {output}")
        return 0


class ServeCommand:
    def __init__(self, app: LastLightApp, host: str, port: int) -> None:
        self.app = app
        self.host = host
        self.port = port

    def execute(self) -> int:
        print(STARTUP_WARNING)
        serve(self.app, host=self.host, port=self.port)
        return 0


class BuildIndexCommand:
    def __init__(self, repository: KnowledgeRepository, output_path: Path | str) -> None:
        self.repository = repository
        self.output_path = output_path

    def execute(self) -> int:
        output = write_index(self.repository, self.output_path)
        print(f"Wrote offline index: {output}")
        return 0


class PackInfoCommand:
    def __init__(self, repository: KnowledgeRepository) -> None:
        self.repository = repository

    def execute(self) -> int:
        describe_pack = getattr(self.repository, "describe_pack", None)
        documents = self.repository.list_documents()
        if not callable(describe_pack):
            print(f"Documents: {len(documents)}")
            return 0

        pack = describe_pack()
        languages = ", ".join(pack.languages) if pack.languages else "unknown"
        print(f"Name: {pack.name}")
        print(f"Version: {pack.version}")
        print(f"Languages: {languages}")
        print(f"Documents: {len(documents)}")
        print(f"License: {pack.license}")
        print(f"Source: {pack.source}")
        if pack.description:
            print(f"Description: {pack.description}")
        print(f"Path: {pack.path}")
        return 0


class ListKnowledgeCommand:
    def __init__(self, repository: KnowledgeRepository, language: str | None = None) -> None:
        self.repository = repository
        self.language = language.casefold() if language else None

    def execute(self) -> int:
        documents = self.repository.list_documents()
        if self.language:
            documents = [
                document
                for document in documents
                if document.language.casefold() == self.language
            ]

        if not documents:
            print("No knowledge documents found.")
            return 0

        for document in sorted(
            documents,
            key=lambda item: (item.language, item.title.casefold(), item.path),
        ):
            tags = ", ".join(document.tags) if document.tags else "none"
            print(
                f"{document.language} | {document.priority} | "
                f"{document.title} | {tags} | {document.path}"
            )
        return 0


class ValidatePackCommand:
    def __init__(self, repository: KnowledgeRepository) -> None:
        self.repository = repository

    def execute(self) -> int:
        report = validate_pack(self.repository)
        print(format_validation_report(report))
        return 0 if report.ok else 1


class ExportPackCommand:
    def __init__(self, source_dir: Path | str, output_path: Path | str) -> None:
        self.source_dir = source_dir
        self.output_path = output_path

    def execute(self) -> int:
        try:
            output = export_pack(self.source_dir, self.output_path)
        except ValueError as error:
            print(f"Export failed: {error}")
            return 1
        print(f"Wrote knowledge pack: {output}")
        print(f"SHA-256: {sha256_file(output)}")
        return 0


class ImportPdfCommand:
    def __init__(
        self,
        pdf_path: Path | str,
        output_path: Path | str | None = None,
        title: str | None = None,
        language: str = "unknown",
        tags: tuple[str, ...] = ("imported", "pdf"),
        priority: str = "normal",
        summary_items: int = 8,
    ) -> None:
        self.pdf_path = Path(pdf_path)
        self.output_path = Path(output_path) if output_path else self.pdf_path.with_suffix(".md")
        self.title = title
        self.language = language
        self.tags = tags
        self.priority = priority
        self.summary_items = summary_items

    def execute(self) -> int:
        try:
            document = load_pdf(self.pdf_path)
            markdown = document_to_markdown(
                document,
                title=self.title,
                language=self.language,
                tags=self.tags,
                priority=self.priority,
                max_summary_items=self.summary_items,
            )
        except Exception as error:
            print(f"PDF import failed: {error}")
            return 1

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(markdown, encoding="utf-8")
        print(f"Wrote Markdown: {self.output_path}")
        return 0


class SelfCheckCommand:
    def __init__(self, repository: KnowledgeRepository) -> None:
        self.repository = repository

    def execute(self) -> int:
        results = run_self_check(self.repository)
        print(format_self_check(results))
        return 0 if all(result.ok for result in results) else 1


class BuildModelCommand:
    def __init__(
        self,
        repository: KnowledgeRepository,
        output_path: Path | str,
        order: int = 2,
    ) -> None:
        self.repository = repository
        self.output_path = output_path
        self.order = order

    def execute(self) -> int:
        output = write_local_model(self.repository, self.output_path, order=self.order)
        print(f"Wrote local n-gram model: {output}")
        return 0


class ModelInfoCommand:
    def __init__(self, model_path: Path | str) -> None:
        self.model_path = model_path

    def execute(self) -> int:
        print(summarize_local_model(self.model_path))
        return 0
