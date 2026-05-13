from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


RMS_RE = re.compile(r"RMS level dB:\s+(-inf|[-0-9.]+)")
PEAK_RE = re.compile(r"Peak level dB:\s+(-inf|[-0-9.]+)")


def parse_db(value: str) -> float:
    return float("-inf") if value == "-inf" else float(value)


def tail_stats(path: Path, tail_start: float) -> dict[str, float]:
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-i",
        str(path),
        "-af",
        f"atrim=start={tail_start},astats=metadata=1:reset=1",
        "-f",
        "null",
        "-",
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=True)
    text = proc.stdout
    rms_matches = RMS_RE.findall(text)
    peak_matches = PEAK_RE.findall(text)
    rms = parse_db(rms_matches[-1]) if rms_matches else float("nan")
    peak = parse_db(peak_matches[-1]) if peak_matches else float("nan")
    return {"tail_rms_db": rms, "tail_peak_db": peak}


def duration_seconds(path: Path) -> float:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=True)
    return float(proc.stdout.strip())


def classify(stats: dict[str, float]) -> str:
    tail_rms = stats["tail_rms_db"]
    tail_peak = stats["tail_peak_db"]
    if tail_rms > -55 or tail_peak > -40:
        return "noisy_tail"
    if tail_rms > -70:
        return "watch_tail"
    return "ok"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+")
    parser.add_argument("--tail-seconds", type=float, default=4.0)
    args = parser.parse_args()

    rows = []
    for item in args.inputs:
        path = Path(item)
        dur = duration_seconds(path)
        tail_start = max(0.0, dur - args.tail_seconds)
        stats = tail_stats(path, tail_start)
        rows.append(
            {
                "file": str(path),
                "duration_s": round(dur, 3),
                "tail_start_s": round(tail_start, 3),
                **stats,
                "status": classify(stats),
            }
        )

    print(json.dumps(rows, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
