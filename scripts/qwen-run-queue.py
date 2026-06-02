from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "voice-pipeline.json"
DEFAULT_MANIFEST = ROOT / "transcripts" / "devlog-final-manifest-reftext.tsv"
DEFAULT_OUT = ROOT / "outputs" / "qwen3-reftext-full-v2"
DEFAULT_MODEL = Path.home() / ".cache" / "huggingface" / "hub" / "models--Qwen--Qwen3-TTS-12Hz-0.6B-Base" / "snapshots" / "5d83992436eae1d760afd27aff78a71d676296fc"
DEFAULT_REF = ROOT / "references" / "karachi-24k-mono-short.wav"
DEFAULT_REF_TEXT = ROOT / "transcripts" / "reference-voice-short.txt"


def load_config() -> dict[str, object]:
    if not CONFIG_PATH.exists():
        return {}
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def clean_status_ready(clean_path: Path) -> bool:
    status_path = clean_path.with_suffix(".status.json")
    if not clean_path.exists() or not status_path.exists():
        return False
    try:
        data = json.loads(status_path.read_text(encoding="utf-8"))
    except Exception:
        return False
    return data.get("status") == "ready"


def config_path(value: object, fallback: Path) -> Path:
    if value is None:
        return fallback
    path = Path(str(value))
    return path if path.is_absolute() else ROOT / path


def parse_args() -> argparse.Namespace:
    config = load_config()
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(config_path(config.get("manifest"), DEFAULT_MANIFEST)))
    parser.add_argument("--output-dir", default=str(config_path(config.get("output_dir"), DEFAULT_OUT)))
    parser.add_argument("--model-id", default=str(config.get("qwen_model_id", DEFAULT_MODEL)))
    parser.add_argument("--reference", default=str(config.get("reference", DEFAULT_REF)))
    parser.add_argument("--reference-text-file", default=str(config.get("reference_text_file", DEFAULT_REF_TEXT)))
    parser.add_argument("--temperature", type=float, default=float(config.get("temperature", 0.35)))
    parser.add_argument("--postprocess-profile", default=str(config.get("postprocess_profile", "light")))
    parser.add_argument("--timeout-sec", type=int, default=int(config.get("timeout_sec", 900)))
    parser.add_argument("--x-vector-only", action="store_true", default=bool(config.get("x_vector_only", False)))
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--start-at", default="")
    parser.add_argument("--limit", type=int, default=0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_root = Path(args.output_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    started = not bool(args.start_at)
    count = 0
    with open(args.manifest, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            raw_seg_id = row.get("id")
            raw_text = row.get("text")
            if raw_seg_id is None or raw_text is None:
                print(f"skip malformed row: {row}")
                continue
            seg_id = raw_seg_id.strip()
            if not seg_id:
                print(f"skip empty id row: {row}")
                continue
            if not started:
                if seg_id == args.start_at:
                    started = True
                else:
                    continue
            if args.limit and count >= args.limit:
                break

            seg_dir = out_root / seg_id
            seg_dir.mkdir(parents=True, exist_ok=True)
            raw_path = seg_dir / "take-01-raw.wav"
            clean_path = seg_dir / "take-01-clean.wav"
            text_path = seg_dir / "take-01.txt"
            original_text_path = seg_dir / "take-01-original.txt"
            original_text = raw_text.strip()
            synthesis_text = row.get("synthesis_text", "").strip() or original_text
            text_path.write_text(synthesis_text, encoding="utf-8")
            if synthesis_text != original_text:
                original_text_path.write_text(original_text, encoding="utf-8")
            else:
                original_text_path.unlink(missing_ok=True)

            if args.skip_existing and clean_status_ready(clean_path):
                print(f"skip {seg_id}")
                count += 1
                continue

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
                cmd.extend(
                    [
                        "--reference-text-file",
                        args.reference_text_file,
                    ]
                )
            proc = subprocess.run(cmd, cwd=ROOT)
            status_path = clean_path.with_suffix(".status.json")
            if status_path.exists():
                try:
                    status = json.loads(status_path.read_text(encoding="utf-8"))
                    status["original_text"] = original_text
                    status["synthesis_text"] = synthesis_text
                    status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
                except Exception:
                    pass
            print(f"{seg_id}\treturn={proc.returncode}")
            count += 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
