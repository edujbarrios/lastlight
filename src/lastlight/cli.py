"""Command-line entrypoint."""

from __future__ import annotations

import argparse

from pathlib import Path

from .commands import (
    BuildIndexCommand,
    BuildModelCommand,
    EvaluationCommand,
    ExportPackCommand,
    ImportPdfCommand,
    InteractiveCommand,
    ListKnowledgeCommand,
    ModelInfoCommand,
    PackInfoCommand,
    QueryCommand,
    ServeCommand,
    SelfCheckCommand,
    ValidatePackCommand,
)
from .factory import ApplicationFactory
from .repository import MarkdownKnowledgeRepository


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lastlight",
        description="Offline intelligence under extreme constraints.",
    )
    parser.add_argument("query", nargs="*", help="single query to answer")
    parser.add_argument("--eval", action="store_true", help="run evaluation suite")
    parser.add_argument(
        "--eval-output",
        default=None,
        metavar="PATH",
        help="write evaluation JSON to this path",
    )
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
        "--language",
        metavar="CODE",
        help="restrict query, interactive, or evaluation mode to a language code",
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
        "--list-knowledge",
        action="store_true",
        help="list available knowledge documents and exit",
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
        "--require-valid-pack",
        action="store_true",
        help="fail --export-pack when pack validation does not pass",
    )
    parser.add_argument(
        "--import-pdf",
        metavar="PATH",
        help="convert a text-based PDF into LastLight Markdown and exit",
    )
    parser.add_argument(
        "--import-output",
        metavar="PATH",
        help="output Markdown path for --import-pdf",
    )
    parser.add_argument("--import-title", help="title override for --import-pdf")
    parser.add_argument(
        "--import-tags",
        default="imported,pdf",
        help="comma-separated tags for --import-pdf",
    )
    parser.add_argument(
        "--import-priority",
        default="normal",
        help="front matter priority for --import-pdf",
    )
    parser.add_argument(
        "--import-summary-items",
        type=int,
        default=8,
        help="maximum important points for --import-pdf",
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
        "--format",
        choices=("text", "json", "sources"),
        default="text",
        help="output format for single-query mode",
    )
    parser.add_argument(
        "--top-k",
        type=positive_int,
        default=3,
        help="number of ranked results to consider for single-query mode",
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
    parser.add_argument(
        "--serve",
        action="store_true",
        help="serve a minimal local dark web interface",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="host for --serve",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="port for --serve",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.self_check:
        repository = MarkdownKnowledgeRepository(args.knowledge)
        return SelfCheckCommand(repository).execute()
    if args.pack_info:
        repository = MarkdownKnowledgeRepository(args.knowledge)
        return PackInfoCommand(repository).execute()
    if args.list_knowledge:
        repository = MarkdownKnowledgeRepository(args.knowledge)
        return ListKnowledgeCommand(repository, language=args.language).execute()
    if args.validate_pack:
        repository = MarkdownKnowledgeRepository(args.knowledge)
        return ValidatePackCommand(repository).execute()
    if args.export_pack:
        repository = MarkdownKnowledgeRepository(args.knowledge)
        return ExportPackCommand(
            repository,
            Path(args.export_pack),
            require_valid=args.require_valid_pack,
        ).execute()
    if args.import_pdf:
        tags = tuple(tag.strip() for tag in args.import_tags.split(",") if tag.strip())
        return ImportPdfCommand(
            args.import_pdf,
            output_path=args.import_output,
            title=args.import_title,
            language=args.language or "unknown",
            tags=tags,
            priority=args.import_priority,
            summary_items=args.import_summary_items,
        ).execute()
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

    app = ApplicationFactory.create(
        knowledge_dir=args.knowledge,
        strategy=args.strategy,
        language=args.language,
    )
    if args.serve:
        return ServeCommand(app, host=args.host, port=args.port).execute()
    if args.eval:
        output_path = Path(args.eval_output) if args.eval_output else None
        command = (
            EvaluationCommand(app, output_path)
            if output_path
            else EvaluationCommand(app)
        )
        return command.execute()
    if args.query:
        return QueryCommand(
            app,
            " ".join(args.query),
            stream=args.stream,
            synthesize=args.synthesize,
            output_format=args.format,
            top_k=args.top_k,
        ).execute()
    return InteractiveCommand(app).execute()
