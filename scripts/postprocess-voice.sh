#!/bin/zsh
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: scripts/postprocess-voice.sh <input.wav> <output.wav> [profile]"
  exit 1
fi

INPUT="$1"
OUTPUT="$2"
PROFILE="${3:-light}"

case "$PROFILE" in
  light)
    FILTERS="silenceremove=start_periods=1:start_silence=0.05:start_threshold=-44dB,areverse,silenceremove=start_periods=1:start_silence=0.12:start_threshold=-52dB,areverse,highpass=f=80,lowpass=f=9000,afftdn=nr=10:nf=-38:tn=1:rf=-42:gs=6,equalizer=f=3200:t=q:w=1.1:g=0.8,alimiter=limit=0.85,volume=1.8"
    ;;
  tail_rescue)
    FILTERS="silenceremove=start_periods=1:start_silence=0.06:start_threshold=-42dB,areverse,silenceremove=start_periods=1:start_silence=0.18:start_threshold=-54dB,areverse,highpass=f=80,lowpass=f=9000,afftdn=nr=12:nf=-40:tn=1:rf=-45:gs=8,agate=threshold=0.010:ratio=3.5:attack=12:release=160:makeup=1,equalizer=f=3200:t=q:w=1.1:g=1.0,alimiter=limit=0.82,volume=1.7"
    ;;
  *)
    echo "unknown profile: $PROFILE" >&2
    exit 2
    ;;
esac

ffmpeg -y -i "$INPUT" \
  -af "$FILTERS" \
  -ar 24000 -ac 1 -c:a pcm_s16le \
  "$OUTPUT"
