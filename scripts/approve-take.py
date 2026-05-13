from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_APPROVALS = ROOT / "transcripts" / "approved-takes.tsv"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "qwen3-reftext-full-v2"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("segment_id")
    parser.add_argument("take")
    parser.add_argument("--note", default="")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--approvals", default=str(DEFAULT_APPROVALS))
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--approve", action="store_true")
    group.add_argument("--baseline-approve", action="store_true")
    group.add_argument("--reject", action="store_true")
    group.add_argument("--retry", action="store_true")
    group.add_argument("--rewrite", action="store_true")
    group.add_argument("--manual-edit", action="store_true")
    return parser.parse_args()


def decision_from_args(args: argparse.Namespace) -> str:
    if args.approve:
        return "approved"
    if args.baseline_approve:
        return "baseline_approved"
    if args.reject:
        return "rejected"
    if args.retry:
        return "needs_retry"
    if args.rewrite:
        return "needs_script_rewrite"
    return "needs_manual_edit"


def main() -> int:
    args = parse_args()
    approvals_path = Path(args.approvals)
    approvals_path.parent.mkdir(parents=True, exist_ok=True)
    existing: list[dict[str, str]] = []
    if approvals_path.exists():
        with approvals_path.open(newline="", encoding="utf-8") as fh:
            existing = list(csv.DictReader(fh, delimiter="\t"))

    decision = decision_from_args(args)
    audio_path = Path(args.output_dir) / args.segment_id / f"{args.take}-clean.wav"
    row = {
        "segment_id": args.segment_id,
        "take": args.take,
        "decision": decision,
        "note": args.note,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "audio_path": str(audio_path),
    }

    replaced = False
    for idx, item in enumerate(existing):
        if item["segment_id"] == args.segment_id:
            existing[idx] = row
            replaced = True
            break
    if not replaced:
        existing.append(row)

    with approvals_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["segment_id", "take", "decision", "note", "updated_at", "audio_path"],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(existing)
    print(approvals_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
