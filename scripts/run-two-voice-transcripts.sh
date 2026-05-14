#!/bin/zsh
set -euo pipefail

ROOT="/Users/developer-cloudprimero/ai-audio-lab"
PY="$ROOT/envs/qwen3/bin/python"
QUEUE="$ROOT/scripts/qwen-run-queue.py"
MANIFEST="$ROOT/transcripts/devlog-final-manifest-spoken.tsv"

run_queue() {
  local output_dir="$1"
  local reference="$2"
  local reference_text="$3"

  "$PY" "$QUEUE" \
    --manifest "$MANIFEST" \
    --output-dir "$output_dir" \
    --reference "$reference" \
    --reference-text-file "$reference_text" \
    --temperature 0.35 \
    --postprocess-profile light \
    --skip-existing
}

cd "$ROOT"

run_queue \
  "$ROOT/outputs/qwen3-reftext-spoken-full-v1" \
  "$ROOT/references/karachi-24k-mono-short.wav" \
  "$ROOT/transcripts/reference-voice-short.txt"

run_queue \
  "$ROOT/outputs/qwen3-whatsapp-spoken-full-v1" \
  "$ROOT/references/whatsapp-voice/reference-24k-mono.wav" \
  "$ROOT/transcripts/reference-whatsapp-short.txt"
