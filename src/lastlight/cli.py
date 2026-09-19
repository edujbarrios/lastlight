"""Command-line entrypoint."""

from __future__ import annotations

import argparse
import json

from pathlib import Path

from .commands import (
    BatchQueryCommand,
    BuildIndexCommand,
    BuildModelCommand,
    EvaluationCommand,
    ExportPackCommand,
    FieldGuideCommand,
    ImportPdfCommand,
    InteractiveCommand,
    ListKnowledgeCommand,
    ModelInfoCommand,
    PackInfoCommand,
    QueryCommand,
    ServeCommand,
    SelfCheckCommand,
    ValidatePackCommand,
    VerifyIndexCommand,
)
from .factory import ApplicationFactory
from .knowledge_sources import build_knowledge_repository
from .repository import MarkdownKnowledgeRepository
from .system_commands import DeviceBenchmarkCommand, VerifyProvenanceCommand


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than 0")
    return parsed


def _single_knowledge_source(
    parser: argparse.ArgumentParser,
    sources: list[str] | None,
    operation: str,
) -> str | None:
    if not sources:
        return None
    if len(sources) > 1:
        parser.error(f"{operation} accepts exactly one --knowledge source")
    return sources[0]


def _application_knowledge_arg(sources: list[str] | None) -> str | list[str] | None:
    if not sources:
        return None
    if len(sources) == 1:
        return sources[0]
    return sources


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lastlight",
        description="Offline intelligence under extreme constraints.",
    )
    parser.add_argument("query", nargs="*", help="single query to answer")
    parser.add_argument(
        "--query-file",
        metavar="PATH",
        help="answer newline-delimited queries as JSONL",
    )
    parser.add_argument(
        "--query-output",
        metavar="PATH",
        help="write --query-file JSONL results to this path",
    )
    parser.add_argument(
        "--field-guide",
        metavar="PATH",
        help="write --query-file answers as a human-readable Markdown guide",
    )
    parser.add_argument("--eval", action="store_true", help="run evaluation suite")
    parser.add_argument(
        "--eval-output",
        default=None,
        metavar="PATH",
        help="write evaluation JSON to this path",
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="run the integrated device/safety/energy benchmark and exit",
    )
    parser.add_argument(
        "--benchmark-json",
        action="store_true",
        help="emit --benchmark output as machine-readable JSON",
    )
    parser.add_argument(
        "--benchmark-max-cases",
        type=positive_int,
        default=None,
        metavar="N",
        help="limit benchmark evaluation cases for a quicker smoke run",
    )
    parser.add_argument(
        "--benchmark-energy-source",
        choices=("auto", "rapl", "counter", "estimate"),
        default="auto",
        help="energy source for --benchmark",
    )
    parser.add_argument(
        "--benchmark-energy-counter",
        metavar="PATH",
        help="cumulative hardware energy counter file for --benchmark",
    )
    parser.add_argument(
        "--benchmark-energy-unit",
        choices=("uj", "mj", "j", "uwh", "mwh", "wh"),
        default="mwh",
        help="unit stored by --benchmark-energy-counter",
    )
    parser.add_argument(
        "--benchmark-watts",
        type=positive_float,
        default=15.0,
        metavar="WATTS",
        help="power assumption used only when benchmark energy is estimated",
    )
    parser.add_argument(
        "--strategy",
        choices=("lexical", "bm25", "c-lexical", "adaptive"),
        default="lexical",
        help="retrieval strategy to use",
    )
    parser.add_argument(
        "--mode",
        choices=("survival", "balanced", "accuracy"),
        default="balanced",
        help="resource policy used by --strategy adaptive",
    )
    parser.add_argument(
        "--energy-budget-mwh",
        type=positive_float,
        default=None,
        metavar="MWH",
        help="per-query energy budget for adaptive retrieval",
    )
    parser.add_argument(
        "--memory-budget-mb",
        type=positive_int,
        default=None,
        metavar="MB",
        help="memory budget for adaptive retrieval",
    )
    parser.add_argument(
        "--plan",
        action="store_true",
        help="print the selected retrieval plan as JSON and exit",
    )
    parser.add_argument(
        "--knowledge",
        action="append",
        default=None,
        metavar="PATH",
        help="knowledge directory or .zip pack; repeat to mount multiple packs",
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
        "--verify-index",
        metavar="PATH",
        help="verify knowledge files against an offline audit index and exit",
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
        "--verify-provenance",
        action="store_true",
        help="verify pack publisher, freshness, provenance, and fingerprint",
    )
    parser.add_argument(
        "--provenance-json",
        action="store_true",
        help="emit --verify-provenance output as JSON",
    )
    parser.add_argument(
        "--stale-after-days",
        type=positive_int,
        default=365,
        metavar="DAYS",
        help="age threshold that triggers a provenance freshness warning",
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
        type=positive_int,
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
        type=positive_int,
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
        "--fail-on-refusal",
        action="store_true",
        help="exit with status 2 when a single query has no acceptable answer",
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
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.benchmark:
        source = _single_knowledge_source(parser, args.knowledge, "--benchmark")
        return DeviceBenchmarkCommand(
            source,
            energy_source=args.benchmark_energy_source,
            energy_counter=args.benchmark_energy_counter,
            energy_unit=args.benchmark_energy_unit,
            watts=args.benchmark_watts,
            max_cases=args.benchmark_max_cases,
            as_json=args.benchmark_json,
        ).execute()
    if args.self_check:
        source = _single_knowledge_source(parser, args.knowledge, "--self-check")
        repository = MarkdownKnowledgeRepository(source)
        return SelfCheckCommand(repository).execute()
    if args.pack_info:
        source = _single_knowledge_source(parser, args.knowledge, "--pack-info")
        repository = MarkdownKnowledgeRepository(source)
        return PackInfoCommand(repository).execute()
    if args.list_knowledge:
        repository = build_knowledge_repository(args.knowledge)
        return ListKnowledgeCommand(repository, language=args.language).execute()
    if args.validate_pack:
        source = _single_knowledge_source(parser, args.knowledge, "--validate-pack")
        repository = MarkdownKnowledgeRepository(source)
        return ValidatePackCommand(repository).execute()
    if args.verify_provenance:
        source = _single_knowledge_source(parser, args.knowledge, "--verify-provenance")
        repository = MarkdownKnowledgeRepository(source)
        return VerifyProvenanceCommand(
            repository,
            stale_after_days=args.stale_after_days,
            as_json=args.provenance_json,
        ).execute()
    if args.export_pack:
        source = _single_knowledge_source(parser, args.knowledge, "--export-pack")
        repository = MarkdownKnowledgeRepository(source)
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
        source = _single_knowledge_source(parser, args.knowledge, "--build-model")
        repository = MarkdownKnowledgeRepository(source)
        return BuildModelCommand(
            repository, Path(args.build_model), order=args.model_order
        ).execute()
    if args.build_index:
        source = _single_knowledge_source(parser, args.knowledge, "--build-index")
        repository = MarkdownKnowledgeRepository(source)
        return BuildIndexCommand(repository, Path(args.build_index)).execute()
    if args.verify_index:
        source = _single_knowledge_source(parser, args.knowledge, "--verify-index")
        repository = MarkdownKnowledgeRepository(source)
        return VerifyIndexCommand(repository, Path(args.verify_index)).execute()

    factory_kwargs: dict[str, object] = {
        "knowledge_dir": _application_knowledge_arg(args.knowledge),
        "strategy": args.strategy,
        "language": args.language,
    }
    if args.strategy == "adaptive":
        factory_kwargs.update(
            mode=args.mode,
            energy_budget_mwh=args.energy_budget_mwh,
            memory_budget_mb=args.memory_budget_mb,
        )
    app = ApplicationFactory.create(**factory_kwargs)

    if args.plan:
        if not args.query:
            parser.error("--plan requires a query")
        query = " ".join(args.query)
        app.search(query, top_k=args.top_k)
        metadata = app.retrieval_metadata() or {
            "strategy": args.strategy,
            "mode": "fixed",
            "effective_top_k": args.top_k,
        }
        print(json.dumps(metadata, ensure_ascii=True, indent=2, sort_keys=True))
        return 0

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
    if args.query_file:
        if args.field_guide:
            return FieldGuideCommand(
                app,
                args.query_file,
                args.field_guide,
                top_k=args.top_k,
            ).execute()
        return BatchQueryCommand(
            app,
            args.query_file,
            output_path=args.query_output,
            top_k=args.top_k,
        ).execute()
    if args.query:
        return QueryCommand(
            app,
            " ".join(args.query),
            stream=args.stream,
            synthesize=args.synthesize,
            output_format=args.format,
            top_k=args.top_k,
            fail_on_refusal=args.fail_on_refusal,
        ).execute()
    return InteractiveCommand(app).execute()
