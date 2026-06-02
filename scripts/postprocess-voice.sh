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
  stitch_safe)
    FILTERS="silenceremove=start_periods=1:start_silence=0.03:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_silence=0.08:start_threshold=-56dB,areverse,highpass=f=70,lowpass=f=9200"
    ;;
  stitch_tight)
    FILTERS="silenceremove=start_periods=1:start_silence=0.02:start_threshold=-44dB,areverse,silenceremove=start_periods=1:start_silence=0.06:start_threshold=-42dB,areverse,highpass=f=70,lowpass=f=9200"
    ;;
  light)
    FILTERS="silenceremove=start_periods=1:start_silence=0.05:start_threshold=-44dB,areverse,silenceremove=start_periods=1:start_silence=0.12:start_threshold=-52dB,areverse,highpass=f=80,lowpass=f=9000,afftdn=nr=10:nf=-38:tn=1:rf=-42:gs=6,equalizer=f=3200:t=q:w=1.1:g=0.8,alimiter=limit=0.85,volume=1.8"
    ;;
  marker_master)
    FILTERS="highpass=f=70,lowpass=f=9200,equalizer=f=3000:t=q:w=1.0:g=0.5,acompressor=threshold=0.16:ratio=1.8:attack=6:release=110:makeup=1,alimiter=limit=0.93"
    ;;
  marker_denoise)
    FILTERS="highpass=f=70,lowpass=f=9200,afftdn=nr=8:nf=-34:tn=1:rf=-38:gs=4,equalizer=f=3000:t=q:w=1.0:g=0.4,acompressor=threshold=0.18:ratio=1.6:attack=8:release=120:makeup=1,alimiter=limit=0.94"
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
