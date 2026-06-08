from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import socket
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "voice-pipeline.json"
DEFAULT_MODEL = Path.home() / ".cache" / "huggingface" / "hub" / "models--Qwen--Qwen3-TTS-12Hz-0.6B-Base" / "snapshots" / "5d83992436eae1d760afd27aff78a71d676296fc"
DEFAULT_REF = ROOT / "references" / "karachi-24k-mono-short.wav"
DEFAULT_REF_TEXT = ROOT / "transcripts" / "reference-voice-short.txt"


def load_config() -> dict[str, object]:
    if not CONFIG_PATH.exists():
        return {}
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def parse_args() -> argparse.Namespace:
    config = load_config()
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True)
    parser.add_argument("--output-raw", required=True)
    parser.add_argument("--output-clean", required=True)
    parser.add_argument("--reference", default=str(config.get("reference", DEFAULT_REF)))
    parser.add_argument("--reference-text-file", default=str(config.get("reference_text_file", DEFAULT_REF_TEXT)))
    parser.add_argument("--model-id", default=str(config.get("qwen_model_id", DEFAULT_MODEL)))
    parser.add_argument("--timeout-sec", type=int, default=int(config.get("timeout_sec", 900)))
    parser.add_argument("--x-vector-only", action="store_true", default=bool(config.get("x_vector_only", False)))
    parser.add_argument("--temperature", type=float, default=float(config.get("temperature", 0.35)))
    parser.add_argument("--skip-postprocess", action="store_true")
    parser.add_argument("--postprocess-profile", default=str(config.get("postprocess_profile", "light")))
    parser.add_argument("--voice-clone-prompt-file", default=str(config.get("voice_clone_prompt_file", "")))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_raw = Path(args.output_raw)
    output_clean = Path(args.output_clean)
    output_raw.parent.mkdir(parents=True, exist_ok=True)
    output_clean.parent.mkdir(parents=True, exist_ok=True)

    status_path = output_clean.with_suffix(".status.json")
    log_path = output_clean.with_suffix(".log.txt")

    cmd = [
        str(ROOT / "envs" / "qwen3" / "bin" / "python"),
        str(ROOT / "scripts" / "qwen3-clone-say.py"),
        args.text,
        "--model-id",
        args.model_id,
        "--reference",
        args.reference,
        "--temperature",
        str(args.temperature),
        "--output-path",
        str(output_raw),
    ]
    if args.voice_clone_prompt_file:
        cmd.extend(["--voice-clone-prompt-file", args.voice_clone_prompt_file])
    if args.x_vector_only:
        cmd.append("--x-vector-only")
    else:
        cmd.extend(
            [
                "--reference-text-file",
                args.reference_text_file,
            ]
        )

    start = time.time()
    status: dict[str, object] = {
        "text_sha256": hashlib.sha256(args.text.encode("utf-8")).hexdigest(),
        "text_chars": len(args.text),
        "output_raw": str(output_raw),
        "output_clean": str(output_clean),
        "reference": args.reference,
        "reference_text_file": args.reference_text_file if not args.x_vector_only else "",
        "model_id": args.model_id,
        "timeout_sec": args.timeout_sec,
        "x_vector_only": args.x_vector_only,
        "temperature": args.temperature,
        "skip_postprocess": args.skip_postprocess,
        "postprocess_profile": args.postprocess_profile,
        "started_at_epoch": start,
        "supervisor_pid": os.getpid(),
        "child_pid": None,
        "hostname": socket.gethostname(),
        "status": "running",
    }
    status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")

    with log_path.open("w", encoding="utf-8") as log_fh:
        proc = subprocess.Popen(
            cmd,
            cwd=ROOT,
            stdout=log_fh,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            text=True,
        )
        status["child_pid"] = proc.pid
        status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
        try:
            return_code = proc.wait(timeout=args.timeout_sec)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            status["status"] = "timeout"
            status["ended_at_epoch"] = time.time()
            status["duration_sec"] = round(time.time() - start, 3)
            status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
            return 124

    status["qwen_return_code"] = return_code
    if return_code != 0:
        status["status"] = "qwen_failed"
        status["ended_at_epoch"] = time.time()
        status["duration_sec"] = round(time.time() - start, 3)
        status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
        return return_code

    if args.skip_postprocess:
        status["postprocess_return_code"] = 0
        status["ended_at_epoch"] = time.time()
        status["duration_sec"] = round(time.time() - start, 3)
        status["status"] = "ready"
        status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
        print(output_raw)
        return 0

    post_cmd = [
        str(ROOT / "scripts" / "postprocess-voice.sh"),
        str(output_raw),
        str(output_clean),
        args.postprocess_profile,
    ]
    post = subprocess.run(
        post_cmd,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    with log_path.open("a", encoding="utf-8") as log_fh:
        log_fh.write("\n\n=== postprocess ===\n")
        log_fh.write(post.stdout)

    status["postprocess_return_code"] = post.returncode
    status["ended_at_epoch"] = time.time()
    status["duration_sec"] = round(time.time() - start, 3)
    status["status"] = "ready" if post.returncode == 0 else "postprocess_failed"
    status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")

    print(output_clean)
    return 0 if post.returncode == 0 else post.returncode


if __name__ == "__main__":
    raise SystemExit(main())
