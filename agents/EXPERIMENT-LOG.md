# Experiment Log

## What Failed

### Fish Speech on this Mac

- too heavy for the hardware target
- not the right local fit for the workflow

### Qwen `x_vector_only` as main transcript path

- more stable than stronger clone mode
- but identity drifted
- accent drift happened
- "Nordic" effect showed up on rewritten lines

### Long one-pass chunks

- often timed out
- prosody became unstable
- long lines caused pace drift or breath-like breakdown

### Tiny stitched chunks

- obvious seams
- voice identity shifted between chunks
- pauses felt artificial

### Early cleanup chains

- some versions boosted the noise floor
- some versions produced tail roar
- some versions caused noise pumping
- some versions created "whooo" artifacts

### Naive resample-based speed edits

- tightened timing, but sometimes shifted perceived pitch/timbre
- created moments where the voice felt slightly less like the source speaker
- should be replaced with pitch-preserving tempo changes when possible

## What Succeeded

### Proper clone mode with short reference

- `ref_audio + ref_text` using:
  - `karachi-24k-mono-short.wav`
  - `reference-voice-short.txt`
- better identity than `x_vector_only`
- more stable than the earlier long full-reference path

### Short sequential chunks

- this is the best current generation pattern on the Mac
- avoids giant row timeouts

### Queue + status + logs

- `qwen-run-one-take.py`
- `qwen-run-queue.py`
- `qwen-status.py`
- `qwen-queue-watch.py`

These made the pipeline observable and resumable.

### Marker-level merging

- `stitch-marker-audio.py`
- `outputs/qwen3-reftext-full-v2-markers`

This made the transcript reviewable in human terms instead of tiny per-chunk fragments.

### Production control layer

- `qwen-review-report.py`
- `approve-take.py`
- `approve-from-report.py`
- `stitch-approved-final.py`
- `add-roomtone-bed.py`

These moved the project from raw generation toward asset lifecycle management.

### V2 control hardening

- `config/voice-pipeline.json` now matches the actual working clone path
- queue/runner scripts now read config defaults
- `baseline_approved` is separated from real `approved`
- status JSON now includes PIDs and hostname
- `qwen-status.py` can distinguish active vs stale running jobs
- ASR download/setup path exists via `download-asr-models.py`
- `qwen-asr-qc.py` now reports `model_missing` cleanly and includes WER
- cached `small.en` faster-whisper now runs locally and produced the first real QC TSV

These changes reduce silent regressions back to the bad clone path and make the queue safer to resume.

### Heuristic alignment + prosody edit

- `qwen-align.py`
- `qwen-prosody-edit.py`

This is not true forced alignment yet, but it is enough to start practical post-generation direction tests on individual chunks.

## Current Noise Conclusion

- some noise is model-side
- FFmpeg helps, but cannot fully erase it without tradeoffs
- better strategy is:
  - lighter denoise
  - stable low noise floor
  - room tone bed later

## Current Identity Conclusion

- `ref_text` mode is the right direction
- but script wording and chunking still strongly affect perceived identity

## External Review Takeaway

- do not destabilize the baseline by piling on advanced modules too early
- build around:
  - QC
  - review
  - approvals
  - room tone
  - final stitching
- treat RVC, DeepFilterNet, AudioSR, and distributed orchestration as later experiments, not current baseline requirements
