from __future__ import annotations

import argparse
import csv
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "transcripts" / "devlog-final-manifest-reftext.tsv"
DEFAULT_APPROVED = ROOT / "transcripts" / "approved-takes.tsv"
DEFAULT_OUTPUT = ROOT / "outputs" / "final" / "devlog-final.wav"


def load_approvals(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return {row["segment_id"].strip(): row for row in csv.DictReader(fh, delimiter="\t")}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--approved", default=str(DEFAULT_APPROVED))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--allow-baseline", action="store_true")
    parser.add_argument("--allow-unapproved", action="store_true")
    parser.add_argument("--gap-ms", type=int, default=180)
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    approved_path = Path(args.approved)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    approvals = load_approvals(approved_path) if approved_path.exists() else {}

    inputs: list[Path] = []
    missing: list[str] = []
    with manifest_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            segment_id = row["id"].strip()
            approval = approvals.get(segment_id)
            if approval and approval.get("decision") == "approved":
                inputs.append(Path(approval["audio_path"]))
                continue
            if args.allow_baseline and approval and approval.get("decision") == "baseline_approved":
                inputs.append(Path(approval["audio_path"]))
                continue
            if args.allow_unapproved:
                inputs.append(ROOT / "outputs" / "qwen3-reftext-full-v2" / segment_id / "take-01-clean.wav")
                continue
            missing.append(segment_id)

    if missing:
        raise SystemExit("missing approved takes for:\n" + "\n".join(missing))

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as fh:
        for item in inputs:
            fh.write(f"file '{item.resolve()}'\n")
        concat_manifest = fh.name

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_manifest,
            "-ar",
            "24000",
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(output_path),
        ],
        check=True,
    )
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
