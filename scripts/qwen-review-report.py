from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "transcripts" / "devlog-final-manifest-reftext.tsv"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "qwen3-reftext-full-v2"
DEFAULT_ASR = ROOT / "reports" / "qwen-asr-qc.tsv"
DEFAULT_APPROVALS = ROOT / "transcripts" / "approved-takes.tsv"
DEFAULT_OUTPUT = ROOT / "reports" / "qwen-review-report.tsv"


def load_tsv(path: Path, key: str) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        return {row[key].strip(): row for row in reader}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--asr-qc", default=str(DEFAULT_ASR))
    parser.add_argument("--approvals", default=str(DEFAULT_APPROVALS))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    output_dir = Path(args.output_dir)
    qc_map = load_tsv(Path(args.asr_qc), "segment_id")
    approval_map = load_tsv(Path(args.approvals), "segment_id")
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    with manifest_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for order, row in enumerate(reader, start=1):
            segment_id = row["id"].strip()
            marker = row["marker"].strip()
            audio_path = output_dir / segment_id / "take-01-clean.wav"
            status_path = output_dir / segment_id / "take-01-clean.status.json"
            status = {}
            if status_path.exists():
                status = json.loads(status_path.read_text(encoding="utf-8"))
            qc = qc_map.get(segment_id, {})
            approval = approval_map.get(segment_id, {})
            rows.append(
                {
                    "order": str(order),
                    "marker": marker,
                    "segment_id": segment_id,
                    "text": row["text"].strip(),
                    "audio_path": str(audio_path),
                    "status": status.get("status", "missing"),
                    "gen_sec": str(status.get("duration_sec", "")),
                    "duration_sec": qc.get("duration_sec", ""),
                    "asr_similarity": qc.get("similarity", ""),
                    "wer": qc.get("wer", ""),
                    "qc_result": qc.get("qc_result", ""),
                    "backend_status": qc.get("backend_status", ""),
                    "approval_decision": approval.get("decision", ""),
                    "notes": approval.get("note", "") or qc.get("note", ""),
                }
            )

    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "order",
                "marker",
                "segment_id",
                "text",
                "audio_path",
                "status",
                "gen_sec",
                "duration_sec",
                "asr_similarity",
                "wer",
                "qc_result",
                "backend_status",
                "approval_decision",
                "notes",
            ],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
