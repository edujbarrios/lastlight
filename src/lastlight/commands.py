"""Command objects for CLI modes."""

from __future__ import annotations

from .app import LastLightApp
from .evaluation import run_evaluation
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
    def __init__(self, app: LastLightApp, query: str) -> None:
        self.app = app
        self.query = query

    def execute(self) -> int:
        print(STARTUP_WARNING)
        print()
        print(self.app.answer(self.query))
        return 0


class EvaluationCommand:
    def __init__(self, app: LastLightApp) -> None:
        self.app = app

    def execute(self) -> int:
        print(run_evaluation(self.app))
        return 0

