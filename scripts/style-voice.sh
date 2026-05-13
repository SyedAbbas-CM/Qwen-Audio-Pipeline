#!/bin/zsh
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: scripts/style-voice.sh <input.wav> <output.wav> [profile]"
  echo "profiles: subtle-deep, deep-warm, deep-slow, crisp-ad"
  exit 1
fi

INPUT="$1"
OUTPUT="$2"
PROFILE="${3:-subtle-deep}"

case "$PROFILE" in
  subtle-deep)
    sox "$INPUT" "$OUTPUT" pitch -120
    ;;
  deep-warm)
    sox "$INPUT" "$OUTPUT" pitch -150 bass 4 treble -1
    ;;
  deep-slow)
    sox "$INPUT" "$OUTPUT" pitch -150 tempo 0.95
    ;;
  crisp-ad)
    sox "$INPUT" "$OUTPUT" bass 2 treble 2 tempo 1.02 gain -1
    ;;
  *)
    echo "unknown profile: $PROFILE"
    exit 1
    ;;
esac
