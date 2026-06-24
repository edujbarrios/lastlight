"""Command objects for CLI modes."""

from __future__ import annotations

from pathlib import Path

from .app import LastLightApp
from .compat import format_self_check, run_self_check
from .evaluation import run_evaluation
from .indexer import write_index
from .interfaces import KnowledgeRepository
from .local_model import summarize_local_model, write_local_model
from .safety import STARTUP_WARNING


class InteractiveCommand:
    def __init__(self, app: LastLightApp) -> None:
        self.app = app

    def execute(self) -> int:
        print(STARTUP_WARNING)
        print("Type a question, or 'exit' to quit.")
        while True:
            try:
                query = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return 0
            if query.casefold() in {"exit", "quit", ":q"}:
                return 0
            if not query:
                continue
            print(self.app.answer(query))
        return 0


class QueryCommand:
    def __init__(
        self,
        app: LastLightApp,
        query: str,
        stream: bool = False,
        synthesize: bool = False,
    ) -> None:
        self.app = app
        self.query = query
        self.stream = stream
        self.synthesize = synthesize

    def execute(self) -> int:
        print(STARTUP_WARNING)
        print()
        answer = self.app.synthesize(self.query) if self.synthesize else self.app.answer(self.query)
        if self.stream:
            for line in answer.splitlines():
                print(line, flush=True)
        else:
            print(answer)
        return 0


class EvaluationCommand:
    def __init__(self, app: LastLightApp) -> None:
        self.app = app

    def execute(self) -> int:
        print(run_evaluation(self.app))
        return 0


class BuildIndexCommand:
    def __init__(self, repository: KnowledgeRepository, output_path: Path | str) -> None:
        self.repository = repository
        self.output_path = output_path

    def execute(self) -> int:
        output = write_index(self.repository, self.output_path)
        print(f"Wrote offline index: {output}")
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
