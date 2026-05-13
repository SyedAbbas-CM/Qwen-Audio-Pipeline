from __future__ import annotations

import argparse
import csv
import re
import subprocess
import tempfile
from collections import OrderedDict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "transcripts" / "devlog-final-manifest.tsv"
DEFAULT_INPUT_DIR = ROOT / "outputs" / "qwen3-devlog-xvec"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "qwen3-devlog-xvec-markers"

CHUNK_SUFFIX_RE = re.compile(r"-c\d+$")


def base_segment_id(segment_id: str) -> str:
    return CHUNK_SUFFIX_RE.sub("", segment_id)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--take", type=int, default=1)
    parser.add_argument("--only-marker", action="append", default=[])
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    selected = set(args.only_marker)

    grouped: "OrderedDict[str, list[str]]" = OrderedDict()
    with open(args.manifest, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            seg_id = row["id"].strip()
            marker_id = base_segment_id(seg_id)
            if selected and marker_id not in selected:
                continue
            grouped.setdefault(marker_id, []).append(seg_id)

    for marker_id, seg_ids in grouped.items():
        inputs: list[Path] = []
        for seg_id in seg_ids:
            wav_path = input_dir / seg_id / f"take-{args.take:02d}-clean.wav"
            if not wav_path.exists():
                print(f"skip {marker_id}: missing {wav_path}")
                inputs = []
                break
            inputs.append(wav_path)
        if not inputs:
            continue

        out_path = output_dir / f"{marker_id}.wav"
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
        print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
