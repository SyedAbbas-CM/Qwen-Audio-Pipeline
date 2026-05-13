from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "voice-pipeline.json"


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
    parser.add_argument("--model", default=str(config.get("asr_model", "small.en")))
    parser.add_argument("--cache-dir", default=str(cache_dir_from_config(config)))
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--compute-type", default="int8")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    from faster_whisper import WhisperModel

    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Instantiating the model triggers download if missing.
    WhisperModel(
        args.model,
        device=args.device,
        compute_type=args.compute_type,
        download_root=str(cache_dir),
        local_files_only=False,
    )
    print(cache_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
