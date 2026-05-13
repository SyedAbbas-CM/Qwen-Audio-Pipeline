from __future__ import annotations

import argparse
import csv
import difflib
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "voice-pipeline.json"
DEFAULT_MANIFEST = ROOT / "transcripts" / "devlog-final-manifest-reftext.tsv"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "qwen3-reftext-full-v2"
DEFAULT_OUTPUT = ROOT / "reports" / "qwen-asr-qc.tsv"


def load_config() -> dict[str, object]:
    if not CONFIG_PATH.exists():
        return {}
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def cache_dir_from_config(config: dict[str, object]) -> Path:
    raw = str(config.get("asr_cache_dir", ".cache/faster-whisper"))
    path = Path(raw)
    return path if path.is_absolute() else ROOT / path


def parse_args() -> argparse.Namespace:
    config = load_config()
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--model", default=str(config.get("asr_model", "small.en")))
    parser.add_argument("--model-path", default="")
    parser.add_argument("--cache-dir", default=str(cache_dir_from_config(config)))
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--compute-type", default="int8")
    parser.add_argument("--language", default="en")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--drop-fillers", action="store_true")
    return parser.parse_args()


def normalize_text(text: str, drop_fillers: bool = False) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s']", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if drop_fillers:
        text = re.sub(r"\b(uh|um|ah|er)\b", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
    return text


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


def classify_similarity(score: float) -> str:
    if score >= 0.92:
        return "pass"
    if score >= 0.80:
        return "warn"
    return "fail"


def word_error_rate(reference: str, hypothesis: str) -> float:
    ref_words = reference.split()
    hyp_words = hypothesis.split()
    if not ref_words:
        return 0.0 if not hyp_words else 1.0

    rows = len(ref_words) + 1
    cols = len(hyp_words) + 1
    dp = [[0] * cols for _ in range(rows)]
    for i in range(rows):
        dp[i][0] = i
    for j in range(cols):
        dp[0][j] = j

    for i in range(1, rows):
        for j in range(1, cols):
            cost = 0 if ref_words[i - 1] == hyp_words[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + cost,
            )
    return dp[-1][-1] / len(ref_words)


def transcribe_with_faster_whisper(
    audio_path: Path,
    model_name: str,
    model_path: str,
    cache_dir: Path,
    language: str,
    device: str,
    compute_type: str,
) -> tuple[str, str]:
    try:
        from faster_whisper import WhisperModel
    except Exception as exc:
        return "", f"backend_unavailable:{exc.__class__.__name__}"

    model_spec = model_path or model_name
    try:
        model = WhisperModel(
            model_spec,
            device=device,
            compute_type=compute_type,
            download_root=str(cache_dir),
            local_files_only=True,
        )
        segments, _info = model.transcribe(str(audio_path), language=language, vad_filter=True)
        text = " ".join(segment.text.strip() for segment in segments).strip()
        return text, "ok"
    except Exception as exc:
        if exc.__class__.__name__ == "LocalEntryNotFoundError":
            return "", "model_missing"
        return "", f"asr_error:{exc.__class__.__name__}"


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest)
    output_dir = Path(args.output_dir)
    output_path = Path(args.output)
    cache_dir = Path(args.cache_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    with manifest_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            segment_id = row["id"].strip()
            marker = row["marker"].strip()
            intended_text = row["text"].strip()
            audio_path = output_dir / segment_id / "take-01-clean.wav"
            if not audio_path.exists():
                rows.append(
                    {
                        "segment_id": segment_id,
                        "marker": marker,
                        "intended_text": intended_text,
                        "asr_text": "",
                        "similarity": "",
                        "wer": "",
                        "duration_sec": "",
                        "status": "missing",
                        "audio_path": str(audio_path),
                        "qc_result": "missing",
                        "backend_status": "missing_audio",
                        "note": "",
                    }
                )
                continue

            asr_text, backend_status = transcribe_with_faster_whisper(
                audio_path,
                args.model,
                args.model_path,
                cache_dir,
                args.language,
                args.device,
                args.compute_type,
            )
            intended_norm = normalize_text(intended_text, args.drop_fillers)
            asr_norm = normalize_text(asr_text, args.drop_fillers)
            similarity = difflib.SequenceMatcher(None, intended_norm, asr_norm).ratio() if asr_norm else 0.0
            wer = word_error_rate(intended_norm, asr_norm) if asr_norm else 1.0
            qc_result = classify_similarity(similarity) if backend_status == "ok" else "unavailable"
            note = ""
            if backend_status == "model_missing":
                note = (
                    "Run: envs/qwen3/bin/python scripts/download-asr-models.py "
                    f"--model {args.model}"
                )
            rows.append(
                {
                    "segment_id": segment_id,
                    "marker": marker,
                    "intended_text": intended_text,
                    "asr_text": asr_text,
                    "similarity": f"{similarity:.4f}" if asr_norm else "",
                    "wer": f"{wer:.4f}" if asr_norm else "",
                    "duration_sec": f"{duration_seconds(audio_path):.3f}",
                    "status": "ready",
                    "audio_path": str(audio_path),
                    "qc_result": qc_result,
                    "backend_status": backend_status,
                    "note": note,
                }
            )

    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "segment_id",
                "marker",
                "intended_text",
                "asr_text",
                "similarity",
                "wer",
                "duration_sec",
                "status",
                "audio_path",
                "qc_result",
                "backend_status",
                "note",
            ],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
