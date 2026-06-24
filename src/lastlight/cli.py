"""Command-line entrypoint."""

from __future__ import annotations

import argparse

from pathlib import Path

from .commands import BuildIndexCommand, EvaluationCommand, InteractiveCommand, QueryCommand
from .factory import ApplicationFactory
from .repository import MarkdownKnowledgeRepository


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lastlight",
        description="Offline intelligence under extreme constraints.",
    )
    parser.add_argument("query", nargs="*", help="single query to answer")
    parser.add_argument("--eval", action="store_true", help="run evaluation suite")
    parser.add_argument(
        "--strategy",
        choices=("lexical", "bm25"),
        default="lexical",
        help="retrieval strategy to use",
    )
    parser.add_argument(
        "--knowledge",
        default=None,
        help="knowledge directory or .zip knowledge pack",
    )
    parser.add_argument(
        "--build-index",
        metavar="PATH",
        help="write an optional offline JSON index and exit",
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="print query output line by line with flushing",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    app = ApplicationFactory.create(knowledge_dir=args.knowledge, strategy=args.strategy)

    if args.build_index:
        repository = MarkdownKnowledgeRepository(args.knowledge)
        return BuildIndexCommand(repository, Path(args.build_index)).execute()
    if args.eval:
        return EvaluationCommand(app).execute()
    if args.query:
        return QueryCommand(app, " ".join(args.query), stream=args.stream).execute()
    return InteractiveCommand(app).execute()
