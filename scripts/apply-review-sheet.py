from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SHEET = ROOT / "reports" / "qwen-review-sheet.tsv"
DEFAULT_APPROVALS = ROOT / "transcripts" / "approved-takes.tsv"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "qwen3-reftext-full-v2"

ACTION_MAP = {
    "A": "approved",
    "B": "baseline_approved",
    "R": "rejected",
    "T": "needs_retry",
    "W": "needs_script_rewrite",
    "M": "needs_manual_edit",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sheet", default=str(DEFAULT_SHEET))
    parser.add_argument("--approvals", default=str(DEFAULT_APPROVALS))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sheet_path = Path(args.sheet)
    approvals_path = Path(args.approvals)
    output_dir = Path(args.output_dir)

    existing: list[dict[str, str]] = []
    existing_map: dict[str, dict[str, str]] = {}
    if approvals_path.exists():
        with approvals_path.open(newline="", encoding="utf-8") as fh:
            existing = list(csv.DictReader(fh, delimiter="\t"))
        existing_map = {row["segment_id"].strip(): row for row in existing}

    with sheet_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            if row["action"].strip().startswith("#"):
                continue
            action = row["action"].strip().upper()
            if not action:
                continue
            decision = ACTION_MAP.get(action)
            if not decision:
                continue
            segment_id = row["segment_id"].strip()
            take = "take-01"
            existing_map[segment_id] = {
                "segment_id": segment_id,
                "take": take,
                "decision": decision,
                "note": row.get("notes", "").strip(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "audio_path": str(output_dir / segment_id / f"{take}-clean.wav"),
            }

    merged = sorted(existing_map.values(), key=lambda item: item["segment_id"])
    approvals_path.parent.mkdir(parents=True, exist_ok=True)
    with approvals_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["segment_id", "take", "decision", "note", "updated_at", "audio_path"],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(merged)
    print(approvals_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
