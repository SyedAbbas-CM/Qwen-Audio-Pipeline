from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QC = ROOT / "reports" / "qwen-asr-qc.tsv"
DEFAULT_APPROVALS = ROOT / "transcripts" / "approved-takes.tsv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qc", default=str(DEFAULT_QC))
    parser.add_argument("--approvals", default=str(DEFAULT_APPROVALS))
    parser.add_argument("--fail-decision", default="needs_retry")
    parser.add_argument("--warn-decision", default="needs_manual_edit")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def load_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def main() -> int:
    args = parse_args()
    qc_path = Path(args.qc)
    approvals_path = Path(args.approvals)
    approvals_path.parent.mkdir(parents=True, exist_ok=True)

    approvals_rows = load_tsv(approvals_path)
    approvals_by_segment = {row["segment_id"]: row for row in approvals_rows}
    qc_rows = load_tsv(qc_path)

    for qc in qc_rows:
        result = qc.get("qc_result", "")
        if result not in {"warn", "fail"}:
            continue
        segment_id = qc["segment_id"].strip()
        existing = approvals_by_segment.get(segment_id)
        if existing and existing.get("decision") == "approved" and not args.force:
            continue
        if (
            existing
            and existing.get("decision") not in {"approved", "baseline_approved"}
            and not args.force
        ):
            continue
        decision = args.fail_decision if result == "fail" else args.warn_decision
        note = f"qc_{result}: similarity={qc.get('similarity','')} wer={qc.get('wer','')}"
        approvals_by_segment[segment_id] = {
            "segment_id": segment_id,
            "take": "take-01",
            "decision": decision,
            "note": note,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "audio_path": qc["audio_path"].strip(),
        }

    rows = sorted(approvals_by_segment.values(), key=lambda row: row["segment_id"])
    with approvals_path.open("w", newline="", encoding="utf-8") as fh:
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
