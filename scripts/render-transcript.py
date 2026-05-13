from __future__ import annotations

import argparse
import csv
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEGMENTS = ROOT / "transcripts" / "devlog-final-segments.tsv"
REF = ROOT / "references" / "karachi.m4a"
OUT_DIR = ROOT / "outputs" / "devlog-final"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--segments", default=str(SEGMENTS))
    parser.add_argument("--reference", default=str(REF))
    parser.add_argument("--output-dir", default=str(OUT_DIR))
    parser.add_argument("--only-id", action="append", default=[])
    parser.add_argument("--skip-existing", action="store_true")
    return parser.parse_args()


def run() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    only_ids = set(args.only_id)

    with open(args.segments, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            seg_id = row["id"].strip()
            if only_ids and seg_id not in only_ids:
                continue

            base_out = output_dir / f"{seg_id}.wav"
            final_out = output_dir / f"{seg_id}-styled.wav"

            if args.skip_existing and final_out.exists():
                print(f"skip {seg_id}")
                continue

            subprocess.run(
                [
                    str(ROOT / "envs" / "chatterbox" / "bin" / "python"),
                    str(ROOT / "scripts" / "chatterbox-say.py"),
                    row["text"],
                    "--preset",
                    row["preset"],
                    "--reference",
                    args.reference,
                    "--output-path",
                    str(base_out),
                ],
                cwd=ROOT,
                check=True,
            )

            subprocess.run(
                [
                    str(ROOT / "scripts" / "style-voice.sh"),
                    str(base_out),
                    str(final_out),
                    row["post"],
                ],
                cwd=ROOT,
                check=True,
            )

            print(final_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
