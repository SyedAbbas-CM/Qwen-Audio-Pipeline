from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from huggingface_hub import snapshot_download


MODELS = {
    "kokoro": "hexgrad/Kokoro-82M",
    "chatterbox": "ResembleAI/chatterbox",
    "qwen3": "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
    "qwen3-base": "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
}


def download_with_retry(repo_id: str, retries: int, pause_seconds: int, max_workers: int) -> int:
    for attempt in range(1, retries + 1):
        try:
            path = snapshot_download(repo_id, max_workers=max_workers)
            print(path)
            return 0
        except KeyboardInterrupt:
            raise
        except Exception as exc:  # noqa: BLE001
            print(
                f"[attempt {attempt}/{retries}] download failed for {repo_id}: {exc}",
                file=sys.stderr,
                flush=True,
            )
            if attempt == retries:
                return 1
            time.sleep(pause_seconds * attempt)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("model", choices=sorted(MODELS))
    parser.add_argument("--retries", type=int, default=20)
    parser.add_argument("--pause-seconds", type=int, default=15)
    parser.add_argument("--max-workers", type=int, default=1)
    args = parser.parse_args()

    # Longer HTTP windows reduce repeated read timeouts on large repos.
    os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "120")
    os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", "30")
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

    cache_root = Path.home() / ".cache" / "huggingface"
    cache_root.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HOME", str(cache_root))

    return download_with_retry(
        repo_id=MODELS[args.model],
        retries=args.retries,
        pause_seconds=args.pause_seconds,
        max_workers=args.max_workers,
    )


if __name__ == "__main__":
    raise SystemExit(main())
