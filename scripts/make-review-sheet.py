from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / "reports" / "qwen-review-report.tsv"
DEFAULT_OUTPUT = ROOT / "reports" / "qwen-review-sheet.tsv"


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

    rows: list[dict[str, str]] = []
    with report_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            rows.append(
                {
                    "action": "",
                    "segment_id": row["segment_id"].strip(),
                    "marker": row["marker"].strip(),
                    "qc": row.get("qc_result", "").strip(),
                    "status": row.get("status", "").strip(),
                    "approval": row.get("approval_decision", "").strip(),
                    "text": row.get("text", "").strip(),
                    "audio_path": row.get("audio_path", "").strip(),
                    "notes": "",
                }
            )

    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["action", "segment_id", "marker", "qc", "status", "approval", "text", "audio_path", "notes"],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerow(
            {
                "action": "#",
                "segment_id": "Codes",
                "marker": "A approve | B baseline_approved | R reject | T retry | W rewrite | M manual_edit | blank keep current",
                "qc": "",
                "status": "",
                "approval": "",
                "text": "",
                "audio_path": "",
                "notes": "",
            }
        )
        writer.writerows(rows)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
