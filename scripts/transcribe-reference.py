from __future__ import annotations

import argparse
from pathlib import Path

from faster_whisper import WhisperModel


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--model", default="small")
    parser.add_argument("--language", default="en")
    parser.add_argument("--output", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path.with_suffix(".txt")

    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    segments, info = model.transcribe(str(input_path), language=args.language, vad_filter=True)
    text = " ".join(segment.text.strip() for segment in segments).strip()
    output_path.write_text(text + "\n", encoding="utf-8")
    print(output_path)
    print(f"language={info.language} prob={info.language_probability:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
