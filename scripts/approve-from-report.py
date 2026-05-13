from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / "reports" / "qwen-review-report.tsv"
DEFAULT_APPROVALS = ROOT / "transcripts" / "approved-takes.tsv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--approvals", default=str(DEFAULT_APPROVALS))
    parser.add_argument("--decision", default="baseline_approved", choices=[
        "approved",
        "baseline_approved",
        "rejected",
        "needs_retry",
        "needs_script_rewrite",
        "needs_manual_edit",
    ])
    parser.add_argument("--status", default="ready")
    parser.add_argument("--marker")
    parser.add_argument("--note", default="bulk decision from review report")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def load_existing(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def main() -> int:
    args = parse_args()
    report_path = Path(args.report)
    approvals_path = Path(args.approvals)
    approvals_path.parent.mkdir(parents=True, exist_ok=True)

    existing = load_existing(approvals_path)
    by_segment = {row["segment_id"]: row for row in existing}

    with report_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            if args.status and row.get("status", "").strip() != args.status:
                continue
            if args.marker and row.get("marker", "").strip() != args.marker:
                continue
            segment_id = row["segment_id"].strip()
            if segment_id in by_segment and not args.force:
                continue
            by_segment[segment_id] = {
                "segment_id": segment_id,
                "take": "take-01",
                "decision": args.decision,
                "note": args.note,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "audio_path": row["audio_path"].strip(),
            }

    rows = sorted(by_segment.values(), key=lambda item: item["segment_id"])
    with approvals_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["segment_id", "take", "decision", "note", "updated_at", "audio_path"],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)
    print(approvals_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
