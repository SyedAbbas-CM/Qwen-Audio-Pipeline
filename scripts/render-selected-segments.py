from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "voice-pipeline.json"
DEFAULT_MANIFEST = ROOT / "transcripts" / "devlog-final-manifest-spoken.tsv"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "qwen3-reftext-full-v2"


def load_config() -> dict[str, object]:
    if not CONFIG_PATH.exists():
        return {}
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def config_path(value: object, fallback: Path) -> Path:
    if value is None:
        return fallback
    path = Path(str(value))
    return path if path.is_absolute() else ROOT / path


def parse_args() -> argparse.Namespace:
    config = load_config()
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--output-dir", default=str(config_path(config.get("output_dir"), DEFAULT_OUTPUT_DIR)))
    parser.add_argument("--reference", default=str(config.get("reference")))
    parser.add_argument("--reference-text-file", default=str(config.get("reference_text_file")))
    parser.add_argument("--model-id", default=str(config.get("qwen_model_id")))
    parser.add_argument("--temperature", type=float, default=float(config.get("temperature", 0.35)))
    parser.add_argument("--timeout-sec", type=int, default=int(config.get("timeout_sec", 900)))
    parser.add_argument("--postprocess-profile", default=str(config.get("postprocess_profile", "light")))
    parser.add_argument("--take-name", default="take-02")
    parser.add_argument("--x-vector-only", action="store_true", default=bool(config.get("x_vector_only", False)))
    parser.add_argument("--segment-id", action="append", dest="segment_ids", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    wanted = set(args.segment_ids)
    manifest_path = Path(args.manifest)
    output_root = Path(args.output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    with manifest_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        rows = {row["id"].strip(): row for row in reader}

    for segment_id in args.segment_ids:
        row = rows.get(segment_id)
        if row is None:
            print(f"missing\t{segment_id}")
            continue
        original_text = row["text"].strip()
        synthesis_text = row.get("synthesis_text", "").strip() or original_text

        seg_dir = output_root / segment_id
        seg_dir.mkdir(parents=True, exist_ok=True)
        raw_path = seg_dir / f"{args.take_name}-raw.wav"
        clean_path = seg_dir / f"{args.take_name}-clean.wav"
        text_path = seg_dir / f"{args.take_name}.txt"
        original_text_path = seg_dir / f"{args.take_name}-original.txt"
        text_path.write_text(synthesis_text, encoding="utf-8")
        if synthesis_text != original_text:
            original_text_path.write_text(original_text, encoding="utf-8")
        else:
            original_text_path.unlink(missing_ok=True)

        cmd = [
            str(ROOT / "envs" / "qwen3" / "bin" / "python"),
            str(ROOT / "scripts" / "qwen-run-one-take.py"),
            "--text",
            synthesis_text,
            "--model-id",
            args.model_id,
            "--reference",
            args.reference,
            "--temperature",
            str(args.temperature),
            "--timeout-sec",
            str(args.timeout_sec),
            "--postprocess-profile",
            args.postprocess_profile,
            "--output-raw",
            str(raw_path),
            "--output-clean",
            str(clean_path),
        ]
        if args.x_vector_only:
            cmd.append("--x-vector-only")
        else:
            cmd.extend(["--reference-text-file", args.reference_text_file])
        proc = subprocess.run(cmd, cwd=ROOT)
        status_path = clean_path.with_suffix(".status.json")
        if status_path.exists():
            try:
                status = json.loads(status_path.read_text(encoding="utf-8"))
                status["segment_id"] = segment_id
                status["original_text"] = original_text
                status["synthesis_text"] = synthesis_text
                status["source_manifest"] = str(manifest_path)
                status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
            except Exception:
                pass
        print(f"{segment_id}\t{args.take_name}\treturn={proc.returncode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
