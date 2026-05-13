from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PRESETS = {
    "subtle": {"level_db": -45, "highpass": 100, "lowpass": 7000},
    "warm": {"level_db": -42, "highpass": 120, "lowpass": 5000},
    "hiss-control": {"level_db": -48, "highpass": 150, "lowpass": 4500},
}


def duration_seconds(path: Path) -> float:
    proc = subprocess.run(
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
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=True,
    )
    return float(proc.stdout.strip())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--preset", default="subtle", choices=sorted(PRESETS))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    preset = PRESETS[args.preset]

    for wav in sorted(input_dir.glob("*.wav")):
        out_path = output_dir / wav.name
        if out_path.exists() and not args.force:
            print(f"skip {out_path}")
            continue
        dur = duration_seconds(wav)
        vol = 10 ** (preset["level_db"] / 20.0)
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(wav),
                "-f",
                "lavfi",
                "-t",
                f"{dur:.3f}",
                "-i",
                (
                    f"anoisesrc=color=white:amplitude={vol}:sample_rate=24000,"
                    f"highpass=f={preset['highpass']},lowpass=f={preset['lowpass']}"
                ),
                "-filter_complex",
                "[0:a][1:a]amix=inputs=2:weights='1 1':normalize=0",
                "-ar",
                "24000",
                "-ac",
                "1",
                "-c:a",
                "pcm_s16le",
                str(out_path),
            ],
            check=True,
        )
        print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
