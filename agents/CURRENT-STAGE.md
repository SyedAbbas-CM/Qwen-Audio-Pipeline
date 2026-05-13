# Current Stage

## Pipeline Stage

We are in the transition from "working generation pipeline" to "basic production pipeline".

Done:
- transcript parsing
- sequential Qwen generation
- status/log tracking
- marker-level stitching
- marker-level room tone bed pass
- short `ref_audio + ref_text` path
- full chunk render for the devlog
- marker-level merged review WAVs
- review report generation
- approval baseline file
- silence-aware heuristic word alignment
- basic word-level prosody editing prototype
- final full narration stitch for comparison
- final approved-baseline narration stitch
- offline ASR download/setup path
- real offline ASR QC pass on the current transcript
- review report with WER/backend status columns
- config-backed queue/runner defaults
- baseline approval semantics split from real approval
- editable review sheet generation
- real `whisper_words` alignment backend using cached `faster-whisper`

Not done:
- meaningful human approval decisions across the transcript
- higher-quality aligner backend like WhisperX/MFA
- higher-quality per-word time/pitch editing

## Current Best Path

Use:
- short reference audio
  - `references/karachi-24k-mono-short.wav`
- short reference text
  - `transcripts/reference-voice-short.txt`
- proper clone mode
  - `ref_audio + ref_text`
- sequential queue
  - `scripts/qwen-run-queue.py`

Avoid as default:
- `x_vector_only`
- long monologue chunks
- heavy rewrite before voice identity is stable
- aggressive silence chasing

## Current Output Folders

- chunked transcript outputs:
  - `outputs/qwen3-reftext-full-v2`
- marker-level merged review WAVs:
  - `outputs/qwen3-reftext-full-v2-markers`
- marker-level roomtone review WAVs:
  - `outputs/qwen3-reftext-full-v2-markers-roomtone`
- stitched full narration for comparison:
  - `outputs/final/devlog-final-unapproved.wav`
- approved-baseline narration:
  - `outputs/final/devlog-final-approved-baseline.wav`
- word alignments:
  - `alignments/qwen3-reftext-full-v2`
- first prosody-edit outputs:
  - `outputs/prosody`
- approvals:
  - `transcripts/approved-takes.tsv`
- ASR QC:
  - `reports/qwen-asr-qc.tsv`
- review report:
  - `reports/qwen-review-report.tsv`

## Current Problems

- low-level generated noise still exists
- denoise can reduce noise, but overdoing it causes pumping or artifacts
- chunk seams can be obvious if chunking is too aggressive
- some script wording is still too pause-heavy
- ASR QC is now working locally with cached `faster-whisper`
- current alignment now supports `whisper_words` from `faster-whisper`, with the heuristic mode kept as fallback

## Current QC Shortlist

Flagged by the first real ASR pass:

- `marker-4-intro-c04`
  - `needs_retry`
  - failed ASR similarity
- `marker-14-lighting-c01`
  - `needs_manual_edit`
- `marker-26-the-boss-c01`
  - `needs_manual_edit`
- `marker-12-testing-c01`
  - `needs_manual_edit`
- `marker-16-elites-c02`
  - `needs_manual_edit`
- `marker-22-inventory-stats-c03`
  - `needs_manual_edit`
- `marker-6-vfx-c01`
  - `needs_manual_edit`
- `marker-21-hallways-c02`
  - `needs_manual_edit`
- `marker-18-stats-armor-c02`
  - `needs_manual_edit`

## Current Win

The transcript is now rendered in chunks, reviewable by marker, stitchable into a full narration, and editable at a basic word level. That is the first real production-style baseline this project has had.

## Current Upgrade

The pipeline now also supports:

- an editable TSV review sheet:
  - `reports/qwen-review-sheet.tsv`
- applying letter-coded decisions back into approvals:
  - `scripts/apply-review-sheet.py`
- real word timestamps from Whisper for current generated WAVs:
  - `alignments/qwen3-reftext-full-v2/*.words.json`
