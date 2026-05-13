from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

WORD_RE = re.compile(r"\b[\w']+\b")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", required=True)
    parser.add_argument("--alignment", required=True)
    parser.add_argument("--instructions", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def db_to_gain(db: float) -> float:
    return 10 ** (db / 20.0)


def normalize_word(word: str) -> str:
    match = WORD_RE.search(word.strip())
    return match.group(0).lower() if match else word.strip().lower()


def stretch_segment(segment: np.ndarray, factor: float) -> np.ndarray:
    if factor <= 0:
        raise ValueError(f"stretch factor must be positive, got {factor}")
    if len(segment) < 2 or abs(factor - 1.0) < 1e-6:
        return segment.copy()
    out_len = max(1, int(round(len(segment) * factor)))
    src_x = np.linspace(0.0, 1.0, num=len(segment), dtype=np.float32)
    dst_x = np.linspace(0.0, 1.0, num=out_len, dtype=np.float32)
    return np.interp(dst_x, src_x, segment).astype(np.float32)


def clamp_region(start: int, end: int, total: int) -> tuple[int, int]:
    start = max(0, min(start, total))
    end = max(start, min(end, total))
    return start, end


def atempo_chain(speed_factor: float) -> str:
    # ffmpeg atempo preserves pitch, but each stage must be within [0.5, 2.0]
    if speed_factor <= 0:
        raise ValueError(f"speed factor must be positive, got {speed_factor}")
    stages: list[float] = []
    remaining = speed_factor
    while remaining > 2.0:
        stages.append(2.0)
        remaining /= 2.0
    while remaining < 0.5:
        stages.append(0.5)
        remaining /= 0.5
    stages.append(remaining)
    return ",".join(f"atempo={stage:.6f}" for stage in stages)


def main() -> int:
    args = parse_args()
    audio_path = Path(args.audio)
    alignment_path = Path(args.alignment)
    instructions_path = Path(args.instructions)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    audio, sr = sf.read(audio_path)
    if audio.ndim > 1:
        audio = audio[:, 0]
    audio = audio.astype(np.float32, copy=False)

    alignment = json.loads(alignment_path.read_text(encoding="utf-8"))
    instructions = json.loads(instructions_path.read_text(encoding="utf-8"))
    words = alignment.get("words", [])

    gain_map = {normalize_word(k): float(v) for k, v in instructions.get("gain_db", {}).items()}
    pause_map = {normalize_word(k): float(v) for k, v in instructions.get("pause_after", {}).items()}
    stretch_map = {normalize_word(k): float(v) for k, v in instructions.get("stretch", {}).items()}
    speed_factor = float(instructions.get("speed", 1.0))

    chunks: list[np.ndarray] = []
    cursor = 0
    total = len(audio)

    for entry in words:
        word = normalize_word(entry["word"])
        start = int(float(entry["start"]) * sr)
        end = int(float(entry["end"]) * sr)
        start, end = clamp_region(start, end, total)
        if start < cursor:
            start = cursor
        if start > cursor:
            chunks.append(audio[cursor:start])

        segment = audio[start:end].copy()
        if word in stretch_map:
            segment = stretch_segment(segment, float(stretch_map[word]))
        if word in gain_map:
            segment *= db_to_gain(float(gain_map[word]))
        chunks.append(segment)

        if word in pause_map:
            pause_ms = float(pause_map[word])
            pause = np.zeros(int(sr * pause_ms / 1000.0), dtype=np.float32)
            chunks.append(pause)

        cursor = end

    if cursor < total:
        chunks.append(audio[cursor:])

    if chunks:
        out_audio = np.concatenate(chunks)
    else:
        out_audio = audio.copy()

    out_audio = np.clip(out_audio, -1.0, 1.0)
    if abs(speed_factor - 1.0) > 1e-6:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fh:
            temp_path = Path(fh.name)
        try:
            sf.write(temp_path, out_audio, sr)
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(temp_path),
                    "-filter:a",
                    atempo_chain(speed_factor),
                    "-ar",
                    str(sr),
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
        finally:
            temp_path.unlink(missing_ok=True)
    else:
        sf.write(output_path, out_audio, sr)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
