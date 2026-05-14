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
- official `Qwen3-ForcedAligner-0.6B` downloaded and tested successfully
- official `Qwen3-ASR-0.6B` downloaded and tested successfully
- full `qwen_forced_aligner` alignment pass completed for all 66 chunks
- pronunciation/style rerender A/B/C testing path working
- V6 planning scaffolding for pronunciation and model research
  - `config/pronunciation-glossary.tsv`
  - `config/model-registry.json`
  - `transcripts/benchmark-lines.tsv`
- first working pronunciation layer
  - `scripts/find-pronunciation-terms.py`
  - `scripts/apply-pronunciation-glossary.py`
  - `scripts/pronunciation-qc.py`
  - `transcripts/devlog-final-manifest-spoken.tsv`
  - `reports/pronunciation-candidates.tsv`
  - `reports/pronunciation-qc.tsv`
- full spoken-manifest rerender started for the original voice
  - `outputs/qwen3-reftext-spoken-full-v1`
- one previously failed spoken chunk repaired successfully
  - `marker-21-hallways-c02`
- complete stitched narration built from the spoken run with fallback only where needed
  - `outputs/final/devlog-final-yours-spoken-v1.wav`
  - `outputs/final/devlog-final-yours-spoken-v1.mapping.tsv`

Not done:
- meaningful human approval decisions across the transcript
- higher-quality aligner backend like WhisperX/MFA for future comparison
- higher-quality per-word time/pitch editing
- better reusable pronunciation/style variant generation flow
- glossary-driven `synthesis_text` manifest flow
- pronunciation QC refinement as glossary expands
- controlled TTS benchmark harness

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
- pronunciation tests:
  - `outputs/qwen3-pronunciation-tests`
- pronunciation/model research scaffolding:
  - `config/pronunciation-glossary.tsv`
  - `config/model-registry.json`
  - `transcripts/benchmark-lines.tsv`
- spoken-manifest full rerender:
  - `outputs/qwen3-reftext-spoken-full-v1`
- stitched mixed-source spoken full narration:
  - `outputs/final/devlog-final-yours-spoken-v1.wav`
  - `outputs/final/devlog-final-yours-spoken-v1.mapping.tsv`

## Current Problems

- low-level generated noise still exists
- denoise can reduce noise, but overdoing it causes pumping or artifacts
- chunk seams can be obvious if chunking is too aggressive
- some script wording is still too pause-heavy
- ASR QC is now working locally with cached `faster-whisper`
- current alignment now supports:
  - `whisper_words` from `faster-whisper`
  - `qwen_forced_aligner` from `Qwen3-ForcedAligner-0.6B`
  - `silence_aware_heuristic` as fallback
- the spoken-manifest full rerender still hangs on the five outro chunks in this environment
- current full narration therefore falls back to the earlier pass for:
  - `marker-29-outro-c01`
  - `marker-29-outro-c02`
  - `marker-29-outro-c03`
  - `marker-29-outro-c04`
  - `marker-29-outro-c05`

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
- real Qwen forced-aligner timestamps for comparison:
  - `alignments/qwen3-reftext-qfa-test/*.words.json`
- pronunciation rerender comparisons:
  - `outputs/qwen3-pronunciation-tests/marker-14-lighting/*.wav`

## Current Direction

The next real pipeline layer is pronunciation control before generation:

- original script text stays human-readable
- `synthesis_text` becomes the Qwen-ready form
- glossary/G2P solves names, acronyms, and technical terms
- Qwen forced aligner and prosody edits stay focused on timing/emphasis after generation

The first version of that layer now exists and is usable.
