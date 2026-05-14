from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "transcripts" / "devlog-final-manifest-reftext.tsv"
DEFAULT_GLOSSARY = ROOT / "config" / "pronunciation-glossary.tsv"
DEFAULT_OUTPUT = ROOT / "transcripts" / "devlog-final-manifest-spoken.tsv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--glossary", default=str(DEFAULT_GLOSSARY))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    return parser.parse_args()


def load_glossary(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    rows = [row for row in rows if row.get("term", "").strip() and row.get("replacement_text", "").strip()]
    rows.sort(key=lambda row: len(row["term"].strip()), reverse=True)
    return rows


def replace_term(text: str, term: str, replacement: str) -> str:
    pattern = re.compile(rf"(?<![\w]){re.escape(term)}(?![\w])", flags=re.IGNORECASE)
    return pattern.sub(replacement, text)


def apply_glossary(text: str, glossary: list[dict[str, str]]) -> str:
    out = text
    for row in glossary:
        out = replace_term(out, row["term"].strip(), row["replacement_text"].strip())
    return out


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest)
    glossary_path = Path(args.glossary)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    glossary = load_glossary(glossary_path)
    with manifest_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    if "synthesis_text" not in fieldnames:
        fieldnames.append("synthesis_text")

    changed = 0
    for row in rows:
        original = row["text"].strip()
        synthesis = apply_glossary(original, glossary)
        row["synthesis_text"] = synthesis
        if synthesis != original:
            changed += 1
            print(f"{row['id']}\t{original}\t=>\t{synthesis}")

    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    print(f"changed_rows\t{changed}")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
