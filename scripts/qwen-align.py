from __future__ import annotations

import argparse
import csv
import json
import math
import re
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "transcripts" / "devlog-final-manifest-reftext.tsv"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "qwen3-reftext-full-v2"
DEFAULT_ALIGNMENTS = ROOT / "alignments" / "qwen3-reftext-full-v2"
DEFAULT_CONFIG = ROOT / "config" / "voice-pipeline.json"

WORD_RE = re.compile(r"\b[\w']+\b")
CLAUSE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|(?<=\.\.\.)\s+|(?<=,)\s+")


def duration_seconds(path: Path) -> float:
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=True,
    )
    return float(proc.stdout.strip())


def words_for_text(text: str) -> list[str]:
    return WORD_RE.findall(text)


def clause_texts(text: str) -> list[str]:
    clauses = [part.strip() for part in CLAUSE_SPLIT_RE.split(text) if part.strip()]
    return clauses or [text.strip()]


def rms_frames(audio: np.ndarray, frame_size: int, hop: int) -> np.ndarray:
    if len(audio) < frame_size:
        padded = np.pad(audio, (0, max(0, frame_size - len(audio))))
        return np.array([np.sqrt(np.mean(padded * padded) + 1e-12)], dtype=np.float32)
    frames = []
    for start in range(0, len(audio) - frame_size + 1, hop):
        frame = audio[start : start + frame_size]
        frames.append(math.sqrt(float(np.mean(frame * frame) + 1e-12)))
    return np.array(frames, dtype=np.float32)


def detect_speech_regions(audio: np.ndarray, sr: int) -> list[tuple[float, float]]:
    frame_ms = 20
    hop_ms = 10
    frame_size = max(1, int(sr * frame_ms / 1000))
    hop = max(1, int(sr * hop_ms / 1000))
    rms = rms_frames(audio, frame_size, hop)
    if len(rms) == 0:
        return [(0.0, len(audio) / sr)]

    peak = float(np.max(rms))
    floor = float(np.percentile(rms, 20))
    threshold = max(floor * 1.8, peak * 0.08, 5e-4)
    voiced = rms >= threshold

    regions: list[tuple[int, int]] = []
    start = None
    for idx, is_voiced in enumerate(voiced):
        if is_voiced and start is None:
            start = idx
        elif not is_voiced and start is not None:
            regions.append((start, idx))
            start = None
    if start is not None:
        regions.append((start, len(voiced)))

    # Merge tiny gaps and discard tiny regions.
    min_region_frames = max(1, int(120 / hop_ms))
    merged: list[tuple[int, int]] = []
    for region in regions:
        if region[1] - region[0] < min_region_frames:
            continue
        if merged and region[0] - merged[-1][1] <= int(120 / hop_ms):
            merged[-1] = (merged[-1][0], region[1])
        else:
            merged.append(region)

    if not merged:
        return [(0.0, len(audio) / sr)]

    speech_regions: list[tuple[float, float]] = []
    total_dur = len(audio) / sr
    for start_f, end_f in merged:
        start_t = max(0.0, start_f * hop / sr)
        end_t = min(total_dur, end_f * hop / sr + frame_size / sr)
        speech_regions.append((round(start_t, 3), round(end_t, 3)))
    return speech_regions


def allocate_regions_to_clauses(
    clauses: list[str], speech_regions: list[tuple[float, float]], total_duration: float
) -> list[tuple[str, float, float]]:
    if not clauses:
        return []
    if not speech_regions:
        return [(clause, 0.0, total_duration / max(1, len(clauses))) for clause in clauses]

    clause_weights = [max(1, len(words_for_text(clause))) for clause in clauses]
    total_weight = sum(clause_weights)

    # If we have fewer speech regions than clauses, merge them into a single speech span and allocate proportionally.
    if len(speech_regions) < len(clauses):
        start = speech_regions[0][0]
        end = speech_regions[-1][1]
        span = max(0.001, end - start)
        out = []
        cursor = start
        for clause, weight in zip(clauses, clause_weights):
            frac = weight / total_weight
            clause_end = end if clause is clauses[-1] else cursor + span * frac
            out.append((clause, round(cursor, 3), round(clause_end, 3)))
            cursor = clause_end
        return out

    # If we have at least as many speech regions as clauses, group adjacent speech regions per clause.
    out: list[tuple[str, float, float]] = []
    region_cursor = 0
    remaining_regions = len(speech_regions)
    remaining_clauses = len(clauses)
    for idx, clause in enumerate(clauses):
        remaining_regions = len(speech_regions) - region_cursor
        remaining_clauses = len(clauses) - idx
        take = max(1, round(remaining_regions / remaining_clauses))
        if idx == len(clauses) - 1:
            take = remaining_regions
        group = speech_regions[region_cursor : region_cursor + take]
        region_cursor += take
        out.append((clause, group[0][0], group[-1][1]))
    return out


def align_words_in_clause(clause: str, start: float, end: float) -> list[dict[str, float | str | None]]:
    words = words_for_text(clause)
    if not words:
        return []
    duration = max(0.001, end - start)
    word_weights = [max(1, len(word)) for word in words]
    total_weight = sum(word_weights)
    cursor = start
    payload = []
    for idx, (word, weight) in enumerate(zip(words, word_weights)):
        frac = weight / total_weight
        word_end = end if idx == len(words) - 1 else cursor + duration * frac
        payload.append(
            {
                "word": word,
                "start": round(cursor, 3),
                "end": round(word_end, 3),
                "confidence": None,
            }
        )
        cursor = word_end
    return payload


def align_text_to_audio(audio_path: Path, text: str) -> dict:
    audio, sr = sf.read(audio_path)
    if audio.ndim > 1:
        audio = audio[:, 0]
    audio = audio.astype(np.float32, copy=False)
    total_duration = len(audio) / sr
    clauses = clause_texts(text)
    speech_regions = detect_speech_regions(audio, sr)
    clause_regions = allocate_regions_to_clauses(clauses, speech_regions, total_duration)

    words_payload = []
    for clause, start, end in clause_regions:
        words_payload.extend(align_words_in_clause(clause, start, end))

    return {
        "text": text,
        "audio_path": str(audio_path),
        "alignment_mode": "silence_aware_heuristic",
        "speech_regions": [{"start": s, "end": e} for s, e in speech_regions],
        "words": words_payload,
    }


def load_config() -> dict:
    if not DEFAULT_CONFIG.exists():
        return {}
    return json.loads(DEFAULT_CONFIG.read_text(encoding="utf-8"))


def normalize_whisper_word(word: str) -> str:
    cleaned = word.strip()
    match = WORD_RE.search(cleaned)
    return match.group(0) if match else cleaned


def align_with_whisper_words(
    audio_path: Path,
    text: str,
    model_name: str,
    cache_dir: Path,
    device: str,
    compute_type: str,
) -> dict:
    from faster_whisper import WhisperModel

    model = WhisperModel(
        model_name,
        device=device,
        compute_type=compute_type,
        download_root=str(cache_dir),
        local_files_only=True,
    )
    segments, _info = model.transcribe(
        str(audio_path),
        language="en",
        word_timestamps=True,
        vad_filter=False,
    )

    words_payload: list[dict[str, float | str | None]] = []
    speech_regions: list[dict[str, float]] = []
    for seg in segments:
        seg_start = round(float(seg.start), 3)
        seg_end = round(float(seg.end), 3)
        speech_regions.append({"start": seg_start, "end": seg_end})
        for word in getattr(seg, "words", None) or []:
            normalized = normalize_whisper_word(getattr(word, "word", ""))
            if not normalized:
                continue
            prob = getattr(word, "probability", None)
            words_payload.append(
                {
                    "word": normalized,
                    "start": round(float(word.start), 3),
                    "end": round(float(word.end), 3),
                    "confidence": None if prob is None else round(float(prob), 3),
                }
            )

    return {
        "text": text,
        "audio_path": str(audio_path),
        "alignment_mode": "whisper_words",
        "speech_regions": speech_regions,
        "words": words_payload,
    }


def align_with_qwen_forced_aligner(audio_path: Path, text: str, aligner: object) -> dict:
    result = aligner.align(audio=str(audio_path), text=text, language="English")
    align_result = result[0] if isinstance(result, list) else result
    words_payload = [
        {
            "word": str(item.text),
            "start": round(float(item.start_time), 3),
            "end": round(float(item.end_time), 3),
            "confidence": None,
        }
        for item in align_result.items
    ]
    speech_regions = []
    if words_payload:
        speech_regions.append({"start": words_payload[0]["start"], "end": words_payload[-1]["end"]})
    return {
        "text": text,
        "audio_path": str(audio_path),
        "alignment_mode": "qwen_forced_aligner",
        "speech_regions": speech_regions,
        "words": words_payload,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--output-alignments", default=str(DEFAULT_ALIGNMENTS))
    parser.add_argument(
        "--aligner",
        choices=["heuristic", "whisper_words", "qwen_forced_aligner"],
        default="heuristic",
    )
    parser.add_argument("--model", default="")
    parser.add_argument("--cache-dir", default="")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--compute-type", default="int8")
    parser.add_argument("--qwen-forced-aligner-model", default="")
    args = parser.parse_args()

    config = load_config()
    manifest_path = Path(args.manifest)
    output_dir = Path(args.output_dir)
    align_dir = Path(args.output_alignments)
    align_dir.mkdir(parents=True, exist_ok=True)
    model_name = args.model or str(config.get("asr_model", "small.en"))
    cache_dir = Path(args.cache_dir or str(config.get("asr_cache_dir", ".cache/faster-whisper")))
    qwen_forced_aligner_model = args.qwen_forced_aligner_model or str(
        config.get("qwen_forced_aligner_model", "Qwen/Qwen3-ForcedAligner-0.6B")
    )
    if not cache_dir.is_absolute():
        cache_dir = ROOT / cache_dir
    qwen_forced_aligner = None
    if args.aligner == "qwen_forced_aligner":
        import torch
        from qwen_asr.inference.qwen3_forced_aligner import Qwen3ForcedAligner

        qwen_forced_aligner = Qwen3ForcedAligner.from_pretrained(
            qwen_forced_aligner_model,
            device_map="cpu",
            torch_dtype=torch.float32,
        )

    with manifest_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            segment_id = row["id"].strip()
            text = row["text"].strip()
            audio_path = output_dir / segment_id / "take-01-clean.wav"
            out_path = align_dir / f"{segment_id}.words.json"
            if not audio_path.exists():
                continue
            if args.aligner == "whisper_words":
                try:
                    payload = align_with_whisper_words(
                        audio_path,
                        text,
                        model_name,
                        cache_dir,
                        args.device,
                        args.compute_type,
                    )
                except Exception as exc:
                    payload = align_text_to_audio(audio_path, text)
                    payload["alignment_error"] = f"whisper_words_failed:{exc}"
            elif args.aligner == "qwen_forced_aligner":
                try:
                    payload = align_with_qwen_forced_aligner(audio_path, text, qwen_forced_aligner)
                except Exception as exc:
                    payload = align_text_to_audio(audio_path, text)
                    payload["alignment_error"] = f"qwen_forced_aligner_failed:{exc}"
            else:
                payload = align_text_to_audio(audio_path, text)
            payload["segment_id"] = segment_id
            out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
