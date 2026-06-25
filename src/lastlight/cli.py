"""Command-line entrypoint."""

from __future__ import annotations

import argparse

from pathlib import Path

from .commands import (
    BuildIndexCommand,
    BuildModelCommand,
    EvaluationCommand,
    ExportPackCommand,
    InteractiveCommand,
    ModelInfoCommand,
    PackInfoCommand,
    QueryCommand,
    SelfCheckCommand,
    ValidatePackCommand,
)
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
        choices=("lexical", "bm25", "c-lexical"),
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
        "--pack-info",
        action="store_true",
        help="print knowledge pack metadata and exit",
    )
    parser.add_argument(
        "--validate-pack",
        action="store_true",
        help="validate a knowledge pack for community publishing and exit",
    )
    parser.add_argument(
        "--export-pack",
        metavar="PATH",
        help="write a deterministic .zip knowledge pack and exit",
    )
    parser.add_argument(
        "--build-model",
        metavar="PATH",
        help="write an experimental local n-gram model JSON and exit",
    )
    parser.add_argument(
        "--model-order",
        type=int,
        default=2,
        help="n-gram order for --build-model",
    )
    parser.add_argument(
        "--model-info",
        metavar="PATH",
        help="inspect a local n-gram model JSON and exit",
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="print query output line by line with flushing",
    )
    parser.add_argument(
        "--synthesize",
        action="store_true",
        help="experimental citation-aware n-gram synthesis from retrieved passage",
    )
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="check offline compatibility for constrained devices",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    app = ApplicationFactory.create(knowledge_dir=args.knowledge, strategy=args.strategy)

    if args.self_check:
        repository = MarkdownKnowledgeRepository(args.knowledge)
        return SelfCheckCommand(repository).execute()
    if args.pack_info:
        repository = MarkdownKnowledgeRepository(args.knowledge)
        return PackInfoCommand(repository).execute()
    if args.validate_pack:
        repository = MarkdownKnowledgeRepository(args.knowledge)
        return ValidatePackCommand(repository).execute()
    if args.export_pack:
        repository = MarkdownKnowledgeRepository(args.knowledge)
        return ExportPackCommand(repository.knowledge_dir, Path(args.export_pack)).execute()
    if args.model_info:
        return ModelInfoCommand(Path(args.model_info)).execute()
    if args.build_model:
        repository = MarkdownKnowledgeRepository(args.knowledge)
        return BuildModelCommand(
            repository, Path(args.build_model), order=args.model_order
        ).execute()
    if args.build_index:
        repository = MarkdownKnowledgeRepository(args.knowledge)
        return BuildIndexCommand(repository, Path(args.build_index)).execute()
    if args.eval:
        return EvaluationCommand(app).execute()
    if args.query:
        return QueryCommand(
            app,
            " ".join(args.query),
            stream=args.stream,
            synthesize=args.synthesize,
        ).execute()
    return InteractiveCommand(app).execute()
