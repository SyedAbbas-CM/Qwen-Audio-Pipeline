from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "transcripts" / "devlog-final.txt"
DEFAULT_OUTPUT = ROOT / "transcripts" / "devlog-final-manifest.tsv"

MARKER_RE = re.compile(r"^\[(?P<label>Marker\s+(?P<num>\d+)\s*-\s*(?P<title>.+))\]$")
HOOK_RE = re.compile(r"^\((?P<title>Hook\s*-\s*Before\s*Marker\s*\d+)\)$", re.IGNORECASE)
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass
class Section:
    section_id: str
    marker: str
    title: str
    text: str


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "section"


def infer_style(marker: str, title: str, chunk_index: int) -> str:
    title_l = title.lower()
    marker_l = marker.lower()
    if marker == "hook":
        return "performative" if chunk_index == 1 else "grounded"
    if "balancing" in title_l:
        return "sarcastic"
    if "outro" in title_l:
        return "laidback"
    if "boss" in title_l:
        return "grounded"
    if "lighting" in title_l or "dungeon" in title_l:
        return "grounded"
    if "treasure" in title_l or "testing" in title_l:
        return "laidback"
    if marker_l.startswith("marker 4"):
        return "laidback"
    return "grounded"


def chunk_text(
    text: str,
    max_chars: int = 220,
    max_sentences: int = 3,
    whole_section_max_chars: int = 500,
    whole_section_max_sentences: int = 8,
) -> list[str]:
    sentences = [s.strip() for s in SENTENCE_SPLIT_RE.split(text.strip()) if s.strip()]
    if not sentences:
        return []
    if len(text.strip()) <= whole_section_max_chars and len(sentences) <= whole_section_max_sentences:
        return [text.strip()]

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for sentence in sentences:
        extra = len(sentence) + (1 if current else 0)
        if current and (len(current) >= max_sentences or current_len + extra > max_chars):
            chunks.append(" ".join(current).strip())
            current = [sentence]
            current_len = len(sentence)
        else:
            current.append(sentence)
            current_len += extra
    if current:
        chunks.append(" ".join(current).strip())
    return chunks


def parse_sections(text: str) -> list[Section]:
    sections: list[Section] = []
    current_marker = "hook"
    current_title = "Hook"
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_lines, current_marker, current_title
        body = "\n".join(current_lines).strip()
        if body:
            section_id = "hook" if current_marker == "hook" else f"{slugify(current_marker)}-{slugify(current_title)}"
            sections.append(
                Section(
                    section_id=section_id,
                    marker=current_marker,
                    title=current_title,
                    text=body.replace("\n", " ").strip(),
                )
            )
        current_lines = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        marker_line = line.strip("*").strip()
        hook_match = HOOK_RE.match(marker_line)
        if hook_match:
            flush()
            current_marker = "hook"
            current_title = "Hook"
            continue
        marker_match = MARKER_RE.match(marker_line)
        if marker_match:
            flush()
            current_marker = f"Marker {marker_match.group('num')}"
            current_title = marker_match.group("title").strip()
            continue
        if line.startswith("*") and line.endswith("*"):
            continue
        if not line:
            continue
        current_lines.append(line)
    flush()
    return sections


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--max-chars", type=int, default=220)
    parser.add_argument("--max-sentences", type=int, default=3)
    parser.add_argument("--whole-section-max-chars", type=int, default=500)
    parser.add_argument("--whole-section-max-sentences", type=int, default=8)
    args = parser.parse_args()

    source = Path(args.input).read_text(encoding="utf-8")
    sections = parse_sections(source)

    rows: list[dict[str, str]] = []
    for section in sections:
        chunks = chunk_text(
            section.text,
            max_chars=args.max_chars,
            max_sentences=args.max_sentences,
            whole_section_max_chars=args.whole_section_max_chars,
            whole_section_max_sentences=args.whole_section_max_sentences,
        )
        for idx, chunk in enumerate(chunks, start=1):
            row_id = f"{section.section_id}-c{idx:02d}"
            rows.append(
                {
                    "id": row_id,
                    "marker": section.marker,
                    "title": section.title,
                    "chunk_index": str(idx),
                    "style": infer_style(section.marker, section.title, idx),
                    "text": chunk,
                }
            )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["id", "marker", "title", "chunk_index", "style", "text"],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
