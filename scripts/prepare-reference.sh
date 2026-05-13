#!/bin/zsh
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: scripts/prepare-reference.sh <input-audio> <output-wav>"
  exit 1
fi

INPUT="$1"
OUTPUT="$2"

mkdir -p "$(dirname "$OUTPUT")"

ffmpeg -y -i "$INPUT" \
  -ac 1 \
  -ar 24000 \
  -c:a pcm_s16le \
  "$OUTPUT"

echo "$OUTPUT"
