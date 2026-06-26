"""Convert a PDF into LastLight-compatible Markdown."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lastlight.pdf_ingest import document_to_markdown, load_pdf  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract PDF text into Markdown with deterministic key points.",
    )
    parser.add_argument("pdf", help="input PDF path")
    parser.add_argument(
        "--output",
        "-o",
        help="output Markdown path; defaults to the PDF name with .md",
    )
    parser.add_argument("--title", help="override inferred Markdown title")
    parser.add_argument("--language", default="unknown", help="document language code")
    parser.add_argument(
        "--tags",
        default="imported,pdf",
        help="comma-separated tags for front matter",
    )
    parser.add_argument("--priority", default="normal", help="front matter priority")
    parser.add_argument(
        "--summary-items",
        type=int,
        default=8,
        help="maximum number of important points",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    pdf_path = Path(args.pdf)
    output = Path(args.output) if args.output else pdf_path.with_suffix(".md")
    tags = tuple(tag.strip() for tag in args.tags.split(",") if tag.strip())

    document = load_pdf(pdf_path)
    markdown = document_to_markdown(
        document,
        title=args.title,
        language=args.language,
        tags=tags,
        priority=args.priority,
        max_summary_items=args.summary_items,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8")
    print(f"Wrote Markdown: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
