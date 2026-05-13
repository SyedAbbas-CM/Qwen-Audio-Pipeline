# File Map

## Core Script Inputs

- master script:
  - `transcripts/devlog-final.txt`
- short reference text:
  - `transcripts/reference-voice-short.txt`
- short reference audio:
  - `references/karachi-24k-mono-short.wav`

## Core Pipeline Scripts

- parse script:
  - `scripts/parse-transcript.py`
- run one take:
  - `scripts/qwen-run-one-take.py`
- run sequential queue:
  - `scripts/qwen-run-queue.py`
- direct clone call:
  - `scripts/qwen3-clone-say.py`
- cleanup:
  - `scripts/postprocess-voice.sh`
- status:
  - `scripts/qwen-status.py`
- queue watcher:
  - `scripts/qwen-queue-watch.py`
- retry:
  - `scripts/qwen-retry.py`
- roar analysis:
  - `scripts/analyze-roar.py`
- marker stitching:
  - `scripts/stitch-marker-audio.py`
- stitch then clean:
  - `scripts/stitch-and-postprocess.py`

## Current Main Outputs

- chunk render:
  - `outputs/qwen3-reftext-full-v2`
- marker review WAVs:
  - `outputs/qwen3-reftext-full-v2-markers`

## Important Support Files

- config:
  - `config/voice-pipeline.json`
- review zip:
  - `qwen-voice-review-code-only-v3.zip`

## Planned Files

- ASR QC:
  - `reports/qwen-asr-qc.tsv`
- review report:
  - `reports/qwen-review-report.tsv`
- approvals:
  - `transcripts/approved-takes.tsv`
- alignments:
  - `alignments/qwen3-reftext-full-v2/*.words.json`
- final narration:
  - `outputs/final/devlog-final.wav`
