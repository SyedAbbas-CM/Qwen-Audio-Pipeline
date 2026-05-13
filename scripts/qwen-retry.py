from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TAKES = ROOT / "transcripts" / "devlog-final-takes.tsv"
DEFAULT_OUT = ROOT / "outputs" / "qwen3-devlog"
DEFAULT_CONFIG = ROOT / "config" / "voice-pipeline.json"


def load_config() -> dict:
    return json.loads(Path(DEFAULT_CONFIG).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--takes-file", default=str(DEFAULT_TAKES))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUT))
    parser.add_argument("--status", action="append", default=["timeout", "qwen_failed", "postprocess_failed"])
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    config = load_config()
    wanted = set(args.status)
    retried = 0

    with open(args.takes_file, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            seg_id = row["segment_id"].strip()
            take = row["take"].strip()
            seg_dir = Path(args.output_dir) / seg_id
            clean_path = seg_dir / f"take-{take}-clean.wav"
            raw_path = seg_dir / f"take-{take}-raw.wav"
            status_path = seg_dir / f"take-{take}-clean.status.json"
            if not status_path.exists():
                continue
            status = json.loads(status_path.read_text(encoding="utf-8")).get("status")
            if status not in wanted:
                continue
            if args.limit and retried >= args.limit:
                break
            retried += 1
            subprocess.run(
                [
                    str(ROOT / "envs" / "qwen3" / "bin" / "python"),
                    str(ROOT / "scripts" / "qwen-run-one-take.py"),
                    "--text",
                    row["text"].strip(),
                    "--model-id",
                    config["qwen_model_id"],
                    "--reference",
                    config["reference"],
                    "--reference-text-file",
                    config["reference_text_file"],
                    "--timeout-sec",
                    str(config["timeout_sec"]),
                    "--output-raw",
                    str(raw_path),
                    "--output-clean",
                    str(clean_path),
                ],
                cwd=ROOT,
                check=False,
            )
            print(status_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
