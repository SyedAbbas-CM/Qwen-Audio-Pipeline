from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "transcripts" / "devlog-final-manifest.tsv"
DEFAULT_TAKES = ROOT / "transcripts" / "devlog-final-takes.tsv"
DEFAULT_REF = ROOT / "references" / "karachi-24k-mono.wav"
DEFAULT_REF_TEXT = ROOT / "transcripts" / "reference-voice.txt"
DEFAULT_MODEL = Path.home() / ".cache" / "huggingface" / "hub" / "models--Qwen--Qwen3-TTS-12Hz-0.6B-Base" / "snapshots" / "5d83992436eae1d760afd27aff78a71d676296fc"
DEFAULT_OUT = ROOT / "outputs" / "qwen3-devlog"
DEFAULT_CONFIG = ROOT / "config" / "voice-pipeline.json"


def load_build_variants():
    helper_path = ROOT / "scripts" / "voice_direction.py"
    spec = importlib.util.spec_from_file_location("create_qwen_takes_helper", helper_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load helper from {helper_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_variants


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--takes-file", default=str(DEFAULT_TAKES))
    parser.add_argument("--use-takes-file", action="store_true")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--reference", default=str(DEFAULT_REF))
    parser.add_argument("--reference-text-file", default=str(DEFAULT_REF_TEXT))
    parser.add_argument("--model-id", default=str(DEFAULT_MODEL))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUT))
    parser.add_argument("--takes", type=int, default=2)
    parser.add_argument("--x-vector-only", action="store_true")
    parser.add_argument("--temperature", type=float, default=0.35)
    parser.add_argument("--postprocess-profile", default="light")
    parser.add_argument("--take-start", type=int, default=1)
    parser.add_argument("--take-end", type=int, default=0)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--only-id", action="append", default=[])
    parser.add_argument("--skip-existing", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    build_variants = load_build_variants()
    if Path(args.config).exists():
        config = json.loads(Path(args.config).read_text(encoding="utf-8"))
        if args.reference == str(DEFAULT_REF):
            args.reference = config.get("reference", args.reference)
        if args.reference_text_file == str(DEFAULT_REF_TEXT):
            args.reference_text_file = config.get("reference_text_file", args.reference_text_file)
        if args.model_id == str(DEFAULT_MODEL):
            args.model_id = config.get("qwen_model_id", args.model_id)
        if args.takes == 2:
            args.takes = int(config.get("default_takes", args.takes))
        if not args.x_vector_only:
            args.x_vector_only = bool(config.get("x_vector_only", False))
        if args.temperature == 0.35:
            args.temperature = float(config.get("temperature", args.temperature))
        if args.postprocess_profile == "light":
            args.postprocess_profile = config.get("postprocess_profile", args.postprocess_profile)

    out_root = Path(args.output_dir)
    out_root.mkdir(parents=True, exist_ok=True)
    selected_ids = set(args.only_id)

    source_file = args.takes_file if args.use_takes_file else args.manifest
    with open(source_file, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        count = 0
        for row in reader:
            seg_id = row["segment_id"].strip() if args.use_takes_file else row["id"].strip()
            if selected_ids and seg_id not in selected_ids:
                continue
            if args.limit and count >= args.limit:
                break
            count += 1

            seg_dir = out_root / seg_id
            seg_dir.mkdir(parents=True, exist_ok=True)
            if args.use_takes_file:
                take_end = args.take_end if args.take_end > 0 else args.takes
                take_idx = int(row["take"])
                if take_idx < args.take_start or take_idx > take_end:
                    continue
                take_rows = [(take_idx, row["text"].strip(), float(row.get("temperature", args.temperature)))]
            else:
                variants = build_variants(
                    row["text"].strip(),
                    row["style"].strip(),
                    args.takes,
                    intent=row.get("intent", "").strip() or "explaining",
                )
                take_end = args.take_end if args.take_end > 0 else args.takes
                take_rows = [
                    (idx, variant["text"], float(variant["temperature"]))
                    for idx, variant in enumerate(variants, start=1)
                    if args.take_start <= idx <= take_end
                ]

            for take_idx, take_text, take_temp in take_rows:
                raw_path = seg_dir / f"take-{take_idx:02d}-raw.wav"
                clean_path = seg_dir / f"take-{take_idx:02d}-clean.wav"
                text_path = seg_dir / f"take-{take_idx:02d}.txt"
                text_path.write_text(take_text, encoding="utf-8")

                if args.skip_existing and clean_path.exists():
                    print(f"skip {seg_id} take {take_idx}")
                    continue

                subprocess.run(
                    [
                        str(ROOT / "envs" / "qwen3" / "bin" / "python"),
                        str(ROOT / "scripts" / "qwen-run-one-take.py"),
                        "--text",
                        take_text,
                        "--model-id",
                        args.model_id,
                        "--reference",
                        args.reference,
                        *(["--x-vector-only"] if args.x_vector_only else ["--reference-text-file", args.reference_text_file]),
                        "--temperature",
                        str(take_temp),
                        "--postprocess-profile",
                        args.postprocess_profile,
                        "--output-raw",
                        str(raw_path),
                        "--output-clean",
                        str(clean_path),
                    ],
                    cwd=ROOT,
                    check=True,
                )
                print(clean_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
