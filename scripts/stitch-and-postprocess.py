from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", nargs="+", required=True)
    parser.add_argument("--output-raw", required=True)
    parser.add_argument("--output-clean", required=True)
    parser.add_argument("--crossfade-ms", type=float, default=45.0)
    parser.add_argument("--postprocess-profile", default="light")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    inputs = [Path(item) for item in args.inputs]
    if len(inputs) < 2:
        raise SystemExit("need at least two inputs")

    output_raw = Path(args.output_raw)
    output_clean = Path(args.output_clean)
    output_raw.parent.mkdir(parents=True, exist_ok=True)
    output_clean.parent.mkdir(parents=True, exist_ok=True)

    ffmpeg_cmd = ["ffmpeg", "-y"]
    for item in inputs:
        ffmpeg_cmd.extend(["-i", str(item)])

    chain = "[0:a][1:a]acrossfade=d={d}:c1=tri:c2=tri[a01]".format(d=args.crossfade_ms / 1000.0)
    last_label = "[a01]"
    for idx in range(2, len(inputs)):
        next_label = f"[a{idx:02d}]"
        chain += f";{last_label}[{idx}:a]acrossfade=d={args.crossfade_ms / 1000.0}:c1=tri:c2=tri{next_label}"
        last_label = next_label

    ffmpeg_cmd.extend(
        [
            "-filter_complex",
            chain,
            "-map",
            last_label,
            "-ar",
            "24000",
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(output_raw),
        ]
    )
    subprocess.run(ffmpeg_cmd, check=True, cwd=ROOT)

    subprocess.run(
        [
            str(ROOT / "scripts" / "postprocess-voice.sh"),
            str(output_raw),
            str(output_clean),
            args.postprocess_profile,
        ],
        check=True,
        cwd=ROOT,
    )
    print(output_clean)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
