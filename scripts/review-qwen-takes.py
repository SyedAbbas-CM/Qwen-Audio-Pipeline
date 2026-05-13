from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "outputs" / "qwen3-devlog"


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
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default=str(DEFAULT_OUT))
    args = parser.parse_args()

    root = Path(args.output_dir)
    print("id\ttake\tduration_s\tstatus\tclean\traw")
    for seg_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        status_files = sorted(seg_dir.glob("take-*-clean.status.json"))
        for status_file in status_files:
            data = json.loads(status_file.read_text(encoding="utf-8"))
            take_id = status_file.name.replace("-clean.status.json", "")
            clean = Path(data["output_clean"])
            raw = Path(data["output_raw"])
            duration = ffprobe_duration(clean) if clean.exists() else 0.0
            print(f"{seg_dir.name}\t{take_id}\t{duration:.2f}\t{data.get('status','unknown')}\t{'yes' if clean.exists() else 'no'}\t{'yes' if raw.exists() else 'no'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
