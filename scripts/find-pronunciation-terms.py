from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRANSCRIPT = ROOT / "transcripts" / "devlog-final.txt"
DEFAULT_OUTPUT = ROOT / "reports" / "pronunciation-candidates.tsv"

ACRONYM_RE = re.compile(r"\b[A-Z]{2,}\b")
DIGIT_MIX_RE = re.compile(r"\b(?=\S*[A-Za-z])(?=\S*\d)\S+\b")
SYMBOL_RE = re.compile(r"\b\S*[*+#/]\S*\b")
CAMEL_CASE_RE = re.compile(r"\b[A-Za-z0-9]*[a-z][A-Z][A-Za-z0-9]*\b|\b[A-Za-z0-9]*[A-Z][a-z]+[A-Z][A-Za-z0-9]*\b")
TERM_RE = re.compile(r"\b[\w'.*+#/:-]+\b")

KNOWN_TECH_TERMS = {
    "godot",
    "webgl",
    "rotmg",
    "vfx",
    "gpu",
    "dps",
    "npc",
    "ai",
    "llm",
    "morrowind",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--transcript", default=str(DEFAULT_TRANSCRIPT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    return parser.parse_args()


def add_candidate(candidates: dict[str, set[str]], term: str, reason: str) -> None:
    if not term.strip():
        return
    candidates.setdefault(term, set()).add(reason)


def main() -> int:
    args = parse_args()
    transcript_path = Path(args.transcript)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    text = transcript_path.read_text(encoding="utf-8")
    candidates: dict[str, set[str]] = {}

    for match in ACRONYM_RE.finditer(text):
        add_candidate(candidates, match.group(0), "all_caps_acronym")
    for match in DIGIT_MIX_RE.finditer(text):
        add_candidate(candidates, match.group(0), "digit_mixed")
    for match in SYMBOL_RE.finditer(text):
        add_candidate(candidates, match.group(0), "symbol_term")
    for match in CAMEL_CASE_RE.finditer(text):
        add_candidate(candidates, match.group(0), "camel_or_internal_caps")
    for match in TERM_RE.finditer(text):
        token = match.group(0)
        if token.lower() in KNOWN_TECH_TERMS:
            add_candidate(candidates, token, "known_technical_term")

    rows = [
        {
            "term": term,
            "reasons": ",".join(sorted(reasons)),
        }
        for term, reasons in sorted(candidates.items(), key=lambda item: item[0].lower())
    ]

    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["term", "reasons"], delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
