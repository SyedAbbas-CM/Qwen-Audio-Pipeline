from __future__ import annotations

import argparse
import csv
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "transcripts" / "devlog-final-manifest-spoken.tsv"
DEFAULT_OUTPUT = ROOT / "outputs" / "final" / "devlog-final-mixed.wav"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--mapping-output", default="")
    parser.add_argument("--take-name", default="take-01")
    parser.add_argument("--source", action="append", required=True, help="name=dir")
    return parser.parse_args()


def parse_sources(items: list[str]) -> list[tuple[str, Path]]:
    sources: list[tuple[str, Path]] = []
    for item in items:
        if "=" not in item:
            raise SystemExit(f"invalid source: {item}")
        name, raw_path = item.split("=", 1)
        path = Path(raw_path)
        if not path.is_absolute():
            path = ROOT / path
        sources.append((name.strip(), path))
    return sources


def ready_audio_path(seg_dir: Path, take_name: str) -> Path | None:
    clean = seg_dir / f"{take_name}-clean.wav"
    status = seg_dir / f"{take_name}-clean.status.json"
    if not clean.exists() or not status.exists():
        return None
    try:
        data = json.loads(status.read_text(encoding="utf-8"))
    except Exception:
        return None
    return clean if data.get("status") == "ready" else None


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mapping_path = Path(args.mapping_output) if args.mapping_output else output_path.with_suffix(".mapping.tsv")
    sources = parse_sources(args.source)

    chosen: list[tuple[str, str, Path]] = []
    missing: list[str] = []

    with manifest_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            seg_id = row["id"].strip()
            picked: tuple[str, Path] | None = None
            for source_name, source_dir in sources:
                candidate = ready_audio_path(source_dir / seg_id, args.take_name)
                if candidate is not None:
                    picked = (source_name, candidate)
                    break
            if picked is None:
                missing.append(seg_id)
            else:
                chosen.append((seg_id, picked[0], picked[1]))

    if missing:
        raise SystemExit("missing ready audio for:\n" + "\n".join(missing))

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as fh:
        for _, _, audio_path in chosen:
            fh.write(f"file '{audio_path.resolve()}'\n")
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
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    with mapping_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, delimiter="\t")
        writer.writerow(["segment_id", "source", "audio_path"])
        for seg_id, source_name, audio_path in chosen:
            writer.writerow([seg_id, source_name, str(audio_path)])

    print(output_path)
    print(mapping_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
