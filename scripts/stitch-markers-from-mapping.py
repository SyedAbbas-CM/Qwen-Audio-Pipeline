from __future__ import annotations

import argparse
import csv
import re
import subprocess
import tempfile
from collections import OrderedDict
from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "transcripts" / "devlog-final-manifest-spoken.tsv"

CHUNK_SUFFIX_RE = re.compile(r"-c\d+$")


def base_segment_id(segment_id: str) -> str:
    return CHUNK_SUFFIX_RE.sub("", segment_id)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--mapping", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--input-kind", choices=["clean", "raw"], default="clean")
    parser.add_argument("--input-postprocess-profile", default="")
    parser.add_argument("--crossfade-ms", type=int, default=18)
    parser.add_argument("--roomtone-preset", default="")
    parser.add_argument("--postprocess-profile", default="")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def mapped_input_path(mapped_path: Path, kind: str) -> Path:
    if kind == "clean":
        return mapped_path
    raw_name = mapped_path.name.replace("-clean.wav", "-raw.wav")
    return mapped_path.with_name(raw_name)


def stitch_concat(inputs: list[Path], out_path: Path) -> None:
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
            str(out_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def stitch_crossfade(inputs: list[Path], out_path: Path, crossfade_ms: int) -> None:
    if len(inputs) == 1 or crossfade_ms <= 0:
        stitch_concat(inputs, out_path)
        return

    fade_sec = crossfade_ms / 1000.0
    cmd = ["ffmpeg", "-y"]
    for item in inputs:
        cmd += ["-i", str(item)]

    filter_parts: list[str] = []
    previous = "[0:a]"
    for idx in range(1, len(inputs)):
        out_label = f"[xf{idx}]"
        filter_parts.append(
            f"{previous}[{idx}:a]acrossfade=d={fade_sec:.3f}:c1=tri:c2=tri{out_label}"
        )
        previous = out_label

    cmd += [
        "-filter_complex",
        ";".join(filter_parts),
        "-map",
        previous,
        "-ar",
        "24000",
        "-ac",
        "1",
        "-c:a",
        "pcm_s16le",
        str(out_path),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def apply_roomtone(in_path: Path, out_path: Path, preset: str) -> None:
    script = ROOT / "scripts" / "add-roomtone-bed.py"
    subprocess.run(
        [
            "python3",
            str(script),
            "--input",
            str(in_path),
            "--output",
            str(out_path),
            "--preset",
            preset,
            "--force",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def apply_postprocess(in_path: Path, out_path: Path, profile: str) -> None:
    script = ROOT / "scripts" / "postprocess-voice.sh"
    subprocess.run(
        [
            str(script),
            str(in_path),
            str(out_path),
            profile,
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def prepare_inputs(inputs: list[Path], temp_dir: Path, profile: str) -> list[Path]:
    if not profile:
        return inputs

    prepared: list[Path] = []
    prep_dir = temp_dir / "prepared_inputs"
    prep_dir.mkdir(parents=True, exist_ok=True)
    for idx, path in enumerate(inputs):
        out_path = prep_dir / f"{idx:03d}-{path.stem}.wav"
        apply_postprocess(path, out_path, profile)
        prepared.append(out_path)
    return prepared


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest)
    mapping_path = Path(args.mapping)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = output_dir / "_intermediate"
    if args.roomtone_preset or args.postprocess_profile:
        temp_dir.mkdir(parents=True, exist_ok=True)

    grouped: "OrderedDict[str, list[str]]" = OrderedDict()
    with manifest_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            seg_id = row["id"].strip()
            grouped.setdefault(base_segment_id(seg_id), []).append(seg_id)

    mapping: dict[str, Path] = {}
    with mapping_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            mapping[row["segment_id"].strip()] = Path(row["audio_path"])

    for marker_id, seg_ids in grouped.items():
        inputs: list[Path] = []
        for seg_id in seg_ids:
            mapped_path = mapping.get(seg_id)
            audio_path = mapped_input_path(mapped_path, args.input_kind) if mapped_path is not None else None
            if audio_path is None or not audio_path.exists():
                inputs = []
                print(f"skip {marker_id}: missing {args.input_kind} audio for {seg_id}")
                break
            inputs.append(audio_path)
        if not inputs:
            continue

        out_path = output_dir / f"{marker_id}.wav"
        if out_path.exists() and not args.force:
            print(f"skip {out_path}")
            continue

        stitched_path = out_path
        roomtone_path = out_path
        if args.roomtone_preset or args.postprocess_profile:
            stitched_path = temp_dir / f"{marker_id}.stitched.wav"
        if args.roomtone_preset and args.postprocess_profile:
            roomtone_path = temp_dir / f"{marker_id}.roomtone.wav"

        prepared_inputs = prepare_inputs(inputs, temp_dir / marker_id, args.input_postprocess_profile)
        stitch_crossfade(prepared_inputs, stitched_path, args.crossfade_ms)

        if args.postprocess_profile:
            post_output = roomtone_path if args.roomtone_preset else out_path
            apply_postprocess(stitched_path, post_output, args.postprocess_profile)
        if args.roomtone_preset:
            roomtone_input = roomtone_path if args.postprocess_profile else stitched_path
            apply_roomtone(roomtone_input, out_path, args.roomtone_preset)
        elif not args.postprocess_profile and stitched_path != out_path:
            stitched_path.replace(out_path)

        print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
