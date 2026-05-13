from __future__ import annotations

import argparse
import csv
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SEGMENTS = ROOT / "transcripts" / "devlog-final-segments.tsv"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "devlog-final"


def ffprobe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--segments", default=str(DEFAULT_SEGMENTS))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--min-seconds", type=float, default=1.0)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)

    print("id\tstatus\tduration_s\tnotes")
    with open(args.segments, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            seg_id = row["id"].strip()
            path = output_dir / f"{seg_id}-styled.wav"
            if not path.exists():
                print(f"{seg_id}\tmissing\t0\tregenerate")
                continue
            duration = ffprobe_duration(path)
            note = "ok"
            status = "ready"
            if duration < args.min_seconds:
                status = "short"
                note = "possible glitch"
            print(f"{seg_id}\t{status}\t{duration:.2f}\t{note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
