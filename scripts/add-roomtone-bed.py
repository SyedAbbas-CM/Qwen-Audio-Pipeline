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


def apply_roomtone(input_path: Path, output_path: Path, preset_name: str) -> None:
    preset = PRESETS[preset_name]
    dur = duration_seconds(input_path)
    vol = 10 ** (preset["level_db"] / 20.0)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
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
            str(output_path),
        ],
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", default="")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--input", default="")
    parser.add_argument("--output", default="")
    parser.add_argument("--preset", default="subtle", choices=sorted(PRESETS))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    single_file = bool(args.input or args.output)
    if single_file:
        if not (args.input and args.output):
            raise SystemExit("--input and --output must be provided together")
        in_path = Path(args.input)
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if out_path.exists() and not args.force:
            print(f"skip {out_path}")
            return 0
        apply_roomtone(in_path, out_path, args.preset)
        print(out_path)
        return 0

    if not args.input_dir or not args.output_dir:
        raise SystemExit("--input-dir and --output-dir are required unless using --input/--output")

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for wav in sorted(input_dir.glob("*.wav")):
        out_path = output_dir / wav.name
        if out_path.exists() and not args.force:
            print(f"skip {out_path}")
            continue
        apply_roomtone(wav, out_path, args.preset)
        print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
