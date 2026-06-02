from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path

from voice_direction import build_variants


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "voice-pipeline.json"
DEFAULT_MANIFEST = ROOT / "transcripts" / "devlog-final-manifest-spoken.tsv"
DEFAULT_OUTPUT = ROOT / "outputs" / "qwen3-intent-probes"
DEFAULT_INTENTS = ["reactive", "annoyed", "deadpan", "sarcastic"]


def load_config() -> dict[str, object]:
    if not CONFIG_PATH.exists():
        return {}
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def parse_args() -> argparse.Namespace:
    config = load_config()
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--segment-id", action="append", required=True)
    parser.add_argument("--intent", action="append", default=[])
    parser.add_argument("--reference", default=str(config.get("reference", "")))
    parser.add_argument("--reference-text-file", default=str(config.get("reference_text_file", "")))
    parser.add_argument("--model-id", default=str(config.get("qwen_model_id", "")))
    parser.add_argument("--timeout-sec", type=int, default=int(config.get("timeout_sec", 900)))
    parser.add_argument("--postprocess-profile", default=str(config.get("postprocess_profile", "light")))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    intents = args.intent or DEFAULT_INTENTS

    with open(args.manifest, newline="", encoding="utf-8") as fh:
        rows = {row["id"].strip(): row for row in csv.DictReader(fh, delimiter="\t")}

    for segment_id in args.segment_id:
        row = rows.get(segment_id)
        if row is None:
            print(f"missing\t{segment_id}")
            continue
        base_text = row.get("synthesis_text", "").strip() or row["text"].strip()
        style = row.get("style", "").strip() or "grounded"
        seg_out = output_dir / segment_id
        seg_out.mkdir(parents=True, exist_ok=True)

        for intent in intents:
            variant = build_variants(base_text, style, 1, intent=intent)[0]
            take_name = f"intent-{intent}"
            raw_path = seg_out / f"{take_name}-raw.wav"
            clean_path = seg_out / f"{take_name}-clean.wav"
            (seg_out / f"{take_name}.txt").write_text(variant["text"], encoding="utf-8")
            subprocess.run(
                [
                    str(ROOT / "envs" / "qwen3" / "bin" / "python"),
                    str(ROOT / "scripts" / "qwen-run-one-take.py"),
                    "--text",
                    variant["text"],
                    "--model-id",
                    args.model_id,
                    "--reference",
                    args.reference,
                    "--reference-text-file",
                    args.reference_text_file,
                    "--temperature",
                    str(variant["temperature"]),
                    "--timeout-sec",
                    str(args.timeout_sec),
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
