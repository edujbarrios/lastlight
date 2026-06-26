# PDF Ingest

`tools/pdf_to_markdown.py` converts a text-based PDF into LastLight-compatible
Markdown. It extracts page text, creates a small deterministic `Important Points`
section, and records source metadata such as filename, page count, and SHA-256.

```bash
python src/main.py --import-pdf field-guide.pdf \
  --import-output knowledge/en/imported/field-guide.md \
  --language en \
  --import-tags imported,pdf,water \
  --import-priority normal
```

The standalone `tools/pdf_to_markdown.py` script exposes the same converter for
people who prefer a dedicated import tool. PDF import is optional. It uses
installed PDF libraries such as `pypdf`, `PyPDF2`, or `PyMuPDF` when available.
Image-only scanned PDFs need OCR first.

After importing:

```bash
python src/main.py --validate-pack
python src/main.py --list-knowledge
python src/main.py "your question"
```
