from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "voice-pipeline.json"
DEFAULT_MANIFEST = ROOT / "transcripts" / "devlog-final-manifest-spoken.tsv"
DEFAULT_OUT = ROOT / "outputs" / "qwen3-reftext-full-v2"


def load_config() -> dict[str, object]:
    if not CONFIG_PATH.exists():
        return {}
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def parse_args() -> argparse.Namespace:
    config = load_config()
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(config.get("manifest", DEFAULT_MANIFEST)))
    parser.add_argument("--output-dir", default=str(config.get("output_dir", DEFAULT_OUT)))
    parser.add_argument("--status", action="append", default=["timeout", "qwen_failed", "postprocess_failed"])
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--reference", default=str(config.get("reference", "")))
    parser.add_argument("--reference-text-file", default=str(config.get("reference_text_file", "")))
    parser.add_argument("--model-id", default=str(config.get("qwen_model_id", "")))
    parser.add_argument("--temperature", type=float, default=float(config.get("temperature", 0.35)))
    parser.add_argument("--timeout-sec", type=int, default=int(config.get("timeout_sec", 900)))
    parser.add_argument("--postprocess-profile", default=str(config.get("postprocess_profile", "light")))
    parser.add_argument("--x-vector-only", action="store_true", default=bool(config.get("x_vector_only", False)))
    parser.add_argument("--fallback-x-vector-only", action="store_true")
    parser.add_argument("--fallback-output-dir", default="")
    return parser.parse_args()


def load_manifest(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return {row["id"].strip(): row for row in csv.DictReader(fh, delimiter="\t")}


def run_take(
    *,
    seg_id: str,
    text: str,
    output_dir: Path,
    model_id: str,
    reference: str,
    reference_text_file: str,
    temperature: float,
    timeout_sec: int,
    postprocess_profile: str,
    x_vector_only: bool,
) -> int:
    seg_dir = output_dir / seg_id
    seg_dir.mkdir(parents=True, exist_ok=True)
    raw_path = seg_dir / "take-01-raw.wav"
    clean_path = seg_dir / "take-01-clean.wav"
    text_path = seg_dir / "take-01.txt"
    text_path.write_text(text, encoding="utf-8")

    cmd = [
        str(ROOT / "envs" / "qwen3" / "bin" / "python"),
        str(ROOT / "scripts" / "qwen-run-one-take.py"),
        "--text",
        text,
        "--model-id",
        model_id,
        "--reference",
        reference,
        "--temperature",
        str(temperature),
        "--timeout-sec",
        str(timeout_sec),
        "--postprocess-profile",
        postprocess_profile,
        "--output-raw",
        str(raw_path),
        "--output-clean",
        str(clean_path),
    ]
    if x_vector_only:
        cmd.append("--x-vector-only")
    else:
        cmd.extend(["--reference-text-file", reference_text_file])

    proc = subprocess.run(cmd, cwd=ROOT, check=False)
    status_path = seg_dir / "take-01-clean.status.json"
    if status_path.exists():
        try:
            data = json.loads(status_path.read_text(encoding="utf-8"))
            data["segment_id"] = seg_id
            data["retry_mode"] = "fallback_xvec" if x_vector_only else "retry_reftext"
            status_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass
    return proc.returncode


def main() -> int:
    args = parse_args()
    manifest = load_manifest(Path(args.manifest))
    output_dir = Path(args.output_dir)
    fallback_output_dir = Path(args.fallback_output_dir) if args.fallback_output_dir else output_dir
    wanted = set(args.status)
    retried = 0

    for seg_dir in sorted(p for p in output_dir.iterdir() if p.is_dir()):
        status_path = seg_dir / "take-01-clean.status.json"
        if not status_path.exists():
            continue
        try:
            status_data = json.loads(status_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        status = status_data.get("status")
        if status not in wanted:
            continue
        seg_id = seg_dir.name
        row = manifest.get(seg_id)
        if row is None:
            print(f"skip missing manifest row: {seg_id}")
            continue
        if args.limit and retried >= args.limit:
            break
        retried += 1

        text = (row.get("synthesis_text") or row.get("text") or "").strip()
        if not text:
            print(f"skip empty text: {seg_id}")
            continue

        target_dir = output_dir
        use_xvec = args.x_vector_only
        if args.fallback_x_vector_only and status == "timeout":
            target_dir = fallback_output_dir
            use_xvec = True

        rc = run_take(
            seg_id=seg_id,
            text=text,
            output_dir=target_dir,
            model_id=args.model_id,
            reference=args.reference,
            reference_text_file=args.reference_text_file,
            temperature=args.temperature,
            timeout_sec=args.timeout_sec,
            postprocess_profile=args.postprocess_profile,
            x_vector_only=use_xvec,
        )
        print(f"{seg_id}\treturn={rc}\tfallback_xvec={use_xvec}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
