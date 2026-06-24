"""Command-line entrypoint."""

from __future__ import annotations

import argparse

from .commands import EvaluationCommand, InteractiveCommand, QueryCommand
from .factory import ApplicationFactory


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lastlight",
        description="Offline intelligence under extreme constraints.",
    )
    parser.add_argument("query", nargs="*", help="single query to answer")
    parser.add_argument("--eval", action="store_true", help="run evaluation suite")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    app = ApplicationFactory.create()

    if args.eval:
        return EvaluationCommand(app).execute()
    if args.query:
        return QueryCommand(app, " ".join(args.query)).execute()
    return InteractiveCommand(app).execute()

