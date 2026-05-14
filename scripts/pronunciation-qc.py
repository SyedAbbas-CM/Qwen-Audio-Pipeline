from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "transcripts" / "devlog-final-manifest-spoken.tsv"
DEFAULT_GLOSSARY = ROOT / "config" / "pronunciation-glossary.tsv"
DEFAULT_ASR = ROOT / "reports" / "qwen-asr-qc.tsv"
DEFAULT_OUTPUT = ROOT / "reports" / "pronunciation-qc.tsv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--glossary", default=str(DEFAULT_GLOSSARY))
    parser.add_argument("--asr-qc", default=str(DEFAULT_ASR))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    return parser.parse_args()


def norm(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s']", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def term_in_text(term: str, text: str) -> bool:
    pattern = re.compile(rf"(?<![\w]){re.escape(term)}(?![\w])", flags=re.IGNORECASE)
    return bool(pattern.search(text))


def load_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def main() -> int:
    args = parse_args()
    manifest_rows = load_tsv(Path(args.manifest))
    glossary_rows = load_tsv(Path(args.glossary))
    asr_rows = {row["segment_id"].strip(): row for row in load_tsv(Path(args.asr_qc))}
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    for row in manifest_rows:
        segment_id = row["id"].strip()
        original_text = row["text"].strip()
        synthesis_text = row.get("synthesis_text", "").strip() or original_text
        synthesis_norm = norm(synthesis_text)
        asr_text = asr_rows.get(segment_id, {}).get("asr_text", "")
        asr_norm = norm(asr_text)

        matched_terms: list[str] = []
        expected_replacements: list[str] = []
        result = "pass"
        note = ""

        for entry in glossary_rows:
            term = entry.get("term", "").strip()
            replacement = entry.get("replacement_text", "").strip()
            if not term or not replacement:
                continue
            if not term_in_text(term, original_text):
                continue

            matched_terms.append(term)
            expected_replacements.append(replacement)

            replacement_norm = norm(replacement)
            if replacement_norm not in synthesis_norm:
                result = "fail"
                note = f"replacement_missing_in_synthesis:{term}"
                break
            if asr_norm and replacement_norm not in asr_norm:
                if result != "fail":
                    result = "warn"
                    note = f"replacement_not_heard_cleanly:{term}"

        if not matched_terms:
            result = "n/a"

        rows.append(
            {
                "segment_id": segment_id,
                "marker": row["marker"].strip(),
                "original_text": original_text,
                "synthesis_text": synthesis_text,
                "matched_terms": ", ".join(matched_terms),
                "expected_replacements": " | ".join(expected_replacements),
                "asr_text": asr_text,
                "result": result,
                "note": note,
            }
        )

    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "segment_id",
                "marker",
                "original_text",
                "synthesis_text",
                "matched_terms",
                "expected_replacements",
                "asr_text",
                "result",
                "note",
            ],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
