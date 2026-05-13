#!/bin/zsh
set -euo pipefail

LAB_ROOT="${0:A:h:h}"
OUT_DIR="$LAB_ROOT/outputs/openmoss-sfx"
mkdir -p "$OUT_DIR"

mlx_audio.tts.generate \
  --model appautomaton/openmoss-sound-effect-mlx \
  --text "Soft thunder rolling over distant rain." \
  --output "$OUT_DIR/smoke.wav"

echo "$OUT_DIR/smoke.wav"
