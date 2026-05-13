# AI Audio Lab

Local audio workspace for Apple Silicon with isolated environments for:

- `kokoro`
- `chatterbox`
- `qwen3-tts`
- `openmoss-sfx`

## Layout

- `apps/` local source checkouts when needed
- `envs/` per-tool virtual environments
- `models/` downloaded model weights and caches
- `references/` voice reference clips
- `outputs/` generated audio
- `logs/` run logs
- `scripts/` helper commands
- `tmp/` scratch files

## Notes

- Python envs are managed with `uv`.
- Model caches are redirected into `models/` where possible.
- `openmoss-sfx` uses `mlx-audio` on Apple Silicon to run the MLX SoundEffect model.
- `qwen3-tts` is set up for `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice`.
- `openmoss-sfx` could not be smoke-tested inside this sandbox because Metal devices are not exposed here; it should be run from your local terminal session on the Mac itself.

## Quick Start

Check env status:

```bash
./scripts/audio-status
```

Activate one env:

```bash
source ./scripts/audio-env kokoro
source ./scripts/audio-env chatterbox
source ./scripts/audio-env qwen3
source ./scripts/audio-env openmoss-sfx
```

Run smoke scripts:

```bash
envs/kokoro/bin/python scripts/kokoro-smoke.py
envs/chatterbox/bin/python scripts/chatterbox-smoke.py
envs/qwen3/bin/python scripts/qwen3-smoke.py
./scripts/openmoss-sfx-smoke.sh
```

Generate a cloned line with style presets:

```bash
envs/chatterbox/bin/python scripts/chatterbox-say.py \
  "This is a laid back test line." \
  --preset laidback \
  --output-name laidback.wav

envs/chatterbox/bin/python scripts/chatterbox-say.py \
  "This line should feel more energetic and punchy." \
  --preset energetic \
  --output-name energetic.wav
```

Post-process a voice line:

```bash
./scripts/style-voice.sh outputs/chatterbox/energetic.wav outputs/chatterbox/energetic-deep.wav deep-warm
```

Render a full transcript line by line:

```bash
envs/chatterbox/bin/python scripts/render-transcript.py --skip-existing
```

Render only one segment again:

```bash
envs/chatterbox/bin/python scripts/render-transcript.py --only-id marker-17-balancing
```

Review rendered segments:

```bash
envs/chatterbox/bin/python scripts/review-segments.py
```

Render performance-style micro-lines:

```bash
envs/chatterbox/bin/python scripts/render-transcript.py \
  --segments transcripts/devlog-perf-segments.tsv \
  --only-id hook-01 --only-id hook-02 --only-id hook-03
```

Generate a Qwen3 cloned line:

```bash
envs/qwen3/bin/python scripts/qwen3-clone-say.py \
  "This is my game. Just me, my ideas, and a pile of tools." \
  --output-path outputs/qwen3/hook.wav \
  --x-vector-only
```

Parse the editable transcript into a render manifest:

```bash
envs/qwen3/bin/python scripts/parse-transcript.py
```

Create explicit take jobs:

```bash
envs/qwen3/bin/python scripts/create-qwen-takes.py
```

Render multi-take Qwen clones from the manifest:

```bash
envs/qwen3/bin/python scripts/render-qwen-manifest.py --use-takes-file --limit 3
```

Review Qwen takes:

```bash
envs/qwen3/bin/python scripts/review-qwen-takes.py
```

Scan Qwen job statuses:

```bash
envs/qwen3/bin/python scripts/qwen-status.py
```

Retry failed Qwen jobs:

```bash
envs/qwen3/bin/python scripts/qwen-retry.py --limit 2
```
