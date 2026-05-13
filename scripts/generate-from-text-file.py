from __future__ import annotations

import argparse
import hashlib
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "transcripts" / "experimental-voice-input.txt"
DEFAULT_REFERENCE = ROOT / "references" / "whatsapp-voice" / "reference-24k-mono.wav"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "qwen3-experimental"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-file", default=str(DEFAULT_INPUT))
    parser.add_argument("--reference", default=str(DEFAULT_REFERENCE))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--output-name", default="friend-voice")
    parser.add_argument("--temperature", type=float, default=0.35)
    parser.add_argument("--timeout-sec", type=int, default=900)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input_file)
    text = input_path.read_text(encoding="utf-8").strip()
    if not text:
        raise SystemExit("input file is empty")

    out_dir = Path(args.output_dir) / args.output_name
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "input.meta.json").write_text(
        (
            "{\n"
            f'  "source_file": "{input_path}",\n'
            f'  "text_chars": {len(text)},\n'
            f'  "text_sha256": "{hashlib.sha256(text.encode("utf-8")).hexdigest()}"\n'
            "}\n"
        ),
        encoding="utf-8",
    )

    cmd = [
        str(ROOT / "envs" / "qwen3" / "bin" / "python"),
        str(ROOT / "scripts" / "qwen-run-one-take.py"),
        "--text",
        text,
        "--reference",
        args.reference,
        "--x-vector-only",
        "--temperature",
        str(args.temperature),
        "--timeout-sec",
        str(args.timeout_sec),
        "--output-raw",
        str(out_dir / "raw.wav"),
        "--output-clean",
        str(out_dir / "clean.wav"),
    ]
    subprocess.run(cmd, cwd=ROOT, check=True)
    print(out_dir / "clean.wav")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
