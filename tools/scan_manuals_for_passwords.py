"""Scan manuals under Resurse/ for driver/communication password hints.

This extracts text from PDFs and DOCX files and prints matches with context.

Usage:
  C:/Users/AngelAdrian/Desktop/Acces/ZKAccessB/.venv/Scripts/python.exe tools/scan_manuals_for_passwords.py

Optional:
  --root Resurse
  --query password
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Hit:
    file: Path
    kind: str
    page: int | None
    snippet: str


def _extract_pdf_text(path: Path) -> list[str]:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages: list[str] = []
    for p in reader.pages:
        try:
            pages.append(p.extract_text() or "")
        except Exception:
            pages.append("")
    return pages


def _extract_docx_text(path: Path) -> list[str]:
    from docx import Document

    doc = Document(str(path))
    text = "\n".join(p.text for p in doc.paragraphs if p.text)
    return [text]


def _normalize(s: str) -> str:
    return (s or "").replace("\x00", " ")


def _find_hits_in_text(
    *,
    file: Path,
    kind: str,
    page: int | None,
    text: str,
    patterns: list[re.Pattern[str]],
    context_chars: int = 120,
) -> list[Hit]:
    hits: list[Hit] = []
    t = _normalize(text)
    for pat in patterns:
        for m in pat.finditer(t):
            start = max(0, m.start() - context_chars)
            end = min(len(t), m.end() + context_chars)
            snippet = t[start:end]
            snippet = re.sub(r"\s+", " ", snippet).strip()
            hits.append(Hit(file=file, kind=kind, page=page, snippet=snippet))
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="Resurse")
    ap.add_argument(
        "--query",
        default="password|passwd|communication password|comm password|device password|default password|communication key|comm key|encryption",
    )
    ns = ap.parse_args()

    root = Path(ns.root)
    if not root.exists():
        raise SystemExit(f"Root not found: {root}")

    patterns = [re.compile(ns.query, re.IGNORECASE)]

    files: list[Path] = []
    files.extend(root.rglob("*.pdf"))
    files.extend(root.rglob("*.docx"))

    hits: list[Hit] = []

    for f in sorted(files):
        suffix = f.suffix.lower()
        try:
            if suffix == ".pdf":
                pages = _extract_pdf_text(f)
                for idx, text in enumerate(pages, start=1):
                    hits.extend(
                        _find_hits_in_text(
                            file=f,
                            kind="pdf",
                            page=idx,
                            text=text,
                            patterns=patterns,
                        )
                    )
            elif suffix == ".docx":
                texts = _extract_docx_text(f)
                for text in texts:
                    hits.extend(
                        _find_hits_in_text(
                            file=f,
                            kind="docx",
                            page=None,
                            text=text,
                            patterns=patterns,
                        )
                    )
        except Exception as e:
            print(f"[WARN] Failed to parse {f}: {type(e).__name__}: {e}")

    if not hits:
        print("No matches found.")
        return 0

    # Print grouped by file
    hits_by_file: dict[Path, list[Hit]] = {}
    for h in hits:
        hits_by_file.setdefault(h.file, []).append(h)

    for file, hs in hits_by_file.items():
        rel = file.as_posix()
        print("\n===", rel, f"(hits={len(hs)})")
        for h in hs[:80]:
            loc = f"page {h.page}" if h.page is not None else "(docx)"
            print(f"- {loc}: {h.snippet}")
        if len(hs) > 80:
            print(f"  ... truncated ({len(hs)-80} more)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
