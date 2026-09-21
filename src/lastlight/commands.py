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
from .indexer import verify_index, write_index
from .interfaces import KnowledgeRepository
from .pack_validation import format_validation_report, validate_pack
from .safety import (
    LOW_CONFIDENCE_RESPONSE,
    STARTUP_WARNING,
    result_to_dict,
    safe_answer,
)
from .session import LastLightSession
from .triage import first_acceptable_result


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
        output_format: str = "text",
        top_k: int = 3,
        fail_on_refusal: bool = False,
    ) -> None:
        self.app = app
        self.query = query
        self.stream = stream
        self.output_format = output_format
        self.top_k = max(top_k, 1)
        self.fail_on_refusal = fail_on_refusal

    def execute(self) -> int:
        if self.output_format == "json":
            output, accepted = self._json_output()
            print(output)
            return 0 if accepted or not self.fail_on_refusal else 2
        if self.output_format == "sources":
            output, accepted = self._sources_output()
            print(output)
            return 0 if accepted or not self.fail_on_refusal else 2

        print(STARTUP_WARNING)
        print()
        answer = self.app.answer(self.query, top_k=self.top_k)
        if self.stream:
            for line in answer.splitlines():
                print(line, flush=True)
        else:
            print(answer)
        if self.fail_on_refusal:
            accepted = first_acceptable_result(
                self.app.search(self.query, top_k=self.top_k)
            )
            return 0 if accepted else 2
        return 0

    def _json_output(self) -> tuple[str, bool]:
        results = self.app.search(self.query, top_k=self.top_k)
        accepted = first_acceptable_result(results)
        payload: dict[str, object] = {
            "query": self.query,
            "accepted": accepted is not None,
            "answer": safe_answer(results),
            "results": [result_to_dict(result) for result in results],
        }
        if accepted is None:
            payload["message"] = LOW_CONFIDENCE_RESPONSE
        return (
            json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True),
            accepted is not None,
        )

    def _sources_output(self) -> tuple[str, bool]:
        results = self.app.search(self.query, top_k=self.top_k)
        accepted = first_acceptable_result(results)
        if not results:
            return LOW_CONFIDENCE_RESPONSE, False

        lines = [f"Sources for: {self.query}"]
        for index, result in enumerate(results, start=1):
            document = result.document
            tags = ", ".join(document.tags) if document.tags else "none"
            lines.append(
                f"{index}. [{result.confidence}] {document.title} | "
                f"{document.path} | score={result.score:.3f} | tags={tags}"
            )
        return "\n".join(lines), accepted is not None


class BatchQueryCommand:
    """Answer a newline-delimited query file without requiring network access."""

    def __init__(
        self,
        app: LastLightApp,
        input_path: Path | str,
        output_path: Path | str | None = None,
        top_k: int = 3,
    ) -> None:
        self.app = app
        self.input_path = Path(input_path)
        self.output_path = Path(output_path) if output_path else None
        self.top_k = max(top_k, 1)

    def execute(self) -> int:
        try:
            queries = [
                line.strip()
                for line in self.input_path.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            ]
        except OSError as error:
            print(f"Batch query failed: {error}")
            return 1

        records = [self._record(query) for query in queries]
        rendered = "\n".join(
            json.dumps(record, ensure_ascii=False, sort_keys=True)
            for record in records
        )
        if rendered:
            rendered += "\n"

        if self.output_path:
            try:
                self.output_path.parent.mkdir(parents=True, exist_ok=True)
                self.output_path.write_text(rendered, encoding="utf-8")
            except OSError as error:
                print(f"Batch query failed: {error}")
                return 1
            print(f"Wrote {len(records)} answers: {self.output_path}")
        else:
            print(rendered, end="")
        return 0

    def _record(self, query: str) -> dict[str, object]:
        results = self.app.search(query, top_k=self.top_k)
        accepted = first_acceptable_result(results)
        return {
            "query": query,
            "accepted": accepted is not None,
            "answer": safe_answer(results),
            "results": [result_to_dict(result) for result in results],
        }


class FieldGuideCommand:
    """Build a deterministic, human-readable guide from planned questions."""

    def __init__(
        self,
        app: LastLightApp,
        input_path: Path | str,
        output_path: Path | str,
        top_k: int = 3,
    ) -> None:
        self.app = app
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        self.top_k = max(top_k, 1)

    def execute(self) -> int:
        try:
            queries = [
                line.strip()
                for line in self.input_path.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            ]
        except OSError as error:
            print(f"Field guide failed: {error}")
            return 1

        sections = ["# LastLight Offline Field Guide", ""]
        accepted_count = 0
        for query in queries:
            results = self.app.search(query, top_k=self.top_k)
            accepted = first_acceptable_result(results)
            accepted_count += accepted is not None
            sections.extend([f"## {query}", "", safe_answer(results), ""])

        try:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            self.output_path.write_text("\n".join(sections), encoding="utf-8")
        except OSError as error:
            print(f"Field guide failed: {error}")
            return 1

        print(
            f"Wrote field guide: {self.output_path} "
            f"({accepted_count}/{len(queries)} questions answered)"
        )
        return 0 if accepted_count == len(queries) else 2


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


class BuildIndexCommand:
    def __init__(self, repository: KnowledgeRepository, output_path: Path | str) -> None:
        self.repository = repository
        self.output_path = output_path

    def execute(self) -> int:
        output = write_index(self.repository, self.output_path)
        print(f"Wrote offline index: {output}")
        return 0


class VerifyIndexCommand:
    def __init__(self, repository: KnowledgeRepository, index_path: Path | str) -> None:
        self.repository = repository
        self.index_path = index_path

    def execute(self) -> int:
        report = verify_index(self.repository, self.index_path)
        if report.get("error"):
            print(f"Index verification failed: {report['error']}")
            return 1
        if report["ok"]:
            print("Index verified: all knowledge sources match.")
            return 0
        for label in ("missing", "modified", "unexpected"):
            for path in report[label]:
                print(f"{label.capitalize()}: {path}")
        return 1


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


class SelfCheckCommand:
    def __init__(self, repository: KnowledgeRepository) -> None:
        self.repository = repository

    def execute(self) -> int:
        results = run_self_check(self.repository)
        print(format_self_check(results))
        return 0 if all(result.ok for result in results) else 1
