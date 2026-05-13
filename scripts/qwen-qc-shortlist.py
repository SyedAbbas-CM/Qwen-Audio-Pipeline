from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / "reports" / "qwen-review-report.tsv"
DEFAULT_OUTPUT = ROOT / "reports" / "qwen-qc-shortlist.tsv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report_path = Path(args.report)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    with report_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            if row.get("approval_decision") not in {
                "needs_retry",
                "needs_manual_edit",
                "needs_script_rewrite",
            }:
                continue
            rows.append(row)

    rows.sort(key=lambda row: (row["approval_decision"], float(row.get("asr_similarity") or 0.0)))

    fieldnames = [
        "marker",
        "segment_id",
        "approval_decision",
        "qc_result",
        "asr_similarity",
        "wer",
        "text",
        "audio_path",
        "notes",
    ]
    slim_rows = [{key: row.get(key, "") for key in fieldnames} for row in rows]

    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=fieldnames,
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(slim_rows)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
